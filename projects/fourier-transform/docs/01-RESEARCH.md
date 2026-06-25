# 调研文档: 傅里叶变换

## 1. 傅里叶变换概述

### 1.1 历史背景

傅里叶变换由法国数学家约瑟夫·傅里叶 (Joseph Fourier) 于 1807 年提出。他发现任何周期函数都可以表示为正弦和余弦函数的无穷级数之和。这一发现彻底改变了信号处理、物理学和工程学。

### 1.2 核心思想

傅里叶变换的核心思想是：**任何信号都可以分解为不同频率的正弦波的叠加**。

- **时域**: 信号随时间的变化
- **频域**: 信号中包含的频率成分及其强度

### 1.3 数学定义

#### 连续傅里叶变换 (CFT)

正变换:
```
X(f) = ∫_{-∞}^{∞} x(t) * e^{-j*2*π*f*t} dt
```

逆变换:
```
x(t) = ∫_{-∞}^{∞} X(f) * e^{j*2*π*f*t} df
```

#### 离散傅里叶变换 (DFT)

正变换:
```
X[k] = Σ_{n=0}^{N-1} x[n] * e^{-j*2*π*k*n/N},  k = 0, 1, ..., N-1
```

逆变换:
```
x[n] = (1/N) * Σ_{k=0}^{N-1} X[k] * e^{j*2*π*k*n/N},  n = 0, 1, ..., N-1
```

## 2. FFT 算法调研

### 2.1 Cooley-Tukey 算法

1965 年，James Cooley 和 John Tukey 发表了快速傅里叶变换 (FFT) 算法，将 DFT 的计算复杂度从 O(N^2) 降低到 O(N log N)。

**核心思想**: 利用 DFT 的对称性和周期性，将 N 点 DFT 分解为两个 N/2 点 DFT。

```
X[k] = E[k] + W_N^k * O[k]
X[k + N/2] = E[k] - W_N^k * O[k]
```

其中:
- E[k] = 偶数索引的 DFT
- O[k] = 奇数索引的 DFT
- W_N^k = e^{-j*2*π*k/N} (旋转因子)

### 2.2 其他 FFT 算法

| 算法 | 复杂度 | 特点 |
|------|--------|------|
| Cooley-Tukey (基2) | O(N log N) | 最常用，要求 N 为 2 的幂 |
| Cooley-Tukey (基4) | O(N log N) | 减少乘法次数 |
| Split-Radix | O(N log N) | 基2和基4的混合 |
| Bluestein | O(N log N) | 任意长度 |
| Rader | O(N log N) | N 为素数 |
| Winograd | O(N log N) | 最少乘法次数 |

### 2.3 实现选择

本项目选择实现:
1. **朴素 DFT** (O(N^2)): 用于理解原理
2. **递归 FFT** (O(N log N)): 教学清晰
3. **迭代 FFT** (O(N log N)): 性能更好

## 3. 频谱分析调研

### 3.1 幅度谱

```
|X[k]| = sqrt(Re(X[k])^2 + Im(X[k])^2)
```

表示每个频率分量的强度。

### 3.2 功率谱

```
P[k] = |X[k]|^2
```

表示每个频率分量的能量。Parseval 定理保证时域和频域的总能量相等。

### 3.3 相位谱

```
φ[k] = arctan(Im(X[k]) / Re(X[k]))
```

表示每个频率分量的相位偏移。

### 3.4 功率谱密度 (PSD)

```
PSD[k] = |X[k]|^2 / (N * fs)
```

单位: V^2/Hz 或 dB/Hz

## 4. 应用领域调研

### 4.1 音频处理
- 音频频谱分析
- 音高检测
- 均衡器 (EQ)
- 降噪

### 4.2 图像处理
- 图像压缩 (JPEG)
- 图像滤波
- 边缘检测

### 4.3 通信系统
- OFDM 调制
- 信道估计
- 频谱分析

### 4.4 生物医学
- 心电图 (ECG) 分析
- 脑电图 (EEG) 分析
- 医学成像 (MRI)

### 4.5 振动分析
- 机械故障诊断
- 结构健康监测

## 5. Python 生态调研

### 5.1 NumPy/SciPy

```python
import numpy as np
X = np.fft.fft(x)          # FFT
x = np.fft.ifft(X)         # IFFT
freqs = np.fft.fftfreq(N)  # 频率轴
```

### 5.2 其他库

- **scipy.fft**: 更多 FFT 变体
- **pyfftw**: FFTW 的 Python 绑定，更快
- **librosa**: 音频专用
- **matplotlib**: 可视化

## 6. 参考资料

1. Cooley, J. W., & Tukey, J. W. (1965). An algorithm for the machine calculation of complex Fourier series.
2. Oppenheim, A. V., & Schafer, R. W. (2010). Discrete-Time Signal Processing.
3. Bracewell, R. N. (2000). The Fourier Transform and Its Applications.
4. [numpy.fft 文档](https://numpy.org/doc/stable/reference/routines.fft.html)
5. [FFT 算法详解 - Wikipedia](https://en.wikipedia.org/wiki/Fast_Fourier_transform)
