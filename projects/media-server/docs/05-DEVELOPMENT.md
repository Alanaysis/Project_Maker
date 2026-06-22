# 开发指南：流媒体服务器

## 1. 开发环境

### 1.1 系统要求

- **操作系统**: Linux/macOS/Windows
- **Go 版本**: 1.21+
- **工具**: Git, Make (可选)

### 1.2 依赖安装

```bash
# 安装 Go (如果未安装)
# Linux
wget https://go.dev/dl/go1.22.2.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.22.2.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin

# macOS
brew install go

# 安装 FFmpeg (用于测试)
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### 1.3 项目初始化

```bash
# 克隆项目
cd projects/media-server

# 下载依赖
go mod tidy

# 验证安装
go build ./cmd/server/
```

## 2. 项目结构

```
media-server/
├── cmd/server/          # 程序入口
│   └── main.go
├── configs/             # 配置管理
│   └── config.go
├── docs/                # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── internal/            # 内部实现
│   ├── hls/             # HLS 协议
│   │   ├── server.go
│   │   └── segment.go
│   ├── rtmp/            # RTMP 协议
│   │   ├── amf.go
│   │   ├── handshake.go
│   │   ├── message.go
│   │   └── server.go
│   ├── stream/          # 流管理
│   │   ├── errors.go
│   │   ├── manager.go
│   │   └── stream.go
│   └── transcoder/      # 转码器
│       └── transcoder.go
├── tests/               # 测试文件
│   ├── hls_test.go
│   ├── integration_test.go
│   ├── rtmp_test.go
│   └── stream_test.go
├── go.mod
├── go.sum
├── LEARNING_NOTES.md
└── README.md
```

## 3. 开发流程

### 3.1 功能开发流程

```
1. 设计 → 2. 实现 → 3. 测试 → 4. 文档 → 5. 代码审查
```

### 3.2 代码规范

**命名规范**：
- 包名：小写单词，如 `stream`, `rtmp`
- 结构体：大写驼峰，如 `StreamManager`
- 函数/方法：大写驼峰，如 `GetStream`
- 变量：小写驼峰，如 `streamKey`
- 常量：大写蛇形，如 `DefaultChunkSize`

**注释规范**：
```go
// GetStream returns a stream by key.
// It returns ErrStreamNotFound if the stream does not exist.
func (m *Manager) GetStream(key string) (*Stream, error) {
    // ...
}
```

**错误处理**：
```go
// 使用自定义错误
var ErrStreamNotFound = errors.New("stream not found")

// 返回错误
if !exists {
    return nil, ErrStreamNotFound
}

// 处理错误
stream, err := manager.GetStream(key)
if err != nil {
    if errors.Is(err, stream.ErrStreamNotFound) {
        // 处理特定错误
    }
    return err
}
```

### 3.3 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

**示例**：
```
feat(rtmp): add RTMP handshake support

Implement C0/C1/S0/S1/S2/C2 handshake protocol.

Closes #123
```

## 4. 编译运行

### 4.1 编译

```bash
# 编译
go build -o media-server ./cmd/server/

# 交叉编译
GOOS=linux GOARCH=amd64 go build -o media-server-linux ./cmd/server/
GOOS=darwin GOARCH=amd64 go build -o media-server-mac ./cmd/server/
GOOS=windows GOARCH=amd64 go build -o media-server.exe ./cmd/server/
```

### 4.2 运行

```bash
# 默认配置运行
./media-server

# 自定义端口
RTMP_PORT=1935 HTTP_PORT=8080 ./media-server

# 调试模式
LOG_LEVEL=debug ./media-server
```

### 4.3 测试

```bash
# 运行所有测试
go test ./...

# 运行特定测试
go test ./tests/ -run TestStreamPublish -v

# 测试覆盖率
go test ./... -cover

# 性能测试
go test ./tests/ -bench=. -benchmem
```

## 5. 调试技巧

### 5.1 日志调试

```go
import log "github.com/sirupsen/logrus"

// 设置日志级别
log.SetLevel(log.DebugLevel)

// 使用日志
log.Debugf("Received message: type=%d", msg.TypeID)
log.Infof("Stream published: %s", streamKey)
log.Warnf("Buffer full, dropping packet")
log.Errorf("Failed to decode message: %v", err)
```

### 5.2 协议调试

```bash
# 使用 Wireshark 抓包
sudo tcpdump -i lo -w rtmp.pcap port 1935

# 使用 FFmpeg 调试
ffmpeg -re -i test.mp4 -c copy -f flv rtmp://localhost:1935/live/test -loglevel debug

# 使用 FFplay 调试
ffplay -loglevel debug http://localhost:8080/live/test/index.m3u8
```

### 5.3 性能调试

```bash
# CPU 分析
go test -cpuprofile=cpu.prof ./tests/
go tool pprof cpu.prof

# 内存分析
go test -memprofile=mem.prof ./tests/
go tool pprof mem.prof

# 竞态检测
go test -race ./...
```

## 6. 常见问题

### 6.1 编译错误

**问题**: `cannot find package`
```bash
# 解决方案
go mod tidy
```

**问题**: `import cycle not allowed`
```bash
# 解决方案：重新组织包结构，避免循环依赖
```

### 6.2 运行时错误

**问题**: `bind: address already in use`
```bash
# 解决方案：查找并关闭占用端口的进程
lsof -i :1935
kill -9 <PID>
```

**问题**: `connection refused`
```bash
# 解决方案：确保服务器已启动
./media-server
```

### 6.3 测试失败

**问题**: `race condition detected`
```bash
# 解决方案：使用 mutex 保护共享数据
go test -race ./...
```

**问题**: `timeout`
```bash
# 解决方案：增加测试超时时间
go test -timeout 60s ./...
```

## 7. 扩展开发

### 7.1 添加新协议

```go
// internal/websocket/server.go
package websocket

type Server struct {
    streamManager *stream.Manager
}

func NewServer(streamManager *stream.Manager) *Server {
    return &Server{
        streamManager: streamManager,
    }
}

func (s *Server) Serve(listener net.Listener) error {
    // 实现 WebSocket 协议
}
```

### 7.2 添加转码功能

```go
// internal/transcoder/transcoder.go
func (t *Transcoder) ProcessPacket(streamKey string, pkt *stream.MediaPacket) (*stream.MediaPacket, error) {
    // 实现转码逻辑
    // 1. 解码
    // 2. 转换
    // 3. 编码
}
```

### 7.3 添加录制功能

```go
// internal/recorder/recorder.go
type Recorder struct {
    stream *stream.Stream
    file   *os.File
}

func (r *Recorder) Start(filename string) error {
    // 开始录制
}

func (r *Recorder) Stop() error {
    // 停止录制
}
```

## 8. 部署指南

### 8.1 单机部署

```bash
# 编译
go build -o media-server ./cmd/server/

# 运行
./media-server

# 后台运行
nohup ./media-server > server.log 2>&1 &
```

### 8.2 Docker 部署

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o media-server ./cmd/server/

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/media-server .
EXPOSE 1935 8080
CMD ["./media-server"]
```

```bash
# 构建镜像
docker build -t media-server .

# 运行容器
docker run -p 1935:1935 -p 8080:8080 media-server
```

### 8.3 Systemd 服务

```ini
# /etc/systemd/system/media-server.service
[Unit]
Description=Media Server
After=network.target

[Service]
Type=simple
User=www-data
ExecStart=/usr/local/bin/media-server
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl enable media-server
sudo systemctl start media-server
```

## 9. 性能优化

### 9.1 并发优化

```go
// 使用 goroutine 池
var pool = make(chan struct{}, 100)

func handleConnection(conn net.Conn) {
    pool <- struct{}{} // 获取令牌
    defer func() { <-pool }() // 释放令牌
    
    // 处理连接
}
```

### 9.2 内存优化

```go
// 使用对象池
var packetPool = sync.Pool{
    New: func() interface{} {
        return &MediaPacket{}
    },
}

func getPacket() *MediaPacket {
    return packetPool.Get().(*MediaPacket)
}

func putPacket(pkt *MediaPacket) {
    packetPool.Put(pkt)
}
```

### 9.3 网络优化

```go
// 设置 TCP 参数
conn.SetReadBuffer(1024 * 1024)  // 1MB
conn.SetWriteBuffer(1024 * 1024) // 1MB
conn.SetNoDelay(true)

// 使用 epoll (Linux)
// 使用 kqueue (macOS)
```

## 10. 学习资源

### 10.1 书籍

- 《Go 程序设计语言》
- 《Go 并发编程实战》
- 《流媒体技术原理与实践》

### 10.2 在线资源

- [Go 官方文档](https://go.dev/doc/)
- [Go 标准库](https://pkg.go.dev/std)
- [RTMP 规范](https://wwwimages2.adobe.com/content/dam/acom/en/devnet/pdf/rtmp_specification_1.0.pdf)
- [HLS 规范](https://developer.apple.com/documentation/http-live-streaming)

### 10.3 开源项目

- [SRS](https://github.com/ossrs/srs)
- [LiveGo](https://github.com/gwuhaolin/livego)
- [MediaSoup](https://github.com/versatica/mediasoup)

## 11. 贡献指南

### 11.1 贡献流程

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request
5. 代码审查
6. 合并

### 11.2 代码审查清单

- [ ] 代码符合规范
- [ ] 测试通过
- [ ] 文档更新
- [ ] 无安全漏洞
- [ ] 性能无退化
