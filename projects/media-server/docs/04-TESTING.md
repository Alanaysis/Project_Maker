# 测试文档：流媒体服务器

## 1. 测试策略

### 1.1 测试层次

```
┌─────────────────────────────────────┐
│         集成测试                     │
│    (端到端推流拉流)                  │
├─────────────────────────────────────┤
│         功能测试                     │
│    (协议处理、流管理)                │
├─────────────────────────────────────┤
│         单元测试                     │
│    (函数级别测试)                    │
└─────────────────────────────────────┘
```

### 1.2 测试类型

| 类型 | 目标 | 覆盖率 |
|------|------|--------|
| 单元测试 | 函数/方法 | 80%+ |
| 功能测试 | 模块功能 | 70%+ |
| 集成测试 | 端到端流程 | 关键路径 |
| 性能测试 | 性能指标 | 可选 |

## 2. 单元测试

### 2.1 流管理器测试

**文件**: `tests/stream_test.go`

**测试用例**：

```go
func TestNewStream(t *testing.T) {
    s := stream.NewStream("test-id", "test-key")
    
    if s.ID != "test-id" {
        t.Errorf("Expected stream ID 'test-id', got '%s'", s.ID)
    }
    
    if s.State != stream.StreamStateIdle {
        t.Errorf("Expected state idle, got %v", s.State)
    }
}

func TestStreamPublish(t *testing.T) {
    s := stream.NewStream("test-id", "test-key")
    
    err := s.Publish("publisher-1")
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }
    
    if s.State != stream.StreamStatePublishing {
        t.Errorf("Expected state publishing, got %v", s.State)
    }
    
    // 测试重复发布
    err = s.Publish("publisher-2")
    if err != stream.ErrStreamAlreadyPublishing {
        t.Errorf("Expected ErrStreamAlreadyPublishing, got %v", err)
    }
}

func TestStreamSubscribe(t *testing.T) {
    s := stream.NewStream("test-id", "test-key")
    
    // 尝试订阅空闲流
    err := s.Subscribe("subscriber-1")
    if err != stream.ErrStreamNotPublishing {
        t.Errorf("Expected ErrStreamNotPublishing, got %v", err)
    }
    
    // 发布后订阅
    s.Publish("publisher-1")
    err = s.Subscribe("subscriber-1")
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }
    
    if s.GetSubscriberCount() != 1 {
        t.Errorf("Expected 1 subscriber, got %d", s.GetSubscriberCount())
    }
}
```

### 2.2 RTMP 协议测试

**文件**: `tests/rtmp_test.go`

**测试用例**：

```go
func TestHandshake(t *testing.T) {
    h := rtmp.NewHandshake()
    
    // 生成 C0+C1
    c0c1 := rtmp.GenerateC0C1()
    if len(c0c1) != 1+1536 {
        t.Errorf("Expected C0+C1 length 1537, got %d", len(c0c1))
    }
    
    // 处理 C0+C1
    s0, s1, s2, err := h.ProcessC0C1(c0c1)
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }
    
    // 验证 S0
    if s0[0] != 3 {
        t.Errorf("Expected S0 version 3, got %d", s0[0])
    }
    
    // 处理 C2
    c2 := rtmp.GenerateC2(s1)
    err = h.ProcessC2(c2)
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }
    
    if !h.IsDone() {
        t.Error("Expected handshake to be done")
    }
}

func TestAMFEncoding(t *testing.T) {
    // 测试字符串编码
    encoder := rtmp.NewAMFEncoder()
    err := encoder.Encode("test")
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }
    
    // 测试数字编码
    encoder = rtmp.NewAMFEncoder()
    err = encoder.Encode(42.0)
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }
}

func TestAMFDecoding(t *testing.T) {
    // 编码后解码
    encoder := rtmp.NewAMFEncoder()
    encoder.Encode("hello")
    
    decoder := rtmp.NewAMFDecoder(encoder.Bytes())
    val, err := decoder.Decode()
    if err != nil {
        t.Errorf("Unexpected error: %v", err)
    }
    
    if str, ok := val.(string); !ok || str != "hello" {
        t.Errorf("Expected 'hello', got '%v'", val)
    }
}
```

### 2.3 HLS 测试

**文件**: `tests/hls_test.go`

**测试用例**：

```go
func TestSegmentManager(t *testing.T) {
    sm := hls.NewSegmentManager("test-stream", 5, 6.0)
    
    // 添加数据
    sm.AddData([]byte("test data"), false)
    
    // 完成分片
    sm.FinalizeSegment()
    
    segments := sm.GetSegments()
    if len(segments) != 1 {
        t.Errorf("Expected 1 segment, got %d", len(segments))
    }
}

func TestM3U8Generation(t *testing.T) {
    sm := hls.NewSegmentManager("test-stream", 5, 6.0)
    
    // 添加分片
    sm.AddData([]byte("data1"), false)
    sm.FinalizeSegment()
    
    sm.AddData([]byte("data2"), false)
    sm.FinalizeSegment()
    
    // 生成播放列表
    playlist := sm.GenerateM3U8()
    
    if !strings.HasPrefix(playlist, "#EXTM3U") {
        t.Error("Expected playlist to start with #EXTM3U")
    }
    
    if !strings.Contains(playlist, "segment_0.ts") {
        t.Error("Expected playlist to contain segment_0.ts")
    }
}
```

## 3. 功能测试

### 3.1 流生命周期测试

**文件**: `tests/integration_test.go`

```go
func TestStreamLifecycle(t *testing.T) {
    m := stream.NewManager()
    
    // 创建流
    s, _ := m.GetOrCreateStream("test-stream")
    
    // 发布
    s.Publish("publisher-1")
    
    // 订阅
    s.Subscribe("subscriber-1")
    
    // 写入数据
    pkt := &stream.MediaPacket{
        Type:      9,
        Timestamp: 1000,
        Data:      []byte{0x17, 0x01, 0x00, 0x00, 0x00},
    }
    s.WritePacket(pkt)
    
    // 取消订阅
    s.Unsubscribe("subscriber-1")
    
    // 取消发布
    s.Unpublish()
    
    // 删除流
    m.DeleteStream("test-stream")
}
```

### 3.2 并发测试

```go
func TestStreamConcurrency(t *testing.T) {
    m := stream.NewManager()
    s, _ := m.GetOrCreateStream("concurrent-stream")
    s.Publish("publisher-1")
    
    // 并发订阅
    done := make(chan bool, 10)
    for i := 0; i < 10; i++ {
        go func(id int) {
            subID := "subscriber-" + string(rune('a'+id))
            s.Subscribe(subID)
            done <- true
        }(i)
    }
    
    for i := 0; i < 10; i++ {
        <-done
    }
    
    if s.GetSubscriberCount() != 10 {
        t.Errorf("Expected 10 subscribers, got %d", s.GetSubscriberCount())
    }
}
```

### 3.3 清理测试

```go
func TestStreamCleanup(t *testing.T) {
    config := &stream.ManagerConfig{
        MaxStreams:      100,
        StreamTimeout:   100 * time.Millisecond,
        CleanupInterval: 50 * time.Millisecond,
    }
    
    m := stream.NewManagerWithConfig(config)
    
    // 创建空闲流
    m.GetOrCreateStream("idle-stream")
    
    // 等待清理
    time.Sleep(200 * time.Millisecond)
    
    // 验证清理
    _, err := m.GetStream("idle-stream")
    if err != stream.ErrStreamNotFound {
        t.Errorf("Expected stream to be cleaned up")
    }
}
```

## 4. 运行测试

### 4.1 运行所有测试

```bash
cd projects/media-server
go test ./...
```

### 4.2 运行特定测试

```bash
# 运行流管理器测试
go test ./tests/ -run TestStream -v

# 运行 RTMP 测试
go test ./tests/ -run TestRTMP -v

# 运行 HLS 测试
go test ./tests/ -run TestHLS -v
```

### 4.3 测试覆盖率

```bash
# 生成覆盖率报告
go test ./... -coverprofile=coverage.out

# 查看覆盖率
go tool cover -func=coverage.out

# 生成 HTML 报告
go tool cover -html=coverage.out -o coverage.html
```

### 4.4 性能测试

```bash
# 运行 benchmark
go test ./tests/ -bench=. -benchmem
```

## 5. 手动测试

### 5.1 推流测试

```bash
# 使用 FFmpeg 推流
ffmpeg -re -i test.mp4 -c copy -f flv rtmp://localhost:1935/live/test

# 使用 FFmpeg 推摄像头
ffmpeg -f v4l2 -i /dev/video0 -c:v libx264 -f flv rtmp://localhost:1935/live/camera
```

### 5.2 拉流测试

```bash
# 使用 FFplay
ffplay http://localhost:8080/live/test/index.m3u8

# 使用 VLC
vlc http://localhost:8080/live/test/index.m3u8

# 使用 curl 测试
curl http://localhost:8080/live/test/index.m3u8
```

### 5.3 多流测试

```bash
# 终端 1: 推流 1
ffmpeg -re -i test1.mp4 -c copy -f flv rtmp://localhost:1935/live/stream1

# 终端 2: 推流 2
ffmpeg -re -i test2.mp4 -c copy -f flv rtmp://localhost:1935/live/stream2

# 终端 3: 拉流 1
ffplay http://localhost:8080/live/stream1/index.m3u8

# 终端 4: 拉流 2
ffplay http://localhost:8080/live/stream2/index.m3u8
```

## 6. 调试测试

### 6.1 调试输出

```bash
# 启用详细日志
LOG_LEVEL=debug go test ./tests/ -v
```

### 6.2 测试失败分析

```bash
# 显示详细错误
go test ./tests/ -v -count=1

# 运行特定失败测试
go test ./tests/ -run TestSpecificFunction -v
```

## 7. 测试数据

### 7.1 测试视频文件

```bash
# 生成测试视频
ffmpeg -f lavfi -i testsrc=duration=10:size=320x240:rate=30 -c:v libx264 test.mp4

# 生成带音频的测试视频
ffmpeg -f lavfi -i testsrc=duration=10:size=320x240:rate=30 \
       -f lavfi -i sine=frequency=440:duration=10 \
       -c:v libx264 -c:a aac test_with_audio.mp4
```

### 7.2 测试数据生成

```go
// 生成测试媒体包
func generateTestPacket(msgType byte, timestamp uint32) *stream.MediaPacket {
    return &stream.MediaPacket{
        Type:      msgType,
        Timestamp: timestamp,
        Data:      []byte{0x17, 0x01, 0x00, 0x00, 0x00},
    }
}
```

## 8. 持续集成

### 8.1 GitHub Actions

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-go@v2
        with:
          go-version: '1.21'
      - run: go test ./...
```

### 8.2 本地 CI

```bash
# 运行完整测试套件
./run_tests.sh
```

## 9. 测试最佳实践

1. **测试命名**：使用描述性的测试名称
2. **测试隔离**：每个测试独立运行
3. **测试数据**：使用有意义的测试数据
4. **错误处理**：测试错误情况
5. **边界条件**：测试边界值
6. **并发测试**：测试并发安全
7. **性能测试**：测试关键路径性能
