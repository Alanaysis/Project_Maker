# 设计文档：流媒体服务器

## 1. 设计目标

### 1.1 核心目标
- 实现 RTMP 协议的推流功能
- 实现 HLS 协议的拉流功能
- 支持多流并发
- 代码结构清晰，易于学习

### 1.2 非目标
- 生产级性能和稳定性
- 完整的 RTMP 协议支持
- 转码功能（仅框架）
- DRM 加密
- 录制回放

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      媒体服务器                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐           ┌─────────────┐                 │
│  │             │           │             │                 │
│  │   RTMP      │           │    HLS      │                 │
│  │   Server    │           │   Server    │                 │
│  │             │           │             │                 │
│  └──────┬──────┘           └──────┬──────┘                 │
│         │                         │                         │
│         │    ┌─────────────┐      │                         │
│         └───▶│   Stream    │◀─────┘                         │
│              │   Manager   │                                │
│              └──────┬──────┘                                │
│                     │                                       │
│              ┌──────▼──────┐                                │
│              │  Transcoder │                                │
│              │  (Optional) │                                │
│              └─────────────┘                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

```
media-server/
├── cmd/server/          # 程序入口
├── configs/             # 配置管理
├── internal/
│   ├── stream/          # 流管理核心
│   ├── rtmp/            # RTMP 协议实现
│   ├── hls/             # HLS 协议实现
│   └── transcoder/      # 转码器
└── tests/               # 测试文件
```

## 3. 核心模块设计

### 3.1 流管理器 (Stream Manager)

**职责**：
- 管理所有活跃的流
- 创建和销毁流
- 提供流查询接口
- 统计信息收集

**接口设计**：
```go
type Manager interface {
    GetOrCreateStream(key string) (*Stream, error)
    GetStream(key string) (*Stream, error)
    DeleteStream(key string)
    GetStreamList() []StreamInfo
    GetStats() ManagerStats
    StopAll()
}
```

**并发模型**：
```go
type Manager struct {
    mu      sync.RWMutex        // 读写锁保护 streams map
    streams map[string]*Stream
}
```

**清理机制**：
- 后台 goroutine 定期检查空闲流
- 空闲超时自动删除
- 防止内存泄漏

### 3.2 流对象 (Stream)

**职责**：
- 管理流状态（idle/publishing/playing）
- 管理发布者和订阅者
- 广播媒体数据

**状态机**：
```
                    ┌─────────┐
                    │  Idle   │
                    └────┬────┘
                         │ Publish()
                         ▼
                    ┌─────────────┐
                    │ Publishing  │
                    └────┬────────┘
                         │ Subscribe()
                         ▼
                    ┌─────────────┐
                    │   Playing   │
                    └────┬────────┘
                         │ Unpublish()
                         ▼
                    ┌─────────┐
                    │  Idle   │
                    └─────────┘
```

**数据广播**：
```go
type Stream struct {
    dataCh chan *MediaPacket  // 带缓冲的 channel
}

func (s *Stream) WritePacket(pkt *MediaPacket) error {
    select {
    case s.dataCh <- pkt:
        return nil
    default:
        return ErrBufferFull
    }
}
```

### 3.3 RTMP 服务器

**职责**：
- 监听 TCP 连接
- 处理 RTMP 握手
- 解析 RTMP 消息
- 处理 AMF 命令

**连接处理流程**：
```
新连接
  │
  ▼
┌─────────────┐
│  Handshake  │  C0/C1 → S0/S1/S2 → C2
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Connect    │  处理 connect 命令
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ CreateStream│  创建流
└──────┬──────┘
       │
       ├──────────────────┐
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│  Publish    │    │    Play     │
└──────┬──────┘    └──────┬──────┘
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│ 音视频数据  │    │ 音视频数据  │
│   写入      │    │   读取      │
└─────────────┘    └─────────────┘
```

**Chunk 解析**：
```go
type RTMPChunk struct {
    Format       byte    // 0-3
    ChunkStreamID int
    Timestamp    uint32
    MsgLength    uint32
    MsgTypeID    byte
    MsgStreamID  uint32
    Data         []byte
}
```

### 3.4 HLS 服务器

**职责**：
- 提供 HTTP 服务
- 生成 M3U8 播放列表
- 提供 TS 分片下载

**分片管理**：
```go
type SegmentManager struct {
    segments     []*Segment
    maxSegments  int
    targetDuration float64
    currentData  []byte
}
```

**分片策略**：
- 基于关键帧分割
- 固定时长分割（6秒）
- 保持最大分片数量

**M3U8 生成**：
```go
func (m *SegmentManager) GenerateM3U8() string {
    playlist := "#EXTM3U\n"
    playlist += "#EXT-X-VERSION:3\n"
    playlist += fmt.Sprintf("#EXT-X-TARGETDURATION:%d\n", maxDuration)
    playlist += fmt.Sprintf("#EXT-X-MEDIA-SEQUENCE:%d\n", firstSeq)
    
    for _, seg := range segments {
        playlist += fmt.Sprintf("#EXTINF:%.3f,\n", seg.Duration)
        playlist += fmt.Sprintf("segment_%d.ts\n", seg.Sequence)
    }
    
    return playlist
}
```

## 4. 数据结构设计

### 4.1 媒体数据包

```go
type MediaPacket struct {
    Type      byte    // 8=audio, 9=video, 18=metadata
    Timestamp uint32  // 毫秒
    Data      []byte
    StreamID  uint32
}
```

### 4.2 流元数据

```go
type Metadata struct {
    Width        int       `json:"width"`
    Height       int       `json:"height"`
    FrameRate    float64   `json:"frame_rate"`
    VideoBitRate int       `json:"video_bit_rate"`
    AudioBitRate int       `json:"audio_bit_rate"`
    SampleRate   int       `json:"sample_rate"`
    Channels     int       `json:"channels"`
    CreatedAt    time.Time `json:"created_at"`
}
```

### 4.3 流信息

```go
type StreamInfo struct {
    Key             string    `json:"key"`
    ID              string    `json:"id"`
    State           StreamState `json:"state"`
    PublisherID     string    `json:"publisher_id,omitempty"`
    SubscriberCount int       `json:"subscriber_count"`
    CreatedAt       time.Time `json:"created_at"`
    UpdatedAt       time.Time `json:"updated_at"`
}
```

## 5. 错误处理设计

### 5.1 错误类型

```go
var (
    ErrStreamNotFound         = errors.New("stream not found")
    ErrStreamAlreadyPublishing = errors.New("stream is already being published")
    ErrStreamNotPublishing    = errors.New("stream is not being published")
    ErrBufferFull             = errors.New("media buffer is full")
    ErrStreamClosed           = errors.New("stream is closed")
    ErrInvalidStreamKey       = errors.New("invalid stream key")
    ErrMaxStreamsReached      = errors.New("maximum number of streams reached")
)
```

### 5.2 错误处理策略

| 场景 | 处理方式 |
|------|----------|
| 握手失败 | 关闭连接 |
| 命令解析错误 | 发送错误响应 |
| 流不存在 | 返回 404 |
| 缓冲区满 | 丢弃数据包 |
| 连接超时 | 自动清理 |

## 6. 性能设计

### 6.1 并发处理

```go
// 每个连接一个 goroutine
go handleConnection(conn)

// 使用 RWMutex 减少锁竞争
mu.RLock()  // 读操作
mu.Lock()   // 写操作

// 使用 channel 进行数据传递
dataCh := make(chan *MediaPacket, 100)
```

### 6.2 内存管理

```go
// 带缓冲的 channel 防止阻塞
dataCh := make(chan *MediaPacket, bufferSize)

// 限制最大流数量
if len(streams) >= maxStreams {
    return ErrMaxStreamsReached
}

// 定期清理空闲流
go cleanupLoop()
```

### 6.3 网络优化

```go
// 设置连接超时
conn.SetDeadline(time.Now().Add(30 * time.Second))

// 使用缓冲读写
buffer := make([]byte, 4096)

// 批量发送
conn.Write(append(s0, append(s1, s2...)...))
```

## 7. 安全设计

### 7.1 输入验证

```go
// 验证流名称
if !isValidStreamKey(key) {
    return ErrInvalidStreamKey
}

// 验证消息长度
if len(data) < expectedLength {
    return ErrInvalidData
}
```

### 7.2 资源限制

```go
// 限制最大连接数
// 限制最大流数量
// 限制缓冲区大小
// 限制消息大小
```

## 8. 测试策略

### 8.1 单元测试

- 握手协议测试
- AMF 编解码测试
- 消息编解码测试
- 流管理器测试
- 分片管理器测试

### 8.2 集成测试

- 推流到拉流完整流程
- 多流并发测试
- 错误恢复测试

### 8.3 性能测试

- 连接数测试
- 吞吐量测试
- 延迟测试

## 9. 扩展性设计

### 9.1 可扩展点

- 支持更多协议（WebRTC、DASH）
- 支持转码功能
- 支持录制回放
- 支持集群部署

### 9.2 接口抽象

```go
// 协议接口
type Protocol interface {
    Serve(listener net.Listener) error
    Stop()
}

// 转码器接口
type Transcoder interface {
    ProcessPacket(streamKey string, pkt *MediaPacket) (*MediaPacket, error)
}
```

## 10. 部署架构

### 10.1 单机部署

```
┌─────────────────┐
│   Media Server  │
│   Port: 1935    │
│   Port: 8080    │
└─────────────────┘
```

### 10.2 集群部署（扩展）

```
┌─────────────┐     ┌─────────────┐
│   Origin    │────▶│    Edge     │
│   Server    │     │   Server    │
└─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│     CDN     │
└─────────────┘
```
