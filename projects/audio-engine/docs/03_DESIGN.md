# 技术设计文档

## 1. 文件组织

### 1.1 目录结构

```
audio-engine/
├── include/
│   └── audio_engine.h          # 统一头文件，包含所有公共接口
├── src/
│   ├── basic/                  # 音频基础模块
│   │   ├── sampling.cpp        # 采样原理演示
│   │   ├── quantization.cpp    # 量化处理演示
│   │   ├── sample_rate.cpp     # 采样率转换
│   │   ├── bit_depth.cpp       # 位深度处理
│   │   └── channels.cpp        # 声道处理
│   ├── codec/                  # 编解码模块
│   │   ├── pcm_codec.cpp       # PCM 编解码
│   │   ├── wav_codec.cpp       # WAV 文件读写
│   │   ├── mp3_codec.cpp       # MP3 概念演示
│   │   ├── aac_codec.cpp       # AAC 概念演示
│   │   └── opus_codec.cpp      # Opus 概念演示
│   ├── processing/             # 音频处理模块
│   │   ├── volume.cpp          # 音量调节
│   │   ├── fade.cpp            # 淡入淡出
│   │   ├── mixer.cpp           # 混音器
│   │   ├── equalizer.cpp       # 均衡器
│   │   ├── compressor.cpp      # 压缩器
│   │   └── limiter.cpp         # 限幅器
│   ├── effects/                # 音频效果模块
│   │   ├── reverb.cpp          # 混响效果
│   │   ├── delay.cpp           # 延迟效果
│   │   ├── chorus.cpp          # 合唱效果
│   │   ├── distortion.cpp      # 失真效果
│   │   └── noise_reduction.cpp # 降噪效果
│   ├── analysis/               # 音频分析模块
│   │   ├── fft.cpp             # FFT 实现
│   │   ├── spectrum.cpp        # 频谱分析
│   │   ├── rhythm.cpp          # 节奏检测
│   │   ├── pitch.cpp           # 音高检测
│   │   └── features.cpp        # 特征提取
│   ├── synthesis/              # 音频合成模块
│   │   ├── waveform.cpp        # 波形合成
│   │   ├── fm_synth.cpp        # FM 合成
│   │   ├── subtractive.cpp     # 减法合成
│   │   └── sampler.cpp         # 采样合成
│   └── apps/                   # 实际应用模块
│       ├── audio_player.cpp    # 音频播放器
│       ├── audio_editor.cpp    # 音频编辑器
│       ├── analyzer.cpp        # 分析工具
│       └── synthesizer.cpp     # 合成器
├── CMakeLists.txt
└── docs/
```

### 1.2 模块依赖关系

```
┌─────────────────────────────────────────────────────────┐
│                      Apps Layer                         │
│   audio_player  audio_editor  analyzer  synthesizer     │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                   Processing Layer                       │
│   processing/  effects/  analysis/  synthesis/           │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    Codec Layer                           │
│              pcm_codec  wav_codec                        │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    Basic Layer                           │
│   sampling  quantization  sample_rate  bit_depth         │
└─────────────────────────────────────────────────────────┘
```

## 2. 核心数据结构设计

### 2.1 AudioBuffer 结构

```cpp
// 音频缓冲区 - 所有音频数据的容器
struct AudioBuffer {
    std::vector<float> samples;  // 采样数据，范围 [-1.0, 1.0]
    uint32_t sample_rate;        // 采样率 (Hz)
    uint16_t channels;           // 声道数
    uint16_t bit_depth;          // 位深度

    // 获取采样数（每声道）
    size_t num_samples() const { return samples.size() / channels; }

    // 获取时长（秒）
    double duration() const {
        return static_cast<double>(num_samples()) / sample_rate;
    }

    // 获取指定位置和声道的采样值
    float get_sample(size_t index, uint16_t channel = 0) const {
        return samples[index * channels + channel];
    }

    // 设置指定位置和声道的采样值
    void set_sample(size_t index, uint16_t channel, float value) {
        samples[index * channels + channel] = value;
    }
};
```

### 2.2 WavHeader 结构

```cpp
// WAV 文件头
struct WavHeader {
    // RIFF 块
    char riff_id[4] = {'R', 'I', 'F', 'F'};
    uint32_t file_size = 0;
    char wave_id[4] = {'W', 'A', 'V', 'E'};

    // fmt 子块
    char fmt_id[4] = {'f', 'm', 't', ' '};
    uint32_t fmt_size = 16;
    uint16_t audio_format = 1;    // 1=PCM, 3=Float
    uint16_t num_channels = 1;
    uint32_t sample_rate = 44100;
    uint32_t byte_rate = 0;
    uint16_t block_align = 0;
    uint16_t bits_per_sample = 16;

    // data 子块
    char data_id[4] = {'d', 'a', 't', 'a'};
    uint32_t data_size = 0;

    // 计算派生字段
    void calculate() {
        block_align = num_channels * bits_per_sample / 8;
        byte_rate = sample_rate * block_align;
        file_size = 36 + data_size;
    }
};
```

### 2.3 FFT 结果结构

```cpp
// FFT 结果
struct FFTResult {
    std::vector<std::complex<double>> spectrum;  // 复数频谱
    size_t fft_size;

    // 获取幅度谱
    std::vector<double> magnitude() const;

    // 获取相位谱
    std::vector<double> phase() const;

    // 获取功率谱
    std::vector<double> power() const;
};
```

## 3. 算法设计

### 3.1 FFT 算法 (Cooley-Tukey)

```
输入: x[0], x[1], ..., x[N-1]
输出: X[0], X[1], ..., X[N-1]

1. 如果 N == 1，返回 x
2. 将 x 分为偶数和奇数部分
   - even = [x[0], x[2], ..., x[N-2]]
   - odd  = [x[1], x[3], ..., x[N-1]]
3. 递归计算
   - E = FFT(even)
   - O = FFT(odd)
4. 蝶形运算
   - 对于 k = 0 到 N/2-1:
     - t = exp(-2πik/N) * O[k]
     - X[k] = E[k] + t
     - X[k + N/2] = E[k] - t
5. 返回 X
```

### 3.2 混响算法 (Schroeder)

```
输入: dry signal
输出: wet signal with reverb

1. 早期反射（Early Reflections）
   - 使用延迟线模拟早期反射
   - 延迟时间: 15-80ms

2. 后期混响（Late Reverb）
   - 4个并行梳状滤波器（Comb Filters）
     - 延迟时间: ~30-45ms
     - 反馈系数: 0.5-0.9
   - 2个串联全通滤波器（Allpass Filters）
     - 延迟时间: ~5ms

3. 混合
   - output = dry * (1 - mix) + wet * mix
```

### 3.3 压缩器算法

```
输入: input signal, threshold, ratio, attack, release
输出: compressed signal

对于每个采样:
1. 计算输入电平（dB）
   level = 20 * log10(|input|)

2. 计算增益减少量
   if level > threshold:
       gain_reduction = (threshold - level) * (1 - 1/ratio)
   else:
       gain_reduction = 0

3. 应用包络平滑
   if gain_reduction < prev_gain:
       // Attack (减少增益)
       gain = prev_gain + (gain_reduction - prev_gain) * attack_coeff
   else:
       // Release (恢复增益)
       gain = prev_gain + (gain_reduction - prev_gain) * release_coeff

4. 应用增益
   output = input * 10^(gain/20)
```

### 3.4 音高检测 (自相关法)

```
输入: audio signal
输出: fundamental frequency (Hz)

1. 预处理
   - 高通滤波去除直流偏移
   - 窗函数（汉宁窗）

2. 自相关计算
   R(τ) = Σ x[n] * x[n + τ]

3. 寻找峰值
   - 在合理范围内搜索（50Hz - 2000Hz）
   - 寻找第一个显著峰值

4. 计算频率
   f = sample_rate / τ_peak
```

## 4. 接口设计

### 4.1 Codec 接口

```cpp
class Codec {
public:
    virtual ~Codec() = default;

    // 编码
    virtual std::vector<uint8_t> encode(const AudioBuffer& buffer) = 0;

    // 解码
    virtual AudioBuffer decode(const std::vector<uint8_t>& data) = 0;

    // 获取格式名称
    virtual std::string name() const = 0;
};
```

### 4.2 Effect 接口

```cpp
class Effect {
public:
    virtual ~Effect() = default;

    // 处理音频
    virtual void process(AudioBuffer& buffer) = 0;

    // 设置参数
    virtual void set_parameter(const std::string& name, float value) = 0;

    // 获取效果名称
    virtual std::string name() const = 0;
};
```

### 4.3 Analyzer 接口

```cpp
class Analyzer {
public:
    virtual ~Analyzer() = default;

    // 分析音频
    virtual std::vector<double> analyze(const AudioBuffer& buffer) = 0;

    // 获取分析器名称
    virtual std::string name() const = 0;
};
```

## 5. 内存管理

### 5.1 缓冲区策略

- 使用 `std::vector<float>` 管理采样数据
- 避免不必要的拷贝，使用移动语义
- 大缓冲区使用智能指针

### 5.2 实时处理

- 固定大小的处理块（512/1024/2048 采样）
- 环形缓冲区用于延迟线
- 预分配内存避免实时分配

## 6. 错误处理

### 6.1 异常类型

```cpp
class AudioError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class FileError : public AudioError {
public:
    using AudioError::AudioError;
};

class FormatError : public AudioError {
public:
    using AudioError::AudioError;
};
```

### 6.2 错误检查

- 文件操作：检查打开/读写状态
- 参数验证：检查范围和有效性
- 缓冲区检查：确保足够空间
