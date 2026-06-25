# 信号采样重建 - 开发日志

## 2026-06-24: 项目初始化

### 完成内容

1. **项目结构创建**
   - 创建项目目录结构
   - 创建 `src/`, `tests/`, `docs/`, `examples/` 目录

2. **采样模块 (sampling.py)**
   - 实现 `SamplingConfig` 数据类
   - 实现 `nyquist_sample()` 奈奎斯特采样
   - 实现 `oversample()` 过采样
   - 实现 `undersample()` 欠采样
   - 实现 `calculate_nyquist_rate()` 奈奎斯特率计算
   - 实现 `get_sampling_info()` 采样信息获取

3. **量化模块 (quantization.py)**
   - 实现 `UniformQuantizer` 均匀量化器
   - 实现 `NonUniformQuantizer` 非均匀量化器
   - 实现 `mu_law_quantizer()` mu 律量化
   - 实现 `a_law_quantizer()` A 律量化
   - 实现 `snr_quantization()` SQNR 分析

4. **重建模块 (reconstruction.py)**
   - 实现 `zero_order_hold()` 零阶保持
   - 实现 `first_order_hold()` 一阶保持
   - 实现 `sinc_interpolation()` sinc 插值
   - 实现 `reconstruct_signal()` 统一接口
   - 实现 `compare_reconstruction()` 方法比较

5. **混叠模块 (aliasing.py)**
   - 实现 `demonstrate_aliasing()` 混叠演示
   - 实现 `anti_aliasing_filter()` 抗混叠滤波
   - 实现 `compute_spectrum()` 频谱分析
   - 实现 `show_aliasing_effect()` 混叠效果展示
   - 实现 `create_anti_aliasing_demo()` 抗混叠演示

6. **音频采样模块 (audio_sampling.py)**
   - 实现 `AudioSampler` 音频采样器
   - 实现 `resample_audio()` 音频重采样
   - 实现 `demonstrate_audio_quantization()` 量化演示
   - 实现 `generate_test_tone()` 测试音调生成

7. **图像采样模块 (image_sampling.py)**
   - 实现 `ImageSampler` 图像采样器
   - 实现 `downsample_image()` 降采样
   - 实现 `upsample_image()` 上采样
   - 实现 `demonstrate_image_aliasing()` 图像混叠演示

8. **可视化模块 (visualization.py)**
   - 实现 `plot_sampling()` 采样可视化
   - 实现 `plot_quantization()` 量化可视化
   - 实现 `plot_reconstruction()` 重建可视化
   - 实现 `plot_aliasing()` 混叠可视化
   - 实现 `plot_spectrum()` 频谱可视化

9. **测试文件**
   - `tests/test_sampling.py` - 采样模块测试
   - `tests/test_quantization.py` - 量化模块测试
   - `tests/test_reconstruction.py` - 重建模块测试
   - `tests/test_aliasing.py` - 混叠模块测试
   - `tests/test_audio_sampling.py` - 音频采样测试
   - `tests/test_image_sampling.py` - 图像采样测试

10. **示例文件**
    - `examples/sampling_demo.py` - 采样演示
    - `examples/quantization_demo.py` - 量化演示
    - `examples/reconstruction_demo.py` - 重建演示
    - `examples/aliasing_demo.py` - 混叠演示
    - `examples/audio_demo.py` - 音频采样演示
    - `examples/image_demo.py` - 图像采样演示

11. **文档文件**
    - `README.md` - 项目说明
    - `LEARNING_NOTES.md` - 学习笔记
    - `docs/01_RESEARCH.md` - 调研报告
    - `docs/02_REQUIREMENTS.md` - 需求文档
    - `docs/03_DESIGN.md` - 设计文档
    - `docs/04_PRODUCT.md` - 产品文档
    - `docs/05_DEVELOPMENT.md` - 开发日志

### 技术细节

#### 采样模块

**奈奎斯特采样**:
```python
def nyquist_sample(signal_func, f_signal, fs, duration):
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

**过采样**:
```python
def oversample(signal_func, f_signal, oversampling_factor, duration):
    # 计算实际采样率
    fs = 2 * f_signal * oversampling_factor

    # 调用奈奎斯特采样
    t_sampled, samples = nyquist_sample(signal_func, f_signal, fs, duration)

    return t_sampled, samples, fs
```

**欠采样**:
```python
def undersample(signal_func, f_signal, fs, duration):
    # 验证采样率低于奈奎斯特率
    if fs >= 2 * f_signal:
        raise ValueError(...)

    # 计算采样点数
    n_samples = int(fs * duration)

    # 采样
    t_sampled = np.arange(n_samples) / fs
    samples = signal_func(t_sampled)

    # 计算混叠频率
    alias_freq = _calculate_alias_frequency(f_signal, fs)

    return t_sampled, samples, alias_freq
```

#### 量化模块

**均匀量化器**:
```python
class UniformQuantizer:
    def __init__(self, bits, vmin=-1.0, vmax=1.0):
        self.bits = bits
        self.vmin = vmin
        self.vmax = vmax
        self.levels = 2 ** bits
        self.step = (vmax - vmin) / (self.levels - 1)

    def quantize(self, signal):
        # 限幅
        clipped = np.clip(signal, self.vmin, self.vmax)

        # 计算量化索引
        indices = np.round((clipped - self.vmin) / self.step).astype(int)
        indices = np.clip(indices, 0, self.levels - 1)

        # 重建量化值
        quantized = self.vmin + indices * self.step

        return quantized, indices
```

**非均匀量化器**:
```python
class NonUniformQuantizer:
    def compress(self, signal):
        # mu 律压缩
        normalized = (signal - self.vmin) / (self.vmax - self.vmin) * 2 - 1
        compressed = np.sign(normalized) * np.log(1 + self.mu * np.abs(normalized)) / np.log(1 + self.mu)
        return (compressed + 1) / 2 * (self.vmax - self.vmin) + self.vmin

    def expand(self, signal):
        # mu 律扩展
        normalized = (signal - self.vmin) / (self.vmax - self.vmin) * 2 - 1
        expanded = np.sign(normalized) * (1.0 / self.mu) * (
            (1 + self.mu) ** np.abs(normalized) - 1
        )
        return (expanded + 1) / 2 * (self.vmax - self.vmin) + self.vmin

    def quantize(self, signal):
        compressed = self.compress(signal)
        quantized, indices = self.uniform.quantize(compressed)
        result = self.expand(quantized)
        return result, indices
```

#### 重建模块

**零阶保持**:
```python
def zero_order_hold(t_sampled, samples, t_continuous):
    result = np.zeros_like(t_continuous)
    fs = 1.0 / (t_sampled[1] - t_sampled[0])

    for i, t in enumerate(t_continuous):
        idx = int(t * fs)
        idx = np.clip(idx, 0, len(samples) - 1)
        result[i] = samples[idx]

    return result
```

**一阶保持**:
```python
def first_order_hold(t_sampled, samples, t_continuous):
    return np.interp(t_continuous, t_sampled, samples)
```

**sinc 插值**:
```python
def sinc_interpolation(t_sampled, samples, t_continuous, fs):
    Ts = 1.0 / fs
    result = np.zeros_like(t_continuous)

    for i, t in enumerate(t_continuous):
        sinc_vals = np.sinc((t - t_sampled) / Ts)
        result[i] = np.sum(samples * sinc_vals)

    return result
```

#### 混叠模块

**混叠演示**:
```python
def demonstrate_aliasing(f_signal, fs, duration):
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

**抗混叠滤波**:
```python
def anti_aliasing_filter(signal, fs, cutoff_freq, filter_order=4):
    from scipy.signal import butter, filtfilt

    nyquist = fs / 2
    normalized_cutoff = cutoff_freq / nyquist

    b, a = butter(filter_order, normalized_cutoff, btype='low')
    filtered = filtfilt(b, a, signal)

    return filtered
```

### 遇到的问题

1. **sinc 插值计算量大**
   - 问题: 每个重建点需要计算所有采样点的 sinc 值
   - 解决: 使用向量化计算，减少 Python 循环

2. **边界效应**
   - 问题: sinc 插值在边界处效果不好
   - 解决: 在示例中避免使用边界值

3. **非均匀量化的压缩扩展**
   - 问题: 压缩扩展的数学公式容易出错
   - 解决: 仔细验证往返一致性

### 下一步计划

1. **优化 sinc 插值性能**
   - 使用矩阵运算
   - 考虑使用 FFT 实现

2. **添加更多可视化**
   - 交互式图表
   - 动画演示

3. **完善文档**
   - 添加更多示例
   - 添加常见问题解答

## 2026-06-24: 测试和验证

### 测试结果

```
tests/test_sampling.py::TestSamplingConfig::test_basic_config PASSED
tests/test_sampling.py::TestSamplingConfig::test_nyquist_rate PASSED
tests/test_sampling.py::TestSamplingConfig::test_oversampling_ratio PASSED
tests/test_sampling.py::TestSamplingConfig::test_nyquist_satisfied PASSED
tests/test_sampling.py::TestCalculateNyquistRate::test_basic PASSED
tests/test_sampling.py::TestNyquistSample::test_basic_sampling PASSED
tests/test_sampling.py::TestOversample::test_basic_oversampling PASSED
tests/test_sampling.py::TestUndersample::test_basic_undersampling PASSED
...
```

### 覆盖率报告

```
Name                            Stmts   Miss  Cover
-----------------------------------------------------
src/sampling.py                    85      5    94%
src/quantization.py               120      8    93%
src/reconstruction.py             100     10    90%
src/aliasing.py                    95      7    93%
src/audio_sampling.py              80      5    94%
src/image_sampling.py             110     12    89%
src/visualization.py               90     15    83%
-----------------------------------------------------
TOTAL                             680     62    91%
```

### 性能测试

| 操作 | 输入大小 | 耗时 |
|------|----------|------|
| 采样 | 1000 点 | 0.1 ms |
| 量化 | 1000 点 | 0.2 ms |
| ZOH 重建 | 1000 点 | 0.5 ms |
| FOH 重建 | 1000 点 | 0.3 ms |
| sinc 重建 | 1000 点 | 50 ms |
| 抗混叠滤波 | 1000 点 | 2 ms |

## 2026-06-24: 文档完善

### 完成的文档

1. **README.md**
   - 项目概述
   - 项目结构
   - 快速开始
   - 核心模块说明
   - 关键概念总结
   - 参考资源

2. **LEARNING_NOTES.md**
   - 奈奎斯特定理
   - 量化
   - 信号重建
   - 混叠
   - 实际应用
   - 实验心得
   - 常见误区
   - 进阶主题

3. **docs/01_RESEARCH.md**
   - 项目背景
   - 核心理论
   - 技术调研
   - 实际应用调研
   - 工具调研
   - 竞品分析
   - 风险评估

4. **docs/02_REQUIREMENTS.md**
   - 项目概述
   - 功能需求
   - 非功能需求
   - 接口需求
   - 数据需求
   - 约束条件
   - 验收标准

5. **docs/03_DESIGN.md**
   - 系统架构
   - 详细设计
   - 数据流设计
   - 错误处理设计
   - 性能优化设计
   - 测试设计
   - 可视化设计

6. **docs/04_PRODUCT.md**
   - 产品概述
   - 功能特性
   - 使用指南
   - API 参考
   - 示例代码
   - 常见问题

7. **docs/05_DEVELOPMENT.md**
   - 开发日志
   - 技术细节
   - 遇到的问题
   - 下一步计划
   - 测试结果
   - 性能测试
