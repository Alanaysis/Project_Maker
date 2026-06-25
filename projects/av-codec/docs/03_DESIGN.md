# 03 技术设计 - 音视频编解码器

## 1. 文件组织

```
av-codec/
├── CMakeLists.txt              # CMake构建配置
├── README.md                   # 项目说明
├── build.sh                    # 构建脚本
├── include/                    # 头文件
│   ├── video/                  # 视频编解码头文件
│   │   ├── h264_codec.h        # H.264编解码接口
│   │   ├── h265_codec.h        # H.265编解码接口
│   │   ├── vp9_codec.h         # VP9编解码接口
│   │   ├── av1_codec.h         # AV1编解码接口
│   │   ├── prediction.h        # 预测接口
│   │   ├── motion_estimation.h # 运动估计接口
│   │   ├── transform_quant.h   # 变换量化接口
│   │   └── entropy_coding.h    # 熵编码接口
│   ├── audio/                  # 音频编解码头文件
│   │   ├── aac_codec.h         # AAC编解码接口
│   │   ├── mp3_codec.h         # MP3编解码接口
│   │   ├── opus_codec.h        # Opus编解码接口
│   │   ├── vorbis_codec.h      # Vorbis编解码接口
│   │   └── audio_processing.h  # 音频处理接口
│   ├── container/              # 容器格式头文件
│   │   └── container.h         # 容器接口
│   ├── protocol/               # 流媒体协议头文件
│   │   └── streaming.h         # 流媒体接口
│   ├── optimization/           # 性能优化头文件
│   │   └── performance.h       # 性能优化接口
│   └── application/            # 应用头文件
│       └── application.h       # 应用接口
├── src/                        # 源代码
│   ├── video/                  # 视频编解码实现
│   ├── audio/                  # 音频编解码实现
│   ├── container/              # 容器格式实现
│   ├── protocol/               # 流媒体协议实现
│   ├── optimization/           # 性能优化实现
│   └── application/            # 应用实现
├── examples/                   # 示例程序
├── tests/                      # 测试代码
└── docs/                       # 文档
```

## 2. 模块设计

### 2.1 视频编码模块

```
┌─────────────────────────────────────────────────────────────┐
│                      Video Encoder                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Intra   │  │  Inter   │  │ Transform│  │ Quantize │   │
│  │Prediction│  │Prediction│  │   (DCT)  │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       ↑              ↑              ↑              ↑        │
│       │              │              │              │        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Motion   │  │  Motion  │  │  Entropy │  │  Deblock │   │
│  │Estimation│  │Compensate│  │  Coding  │  │  Filter  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 视频解码模块

```
┌─────────────────────────────────────────────────────────────┐
│                      Video Decoder                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Entropy  │  │ Dequant  │  │  Inverse │  │  Reconstruct│
│  │ Decoding │  │          │  │  Transform│  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       ↑              ↑              ↑              ↑        │
│       │              │              │              │        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Intra   │  │  Inter   │  │  Motion  │  │  Deblock │   │
│  │Prediction│  │Prediction│  │Compensate│  │  Filter  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 音频编码模块

```
┌─────────────────────────────────────────────────────────────┐
│                      Audio Encoder                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Window  │  │  MDCT/   │  │Psychoacoustic│ Quantize │   │
│  │  Function│  │  FFT     │  │  Model   │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       ↑              ↑              ↑              ↑        │
│       │              │              │              │        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Frame   │  │  Spectral│  │  Bitrate │  │  Entropy │   │
│  │ Analysis │  │  Coding  │  │ Allocation│  │  Coding  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 3. 接口设计

### 3.1 编码器接口

```cpp
class IVideoEncoder {
public:
    virtual int init(const EncodeParams& params) = 0;
    virtual int encode(const uint8_t* input, std::vector<uint8_t>& output) = 0;
    virtual int flush(std::vector<uint8_t>& output) = 0;
    virtual EncodeStats getStats() const = 0;
    virtual void close() = 0;
};
```

### 3.2 解码器接口

```cpp
class IVideoDecoder {
public:
    virtual int init(const DecodeParams& params) = 0;
    virtual int decode(const uint8_t* input, int size, std::vector<uint8_t>& output) = 0;
    virtual int flush(std::vector<uint8_t>& output) = 0;
    virtual void close() = 0;
};
```

### 3.3 容器接口

```cpp
class IMuxer {
public:
    virtual int init(const char* filename, ContainerFormat format) = 0;
    virtual int addVideoStream(const VideoStreamInfo& info) = 0;
    virtual int addAudioStream(const AudioStreamInfo& info) = 0;
    virtual int writeHeader() = 0;
    virtual int writePacket(const AVPacketData& pkt) = 0;
    virtual int writeTrailer() = 0;
    virtual void close() = 0;
};
```

## 4. 数据流设计

### 4.1 编码数据流

```
原始数据 → 预处理 → 帧内/帧间预测 → 残差计算 → DCT变换 → 量化 → 熵编码 → 码流
```

### 4.2 解码数据流

```
码流 → 熵解码 → 反量化 → 逆DCT → 预测重建 → 环路滤波 → 输出
```

### 4.3 容器封装数据流

```
编码码流 → 分帧 → 添加时间戳 → 写入容器 → 输出文件
```

## 5. 错误处理

### 5.1 错误码定义

```cpp
enum class ErrorCode {
    OK = 0,
    INVALID_PARAM = -1,
    OUT_OF_MEMORY = -2,
    INVALID_FORMAT = -3,
    DECODE_ERROR = -4,
    ENCODE_ERROR = -5,
    IO_ERROR = -6,
    NOT_SUPPORTED = -7
};
```

### 5.2 错误恢复

- 解码错误：跳过当前帧，使用参考帧
- 编码错误：重试或降级编码参数
- IO错误：重试或报错退出
