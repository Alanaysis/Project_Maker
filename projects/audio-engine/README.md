# 音频处理引擎 (Audio Engine)

从零实现音频处理引擎，深入理解音频信号处理、FFT 变换和音频特效算法。

## 学习目标

- **理解音频信号处理**：掌握数字音频的基础概念（采样、量化、频域分析）
- **掌握 FFT 变换**：实现 Cooley-Tukey FFT 算法，理解蝶形运算和频域表示
- **学会音频特效算法**：实现延迟、混响、合唱、失真等经典音频效果

## 核心循环

```
音频输入 → FFT → 频域处理 → IFFT → 音频输出
```

1. **音频输入**：读取或生成音频信号（时域表示）
2. **FFT 变换**：将时域信号转换为频域表示
3. **频域处理**：在频域进行滤波、均衡、降噪等处理
4. **IFFT 变换**：将处理后的频域信号转换回时域
5. **音频输出**：输出处理后的音频信号

## 项目结构

```
audio-engine/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── docs/
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现文档
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档
├── src/
│   ├── __init__.py             # 包初始化
│   ├── fft.py                  # FFT/IFFT 变换
│   ├── audio_signal.py         # 音频信号类
│   ├── filters.py              # 滤波器（低通、高通、带通、陷波）
│   ├── effects.py              # 音频特效（延迟、混响、合唱、失真、压缩）
│   ├── mixer.py                # 混音器
│   ├── denoiser.py             # 降噪器
│   └── equalizer.py            # 均衡器
├── tests/
│   ├── __init__.py
│   ├── test_fft.py
│   ├── test_audio_signal.py
│   ├── test_filters.py
│   ├── test_effects.py
│   ├── test_mixer.py
│   ├── test_denoiser.py
│   └── test_equalizer.py
└── examples/
    ├── basic_fft.py            # FFT 基础示例
    ├── audio_filtering.py      # 滤波示例
    ├── audio_effects.py        # 特效示例
    └── mixing_denoising.py     # 混音降噪示例
```

## 快速开始

### 基本使用

```python
import numpy as np
from src import FFT, IFFT, AudioSignal, LowPassFilter, Equalizer

# 创建音频信号
signal = AudioSignal.from_tone(440, duration=1.0, sample_rate=44100)
print(f"信号: {signal}")

# FFT 变换
spectrum = FFT.transform(signal.data)
magnitude = FFT.magnitude_spectrum(signal.data)

# 低通滤波
lpf = LowPassFilter(cutoff_freq=2000, sample_rate=44100)
filtered = lpf.apply(signal)

# 均衡处理
eq = Equalizer(sample_rate=44100)
eq.add_band(440, gain_db=6.0, q_factor=2.0)  # 提升 440 Hz
eq.add_band(8000, gain_db=-3.0, q_factor=1.0)  # 衰减高频
equalized = eq.apply(signal)
```

### 音频特效

```python
from src import Delay, Reverb, Chorus, Distortion

# 延迟效果
delay = Delay(delay_time=0.3, feedback=0.5, mix=0.5)
delayed = delay.apply(signal)

# 混响效果
reverb = Reverb(room_size=0.5, damping=0.5, mix=0.3)
reverbed = reverb.apply(signal)

# 合唱效果
chorus = Chorus(rate=1.5, depth=0.002, mix=0.5)
chorused = chorus.apply(signal)

# 失真效果
distortion = Distortion(drive=0.5, mix=1.0)
distorted = distortion.apply(signal)
```

### 混音

```python
from src import Mixer

# 创建混音器
mixer = Mixer(sample_rate=44100)

# 添加音轨
mixer.add_track(vocal_signal, name="Vocal", volume=0.8, pan=0.0)
mixer.add_track(drum_signal, name="Drums", volume=0.7, pan=-0.2)
mixer.add_track(bass_signal, name="Bass", volume=0.6, pan=0.2)

# 渲染混音
left, right = mixer.render()  # 立体声
mono = mixer.render_to_mono()  # 单声道
```

### 降噪

```python
from src import Denoiser

# 创建降噪器
denoiser = Denoiser(noise_factor=2.0, spectral_floor=0.1)

# 估计噪声（从信号开头的静音段）
denoiser.estimate_noise(noisy_signal, noise_duration=0.5)

# 应用降噪
clean_signal = denoiser.apply(noisy_signal)
```

## 核心算法

### 1. FFT 变换（Cooley-Tukey 算法）

```python
def _fft_recursive(x):
    N = len(x)
    if N == 1:
        return x.copy()

    # 分治
    even = _fft_recursive(x[0::2])
    odd = _fft_recursive(x[1::2])

    # 蝶形运算
    T = np.exp(-2j * np.pi * np.arange(N // 2) / N) * odd
    result = np.zeros(N, dtype=complex)
    result[:N // 2] = even + T
    result[N // 2:] = even - T

    return result
```

**时间复杂度**：O(N log N)
**空间复杂度**：O(N)

### 2. 频域滤波

```python
def apply_filter(signal, filter_mask):
    # FFT 变换
    spectrum = FFT.transform(signal)

    # 频域乘法（时域卷积）
    filtered_spectrum = spectrum * filter_mask

    # IFFT 变换
    return IFFT.transform_real(filtered_spectrum)
```

### 3. 频谱减法降噪

```python
def spectral_subtraction(noisy_spectrum, noise_spectrum, alpha=2.0, beta=0.1):
    # 减去噪声频谱
    clean_sq = np.abs(noisy_spectrum)**2 - alpha * np.abs(noise_spectrum)**2

    # 应用谱下限
    clean_sq = np.maximum(clean_sq, beta * np.abs(noisy_spectrum)**2)

    return np.sqrt(clean_sq) * np.exp(1j * np.angle(noisy_spectrum))
```

## 关键概念

### 奈奎斯特定理

采样频率必须至少是信号最高频率的两倍：
```
采样率 >= 2 × 最高频率
```

### 帕塞瓦尔定理

时域能量 = 频域能量（能量守恒）：
```
Σ|x[n]|² = (1/N) Σ|X[k]|²
```

### 频域卷积定理

时域卷积 = 频域乘法：
```
y[n] = x[n] * h[n]  ↔  Y[k] = X[k] × H[k]
```

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_fft.py -v
pytest tests/test_filters.py -v
pytest tests/test_effects.py -v

# 运行测试并显示覆盖率
pytest tests/ -v --cov=src --cov-report=term-missing
```

## 运行示例

```bash
# FFT 基础示例
python examples/basic_fft.py

# 滤波示例
python examples/audio_filtering.py

# 特效示例
python examples/audio_effects.py

# 混音降噪示例
python examples/mixing_denoising.py
```

## 技术栈

- **Python 3.8+**
- **NumPy**：数值计算
- **pytest**：测试框架

## 参考资料

### 书籍

- 《数字信号处理》- 奥本海默
- 《音频处理与编码》
- 《计算机音乐教程》- Curtis Roads

### 在线资源

- [FFT 算法详解](https://en.wikipedia.org/wiki/Fast_Fourier_transform)
- [数字信号处理入门](https://www.dspguide.com/)
- [音频处理基础](https://www.audioholics.com/)

### 开源项目

- [FFmpeg](https://github.com/FFmpeg/FFmpeg) - 多媒体处理框架
- [libsndfile](https://github.com/libsndfile/libsndfile) - 音频文件读写
- [Aubio](https://github.com/aubio/aubio) - 音频分析库

## License

This project is for educational purposes.

---

[返回多媒体模块](../MEDIA_README.md) | [返回主目录](../../README.md)
