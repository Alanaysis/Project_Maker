"""
车载场景目标检测 Demo

演示如何使用量化框架进行目标检测模型的量化和推理
"""

import numpy as np
import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.quantization import Quantizer, QuantConfig
from src.operators.fusion import OperatorFusion


class SimpleDetectionModel:
    """
    简单的目标检测模型

    模拟一个简单的目标检测网络
    """

    def __init__(self):
        """初始化模型"""
        # 模拟卷积层权重
        self.conv1_weight = np.random.randn(16, 3, 3, 3).astype(np.float32) * 0.1
        self.conv1_bias = np.zeros(16, dtype=np.float32)

        self.conv2_weight = np.random.randn(32, 16, 3, 3).astype(np.float32) * 0.1
        self.conv2_bias = np.zeros(32, dtype=np.float32)

        # 全连接层
        self.fc_weight = np.random.randn(10, 32 * 8 * 8).astype(np.float32) * 0.1
        self.fc_bias = np.zeros(10, dtype=np.float32)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        前向传播

        Args:
            x: 输入图像 [batch, channels, height, width]

        Returns:
            检测结果
        """
        # Conv1 + ReLU
        x = self._conv2d(x, self.conv1_weight, self.conv1_bias)
        x = np.maximum(0, x)  # ReLU

        # MaxPool
        x = self._maxpool2d(x, kernel_size=2, stride=2)

        # Conv2 + ReLU
        x = self._conv2d(x, self.conv2_weight, self.conv2_bias)
        x = np.maximum(0, x)  # ReLU

        # MaxPool
        x = self._maxpool2d(x, kernel_size=2, stride=2)

        # Flatten
        batch_size = x.shape[0]
        x = x.reshape(batch_size, -1)

        # FC
        x = np.dot(x, self.fc_weight.T) + self.fc_bias

        return x

    def _conv2d(self, x, weight, bias, stride=1, padding=1):
        """卷积实现"""
        batch, in_channels, h, w = x.shape
        out_channels, _, kh, kw = weight.shape

        # 添加 padding
        if padding > 0:
            x = np.pad(x, ((0, 0), (0, 0), (padding, padding), (padding, padding)))

        out_h = (h + 2 * padding - kh) // stride + 1
        out_w = (w + 2 * padding - kw) // stride + 1

        output = np.zeros((batch, out_channels, out_h, out_w))

        for b in range(batch):
            for oc in range(out_channels):
                for oh in range(out_h):
                    for ow in range(out_w):
                        h_start = oh * stride
                        w_start = ow * stride
                        receptive_field = x[b, :, h_start:h_start+kh, w_start:w_start+kw]
                        output[b, oc, oh, ow] = np.sum(receptive_field * weight[oc]) + bias[oc]

        return output

    def _maxpool2d(self, x, kernel_size=2, stride=2):
        """最大池化实现"""
        batch, channels, h, w = x.shape
        out_h = (h - kernel_size) // stride + 1
        out_w = (w - kernel_size) // stride + 1

        output = np.zeros((batch, channels, out_h, out_w))

        for b in range(batch):
            for c in range(channels):
                for oh in range(out_h):
                    for ow in range(out_w):
                        h_start = oh * stride
                        w_start = ow * stride
                        receptive_field = x[b, c, h_start:h_start+kernel_size, w_start:w_start+kernel_size]
                        output[b, c, oh, ow] = np.max(receptive_field)

        return output

    def get_weights(self):
        """获取模型权重"""
        return {
            "conv1_weight": self.conv1_weight,
            "conv1_bias": self.conv1_bias,
            "conv2_weight": self.conv2_weight,
            "conv2_bias": self.conv2_bias,
            "fc_weight": self.fc_weight,
            "fc_bias": self.fc_bias,
        }


def create_calibration_data(num_samples=10, image_size=32):
    """
    创建校准数据

    Args:
        num_samples: 样本数量
        image_size: 图像大小

    Returns:
        校准数据列表
    """
    data = []
    for _ in range(num_samples):
        # 模拟车载图像数据
        image = np.random.randn(1, 3, image_size, image_size).astype(np.float32)
        data.append(image)
    return data


def run_detection_demo():
    """运行目标检测 demo"""
    print("=" * 60)
    print("车载场景目标检测 Demo")
    print("=" * 60)

    # 1. 创建模型
    print("\n1. 创建目标检测模型...")
    model = SimpleDetectionModel()
    print("   模型创建完成")

    # 2. 创建校准数据
    print("\n2. 创建校准数据...")
    calibration_data = create_calibration_data(num_samples=5, image_size=32)
    print(f"   创建了 {len(calibration_data)} 个校准样本")

    # 3. 配置量化
    print("\n3. 配置量化参数...")
    config = QuantConfig(
        quant_type="int8",
        calibration_method="percentile",
        calibration_percentile=99.99,
        per_channel=True,
        symmetric=True,
    )
    print(f"   量化类型: {config.quant_type}")
    print(f"   校准方法: {config.calibration_method}")
    print(f"   逐通道量化: {config.per_channel}")

    # 4. 执行量化
    print("\n4. 执行量化...")
    quantizer = Quantizer(config)

    # 获取原始权重
    original_weights = model.get_weights()

    # 量化模型
    quant_result = quantizer.quantize(model, calibration_data)

    # 5. 评估量化误差
    print("\n5. 评估量化误差...")
    quantized_weights = quant_result["weights"]
    errors = quantizer.evaluate_quantization_error(original_weights, quantized_weights)

    for name, error in errors.items():
        print(f"   {name}:")
        print(f"     MSE: {error['mse']:.6f}")
        print(f"     MAE: {error['mae']:.6f}")
        print(f"     SNR: {error['snr']:.2f} dB")

    # 6. 性能测试
    print("\n6. 性能测试...")
    test_input = np.random.randn(1, 3, 32, 32).astype(np.float32)

    # 测试原始模型
    start_time = time.time()
    for _ in range(10):
        original_output = model.forward(test_input)
    original_time = (time.time() - start_time) / 10

    print(f"   原始模型推理时间: {original_time*1000:.2f} ms")

    # 7. 模型大小对比
    print("\n7. 模型大小对比...")
    original_size = sum(w.nbytes for w in original_weights.values())
    quantized_size = sum(w.size for w in quantized_weights.values())  # INT8

    print(f"   原始模型大小: {original_size / 1024:.2f} KB")
    print(f"   量化模型大小: {quantized_size / 1024:.2f} KB")
    print(f"   压缩比: {original_size / quantized_size:.2f}x")

    # 8. 输出结果
    print("\n8. 检测结果...")
    print(f"   原始模型输出: {original_output[0][:5]}...")  # 显示前5个值

    # 模拟检测结果
    print("\n   模拟检测结果:")
    print("   - 目标 1: 车辆, 置信度 0.95, 位置 [100, 150, 200, 250]")
    print("   - 目标 2: 行人, 置信度 0.87, 位置 [300, 200, 350, 300]")

    print("\n" + "=" * 60)
    print("Demo 完成!")
    print("=" * 60)

    return {
        "quantizer": quantizer,
        "quant_result": quant_result,
        "errors": errors,
    }


def run_benchmark():
    """运行基准测试"""
    print("\n" + "=" * 60)
    print("性能基准测试")
    print("=" * 60)

    model = SimpleDetectionModel()
    test_input = np.random.randn(1, 3, 32, 32).astype(np.float32)

    # 预热
    for _ in range(5):
        model.forward(test_input)

    # 测试
    num_iterations = 50
    times = []

    for _ in range(num_iterations):
        start_time = time.time()
        model.forward(test_input)
        end_time = time.time()
        times.append(end_time - start_time)

    times = np.array(times) * 1000  # 转换为毫秒

    print(f"\n测试配置:")
    print(f"  迭代次数: {num_iterations}")
    print(f"  输入形状: (1, 3, 32, 32)")

    print(f"\n性能结果:")
    print(f"  平均延迟: {np.mean(times):.2f} ms")
    print(f"  标准差: {np.std(times):.2f} ms")
    print(f"  最小延迟: {np.min(times):.2f} ms")
    print(f"  最大延迟: {np.max(times):.2f} ms")
    print(f"  P95 延迟: {np.percentile(times, 95):.2f} ms")
    print(f"  P99 延迟: {np.percentile(times, 99):.2f} ms")
    print(f"  吞吐量: {1000 / np.mean(times):.2f} FPS")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # 运行检测 demo
    run_detection_demo()

    # 运行基准测试
    run_benchmark()
