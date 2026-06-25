# 信号采样重建 - 设计文档

## 1. 系统架构

### 1.1 模块划分

```
signal-sampling/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── sampling.py          # 采样模块
│   ├── quantization.py      # 量化模块
│   ├── reconstruction.py    # 重建模块
│   ├── aliasing.py          # 混叠模块
│   ├── audio_sampling.py    # 音频采样模块
│   ├── image_sampling.py    # 图像采样模块
│   └── visualization.py     # 可视化模块
├── tests/                   # 测试模块
└── examples/                # 示例代码
```

### 1.2 依赖关系

```
visualization (可选)
    ↓
sampling ← quantization ← reconstruction
    ↓           ↓              ↓
aliasing ← audio_sampling ← image_sampling
```

### 1.3 核心类图

```python
# 采样配置
@dataclass
class SamplingConfig:
    fs: float          # 采样频率
    duration: float    # 持续时间
    f_signal: float    # 信号频率

# 量化器
class UniformQuantizer:
    bits: int
    vmin: float
    vmax: float

class NonUniformQuantizer:
    bits: int
    mu: float
    vmin: float
    vmax: float

# 音频采样器
class AudioSampler:
    fs: float
    bits: int
    channels: int
    quantizer: UniformQuantizer

# 图像采样器
class ImageSampler:
    image: np.ndarray
```

## 2. 详细设计

### 2.1 采样模块 (sampling.py)

#### 2.1.1 数据结构

```python
@dataclass
class SamplingConfig:
    """采样配置"""
    fs: float          # 采样频率 (Hz)
    duration: float    # 采样持续时间 (秒)
    f_signal: float    # 信号频率 (Hz)

    @property
    def nyquist_rate(self) -> float:
        """奈奎斯特率"""
        return 2.0 * self.f_signal

    @property
    def oversampling_ratio(self) -> float:
        """过采样率"""
        return self.fs / self.nyquist_rate

    @property
    def is_nyquist_satisfied(self) -> bool:
        """是否满足奈奎斯特定理"""
        return self.fs >= self.nyquist_rate
```

#### 2.1.2 核心函数

```python
def nyquist_sample(
    signal_func: Callable,
    f_signal: float,
    fs: float,
    duration: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """奈奎斯特采样

    Parameters
    ----------
    signal_func : callable
        信号函数
    f_signal : float
        信号频率 (Hz)
    fs : float
        采样频率 (Hz)
    duration : float
        采样持续时间 (秒)

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (采样时间点, 采样值)
    """
    # 验证奈奎斯特条件
    if fs < 2 * f_signal:
        raise ValueError(...)

    # 计算采样点数
    n_samples = int(fs * duration)

    # 生成采样时间点
    t_sampled = np.arange(n_samples) / fs

    # 采样
    samples = signal_func(t_sampled)

    return t_sampled, samples
```

#### 2.1.3 算法设计

**采样过程**:
1. 验证采样率满足奈奎斯特条件
2. 计算采样点数: n = fs * duration
3. 生成采样时间点: t[n] = n / fs
4. 计算采样值: x[n] = signal_func(t[n])

**过采样**:
1. 计算实际采样率: fs = 2 * f_signal * oversampling_factor
2. 调用 nyquist_sample

**欠采样**:
1. 验证采样率低于奈奎斯特率
2. 计算混叠频率: f_alias = |f - round(f/fs) * fs|

### 2.2 量化模块 (quantization.py)

#### 2.2.1 均匀量化器

```python
class UniformQuantizer:
    """均匀量化器"""

    def __init__(self, bits: int, vmin: float = -1.0, vmax: float = 1.0):
        self.bits = bits
        self.vmin = vmin
        self.vmax = vmax
        self.levels = 2 ** bits
        self.step = (vmax - vmin) / (self.levels - 1)

    def quantize(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """量化信号"""
        # 限幅
        clipped = np.clip(signal, self.vmin, self.vmax)

        # 计算量化索引
        indices = np.round((clipped - self.vmin) / self.step).astype(int)
        indices = np.clip(indices, 0, self.levels - 1)

        # 重建量化值
        quantized = self.vmin + indices * self.step

        return quantized, indices

    def sqnr(self, signal: np.ndarray) -> float:
        """计算 SQNR"""
        quantized, _ = self.quantize(signal)
        noise = signal - quantized

        signal_power = np.mean(signal ** 2)
        noise_power = np.mean(noise ** 2)

        return 10.0 * np.log10(signal_power / noise_power)
```

#### 2.2.2 非均匀量化器

```python
class NonUniformQuantizer:
    """非均匀量化器 (mu律)"""

    def __init__(self, bits: int, mu: float = 255.0, vmin: float = -1.0, vmax: float = 1.0):
        self.bits = bits
        self.mu = mu
        self.vmin = vmin
        self.vmax = vmax
        self.uniform = UniformQuantizer(bits, vmin, vmax)

    def compress(self, signal: np.ndarray) -> np.ndarray:
        """mu律压缩"""
        normalized = (signal - self.vmin) / (self.vmax - self.vmin) * 2 - 1
        compressed = np.sign(normalized) * np.log(1 + self.mu * np.abs(normalized)) / np.log(1 + self.mu)
        return (compressed + 1) / 2 * (self.vmax - self.vmin) + self.vmin

    def expand(self, signal: np.ndarray) -> np.ndarray:
        """mu律扩展"""
        normalized = (signal - self.vmin) / (self.vmax - self.vmin) * 2 - 1
        expanded = np.sign(normalized) * (1.0 / self.mu) * (
            (1 + self.mu) ** np.abs(normalized) - 1
        )
        return (expanded + 1) / 2 * (self.vmax - self.vmin) + self.vmin

    def quantize(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """非均匀量化"""
        compressed = self.compress(signal)
        quantized, indices = self.uniform.quantize(compressed)
        result = self.expand(quantized)
        return result, indices
```

### 2.3 重建模块 (reconstruction.py)

#### 2.3.1 零阶保持

```python
def zero_order_hold(
    t_sampled: np.ndarray,
    samples: np.ndarray,
    t_continuous: np.ndarray,
) -> np.ndarray:
    """零阶保持重建"""
    result = np.zeros_like(t_continuous)
    fs = 1.0 / (t_sampled[1] - t_sampled[0])

    for i, t in enumerate(t_continuous):
        # 找到最近的采样点 (向下取整)
        idx = int(t * fs)
        idx = np.clip(idx, 0, len(samples) - 1)
        result[i] = samples[idx]

    return result
```

#### 2.3.2 一阶保持

```python
def first_order_hold(
    t_sampled: np.ndarray,
    samples: np.ndarray,
    t_continuous: np.ndarray,
) -> np.ndarray:
    """一阶保持重建"""
    return np.interp(t_continuous, t_sampled, samples)
```

#### 2.3.3 sinc 插值

```python
def sinc_interpolation(
    t_sampled: np.ndarray,
    samples: np.ndarray,
    t_continuous: np.ndarray,
    fs: float,
) -> np.ndarray:
    """sinc 插值重建"""
    Ts = 1.0 / fs
    result = np.zeros_like(t_continuous)

    for i, t in enumerate(t_continuous):
        # sinc 插值
        sinc_vals = np.sinc((t - t_sampled) / Ts)
        result[i] = np.sum(samples * sinc_vals)

    return result
```

### 2.4 混叠模块 (aliasing.py)

#### 2.4.1 混叠演示

```python
def demonstrate_aliasing(
    f_signal: float,
    fs: float,
    duration: float = 1.0,
) -> dict:
    """演示混叠现象"""
    # 连续时间轴
    t_continuous = np.linspace(0, duration, 10000)
    signal_continuous = np.sin(2 * np.pi * f_signal * t_continuous)

    # 采样
    n_samples = int(fs * duration)
    t_sampled = np.arange(n_samples) / fs
    samples = np.sin(2 * np.pi * f_signal * t_sampled)

    # 计算混叠频率
    alias_freq = _calculate_alias_frequency(f_signal, fs)

    return {
        "t_continuous": t_continuous,
        "signal_continuous": signal_continuous,
        "t_sampled": t_sampled,
        "samples": samples,
        "alias_freq": alias_freq,
    }
```

#### 2.4.2 抗混叠滤波

```python
def anti_aliasing_filter(
    signal: np.ndarray,
    fs: float,
    cutoff_freq: float,
    filter_order: int = 4,
) -> np.ndarray:
    """抗混叠低通滤波器"""
    from scipy.signal import butter, filtfilt

    nyquist = fs / 2
    normalized_cutoff = cutoff_freq / nyquist

    b, a = butter(filter_order, normalized_cutoff, btype='low')
    filtered = filtfilt(b, a, signal)

    return filtered
```

### 2.5 音频采样模块 (audio_sampling.py)

#### 2.5.1 音频采样器

```python
class AudioSampler:
    """音频采样器"""

    SAMPLE_RATES = {
        "telephone": 8000,
        "radio": 22050,
        "cd": 44100,
        "dvd": 48000,
        "studio": 96000,
    }

    def __init__(self, fs: float = 44100, bits: int = 16, channels: int = 1):
        self.fs = fs
        self.bits = bits
        self.channels = channels
        self.quantizer = UniformQuantizer(bits, vmin=-1.0, vmax=1.0)

    def sample(self, signal: np.ndarray, t: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """采样"""
        return sample_signal(t, signal, self.fs)

    def quantize(self, samples: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """量化"""
        max_val = np.max(np.abs(samples))
        normalized = samples / max_val if max_val > 0 else samples
        quantized, indices = self.quantizer.quantize(normalized)
        return quantized * max_val if max_val > 0 else quantized, indices

    def encode(self, samples: np.ndarray) -> np.ndarray:
        """PCM 编码"""
        ...

    def decode(self, pcm: np.ndarray) -> np.ndarray:
        """PCM 解码"""
        ...
```

### 2.6 图像采样模块 (image_sampling.py)

#### 2.6.1 图像采样器

```python
class ImageSampler:
    """图像采样器"""

    def __init__(self, image: np.ndarray):
        self.image = image.astype(np.float64)

    def downsample(self, factor: int, method: str = 'average', anti_aliasing: bool = True) -> np.ndarray:
        """降采样"""
        image = self.image.copy()

        if anti_aliasing:
            image = _box_blur(image, kernel_size=factor)

        if method == 'average':
            # 块平均
            ...
        elif method == 'subsample':
            # 直接抽取
            ...

    def upsample(self, factor: int, method: str = 'bilinear') -> np.ndarray:
        """上采样"""
        if method == 'nearest':
            return self._nearest_interpolation(...)
        elif method == 'bilinear':
            return self._bilinear_interpolation(...)
        elif method == 'bicubic':
            return self._bicubic_interpolation(...)
```

## 3. 数据流设计

### 3.1 采样流程

```
连续信号 x(t)
    ↓
采样配置 (fs, duration)
    ↓
采样函数 (nyquist_sample/oversample/undersample)
    ↓
采样值 x[n] = x(nTs)
    ↓
返回 (t_sampled, samples)
```

### 3.2 量化流程

```
采样值 x[n]
    ↓
量化器 (UniformQuantizer/NonUniformQuantizer)
    ↓
量化索引 indices[n]
    ↓
量化值 Q(x[n]) = vmin + indices[n] * step
    ↓
返回 (quantized, indices)
```

### 3.3 重建流程

```
采样值 x[n]
    ↓
重建方法 (ZOH/FOH/sinc)
    ↓
重建信号 x_r(t)
    ↓
返回 reconstructed
```

## 4. 错误处理设计

### 4.1 输入验证

```python
def nyquist_sample(signal_func, f_signal, fs, duration):
    # 验证采样率
    if fs < 2 * f_signal:
        raise ValueError(
            f"采样率 {fs} Hz 低于奈奎斯特率 {2*f_signal} Hz，会产生混叠"
        )

    # 验证持续时间
    if duration <= 0:
        raise ValueError("持续时间必须为正数")

    # 验证信号频率
    if f_signal <= 0:
        raise ValueError("信号频率必须为正数")
```

### 4.2 边界处理

```python
def zero_order_hold(t_sampled, samples, t_continuous):
    # 处理边界
    idx = np.clip(idx, 0, len(samples) - 1)
    ...
```

### 4.3 数值稳定性

```python
def sqnr(self, signal):
    # 避免除零
    if noise_power == 0:
        return float('inf')
    ...
```

## 5. 性能优化设计

### 5.1 向量化

```python
# 差的实现
for i in range(len(signal)):
    result[i] = func(signal[i])

# 好的实现
result = func(signal)
```

### 5.2 内存优化

```python
# 使用 view 而不是 copy
samples = signal[::step]  # view
```

### 5.3 计算优化

```python
# sinc 插值优化
# 预计算 sinc 值
sinc_matrix = np.sinc((t_continuous[:, None] - t_sampled[None, :]) / Ts)
result = sinc_matrix @ samples
```

## 6. 测试设计

### 6.1 单元测试

```python
class TestNyquistSample:
    def test_basic_sampling(self):
        """测试基本采样"""
        ...

    def test_nyquist_rate_sampling(self):
        """测试奈奎斯特率采样"""
        ...

    def test_below_nyquist_raises(self):
        """测试低于奈奎斯特率应抛出异常"""
        ...
```

### 6.2 集成测试

```python
class TestSamplingPipeline:
    def test_sample_quantize_reconstruct(self):
        """测试采样-量化-重建流水线"""
        ...
```

### 6.3 性能测试

```python
class TestPerformance:
    def test_sinc_interpolation_speed(self):
        """测试 sinc 插值速度"""
        ...
```

## 7. 可视化设计

### 7.1 采样可视化

```python
def plot_sampling(t_continuous, signal, t_sampled, samples):
    # 绘制原始信号
    plt.plot(t_continuous, signal, 'b-', label='原始信号')

    # 绘制采样点
    plt.stem(t_sampled, samples, 'r-', label='采样点')
```

### 7.2 量化可视化

```python
def plot_quantization(signal, quantized, bits):
    # 绘制信号对比
    plt.plot(signal, 'b-', label='原始信号')
    plt.plot(quantized, 'r-', label=f'量化信号 ({bits} bit)')
```

### 7.3 重建可视化

```python
def plot_reconstruction(t_sampled, samples, t_continuous, reconstructed_dict):
    # 绘制采样点
    plt.plot(t_sampled, samples, 'ko', label='采样点')

    # 绘制各方法重建结果
    for method, signal in reconstructed_dict.items():
        plt.plot(t_continuous, signal, label=method)
```
