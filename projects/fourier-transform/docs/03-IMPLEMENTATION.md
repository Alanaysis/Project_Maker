# 实现文档: 傅里叶变换

## 1. DFT 实现

### 1.1 矩阵方法

```python
def dft(x):
    x = np.asarray(x, dtype=complex)
    N = len(x)
    n = np.arange(N)
    k = n.reshape((N, 1))
    W = np.exp(-2j * np.pi * k * n / N)
    return W @ x
```

**要点**:
- 使用 NumPy 广播构建 DFT 矩阵
- 矩阵-向量乘法一次性完成计算
- 自动处理实数和复数输入

### 1.2 朴素循环方法

```python
def dft_slow(x):
    N = len(x)
    X = np.zeros(N, dtype=complex)
    for k in range(N):
        for n in range(N):
            X[k] += x[n] * np.exp(-2j * np.pi * k * n / N)
    return X
```

**要点**:
- 直接按照数学定义实现
- 双重循环，O(N^2) 复杂度
- 便于理解原理

## 2. FFT 实现

### 2.1 递归实现

```python
def _fft_recursive(x):
    N = len(x)
    if N == 1:
        return x.copy()

    even = _fft_recursive(x[0::2])
    odd = _fft_recursive(x[1::2])

    k = np.arange(N // 2)
    twiddle = np.exp(-2j * np.pi * k / N)
    t = twiddle * odd

    return np.concatenate([even + t, even - t])
```

**关键实现细节**:

1. **基础情况**: N=1 直接返回
2. **分治**: 偶数索引和奇数索引
3. **旋转因子**: `W_N^k = e^{-j*2*π*k/N}`
4. **蝶形运算**: `even ± twiddle * odd`

### 2.2 自动补零

```python
def fft(x):
    N = len(x)
    if N & (N - 1) != 0:  # 不是 2 的幂
        next_power = 1
        while next_power < N:
            next_power <<= 1
        x = np.pad(x, (0, next_power - N))
    return _fft_recursive(x)
```

**原理**: N & (N-1) == 0 判断 N 是否为 2 的幂。

### 2.3 迭代实现 (Radix-2)

```python
def fft_radix2(x):
    # 位反转排列
    X = _bit_reverse_copy(x)

    # 蝶形运算
    length = 2
    while length <= N:
        half = length // 2
        twiddle = np.exp(-2j * np.pi * np.arange(half) / length)

        for start in range(0, N, length):
            for j in range(half):
                t = twiddle[j] * X[start + j + half]
                X[start + j + half] = X[start + j] - t
                X[start + j] += t

        length <<= 1
    return X
```

**位反转**:
```python
# 例: N=8, 索引 3 (011) → 反转 110 = 6
def _bit_reverse(x, bits):
    result = 0
    for _ in range(bits):
        result = (result << 1) | (x & 1)
        x >>= 1
    return result
```

### 2.4 IFFT 实现

```python
def ifft(X):
    # 利用 FFT 计算: x = (1/N) * conj(FFT(conj(X)))
    return np.conj(fft(np.conj(X))) / len(X)
```

**原理**: 利用 DFT 和 IDFT 的对偶关系，复用 FFT 代码。

## 3. 频谱分析实现

### 3.1 幅度谱和功率谱

```python
def magnitude_spectrum(X):
    return np.abs(X)

def power_spectrum(X):
    return np.abs(X) ** 2
```

### 3.2 相位谱

```python
def phase_spectrum(X, unwrap=False):
    phase = np.angle(X)
    if unwrap:
        phase = np.unwrap(phase)
    return phase
```

**相位展开**: `np.unwrap` 去除 2π 跳变，使相位连续。

### 3.3 频率轴

```python
def frequency_bins(N, sample_rate):
    return np.fft.fftfreq(N, d=1.0/sample_rate)
```

**说明**: `fftfreq` 返回 [0, fs/2, ..., -fs/2, ..., -1/N] 的频率序列。

### 3.4 峰值检测

```python
def find_peaks(spectrum, threshold, min_distance):
    max_val = np.max(spectrum)
    abs_threshold = max_val * threshold
    peaks = []
    for i in range(1, len(spectrum) - 1):
        if (spectrum[i] > spectrum[i-1] and
            spectrum[i] > spectrum[i+1] and
            spectrum[i] >= abs_threshold):
            if not peaks or (i - peaks[-1]) >= min_distance:
                peaks.append(i)
    return peaks
```

**算法**:
1. 找局部最大值（比相邻点大）
2. 阈值过滤（相对于最大值的比例）
3. 最小距离约束（避免相邻峰）

### 3.5 频谱质心

```python
def spectral_centroid(X, sample_rate):
    mag = np.abs(X)
    freqs = frequency_bins(len(X), sample_rate)
    return np.sum(freqs * mag) / np.sum(mag)
```

**含义**: 频谱的"重心"，反映频率分布特征。

## 4. 信号生成实现

### 4.1 基本信号

```python
def sine_wave(frequency, sample_rate, duration, amplitude=1.0, phase=0.0):
    t = np.arange(int(sample_rate * duration)) / sample_rate
    return amplitude * np.sin(2 * np.pi * frequency * t + phase)
```

### 4.2 复合信号

```python
def composite_signal(frequencies, amplitudes, sample_rate, duration):
    N = int(sample_rate * duration)
    t = np.arange(N) / sample_rate
    signal = np.zeros(N)
    for freq, amp in zip(frequencies, amplitudes):
        signal += amp * np.sin(2 * np.pi * freq * t)
    return signal
```

## 5. 关键数学公式

### 5.1 欧拉公式

```
e^{jθ} = cos(θ) + j*sin(θ)
```

### 5.2 旋转因子

```
W_N^k = e^{-j*2*π*k/N} = cos(2πk/N) - j*sin(2πk/N)
```

### 5.3 Parseval 定理

```
Σ|x[n]|^2 = (1/N) * Σ|X[k]|^2
```

### 5.4 卷积定理

```
FFT(x * h) = FFT(x) · FFT(h)
```

其中 `*` 表示卷积，`·` 表示逐元素乘法。
