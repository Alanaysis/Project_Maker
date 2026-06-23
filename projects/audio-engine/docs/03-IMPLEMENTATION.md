# 03 - 实现文档

## 实现概览

本项目使用纯 Python + NumPy 实现音频处理引擎，不依赖外部音频处理库。

## 核心实现

### 1. FFT 实现

#### Cooley-Tukey 算法

```python
def _fft_recursive(x: np.ndarray) -> np.ndarray:
    """递归实现 FFT"""
    N = len(x)

    # 基础情况
    if N == 1:
        return x.copy()

    # 分治：分离偶数项和奇数项
    even = _fft_recursive(x[0::2])
    odd = _fft_recursive(x[1::2])

    # 蝶形运算
    T = np.exp(-2j * np.pi * np.arange(N // 2) / N) * odd

    # 合并结果
    result = np.zeros(N, dtype=complex)
    result[:N // 2] = even + T
    result[N // 2:] = even - T

    return result
```

**关键点**：
1. **分治策略**：将 N 点 DFT 分解为两个 N/2 点 DFT
2. **蝶形运算**：`X[k] = E[k] + W_N^k * O[k]`
3. **旋转因子**：`W_N^k = e^(-2πik/N)`

#### 自动填充

```python
if N & (N - 1) != 0:  # 不是 2 的幂次
    next_power = 1
    while next_power < N:
        next_power <<= 1
    x = np.pad(x, (0, next_power - N))
```

### 2. AudioSignal 实现

#### 信号生成

```python
@classmethod
def from_tone(cls, frequency, duration, sample_rate, amplitude):
    """生成正弦波"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    data = amplitude * np.sin(2 * np.pi * frequency * t)
    return cls(data, sample_rate)
```

#### 归一化

```python
def normalize(self, target_level=0.9):
    max_val = np.max(np.abs(self.data))
    if max_val > 0:
        normalized = self.data * (target_level / max_val)
    return AudioSignal(normalized, self.sample_rate, self.channels)
```

### 3. 滤波器实现

#### 频域滤波

```python
def apply(self, signal: AudioSignal) -> AudioSignal:
    # FFT 变换
    spectrum = FFT.transform(signal.data)
    N = len(spectrum)

    # 创建滤波器掩码
    filter_mask = self._create_filter_mask(N)

    # 频域乘法（时域卷积）
    filtered_spectrum = spectrum * filter_mask

    # IFFT 变换
    filtered_data = IFFT.transform_real(filtered_spectrum)

    return AudioSignal(filtered_data[:len(signal.data)], ...)
```

#### 低通滤波器掩码

```python
def _create_filter_mask(self, n_samples):
    freqs = np.fft.fftfreq(n_samples, 1.0 / self.sample_rate)
    freqs_abs = np.abs(freqs)

    if self.rolloff_width is None:
        # 硬截止
        mask = (freqs_abs <= self.cutoff_freq).astype(float)
    else:
        # 余弦过渡
        mask = np.zeros(n_samples)
        for i in range(n_samples):
            f = freqs_abs[i]
            if f <= self.cutoff_freq - self.rolloff_width / 2:
                mask[i] = 1.0
            elif f >= self.cutoff_freq + self.rolloff_width / 2:
                mask[i] = 0.0
            else:
                normalized = (f - (self.cutoff_freq - self.rolloff_width / 2)) / self.rolloff_width
                mask[i] = 0.5 * (1 + np.cos(np.pi * normalized))
    return mask
```

### 4. 延迟效果实现

```python
def apply(self, signal: AudioSignal) -> AudioSignal:
    data = signal.data.copy()
    delay_samples = int(self.delay_time * self.sample_rate)

    # 创建延迟缓冲区
    delayed = np.zeros(len(data) + delay_samples)
    delayed[:len(data)] = data

    # 应用反馈延迟
    output = data.copy()
    gain = 1.0

    for i in range(1, int(3.0 / self.delay_time) + 1):
        gain *= self.feedback
        if gain < 0.01:
            break

        start = i * delay_samples
        end = start + len(data)
        if end <= len(delayed):
            output += gain * delayed[start:end]

    # 混合干湿信号
    result = (1 - self.mix) * data + self.mix * output[:len(data)]
    return AudioSignal(result, ...)
```

### 5. 混响实现（Schroeder 模型）

```python
class Reverb:
    # 梳状滤波器参数
    comb_delays = [0.0297, 0.0371, 0.0411, 0.0437]
    comb_gains = [0.75, 0.73, 0.71, 0.69]

    # 全通滤波器参数
    allpass_delays = [0.005, 0.0017]
    allpass_gains = [0.7, 0.7]

    def _comb_filter(self, data, delay_time, gain):
        """梳状滤波器"""
        delay_samples = int(delay_time * self.sample_rate * self.room_size)
        output = np.zeros(len(data) + delay_samples)

        for i in range(len(data)):
            if i >= delay_samples:
                output[i] = data[i] + gain * output[i - delay_samples]
            else:
                output[i] = data[i]

        return output[:len(data)]

    def _allpass_filter(self, data, delay_time, gain):
        """全通滤波器"""
        delay_samples = int(delay_time * self.sample_rate)
        output = np.zeros(len(data))

        for i in range(len(data)):
            if i >= delay_samples:
                output[i] = -gain * data[i] + data[i - delay_samples] + gain * output[i - delay_samples]
            else:
                output[i] = data[i]

        return output

    def apply(self, signal):
        # 并行梳状滤波
        comb_outputs = []
        for delay, gain in zip(self.comb_delays, self.comb_gains):
            comb_outputs.append(self._comb_filter(signal.data, delay, gain * (1 - self.damping * 0.5)))

        # 混合
        reverb = np.mean(comb_outputs, axis=0)

        # 串联全通滤波
        for delay, gain in zip(self.allpass_delays, self.allpass_gains):
            reverb = self._allpass_filter(reverb, delay, gain)

        # 混合干湿信号
        result = (1 - self.mix) * signal.data + self.mix * reverb
        return AudioSignal(result, ...)
```

### 6. 降噪实现

#### 频谱减法

```python
def apply(self, signal: AudioSignal) -> AudioSignal:
    data = signal.data.copy()
    output = np.zeros_like(data)
    window = np.hanning(self.frame_size)

    # 重叠相加法
    for start in range(0, len(data) - self.frame_size, self.hop_size):
        # 提取帧并加窗
        frame = data[start:start + self.frame_size]
        windowed = frame * window

        # FFT
        spectrum = FFT.transform(windowed)
        magnitude = np.abs(spectrum[:self.frame_size // 2 + 1])
        phase = np.angle(spectrum[:self.frame_size // 2 + 1])

        # 频谱减法
        magnitude_sq = magnitude ** 2
        noise_sq = self.noise_spectrum[:self.frame_size // 2 + 1]

        clean_sq = magnitude_sq - self.noise_factor * noise_sq

        # 应用谱下限
        clean_sq = np.maximum(clean_sq, self.spectral_floor * magnitude_sq)
        clean_magnitude = np.sqrt(clean_sq)

        # 重建频谱
        clean_spectrum = np.zeros(self.frame_size, dtype=complex)
        clean_spectrum[:self.frame_size // 2 + 1] = clean_magnitude * np.exp(1j * phase)
        clean_spectrum[self.frame_size // 2 + 1:] = np.conj(
            clean_spectrum[self.frame_size // 2 - 1:0:-1]
        )

        # IFFT
        clean_frame = IFFT.transform_real(clean_spectrum)

        # 重叠相加
        output[start:start + self.frame_size] += clean_frame * window

    # 归一化
    window_sum = np.zeros(len(data))
    for start in range(0, len(data) - self.frame_size, self.hop_size):
        window_sum[start:start + self.frame_size] += window ** 2

    output /= np.maximum(window_sum, 1e-10)

    return AudioSignal(output, ...)
```

### 7. 均衡器实现

#### 钟形函数

```python
def _calculate_band_response(self, freqs, band):
    """计算单个频段的频率响应"""
    fc = band.frequency
    gain = band.gain_linear
    Q = band.q_factor

    response = np.ones(len(freqs))
    for i, f in enumerate(freqs):
        if f > 0:
            normalized = (f ** 2 - fc ** 2) / (f * fc / Q)
            bell = 1.0 / (1.0 + normalized ** 2)
            response[i] = 1.0 + (gain - 1.0) * bell

    return response
```

## 关键算法解析

### 蝶形运算图示

```
输入: x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7]

第一级:
x[0]─────┬─────X[0]
         │
x[4]──W0─┴─────X[1]

x[2]─────┬─────X[2]
         │
x[6]──W0─┴─────X[3]

... (类似)

第二级:
组合第一级的输出

第三级:
组合第二级的输出

输出: X[0], X[1], X[2], X[3], X[4], X[5], X[6], X[7]
```

### 重叠相加法

```
帧1:   [AAAA]
帧2:       [BBBB]
帧3:           [CCCC]

重叠区域: AB, BC

输出: [A AB B BC C]
```

## 实现挑战与解决方案

### 1. FFT 长度问题

**问题**：FFT 要求输入长度为 2 的幂次

**解决方案**：
```python
# 自动填充到下一个 2 的幂次
if N & (N - 1) != 0:
    next_power = 1 << (N - 1).bit_length()
    x = np.pad(x, (0, next_power - N))
```

### 2. 相位保持

**问题**：滤波时需要保持相位信息

**解决方案**：
```python
# 分离幅度和相位
magnitude = np.abs(spectrum)
phase = np.angle(spectrum)

# 只修改幅度
filtered_magnitude = magnitude * filter_mask

# 重建频谱
filtered_spectrum = filtered_magnitude * np.exp(1j * phase)
```

### 3. 重叠相加的归一化

**问题**：重叠区域会被重复累加

**解决方案**：
```python
# 计算窗函数的累加
window_sum = np.zeros(len(data))
for start in range(0, len(data) - frame_size, hop_size):
    window_sum[start:start + frame_size] += window ** 2

# 归一化
output /= np.maximum(window_sum, 1e-10)
```

## 代码规范

### 命名规范

- 类名：PascalCase
- 函数名：snake_case
- 常量：UPPER_SNAKE_CASE
- 私有方法：_leading_underscore

### 文档规范

- 每个类都有 docstring
- 每个公共方法都有 docstring
- 参数说明使用 Args/Returns 格式
- 复杂算法有注释说明

### 测试规范

- 每个模块对应一个测试文件
- 测试类名：Test{ClassName}
- 测试方法名：test_{功能描述}
- 使用 pytest 断言
