"""
量化配置模块

提供量化相关的配置类
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class QuantConfig:
    """
    量化配置

    Attributes:
        quant_type: 量化类型，支持 'int8', 'int4'
        calibration_method: 校准方法，支持 'minmax', 'percentile', 'entropy'
        calibration_percentile: 百分位校准的百分位数
        per_channel: 是否逐通道量化
        symmetric: 是否对称量化
        num_calibration_samples: 校准样本数量
        num_bits: 量化位数
        skip_ops: 跳过量化的算子列表
    """

    # 量化类型
    quant_type: str = "int8"

    # 校准方法
    calibration_method: str = "percentile"

    # 百分位校准参数
    calibration_percentile: float = 99.99

    # 量化粒度
    per_channel: bool = True
    symmetric: bool = True

    # 校准数据
    num_calibration_samples: int = 100

    # 量化位数
    num_bits: int = 8

    # 跳过的算子
    skip_ops: List[str] = field(default_factory=list)

    def __post_init__(self):
        """验证配置参数"""
        valid_quant_types = ["int8", "int4"]
        if self.quant_type not in valid_quant_types:
            raise ValueError(f"不支持的量化类型: {self.quant_type}，支持: {valid_quant_types}")

        valid_calib_methods = ["minmax", "percentile", "entropy"]
        if self.calibration_method not in valid_calib_methods:
            raise ValueError(f"不支持的校准方法: {self.calibration_method}，支持: {valid_calib_methods}")

        if self.quant_type == "int8":
            self.num_bits = 8
        elif self.quant_type == "int4":
            self.num_bits = 4

    @property
    def quant_range(self) -> tuple:
        """获取量化范围"""
        if self.symmetric:
            return (-(2 ** (self.num_bits - 1)), 2 ** (self.num_bits - 1) - 1)
        else:
            return (0, 2**self.num_bits - 1)
