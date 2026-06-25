# 信号采样重建 (Signal Sampling & Reconstruction)

从零实现信号采样与重建，深入理解奈奎斯特定理、量化、重建和混叠原理。

## 项目概述

本项目实现了信号处理中的采样与重建核心算法，包括奈奎斯特采样、过采样、欠采样、均匀/非均匀量化、零阶保持/一阶保持/sinc 插值重建，以及混叠现象演示和抗混叠滤波。通过纯 Python 实现，不依赖信号处理库，帮助深入理解数字信号处理的基础原理。

### 核心循环

```
连续信号 → 采样 → 量化 → 编码 → 传输 → 解码 → 重建 → 连续信号
```

### 学习目标

- 理解奈奎斯特定理及其工程意义
- 掌握采样率选择和过采样/欠采样 tradeoff
- 理解均匀量化和非均匀量化的区别与应用
- 掌握零阶保持、一阶保持和 sinc 插值重建
- 理解混叠现象和抗混叠滤波的重要性
- 掌握音频和图像采样的实际应用

## 项目结构

```
signal-sampling/
├── README.md                 # 项目说明
├── LEARNING_NOTES.md         # 学习笔记
├── docs/                     # 文档目录
│   ├── 01_RESEARCH.md        # 调研报告
│   ├── 02_REQUIREMENTS.md    # 需求文档
│   ├── 03_DESIGN.md          # 设计文档
│   ├── 04_PRODUCT.md         # 产品文档
│   └── 05_DEVELOPMENT.md     # 开发日志
├── src/                      # 源代码
│   ├── __init__.py
│   ├── sampling.py           # 采样 (奈奎斯特/过采样/欠采样)
│   ├── quantization.py       # 量化 (均匀/非均匀)
│   ├── reconstruction.py     # 重建 (ZOH/FOH/sinc)
│   ├── aliasing.py           # 混叠与抗混叠滤波
│   ├── audio_sampling.py     # 音频采样应用
│   ├── image_sampling.py     # 图像采样应用
│   └── visualization.py      # 可视化工具
├── tests/                    # 测试代码
│   ├── test_sampling.py
│   ├── test_quantization.py
│   ├── test_reconstruction.py
│   ├── test_aliasing.py
│   ├── test_audio_sampling.py
│   └── test_image_sampling.py
└── examples/                 # 示例代码
    ├── sampling_demo.py      # 采样演示
    ├── quantization_demo.py  # 量化演示
    ├── reconstruction_demo.py # 重建演示
    ├── aliasing_demo.py      # 混叠演示
    ├── audio_demo.py         # 音频采样演示
    └── image_demo.py         # 图像采样演示
```

## 快速开始

### 环境要求

- Python 3.8+
- NumPy
- SciPy (可选，用于抗混叠滤波)
- Matplotlib (可选，用于可视化)

### 安装依赖

```bash
pip install numpy scipy matplotlib
```

### 运行示例

```bash
cd projects/signal-sampling

# 采样演示
python examples/sampling_demo.py

# 量化演示
python examples/quantization_demo.py

# 重建演示
python examples/reconstruction_demo.py

# 混叠演示
python examples/aliasing_demo.py

# 音频采样演示
python examples/audio_demo.py

# 图像采样演示
python examples/image_demo.py
```

### 运行测试

```bash
cd projects/signal-sampling
python -m pytest tests/ -v
```

## 核心模块

### 1. 采样

实现奈奎斯特定理、过采样和欠采样。

```python
from src.sampling import (
    SamplingConfig,
    nyquist_sample,
    oversample,
    undersample,
    calculate_nyquist_rate,
)

# 计算奈奎斯特率
nyquist_rate = calculate_nyquist_rate(1000)  # 2000 Hz

# 奈奎斯特采样
signal_func = lambda t: np.sin(2 * np.pi * 100 * t)
t_sampled, samples = nyquist_sample(signal_func, f_signal=100, fs=250, duration=0.1)

# 过采样
t_sampled, samples, fs = oversample(signal_func, f_signal=100, oversampling_factor=4, duration=0.1)

# 欠采样 (产生混叠)
t_sampled, samples, alias_freq = undersample(signal_func, f_signal=100, fs=80, duration=0.1)
print(f"混叠频率: {alias_freq} Hz")
```

### 2. 量化

实现均匀量化和非均匀量化 (mu律/A律)。

```python
from src.quantization import (
    UniformQuantizer,
    NonUniformQuantizer,
    mu_law_quantizer,
    a_law_quantizer,
)

# 均匀量化
quantizer = UniformQuantizer(bits=8, vmin=-1.0, vmax=1.0)
quantized, indices = quantizer.quantize(signal)
sqnr = quantizer.sqnr(signal)
print(f"SQNR: {sqnr:.2f} dB")
print(f"理论 SQNR: {quantizer.theoretical_sqnr:.2f} dB")

# 非均匀量化 (mu律)
non_uniform = NonUniformQuantizer(bits=8, mu=255.0, vmin=-1.0, vmax=1.0)
quantized, indices = non_uniform.quantize(signal)

# mu律量化 (便捷函数)
quantized, indices = mu_law_quantizer(signal, bits=8, mu=255.0)
```

### 3. 重建

实现零阶保持、一阶保持和 sinc 插值重建。

```python
from src.reconstruction import (
    zero_order_hold,
    first_order_hold,
    sinc_interpolation,
    reconstruct_signal,
    compare_reconstruction,
)

# 零阶保持
reconstructed = zero_order_hold(t_sampled, samples, t_continuous)

# 一阶保持
reconstructed = first_order_hold(t_sampled, samples, t_continuous)

# sinc 插值 (理想重建)
reconstructed = sinc_interpolation(t_sampled, samples, t_continuous, fs)

# 统一接口
reconstructed = reconstruct_signal(t_sampled, samples, t_continuous, method='sinc')

# 比较不同方法
results = compare_reconstruction(t_sampled, samples, t_continuous, original, fs)
for method, data in results.items():
    print(f"{method}: MSE={data['mse']:.8f}, SNR={data['snr_db']:.2f} dB")
```

### 4. 混叠与抗混叠

演示混叠现象和抗混叠滤波。

```python
from src.aliasing import (
    demonstrate_aliasing,
    anti_aliasing_filter,
    compute_spectrum,
    show_aliasing_effect,
)

# 混叠演示
result = demonstrate_aliasing(f_signal=100, fs=80, duration=0.1)
print(f"混叠频率: {result['alias_freq']} Hz")

# 抗混叠滤波
filtered = anti_aliasing_filter(signal, fs=1000, cutoff_freq=100)

# 频谱分析
freqs, magnitude = compute_spectrum(signal, fs=1000)
```

### 5. 音频采样

音频信号的采样和量化。

```python
from src.audio_sampling import AudioSampler, resample_audio

# 创建音频采样器
sampler = AudioSampler.from_preset('cd')  # 44100 Hz, 16 bit, 2 channels
print(sampler.info)

# 采样和量化
t_sampled, samples = sampler.sample(signal, t)
quantized, indices = sampler.quantize(samples)

# 重采样
resampled, fs = resample_audio(samples, fs_original=44100, fs_target=22050)
```

### 6. 图像采样

图像的降采样和上采样。

```python
from src.image_sampling import ImageSampler, downsample_image, upsample_image

# 降采样
sampler = ImageSampler(image)
downsampled = sampler.downsample(4, method='average', anti_aliasing=True)

# 上采样
upsampled = sampler.upsample(4, method='bilinear')

# 便捷函数
downsampled = downsample_image(image, factor=4, anti_aliasing=True)
upsampled = upsample_image(image, factor=4, method='bilinear')
```

## 关键概念总结

### 奈奎斯特定理

| 概念 | 公式 | 说明 |
|------|------|------|
| 奈奎斯特率 | fs_min = 2 * fmax | 完美重建的最低采样率 |
| 奈奎斯特频率 | fN = fs / 2 | 采样率的一半 |
| 混叠频率 | f_alias = \|f - k*fs\| | 欠采样产生的假频率 |

### 量化

| 量化类型 | 位数 | SQNR (dB) | 适用场景 |
|----------|------|-----------|----------|
| 4 bit | 4 | ~25.8 | 低质量语音 |
| 8 bit | 8 | ~49.9 | 电话、radio |
| 16 bit | 16 | ~98.1 | CD 音质 |
| 24 bit | 24 | ~146.2 | 专业录音 |

### 重建方法

| 方法 | 特点 | 计算复杂度 | 质量 |
|------|------|------------|------|
| 零阶保持 | 阶梯波形，硬件友好 | O(n) | 一般 |
| 一阶保持 | 折线波形，较平滑 | O(n) | 较好 |
| sinc 插值 | 理想重建，完美恢复 | O(n*m) | 最好 |

## 参考资源

- 《信号与系统》- 奥本海姆
- 《数字信号处理》- 奥本海姆
- 《离散时间信号处理》- 奥本海姆
- [MIT OpenCourseWare - Signals and Systems](https://ocw.mit.edu/resources/res-6-007-signals-and-systems-spring-2011/)
