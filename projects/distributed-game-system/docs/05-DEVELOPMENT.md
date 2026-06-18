# 开发手册

## 1. 环境搭建

### 1.1 前置要求

| 工具 | 版本 | 说明 |
|------|------|------|
| Go | 1.21+ | 主语言 |
| Protobuf | 3.21+ | 协议编译器 |
| Git | 2.30+ | 版本控制 |
| Make | 3.81+ | 构建工具 |

### 1.2 安装步骤

```bash
# 1. 安装 Go
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin

# 2. 安装 Protobuf
sudo apt install -y protobuf-compiler
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest

# 3. 克隆项目
git clone https://github.com/yourusername/distributed-game-system.git
cd distributed-game-system

# 4. 安装依赖
go mod tidy
```

### 1.3 编译项目

```bash
# 编译服务器
go build -o bin/server ./cmd/server

# 编译客户端
go build -o bin/client ./cmd/client

# 编译所有
make build
```

## 2. 项目配置

### 2.1 配置文件

配置文件位于 `configs/server.yaml`:

```yaml
server:
  id: "server-1"
  host: "0.0.0.0"
  udp_port: 8080
  tcp_port: 8081
  max_players: 100

game:
  tick_rate: 20
  snapshot_rate: 10
  world_width: 2000
  world_height: 2000

network:
  heartbeat_interval: 5
  connection_timeout: 30
  max_packet_size: 1024
```

### 2.2 命令行参数

```bash
# 服务器参数
./bin/server [options]
  -config string    配置文件路径 (default "configs/server.yaml")
  -port int         UDP 端口 (default 8080)
  -id string        服务器 ID (default "server-1")

# 客户端参数
./bin/client [options]
  -server string    服务器地址 (default "localhost:8080")
  -name string      玩家名称 (default "Player")
```

## 3. 核心模块解析

### 3.1 网络层 (internal/network/)

**职责**: 处理底层网络通信，支持 UDP 和 TCP。

```go
// UDP 服务器核心
type UDPServer struct {
    conn       *net.UDPConn
    sessions   map[string]*Session
    packetChan chan *Packet
}

// 启动服务器
func (s *UDPServer) Start(addr string) error {
    udpAddr, _ := net.ResolveUDPAddr("udp", addr)
    conn, _ := net.ListenUDP("udp", udpAddr)
    s.conn = conn
    
    // 启动接收循环
    go s.receiveLoop()
    return nil
}
```

**关键设计**:
- 使用 Goroutine 处理并发连接
- 使用 Channel 进行数据包传递
- 会话管理支持连接复用

### 3.2 游戏逻辑 (internal/game/)

**职责**: 实现游戏核心逻辑，包括世界管理和实体更新。

```go
// 世界状态管理
type World struct {
    mu       sync.RWMutex
    players  map[uint32]*Player
    width    float64
    height   float64
}

// 游戏主循环
func (w *World) Update(deltaTime float64) {
    w.mu.Lock()
    defer w.mu.Unlock()
    
    for _, player := range w.players {
        // 更新位置
        player.Position.X += player.Velocity.X * deltaTime
        player.Position.Y += player.Velocity.Y * deltaTime
        
        // 边界检查
        w.clampPosition(player)
    }
}
```

### 3.3 状态同步 (internal/sync/)

**职责**: 实现状态快照和增量同步。

```go
// 快照管理器
type SnapshotManager struct {
    snapshots    []WorldSnapshot
    maxSnapshots int
}

// 创建快照
func (m *SnapshotManager) TakeSnapshot(world *World) WorldSnapshot {
    snapshot := WorldSnapshot{
        Tick:      m.currentTick,
        Timestamp: time.Now().UnixMilli(),
        Players:   make(map[uint32]PlayerState),
    }
    
    for id, player := range world.players {
        snapshot.Players[id] = player.ToState()
    }
    
    return snapshot
}

// 计算增量
func (m *SnapshotManager) CalculateDelta(base, current WorldSnapshot) DeltaSnapshot {
    delta := DeltaSnapshot{
        BaseTick: base.Tick,
        Tick:     current.Tick,
        Players:  make(map[uint32]PlayerDelta),
    }
    
    for id, curr := range current.Players {
        base, exists := base.Players[id]
        if !exists || !base.Equals(curr) {
            delta.Players[id] = CalculatePlayerDelta(base, curr)
        }
    }
    
    return delta
}
```

### 3.4 客户端预测 (internal/prediction/)

**职责**: 实现客户端预测和服务器校正。

```go
// 预测器
type Predictor struct {
    inputBuffer    []BufferedInput
    lastServerState PlayerState
}

// 处理输入并预测
func (p *Predictor) ProcessInput(input PlayerInput, currentState PlayerState) PlayerState {
    // 保存输入
    p.inputBuffer = append(p.inputBuffer, BufferedInput{
        Input:     input,
        State:     currentState,
    })
    
    // 预测新状态
    predicted := currentState
    predicted.Position.X += input.MoveX * moveSpeed * deltaTime
    predicted.Position.Y += input.MoveY * moveSpeed * deltaTime
    
    return predicted
}

// 服务器校正
func (p *Predictor) Reconcile(serverState PlayerState, lastProcessedSeq uint32) PlayerState {
    // 移除已确认的输入
    p.removeAcknowledgedInputs(lastProcessedSeq)
    
    // 从服务器状态开始，重新应用未确认输入
    reconciled := serverState
    for _, buffered := range p.inputBuffer {
        reconciled = p.applyInput(buffered.Input, reconciled)
    }
    
    return reconciled
}
```

### 3.5 一致性哈希 (internal/hashing/)

**职责**: 实现一致性哈希环，用于玩家分配。

```go
// 哈希环
type HashRing struct {
    nodes    []uint32
    vnodeMap map[uint32]string
    replicas int
}

// 添加节点
func (r *HashRing) AddNode(nodeID string) {
    for i := 0; i < r.replicas; i++ {
        hash := r.hash(fmt.Sprintf("%s#%d", nodeID, i))
        r.nodes = append(r.nodes, hash)
        r.vnodeMap[hash] = nodeID
    }
    sort.Slice(r.nodes, func(i, j int) bool {
        return r.nodes[i] < r.nodes[j]
    })
}

// 查找节点
func (r *HashRing) GetNode(key string) string {
    hash := r.hash(key)
    
    // 顺时针查找第一个节点
    idx := sort.Search(len(r.nodes), func(i int) bool {
        return r.nodes[i] >= hash
    })
    
    // 环形处理
    if idx == len(r.nodes) {
        idx = 0
    }
    
    return r.vnodeMap[r.nodes[idx]]
}
```

## 4. 测试指南

### 4.1 单元测试

```bash
# 运行所有测试
go test ./...

# 运行特定包的测试
go test ./internal/game/...

# 运行测试并显示覆盖率
go test -cover ./...

# 生成覆盖率报告
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### 4.2 集成测试

```bash
# 启动服务器
./bin/server -port 8080 &

# 运行集成测试
go test ./tests/... -tags=integration
```

### 4.3 压力测试

```bash
# 运行压力测试
go test ./tests/... -tags=stress -count=100
```

## 5. 调试技巧

### 5.1 日志级别

```bash
# 设置日志级别
export LOG_LEVEL=debug  # debug, info, warn, error

# 运行服务器
./bin/server
```

### 5.2 网络调试

```bash
# 使用 tcpdump 抓包
sudo tcpdump -i lo -nn -X port 8080

# 使用 Wireshark 分析
# 导出 pcap 文件后用 Wireshark 打开
```

### 5.3 性能分析

```bash
# CPU 分析
go test -cpuprofile=cpu.prof ./...
go tool pprof cpu.prof

# 内存分析
go test -memprofile=mem.prof ./...
go tool pprof mem.prof
```

## 6. 常见问题

### 6.1 编译错误

| 错误 | 解决方案 |
|------|----------|
| `cannot find package` | 运行 `go mod tidy` |
| `protoc: command not found` | 安装 protobuf-compiler |
| `undefined: proto.XXX` | 运行 `protoc --go_out=. proto/*.proto` |

### 6.2 运行时错误

| 错误 | 解决方案 |
|------|----------|
| `bind: address already in use` | 检查端口占用，或更换端口 |
| `connection refused` | 确保服务器已启动 |
| `timeout` | 检查网络连接和防火墙 |

### 6.3 性能问题

| 问题 | 解决方案 |
|------|----------|
| CPU 使用率高 | 降低 tick_rate 或 snapshot_rate |
| 内存占用大 | 减少 max_players 或快照数量 |
| 网络延迟高 | 检查网络带宽和拥塞 |

## 7. 部署指南

### 7.1 单机部署

```bash
# 编译
make build

# 运行
./bin/server -config configs/server.yaml
```

### 7.2 Docker 部署

```bash
# 构建镜像
docker build -t game-server .

# 运行容器
docker run -p 8080:8080/udp -p 8081:8081 game-server
```

### 7.3 多服务器部署

```bash
# 启动多个实例
./bin/server -id server-1 -port 8080 &
./bin server -id server-2 -port 8082 &
./bin server -id server-3 -port 8084 &

# 使用一致性哈希路由器
./bin/router -servers "localhost:8080,localhost:8082,localhost:8084"
```

## 8. 贡献指南

### 8.1 代码规范

- 使用 `gofmt` 格式化代码
- 使用 `golint` 检查代码规范
- 每个导出函数必须有注释
- 测试覆盖率 > 70%

### 8.2 提交规范

```
<type>(<scope>): <subject>

类型:
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

示例:
feat(network): add UDP server implementation
fix(prediction): fix reconciliation bug
docs(readme): update quick start guide
```

### 8.3 Pull Request 流程

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 运行测试
5. 提交 PR
6. 代码审查
7. 合并
