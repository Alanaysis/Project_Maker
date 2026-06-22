# 分布式锁 (Distributed Lock)

基于 Redis 的分布式锁实现，包含 Redlock 算法和自动续期机制。

## 项目简介

本项目实现了一个生产级的分布式锁系统，用于在分布式环境中协调多个进程对共享资源的访问。

### 核心特性

- **单节点 Redis 锁**：基于 SET NX EX 的基本分布式锁
- **Redlock 算法**：基于多个独立 Redis 节点的分布式锁算法
- **锁续期（Watchdog）**：自动延长锁的过期时间，防止业务未完成时锁被释放
- **可重入锁**：支持同一客户端多次获取同一把锁
- **公平等待队列**：基于 Redis List 的公平锁实现

## 项目结构

```
distributed-lock/
├── README.md                    # 项目说明
├── docs/                        # 文档目录
│   ├── 01-RESEARCH.md          # 调研报告
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现细节
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发指南
├── LEARNING_NOTES.md            # 学习笔记
├── go.mod                       # Go 模块定义
├── go.sum                       # 依赖校验
├── internal/
│   ├── lock/                    # 基础分布式锁实现
│   │   ├── lock.go             # 锁接口和基础实现
│   │   └── lock_test.go        # 基础锁测试
│   ├── redlock/                 # Redlock 算法实现
│   │   ├── redlock.go          # Redlock 实现
│   │   └── redlock_test.go     # Redlock 测试
│   └── watchdog/                # 锁续期机制
│       ├── watchdog.go         # Watchdog 实现
│       └── watchdog_test.go    # Watchdog 测试
├── pkg/
│   └── utils/                   # 工具函数
│       ├── id.go               # 唯一标识生成
│       └── id_test.go          # 工具函数测试
├── cmd/
│   └── demo/                    # 演示程序
│       └── main.go
└── examples/                    # 使用示例
    └── example_test.go
```

## 快速开始

### 前置条件

- Go 1.21+
- Redis 6.0+（单节点或多节点）

### 安装

```bash
go mod tidy
```

### 基本使用

```go
package main

import (
    "context"
    "fmt"
    "time"

    "github.com/example/distributed-lock/internal/lock"
    "github.com/redis/go-redis/v9"
)

func main() {
    // 创建 Redis 客户端
    client := redis.NewClient(&redis.Options{
        Addr: "localhost:6379",
    })
    defer client.Close()

    // 创建分布式锁
    ctx := context.Background()
    distLock := lock.NewRedisLock(client, "my-resource", 10*time.Second)

    // 获取锁
    acquired, err := distLock.Acquire(ctx)
    if err != nil {
        panic(err)
    }
    if !acquired {
        fmt.Println("无法获取锁")
        return
    }
    defer distLock.Release(ctx)

    // 执行业务逻辑
    fmt.Println("获取锁成功，执行业务逻辑...")
}
```

### 使用 Redlock

```go
// 创建多个 Redis 客户端
clients := []*redis.Client{
    redis.NewClient(&redis.Options{Addr: "redis1:6379"}),
    redis.NewClient(&redis.Options{Addr: "redis2:6379"}),
    redis.NewClient(&redis.Options{Addr: "redis3:6379"}),
}

// 创建 Redlock
rl := redlock.NewRedLock(clients, "my-resource", 10*time.Second)

// 获取锁（需要大多数节点成功）
acquired, err := rl.Acquire(ctx)
```

### 使用 Watchdog 自动续期

```go
// 创建带 Watchdog 的锁
distLock := lock.NewRedisLock(client, "my-resource", 10*time.Second)
wd := watchdog.NewWatchdog(distLock, 3*time.Second)

// 启动 Watchdog
wd.Start(ctx)
defer wd.Stop()

// 获取锁并自动续期
acquired, err := distLock.Acquire(ctx)
if acquired {
    // 执行长时间任务，锁会自动续期
    time.Sleep(5 * time.Minute)
}
```

## 运行测试

```bash
# 运行所有测试
go test ./...

# 运行特定包的测试
go test ./internal/lock/...
go test ./internal/redlock/...
go test ./internal/watchdog/...

# 运行带竞态检测的测试
go test -race ./...
```

## 核心设计

### 锁的生命周期

```
锁请求 → 锁获取 → 业务执行 → 锁释放
   │         │          │          │
   │         │          │          └─ 删除锁（带校验）
   │         │          └─ 执行业务逻辑
   │         └─ SET NX EX（原子操作）
   └─ 准备锁标识和过期时间
```

### Redlock 算法流程

1. 获取当前时间 T1
2. 依次向 N 个 Redis 节点请求加锁
3. 计算获取锁耗时 T2 - T1
4. 如果在 N/2+1 个以上节点获取成功，且耗时小于锁过期时间，则获取成功
5. 锁的有效时间 = 过期时间 - 获取锁耗时

### 锁续期机制

```
Watchdog 定时器 → 检查锁是否存在 → 续期锁 → 重置定时器
      │                                    │
      └─ 业务完成，停止 Watchdog            └─ 继续监控
```

## 参考资料

- [Distributed locks with Redis](https://redis.io/docs/manual/patterns/distributed-locks/)
- [Redlock Algorithm](https://redis.io/topics/distlock)
- Martin Kleppmann: [How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)

## License

MIT
