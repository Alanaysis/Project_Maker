# 傅里叶变换 (Fourier Transform)

从零实现 DFT/FFT 傅里叶变换，深入理解频域分析的核心原理。

## 学习目标

- **理解傅里叶变换原理**：任何信号都可以分解为不同频率的正弦波叠加
- **掌握 FFT 算法**：Cooley-Tukey 算法如何将 O(N^2) 降低到 O(N log N)
- **学会频谱分析**：幅度谱、功率谱、相位谱、峰值检测

## 核心循环

```
时域信号 → FFT → 频域表示 → 频谱分析
```

1. **时域信号**：信号随时间的变化 x[n]
2. **FFT**：快速傅里叶变换，将信号从时域变换到频域
3. **频域表示**：信号中包含的频率成分 X[k]
4. **频谱分析**：提取幅度、功率、相位等特征

## 项目结构

```
fourier-transform/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── docs/
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现文档
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档
├── src/
│   ├── __init__.py
│   ├── dft.py                  # DFT/IDFT 实现
│   ├── fft.py                  # FFT/IFFT 实现
│   ├── spectrum.py             # 频谱分析
│   ├── signals.py              # 信号生成
│   └── visualization.py        # 可视化
├── tests/
│   ├── test_dft.py             # DFT 测试
│   ├── test_fft.py             # FFT 测试
│   ├── test_spectrum.py        # 频谱分析测试
│   └── test_signals.py         # 信号生成测试
└── examples/
    ├── basic_example.py        # 基础示例
    ├── signal_analysis.py      # 信号分析
    ├── filter_example.py       # 频域滤波
    └── visualization_example.py # 可视化示例
```

## 快速开始

### 基本使用

```python
import numpy as np
from src.fft import fft, ifft
from src.spectrum import magnitude_spectrum, frequency_bins, peak_frequencies

# 创建信号: 50 Hz + 120 Hz
sample_rate = 1000.0
t = np.arange(1000) / sample_rate
signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)

# FFT 变换
X = fft(signal)

# 幅度谱
mag = magnitude_spectrum(X)
freqs = frequency_bins(len(signal), sample_rate)

# 检测主要频率
peaks = peak_frequencies(X, sample_rate, threshold=0.1)
for freq, amp in peaks:
    print(f"频率: {freq:.1f} Hz, 幅度: {amp:.2f}")

# 逆变换恢复信号
x_recovered = ifft(X)
print(f"恢复误差: {np.max(np.abs(signal - x_recovered.real)):.2e}")
```

### 频域滤波

```python
from src.fft import fft, ifft
from src.spectrum import frequency_bins

# FFT
X = fft(signal)

# 低通滤波: 去除 100 Hz 以上的频率
freqs = frequency_bins(len(signal), sample_rate)
X[np.abs(freqs) > 100] = 0

# IFFT 恢复
filtered = np.real(ifft(X))
```

### 频谱分析

```python
from src.spectrum import (
    magnitude_spectrum,
    power_spectrum,
    phase_spectrum,
    spectral_centroid,
    bandwidth,
)

X = fft(signal)

# 幅度谱
mag = magnitude_spectrum(X)

# 功率谱 (dB)
from src.spectrum import power_spectrum_db
power_db = power_spectrum_db(X)

# 相位谱
phase = phase_spectrum(X)

# 频谱质心
centroid = spectral_centroid(X, sample_rate)
print(f"频谱质心: {centroid:.1f} Hz")

# 带宽
bw = bandwidth(X, sample_rate)
print(f"带宽: {bw:.1f} Hz")
```

### 可视化

```python
from src.visualization import plot_full_analysis

# 完整分析图 (时域 + 幅度谱 + 功率谱 + 相位谱)
fig = plot_full_analysis(signal, sample_rate, title="信号分析")
fig.savefig("analysis.png")
```

## 核心算法

### 1. DFT (离散傅里叶变换)

```python
def dft(x):
    """朴素 DFT，O(N^2)"""
    N = len(x)
    n = np.arange(N)
    k = n.reshape((N, 1))
    W = np.exp(-2j * np.pi * k * n / N)
    return W @ x
```

**原理**: 用 DFT 矩阵乘以输入向量。

### 2. FFT (快速傅里叶变换)

```python
def fft(x):
    """Cooley-Tukey FFT，O(N log N)"""
    N = len(x)
    if N == 1:
        return x

    even = fft(x[0::2])  # 偶数索引
    odd = fft(x[1::2])   # 奇数索引

    k = np.arange(N // 2)
    twiddle = np.exp(-2j * np.pi * k / N)
    t = twiddle * odd

    return np.concatenate([even + t, even - t])
```

**原理**: 分治策略，利用旋转因子的对称性。

### 3. IFFT (逆变换)

```python
def ifft(X):
    """利用 FFT 计算逆变换"""
    return np.conj(fft(np.conj(X))) / len(X)
```

## 关键概念

### 频率分辨率

```
Δf = 采样率 / FFT 点数
```

更多采样点 → 更高的频率分辨率。

### 采样定理 (奈奎斯特定理)

```
采样率 > 2 × 信号最高频率
```

否则会出现混叠 (Aliasing)。

### Parseval 定理

```
时域能量 = 频域能量
Σ|x[n]|^2 = (1/N) Σ|X[k]|^2
```

### 卷积定理

```
时域卷积 = 频域乘法
FFT(x * h) = FFT(x) · FFT(h)
```

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块
pytest tests/test_fft.py -v

# 运行示例
python examples/basic_example.py
python examples/signal_analysis.py
python examples/filter_example.py
```

## 参考资料

- [Cooley, J. W., & Tukey, J. W. (1965). An algorithm for the machine calculation of complex Fourier series.](https://doi.org/10.2307/2003354)
- [Oppenheim, A. V., & Schafer, R. W. (2010). Discrete-Time Signal Processing.](https://www.pearson.com/en-us/subject-catalog/p/discrete-time-signal-processing/P200000003336)
- [numpy.fft 文档](https://numpy.org/doc/stable/reference/routines.fft.html)
- [FFT 算法详解 - Wikipedia](https://en.wikipedia.org/wiki/Fast_Fourier_transform)

## License

This project is for educational purposes.

---

[返回主目录](../../README.md)
