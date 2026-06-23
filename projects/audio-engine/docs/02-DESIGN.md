# 02 - 设计文档

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Audio Engine                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   FFT 模块   │  │  滤波器模块  │  │  特效模块    │         │
│  │  (核心变换)  │  │  (频域处理)  │  │  (音频效果)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              AudioSignal (信号表示)                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  混音器模块  │  │  降噪模块    │  │  均衡器模块  │         │
│  │  (多轨混合)  │  │  (噪声消除)  │  │  (频率均衡)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 核心数据流

```
音频输入 → AudioSignal → FFT → 频域处理 → IFFT → AudioSignal → 音频输出
                │
                ▼
        ┌───────────────┐
        │  可选处理链    │
        │  - 滤波       │
        │  - 降噪       │
        │  - 均衡       │
        │  - 特效       │
        └───────────────┘
```

## 模块设计

### 1. FFT 模块 (fft.py)

#### 类设计

```python
class FFT:
    """快速傅里叶变换"""

    @staticmethod
    def transform(x: np.ndarray) -> np.ndarray:
        """时域 → 频域"""

    @staticmethod
    def magnitude_spectrum(x: np.ndarray) -> np.ndarray:
        """计算幅度谱"""

    @staticmethod
    def power_spectrum(x: np.ndarray) -> np.ndarray:
        """计算功率谱"""

    @staticmethod
    def phase_spectrum(x: np.ndarray) -> np.ndarray:
        """计算相位谱"""

class IFFT:
    """逆快速傅里叶变换"""

    @staticmethod
    def transform(X: np.ndarray) -> np.ndarray:
        """频域 → 时域"""

    @staticmethod
    def transform_real(X: np.ndarray) -> np.ndarray:
        """频域 → 时域（只返回实部）"""
```

#### 算法选择

**Cooley-Tukey FFT 算法**：
- 分治策略
- 将 N 点 DFT 分解为两个 N/2 点 DFT
- 通过蝶形运算合并

**实现细节**：
1. 检查输入长度，自动填充到 2 的幂次
2. 递归实现（清晰易懂）
3. 使用旋转因子 `W_N^k = e^(-2πik/N)`

### 2. AudioSignal 类 (audio_signal.py)

#### 设计原则

- **不可变性**：操作返回新对象，不修改原对象
- **链式操作**：支持方法链
- **类型安全**：使用类型注解

#### 属性

```python
class AudioSignal:
    data: np.ndarray          # 采样数据
    sample_rate: int          # 采样率
    channels: int             # 通道数

    @property
    def duration(self) -> float    # 时长
    @property
    def num_samples(self) -> int   # 采样点数
    @property
    def nyquist_freq(self) -> float # 奈奎斯特频率
```

#### 工厂方法

```python
@classmethod
def from_tone(cls, frequency, duration, ...) -> AudioSignal
    """生成正弦波"""

@classmethod
def from_noise(cls, duration, ...) -> AudioSignal
    """生成白噪声"""

@classmethod
def from_wav(cls, filepath) -> AudioSignal
    """从文件加载"""
```

#### 操作方法

```python
def normalize(self, target_level) -> AudioSignal
def mix(self, other, ratio) -> AudioSignal
def apply_gain(self, gain_db) -> AudioSignal
def trim(self, start, end) -> AudioSignal
def get_spectrum(self) -> Tuple[ndarray, ndarray]
```

### 3. 滤波器模块 (filters.py)

#### 继承结构

```
Filter (基类)
├── LowPassFilter (低通)
├── HighPassFilter (高通)
├── BandPassFilter (带通)
└── NotchFilter (陷波)
```

#### 基类设计

```python
class Filter:
    def _create_filter_mask(self, n_samples) -> np.ndarray:
        """创建频率响应掩码（子类实现）"""

    def apply(self, signal: AudioSignal) -> AudioSignal:
        """应用滤波器"""
        # 1. FFT 变换
        # 2. 创建滤波器掩码
        # 3. 频域乘法
        # 4. IFFT 变换

    def get_frequency_response(self, n_points) -> Tuple:
        """获取频率响应曲线"""
```

#### 滤波器设计

**理想滤波器**（硬截止）：
```python
# 低通
mask = (freqs <= cutoff).astype(float)

# 高通
mask = (freqs >= cutoff).astype(float)
```

**平滑滤波器**（余弦过渡）：
```python
# 过渡带使用余弦函数
if f in transition_band:
    normalized = (f - f_low) / (f_high - f_low)
    mask = 0.5 * (1 + cos(π * normalized))
```

### 4. 特效模块 (effects.py)

#### 继承结构

```
AudioEffect (基类)
├── Delay (延迟)
├── Reverb (混响)
├── Chorus (合唱)
├── Distortion (失真)
└── Compressor (压缩器)
```

#### 延迟设计

```python
class Delay(AudioEffect):
    def apply(self, signal):
        # 1. 计算延迟采样数
        # 2. 创建延迟缓冲区
        # 3. 应用反馈延迟
        # 4. 混合干湿信号
```

#### 混响设计（Schroeder 模型）

```python
class Reverb(AudioEffect):
    # 4 个并行梳状滤波器
    comb_delays = [0.0297, 0.0371, 0.0411, 0.0437]
    comb_gains = [0.75, 0.73, 0.71, 0.69]

    # 2 个串联全通滤波器
    allpass_delays = [0.005, 0.0017]
    allpass_gains = [0.7, 0.7]

    def apply(self, signal):
        # 1. 并行梳状滤波
        # 2. 混合梳状输出
        # 3. 串联全通滤波
        # 4. 混合干湿信号
```

### 5. 混音器模块 (mixer.py)

#### 类设计

```python
class MixerTrack:
    signal: AudioSignal
    name: str
    volume: float      # 0-1
    pan: float         # -1 (左) 到 1 (右)
    mute: bool
    solo: bool

class Mixer:
    tracks: List[MixerTrack]
    master_volume: float

    def add_track(self, signal, name, volume, pan) -> int
    def render(self) -> Tuple[AudioSignal, AudioSignal]
    def render_to_mono(self) -> AudioSignal
    def render_to_stereo(self) -> AudioSignal
```

#### 声像定位算法

使用正弦定律：
```python
angle = (pan + 1) / 2 * π / 2
left = signal * cos(angle)
right = signal * sin(angle)
```

#### 限幅处理

使用软限幅（tanh）防止削波：
```python
output = tanh(mixed_signal)
```

### 6. 降噪模块 (denoiser.py)

#### 频谱减法算法

```python
class Denoiser:
    def estimate_noise(self, signal, noise_duration):
        """从静音段估计噪声频谱"""

    def apply(self, signal):
        """应用降噪"""
        # 1. 分帧、加窗
        # 2. FFT 变换
        # 3. 频谱减法
        # 4. 应用谱下限
        # 5. IFFT 变换
        # 6. 重叠相加
```

#### 重叠相加法（OLA）

```
帧1:   [████████]
帧2:         [████████]
帧3:               [████████]
输出: [████████████████████████]
```

### 7. 均衡器模块 (equalizer.py)

#### 参数均衡器

```python
class EQBand:
    frequency: float   # 中心频率
    gain_db: float     # 增益 (dB)
    q_factor: float    # 品质因子

class Equalizer:
    bands: List[EQBand]

    def apply(self, signal):
        # 1. FFT 变换
        # 2. 计算总频率响应
        # 3. 应用均衡
        # 4. IFFT 变换
```

#### 钟形函数

```python
def bell_response(f, fc, Q, gain):
    normalized = (f² - fc²) / (f * fc / Q)
    bell = 1 / (1 + normalized²)
    return 1 + (gain - 1) * bell
```

## 接口设计

### 统一的处理接口

所有处理模块都遵循相同的接口模式：

```python
class Processor:
    def apply(self, signal: AudioSignal) -> AudioSignal:
        """处理音频信号"""
        pass
```

### 处理链设计

```python
def process_chain(signal: AudioSignal,
                  processors: List[Processor]) -> AudioSignal:
    """应用处理链"""
    result = signal
    for processor in processors:
        result = processor.apply(result)
    return result
```

## 性能考虑

### FFT 优化

1. **缓存旋转因子**：预计算 `W_N^k`
2. **使用 NumPy 向量化**：避免 Python 循环
3. **内存预分配**：减少内存分配开销

### 滤波器优化

1. **频域处理**：比时域卷积快
2. **批量处理**：一次处理整段音频
3. **避免重复计算**：缓存滤波器掩码

### 降噪优化

1. **分帧处理**：减少内存占用
2. **重叠相加**：保证平滑过渡
3. **谱下限**：防止音乐噪声

## 测试策略

### 单元测试

- FFT 正确性验证
- 滤波器频率响应
- 特效参数验证

### 集成测试

- 处理链测试
- 端到端测试

### 性能测试

- FFT 速度基准
- 大文件处理测试
