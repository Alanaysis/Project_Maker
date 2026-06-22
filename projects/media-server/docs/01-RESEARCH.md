# 调研报告：流媒体服务器

## 1. 项目背景

流媒体技术是现代互联网视频传输的核心技术，广泛应用于直播、点播、视频会议等场景。本项目旨在通过实现一个简易的流媒体服务器，深入理解流媒体协议和服务器架构。

## 2. 流媒体协议调研

### 2.1 RTMP 协议

**概述**：
- Real-Time Messaging Protocol（实时消息传输协议）
- 由 Adobe 公司开发，主要用于音视频数据传输
- 基于 TCP 协议，默认端口 1935

**协议特点**：
- 低延迟（通常 1-3 秒）
- 支持推流（Publish）和拉流（Play）
- 使用 AMF（Action Message Format）编码
- 支持多路复用

**协议流程**：
1. TCP 连接建立
2. RTMP 握手（C0/C1, S0/S1, C2）
3. 连接命令（connect）
4. 创建流（createStream）
5. 发布/播放命令（publish/play）
6. 数据传输
7. 断开连接

**消息类型**：
| 类型 ID | 名称 | 说明 |
|---------|------|------|
| 1 | Set Chunk Size | 设置块大小 |
| 2 | Abort | 中止消息 |
| 3 | Acknowledgement | 确认消息 |
| 4 | User Control | 用户控制 |
| 5 | Window Ack Size | 窗口确认大小 |
| 6 | Set Peer Bandwidth | 设置带宽 |
| 8 | Audio | 音频数据 |
| 9 | Video | 视频数据 |
| 18 | Data (AMF0) | 元数据 |
| 20 | Command (AMF0) | 命令消息 |

**Chunk 格式**：
```
 0               1               2               3
 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7 0 1 2 3 4 5 6 7
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| fmt |   cs id |                                               |
+-+-+-+-+-+-+-+-+                                               |
|                   timestamp (3 bytes)                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 message length (3 bytes)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    message type id    |                                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+                                     |
|                    message stream id (4 bytes)                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 2.2 HLS 协议

**概述**：
- HTTP Live Streaming（HTTP 直播流）
- 由 Apple 公司开发
- 基于 HTTP 协议，默认端口 80/443

**协议特点**：
- 兼容性好（支持所有主流平台）
- 支持自适应码率（ABR）
- 易于穿透防火墙和 CDN 分发
- 延迟较高（通常 10-30 秒）

**组成要素**：
1. **M3U8 播放列表**：描述媒体分片信息
2. **TS 分片**：实际的媒体数据
3. **Master Playlist**：多码率变体列表
4. **Media Playlist**：单码率分片列表

**M3U8 格式**：
```m3u8
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:6
#EXT-X-MEDIA-SEQUENCE:0

#EXTINF:6.000,
segment_0.ts
#EXTINF:6.000,
segment_1.ts
#EXTINF:6.000,
segment_2.ts
```

**Master Playlist 示例**：
```m3u8
#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=2000000,RESOLUTION=1280x720
720p/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=854x480
480p/index.m3u8
```

### 2.3 DASH 协议

**概述**：
- Dynamic Adaptive Streaming over HTTP
- 基于 ISO 标准（ISO/IEC 23009-1）
- 类似 HLS，但使用 MPD 格式

**与 HLS 对比**：
| 特性 | HLS | DASH |
|------|-----|------|
| 开发商 | Apple | ISO 标准 |
| 格式 | M3U8 + TS | MPD + MP4 |
| 兼容性 | iOS/Android/Web | 主要 Web |
| 自适应码率 | 支持 | 支持 |
| DRM | FairPlay | Widevine/PlayReady |

## 3. 流媒体服务器架构

### 3.1 核心组件

```
                    ┌─────────────────────────────────────┐
                    │         流媒体服务器                 │
                    ├─────────────────────────────────────┤
                    │  ┌─────────┐  ┌─────────┐         │
   推流端 ──────────▶│  │  RTMP   │  │   HLS   │         │
   (OBS/FFmpeg)     │  │  Server  │  │  Server │         │
                    │  └────┬────┘  └────┬────┘         │
                    │       │            │               │
                    │  ┌────▼────────────▼────┐         │
                    │  │     流管理器         │         │
                    │  │   (Stream Manager)   │         │
                    │  └────────┬────────────┘         │
                    │           │                       │
                    │  ┌────────▼────────┐             │
                    │  │    转码器       │             │
                    │  │  (Transcoder)  │             │
                    │  └────────────────┘             │
                    └─────────────────────────────────────┘
                                          │
                                          ▼
                                    ┌─────────┐
                                    │  拉流端  │
                                    │(VLC/Web)│
                                    └─────────┘
```

### 3.2 数据流

```
推流端 (RTMP)
    │
    ▼
┌─────────────┐
│   RTMP      │  解析 RTMP 协议
│   Server    │  提取音视频数据
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Stream    │  管理流状态
│   Manager   │  广播给订阅者
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   HLS       │  切片 TS 数据
│   Server    │  生成 M3U8 播放列表
└──────┬──────┘
       │
       ▼
拉流端 (HTTP/HLS)
```

### 3.3 并发模型

Go 语言的并发模型非常适合流媒体服务器：

```go
// 每个连接一个 goroutine
go handleConnection(conn)

// 流管理器使用 mutex 保护共享状态
type Manager struct {
    mu      sync.RWMutex
    streams map[string]*Stream
}

// 使用 channel 进行数据广播
type Stream struct {
    dataCh chan *MediaPacket
}
```

## 4. 技术选型

### 4.1 语言选择

**选择 Go 的原因**：
- 内置并发支持（goroutine、channel）
- 标准库网络支持完善
- 编译型语言，性能好
- 代码简洁，易于维护

### 4.2 依赖库

| 库 | 用途 |
|----|------|
| `net` | TCP 服务器 |
| `net/http` | HTTP 服务器 |
| `encoding/binary` | 二进制数据处理 |
| `sync` | 并发控制 |
| `github.com/sirupsen/logrus` | 日志库 |

### 4.3 工具链

| 工具 | 用途 |
|------|------|
| FFmpeg | 推流测试 |
| FFplay | 拉流测试 |
| VLC | 拉流测试 |
| Wireshark | 协议分析 |

## 5. 竞品分析

### 5.1 开源方案

| 项目 | 语言 | 特点 |
|------|------|------|
| SRS | C++ | 高性能，功能全面 |
| Nginx-RTMP | C | Nginx 模块，稳定 |
| LiveGo | Go | 简单，易学习 |
| MediaSoup | C++/Node.js | WebRTC 支持 |

### 5.2 本项目定位

本项目定位为**学习型项目**，目标是：
- 理解流媒体协议原理
- 掌握服务器架构设计
- 学习 Go 并发编程

不追求：
- 生产级性能
- 完整协议支持
- 高级功能（DRM、转码等）

## 6. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 协议复杂度高 | 实现困难 | 分阶段实现，先核心后扩展 |
| 性能瓶颈 | 高并发下表现差 | 使用 channel 和 goroutine |
| 兼容性问题 | 客户端连接失败 | 参考 RFC 和开源实现 |

## 7. 参考资料

1. [RTMP Specification (Adobe)](https://wwwimages2.adobe.com/content/dam/acom/en/devnet/pdf/rtmp_specification_1.0.pdf)
2. [RFC 8216 - HTTP Live Streaming](https://tools.ietf.org/html/rfc8216)
3. [ISO/IEC 23009-1 - DASH](https://www.iso.org/standard/79329.html)
4. [SRS Documentation](https://ossrs.io/)
5. [LiveGo Source Code](https://github.com/gwuhaolin/livego)
