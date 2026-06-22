# 01 - 调研文档

## 1. 技术背景

### 1.1 音视频编解码概述

音视频编解码是多媒体技术的核心，主要解决以下问题：
- **数据压缩**: 原始音视频数据量巨大，需要压缩才能存储和传输
- **格式兼容**: 不同设备和平台需要统一的编码格式
- **质量平衡**: 在压缩率和质量之间找到最佳平衡点

### 1.2 原始数据量计算

#### 视频数据量
```
数据量 = 分辨率 × 像素位深 × 帧率 × 时长

示例：1080p YUV420 30fps 1分钟
- Y分量: 1920 × 1080 × 1 = 2,073,600 字节/帧
- U分量: 960 × 540 × 1 = 518,400 字节/帧
- V分量: 960 × 540 × 1 = 518,400 字节/帧
- 每帧: 3,110,400 字节 ≈ 3 MB
- 每秒: 3 × 30 = 90 MB
- 每分钟: 90 × 60 = 5.4 GB
```

#### 音频数据量
```
数据量 = 采样率 × 位深 × 声道数 × 时长

示例：44.1kHz 16bit 立体声 1分钟
- 每秒: 44100 × 2 × 2 = 176,400 字节 ≈ 172 KB
- 每分钟: 172 × 60 = 10.3 MB
```

### 1.3 压缩的必要性

| 内容 | 原始大小 | 压缩后 | 压缩率 |
|------|----------|--------|--------|
| 1分钟1080p视频 | 5.4 GB | ~100 MB | 54:1 |
| 1分钟CD音频 | 10.3 MB | ~1 MB | 10:1 |

## 2. 视频编码技术调研

### 2.1 H.264/AVC

#### 技术特点
- **标准**: ITU-T H.264 / ISO/IEC 14496-10
- **发布时间**: 2003年
- **应用**: 蓝光、流媒体、视频会议

#### 核心技术
1. **帧内预测**: 利用空间相关性
2. **帧间预测**: 利用时间相关性
3. **变换编码**: DCT变换
4. **量化**: 有损压缩
5. **熵编码**: CAVLC/CABAC

#### 编码档次
| 档次 | 特点 | 应用场景 |
|------|------|----------|
| Baseline | 无B帧，无CABAC | 视频通话 |
| Main | B帧，CABAC | 标清电视 |
| High | 8x8变换，自适应量化 | 蓝光，HDTV |

### 2.2 H.265/HEVC

#### 技术特点
- **标准**: ITU-T H.265 / ISO/IEC 23008-2
- **发布时间**: 2013年
- **优势**: 相比H.264节省50%码率

#### 核心改进
1. **CTU划分**: 支持64x64编码树单元
2. **更多预测模式**: 35种帧内预测方向
3. **高级运动补偿**: 更精确的运动向量
4. **并行处理**: Tiles和WPP

### 2.3 VP9/AV1

#### VP9
- Google开发
- 开源免费
- YouTube主要使用

#### AV1
- AOM联盟开发
- 免版税
- 压缩效率优于H.265

## 3. 音频编码技术调研

### 3.1 AAC (Advanced Audio Coding)

#### 技术特点
- **标准**: ISO/IEC 14496-3
- **优势**: 相比MP3提升30%压缩率
- **应用**: Apple Music, YouTube, 广播

#### 编码类型
| 类型 | 复杂度 | 码率范围 | 应用 |
|------|--------|----------|------|
| AAC-LC | 低 | 64-256 kbps | 通用 |
| HE-AAC | 中 | 32-128 kbps | 流媒体 |
| HE-AAC v2 | 中 | 16-64 kbps | 低码率 |

#### 编码流程
```
输入PCM → 心理声学模型 → MDCT → 量化 → 哈夫曼编码 → 输出
```

### 3.2 Opus

#### 技术特点
- **标准**: RFC 6716
- **优势**: 低延迟，高质量
- **应用**: WebRTC, VoIP

#### 技术组成
- SILK: 语音编码
- CELT: 音乐编码

### 3.3 MP3

#### 技术特点
- **标准**: ISO/IEC 11172-3
- **状态**: 逐渐被AAC取代
- **兼容性**: 几乎所有设备支持

## 4. 容器格式调研

### 4.1 MP4

#### 结构特点
- 基于box的树状结构
- 支持随机访问
- 广泛兼容

#### 主要box
```
ftyp: 文件类型
moov: 元数据
  mvhd: 影片头
  trak: 轨道
    tkhd: 轨道头
    mdia: 媒体
      mdhd: 媒体头
      hdlr: 处理器
      minf: 媒体信息
        stbl: 采样表
          stsd: 采样描述
          stts: 时间戳
          stsc: 采样到chunk映射
          stsz: 采样大小
          stco: chunk偏移
mdat: 媒体数据
```

### 4.2 FLV

#### 结构特点
- 流媒体格式
- 适合网络传输
- 结构简单

#### 文件结构
```
FLV Header (9字节)
PreviousTagSize0 (4字节)
Tag1
PreviousTagSize1 (4字节)
Tag2
...
```

### 4.3 MKV (Matroska)

#### 结构特点
- 开源格式
- 支持多音轨、多字幕
- 功能强大

### 4.4 TS (MPEG-TS)

#### 结构特点
- 传输流格式
- 支持实时传输
- 抗丢包能力强

## 5. FFmpeg框架调研

### 5.1 核心组件

| 组件 | 功能 | 库 |
|------|------|-----|
| libavformat | 容器格式处理 | muxer/demuxer |
| libavcodec | 编解码器 | encoder/decoder |
| libavutil | 工具函数 | 通用工具 |
| libswscale | 图像缩放 | 像素格式转换 |
| libswresample | 音频重采样 | 采样格式转换 |
| libavfilter | 滤镜 | 音视频处理 |

### 5.2 核心数据结构

```cpp
AVFormatContext  // 格式上下文
├── AVStream     // 流
│   └── AVCodecContext  // 编解码器上下文
├── AVPacket     // 编码数据包
└── AVIOContext   // IO上下文

AVCodecContext   // 编解码器上下文
├── AVCodec      // 编解码器
├── AVFrame      // 帧数据
└── AVPacket     // 编码数据包
```

### 5.3 API使用模式

#### 编码模式
```cpp
// 创建上下文
AVCodecContext *ctx = avcodec_alloc_context3(codec);

// 设置参数
ctx->width = width;
ctx->height = height;

// 打开编码器
avcodec_open2(ctx, codec, NULL);

// 编码循环
avcodec_send_frame(ctx, frame);
avcodec_receive_packet(ctx, pkt);
```

#### 解码模式
```cpp
// 创建上下文
AVCodecContext *ctx = avcodec_alloc_context3(codec);

// 打开解码器
avcodec_open2(ctx, codec, NULL);

// 解码循环
avcodec_send_packet(ctx, pkt);
avcodec_receive_frame(ctx, frame);
```

## 6. 技术选型

### 6.1 编码格式选择

| 需求 | 推荐格式 | 理由 |
|------|----------|------|
| 通用视频 | H.264 | 兼容性最好 |
| 高效压缩 | H.265 | 节省50%码率 |
| 开源免费 | VP9/AV1 | 无版税 |
| 通用音频 | AAC-LC | 广泛支持 |
| 低码率 | HE-AAC | 质量好 |
| 低延迟 | Opus | 延迟最低 |

### 6.2 容器格式选择

| 需求 | 推荐格式 | 理由 |
|------|----------|------|
| 通用存储 | MP4 | 兼容性最好 |
| 流媒体 | FLV | 适合网络 |
| 高质量 | MKV | 功能强大 |
| 广播 | TS | 抗丢包 |

### 6.3 开发框架选择

| 选项 | 优点 | 缺点 |
|------|------|------|
| FFmpeg | 功能全面，文档丰富 | 学习曲线陡峭 |
| GStreamer | 插件架构灵活 | 依赖较多 |
| 自研 | 完全控制 | 工作量巨大 |

**选择**: FFmpeg - 最成熟的开源多媒体框架

## 7. 风险评估

### 7.1 技术风险
- H.264/H.265专利问题（学习项目可忽略）
- FFmpeg API复杂度高
- 音视频同步难度大

### 7.2 缓解措施
- 先实现简单功能，逐步完善
- 参考FFmpeg官方示例
- 使用现有测试数据

## 8. 参考资源

1. [FFmpeg官方文档](https://ffmpeg.org/documentation.html)
2. [FFmpeg示例代码](https://github.com/FFmpeg/FFmpeg/tree/master/doc/examples)
3. [H.264标准文档](https://www.itu.int/rec/T-REC-H.264)
4. [AAC标准文档](https://www.iso.org/standard/43345.html)
5. [MP4格式规范](https://www.iso.org/standard/75928.html)
