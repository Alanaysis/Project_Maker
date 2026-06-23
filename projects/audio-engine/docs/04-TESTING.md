# 04 - 测试文档

## 测试策略

### 测试层次

1. **单元测试**：测试单个函数/类
2. **集成测试**：测试模块间交互
3. **端到端测试**：测试完整处理流程
4. **性能测试**：测试处理速度

### 测试覆盖目标

- 核心算法：100%
- 公共 API：90%+
- 边界条件：全覆盖

## 测试用例

### 1. FFT 模块测试

#### 基本变换测试

```python
def test_basic_transform():
    """测试基本 FFT 变换"""
    N = 64
    t = np.linspace(0, 1, N, endpoint=False)
    signal = np.sin(2 * np.pi * 5 * t)

    spectrum = FFT.transform(signal)

    # 检查长度
    assert len(spectrum) == N

    # 检查对称性（实数信号的 FFT 具有共轭对称性）
    assert np.allclose(spectrum[1:N//2], np.conj(spectrum[N-1:N//2:-1]))
```

#### 幂次长度测试

```python
def test_power_of_two():
    """测试2的幂次长度"""
    for n in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]:
        signal = np.random.randn(n)
        spectrum = FFT.transform(signal)
        assert len(spectrum) == n
```

#### 频率检测测试

```python
def test_single_frequency_detection():
    """测试单频率检测"""
    N = 256
    sample_rate = 256
    freq = 32

    t = np.linspace(0, 1, N, endpoint=False)
    signal = np.sin(2 * np.pi * freq * t)

    spectrum = FFT.transform(signal)
    magnitude = np.abs(spectrum) * 2.0 / N

    freqs = np.fft.fftfreq(N, 1.0 / sample_rate)
    peak_idx = np.argmax(magnitude[:N//2])
    peak_freq = freqs[peak_idx]

    assert abs(peak_freq - freq) < sample_rate / N
```

#### FFT 性质测试

```python
def test_linearity():
    """测试线性性质: FFT(a*x + b*y) = a*FFT(x) + b*FFT(y)"""
    N = 64
    x = np.random.randn(N)
    y = np.random.randn(N)
    a, b = 2.0, 3.0

    direct = FFT.transform(a * x + b * y)
    linear = a * FFT.transform(x) + b * FFT.transform(y)

    assert np.allclose(direct, linear, atol=1e-10)


def test_parseval_theorem():
    """测试帕塞瓦尔定理: 时域能量 = 频域能量"""
    N = 128
    signal = np.random.randn(N)

    time_energy = np.sum(signal ** 2)
    spectrum = FFT.transform(signal)
    freq_energy = np.sum(np.abs(spectrum) ** 2) / N

    assert abs(time_energy - freq_energy) < 1e-10
```

#### IFFT 往返测试

```python
def test_fft_ifft_roundtrip():
    """测试 FFT -> IFFT 往返变换"""
    signal = np.random.randn(128)

    spectrum = FFT.transform(signal)
    reconstructed = IFFT.transform_real(spectrum)

    assert np.allclose(signal, reconstructed, atol=1e-10)
```

### 2. AudioSignal 测试

#### 创建测试

```python
def test_basic_creation():
    """测试基本创建"""
    data = np.sin(np.linspace(0, 2 * np.pi * 440, 44100))
    signal = AudioSignal(data, sample_rate=44100)

    assert signal.sample_rate == 44100
    assert signal.channels == 1
    assert len(signal) == 44100
    assert abs(signal.duration - 1.0) < 0.01
```

#### 工厂方法测试

```python
def test_from_tone():
    """测试生成音调"""
    signal = AudioSignal.from_tone(440, duration=1.0, sample_rate=44100)

    assert signal.sample_rate == 44100
    assert abs(signal.duration - 1.0) < 0.01

    t = np.linspace(0, 1.0, 44100, endpoint=False)
    expected = np.sin(2 * np.pi * 440 * t)
    assert np.allclose(signal.data, expected, atol=1e-10)
```

#### 操作测试

```python
def test_normalize():
    """测试归一化"""
    data = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    signal = AudioSignal(data, sample_rate=44100)
    normalized = signal.normalize(target_level=0.9)

    assert np.max(np.abs(normalized.data)) <= 0.9 + 1e-10


def test_mix():
    """测试混合"""
    signal1 = AudioSignal(np.ones(100), sample_rate=44100)
    signal2 = AudioSignal(np.zeros(100), sample_rate=44100)

    mixed = signal1.mix(signal2, ratio=0.5)
    assert np.allclose(mixed.data, 0.5)
```

### 3. 滤波器测试

#### 低通滤波测试

```python
def test_lowpass_filtering():
    """测试低通滤波"""
    sample_rate = 44100
    t = np.linspace(0, 0.1, int(sample_rate * 0.1), endpoint=False)
    low_freq = np.sin(2 * np.pi * 100 * t)
    high_freq = np.sin(2 * np.pi * 5000 * t)
    signal = AudioSignal(low_freq + high_freq, sample_rate)

    lpf = LowPassFilter(cutoff_freq=1000, sample_rate=sample_rate)
    filtered = lpf.apply(signal)

    # 检查频谱
    spectrum = np.abs(np.fft.fft(filtered.data))
    freqs = np.fft.fftfreq(len(filtered.data), 1.0 / sample_rate)

    idx_100 = np.argmin(np.abs(freqs - 100))
    idx_5000 = np.argmin(np.abs(freqs - 5000))

    assert spectrum[idx_100] > spectrum[idx_5000] * 10
```

#### 频率响应测试

```python
def test_cutoff_frequency():
    """测试截止频率"""
    sample_rate = 44100
    lpf = LowPassFilter(cutoff_freq=1000, sample_rate=sample_rate)

    freqs, response = lpf.get_frequency_response(1024)

    below_cutoff = freqs < 800
    assert np.all(response[below_cutoff] > 0.8)

    above_cutoff = freqs > 1200
    assert np.all(response[above_cutoff] < 0.2)
```

### 4. 特效测试

#### 延迟测试

```python
def test_basic_delay():
    """测试基本延迟"""
    sample_rate = 44100
    signal = AudioSignal.from_tone(440, duration=0.5, sample_rate=sample_rate)

    delay = Delay(delay_time=0.1, feedback=0.5, mix=0.5, sample_rate=sample_rate)
    delayed = delay.apply(signal)

    assert len(delayed) == len(signal)
    assert not np.allclose(delayed.data, signal.data)
```

#### 混响测试

```python
def test_reverb_room_size():
    """测试房间大小影响"""
    sample_rate = 44100
    signal_data = np.zeros(44100)
    signal_data[0] = 1.0
    signal = AudioSignal(signal_data, sample_rate)

    reverb_small = Reverb(room_size=0.2, mix=0.5, sample_rate=sample_rate)
    result_small = reverb_small.apply(signal)

    reverb_large = Reverb(room_size=0.8, mix=0.5, sample_rate=sample_rate)
    result_large = reverb_large.apply(signal)

    mid = len(signal) // 2
    energy_small = np.sum(result_small.data[mid:] ** 2)
    energy_large = np.sum(result_large.data[mid:] ** 2)

    assert energy_large > energy_small
```

### 5. 混音器测试

#### 多轨混合测试

```python
def test_basic_mixing():
    """测试基本混音"""
    mixer = Mixer(sample_rate=44100)

    signal1 = AudioSignal.from_tone(440, duration=0.1)
    signal2 = AudioSignal.from_tone(880, duration=0.1)

    mixer.add_track(signal1, name="Track 1")
    mixer.add_track(signal2, name="Track 2")

    left, right = mixer.render()

    assert len(left) > 0
    assert len(right) > 0
```

#### 声像测试

```python
def test_stereo_panning():
    """测试声像定位"""
    signal = AudioSignal(np.ones(100), sample_rate=44100)

    track_left = MixerTrack(signal, pan=-1.0)
    left, right = track_left.get_stereo_signal()

    assert np.allclose(left, 1.0)
    assert np.allclose(right, 0.0, atol=1e-10)
```

### 6. 降噪测试

#### 基本降噪测试

```python
def test_basic_denoising():
    """测试基本降噪"""
    sample_rate = 44100
    t = np.linspace(0, 1, sample_rate, endpoint=False)
    clean_signal = np.sin(2 * np.pi * 440 * t)

    noise = np.random.randn(sample_rate) * 0.3
    noisy_signal = clean_signal + noise

    signal = AudioSignal(noisy_signal, sample_rate)

    denoiser = Denoiser(noise_factor=2.0, sample_rate=sample_rate)
    denoised = denoiser.apply(signal)

    noise_before = np.sum(noisy_signal[:1000] ** 2)
    noise_after = np.sum(denoised.data[:1000] ** 2)

    assert noise_after < noise_before
```

### 7. 均衡器测试

#### 频率提升测试

```python
def test_boost_frequency():
    """测试提升特定频率"""
    sample_rate = 44100
    t = np.linspace(0, 0.5, sample_rate // 2, endpoint=False)
    signal_data = np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 1000 * t)
    signal = AudioSignal(signal_data, sample_rate)

    eq = Equalizer(sample_rate=sample_rate)
    eq.add_band(440, gain_db=6.0, q_factor=2.0)

    equalized = eq.apply(signal)

    spectrum_orig = np.abs(np.fft.fft(signal.data))
    spectrum_eq = np.abs(np.fft.fft(equalized.data))
    freqs = np.fft.fftfreq(len(signal.data), 1.0 / sample_rate)

    idx_440 = np.argmin(np.abs(freqs - 440))
    gain_440 = spectrum_eq[idx_440] / spectrum_orig[idx_440]

    assert gain_440 > 1.0
```

## 运行测试

### 运行所有测试

```bash
cd projects/audio-engine
pytest tests/ -v
```

### 运行特定模块测试

```bash
pytest tests/test_fft.py -v
pytest tests/test_audio_signal.py -v
pytest tests/test_filters.py -v
pytest tests/test_effects.py -v
pytest tests/test_mixer.py -v
pytest tests/test_denoiser.py -v
pytest tests/test_equalizer.py -v
```

### 运行带覆盖率的测试

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

### 运行特定测试

```bash
pytest tests/test_fft.py::TestFFT::test_basic_transform -v
```

## 测试输出示例

```
tests/test_fft.py::TestFFT::test_basic_transform PASSED
tests/test_fft.py::TestFFT::test_power_of_two PASSED
tests/test_fft.py::TestFFT::test_single_frequency_detection PASSED
tests/test_fft.py::TestIFFT::test_fft_ifft_roundtrip PASSED
tests/test_audio_signal.py::TestAudioSignal::test_basic_creation PASSED
tests/test_audio_signal.py::TestAudioSignal::test_from_tone PASSED
tests/test_filters.py::TestLowPassFilter::test_basic_filtering PASSED
tests/test_effects.py::TestDelay::test_basic_delay PASSED
tests/test_mixer.py::TestMixer::test_basic_mixing PASSED
tests/test_denoiser.py::TestDenoiser::test_basic_denoising PASSED
tests/test_equalizer.py::TestEqualizer::test_basic_equalization PASSED

========================= 45 passed in 2.34s =========================
```

## 边界条件测试

### 空输入

```python
def test_empty_input():
    with pytest.raises(ValueError):
        FFT.transform(np.array([]))
```

### 无效参数

```python
def test_invalid_sample_rate():
    with pytest.raises(ValueError):
        AudioSignal(np.zeros(100), sample_rate=0)
```

### 极端值

```python
def test_very_small_signal():
    signal = AudioSignal(np.ones(1) * 1e-10, sample_rate=44100)
    normalized = signal.normalize()
    # 不应该产生 NaN 或 Inf
    assert not np.any(np.isnan(normalized.data))
    assert not np.any(np.isinf(normalized.data))
```

## 性能测试

### FFT 速度基准

```python
def test_fft_performance():
    import time

    sizes = [1024, 4096, 16384, 65536]
    for N in sizes:
        signal = np.random.randn(N)

        start = time.time()
        for _ in range(100):
            FFT.transform(signal)
        elapsed = time.time() - start

        print(f"N={N}: {elapsed/100*1000:.2f} ms")
```

### 大文件测试

```python
def test_large_file_processing():
    # 创建 10 秒音频
    sample_rate = 44100
    duration = 10.0
    signal = AudioSignal.from_tone(440, duration=duration, sample_rate=sample_rate)

    # 应用处理链
    lpf = LowPassFilter(cutoff_freq=2000, sample_rate=sample_rate)
    filtered = lpf.apply(signal)

    assert len(filtered) == len(signal)
```
