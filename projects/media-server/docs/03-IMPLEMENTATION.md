# 实现细节：流媒体服务器

## 1. 项目初始化

### 1.1 Go 模块初始化

```bash
cd projects/media-server
go mod init github.com/media-server
```

### 1.2 依赖管理

```go
// go.mod
module github.com/media-server

go 1.21

require (
    github.com/sirupsen/logrus v1.9.3
)
```

## 2. 核心模块实现

### 2.1 流管理器实现

**文件**: `internal/stream/manager.go`

**关键实现点**：

1. **并发安全**：
```go
type Manager struct {
    mu      sync.RWMutex
    streams map[string]*Stream
}
```

2. **流创建**：
```go
func (m *Manager) GetOrCreateStream(key string) (*Stream, error) {
    m.mu.Lock()
    defer m.mu.Unlock()
    
    // 检查是否已存在
    if stream, ok := m.streams[key]; ok {
        return stream, nil
    }
    
    // 检查数量限制
    if len(m.streams) >= m.config.MaxStreams {
        return nil, ErrMaxStreamsReached
    }
    
    // 创建新流
    stream := NewStream(streamID, key)
    m.streams[key] = stream
    
    return stream, nil
}
```

3. **清理机制**：
```go
func (m *Manager) cleanupLoop() {
    ticker := time.NewTicker(m.config.CleanupInterval)
    defer ticker.Stop()
    
    for range ticker.C {
        m.cleanup()
    }
}

func (m *Manager) cleanup() {
    m.mu.Lock()
    defer m.mu.Unlock()
    
    now := time.Now()
    for key, stream := range m.streams {
        if stream.State == StreamStateIdle && 
           now.Sub(stream.updatedAt) > m.config.StreamTimeout {
            stream.Close()
            delete(m.streams, key)
        }
    }
}
```

### 2.2 流对象实现

**文件**: `internal/stream/stream.go`

**关键实现点**：

1. **状态管理**：
```go
func (s *Stream) Publish(publisherID string) error {
    s.mu.Lock()
    defer s.mu.Unlock()
    
    if s.State == StreamStatePublishing {
        return ErrStreamAlreadyPublishing
    }
    
    s.State = StreamStatePublishing
    s.publisher = &Publisher{ID: publisherID}
    
    return nil
}
```

2. **数据广播**：
```go
func (s *Stream) WritePacket(pkt *MediaPacket) error {
    s.mu.RLock()
    if s.State != StreamStatePublishing {
        s.mu.RUnlock()
        return ErrStreamNotPublishing
    }
    s.mu.RUnlock()
    
    select {
    case s.dataCh <- pkt:
        return nil
    default:
        return ErrBufferFull
    }
}
```

3. **订阅管理**：
```go
func (s *Stream) Subscribe(subscriberID string) error {
    s.mu.Lock()
    defer s.mu.Unlock()
    
    if s.State != StreamStatePublishing {
        return ErrStreamNotPublishing
    }
    
    s.subscribers[subscriberID] = &Subscriber{
        ID:        subscriberID,
        StartTime: time.Now(),
        Active:    true,
    }
    
    return nil
}
```

### 2.3 RTMP 协议实现

**文件**: `internal/rtmp/`

**握手实现** (`handshake.go`):

1. **C0/C1 解析**：
```go
func (h *Handshake) ProcessC0C1(data []byte) ([]byte, []byte, []byte, error) {
    // C0: 版本号 (1 字节)
    c0 := data[0]
    if c0 != rtmpVersion {
        return nil, nil, nil, fmt.Errorf("unsupported version: %d", c0)
    }
    
    // C1: 时间戳 + 零 + 随机数 (1536 字节)
    c1Data := data[1 : 1+handshakeSize]
    h.c1 = parseHandshakeMessage(c1Data)
    
    // 生成 S0, S1, S2
    s0 := []byte{rtmpVersion}
    s1 := h.generateS1()
    s2 := h.generateS2()
    
    return s0, s1, s2, nil
}
```

2. **消息编解码** (`message.go`):

```go
// 编码
func (e *MessageEncoder) Encode(msg *RTMPMessage) ([]byte, error) {
    var result []byte
    
    // Chunk header (Format 0)
    chunkHeader := e.encodeChunkHeader(msg, 0)
    result = append(result, chunkHeader...)
    
    // 分割 payload
    for offset < len(payload) {
        chunkLen := min(e.chunkSize, len(payload)-offset)
        result = append(result, payload[offset:offset+chunkLen]...)
        offset += chunkLen
        
        // 添加 Format 3 header
        if offset < len(payload) {
            result = append(result, e.encodeChunkHeaderContinuation(msg)...)
        }
    }
    
    return result, nil
}
```

3. **AMF 编解码** (`amf.go`):

```go
// 编码
func (e *AMFEncoder) Encode(value interface{}) error {
    switch v := value.(type) {
    case string:
        return e.encodeString(v)
    case float64:
        return e.encodeNumber(v)
    case bool:
        return e.encodeBoolean(v)
    case AMFObject:
        return e.encodeObject(v)
    }
}

// 解码
func (d *AMFDecoder) Decode() (interface{}, error) {
    amfType := d.data[d.offset]
    d.offset++
    
    switch amfType {
    case AMF0Number:
        return d.decodeNumber()
    case AMF0String:
        return d.decodeString()
    case AMF0Object:
        return d.decodeObject()
    }
}
```

4. **服务器实现** (`server.go`):

```go
func (s *Server) handleConnection(conn net.Conn) {
    client := &Client{
        conn:      conn,
        handshake: NewHandshake(),
        encoder:   NewMessageEncoder(),
        decoder:   NewMessageDecoder(),
    }
    
    // 握手
    if err := s.handleHandshake(client); err != nil {
        log.Errorf("Handshake failed: %v", err)
        return
    }
    
    // 处理消息
    s.handleMessages(client)
}

func (s *Server) handleMessages(client *Client) {
    buffer := make([]byte, 4096)
    
    for {
        n, err := client.conn.Read(buffer)
        if err != nil {
            return
        }
        
        data := buffer[:n]
        offset := 0
        
        for offset < len(data) {
            msg, consumed, _ := client.decoder.Decode(data[offset:])
            offset += consumed
            
            if msg != nil {
                s.handleMessage(client, msg)
            }
        }
    }
}
```

### 2.4 HLS 服务器实现

**文件**: `internal/hls/`

**分片管理** (`segment.go`):

```go
func (m *SegmentManager) AddData(data []byte, isKeyFrame bool) {
    m.mu.Lock()
    defer m.mu.Unlock()
    
    // 关键帧时分割
    if isKeyFrame && len(m.currentData) > 0 {
        m.finalizeSegment()
    }
    
    m.currentData = append(m.currentData, data...)
}

func (m *SegmentManager) finalizeSegment() {
    if len(m.currentData) == 0 {
        return
    }
    
    segment := &Segment{
        Sequence:  m.sequence,
        Duration:  time.Since(m.segmentStart).Seconds(),
        Data:      m.currentData,
    }
    
    m.segments = append(m.segments, segment)
    m.sequence++
    
    // 限制最大分片数
    if len(m.segments) > m.maxSegments {
        m.segments = m.segments[1:]
    }
    
    m.currentData = nil
    m.segmentStart = time.Now()
}
```

**M3U8 生成**：

```go
func (m *SegmentManager) GenerateM3U8() string {
    playlist := "#EXTM3U\n"
    playlist += "#EXT-X-VERSION:3\n"
    playlist += fmt.Sprintf("#EXT-X-TARGETDURATION:%d\n", maxDuration+1)
    playlist += fmt.Sprintf("#EXT-X-MEDIA-SEQUENCE:%d\n", firstSeq)
    
    for _, seg := range m.segments {
        playlist += fmt.Sprintf("#EXTINF:%.3f,\n", seg.Duration)
        playlist += fmt.Sprintf("segment_%d.ts\n", seg.Sequence)
    }
    
    return playlist
}
```

**HTTP 服务** (`server.go`):

```go
func (s *Server) HandleHLS(w http.ResponseWriter, r *http.Request) {
    path := strings.TrimPrefix(r.URL.Path, "/live/")
    parts := strings.Split(path, "/")
    
    streamKey := parts[0]
    
    // 请求分片
    if len(parts) >= 2 && strings.HasSuffix(parts[1], ".ts") {
        s.handleSegment(w, r, streamKey, parts[1])
        return
    }
    
    // 请求播放列表
    s.handlePlaylist(w, r, streamKey)
}
```

## 3. 配置管理

**文件**: `configs/config.go`

```go
type Config struct {
    RTMPPort        string
    HTTPPort        string
    MaxStreams       int
    StreamTimeout    time.Duration
    CleanupInterval  time.Duration
    BufferSize       int
    MaxSegments      int
    TargetDuration   float64
}

func LoadConfig() *Config {
    config := DefaultConfig()
    
    if port := os.Getenv("RTMP_PORT"); port != "" {
        config.RTMPPort = port
    }
    
    // ... 其他环境变量
    
    return config
}
```

## 4. 主程序入口

**文件**: `cmd/server/main.go`

```go
func main() {
    // 初始化配置
    config := configs.LoadConfig()
    
    // 初始化流管理器
    streamManager := stream.NewManager()
    
    // 初始化 RTMP 服务器
    rtmpServer := rtmp.NewServer(streamManager)
    
    // 初始化 HLS 服务器
    hlsServer := hls.NewServer(streamManager)
    
    // 启动 RTMP 服务器
    go rtmpServer.Serve(rtmpListener)
    
    // 启动 HTTP 服务器
    httpServer.ListenAndServe()
}
```

## 5. 关键问题解决

### 5.1 并发安全

**问题**：多个 goroutine 同时访问共享数据

**解决方案**：
- 使用 `sync.RWMutex` 保护共享状态
- 使用 channel 进行数据传递
- 避免锁竞争

```go
// 读操作使用 RLock
func (m *Manager) GetStream(key string) (*Stream, error) {
    m.mu.RLock()
    defer m.mu.RUnlock()
    // ...
}

// 写操作使用 Lock
func (m *Manager) GetOrCreateStream(key string) (*Stream, error) {
    m.mu.Lock()
    defer m.mu.Unlock()
    // ...
}
```

### 5.2 内存管理

**问题**：长时间运行导致内存泄漏

**解决方案**：
- 定期清理空闲流
- 限制缓冲区大小
- 及时释放资源

```go
func (m *Manager) cleanupLoop() {
    ticker := time.NewTicker(m.config.CleanupInterval)
    for range ticker.C {
        m.cleanup()
    }
}
```

### 5.3 协议解析

**问题**：RTMP 协议复杂，解析容易出错

**解决方案**：
- 分层实现（握手、消息、命令）
- 详细的错误处理
- 参考 RFC 和开源实现

### 5.4 数据广播

**问题**：如何高效地将数据广播给多个订阅者

**解决方案**：
- 使用带缓冲的 channel
- 非阻塞写入
- 缓冲区满时丢弃数据

```go
func (s *Stream) WritePacket(pkt *MediaPacket) error {
    select {
    case s.dataCh <- pkt:
        return nil
    default:
        return ErrBufferFull  // 非阻塞
    }
}
```

## 6. 性能优化

### 6.1 减少锁竞争

```go
// 使用 RWMutex 而不是 Mutex
mu sync.RWMutex

// 读操作使用 RLock
mu.RLock()
defer mu.RUnlock()

// 写操作使用 Lock
mu.Lock()
defer mu.Unlock()
```

### 6.2 缓冲区优化

```go
// 使用带缓冲的 channel
dataCh := make(chan *MediaPacket, bufferSize)

// 批量读写
buffer := make([]byte, 4096)
```

### 6.3 连接复用

```go
// 使用连接池
// 复用编码器/解码器
```

## 7. 调试技巧

### 7.1 日志输出

```go
log.SetLevel(log.DebugLevel)
log.Debugf("Received message: type=%d, length=%d", msg.TypeID, len(msg.Payload))
```

### 7.2 协议分析

```bash
# 使用 Wireshark 抓包
tcpdump -i lo -w rtmp.pcap port 1935

# 使用 FFmpeg 测试
ffmpeg -re -i test.mp4 -c copy -f flv rtmp://localhost:1935/live/test -loglevel debug
```

### 7.3 单元测试

```bash
# 运行所有测试
go test ./...

# 运行特定测试
go test ./tests/ -run TestStreamPublish -v

# 测试覆盖率
go test ./... -cover
```

## 8. 已知限制

1. **不支持完整 RTMP 协议**：仅支持基本的推流/拉流
2. **无转码功能**：仅框架，未实现实际转码
3. **无录制功能**：不支持录制回放
4. **无认证机制**：任何人可以推流/拉流
5. **单机部署**：不支持集群

## 9. 后续改进

1. 完善 RTMP 协议支持
2. 实现实际转码功能
3. 添加录制回放
4. 添加认证机制
5. 支持集群部署
