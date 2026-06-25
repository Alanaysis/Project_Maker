# 流媒体服务器 (Streaming Server)

一个用于学习流媒体服务器核心技术的 C++17/20 实现项目。

## 项目概述

本项目实现了一个完整的流媒体服务器框架，涵盖：

- **协议支持**：RTMP、RTSP、HLS、DASH、WebRTC
- **媒体处理**：视频/音频转码、切片生成、清单生成
- **会话管理**：客户端连接、会话管理、负载均衡、集群支持
- **性能优化**：异步 I/O、多线程处理、缓存优化、带宽自适应
- **监控统计**：流量监控、质量统计、错误处理、日志系统
- **实际应用**：直播服务器、点播服务器、视频会议服务器

## 核心流程

```
推流端 → [RTMP/RTSP/WebRTC] → 流媒体服务器 → [HLS/DASH] → 播放端
                                  ↓
                              [录制/转码]
                                  ↓
                              [存储/CDN]
```

## 功能特性

### 协议支持
- **RTMP 服务器**：支持推流/拉流、AMF 编解码、握手协议、消息分块
- **RTSP 服务器**：支持 RTSP 请求/响应、RTP/RTCP 传输、SDP 协商
- **HLS 服务器**：支持 M3U8 播放列表、TS 切片、自适应码率
- **DASH 服务器**：支持 MPD 清单、分段 MP4、自适应码率
- **WebRTC 服务器**：支持信令、ICE/STUN/TURN、SRTP 加密

### 媒体处理
- 视频转码（H.264/H.265）
- 音频转码（AAC/Opus）
- TS 切片生成
- M3U8/MPD 清单生成
- 流录制功能

### 会话管理
- 客户端连接管理
- 会话状态跟踪
- 多种负载均衡算法
- 集群节点管理

### 性能优化
- epoll 异步 I/O
- 优先级线程池
- LRU 内存缓存
- AIMD 拥塞控制
- 自适应码率切换

### 监控统计
- 流量/质量指标收集
- 时间序列数据存储
- 服务器性能监控
- 多级别日志系统

## 系统要求

- Linux/macOS
- GCC 9+ / Clang 10+
- CMake 3.16+
- C++17 支持

## 快速开始

### 编译

```bash
cd projects/streaming-server
mkdir build && cd build
cmake ..
make -j$(nproc)
```

### 运行示例

```bash
# RTMP 服务器
./bin/rtmp_server_example 1935

# HLS 服务器
./bin/hls_server_example 8080

# 直播服务器
./bin/live_server_example

# 点播服务器
./bin/vod_server_example
```

### 推流测试

```bash
# 使用 FFmpeg 推流
ffmpeg -re -i input.mp4 -c copy -f flv rtmp://localhost:1935/live/stream

# 使用 VLC 播放 HLS
vlc http://localhost:8080/live/playlist.m3u8
```

## 技术分类

### 1. 协议层
- RTMP 协议实现
- RTSP 协议实现
- HLS 协议实现
- DASH 协议实现
- WebRTC 协议实现

### 2. 媒体层
- 视频编解码
- 音频编解码
- 容器封装
- 切片生成

### 3. 传输层
- 异步 I/O
- 连接管理
- 流量控制

### 4. 应用层
- 直播系统
- 点播系统
- 会议系统

## 学习路径

1. **协议基础**：理解 RTMP/HLS/DASH 协议
2. **媒体处理**：学习音视频编解码、切片生成
3. **网络编程**：掌握异步 I/O、事件驱动
4. **系统设计**：了解负载均衡、集群架构
5. **性能优化**：学习缓存策略、拥塞控制

## 项目结构

```
streaming-server/
├── CMakeLists.txt          # 编译配置
├── README.md               # 项目文档
├── include/                # 头文件
│   └── streaming/
│       ├── types.hpp       # 核心类型定义
│       ├── protocol/       # 协议实现
│       ├── media/          # 媒体处理
│       ├── session/        # 会话管理
│       ├── core/           # 核心组件
│       ├── monitor/        # 监控系统
│       └── application/    # 应用层
├── src/                    # 源文件
│   ├── protocol/
│   ├── media/
│   ├── session/
│   ├── core/
│   ├── monitor/
│   ├── application/
│   └── utils/
├── examples/               # 示例程序
├── tests/                  # 测试代码
└── docs/                   # 文档
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
