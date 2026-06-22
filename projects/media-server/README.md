# 流媒体服务器 (Media Server)

一个用于学习流媒体协议和服务器架构的简易实现项目。

## 项目概述

本项目实现了一个简易的流媒体服务器，帮助理解：
- RTMP 协议原理和实现
- HLS 协议原理和实现
- 流媒体服务器架构设计
- 推流和拉流的完整流程

## 核心流程

```
推流端 (OBS/FFmpeg) → RTMP服务器 → 流管理器 → HLS切片 → 分发 → 拉流端 (VLC/Browser)
```

## 功能特性

### RTMP 协议支持
- TCP 连接管理
- RTMP 握手协议 (C0/C1/S0/S1/C2/S2)
- Chunk 消息解析
- AMF0 编解码
- connect/createStream/publish/play 命令处理

### HLS 协议支持
- M3U8 播放列表生成
- TS 分片管理
- 实时切片和索引更新
- 跨域访问支持

### 流管理
- 多流并发支持
- 流状态管理 (idle/publishing/playing)
- 订阅者管理
- 超时检测和清理

### 转码支持
- 关键帧检测
- 分片生成
- 码率自适应 (基础支持)

## 系统要求

- Go 1.21+
- FFmpeg (用于推流测试)
- VLC 或浏览器 (用于拉流测试)

## 快速开始

### 安装依赖

```bash
# 下载 Go 依赖
cd projects/media-server
go mod tidy
```

### 编译运行

```bash
# 编译
go build -o media-server ./cmd/server/

# 运行 (默认 RTMP:1935, HTTP:8080)
./media-server

# 自定义端口
RTMP_PORT=1935 HTTP_PORT=8080 ./media-server
```

### 推流测试

```bash
# 使用 FFmpeg 推流
ffmpeg -re -i input.mp4 -c copy -f flv rtmp://localhost:1935/live/test

# 使用 FFmpeg 推摄像头 (Linux)
ffmpeg -f v4l2 -i /dev/video0 -c:v libx264 -f flv rtmp://localhost:1935/live/camera
```

### 拉流测试

```bash
# 使用 FFplay 拉流
ffplay http://localhost:8080/live/test/index.m3u8

# 使用 VLC 拉流
vlc http://localhost:8080/live/test/index.m3u8

# 浏览器访问 (需要支持 HLS 的播放器)
# http://localhost:8080/live/test/index.m3u8
```

## 项目结构

```
media-server/
├── cmd/
│   └── server/
│       └── main.go           # 服务器入口
├── configs/
│   └── config.go             # 配置管理
├── docs/
│   ├── 01-RESEARCH.md        # 调研报告
│   ├── 02-DESIGN.md          # 设计文档
│   ├── 03-IMPLEMENTATION.md  # 实现细节
│   ├── 04-TESTING.md         # 测试文档
│   └── 05-DEVELOPMENT.md     # 开发指南
├── internal/
│   ├── hls/                  # HLS 协议实现
│   │   ├── server.go         # HLS HTTP 服务
│   │   └── segment.go        # 分片管理
│   ├── rtmp/                 # RTMP 协议实现
│   │   ├── server.go         # RTMP 服务
│   │   ├── handshake.go      # 握手协议
│   │   └── message.go        # 消息解析
│   ├── stream/               # 流管理
│   │   ├── manager.go        # 流管理器
│   │   └── stream.go         # 流对象
│   └── transcoder/           # 转码器
│       └── transcoder.go     # 转码实现
├── tests/
│   ├── rtmp_test.go          # RTMP 测试
│   ├── hls_test.go           # HLS 测试
│   ├── stream_test.go        # 流管理测试
│   └── integration_test.go   # 集成测试
├── go.mod
├── go.sum
├── LEARNING_NOTES.md         # 学习笔记
└── README.md
```

## 协议说明

### RTMP 协议
- **默认端口**: 1935
- **传输协议**: TCP
- **用途**: 推流 (Publish)
- **特点**: 低延迟，实时性好

### HLS 协议
- **默认端口**: 8080
- **传输协议**: HTTP
- **用途**: 拉流 (Play)
- **特点**: 兼容性好，支持自适应码率

## 学习路径

1. **协议基础**: 了解 RTMP 和 HLS 协议规范
2. **握手协议**: 理解 RTMP 握手过程
3. **消息格式**: 掌握 Chunk 消息格式
4. **流管理**: 学习流的生命周期管理
5. **HLS 切片**: 理解 M3U8 和 TS 分片机制
6. **集成测试**: 完成推流到拉流的完整流程

## 常见问题

### Q: 为什么选择 Go 实现？
A: Go 的并发模型 (goroutine) 非常适合网络服务器开发，标准库对 TCP/HTTP 支持完善。

### Q: 为什么需要转码？
A: 原始推流格式可能不适合所有客户端，转码可以提供更好的兼容性和自适应码率。

### Q: 如何扩展支持 DASH？
A: DASH 协议与 HLS 类似，主要区别是使用 MPD 文件而非 M3U8，可以复用大部分架构。

## 参考资料

- [RTMP Specification](https://www.adobe.com/content/dam/acom/en/devnet/pdf/amf0-file-format-specification.pdf)
- [HLS Specification](https://developer.apple.com/documentation/http-live-streaming)
- [RFC 8216 - HTTP Live Streaming](https://tools.ietf.org/html/rfc8216)
