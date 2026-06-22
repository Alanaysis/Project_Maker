# 04 - 测试文档

## 1. 测试策略

### 1.1 测试层次

```
┌─────────────────────────────────────────────────────────┐
│                    系统测试                               │
│              完整编码-解码流程测试                          │
├─────────────────────────────────────────────────────────┤
│                    集成测试                               │
│            模块间接口和交互测试                             │
├─────────────────────────────────────────────────────────┤
│                    单元测试                               │
│              单个模块功能测试                               │
└─────────────────────────────────────────────────────────┘
```

### 1.2 测试类型

| 类型 | 目的 | 工具 |
|------|------|------|
| 单元测试 | 测试单个函数/类 | Google Test / CTest |
| 集成测试 | 测试模块交互 | 手动/脚本 |
| 系统测试 | 测试完整流程 | 脚本 |
| 性能测试 | 测试性能指标 | 自定义工具 |
| 回归测试 | 确保修改不引入问题 | CI/CD |

## 2. 单元测试

### 2.1 视频编码器测试

#### 测试用例

```cpp
// test_video_codec.cpp

#include <gtest/gtest.h>
#include "video_encoder.h"
#include "video_decoder.h"
#include "utils.h"

class VideoEncoderTest : public ::testing::Test {
protected:
    void SetUp() override {
        encoder = std::make_unique<VideoEncoder>();
        config.width = 320;
        config.height = 240;
        config.fps = 30;
        config.bitrate = 500000;
        config.gop_size = 30;
        config.max_b_frames = 0;
        config.preset = "ultrafast";
    }
    
    void TearDown() override {
        encoder->close();
    }
    
    std::unique_ptr<VideoEncoder> encoder;
    VideoEncoderConfig config;
};

// 测试初始化
TEST_F(VideoEncoderTest, InitSuccess) {
    int ret = encoder->init(config);
    EXPECT_EQ(ret, 0);
}

// 测试重复初始化
TEST_F(VideoEncoderTest, InitTwice) {
    EXPECT_EQ(encoder->init(config), 0);
    EXPECT_EQ(encoder->init(config), -1);
}

// 测试编码单帧
TEST_F(VideoEncoderTest, EncodeSingleFrame) {
    ASSERT_EQ(encoder->init(config), 0);
    
    AVFrame* frame = utils::createTestFrame(config.width, config.height, 0);
    ASSERT_NE(frame, nullptr);
    
    AVPacket* pkt = av_packet_alloc();
    ASSERT_NE(pkt, nullptr);
    
    int ret = encoder->encode(frame, pkt);
    EXPECT_EQ(ret, 0);
    EXPECT_GT(pkt->size, 0);
    
    av_frame_free(&frame);
    av_packet_free(&pkt);
}

// 测试编码多帧
TEST_F(VideoEncoderTest, EncodeMultipleFrames) {
    ASSERT_EQ(encoder->init(config), 0);
    
    for (int i = 0; i < 10; i++) {
        AVFrame* frame = utils::createTestFrame(config.width, config.height, i);
        ASSERT_NE(frame, nullptr);
        
        AVPacket* pkt = av_packet_alloc();
        ASSERT_NE(pkt, nullptr);
        
        int ret = encoder->encode(frame, pkt);
        EXPECT_EQ(ret, 0);
        
        av_frame_free(&frame);
        av_packet_free(&pkt);
    }
}

// 测试刷新编码器
TEST_F(VideoEncoderTest, FlushEncoder) {
    ASSERT_EQ(encoder->init(config), 0);
    
    // 编码几帧
    for (int i = 0; i < 5; i++) {
        AVFrame* frame = utils::createTestFrame(config.width, config.height, i);
        AVPacket* pkt = av_packet_alloc();
        encoder->encode(frame, pkt);
        av_frame_free(&frame);
        av_packet_free(&pkt);
    }
    
    // 刷新
    std::vector<AVPacket*> packets;
    int ret = encoder->flush(packets);
    EXPECT_EQ(ret, 0);
    
    // 清理
    for (auto* pkt : packets) {
        av_packet_free(&pkt);
    }
}

// 测试获取编码器名称
TEST_F(VideoEncoderTest, GetEncoderName) {
    ASSERT_EQ(encoder->init(config), 0);
    const char* name = encoder->getName();
    EXPECT_NE(name, nullptr);
    EXPECT_STREQ(name, "libx264");
}
```

### 2.2 视频解码器测试

```cpp
// test_video_decoder.cpp

#include <gtest/gtest.h>
#include "video_encoder.h"
#include "video_decoder.h"
#include "utils.h"

class VideoDecoderTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 先编码一帧
        encoder = std::make_unique<VideoEncoder>();
        VideoEncoderConfig enc_config;
        enc_config.width = 320;
        enc_config.height = 240;
        enc_config.fps = 30;
        enc_config.bitrate = 500000;
        enc_config.gop_size = 30;
        enc_config.max_b_frames = 0;
        enc_config.preset = "ultrafast";
        
        ASSERT_EQ(encoder->init(enc_config), 0);
        
        // 编码一帧
        AVFrame* frame = utils::createTestFrame(enc_config.width, enc_config.height, 0);
        AVPacket* pkt = av_packet_alloc();
        ASSERT_EQ(encoder->encode(frame, pkt), 0);
        
        // 初始化解码器
        decoder = std::make_unique<VideoDecoder>();
        decoder_config.codec_id = AV_CODEC_ID_H264;
        decoder_config.width = enc_config.width;
        decoder_config.height = enc_config.height;
        decoder_config.pix_fmt = AV_PIX_FMT_YUV420P;
        
        encoded_pkt = pkt;
        av_frame_free(&frame);
    }
    
    void TearDown() override {
        encoder->close();
        decoder->close();
        av_packet_free(&encoded_pkt);
    }
    
    std::unique_ptr<VideoEncoder> encoder;
    std::unique_ptr<VideoDecoder> decoder;
    VideoDecoderConfig decoder_config;
    AVPacket* encoded_pkt;
};

// 测试解码器初始化
TEST_F(VideoDecoderTest, InitSuccess) {
    int ret = decoder->init(decoder_config);
    EXPECT_EQ(ret, 0);
}

// 测试解码单帧
TEST_F(VideoDecoderTest, DecodeSingleFrame) {
    ASSERT_EQ(decoder->init(decoder_config), 0);
    
    AVFrame* frame = av_frame_alloc();
    ASSERT_NE(frame, nullptr);
    
    int ret = decoder->decode(encoded_pkt, frame);
    EXPECT_EQ(ret, 0);
    EXPECT_GT(frame->width, 0);
    EXPECT_GT(frame->height, 0);
    
    av_frame_free(&frame);
}

// 测试编解码往返
TEST_F(VideoDecoderTest, EncodeDecodeRoundTrip) {
    // 编码
    AVFrame* original = utils::createTestFrame(320, 240, 0);
    AVPacket* pkt = av_packet_alloc();
    ASSERT_EQ(encoder->encode(original, pkt), 0);
    
    // 解码
    ASSERT_EQ(decoder->init(decoder_config), 0);
    AVFrame* decoded = av_frame_alloc();
    ASSERT_EQ(decoder->decode(pkt, decoded), 0);
    
    // 验证尺寸
    EXPECT_EQ(decoded->width, original->width);
    EXPECT_EQ(decoded->height, original->height);
    EXPECT_EQ(decoded->format, original->format);
    
    av_frame_free(&original);
    av_frame_free(&decoded);
    av_packet_free(&pkt);
}
```

### 2.3 音频编码器测试

```cpp
// test_audio_codec.cpp

#include <gtest/gtest.h>
#include "audio_encoder.h"
#include "audio_decoder.h"

class AudioEncoderTest : public ::testing::Test {
protected:
    void SetUp() override {
        encoder = std::make_unique<AudioEncoder>();
        config.sample_rate = 44100;
        config.channels = 2;
        config.bitrate = 128000;
        config.sample_fmt = AV_SAMPLE_FMT_FLTP;
    }
    
    void TearDown() override {
        encoder->close();
    }
    
    std::unique_ptr<AudioEncoder> encoder;
    AudioEncoderConfig config;
    
    // 创建测试音频帧
    AVFrame* createTestAudioFrame() {
        AVFrame* frame = av_frame_alloc();
        frame->format = config.sample_fmt;
        frame->channels = config.channels;
        frame->channel_layout = av_get_default_channel_layout(config.channels);
        frame->sample_rate = config.sample_rate;
        frame->nb_samples = 1024;
        
        av_frame_get_buffer(frame, 0);
        
        // 填充正弦波数据
        for (int ch = 0; ch < config.channels; ch++) {
            float* data = (float*)frame->data[ch];
            for (int i = 0; i < frame->nb_samples; i++) {
                data[i] = sin(2 * M_PI * 440 * i / config.sample_rate) * 0.5;
            }
        }
        
        return frame;
    }
};

// 测试初始化
TEST_F(AudioEncoderTest, InitSuccess) {
    int ret = encoder->init(config);
    EXPECT_EQ(ret, 0);
}

// 测试编码单帧
TEST_F(AudioEncoderTest, EncodeSingleFrame) {
    ASSERT_EQ(encoder->init(config), 0);
    
    AVFrame* frame = createTestAudioFrame();
    ASSERT_NE(frame, nullptr);
    
    AVPacket* pkt = av_packet_alloc();
    ASSERT_NE(pkt, nullptr);
    
    int ret = encoder->encode(frame, pkt);
    EXPECT_EQ(ret, 0);
    EXPECT_GT(pkt->size, 0);
    
    av_frame_free(&frame);
    av_packet_free(&pkt);
}

// 测试编码多帧
TEST_F(AudioEncoderTest, EncodeMultipleFrames) {
    ASSERT_EQ(encoder->init(config), 0);
    
    for (int i = 0; i < 10; i++) {
        AVFrame* frame = createTestAudioFrame();
        AVPacket* pkt = av_packet_alloc();
        
        int ret = encoder->encode(frame, pkt);
        EXPECT_EQ(ret, 0);
        
        av_frame_free(&frame);
        av_packet_free(&pkt);
    }
}
```

### 2.4 复用器测试

```cpp
// test_muxer.cpp

#include <gtest/gtest.h>
#include "muxer.h"
#include "demuxer.h"
#include "video_encoder.h"
#include "audio_encoder.h"

class MuxerTest : public ::testing::Test {
protected:
    void SetUp() override {
        muxer = std::make_unique<Muxer>();
        output_file = "test_output.mp4";
    }
    
    void TearDown() override {
        muxer->close();
        remove(output_file.c_str());
    }
    
    std::unique_ptr<Muxer> muxer;
    std::string output_file;
};

// 测试初始化
TEST_F(MuxerTest, InitSuccess) {
    MuxerConfig config;
    config.filename = output_file.c_str();
    config.format = "mp4";
    
    int ret = muxer->init(config);
    EXPECT_EQ(ret, 0);
}

// 测试添加流
TEST_F(MuxerTest, AddStream) {
    MuxerConfig config;
    config.filename = output_file.c_str();
    config.format = "mp4";
    
    ASSERT_EQ(muxer->init(config), 0);
    
    // 创建视频编码器上下文
    VideoEncoder encoder;
    VideoEncoderConfig enc_config;
    enc_config.width = 320;
    enc_config.height = 240;
    ASSERT_EQ(encoder.init(enc_config), 0);
    
    // 添加流
    // 注意：需要获取AVCodecContext指针
    // 这里简化处理
}

// 测试写入文件头尾
TEST_F(MuxerTest, WriteHeaderTrailer) {
    MuxerConfig config;
    config.filename = output_file.c_str();
    config.format = "mp4";
    
    ASSERT_EQ(muxer->init(config), 0);
    
    // 添加流（需要先添加至少一个流）
    // ...
    
    int ret = muxer->writeHeader();
    EXPECT_EQ(ret, 0);
    
    ret = muxer->writeTrailer();
    EXPECT_EQ(ret, 0);
}
```

## 3. 集成测试

### 3.1 完整编码解码流程测试

```cpp
// test_integration.cpp

#include <gtest/gtest.h>
#include "video_encoder.h"
#include "video_decoder.h"
#include "audio_encoder.h"
#include "muxer.h"
#include "demuxer.h"
#include "utils.h"

class IntegrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        output_file = "integration_test.mp4";
    }
    
    void TearDown() override {
        remove(output_file.c_str());
    }
    
    std::string output_file;
};

// 测试视频编码封装流程
TEST_F(IntegrationTest, VideoEncodeMux) {
    // 1. 初始化视频编码器
    VideoEncoder encoder;
    VideoEncoderConfig enc_config;
    enc_config.width = 320;
    enc_config.height = 240;
    enc_config.fps = 30;
    enc_config.bitrate = 500000;
    enc_config.gop_size = 30;
    enc_config.max_b_frames = 0;
    enc_config.preset = "ultrafast";
    
    ASSERT_EQ(encoder.init(enc_config), 0);
    
    // 2. 初始化复用器
    Muxer muxer;
    MuxerConfig mux_config;
    mux_config.filename = output_file.c_str();
    mux_config.format = "mp4";
    
    ASSERT_EQ(muxer.init(mux_config), 0);
    
    // 3. 编码和封装循环
    for (int i = 0; i < 30; i++) {
        // 创建测试帧
        AVFrame* frame = utils::createTestFrame(enc_config.width, 
                                                 enc_config.height, i);
        ASSERT_NE(frame, nullptr);
        
        // 编码
        AVPacket* pkt = av_packet_alloc();
        int ret = encoder.encode(frame, pkt);
        ASSERT_EQ(ret, 0);
        
        // 写入复用器
        ret = muxer.writePacket(pkt);
        ASSERT_EQ(ret, 0);
        
        av_frame_free(&frame);
        av_packet_free(&pkt);
    }
    
    // 4. 刷新编码器
    std::vector<AVPacket*> packets;
    encoder.flush(packets);
    for (auto* pkt : packets) {
        muxer.writePacket(pkt);
        av_packet_free(&pkt);
    }
    
    // 5. 完成
    muxer.writeTrailer();
    muxer.close();
    encoder.close();
    
    // 验证输出文件存在
    EXPECT_TRUE(std::filesystem::exists(output_file));
}

// 测试音视频同步封装
TEST_F(IntegrationTest, AudioVideoMux) {
    // 类似上面的测试，但同时编码音频和视频
    // 注意：需要处理时间戳同步
}
```

## 4. 性能测试

### 4.1 编码性能测试

```cpp
// test_performance.cpp

#include <gtest/gtest.h>
#include "video_encoder.h"
#include "utils.h"
#include <chrono>

class PerformanceTest : public ::testing::Test {
protected:
    void SetUp() override {
        encoder = std::make_unique<VideoEncoder>();
        config.width = 1920;
        config.height = 1080;
        config.fps = 30;
        config.bitrate = 2000000;
        config.gop_size = 30;
        config.max_b_frames = 3;
        config.preset = "medium";
    }
    
    std::unique_ptr<VideoEncoder> encoder;
    VideoEncoderConfig config;
};

// 测试编码速度
TEST_F(PerformanceTest, EncodingSpeed) {
    ASSERT_EQ(encoder->init(config), 0);
    
    const int num_frames = 100;
    auto start = std::chrono::high_resolution_clock::now();
    
    for (int i = 0; i < num_frames; i++) {
        AVFrame* frame = utils::createTestFrame(config.width, config.height, i);
        AVPacket* pkt = av_packet_alloc();
        
        encoder->encode(frame, pkt);
        
        av_frame_free(&frame);
        av_packet_free(&pkt);
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    double fps = num_frames * 1000.0 / duration.count();
    std::cout << "Encoding speed: " << fps << " fps" << std::endl;
    std::cout << "Time per frame: " << duration.count() / num_frames << " ms" << std::endl;
    
    // 期望至少达到实时编码
    EXPECT_GT(fps, config.fps);
}

// 测试不同预设的性能
TEST_F(PerformanceTest, PresetComparison) {
    const char* presets[] = {"ultrafast", "superfast", "veryfast", "faster", 
                             "fast", "medium", "slow", "slower", "veryslow"};
    
    for (const char* preset : presets) {
        config.preset = preset;
        encoder->close();
        ASSERT_EQ(encoder->init(config), 0);
        
        auto start = std::chrono::high_resolution_clock::now();
        
        for (int i = 0; i < 30; i++) {
            AVFrame* frame = utils::createTestFrame(config.width, config.height, i);
            AVPacket* pkt = av_packet_alloc();
            encoder->encode(frame, pkt);
            av_frame_free(&frame);
            av_packet_free(&pkt);
        }
        
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        
        std::cout << "Preset " << preset << ": " 
                  << 30 * 1000.0 / duration.count() << " fps" << std::endl;
    }
}
```

### 4.2 内存使用测试

```cpp
// test_memory.cpp

#include <gtest/gtest.h>
#include "video_encoder.h"
#include "utils.h"

TEST(MemoryTest, NoMemoryLeak) {
    VideoEncoder encoder;
    VideoEncoderConfig config;
    config.width = 320;
    config.height = 240;
    config.fps = 30;
    config.bitrate = 500000;
    
    ASSERT_EQ(encoder.init(config), 0);
    
    // 编码1000帧
    for (int i = 0; i < 1000; i++) {
        AVFrame* frame = utils::createTestFrame(config.width, config.height, i);
        AVPacket* pkt = av_packet_alloc();
        
        encoder.encode(frame, pkt);
        
        av_frame_free(&frame);
        av_packet_free(&pkt);
    }
    
    encoder.close();
    
    // 使用valgrind或sanitizer检测内存泄漏
    // 编译时添加: -fsanitize=address
}
```

## 5. 测试运行

### 5.1 CMake测试配置

```cmake
# 启用测试
enable_testing()

# 添加测试
add_test(NAME test_video_codec COMMAND test_video_codec)
add_test(NAME test_audio_codec COMMAND test_audio_codec)
add_test(NAME test_muxer COMMAND test_muxer)
add_test(NAME test_integration COMMAND test_integration)
add_test(NAME test_performance COMMAND test_performance)
```

### 5.2 运行测试

```bash
# 运行所有测试
cd build
make test

# 或使用ctest
ctest

# 运行特定测试
./test_video_codec

# 运行带详细输出
ctest --verbose

# 运行特定测试用例
./test_video_codec --gtest_filter="VideoEncoderTest.EncodeSingleFrame"
```

### 5.3 测试覆盖率

```bash
# 编译时启用覆盖率
cmake -DCMAKE_CXX_FLAGS="--coverage" ..

# 运行测试
make test

# 生成覆盖率报告
gcov src/*.cpp
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_report
```

## 6. 测试数据

### 6.1 测试视频文件

```bash
# 生成测试YUV文件
ffmpeg -f lavfi -i testsrc=duration=10:size=320x240:rate=30 \
       -pix_fmt yuv420p test_input.yuv

# 生成测试音频文件
ffmpeg -f lavfi -i sine=frequency=440:duration=10 \
       -ar 44100 -ac 2 test_input.pcm
```

### 6.2 测试脚本

```bash
#!/bin/bash
# run_tests.sh

echo "Running unit tests..."
./test_video_codec
./test_audio_codec
./test_muxer

echo "Running integration tests..."
./test_integration

echo "Running performance tests..."
./test_performance

echo "All tests completed!"
```

## 7. 持续集成

### 7.1 GitHub Actions配置

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y cmake libavcodec-dev libavformat-dev \
            libavutil-dev libswscale-dev libswresample-dev
    
    - name: Build
      run: |
        mkdir build && cd build
        cmake ..
        make -j$(nproc)
    
    - name: Test
      run: |
        cd build
        ctest --verbose
```

## 8. 测试报告

### 8.1 测试结果模板

```
测试报告
========

测试时间: 2024-XX-XX XX:XX:XX
测试环境: Ubuntu 20.04, GCC 9.3.0

单元测试结果
-----------
- test_video_codec: PASSED (45 tests)
- test_audio_codec: PASSED (30 tests)
- test_muxer: PASSED (20 tests)

集成测试结果
-----------
- test_integration: PASSED (5 tests)

性能测试结果
-----------
- Encoding speed (1080p): 45 fps
- Memory usage: No leaks detected

总结
----
所有测试通过，代码质量良好。
```
