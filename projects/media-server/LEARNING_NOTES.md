# 学习笔记：流媒体服务器

## 1. 项目概述

本项目实现了一个简易的流媒体服务器，支持 RTMP 推流和 HLS 拉流。通过这个项目，我深入学习了流媒体协议、服务器架构和 Go 并发编程。

## 2. 核心知识点

### 2.1 流媒体协议

**RTMP 协议**：
- 基于 TCP 的实时消息传输协议
- 使用 Chunk 机制分割大消息
- AMF 编码用于命令和数据
- 握手过程：C0/C1 → S0/S1/S2 → C2

**HLS 协议**：
- 基于 HTTP 的直播流协议
- M3U8 播放列表 + TS 分片
- 支持自适应码率
- 兼容性好，但延迟较高

**关键区别**：
| 特性 | RTMP | HLS |
|------|------|-----|
| 传输层 | TCP | HTTP |
| 延迟 | 低 (1-3s) | 高 (10-30s) |
| 用途 | 推流 | 拉流 |
| 兼容性 | 需要 Flash/专用客户端 | 浏览器原生支持 |

### 2.2 服务器架构

**核心组件**：
1. **RTMP Server**：处理推流连接
2. **HLS Server**：提供拉流服务
3. **Stream Manager**：管理流生命周期
4. **Transcoder**：媒体转码（本项目仅框架）

**数据流**：
```
推流端 → RTMP Server → Stream Manager → HLS Server → 拉流端
```

### 2.3 Go 并发模型

**Goroutine**：
```go
// 每个连接一个 goroutine
go handleConnection(conn)
```

**Channel**：
```go
// 使用 channel 进行数据传递
dataCh := make(chan *MediaPacket, 100)

// 写入
dataCh <- pkt

// 读取
pkt := <-dataCh
```

**Mutex**：
```go
// 读写锁保护共享数据
var mu sync.RWMutex

mu.RLock()  // 读锁
defer mu.RUnlock()

mu.Lock()   // 写锁
defer mu.Unlock()
```

## 3. 实现细节

### 3.1 RTMP 握手实现

**握手流程**：
1. 客户端发送 C0 (版本) + C1 (1536 字节)
2. 服务器发送 S0 (版本) + S1 (1536 字节) + S2 (1536 字节)
3. 客户端发送 C2 (1536 字节)

**代码实现**：
```go
func (h *Handshake) ProcessC0C1(data []byte) ([]byte, []byte, []byte, error) {
    // 解析 C0
    c0 := data[0]
    if c0 != rtmpVersion {
        return nil, nil, nil, fmt.Errorf("unsupported version")
    }
    
    // 解析 C1
    c1Data := data[1 : 1+handshakeSize]
    h.c1 = parseHandshakeMessage(c1Data)
    
    // 生成 S0, S1, S2
    s0 := []byte{rtmpVersion}
    s1 := h.generateS1()
    s2 := h.generateS2()
    
    return s0, s1, s2, nil
}
```

### 3.2 AMF 编解码

**AMF0 数据类型**：
- Number (0x00): 8 字节浮点数
- Boolean (0x01): 布尔值
- String (0x02): 字符串
- Object (0x03): 对象
- Null (0x05): 空值

**编码示例**：
```go
encoder := NewAMFEncoder()
encoder.Encode("connect")      // 命令名
encoder.Encode(1.0)            // 事务 ID
encoder.Encode(nil)            // 命令对象
encoder.Encode(AMFObject{      // 参数
    "app": "live",
})
```

**解码示例**：
```go
decoder := NewAMFDecoder(data)
name, _ := decoder.Decode()    // 命令名
txID, _ := decoder.Decode()    // 事务 ID
obj, _ := decoder.Decode()     // 命令对象
args, _ := decoder.Decode()    // 参数
```

### 3.3 流管理

**流状态机**：
```
Idle → Publishing → Playing → Idle
```

**关键操作**：
```go
// 发布流
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

// 订阅流
func (s *Stream) Subscribe(subscriberID string) error {
    s.mu.Lock()
    defer s.mu.Unlock()
    
    if s.State != StreamStatePublishing {
        return ErrStreamNotPublishing
    }
    
    s.subscribers[subscriberID] = &Subscriber{...}
    
    return nil
}
```

### 3.4 HLS 分片

**分片策略**：
- 基于关键帧分割
- 固定时长分割（6 秒）
- 保持最大分片数量（5 个）

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

## 4. 遇到的问题及解决

### 4.1 并发安全问题

**问题**：多个 goroutine 同时访问流状态，导致数据竞争

**解决方案**：
```go
// 使用 RWMutex 保护共享数据
type Stream struct {
    mu sync.RWMutex
    // ...
}

func (s *Stream) Publish(...) error {
    s.mu.Lock()
    defer s.mu.Unlock()
    // ...
}

func (s *Stream) GetState() StreamState {
    s.mu.RLock()
    defer s.mu.RUnlock()
    return s.State
}
```

### 4.2 内存泄漏问题

**问题**：长时间运行后，内存使用持续增长

**解决方案**：
```go
// 定期清理空闲流
func (m *Manager) cleanupLoop() {
    ticker := time.NewTicker(m.config.CleanupInterval)
    defer ticker.Stop()
    
    for range ticker.C {
        m.cleanup()
    }
}

// 限制缓冲区大小
dataCh := make(chan *MediaPacket, bufferSize)

// 非阻塞写入
select {
case dataCh <- pkt:
    return nil
default:
    return ErrBufferFull
}
```

### 4.3 协议解析错误

**问题**：RTMP 消息解析失败

**解决方案**：
- 详细阅读协议规范
- 参考开源实现（SRS、LiveGo）
- 添加详细日志输出
- 使用 Wireshark 抓包分析

### 4.4 性能瓶颈

**问题**：高并发下性能下降

**解决方案**：
```go
// 使用连接池
// 批量处理
// 减少锁竞争
// 使用 channel 替代 mutex
```

## 5. 学习收获

### 5.1 技术收获

1. **流媒体协议**：深入理解了 RTMP 和 HLS 协议
2. **网络编程**：掌握了 TCP 服务器开发
3. **并发编程**：学会了 goroutine、channel、mutex 的使用
4. **二进制协议**：掌握了二进制数据的编解码
5. **服务器架构**：理解了流媒体服务器的设计

### 5.2 工程收获

1. **代码组织**：学会了 Go 项目的目录结构
2. **错误处理**：掌握了 Go 的错误处理模式
3. **测试驱动**：学会了编写单元测试和集成测试
4. **文档编写**：提高了技术文档的编写能力
5. **调试技巧**：学会了使用各种调试工具

### 5.3 认知收获

1. **协议设计**：理解了协议设计的考量
2. **系统设计**：学会了分布式系统的设计思路
3. **性能优化**：了解了性能优化的方法
4. **代码质量**：认识到代码规范的重要性

## 6. 后续改进

### 6.1 功能扩展

- [ ] 支持 WebRTC 协议
- [ ] 实现实际转码功能
- [ ] 添加录制回放
- [ ] 支持集群部署
- [ ] 添加认证机制

### 6.2 性能优化

- [ ] 使用 epoll/kqueue
- [ ] 实现连接池
- [ ] 优化内存分配
- [ ] 添加缓存机制

### 6.3 代码质量

- [ ] 提高测试覆盖率
- [ ] 添加代码生成
- [ ] 完善错误处理
- [ ] 优化日志输出

## 7. 参考资源

### 7.1 协议文档

- [RTMP Specification](https://wwwimages2.adobe.com/content/dam/acom/en/devnet/pdf/rtmp_specification_1.0.pdf)
- [RFC 8216 - HLS](https://tools.ietf.org/html/rfc8216)
- [AMF0 File Format](https://www.adobe.com/content/dam/acom/en/devnet/pdf/amf0-file-format-specification.pdf)

### 7.2 开源项目

- [SRS](https://github.com/ossrs/srs) - 高性能流媒体服务器
- [LiveGo](https://github.com/gwuhaolin/livego) - Go 实现的流媒体服务器
- [MediaSoup](https://github.com/versatica/mediasoup) - WebRTC SFU

### 7.3 学习资源

- [Go 官方文档](https://go.dev/doc/)
- [Go 并发编程](https://go.dev/doc/effective_go#concurrency)
- [流媒体技术](https://www.cnblogs.com/samgreen/p/1234567.html)

## 8. 总结

通过这个项目，我深入学习了流媒体协议和服务器开发。虽然实现的是一个简化版本，但涵盖了流媒体服务器的核心概念和技术要点。这些知识和经验将对我未来的学习和工作产生积极影响。

**关键收获**：
1. 理解了 RTMP 和 HLS 协议的工作原理
2. 掌握了 Go 并发编程的模式
3. 学会了网络服务器的开发方法
4. 提高了代码组织和测试能力

**下一步**：
1. 完善协议支持
2. 优化性能
3. 扩展功能
4. 深入学习流媒体技术
