# 03 - 实现文档

## 1. 开发环境搭建

### 1.1 依赖安装

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install build-essential cmake pkg-config
sudo apt install libavcodec-dev libavformat-dev libavutil-dev
sudo apt install libswscale-dev libswresample-dev
sudo apt install libavdevice-dev libavfilter-dev
```

#### macOS
```bash
brew install cmake pkg-config ffmpeg
```

### 1.2 验证安装

```bash
# 检查FFmpeg版本
ffmpeg -version

# 检查开发库
pkg-config --libs libavcodec libavformat libavutil
```

## 2. 项目结构实现

### 2.1 CMakeLists.txt实现

```cmake
cmake_minimum_required(VERSION 3.16)
project(av-codec VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找FFmpeg
find_package(PkgConfig REQUIRED)
pkg_check_modules(AVCODEC REQUIRED libavcodec)
pkg_check_modules(AVFORMAT REQUIRED libavformat)
pkg_check_modules(AVUTIL REQUIRED libavutil)
pkg_check_modules(SWSCALE REQUIRED libswscale)
pkg_check_modules(SWRESAMPLE REQUIRED libswresample)

# 头文件目录
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${AVCODEC_INCLUDE_DIRS}
    ${AVFORMAT_INCLUDE_DIRS}
    ${AVUTIL_INCLUDE_DIRS}
    ${SWSCALE_INCLUDE_DIRS}
    ${SWRESAMPLE_INCLUDE_DIRS}
)

# 库目录
link_directories(
    ${AVCODEC_LIBRARY_DIRS}
    ${AVFORMAT_LIBRARY_DIRS}
    ${AVUTIL_LIBRARY_DIRS}
    ${SWSCALE_LIBRARY_DIRS}
    ${SWRESAMPLE_LIBRARY_DIRS}
)

# 源文件
set(SOURCES
    src/video_encoder.cpp
    src/video_decoder.cpp
    src/audio_encoder.cpp
    src/audio_decoder.cpp
    src/muxer.cpp
    src/demuxer.cpp
    src/utils.cpp
)

# 创建静态库
add_library(avcodec_lib STATIC ${SOURCES})
target_link_libraries(avcodec_lib
    ${AVCODEC_LIBRARIES}
    ${AVFORMAT_LIBRARIES}
    ${AVUTIL_LIBRARIES}
    ${SWSCALE_LIBRARIES}
    ${SWRESAMPLE_LIBRARIES}
)

# 示例程序
add_executable(video_encoder_example examples/video_encoder_example.cpp)
target_link_libraries(video_encoder_example avcodec_lib)

add_executable(audio_encoder_example examples/audio_encoder_example.cpp)
target_link_libraries(audio_encoder_example avcodec_lib)

add_executable(muxer_example examples/muxer_example.cpp)
target_link_libraries(muxer_example avcodec_lib)

# 测试
enable_testing()
add_executable(test_video_codec tests/test_video_codec.cpp)
target_link_libraries(test_video_codec avcodec_lib)
add_test(NAME test_video_codec COMMAND test_video_codec)

add_executable(test_audio_codec tests/test_audio_codec.cpp)
target_link_libraries(test_audio_codec avcodec_lib)
add_test(NAME test_audio_codec COMMAND test_audio_codec)

add_executable(test_muxer tests/test_muxer.cpp)
target_link_libraries(test_muxer avcodec_lib)
add_test(NAME test_muxer COMMAND test_muxer)

# 安装
install(TARGETS avcodec_lib
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/ DESTINATION include)
```

## 3. 核心模块实现

### 3.1 视频编码器实现

#### 头文件 (include/video_encoder.h)
```cpp
#pragma once

#include <memory>
#include <string>
#include "codec_types.h"

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/imgutils.h>
}

class VideoEncoder {
public:
    VideoEncoder();
    ~VideoEncoder();
    
    // 初始化编码器
    int init(const VideoEncoderConfig& config);
    
    // 编码一帧
    int encode(const AVFrame* frame, AVPacket* pkt);
    
    // 刷新编码器
    int flush(std::vector<AVPacket*>& packets);
    
    // 获取编码器名称
    const char* getName() const;
    
    // 关闭编码器
    void close();
    
private:
    AVCodecContext* codec_ctx_;
    const AVCodec* codec_;
    bool initialized_;
};
```

#### 源文件 (src/video_encoder.cpp)
```cpp
#include "video_encoder.h"
#include <iostream>

VideoEncoder::VideoEncoder() 
    : codec_ctx_(nullptr), codec_(nullptr), initialized_(false) {
}

VideoEncoder::~VideoEncoder() {
    close();
}

int VideoEncoder::init(const VideoEncoderConfig& config) {
    if (initialized_) {
        std::cerr << "Encoder already initialized" << std::endl;
        return -1;
    }
    
    // 查找编码器
    codec_ = avcodec_find_encoder(AV_CODEC_ID_H264);
    if (!codec_) {
        std::cerr << "H.264 encoder not found" << std::endl;
        return -1;
    }
    
    // 创建编码器上下文
    codec_ctx_ = avcodec_alloc_context3(codec_);
    if (!codec_ctx_) {
        std::cerr << "Could not allocate codec context" << std::endl;
        return -1;
    }
    
    // 设置编码参数
    codec_ctx_->width = config.width;
    codec_ctx_->height = config.height;
    codec_ctx_->bit_rate = config.bitrate;
    codec_ctx_->time_base = {1, config.fps};
    codec_ctx_->framerate = {config.fps, 1};
    codec_ctx_->gop_size = config.gop_size;
    codec_ctx_->max_b_frames = config.max_b_frames;
    codec_ctx_->pix_fmt = AV_PIX_FMT_YUV420P;
    
    // 设置预设
    if (config.preset) {
        av_opt_set(codec_ctx_->priv_data, "preset", config.preset, 0);
    }
    
    // 设置档次
    if (config.profile) {
        av_opt_set(codec_ctx_->priv_data, "profile", config.profile, 0);
    }
    
    // 打开编码器
    int ret = avcodec_open2(codec_ctx_, codec_, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not open codec: " << errbuf << std::endl;
        avcodec_free_context(&codec_ctx_);
        return ret;
    }
    
    initialized_ = true;
    return 0;
}

int VideoEncoder::encode(const AVFrame* frame, AVPacket* pkt) {
    if (!initialized_) {
        std::cerr << "Encoder not initialized" << std::endl;
        return -1;
    }
    
    // 发送帧到编码器
    int ret = avcodec_send_frame(codec_ctx_, frame);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error sending frame: " << errbuf << std::endl;
        return ret;
    }
    
    // 接收编码后的数据包
    ret = avcodec_receive_packet(codec_ctx_, pkt);
    if (ret < 0) {
        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            return ret;
        }
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error receiving packet: " << errbuf << std::endl;
        return ret;
    }
    
    return 0;
}

int VideoEncoder::flush(std::vector<AVPacket*>& packets) {
    if (!initialized_) {
        return -1;
    }
    
    // 发送NULL帧刷新编码器
    int ret = avcodec_send_frame(codec_ctx_, nullptr);
    if (ret < 0) {
        return ret;
    }
    
    // 接收所有剩余的数据包
    while (true) {
        AVPacket* pkt = av_packet_alloc();
        ret = avcodec_receive_packet(codec_ctx_, pkt);
        if (ret == AVERROR_EOF || ret == AVERROR(EAGAIN)) {
            av_packet_free(&pkt);
            break;
        }
        if (ret < 0) {
            av_packet_free(&pkt);
            return ret;
        }
        packets.push_back(pkt);
    }
    
    return 0;
}

const char* VideoEncoder::getName() const {
    return codec_ ? codec_->name : "unknown";
}

void VideoEncoder::close() {
    if (codec_ctx_) {
        avcodec_free_context(&codec_ctx_);
        codec_ctx_ = nullptr;
    }
    codec_ = nullptr;
    initialized_ = false;
}
```

### 3.2 视频解码器实现

#### 头文件 (include/video_decoder.h)
```cpp
#pragma once

#include <memory>
#include <string>
#include "codec_types.h"

extern "C" {
#include <libavcodec/avcodec.h>
}

class VideoDecoder {
public:
    VideoDecoder();
    ~VideoDecoder();
    
    // 初始化解码器
    int init(const VideoDecoderConfig& config);
    
    // 解码一个数据包
    int decode(const AVPacket* pkt, AVFrame* frame);
    
    // 刷新解码器
    int flush(AVFrame* frame);
    
    // 获取解码器名称
    const char* getName() const;
    
    // 关闭解码器
    void close();
    
private:
    AVCodecContext* codec_ctx_;
    const AVCodec* codec_;
    bool initialized_;
};
```

#### 源文件 (src/video_decoder.cpp)
```cpp
#include "video_decoder.h"
#include <iostream>

VideoDecoder::VideoDecoder() 
    : codec_ctx_(nullptr), codec_(nullptr), initialized_(false) {
}

VideoDecoder::~VideoDecoder() {
    close();
}

int VideoDecoder::init(const VideoDecoderConfig& config) {
    if (initialized_) {
        std::cerr << "Decoder already initialized" << std::endl;
        return -1;
    }
    
    // 查找解码器
    codec_ = avcodec_find_decoder(config.codec_id);
    if (!codec_) {
        std::cerr << "Decoder not found" << std::endl;
        return -1;
    }
    
    // 创建解码器上下文
    codec_ctx_ = avcodec_alloc_context3(codec_);
    if (!codec_ctx_) {
        std::cerr << "Could not allocate codec context" << std::endl;
        return -1;
    }
    
    // 设置解码参数
    codec_ctx_->width = config.width;
    codec_ctx_->height = config.height;
    codec_ctx_->pix_fmt = config.pix_fmt;
    
    // 打开解码器
    int ret = avcodec_open2(codec_ctx_, codec_, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not open codec: " << errbuf << std::endl;
        avcodec_free_context(&codec_ctx_);
        return ret;
    }
    
    initialized_ = true;
    return 0;
}

int VideoDecoder::decode(const AVPacket* pkt, AVFrame* frame) {
    if (!initialized_) {
        std::cerr << "Decoder not initialized" << std::endl;
        return -1;
    }
    
    // 发送数据包到解码器
    int ret = avcodec_send_packet(codec_ctx_, pkt);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error sending packet: " << errbuf << std::endl;
        return ret;
    }
    
    // 接收解码后的帧
    ret = avcodec_receive_frame(codec_ctx_, frame);
    if (ret < 0) {
        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            return ret;
        }
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error receiving frame: " << errbuf << std::endl;
        return ret;
    }
    
    return 0;
}

int VideoDecoder::flush(AVFrame* frame) {
    if (!initialized_) {
        return -1;
    }
    
    // 发送NULL数据包刷新解码器
    int ret = avcodec_send_packet(codec_ctx_, nullptr);
    if (ret < 0) {
        return ret;
    }
    
    // 接收剩余的帧
    ret = avcodec_receive_frame(codec_ctx_, frame);
    return ret;
}

const char* VideoDecoder::getName() const {
    return codec_ ? codec_->name : "unknown";
}

void VideoDecoder::close() {
    if (codec_ctx_) {
        avcodec_free_context(&codec_ctx_);
        codec_ctx_ = nullptr;
    }
    codec_ = nullptr;
    initialized_ = false;
}
```

### 3.3 音频编码器实现

#### 头文件 (include/audio_encoder.h)
```cpp
#pragma once

#include <memory>
#include <string>
#include "codec_types.h"

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/opt.h>
}

class AudioEncoder {
public:
    AudioEncoder();
    ~AudioEncoder();
    
    // 初始化编码器
    int init(const AudioEncoderConfig& config);
    
    // 编码一帧
    int encode(const AVFrame* frame, AVPacket* pkt);
    
    // 刷新编码器
    int flush(std::vector<AVPacket*>& packets);
    
    // 获取编码器名称
    const char* getName() const;
    
    // 关闭编码器
    void close();
    
private:
    AVCodecContext* codec_ctx_;
    const AVCodec* codec_;
    bool initialized_;
};
```

#### 源文件 (src/audio_encoder.cpp)
```cpp
#include "audio_encoder.h"
#include <iostream>

AudioEncoder::AudioEncoder() 
    : codec_ctx_(nullptr), codec_(nullptr), initialized_(false) {
}

AudioEncoder::~AudioEncoder() {
    close();
}

int AudioEncoder::init(const AudioEncoderConfig& config) {
    if (initialized_) {
        std::cerr << "Encoder already initialized" << std::endl;
        return -1;
    }
    
    // 查找AAC编码器
    codec_ = avcodec_find_encoder(AV_CODEC_ID_AAC);
    if (!codec_) {
        std::cerr << "AAC encoder not found" << std::endl;
        return -1;
    }
    
    // 创建编码器上下文
    codec_ctx_ = avcodec_alloc_context3(codec_);
    if (!codec_ctx_) {
        std::cerr << "Could not allocate codec context" << std::endl;
        return -1;
    }
    
    // 设置编码参数
    codec_ctx_->sample_rate = config.sample_rate;
    codec_ctx_->channels = config.channels;
    codec_ctx_->channel_layout = av_get_default_channel_layout(config.channels);
    codec_ctx_->sample_fmt = config.sample_fmt;
    codec_ctx_->bit_rate = config.bitrate;
    codec_ctx_->time_base = {1, config.sample_rate};
    
    // 打开编码器
    int ret = avcodec_open2(codec_ctx_, codec_, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not open codec: " << errbuf << std::endl;
        avcodec_free_context(&codec_ctx_);
        return ret;
    }
    
    initialized_ = true;
    return 0;
}

int AudioEncoder::encode(const AVFrame* frame, AVPacket* pkt) {
    if (!initialized_) {
        std::cerr << "Encoder not initialized" << std::endl;
        return -1;
    }
    
    // 发送帧到编码器
    int ret = avcodec_send_frame(codec_ctx_, frame);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error sending frame: " << errbuf << std::endl;
        return ret;
    }
    
    // 接收编码后的数据包
    ret = avcodec_receive_packet(codec_ctx_, pkt);
    if (ret < 0) {
        if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
            return ret;
        }
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error receiving packet: " << errbuf << std::endl;
        return ret;
    }
    
    return 0;
}

int AudioEncoder::flush(std::vector<AVPacket*>& packets) {
    if (!initialized_) {
        return -1;
    }
    
    // 发送NULL帧刷新编码器
    int ret = avcodec_send_frame(codec_ctx_, nullptr);
    if (ret < 0) {
        return ret;
    }
    
    // 接收所有剩余的数据包
    while (true) {
        AVPacket* pkt = av_packet_alloc();
        ret = avcodec_receive_packet(codec_ctx_, pkt);
        if (ret == AVERROR_EOF || ret == AVERROR(EAGAIN)) {
            av_packet_free(&pkt);
            break;
        }
        if (ret < 0) {
            av_packet_free(&pkt);
            return ret;
        }
        packets.push_back(pkt);
    }
    
    return 0;
}

const char* AudioEncoder::getName() const {
    return codec_ ? codec_->name : "unknown";
}

void AudioEncoder::close() {
    if (codec_ctx_) {
        avcodec_free_context(&codec_ctx_);
        codec_ctx_ = nullptr;
    }
    codec_ = nullptr;
    initialized_ = false;
}
```

### 3.4 复用器实现

#### 头文件 (include/muxer.h)
```cpp
#pragma once

#include <memory>
#include <string>
#include <vector>
#include "codec_types.h"

extern "C" {
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
}

class Muxer {
public:
    Muxer();
    ~Muxer();
    
    // 初始化复用器
    int init(const MuxerConfig& config);
    
    // 添加流
    int addStream(const AVCodecContext* codec_ctx);
    
    // 写入文件头
    int writeHeader();
    
    // 写入数据包
    int writePacket(AVPacket* pkt);
    
    // 写入文件尾
    int writeTrailer();
    
    // 关闭复用器
    void close();
    
private:
    AVFormatContext* fmt_ctx_;
    bool initialized_;
    bool header_written_;
};
```

#### 源文件 (src/muxer.cpp)
```cpp
#include "muxer.h"
#include <iostream>

Muxer::Muxer() 
    : fmt_ctx_(nullptr), initialized_(false), header_written_(false) {
}

Muxer::~Muxer() {
    close();
}

int Muxer::init(const MuxerConfig& config) {
    if (initialized_) {
        std::cerr << "Muxer already initialized" << std::endl;
        return -1;
    }
    
    // 分配输出格式上下文
    int ret = avformat_alloc_output_context2(&fmt_ctx_, nullptr, 
                                              config.format, 
                                              config.filename);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not allocate output context: " << errbuf << std::endl;
        return ret;
    }
    
    initialized_ = true;
    return 0;
}

int Muxer::addStream(const AVCodecContext* codec_ctx) {
    if (!initialized_) {
        std::cerr << "Muxer not initialized" << std::endl;
        return -1;
    }
    
    // 创建新流
    AVStream* stream = avformat_new_stream(fmt_ctx_, nullptr);
    if (!stream) {
        std::cerr << "Could not create stream" << std::endl;
        return -1;
    }
    
    // 复制编解码器参数到流
    int ret = avcodec_parameters_from_context(stream->codecpar, codec_ctx);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not copy codec parameters: " << errbuf << std::endl;
        return ret;
    }
    
    stream->time_base = codec_ctx->time_base;
    
    return 0;
}

int Muxer::writeHeader() {
    if (!initialized_) {
        std::cerr << "Muxer not initialized" << std::endl;
        return -1;
    }
    
    if (header_written_) {
        std::cerr << "Header already written" << std::endl;
        return -1;
    }
    
    // 打开输出文件
    int ret = avio_open(&fmt_ctx_->pb, fmt_ctx_->url, AVIO_FLAG_WRITE);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not open output file: " << errbuf << std::endl;
        return ret;
    }
    
    // 写入文件头
    ret = avformat_write_header(fmt_ctx_, nullptr);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Could not write header: " << errbuf << std::endl;
        avio_closep(&fmt_ctx_->pb);
        return ret;
    }
    
    header_written_ = true;
    return 0;
}

int Muxer::writePacket(AVPacket* pkt) {
    if (!initialized_ || !header_written_) {
        std::cerr << "Muxer not ready" << std::endl;
        return -1;
    }
    
    // 写入数据包
    int ret = av_interleaved_write_frame(fmt_ctx_, pkt);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error writing packet: " << errbuf << std::endl;
        return ret;
    }
    
    return 0;
}

int Muxer::writeTrailer() {
    if (!initialized_ || !header_written_) {
        std::cerr << "Muxer not ready" << std::endl;
        return -1;
    }
    
    // 写入文件尾
    int ret = av_write_trailer(fmt_ctx_);
    if (ret < 0) {
        char errbuf[AV_ERROR_MAX_STRING_SIZE];
        av_strerror(ret, errbuf, sizeof(errbuf));
        std::cerr << "Error writing trailer: " << errbuf << std::endl;
        return ret;
    }
    
    header_written_ = false;
    return 0;
}

void Muxer::close() {
    if (fmt_ctx_) {
        if (header_written_) {
            av_write_trailer(fmt_ctx_);
        }
        if (!(fmt_ctx_->oformat->flags & AVFMT_NOFILE)) {
            avio_closep(&fmt_ctx_->pb);
        }
        avformat_free_context(fmt_ctx_);
        fmt_ctx_ = nullptr;
    }
    initialized_ = false;
    header_written_ = false;
}
```

## 4. 类型定义

### 4.1 codec_types.h

```cpp
#pragma once

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/pixfmt.h>
#include <libavutil/samplefmt.h>
}

// 视频编码器配置
struct VideoEncoderConfig {
    int width = 1920;
    int height = 1080;
    int fps = 30;
    int64_t bitrate = 2000000;
    int gop_size = 30;
    int max_b_frames = 3;
    AVPixelFormat pix_fmt = AV_PIX_FMT_YUV420P;
    const char* preset = "medium";
    const char* profile = "high";
};

// 视频解码器配置
struct VideoDecoderConfig {
    AVCodecID codec_id = AV_CODEC_ID_H264;
    int width = 0;
    int height = 0;
    AVPixelFormat pix_fmt = AV_PIX_FMT_YUV420P;
};

// 音频编码器配置
struct AudioEncoderConfig {
    int sample_rate = 44100;
    int channels = 2;
    int64_t bitrate = 128000;
    AVSampleFormat sample_fmt = AV_SAMPLE_FMT_FLTP;
};

// 音频解码器配置
struct AudioDecoderConfig {
    AVCodecID codec_id = AV_CODEC_ID_AAC;
    int sample_rate = 44100;
    int channels = 2;
    AVSampleFormat sample_fmt = AV_SAMPLE_FMT_FLTP;
};

// 复用器配置
struct MuxerConfig {
    const char* filename = nullptr;
    const char* format = nullptr;
};

// 解复用器配置
struct DemuxerConfig {
    const char* filename = nullptr;
};
```

## 5. 工具函数

### 5.1 utils.h

```cpp
#pragma once

#include <string>
#include <vector>
#include "codec_types.h"

extern "C" {
#include <libavutil/frame.h>
#include <libavutil/imgutils.h>
}

namespace utils {
    // 读取YUV文件
    int readYUVFile(const char* filename, std::vector<uint8_t>& buffer, 
                    int width, int height);
    
    // 写入YUV文件
    int writeYUVFile(const char* filename, const AVFrame* frame);
    
    // 创建测试帧
    AVFrame* createTestFrame(int width, int height, int frame_number);
    
    // 保存PPM图像
    int savePPM(const char* filename, const AVFrame* frame);
    
    // 打印帧信息
    void printFrameInfo(const AVFrame* frame);
    
    // 打印数据包信息
    void printPacketInfo(const AVPacket* pkt);
}
```

### 5.2 utils.cpp

```cpp
#include "utils.h"
#include <iostream>
#include <fstream>
#include <cmath>

extern "C" {
#include <libavutil/imgutils.h>
}

namespace utils {

int readYUVFile(const char* filename, std::vector<uint8_t>& buffer, 
                int width, int height) {
    // 计算YUV420P大小
    int y_size = width * height;
    int uv_size = (width / 2) * (height / 2);
    int total_size = y_size + uv_size * 2;
    
    // 读取文件
    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Could not open file: " << filename << std::endl;
        return -1;
    }
    
    buffer.resize(total_size);
    file.read(reinterpret_cast<char*>(buffer.data()), total_size);
    
    return file.gcount();
}

int writeYUVFile(const char* filename, const AVFrame* frame) {
    std::ofstream file(filename, std::ios::binary | std::ios::app);
    if (!file.is_open()) {
        std::cerr << "Could not open file: " << filename << std::endl;
        return -1;
    }
    
    // 写入Y分量
    for (int y = 0; y < frame->height; y++) {
        file.write(reinterpret_cast<const char*>(frame->data[0] + y * frame->linesize[0]),
                   frame->width);
    }
    
    // 写入U分量
    for (int y = 0; y < frame->height / 2; y++) {
        file.write(reinterpret_cast<const char*>(frame->data[1] + y * frame->linesize[1]),
                   frame->width / 2);
    }
    
    // 写入V分量
    for (int y = 0; y < frame->height / 2; y++) {
        file.write(reinterpret_cast<const char*>(frame->data[2] + y * frame->linesize[2]),
                   frame->width / 2);
    }
    
    return 0;
}

AVFrame* createTestFrame(int width, int height, int frame_number) {
    AVFrame* frame = av_frame_alloc();
    if (!frame) {
        return nullptr;
    }
    
    frame->format = AV_PIX_FMT_YUV420P;
    frame->width = width;
    frame->height = height;
    
    int ret = av_frame_get_buffer(frame, 0);
    if (ret < 0) {
        av_frame_free(&frame);
        return nullptr;
    }
    
    // 填充Y分量 (灰度渐变)
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            frame->data[0][y * frame->linesize[0] + x] = 
                (x + y + frame_number * 3) % 256;
        }
    }
    
    // 填充U分量
    for (int y = 0; y < height / 2; y++) {
        for (int x = 0; x < width / 2; x++) {
            frame->data[1][y * frame->linesize[1] + x] = 128;
        }
    }
    
    // 填充V分量
    for (int y = 0; y < height / 2; y++) {
        for (int x = 0; x < width / 2; x++) {
            frame->data[2][y * frame->linesize[2] + x] = 128;
        }
    }
    
    frame->pts = frame_number;
    
    return frame;
}

int savePPM(const char* filename, const AVFrame* frame) {
    std::ofstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        return -1;
    }
    
    // PPM头
    file << "P6\n" << frame->width << " " << frame->height << "\n255\n";
    
    // YUV转RGB并写入
    for (int y = 0; y < frame->height; y++) {
        for (int x = 0; x < frame->width; x++) {
            int Y = frame->data[0][y * frame->linesize[0] + x];
            int U = frame->data[1][(y/2) * frame->linesize[1] + (x/2)] - 128;
            int V = frame->data[2][(y/2) * frame->linesize[2] + (x/2)] - 128;
            
            int R = Y + 1.402 * V;
            int G = Y - 0.344 * U - 0.714 * V;
            int B = Y + 1.772 * U;
            
            R = std::max(0, std::min(255, R));
            G = std::max(0, std::min(255, G));
            B = std::max(0, std::min(255, B));
            
            file.put(R);
            file.put(G);
            file.put(B);
        }
    }
    
    return 0;
}

void printFrameInfo(const AVFrame* frame) {
    std::cout << "Frame Info:" << std::endl;
    std::cout << "  Format: " << frame->format << std::endl;
    std::cout << "  Width: " << frame->width << std::endl;
    std::cout << "  Height: " << frame->height << std::endl;
    std::cout << "  PTS: " << frame->pts << std::endl;
    std::cout << "  Key Frame: " << (frame->key_frame ? "Yes" : "No") << std::endl;
}

void printPacketInfo(const AVPacket* pkt) {
    std::cout << "Packet Info:" << std::endl;
    std::cout << "  Size: " << pkt->size << std::endl;
    std::cout << "  PTS: " << pkt->pts << std::endl;
    std::cout << "  DTS: " << pkt->dts << std::endl;
    std::cout << "  Duration: " << pkt->duration << std::endl;
    std::cout << "  Key Packet: " << (pkt->flags & AV_PKT_FLAG_KEY ? "Yes" : "No") << std::endl;
}

} // namespace utils
```

## 6. 编译和测试

### 6.1 编译命令

```bash
# 创建构建目录
mkdir -p build && cd build

# 配置
cmake ..

# 编译
make -j$(nproc)

# 运行测试
make test
```

### 6.2 运行示例

```bash
# 视频编码示例
./build/bin/video_encoder_example

# 音频编码示例
./build/bin/audio_encoder_example

# 容器封装示例
./build/bin/muxer_example
```

## 7. 常见问题

### 7.1 编译错误

**问题**: 找不到FFmpeg库
```bash
# 解决方案
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH
```

**问题**: 链接错误
```bash
# 解决方案
cmake -DCMAKE_LIBRARY_PATH=/usr/local/lib ..
```

### 7.2 运行错误

**问题**: 编码器初始化失败
- 检查参数是否正确
- 检查编码器是否支持该格式

**问题**: 内存泄漏
- 确保所有分配的资源都被释放
- 使用RAII包装器
