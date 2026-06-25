# Audio Processing Engine (音频处理引擎)

一个基于 C++17/20 的完整音频处理引擎，涵盖音频基础、编解码、处理、效果、分析和合成等核心技术。

## 项目简介

本项目是一个教学级音频处理引擎，通过独立的示例程序演示音频处理的各个方面。每个功能模块都是独立的可执行文件，便于学习和实验。

### 核心特性

- **音频基础**: 采样、量化、采样率、位深度、声道处理
- **音频编解码**: PCM、WAV 格式支持（MP3/AAC/Opus 概念演示）
- **音频处理**: 音量调节、淡入淡出、混音、均衡器、压缩器、限幅器
- **音频效果**: 混响、延迟、合唱、失真、降噪
- **音频分析**: FFT、频谱分析、节奏检测、音高检测、特征提取
- **音频合成**: 波形合成、FM 合成、减法合成、采样合成
- **实际应用**: 音频播放器、编辑器、分析工具、合成器

## 快速开始

### 环境要求

- C++17 或更高版本的编译器（GCC 8+, Clang 7+, MSVC 2019+）
- CMake 3.16+

### 编译运行

```bash
# 进入项目目录
cd projects/audio-engine

# 创建构建目录
mkdir build && cd build

# 配置
cmake ..

# 编译
make -j$(nproc)

# 运行示例
./bin/basic_sampling          # 音频采样示例
./bin/wav_codec               # WAV 编解码
./bin/volume_control          # 音量控制
./bin/reverb_effect           # 混响效果
./bin/fft_analysis            # FFT 分析
./bin/sine_synth              # 正弦波合成
./bin/audio_player            # 音频播放器
```

## 技术分类

```
audio-engine/
├── src/
│   ├── basic/          # 音频基础
│   │   ├── sampling.cpp        # 采样原理
│   │   ├── quantization.cpp    # 量化处理
│   │   ├── sample_rate.cpp     # 采样率转换
│   │   ├── bit_depth.cpp       # 位深度处理
│   │   └── channels.cpp        # 声道处理
│   ├── codec/          # 音频编解码
│   │   ├── pcm_codec.cpp       # PCM 编解码
│   │   ├── wav_codec.cpp       # WAV 文件读写
│   │   ├── mp3_codec.cpp       # MP3 概念演示
│   │   ├── aac_codec.cpp       # AAC 概念演示
│   │   └── opus_codec.cpp      # Opus 概念演示
│   ├── processing/     # 音频处理
│   │   ├── volume.cpp          # 音量调节
│   │   ├── fade.cpp            # 淡入淡出
│   │   ├── mixer.cpp           # 混音器
│   │   ├── equalizer.cpp       # 均衡器
│   │   ├── compressor.cpp      # 压缩器
│   │   └── limiter.cpp         # 限幅器
│   ├── effects/        # 音频效果
│   │   ├── reverb.cpp          # 混响
│   │   ├── delay.cpp           # 延迟
│   │   ├── chorus.cpp          # 合唱
│   │   ├── distortion.cpp      # 失真
│   │   └── noise_reduction.cpp # 降噪
│   ├── analysis/       # 音频分析
│   │   ├── fft.cpp             # FFT 实现
│   │   ├── spectrum.cpp        # 频谱分析
│   │   ├── rhythm.cpp          # 节奏检测
│   │   ├── pitch.cpp           # 音高检测
│   │   └── features.cpp        # 特征提取
│   ├── synthesis/      # 音频合成
│   │   ├── waveform.cpp        # 波形合成
│   │   ├── fm_synth.cpp        # FM 合成
│   │   ├── subtractive.cpp     # 减法合成
│   │   └── sampler.cpp         # 采样合成
│   └── apps/           # 实际应用
│       ├── audio_player.cpp    # 音频播放器
│       ├── audio_editor.cpp    # 音频编辑器
│       ├── analyzer.cpp        # 分析工具
│       └── synthesizer.cpp     # 合成器
├── include/            # 公共头文件
│   └── audio_engine.h
├── CMakeLists.txt
└── docs/               # 文档
    ├── 01_RESEARCH.md
    ├── 02_REQUIREMENTS.md
    ├── 03_DESIGN.md
    ├── 04_PRODUCT.md
    └── 05_DEVELOPMENT.md
```

## 学习路径

### 初级：音频基础
1. `sampling.cpp` - 理解采样定理
2. `quantization.cpp` - 理解量化过程
3. `sample_rate.cpp` - 采样率转换
4. `wav_codec.cpp` - WAV 文件格式

### 中级：音频处理
5. `volume.cpp` - 音量控制
6. `fade.cpp` - 淡入淡出
7. `mixer.cpp` - 多轨混音
8. `equalizer.cpp` - 频率均衡

### 高级：效果与分析
9. `reverb.cpp` - 混响算法
10. `fft.cpp` - 快速傅里叶变换
11. `pitch.cpp` - 音高检测
12. `fm_synth.cpp` - FM 合成

## 许可证

MIT License
