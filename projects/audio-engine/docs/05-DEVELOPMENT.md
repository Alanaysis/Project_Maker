# 05 - 开发文档

## 开发环境

### 依赖

- Python 3.8+
- NumPy
- pytest（测试）

### 安装

```bash
cd projects/audio-engine

# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install numpy pytest
```

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
│   ├── fft.py                  # FFT 变换
│   ├── audio_signal.py         # 音频信号
│   ├── filters.py              # 滤波器
│   ├── effects.py              # 音频特效
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

## 开发流程

### 1. 添加新功能

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 实现功能
# 编辑 src/ 目录下的文件

# 3. 编写测试
# 编辑 tests/ 目录下的文件

# 4. 运行测试
pytest tests/ -v

# 5. 提交代码
git add .
git commit -m "feat: 添加新功能"

# 6. 合并到主分支
git checkout master
git merge feature/new-feature
```

### 2. 修复 Bug

```bash
# 1. 创建修复分支
git checkout -b fix/bug-description

# 2. 修复 Bug
# 编辑相关文件

# 3. 添加回归测试
# 编辑 tests/ 目录下的文件

# 4. 运行测试
pytest tests/ -v

# 5. 提交代码
git add .
git commit -m "fix: 修复 Bug 描述"
```

## 代码规范

### Python 风格

- 遵循 PEP 8
- 使用 4 空格缩进
- 行长度限制：120 字符
- 使用类型注解

### 命名规范

```python
# 类名：PascalCase
class AudioSignal:
    pass

# 函数名：snake_case
def apply_filter():
    pass

# 常量：UPPER_SNAKE_CASE
SAMPLE_RATE = 44100

# 私有方法：_leading_underscore
def _internal_method():
    pass
```

### 文档规范

```python
def complex_function(param1: int, param2: str) -> bool:
    """函数的简短描述

    函数的详细描述（如果需要）。

    Args:
        param1: 参数1的描述
        param2: 参数2的描述

    Returns:
        返回值的描述

    Raises:
        ValueError: 异常情况描述
    """
    pass
```

## 调试技巧

### 1. FFT 调试

```python
# 可视化频谱
import matplotlib.pyplot as plt

spectrum = FFT.transform(signal)
magnitude = np.abs(spectrum)
freqs = np.fft.fftfreq(len(signal), 1.0 / sample_rate)

plt.plot(freqs[:len(freqs)//2], magnitude[:len(magnitude)//2])
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
plt.title('Spectrum')
plt.show()
```

### 2. 滤波器调试

```python
# 查看频率响应
freqs, response = filter.get_frequency_response(1024)

plt.semilogx(freqs, 20 * np.log10(response))
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude (dB)')
plt.title('Filter Response')
plt.grid(True)
plt.show()
```

### 3. 信号调试

```python
# 对比处理前后
fig, axes = plt.subplots(2, 1)

axes[0].plot(original.data[:1000])
axes[0].set_title('Original')

axes[1].plot(processed.data[:1000])
axes[1].set_title('Processed')

plt.tight_layout()
plt.show()
```

## 常见问题

### 1. FFT 结果不正确

**问题**：FFT 幅度谱不对

**原因**：未归一化

**解决**：
```python
magnitude = np.abs(spectrum) * 2.0 / N  # 单边谱归一化
magnitude[0] /= 2.0  # DC 分量不需要乘以2
```

### 2. 滤波后有振铃

**问题**：滤波后出现振荡

**原因**：理想滤波器（硬截止）会导致吉布斯现象

**解决**：使用平滑过渡带
```python
lpf = LowPassFilter(cutoff_freq=1000, rolloff_width=200)
```

### 3. 降噪后有音乐噪声

**问题**：降噪后出现"音乐噪声"

**原因**：频谱减法过度

**解决**：调整谱下限
```python
denoiser = Denoiser(noise_factor=2.0, spectral_floor=0.3)
```

### 4. 混音时出现削波

**问题**：混音后信号失真

**原因**：信号超出 [-1, 1] 范围

**解决**：使用软限幅
```python
output = np.tanh(mixed_signal)
```

## 性能优化

### 1. 使用 NumPy 向量化

```python
# 慢
for i in range(len(data)):
    result[i] = data[i] * gain

# 快
result = data * gain
```

### 2. 预分配内存

```python
# 慢
result = []
for item in data:
    result.append(process(item))

# 快
result = np.zeros(len(data))
for i, item in enumerate(data):
    result[i] = process(item)
```

### 3. 缓存计算结果

```python
class Filter:
    def __init__(self):
        self._cache = {}

    def get_mask(self, n_samples):
        if n_samples not in self._cache:
            self._cache[n_samples] = self._create_mask(n_samples)
        return self._cache[n_samples]
```

## 扩展开发

### 添加新的滤波器

```python
class CustomFilter(Filter):
    def _create_filter_mask(self, n_samples):
        # 实现自定义频率响应
        freqs = np.fft.fftfreq(n_samples, 1.0 / self.sample_rate)
        mask = np.zeros(n_samples)
        # ... 自定义逻辑
        return mask
```

### 添加新的特效

```python
class CustomEffect(AudioEffect):
    def apply(self, signal: AudioSignal) -> AudioSignal:
        # 实现自定义效果
        data = signal.data.copy()
        # ... 处理逻辑
        return AudioSignal(data, signal.sample_rate, signal.channels)
```

## 版本历史

### v1.0.0 (当前版本)

- 实现 FFT/IFFT 变换
- 实现 AudioSignal 类
- 实现低通、高通、带通、陷波滤波器
- 实现延迟、混响、合唱、失真、压缩效果
- 实现混音器
- 实现频谱减法降噪
- 实现参数均衡器和图示均衡器
- 完整的单元测试
- 示例代码

### 未来计划

- [ ] 添加 WAV 文件支持
- [ ] 实现实时处理
- [ ] 添加更多特效（Phaser、Flanger）
- [ ] 优化性能（使用 Cython）
- [ ] 添加 GUI 界面

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目仅用于学习目的。
