# 02 - 设计文档

## 1. 系统架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      应用层 (Application)                     │
├─────────────────────────────────────────────────────────────┤
│                    容器层 (Container Layer)                    │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │   MP4 Muxer  │  │   FLV Muxer  │  │   TS Muxer   │    │
│   └──────────────┘  └──────────────┘  └──────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    编解码层 (Codec Layer)                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │ Video Codec  │  │ Audio Codec  │  │ Subtitle Codec│    │
│   │ H.264/H.265  │  │   AAC/Opus   │  │   SRT/ASS    │    │
│   └──────────────┘  └──────────────┘  └──────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    处理层 (Processing Layer)                   │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │  Swscale     │  │ Swresample   │  │  AVFilter    │    │
│   │  像素转换     │  │  采样转换     │  │  滤镜处理    │    │
│   └──────────────┘  └──────────────┘  └──────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    工具层 (Utility Layer)                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│   │  AVUtil      │  │  AVIO        │  │  Math        │    │
│   │  通用工具     │  │  IO操作       │  │  数学运算    │    │
│   └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

#### 视频编码模块
- VideoEncoder: 视频编码器接口
- H264Encoder: H.264编码实现
- H265Encoder: H.265编码实现

#### 视频解码模块
- VideoDecoder: 视频解码器接口
- H264Decoder: H.264解码实现
- H265Decoder: H.265解码实现

#### 音频编码模块
- AudioEncoder: 音频编码器接口
- AACEncoder: AAC编码实现
- OpusEncoder: Opus编码实现

#### 音频解码模块
- AudioDecoder: 音频解码器接口
- AACDecoder: AAC解码实现
- OpusDecoder: Opus解码实现

#### 容器模块
- Muxer: 复用器接口
- Demuxer: 解复用器接口
- MP4Muxer: MP4复用实现
- FLVMuxer: FLV复用实现

## 2. 接口设计

### 2.1 视频编码器接口

```cpp
class VideoEncoder {
public:
    virtual ~VideoEncoder() = default;
    
    // 初始化编码器
    virtual int init(const VideoEncoderConfig& config) = 0;
    
    // 编码一帧
    virtual int encode(const AVFrame* frame, AVPacket* pkt) = 0;
    
    // 刷新编码器
    virtual int flush(std::vector<AVPacket*>& packets) = 0;
    
    // 获取编码器信息
    virtual const char* getName() const = 0;
    
    // 释放资源
    virtual void close() = 0;
};

struct VideoEncoderConfig {
    int width;              // 视频宽度
    int height;             // 视频高度
    int fps;                // 帧率
    int64_t bitrate;        // 码率
    int gop_size;           // GOP大小
    int max_b_frames;       // 最大B帧数
    AVPixelFormat pix_fmt;  // 像素格式
    const char* preset;     // 编码预设
    const char* profile;    // 编码档次
};
```

### 2.2 视频解码器接口

```cpp
class VideoDecoder {
public:
    virtual ~VideoDecoder() = default;
    
    // 初始化解码器
    virtual int init(const VideoDecoderConfig& config) = 0;
    
    // 解码一个数据包
    virtual int decode(const AVPacket* pkt, AVFrame* frame) = 0;
    
    // 刷新解码器
    virtual int flush(AVFrame* frame) = 0;
    
    // 获取解码器信息
    virtual const char* getName() const = 0;
    
    // 释放资源
    virtual void close() = 0;
};

struct VideoDecoderConfig {
    AVCodecID codec_id;     // 编码ID
    int width;              // 视频宽度
    int height;             // 视频高度
    AVPixelFormat pix_fmt;  // 像素格式
};
```

### 2.3 音频编码器接口

```cpp
class AudioEncoder {
public:
    virtual ~AudioEncoder() = default;
    
    // 初始化编码器
    virtual int init(const AudioEncoderConfig& config) = 0;
    
    // 编码一帧
    virtual int encode(const AVFrame* frame, AVPacket* pkt) = 0;
    
    // 刷新编码器
    virtual int flush(std::vector<AVPacket*>& packets) = 0;
    
    // 获取编码器信息
    virtual const char* getName() const = 0;
    
    // 释放资源
    virtual void close() = 0;
};

struct AudioEncoderConfig {
    int sample_rate;        // 采样率
    int channels;           // 声道数
    int64_t bitrate;        // 码率
    AVSampleFormat sample_fmt;  // 采样格式
    int frame_size;         // 帧大小
};
```

### 2.4 音频解码器接口

```cpp
class AudioDecoder {
public:
    virtual ~AudioDecoder() = default;
    
    // 初始化解码器
    virtual int init(const AudioDecoderConfig& config) = 0;
    
    // 解码一个数据包
    virtual int decode(const AVPacket* pkt, AVFrame* frame) = 0;
    
    // 刷新解码器
    virtual int flush(AVFrame* frame) = 0;
    
    // 获取解码器信息
    virtual const char* getName() const = 0;
    
    // 释放资源
    virtual void close() = 0;
};

struct AudioDecoderConfig {
    AVCodecID codec_id;     // 编码ID
    int sample_rate;        // 采样率
    int channels;           // 声道数
    AVSampleFormat sample_fmt;  // 采样格式
};
```

### 2.5 复用器接口

```cpp
class Muxer {
public:
    virtual ~Muxer() = default;
    
    // 初始化复用器
    virtual int init(const MuxerConfig& config) = 0;
    
    // 添加流
    virtual int addStream(const AVCodecContext* codec_ctx) = 0;
    
    // 写入文件头
    virtual int writeHeader() = 0;
    
    // 写入数据包
    virtual int writePacket(AVPacket* pkt) = 0;
    
    // 写入文件尾
    virtual int writeTrailer() = 0;
    
    // 释放资源
    virtual void close() = 0;
};

struct MuxerConfig {
    const char* filename;   // 输出文件名
    const char* format;     // 容器格式
};
```

### 2.6 解复用器接口

```cpp
class Demuxer {
public:
    virtual ~Demuxer() = default;
    
    // 初始化解复用器
    virtual int init(const DemuxerConfig& config) = 0;
    
    // 打开输入文件
    virtual int openInput(const char* filename) = 0;
    
    // 读取流信息
    virtual int findStreamInfo() = 0;
    
    // 获取流数量
    virtual int getStreamCount() const = 0;
    
    // 获取流信息
    virtual const AVStream* getStream(int index) const = 0;
    
    // 读取数据包
    virtual int readPacket(AVPacket* pkt) = 0;
    
    // 释放资源
    virtual void close() = 0;
};

struct DemuxerConfig {
    const char* filename;   // 输入文件名
};
```

## 3. 数据流设计

### 3.1 视频编码数据流

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  YUV Frame  │───▶│   Encoder   │───▶│   Packet    │
│  (原始帧)    │    │  (编码器)    │    │  (编码包)    │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Filter    │
                   │  (滤镜处理)  │
                   └─────────────┘
```

### 3.2 视频解码数据流

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Packet    │───▶│   Decoder   │───▶│  YUV Frame  │
│  (编码包)    │    │  (解码器)    │    │  (原始帧)    │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Converter  │
                   │  (格式转换)  │
                   └─────────────┘
```

### 3.3 音频编码数据流

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  PCM Frame  │───▶│   Encoder   │───▶│   Packet    │
│  (原始音频)  │    │  (编码器)    │    │  (编码包)    │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Resample   │
                   │  (重采样)    │
                   └─────────────┘
```

### 3.4 容器封装数据流

```
┌─────────────┐
│ Video Packet│──┐
└─────────────┘  │
                 ▼
┌─────────────┐  ┌─────────────┐    ┌─────────────┐
│ Audio Packet│─▶│    Muxer    │───▶│   Output    │
└─────────────┘  │  (复用器)    │    │  (输出文件)  │
                 └─────────────┘    └─────────────┘
```

## 4. 类图设计

### 4.1 编解码器类图

```
┌─────────────────────────────────────────────────────────┐
│                    <<interface>>                         │
│                    ICodec                                │
├─────────────────────────────────────────────────────────┤
│ + init(config): int                                     │
│ + encode/decode(frame/pkt): int                         │
│ + flush(): int                                          │
│ + getName(): const char*                                │
│ + close(): void                                         │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ VideoEncoder  │ │ VideoDecoder  │ │ AudioEncoder  │
├───────────────┤ ├───────────────┤ ├───────────────┤
│ - ctx: *      │ │ - ctx: *      │ │ - ctx: *      │
├───────────────┤ ├───────────────┤ ├───────────────┤
│ + encode()    │ │ + decode()    │ │ + encode()    │
└───────────────┘ └───────────────┘ └───────────────┘
        ▲                 ▲                 ▲
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  H264Encoder  │ │  H264Decoder  │ │  AACEncoder   │
└───────────────┘ └───────────────┘ └───────────────┘
```

### 4.2 容器类图

```
┌─────────────────────────────────────────────────────────┐
│                    <<interface>>                         │
│                    IContainer                            │
├─────────────────────────────────────────────────────────┤
│ + init(config): int                                     │
│ + addStream(codec_ctx): int                             │
│ + writeHeader/writeTrailer(): int                       │
│ + read/writePacket(pkt): int                            │
│ + close(): void                                         │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│    Muxer      │ │   Demuxer     │ │    Player     │
├───────────────┤ ├───────────────┤ ├───────────────┤
│ - fmt_ctx: *  │ │ - fmt_ctx: *  │ │ - fmt_ctx: *  │
├───────────────┤ ├───────────────┤ ├───────────────┤
│ + write()     │ │ + read()      │ │ + play()      │
└───────────────┘ └───────────────┘ └───────────────┘
        ▲                 ▲
        │                 │
        ▼                 ▼
┌───────────────┐ ┌───────────────┐
│  MP4Muxer     │ │  MP4Demuxer   │
└───────────────┘ └───────────────┘
```

## 5. 错误处理设计

### 5.1 错误码定义

```cpp
enum AVCodecError {
    AV_CODEC_SUCCESS = 0,
    AV_CODEC_ERROR_INIT = -1,
    AV_CODEC_ERROR_ENCODE = -2,
    AV_CODEC_ERROR_DECODE = -3,
    AV_CODEC_ERROR_MUX = -4,
    AV_CODEC_ERROR_DEMUX = -5,
    AV_CODEC_ERROR_IO = -6,
    AV_CODEC_ERROR_PARAM = -7,
    AV_CODEC_ERROR_NOMEM = -8,
    AV_CODEC_ERROR_NOT_FOUND = -9,
    AV_CODEC_ERROR_EOF = -10,
};
```

### 5.2 错误处理策略

```cpp
// 统一错误处理宏
#define CHECK_ERROR(ret, msg) \
    if (ret < 0) { \
        char errbuf[AV_ERROR_MAX_STRING_SIZE]; \
        av_strerror(ret, errbuf, sizeof(errbuf)); \
        fprintf(stderr, "%s: %s\n", msg, errbuf); \
        return ret; \
    }

// 资源清理
#define CLEANUP(ptr) \
    if (ptr) { \
        av_free(ptr); \
        ptr = nullptr; \
    }
```

## 6. 内存管理设计

### 6.1 内存分配策略

```cpp
// 使用FFmpeg内存管理
AVFrame* frame = av_frame_alloc();
AVPacket* pkt = av_packet_alloc();

// 使用RAII包装
class FrameGuard {
    AVFrame* frame;
public:
    FrameGuard() : frame(av_frame_alloc()) {}
    ~FrameGuard() { av_frame_free(&frame); }
    AVFrame* get() { return frame; }
};
```

### 6.2 内存池设计

```cpp
class FramePool {
    std::queue<AVFrame*> pool;
    std::mutex mutex;
    
public:
    AVFrame* acquire() {
        std::lock_guard<std::mutex> lock(mutex);
        if (!pool.empty()) {
            AVFrame* frame = pool.front();
            pool.pop();
            return frame;
        }
        return av_frame_alloc();
    }
    
    void release(AVFrame* frame) {
        std::lock_guard<std::mutex> lock(mutex);
        av_frame_unref(frame);
        pool.push(frame);
    }
};
```

## 7. 线程安全设计

### 7.1 线程模型

```
┌─────────────────────────────────────────────────────────┐
│                      主线程                               │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│   │  读取线程    │  │  编码线程    │  │  写入线程    │    │
│   │  (Demuxer)  │  │  (Encoder)  │  │  (Muxer)    │    │
│   └─────────────┘  └─────────────┘  └─────────────┘    │
│          │                │                │            │
│          ▼                ▼                ▼            │
│   ┌─────────────────────────────────────────────────┐  │
│   │              线程安全队列 (Thread Safe Queue)     │  │
│   └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 7.2 线程安全队列

```cpp
template<typename T>
class ThreadSafeQueue {
    std::queue<T> queue;
    std::mutex mutex;
    std::condition_variable cv;
    
public:
    void push(T item) {
        std::lock_guard<std::mutex> lock(mutex);
        queue.push(std::move(item));
        cv.notify_one();
    }
    
    T pop() {
        std::unique_lock<std::mutex> lock(mutex);
        cv.wait(lock, [this] { return !queue.empty(); });
        T item = std::move(queue.front());
        queue.pop();
        return item;
    }
    
    bool empty() {
        std::lock_guard<std::mutex> lock(mutex);
        return queue.empty();
    }
};
```

## 8. 配置管理设计

### 8.1 配置文件格式

```yaml
# config.yaml
video:
  encoder: h264
  width: 1920
  height: 1080
  fps: 30
  bitrate: 2000000
  preset: medium
  profile: high

audio:
  encoder: aac
  sample_rate: 44100
  channels: 2
  bitrate: 128000

output:
  format: mp4
  filename: output.mp4
```

### 8.2 配置管理类

```cpp
class Config {
public:
    static Config& getInstance();
    
    bool load(const char* filename);
    
    // 视频配置
    struct VideoConfig {
        std::string encoder;
        int width;
        int height;
        int fps;
        int64_t bitrate;
        std::string preset;
        std::string profile;
    } video;
    
    // 音频配置
    struct AudioConfig {
        std::string encoder;
        int sample_rate;
        int channels;
        int64_t bitrate;
    } audio;
    
    // 输出配置
    struct OutputConfig {
        std::string format;
        std::string filename;
    } output;
};
```

## 9. 日志设计

### 9.1 日志级别

```cpp
enum LogLevel {
    LOG_DEBUG = 0,
    LOG_INFO = 1,
    LOG_WARNING = 2,
    LOG_ERROR = 3,
    LOG_FATAL = 4
};
```

### 9.2 日志宏

```cpp
#define LOG_DEBUG(fmt, ...) \
    Logger::getInstance().log(LOG_DEBUG, __FILE__, __LINE__, fmt, ##__VA_ARGS__)

#define LOG_INFO(fmt, ...) \
    Logger::getInstance().log(LOG_INFO, __FILE__, __LINE__, fmt, ##__VA_ARGS__)

#define LOG_WARNING(fmt, ...) \
    Logger::getInstance().log(LOG_WARNING, __FILE__, __LINE__, fmt, ##__VA_ARGS__)

#define LOG_ERROR(fmt, ...) \
    Logger::getInstance().log(LOG_ERROR, __FILE__, __LINE__, fmt, ##__VA_ARGS__)
```

## 10. 测试策略

### 10.1 单元测试
- 测试每个编码器/解码器的基本功能
- 测试边界条件和错误处理

### 10.2 集成测试
- 测试完整的编码-解码流程
- 测试容器封装和解封装

### 10.3 性能测试
- 测试编码速度
- 测试内存使用
- 测试CPU占用

### 10.4 兼容性测试
- 测试不同格式的兼容性
- 测试不同参数的兼容性
