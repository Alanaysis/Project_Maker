# 流媒体服务器技术设计

## 文件组织

```
streaming-server/
├── CMakeLists.txt              # 顶层编译配置
├── README.md                   # 项目文档
├── include/                    # 头文件
│   └── streaming/
│       ├── types.hpp           # 核心类型定义
│       ├── protocol/           # 协议层
│       │   ├── rtmp_server.hpp
│       │   ├── rtsp_server.hpp
│       │   ├── hls_server.hpp
│       │   ├── dash_server.hpp
│       │   └── webrtc_server.hpp
│       ├── media/              # 媒体层
│       │   ├── video_transcoder.hpp
│       │   ├── audio_transcoder.hpp
│       │   ├── segment_generator.hpp
│       │   ├── playlist_generator.hpp
│       │   └── recorder.hpp
│       ├── session/            # 会话层
│       │   ├── session_manager.hpp
│       │   ├── client_connection.hpp
│       │   └── load_balancer.hpp
│       ├── core/               # 核心组件
│       │   ├── async_io.hpp
│       │   ├── thread_pool.hpp
│       │   ├── cache_manager.hpp
│       │   └── bandwidth_adaptor.hpp
│       ├── monitor/            # 监控层
│       │   ├── stats_collector.hpp
│       │   └── logger.hpp
│       └── application/        # 应用层
│           ├── live_server.hpp
│           ├── vod_server.hpp
│           └── conference_server.hpp
├── src/                        # 源文件
│   ├── protocol/
│   ├── media/
│   ├── session/
│   ├── core/
│   ├── monitor/
│   ├── application/
│   └── utils/
├── examples/                   # 示例程序
├── tests/                      # 测试代码
└── docs/                       # 文档
```

## 架构设计

### 1. 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      应用层 (Application)                     │
│   LiveServer    VodServer    ConferenceServer    MonitorServer│
├─────────────────────────────────────────────────────────────┤
│                      协议层 (Protocol)                        │
│   RTMP Server   RTSP Server   HLS Server   DASH Server       │
│   WebRTC Server                                             │
├─────────────────────────────────────────────────────────────┤
│                      媒体层 (Media)                           │
│   VideoTranscoder  AudioTranscoder  SegmentGenerator        │
│   PlaylistGenerator  Recorder                               │
├─────────────────────────────────────────────────────────────┤
│                      会话层 (Session)                         │
│   SessionManager  ClientConnection  LoadBalancer             │
│   ClusterManager                                            │
├─────────────────────────────────────────────────────────────┤
│                      核心层 (Core)                            │
│   AsyncIO  ThreadPool  CacheManager  BandwidthAdaptor       │
├─────────────────────────────────────────────────────────────┤
│                      监控层 (Monitor)                         │
│   StatsCollector  Logger  MetricsCollector                   │
└─────────────────────────────────────────────────────────────┘
```

### 2. 数据流设计

```
推流端                                           拉流端
  │                                                │
  ▼                                                ▼
┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ RTMP │───▶│ Session  │───▶│  Media   │───▶│   HLS    │
│Client│    │ Manager  │    │ Processor│    │  Server  │
└──────┘    └──────────┘    └──────────┘    └──────────┘
                │                │                │
                ▼                ▼                ▼
           ┌──────────┐    ┌──────────┐    ┌──────────┐
           │  Cache   │    │   TS     │    │   HTTP   │
           │ Manager  │    │ Muxer    │    │ Response │
           └──────────┘    └──────────┘    └──────────┘
```

### 3. 模块设计

#### 3.1 协议模块

```
┌─────────────────────────────────────────────────────────────┐
│                    Protocol Module                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ RTMP Server │  │ RTSP Server │  │ HLS Server  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐                           │
│  │ DASH Server │  │WebRTC Server│                           │
│  └─────────────┘  └─────────────┘                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Common Protocol Utils                   │    │
│  │  - AMF Codec  - SDP Parser  - STUN Message          │    │
│  │  - RTP Packetizer  - TS Muxer  - fMP4 Muxer         │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

#### 3.2 媒体模块

```
┌─────────────────────────────────────────────────────────────┐
│                     Media Module                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │                Transcoder                            │    │
│  │  - Video Transcoder (H.264, H.265, VP8, VP9)        │    │
│  │  - Audio Transcoder (AAC, MP3, Opus)                │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                Generator                             │    │
│  │  - Segment Generator (TS, fMP4)                     │    │
│  │  - Playlist Generator (M3U8, MPD)                   │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                Recorder                              │    │
│  │  - MP4 Recorder  - FLV Recorder  - Segment Recorder │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

#### 3.3 会话模块

```
┌─────────────────────────────────────────────────────────────┐
│                    Session Module                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Session Manager                         │    │
│  │  - Session Creation/Destruction                     │    │
│  │  - Session State Tracking                           │    │
│  │  - Session Timeout Handling                         │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Load Balancer                           │    │
│  │  - Round Robin  - Least Connections                 │    │
│  │  - Weighted RR  - Consistent Hash                   │    │
│  │  - Health Checker                                   │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Cluster Manager                         │    │
│  │  - Node Discovery  - Heartbeat                      │    │
│  │  - Message Broadcast  - State Sync                  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

#### 3.4 核心模块

```
┌─────────────────────────────────────────────────────────────┐
│                      Core Module                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  AsyncIO    │  │ ThreadPool  │  │Cache Manager│         │
│  │  (epoll)    │  │  (Priority) │  │  (LRU/Disk) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Bandwidth Adaptor                       │    │
│  │  - Bandwidth Estimator  - Buffer Estimator           │    │
│  │  - Adaptive Bitrate Controller                      │    │
│  │  - Congestion Controller (AIMD)                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

#### 3.5 监控模块

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitor Module                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Stats Collector                         │    │
│  │  - Metrics Collector  - Time Series Store            │    │
│  │  - Stream Stats  - Server Performance               │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Logger                                  │    │
│  │  - Multi-level Logging  - Async Logging             │    │
│  │  - Log Rotation  - Multiple Appenders               │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 类设计

### 1. 协议层类

```cpp
// RTMP 服务器
class RtmpServer {
    void start(host, port);
    void stop();
    void set_frame_callback(callback);
    void set_connection_callback(callback);
private:
    void accept_loop();
    void handle_accept(client_fd, client_addr);
    std::unordered_map<uint64_t, RtmpSession> sessions_;
};

// HLS 服务器
class HlsServer {
    void start(host, port);
    void add_stream(name, params);
    void push_frame(name, frame);
private:
    void http_loop();
    void handle_http_request(fd, request);
    std::unordered_map<string, StreamInfo> streams_;
};
```

### 2. 媒体层类

```cpp
// HLS 切片器
class HlsSegmenter {
    void set_target_duration(duration);
    void set_segment_count(count);
    void process_frame(frame);
    std::vector<HlsSegment> get_segments();
private:
    bool should_start_new_segment(frame);
    void start_new_segment();
    void finish_current_segment();
    std::unique_ptr<TsMuxer> muxer_;
};

// TS 封装器
class TsMuxer {
    bool initialize(params);
    Buffer mux_frame(frame);
    Buffer get_pat();
    Buffer get_pmt();
private:
    Buffer create_pes_packet(frame);
};
```

### 3. 会话层类

```cpp
// 会话管理器
class SessionManager {
    bool initialize(max_sessions, timeout);
    Session create_session(type, protocol);
    void remove_session(session_id);
    void start_cleanup_thread();
private:
    void cleanup_loop();
    std::unordered_map<uint64_t, Session> sessions_;
};

// 负载均衡器
class LoadBalancer {
    bool initialize(algorithm);
    void add_node(node);
    ClusterNode select_node(key);
private:
    ClusterNode select_round_robin();
    ClusterNode select_least_connections();
    std::unique_ptr<ConsistentHash> consistent_hash_;
};
```

### 4. 核心层类

```cpp
// 事件循环
class EventLoop {
    bool initialize();
    void run();
    void stop();
    bool add_fd(fd, type, callback);
    uint64_t add_timer(interval, callback, repeat);
private:
    void process_events(timeout);
    void process_timers();
    int epoll_fd_;
};

// 线程池
class ThreadPool {
    void start();
    void stop(wait);
    void submit_void(func, priority);
    void wait_all();
private:
    void worker_thread();
    std::priority_queue<Task> task_queue_;
    std::vector<std::thread> threads_;
};
```

## 数据结构设计

### 1. 媒体帧

```cpp
struct MediaFrame {
    FrameType type;          // 帧类型
    MediaType media_type;    // 媒体类型
    Buffer data;             // 帧数据
    Timestamp timestamp;     // 时间戳
    int64_t pts;             // 显示时间戳
    int64_t dts;             // 解码时间戳
    bool is_keyframe;        // 是否关键帧
};
```

### 2. 会话信息

```cpp
struct SessionInfo {
    uint64_t session_id;
    SessionType type;
    SessionState state;
    ProtocolType protocol;
    std::string client_ip;
    std::string stream_name;
    Timestamp create_time;
    Timestamp last_active;
    uint64_t bytes_sent;
    uint64_t bytes_received;
};
```

### 3. 流统计

```cpp
struct StreamStats {
    uint64_t bytes_sent;
    uint64_t bytes_received;
    uint64_t frames_sent;
    uint64_t frames_received;
    double current_bitrate;
    double current_fps;
    uint32_t viewers;
};
```

## 线程模型

### 1. 主线程

- 事件循环
- 定时器处理
- 统计收集

### 2. 接受线程

- 接受新连接
- 创建会话

### 3. 工作线程池

- 处理媒体数据
- 协议解析
- 响应生成

### 4. 清理线程

- 会话超时清理
- 缓存淘汰
- 资源回收

## 错误处理设计

### 1. 错误分类

- 网络错误：连接超时、连接重置
- 协议错误：格式错误、版本不匹配
- 媒体错误：编解码失败、格式不支持
- 系统错误：内存不足、文件错误

### 2. 错误恢复

- 自动重连
- 错误重试
- 降级处理
- 告警通知

## 配置管理设计

### 1. 配置文件

```json
{
    "server": {
        "host": "0.0.0.0",
        "rtmp_port": 1935,
        "http_port": 8080
    },
    "hls": {
        "segment_duration": 6,
        "segment_count": 5
    },
    "log": {
        "level": "info",
        "file": "streaming.log"
    }
}
```

### 2. 配置热更新

- 监听配置文件变化
- 动态更新参数
- 无需重启服务
