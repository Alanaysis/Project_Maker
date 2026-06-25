# 信号采样重建 - 产品文档

## 1. 产品概述

### 1.1 产品定位

信号采样重建是一个教学型 Python 库，用于:
- 学习信号采样与重建的核心原理
- 理解奈奎斯特定理的工程意义
- 掌握量化、重建、混叠等概念
- 通过实际代码加深理解

### 1.2 目标用户

| 用户类型 | 需求 | 使用场景 |
|----------|------|----------|
| 学生 | 学习信号处理 | 课程作业、实验 |
| 教师 | 教学演示 | 课堂教学、实验指导 |
| 工程师 | 快速验证 | 原型开发、算法验证 |
| 爱好者 | 兴趣学习 | 自学、项目实践 |

### 1.3 核心价值

1. **从零实现**: 不依赖信号处理库，深入理解算法
2. **代码清晰**: 完整注释，易于理解
3. **覆盖全面**: 采样、量化、重建、混叠、应用
4. **即学即用**: 丰富的示例和测试

## 2. 功能特性

### 2.1 采样功能

#### 奈奎斯特采样
- 以奈奎斯特率或更高采样率采样
- 自动验证采样率条件
- 返回采样时间点和采样值

#### 过采样
- 以远高于奈奎斯特率的频率采样
- 可指定过采样倍数
- 降低混叠风险

#### 欠采样
- 以低于奈奎斯特率的频率采样
- 自动计算混叠频率
- 用于演示混叠现象

### 2.2 量化功能

#### 均匀量化
- 等间隔划分量化区间
- 可配置量化位数 (4-24 bit)
- 计算 SQNR (信号量化噪声比)
- 验证理论 SQNR 公式

#### 非均匀量化
- mu 律压缩/扩展
- A 律压缩/扩展
- 改善小信号 SQNR
- 模拟电话系统量化

### 2.3 重建功能

#### 零阶保持 (ZOH)
- 每个采样值保持到下一个采样点
- 产生阶梯状波形
- 硬件友好，用于 DAC

#### 一阶保持 (FOH)
- 采样点之间线性插值
- 产生折线波形
- 比 ZOH 更平滑

#### sinc 插值
- 理想重建方法
- 完美恢复带限信号
- 计算量较大

### 2.4 混叠功能

#### 混叠演示
- 演示欠采样产生的混叠
- 计算混叠频率
- 可视化混叠效果

#### 抗混叠滤波
- 巴特沃斯低通滤波器
- 可配置截止频率和阶数
- 零相位滤波

#### 频谱分析
- 计算信号频谱
- 识别峰值频率
- 分析混叠效果

### 2.5 音频采样功能

#### 音频采样器
- 支持多种采样率预设
- 支持多种量化位数
- 支持单声道/立体声
- PCM 编码/解码

#### 重采样
- sinc 插值重采样
- 支持上采样和下采样
- 保持信号质量

### 2.6 图像采样功能

#### 降采样
- 平均法降采样
- 抽取法降采样
- 抗混叠滤波选项

#### 上采样
- 最近邻插值
- 双线性插值
- 双三次插值

## 3. 使用指南

### 3.1 快速开始

```python
from src.sampling import nyquist_sample, calculate_nyquist_rate
import numpy as np

# 计算奈奎斯特率
f_signal = 1000  # Hz
nyquist_rate = calculate_nyquist_rate(f_signal)
print(f"奈奎斯特率: {nyquist_rate} Hz")

# 采样
signal_func = lambda t: np.sin(2 * np.pi * f_signal * t)
t_sampled, samples = nyquist_sample(signal_func, f_signal, fs=4000, duration=0.01)
print(f"采样点数: {len(samples)}")
```

### 3.2 采样演示

```python
from src.sampling import oversample, undersample

# 过采样
t, samples, fs = oversample(signal_func, f_signal=100, oversampling_factor=4, duration=0.1)
print(f"过采样率: {fs} Hz")

# 欠采样
t, samples, alias_freq = undersample(signal_func, f_signal=100, fs=80, duration=0.1)
print(f"混叠频率: {alias_freq} Hz")
```

### 3.3 量化演示

```python
from src.quantization import UniformQuantizer, NonUniformQuantizer

# 均匀量化
quantizer = UniformQuantizer(bits=8, vmin=-1.0, vmax=1.0)
signal = np.sin(np.linspace(0, 2 * np.pi, 1000))
quantized, indices = quantizer.quantize(signal)
sqnr = quantizer.sqnr(signal)
print(f"SQNR: {sqnr:.2f} dB")

# 非均匀量化
non_uniform = NonUniformQuantizer(bits=8, mu=255.0, vmin=-1.0, vmax=1.0)
quantized, indices = non_uniform.quantize(signal)
sqnr = non_uniform.sqnr(signal)
print(f"SQNR (mu律): {sqnr:.2f} dB")
```

### 3.4 重建演示

```python
from src.reconstruction import zero_order_hold, first_order_hold, sinc_interpolation

# 零阶保持
reconstructed = zero_order_hold(t_sampled, samples, t_continuous)

# 一阶保持
reconstructed = first_order_hold(t_sampled, samples, t_continuous)

# sinc 插值
reconstructed = sinc_interpolation(t_sampled, samples, t_continuous, fs)
```

### 3.5 混叠演示

```python
from src.aliasing import demonstrate_aliasing, anti_aliasing_filter

# 混叠演示
result = demonstrate_aliasing(f_signal=100, fs=80, duration=0.1)
print(f"混叠频率: {result['alias_freq']} Hz")

# 抗混叠滤波
filtered = anti_aliasing_filter(signal, fs=1000, cutoff_freq=100)
```

### 3.6 音频采样演示

```python
from src.audio_sampling import AudioSampler, resample_audio

# 创建音频采样器
sampler = AudioSampler.from_preset('cd')
print(sampler.info)

# 采样和量化
t_sampled, samples = sampler.sample(signal, t)
quantized, indices = sampler.quantize(samples)

# 重采样
resampled, fs = resample_audio(samples, 44100, 22050)
```

### 3.7 图像采样演示

```python
from src.image_sampling import ImageSampler, downsample_image, upsample_image

# 降采样
sampler = ImageSampler(image)
downsampled = sampler.downsample(4, method='average', anti_aliasing=True)

# 上采样
upsampled = sampler.upsample(4, method='bilinear')
```

## 4. API 参考

### 4.1 采样模块

#### calculate_nyquist_rate(fmax)
计算奈奎斯特率。

**Parameters**:
- `fmax` (float): 信号最高频率分量 (Hz)

**Returns**:
- float: 奈奎斯特率 (Hz)

#### nyquist_sample(signal_func, f_signal, fs, duration)
奈奎斯特采样。

**Parameters**:
- `signal_func` (callable): 信号函数
- `f_signal` (float): 信号频率 (Hz)
- `fs` (float): 采样频率 (Hz)
- `duration` (float): 采样持续时间 (秒)

**Returns**:
- Tuple[np.ndarray, np.ndarray]: (采样时间点, 采样值)

#### oversample(signal_func, f_signal, oversampling_factor, duration)
过采样。

**Parameters**:
- `signal_func` (callable): 信号函数
- `f_signal` (float): 信号频率 (Hz)
- `oversampling_factor` (int): 过采样倍数
- `duration` (float): 采样持续时间 (秒)

**Returns**:
- Tuple[np.ndarray, np.ndarray, float]: (采样时间点, 采样值, 采样频率)

#### undersample(signal_func, f_signal, fs, duration)
欠采样。

**Parameters**:
- `signal_func` (callable): 信号函数
- `f_signal` (float): 信号频率 (Hz)
- `fs` (float): 采样频率 (Hz)
- `duration` (float): 采样持续时间 (秒)

**Returns**:
- Tuple[np.ndarray, np.ndarray, float]: (采样时间点, 采样值, 混叠频率)

### 4.2 量化模块

#### UniformQuantizer(bits, vmin, vmax)
均匀量化器。

**Parameters**:
- `bits` (int): 量化位数
- `vmin` (float): 最小量化值
- `vmax` (float): 最大量化值

**Methods**:
- `quantize(signal)`: 量化信号
- `dequantize(indices)`: 反量化
- `sqnr(signal)`: 计算 SQNR

#### NonUniformQuantizer(bits, mu, vmin, vmax)
非均匀量化器。

**Parameters**:
- `bits` (int): 量化位数
- `mu` (float): mu 律压缩参数
- `vmin` (float): 最小量化值
- `vmax` (float): 最大量化值

**Methods**:
- `compress(signal)`: mu 律压缩
- `expand(signal)`: mu 律扩展
- `quantize(signal)`: 非均匀量化
- `sqnr(signal)`: 计算 SQNR

### 4.3 重建模块

#### zero_order_hold(t_sampled, samples, t_continuous)
零阶保持重建。

**Parameters**:
- `t_sampled` (np.ndarray): 采样时间点
- `samples` (np.ndarray): 采样值
- `t_continuous` (np.ndarray): 重建的时间轴

**Returns**:
- np.ndarray: 重建的信号

#### first_order_hold(t_sampled, samples, t_continuous)
一阶保持重建。

**Parameters**:
- `t_sampled` (np.ndarray): 采样时间点
- `samples` (np.ndarray): 采样值
- `t_continuous` (np.ndarray): 重建的时间轴

**Returns**:
- np.ndarray: 重建的信号

#### sinc_interpolation(t_sampled, samples, t_continuous, fs)
sinc 插值重建。

**Parameters**:
- `t_sampled` (np.ndarray): 采样时间点
- `samples` (np.ndarray): 采样值
- `t_continuous` (np.ndarray): 重建的时间轴
- `fs` (float): 采样频率

**Returns**:
- np.ndarray: 重建的信号

### 4.4 混叠模块

#### demonstrate_aliasing(f_signal, fs, duration)
演示混叠现象。

**Parameters**:
- `f_signal` (float): 信号频率 (Hz)
- `fs` (float): 采样频率 (Hz)
- `duration` (float): 采样持续时间 (秒)

**Returns**:
- dict: 包含原始信号、采样点、混叠频率等信息

#### anti_aliasing_filter(signal, fs, cutoff_freq, filter_order)
抗混叠低通滤波器。

**Parameters**:
- `signal` (np.ndarray): 输入信号
- `fs` (float): 采样频率 (Hz)
- `cutoff_freq` (float): 截止频率 (Hz)
- `filter_order` (int): 滤波器阶数

**Returns**:
- np.ndarray: 滤波后的信号

## 5. 示例代码

### 5.1 采样演示

```python
# examples/sampling_demo.py
from src.sampling import nyquist_sample, oversample, undersample
import numpy as np

# 奈奎斯特采样
f_signal = 100
fs = 250
signal_func = lambda t: np.sin(2 * np.pi * f_signal * t)
t_sampled, samples = nyquist_sample(signal_func, f_signal, fs, duration=0.1)
print(f"采样点数: {len(samples)}")

# 过采样
t, samples, fs = oversample(signal_func, f_signal, oversampling_factor=4, duration=0.1)
print(f"过采样率: {fs} Hz")

# 欠采样
t, samples, alias_freq = undersample(signal_func, f_signal, fs=80, duration=0.1)
print(f"混叠频率: {alias_freq} Hz")
```

### 5.2 量化演示

```python
# examples/quantization_demo.py
from src.quantization import UniformQuantizer, NonUniformQuantizer
import numpy as np

signal = np.sin(np.linspace(0, 2 * np.pi, 1000))

# 均匀量化
for bits in [4, 8, 12, 16]:
    quantizer = UniformQuantizer(bits=bits, vmin=-1.0, vmax=1.0)
    sqnr = quantizer.sqnr(signal)
    print(f"{bits} bit: SQNR = {sqnr:.2f} dB")

# 非均匀量化
non_uniform = NonUniformQuantizer(bits=8, mu=255.0, vmin=-1.0, vmax=1.0)
sqnr = non_uniform.sqnr(signal)
print(f"mu律 8 bit: SQNR = {sqnr:.2f} dB")
```

### 5.3 重建演示

```python
# examples/reconstruction_demo.py
from src.reconstruction import zero_order_hold, first_order_hold, sinc_interpolation
import numpy as np

# 采样
fs = 50
f_signal = 5
t_sampled = np.arange(int(fs * 0.5)) / fs
samples = np.sin(2 * np.pi * f_signal * t_sampled)

# 重建
t_continuous = np.linspace(0, 0.5, 500)
zoh = zero_order_hold(t_sampled, samples, t_continuous)
foh = first_order_hold(t_sampled, samples, t_continuous)
sinc = sinc_interpolation(t_sampled, samples, t_continuous, fs)
```

## 6. 常见问题

### 6.1 采样率选择

**Q: 如何选择合适的采样率?**

A: 首先确定信号的最高频率分量 fmax，然后:
1. 计算奈奎斯特率: fs_min = 2 * fmax
2. 考虑抗混叠滤波器的过渡带: fs = 2 * (fmax + transition_band)
3. 实际应用中通常选择 2.5-4 倍的 fmax

### 6.2 量化位数选择

**Q: 如何选择合适的量化位数?**

A: 根据应用需求:
1. 语音: 8-12 bit
2. 音乐: 16-24 bit
3. 图像: 8-16 bit

每增加 1 bit，SQNR 增加约 6 dB。

### 6.3 重建方法选择

**Q: 如何选择合适的重建方法?**

A: 根据应用场景:
1. 硬件 DAC: 零阶保持 (简单)
2. 软件处理: sinc 插值 (精确)
3. 实时系统: 一阶保持 (折中)

### 6.4 混叠避免

**Q: 如何避免混叠?**

A: 两种方法:
1. 提高采样率 (过采样)
2. 使用抗混叠滤波器

实际应用中通常两者结合。

## 7. 版本历史

### v1.0.0 (2026-06-24)
- 初始版本
- 实现采样、量化、重建核心模块
- 实现混叠和抗混叠滤波
- 实现音频和图像采样应用
- 完整的测试和文档
