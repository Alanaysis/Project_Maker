"""
量化器主类

负责协调整个量化流程：
1. 加载模型
2. 校准激活值
3. 计算量化参数
4. 量化模型权重
5. 导出量化模型
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .config import QuantConfig
from .calibration import CalibratorFactory, Calibrator
from .quant_ops import (
    QuantParams,
    quantize_tensor,
    dequantize_tensor,
    compute_quantization_error,
)

logger = logging.getLogger(__name__)


@dataclass
class LayerQuantInfo:
    """层量化信息"""
    name: str
    weight_params: Optional[QuantParams] = None
    activation_params: Optional[QuantParams] = None
    quantized_weight: Optional[np.ndarray] = None


class Quantizer:
    """
    量化器

    负责将浮点模型量化为定点模型

    使用示例:
        config = QuantConfig(quant_type="int8", calibration_method="percentile")
        quantizer = Quantizer(config)

        # 校准
        quantizer.calibrate(model, calibration_data)

        # 量化
        quant_model = quantizer.quantize(model)
    """

    def __init__(self, config: Optional[QuantConfig] = None):
        """
        初始化量化器

        Args:
            config: 量化配置，如果为 None 则使用默认配置
        """
        self.config = config or QuantConfig()
        self.calibrator = CalibratorFactory.create(
            self.config.calibration_method,
            percentile=self.config.calibration_percentile,
        )
        self.layer_quant_info: Dict[str, LayerQuantInfo] = {}
        self.calibration_stats: Dict[str, List[np.ndarray]] = {}

        logger.info(f"初始化量化器: quant_type={self.config.quant_type}, "
                    f"calibration={self.config.calibration_method}")

    def calibrate(
        self,
        model: Any,
        calibration_data: List[np.ndarray],
        num_samples: Optional[int] = None,
    ) -> Dict[str, Tuple[float, float]]:
        """
        校准模型

        收集激活值统计信息，用于计算量化参数

        Args:
            model: 待校准的模型
            calibration_data: 校准数据集
            num_samples: 校准样本数量

        Returns:
            各层的校准结果 {layer_name: (min_val, max_val)}
        """
        num_samples = num_samples or self.config.num_calibration_samples
        logger.info(f"开始校准，使用 {num_samples} 个样本")

        # 收集激活值统计
        self._collect_activation_stats(model, calibration_data, num_samples)

        # 计算校准结果
        calibration_results = {}
        for layer_name, activations in self.calibration_stats.items():
            min_val, max_val = self.calibrator.calibrate(activations)
            calibration_results[layer_name] = (min_val, max_val)
            logger.debug(f"层 {layer_name}: min={min_val:.4f}, max={max_val:.4f}")

        logger.info(f"校准完成，共 {len(calibration_results)} 层")
        return calibration_results

    def _collect_activation_stats(
        self,
        model: Any,
        calibration_data: List[np.ndarray],
        num_samples: int,
    ):
        """
        收集激活值统计信息

        Args:
            model: 模型
            calibration_data: 校准数据
            num_samples: 样本数量
        """
        # 简化实现：假设模型有 forward 方法
        # 实际实现需要注册 hook 来收集中间层激活值
        for i, data in enumerate(calibration_data[:num_samples]):
            if hasattr(model, 'forward'):
                # 前向传播，收集激活值
                activations = model.forward(data)

                # 存储激活值（简化处理）
                if 'output' not in self.calibration_stats:
                    self.calibration_stats['output'] = []
                self.calibration_stats['output'].append(activations)

    def compute_quant_params(
        self,
        calibration_results: Dict[str, Tuple[float, float]],
        weights: Optional[Dict[str, np.ndarray]] = None,
    ) -> Dict[str, QuantParams]:
        """
        计算量化参数

        Args:
            calibration_results: 校准结果
            weights: 模型权重

        Returns:
            各层的量化参数
        """
        logger.info("计算量化参数")

        quant_params = {}

        for layer_name, (min_val, max_val) in calibration_results.items():
            if self.config.symmetric:
                # 对称量化
                abs_max = max(abs(min_val), abs(max_val))
                qmin, qmax = self.config.quant_range
                scale = abs_max / qmax if abs_max > 0 else 1.0
                zero_point = 0
            else:
                # 非对称量化
                qmin, qmax = self.config.quant_range
                scale = (max_val - min_val) / (qmax - qmin) if max_val != min_val else 1.0
                zero_point = int(np.clip(np.round(-min_val / scale), qmin, qmax))

            params = QuantParams(
                scale=scale,
                zero_point=zero_point,
                num_bits=self.config.num_bits,
                symmetric=self.config.symmetric,
                per_channel=False,
            )

            quant_params[layer_name] = params

            logger.debug(
                f"层 {layer_name}: scale={scale:.6f}, zero_point={zero_point}"
            )

        return quant_params

    def quantize_weight(
        self,
        weight: np.ndarray,
        params: QuantParams,
    ) -> Tuple[np.ndarray, QuantParams]:
        """
        量化单个权重张量

        Args:
            weight: 权重张量
            params: 量化参数

        Returns:
            (quantized_weight, updated_params)
        """
        if self.config.per_channel:
            # 逐通道量化
            quantized, updated_params = quantize_tensor(
                weight,
                num_bits=self.config.num_bits,
                symmetric=self.config.symmetric,
                per_channel=True,
                channel_axis=0,
            )
        else:
            # 逐层量化
            quantized, updated_params = quantize_tensor(
                weight,
                num_bits=self.config.num_bits,
                symmetric=self.config.symmetric,
                per_channel=False,
            )

        return quantized, updated_params

    def quantize(
        self,
        model: Any,
        calibration_data: Optional[List[np.ndarray]] = None,
    ) -> Dict[str, Any]:
        """
        量化模型

        Args:
            model: 待量化的模型
            calibration_data: 校准数据（如果需要校准）

        Returns:
            量化后的模型表示
        """
        logger.info("开始量化模型")

        # 如果提供了校准数据，先进行校准
        calibration_results = {}
        if calibration_data is not None:
            calibration_results = self.calibrate(model, calibration_data)

        # 获取模型权重
        weights = self._extract_weights(model)

        # 量化权重
        quantized_weights = {}
        for name, weight in weights.items():
            if name in self.config.skip_ops:
                logger.info(f"跳过算子 {name}")
                quantized_weights[name] = weight
                continue

            # 计算量化参数
            if name in calibration_results:
                min_val, max_val = calibration_results[name]
            else:
                min_val, max_val = float(weight.min()), float(weight.max())

            # 创建量化参数
            if self.config.symmetric:
                abs_max = max(abs(min_val), abs(max_val))
                qmin, qmax = self.config.quant_range
                scale = abs_max / qmax if abs_max > 0 else 1.0
                zero_point = 0
            else:
                qmin, qmax = self.config.quant_range
                scale = (max_val - min_val) / (qmax - qmin) if max_val != min_val else 1.0
                zero_point = int(np.clip(np.round(-min_val / scale), qmin, qmax))

            params = QuantParams(
                scale=scale,
                zero_point=zero_point,
                num_bits=self.config.num_bits,
                symmetric=self.config.symmetric,
            )

            # 量化
            quantized, params = self.quantize_weight(weight, params)

            # 存储量化信息
            self.layer_quant_info[name] = LayerQuantInfo(
                name=name,
                weight_params=params,
                quantized_weight=quantized,
            )

            quantized_weights[name] = quantized

            logger.debug(f"量化层 {name}: shape={weight.shape}, scale={scale:.6f}")

        logger.info(f"量化完成，共 {len(quantized_weights)} 层")

        return {
            "weights": quantized_weights,
            "quant_info": self.layer_quant_info,
        }

    def _extract_weights(self, model: Any) -> Dict[str, np.ndarray]:
        """
        提取模型权重

        Args:
            model: 模型

        Returns:
            权重字典 {name: weight}
        """
        weights = {}

        # PyTorch 模型
        if hasattr(model, 'state_dict'):
            state_dict = model.state_dict()
            for name, param in state_dict.items():
                if isinstance(param, np.ndarray):
                    weights[name] = param
                else:
                    # 转换 PyTorch 张量为 NumPy
                    weights[name] = param.detach().cpu().numpy()

        # ONNX 模型
        elif hasattr(model, 'graph'):
            for initializer in model.graph.initializer:
                weights[initializer.name] = np.frombuffer(
                    initializer.raw_data, dtype=np.float32
                ).reshape(initializer.dims)

        # 字典格式
        elif isinstance(model, dict):
            weights = model

        return weights

    def get_quantization_summary(self) -> Dict[str, Any]:
        """
        获取量化摘要

        Returns:
            量化摘要信息
        """
        summary = {
            "config": {
                "quant_type": self.config.quant_type,
                "calibration_method": self.config.calibration_method,
                "per_channel": self.config.per_channel,
                "symmetric": self.config.symmetric,
            },
            "layers": {},
        }

        for name, info in self.layer_quant_info.items():
            if info.weight_params is not None:
                summary["layers"][name] = {
                    "scale": float(info.weight_params.scale) if not info.weight_params.per_channel else info.weight_params.scale.tolist(),
                    "zero_point": int(info.weight_params.zero_point) if not info.weight_params.per_channel else info.weight_params.zero_point.tolist(),
                    "num_bits": info.weight_params.num_bits,
                }

        return summary

    def evaluate_quantization_error(
        self,
        original_weights: Dict[str, np.ndarray],
        quantized_weights: Dict[str, np.ndarray],
    ) -> Dict[str, Dict[str, float]]:
        """
        评估量化误差

        Args:
            original_weights: 原始权重
            quantized_weights: 量化后的权重

        Returns:
            各层的量化误差
        """
        errors = {}

        for name in original_weights:
            if name in quantized_weights and name in self.layer_quant_info:
                info = self.layer_quant_info[name]
                if info.weight_params is not None:
                    error = compute_quantization_error(
                        original_weights[name],
                        quantized_weights[name],
                        info.weight_params,
                    )
                    errors[name] = error

        return errors
