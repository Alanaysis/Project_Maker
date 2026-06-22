# 🎬 多媒体模块

> 音视频编解码、流媒体传输、多媒体处理相关项目

---

## 📋 项目列表

| 项目 | 描述 | 技术栈 | 难度 | 状态 |
|------|------|--------|------|------|
| [av-codec](av-codec/) | 音视频编解码器 | C++, FFmpeg | ⭐⭐⭐⭐⭐⭐ | ✅ 完成 |
| [media-server](media-server/) | 流媒体服务器 | Go | ⭐⭐⭐⭐⭐ | ✅ 完成 |

---

## 🛤️ 学习路径

### 推荐学习顺序

```
1. av-codec (编解码基础)
   │
   ├── 理解音视频编码原理
   ├── 学习容器格式 (MP4/FLV)
   └── 掌握 FFmpeg 使用
   │
   ▼
2. media-server (流媒体传输)
   │
   ├── 理解 RTMP/HLS 协议
   ├── 学习服务器架构
   └── 掌握推流拉流
```

### 学习目标

**阶段一：编解码基础**
- 理解 H.264/H.265 视频编码
- 理解 AAC 音频编码
- 掌握容器格式封装

**阶段二：流媒体传输**
- 理解 RTMP 协议原理
- 理解 HLS 协议原理
- 掌握流媒体服务器架构

---

## 🔧 技术栈说明

### 编解码技术

| 技术 | 用途 | 项目 |
|------|------|------|
| H.264/H.265 | 视频编码 | av-codec |
| AAC | 音频编码 | av-codec |
| FFmpeg | 多媒体处理 | av-codec |
| MP4/FLV | 容器格式 | av-codec |

### 流媒体技术

| 技术 | 用途 | 项目 |
|------|------|------|
| RTMP | 推流协议 | media-server |
| HLS | 拉流协议 | media-server |
| TCP | 传输层 | media-server |
| HTTP | 分发协议 | media-server |

---

## 📖 项目详情

### av-codec - 音视频编解码器

**核心功能**：
- H.264 视频编码
- AAC 音频编码
- MP4/FLV 容器封装
- 编解码完整流程

**快速开始**：
```bash
cd projects/av-codec
mkdir build && cd build
cmake ..
make
```

**学习要点**：
- 视频编码原理 (I/P/B 帧)
- 运动估计和运动补偿
- 容器格式封装
- FFmpeg API 使用

📖 [详细文档](av-codec/README.md)

---

### media-server - 流媒体服务器

**核心功能**：
- RTMP 推流服务
- HLS 拉流服务
- 多流并发管理
- M3U8 播放列表生成

**快速开始**：
```bash
cd projects/media-server
go mod tidy
go build ./cmd/server/

# 运行服务器
./media-server

# 推流测试
ffmpeg -re -i test.mp4 -c copy -f flv rtmp://localhost:1935/live/test

# 拉流测试
ffplay http://localhost:8080/live/test/index.m3u8
```

**学习要点**：
- RTMP 协议握手和消息解析
- AMF 编解码
- HLS 分片和播放列表
- 并发服务器设计

📖 [详细文档](media-server/README.md)

---

## 📚 学习资源

### 书籍

- 《音视频开发进阶指南》- 雷霄骅
- 《FFmpeg 从入门到精通》- 刘歧
- 《流媒体技术原理与应用》

### 在线课程

- [FFmpeg 官方文档](https://ffmpeg.org/documentation.html)
- [RTMP 规范](https://wwwimages2.adobe.com/content/dam/acom/en/devnet/pdf/rtmp_specification_1.0.pdf)
- [HLS 规范](https://developer.apple.com/documentation/http-live-streaming)

### 开源项目

| 项目 | 语言 | 特点 |
|------|------|------|
| [FFmpeg](https://github.com/FFmpeg/FFmpeg) | C | 最强大的多媒体处理库 |
| [SRS](https://github.com/ossrs/srs) | C++ | 高性能流媒体服务器 |
| [LiveGo](https://github.com/gwuhaolin/livego) | Go | 简单的流媒体服务器 |
| [MediaSoup](https://github.com/versatica/mediasoup) | C++ | WebRTC SFU |

### 工具

| 工具 | 用途 |
|------|------|
| FFmpeg | 多媒体处理 |
| FFplay | 媒体播放 |
| VLC | 媒体播放 |
| Wireshark | 协议分析 |
| MediaInfo | 媒体信息查看 |

---

## 🔗 相关链接

- [返回主 README](../README.md)
- [自动驾驶模块](ADAS_README.md)
- [区块链模块](BLOCKCHAIN_README.md)
- [AI 模块](AI_README.md)
- [系统模块](SYSTEM_README.md)
- [网络模块](NETWORK_README.md)
- [异构计算模块](HETERO_README.md)
- [分布式模块](DISTRIBUTED_README.md)
- [应用模块](APPS_README.md)
