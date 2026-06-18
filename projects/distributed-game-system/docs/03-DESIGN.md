# 技术设计文档

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                     │
│  │ Client1 │  │ Client2 │  │ Client3 │  ...                 │
│  └────┬────┘  └────┬────┘  └────┬────┘                     │
└───────┼────────────┼────────────┼───────────────────────────┘
        │ UDP/TCP    │            │
┌───────┼────────────┼────────────┼───────────────────────────┐
│       ▼            ▼            ▼        负载均衡层          │
│  ┌─────────────────────────────────────┐                    │
│  │        Consistent Hash Router       │                    │
│  └─────────────────┬───────────────────┘                    │
└────────────────────┼────────────────────────────────────────┘
                     │
┌────────────────────┼────────────────────────────────────────┐
│                    ▼            服务器层                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                     │
│  │ Server1 │  │ Server2 │  │ Server3 │  ...                 │
│  │  (Zone) │  │  (Zone) │  │  (Zone) │                     │
│  └────┬────┘  └────┬────┘  └────┬────┘                     │
└───────┼────────────┼────────────┼───────────────────────────┘
        │            │            │
┌───────┼────────────┼────────────┼───────────────────────────┐
│       ▼            ▼            ▼        存储层              │
│  ┌─────────────────────────────────────┐                    │
│  │           State Store               │                    │
│  └─────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
distributed-game-system/
├── cmd/                    # 应用入口
│   ├── server/            # 游戏服务器
│   └── client/            # 游戏客户端
├── internal/              # 内部实现
│   ├── game/             # 游戏逻辑核心
│   │   ├── world.go      # 世界状态管理
│   │   ├── player.go     # 玩家实体
│   │   ├── combat.go     # 战斗系统
│   │   └── physics.go    # 物理模拟
│   ├── network/          # 网络层
│   │   ├── udp_server.go # UDP 服务器
│   │   ├── tcp_server.go # TCP 服务器
│   │   ├── session.go    # 会话管理
│   │   └── packet.go     # 数据包处理
│   ├── sync/             # 状态同步
│   │   ├── snapshot.go   # 快照管理
│   │   ├── delta.go      # 增量同步
│   │   └── interpolator.go # 插值器
│   ├── prediction/       # 客户端预测
│   │   ├── predictor.go  # 预测器
│   │   ├── reconciler.go # 校正器
│   │   └── buffer.go     # 输入缓冲
│   └── hashing/          # 一致性哈希
│       ├── ring.go       # 哈希环
│       └── vnode.go      # 虚拟节点
├── pkg/                   # 公共包
│   ├── protocol/         # 协议定义
│   ├── config/           # 配置管理
│   └── logger/           # 日志封装
└── proto/                 # Protobuf 定义
    └── game.proto
```

## 2. 核心数据结构

### 2.1 玩家状态

```go
type Vector2 struct {
    X float64
    Y float64
}

type PlayerState struct {
    ID        uint32
    Position  Vector2
    Velocity  Vector2
    Health    int32
    Direction float64  // 朝向角度
    Action    Action   // 当前动作
    Timestamp int64    // 状态时间戳
}

type Action int32

const (
    ActionNone   Action = 0
    ActionMove   Action = 1
    ActionAttack Action = 2
    ActionDie    Action = 3
)
```

### 2.2 输入命令

```go
type PlayerInput struct {
    Sequence   uint32    // 输入序号，用于校正
    Timestamp  int64     // 输入时间戳
    MoveX      float64   // 移动方向 X
    MoveY      float64   // 移动方向 Y
    Attack     bool      // 是否攻击
    ViewAngle  float64   // 视角角度
}
```

### 2.3 世界快照

```go
type WorldSnapshot struct {
    Tick      uint32                    // 服务器帧号
    Timestamp int64                     // 快照时间
    Players   map[uint32]PlayerState    // 所有玩家状态
}

type DeltaSnapshot struct {
    BaseTick  uint32                    // 基准帧号
    Tick      uint32                    // 当前帧号
    Players   map[uint32]PlayerDelta    // 变化的玩家
}

type PlayerDelta struct {
    ID        uint32
    Position  *Vector2  // nil 表示未变化
    Velocity  *Vector2
    Health    *int32
    Action    *Action
}
```

### 2.4 一致性哈希

```go
type HashRing struct {
    nodes     []uint32              // 排序的哈希值
    vnodeMap  map[uint32]string     // 哈希值 -> 服务器ID
    replicas  int                   // 每个物理节点的虚拟节点数
    hashFunc  func([]byte) uint32   // 哈希函数
}
```

## 3. 核心算法

### 3.1 客户端预测算法

```
输入: PlayerInput, 当前本地状态
输出: 预测的 PlayerState

1. 保存输入到待确认队列 (inputBuffer)
2. 基于输入计算新状态:
   newVelocity = Input.Direction * MoveSpeed
   newPosition = CurrentPosition + newVelocity * DeltaTime
3. 如果有攻击输入:
   执行攻击逻辑，预测伤害
4. 返回预测状态
5. 立即显示预测状态
```

### 3.2 服务器校正算法

```
输入: 服务器权威状态, 待确认输入队列
输出: 校正后的本地状态

1. 收到服务器状态 S_server
2. 从待确认队列移除已确认的输入 (sequence <= S_server.lastProcessedInput)
3. 如果本地预测状态与 S_server 有偏差:
   a. 以 S_server 为起点
   b. 重新应用队列中所有未确认的输入
   c. 得到校正后的状态 S_corrected
4. 平滑过渡到 S_corrected (避免突变)
```

### 3.3 实体插值算法

```
输入: 两个服务器快照 S1(t1), S2(t2), 当前渲染时间 t_render
输出: 插值后的实体状态

1. 计算渲染时间在快照之间的位置:
   renderTime = t_render - InterpolationDelay
   alpha = (renderTime - t1) / (t2 - t1)
   alpha = clamp(alpha, 0, 1)
2. 线性插值:
   position = S1.Position * (1 - alpha) + S2.Position * alpha
   velocity = S1.Velocity * (1 - alpha) + S2.Velocity * alpha
3. 返回插值状态
```

### 3.4 一致性哈希算法

```
输入: 玩家ID
输出: 分配的服务器

1. 计算玩家哈希值:
   hash = Hash(playerID)
2. 在哈希环上顺时针查找第一个节点:
   找到第一个 nodeHash >= hash 的节点
3. 返回该节点对应的服务器
4. 如果没有找到，返回环上的第一个节点 (环形)
```

## 4. 网络协议设计

### 4.1 消息类型

```protobuf
enum MessageType {
    // 连接管理
    MSG_CONNECT         = 0;
    MSG_CONNECT_ACK     = 1;
    MSG_DISCONNECT      = 2;
    MSG_HEARTBEAT       = 3;
    
    // 游戏状态
    MSG_PLAYER_INPUT    = 10;
    MSG_STATE_SNAPSHOT  = 11;
    MSG_STATE_DELTA     = 12;
    
    // 游戏事件
    MSG_PLAYER_JOIN     = 20;
    MSG_PLAYER_LEAVE    = 21;
    MSG_PLAYER_ATTACK   = 22;
    MSG_PLAYER_DAMAGE   = 23;
}
```

### 4.2 数据包格式

```
┌─────────────────────────────────────────┐
│ Header (8 bytes)                        │
├─────────────────────────────────────────┤
│ - MessageType (1 byte)                  │
│ - Sequence (2 bytes)                    │
│ - Timestamp (4 bytes)                   │
│ - PayloadLength (1 byte)                │
├─────────────────────────────────────────┤
│ Payload (variable)                      │
│ - Protobuf encoded data                 │
└─────────────────────────────────────────┘
```

### 4.3 连接流程

```
Client                    Server
  │                         │
  │──── MSG_CONNECT ───────>│
  │                         │
  │<─── MSG_CONNECT_ACK ───│
  │                         │
  │     (建立连接)          │
  │                         │
  │<─── MSG_STATE_SNAPSHOT ─│
  │                         │
  │  (开始游戏循环)         │
```

## 5. 状态同步策略

### 5.1 同步频率

| 类型 | 频率 | 说明 |
|------|------|------|
| 完整快照 | 1Hz | 每秒一次，用于新加入玩家 |
| 增量更新 | 20Hz | 每秒 20 次，只发送变化部分 |
| 输入发送 | 60Hz | 客户端输入频率 |

### 5.2 带宽优化

1. **增量同步**: 只发送变化的状态
2. **差量压缩**: 使用 delta encoding
3. **优先级排序**: 重要实体优先同步
4. **范围裁剪**: 只同步视野范围内的实体

## 6. 并发模型

### 6.1 服务器并发

```go
// 主循环
func (s *Server) Run() {
    // 网络 Goroutine: 接收数据包
    go s.receiveLoop()
    
    // 游戏逻辑 Goroutine: 固定帧率更新
    go s.gameLoop()
    
    // 状态同步 Goroutine: 定时广播
    go s.syncLoop()
}
```

### 6.2 数据竞争防护

```go
type World struct {
    mu      sync.RWMutex
    players map[uint32]*Player
}

func (w *World) GetPlayer(id uint32) *Player {
    w.mu.RLock()
    defer w.mu.RUnlock()
    return w.players[id]
}
```

## 7. 配置设计

```yaml
# server.yaml
server:
  id: "server-1"
  host: "0.0.0.0"
  udp_port: 8080
  tcp_port: 8081
  max_players: 100

game:
  tick_rate: 20          # 服务器帧率
  snapshot_rate: 10      # 快照发送频率
  world_width: 2000
  world_height: 2000

network:
  heartbeat_interval: 5s
  connection_timeout: 30s
  max_packet_size: 1024

prediction:
  enabled: true
  max_buffer_size: 60
  correction_smoothing: 0.1
```
