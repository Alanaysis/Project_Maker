# 开发文档: 傅里叶变换

## 1. 开发环境

### 1.1 依赖

- Python >= 3.8
- numpy
- matplotlib (可选，用于可视化)
- pytest (测试)

### 1.2 安装

```bash
pip install numpy matplotlib pytest
```

## 2. 项目结构

```
fourier-transform/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── docs/
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现文档
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档 (本文件)
├── src/
│   ├── __init__.py             # 包初始化
│   ├── dft.py                  # DFT/IDFT
│   ├── fft.py                  # FFT/IFFT
│   ├── spectrum.py             # 频谱分析
│   ├── signals.py              # 信号生成
│   └── visualization.py        # 可视化
├── tests/
│   ├── __init__.py
│   ├── test_dft.py
│   ├── test_fft.py
│   ├── test_spectrum.py
│   └── test_signals.py
└── examples/
    ├── basic_example.py        # 基础示例
    ├── signal_analysis.py      # 信号分析
    ├── filter_example.py       # 频域滤波
    └── visualization_example.py # 可视化示例
```

## 3. 开发流程

### 3.1 核心循环

```
时域信号 → FFT → 频域表示 → 频谱分析
```

### 3.2 开发顺序

1. **DFT 实现** (dft.py)
   - 矩阵方法 dft()
   - 循环方法 dft_slow()
   - 逆变换 idft()

2. **FFT 实现** (fft.py)
   - 递归 fft()
   - 迭代 fft_radix2()
   - 逆变换 ifft()
   - 二维 fft2d()

3. **频谱分析** (spectrum.py)
   - 幅度谱、功率谱、相位谱
   - 频率轴
   - 峰值检测
   - 频谱特征

4. **信号生成** (signals.py)
   - 基本波形
   - 复合信号
   - 噪声

5. **可视化** (visualization.py)
   - 时域/频域绘图
   - 频谱图

## 4. 使用示例

### 4.1 基本 FFT

```python
import numpy as np
from src.fft import fft, ifft
from src.spectrum import magnitude_spectrum, frequency_bins

# 创建信号
sample_rate = 1000.0
t = np.arange(1000) / sample_rate
signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)

# FFT
X = fft(signal)

# 幅度谱
mag = magnitude_spectrum(X)
freqs = frequency_bins(len(signal), sample_rate)

# 找主要频率
half = len(signal) // 2
peak_idx = np.argsort(mag[:half])[-2:]
for idx in peak_idx:
    print(f"频率: {freqs[idx]:.1f} Hz, 幅度: {mag[idx]:.2f}")
```

### 4.2 频域滤波

```python
from src.fft import fft, ifft

# 低通滤波
X = fft(signal)
cutoff = 100  # Hz
freqs = frequency_bins(len(signal), sample_rate)
X[np.abs(freqs) > cutoff] = 0
filtered = np.real(ifft(X))
```

### 4.3 频谱分析

```python
from src.spectrum import (
    magnitude_spectrum,
    spectral_centroid,
    bandwidth,
    peak_frequencies,
)

X = fft(signal)

# 频谱质心
centroid = spectral_centroid(X, sample_rate)

# 带宽
bw = bandwidth(X, sample_rate)

# 峰值频率
peaks = peak_frequencies(X, sample_rate, threshold=0.1)
for freq, amp in peaks:
    print(f"{freq:.1f} Hz: {amp:.2f}")
```

### 4.4 可视化

```python
from src.visualization import plot_full_analysis

fig = plot_full_analysis(signal, sample_rate, title="信号分析")
fig.savefig("analysis.png")
```

## 5. 运行示例

```bash
cd projects/fourier-transform

# 基础示例
python examples/basic_example.py

# 信号分析
python examples/signal_analysis.py

# 频域滤波
python examples/filter_example.py

# 可视化
python examples/visualization_example.py
```

## 6. 运行测试

```bash
cd projects/fourier-transform

# 所有测试
pytest tests/ -v

# 特定测试
pytest tests/test_fft.py -v

# 跳过慢测试
pytest tests/ -v -m "not slow"
```

## 7. 扩展方向

### 7.1 算法扩展

- 短时傅里叶变换 (STFT)
- 窗函数 (Hanning, Hamming, Blackman)
- 功率谱密度 (Welch 方法)
- 时频分析 (小波变换)

### 7.2 应用扩展

- 音频频谱分析器
- 实时频谱显示
- 音高检测
- 语音识别基础

### 7.3 性能优化

- FFTW 绑定 (pyfftw)
- GPU 加速 (CuPy)
- 并行计算
