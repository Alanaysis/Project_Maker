# 模拟滤波器产品文档

## 1. 产品概述

模拟滤波器是一个教学级 Python 库，实现了常见的模拟滤波器，帮助学习者深入理解滤波器原理和应用。

## 2. 目标用户

- 电子工程学生
- 信号处理学习者
- 嵌入式系统开发者
- 音频工程师

## 3. 功能特性

### 3.1 核心滤波器

| 滤波器 | 类名 | 参数 | 输出 |
|--------|------|------|------|
| RC 低通 | RCLowPass | R, C | fc, τ, H(f) |
| RL 低通 | RLLowPass | R, L | fc, τ, H(f) |
| RC 高通 | RCHighPass | R, C | fc, τ, H(f) |
| RL 高通 | RLHighPass | R, L | fc, τ, H(f) |
| RLC 带通 | RLCBandPass | R, L, C | f0, BW, Q, H(f) |
| RLC 带阻 | RLCBandStop | R, L, C | f0, BW, Q, H(f) |

### 3.2 频率响应分析

- 幅频响应 (线性值和 dB)
- 相频响应 (度)
- 截止频率检测
- 带宽检测
- 滤波器级联分析

### 3.3 可视化

- 波特图 (幅频 + 相频)
- 幅频响应图
- 相频响应图
- 阶跃响应图
- 冲激响应图
- 多滤波器对比图

### 3.4 实际应用

- 音频分频器
- 陷波滤波器
- 信号调理器

## 4. 使用指南

### 4.1 安装

```bash
pip install numpy matplotlib
```

### 4.2 基本使用

```python
import numpy as np
from src.lowpass import RCLowPass

# 创建滤波器
filt = RCLowPass(R=1000, C=1e-6)

# 查看参数
print(f"截止频率: {filt.fc:.2f} Hz")
print(f"时间常数: {filt.tau*1000:.2f} ms")

# 计算频率响应
f = np.logspace(1, 5, 100)
mag_db = filt.magnitude_db(f)
phase = filt.phase(f)
```

### 4.3 音频处理

```python
from src.applications import AudioCrossover

# 创建分频器
crossover = AudioCrossover(crossover_freq=1000)

# 处理信号
low = crossover.process(signal, t, 'low')
high = crossover.process(signal, t, 'high')
```

### 4.4 噪声消除

```python
from src.applications import NotchFilter

# 创建陷波滤波器
notch = NotchFilter(notch_freq=50.0, Q=30)

# 消除工频干扰
cleaned = notch.process(noisy_signal, t)
```

### 4.5 可视化

```python
from src.visualization import plot_bode, plot_comparison

# 绘制波特图
plot_bode(filt, f, title="RC 低通滤波器")

# 对比多个滤波器
plot_comparison([rc_lp, rl_lp], f, labels=["RC", "RL"])
```

## 5. API 参考

### 5.1 RCLowPass

```python
class RCLowPass:
    """RC 低通滤波器"""

    def __init__(self, R: float, C: float):
        """
        Parameters
        ----------
        R : float
            电阻值 (欧姆)
        C : float
            电容值 (法拉)
        """

    @property
    def fc(self) -> float:
        """截止频率 (Hz)"""

    @property
    def tau(self) -> float:
        """时间常数 (秒)"""

    def transfer_function(self, f: np.ndarray) -> np.ndarray:
        """计算传递函数"""

    def magnitude(self, f: np.ndarray) -> np.ndarray:
        """计算幅频响应 (线性值)"""

    def magnitude_db(self, f: np.ndarray) -> np.ndarray:
        """计算幅频响应 (dB)"""

    def phase(self, f: np.ndarray) -> np.ndarray:
        """计算相频响应 (度)"""

    def step_response(self, t: np.ndarray) -> np.ndarray:
        """计算阶跃响应"""

    def impulse_response(self, t: np.ndarray) -> np.ndarray:
        """计算冲激响应"""
```

### 5.2 RLCBandPass

```python
class RLCBandPass:
    """RLC 带通滤波器"""

    def __init__(self, R: float, L: float, C: float):
        """
        Parameters
        ----------
        R : float
            电阻值 (欧姆)
        L : float
            电感值 (亨利)
        C : float
            电容值 (法拉)
        """

    @property
    def f0(self) -> float:
        """中心频率 (Hz)"""

    @property
    def bw(self) -> float:
        """带宽 (Hz)"""

    @property
    def Q(self) -> float:
        """品质因数"""

    def lower_cutoff(self) -> float:
        """下截止频率 (Hz)"""

    def upper_cutoff(self) -> float:
        """上截止频率 (Hz)"""
```

### 5.3 频率响应分析

```python
def generate_log_freq(start: float, stop: float, num_points: int) -> np.ndarray:
    """生成对数间隔频率数组"""

def find_cutoff_frequency(f: np.ndarray, mag_db: np.ndarray, attenuation: float = -3.0) -> float:
    """查找截止频率"""

def analyze_filter(filter_obj, f: np.ndarray) -> dict:
    """全面分析滤波器特性"""
```

### 5.4 可视化

```python
def plot_bode(filter_obj, f: np.ndarray, title: str = "波特图"):
    """绘制波特图"""

def plot_comparison(filters: list, f: np.ndarray, labels: list = None):
    """对比多个滤波器"""
```

## 6. 示例代码

### 6.1 基本滤波器

```python
# examples/basic_filters.py
python examples/basic_filters.py
```

### 6.2 音频处理

```python
# examples/audio_processing.py
python examples/audio_processing.py
```

### 6.3 信号调理

```python
# examples/signal_conditioning.py
python examples/signal_conditioning.py
```

## 7. 常见问题

### Q1: 如何选择 R、L、C 的值？

根据截止频率公式反推：
- RC 低通: C = 1 / (2π × R × fc)
- RL 低通: L = R / (2π × fc)

### Q2: 为什么使用 dB 表示增益？

dB 是对数刻度：
- 便于表示大范围数值
- 简化级联系统计算
- 符合人耳感知

### Q3: Q 值的意义是什么？

Q = f₀ / BW
- Q 越高，带宽越窄，选择性越好
- Q 越低，带宽越宽，选择性越差

## 8. 版本历史

### v1.0.0 (2024)
- 初始版本
- 实现 6 种基本滤波器
- 频率响应分析
- 可视化工具
- 音频处理应用
- 信号调理应用
