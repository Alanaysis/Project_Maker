# 03 - 技术设计

## 一、系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        HA-Server 网关                           │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  接收模块  │───▶│  HTTP    │───▶│  负载    │───▶│  请求    │  │
│  │ (Accept)  │    │  解析器  │    │  均衡器  │    │  转发器  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │                                │               │        │
│       ▼                                ▼               ▼        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  事件    │    │  健康    │    │  后端    │    │  连接池  │  │
│  │  循环    │    │  检查器  │    │  管理器  │    │  管理器  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 模块职责

| 模块 | 职责 | 关键接口 |
|------|------|----------|
| 事件循环 | I/O 多路复用、事件分发 | `add_event()`, `remove_event()`, `run()` |
| 接收模块 | 接受新连接 | `accept_connection()` |
| HTTP 解析器 | 解析 HTTP 请求/响应 | `parse_request()`, `build_response()` |
| 负载均衡器 | 选择后端服务器 | `select_backend()` |
| 后端管理器 | 管理后端服务器状态 | `add_backend()`, `get_status()` |
| 健康检查器 | 检测后端健康状态 | `start_check()`, `is_healthy()` |
| 连接池管理器 | 管理到后端的连接 | `get_connection()`, `release_connection()` |
| 请求转发器 | 转发请求到后端 | `forward_request()` |

## 二、核心数据结构

### 2.1 后端服务器 (Backend)

```cpp
struct Backend {
    std::string id;              // 唯一标识
    std::string host;            // 主机地址
    int port;                    // 端口号
    int weight;                  // 权重（用于加权轮询）
    BackendStatus status;        // 状态：Healthy/Unhealthy/Unknown
    int active_connections;      // 当前活跃连接数
    int total_connections;       // 总连接数
    int failed_requests;         // 失败请求数
    std::chrono::steady_clock::time_point last_check_time;  // 最后检查时间
    int consecutive_failures;    // 连续失败次数
};

enum class BackendStatus {
    Unknown,    // 未知状态
    Healthy,    // 健康
    Unhealthy   // 不健康
};
```

### 2.2 负载均衡器 (LoadBalancer)

```cpp
class LoadBalancer {
public:
    virtual Backend* select_backend(const std::vector<Backend*>& backends) = 0;
    virtual std::string name() const = 0;
};

// 轮询实现
class RoundRobinBalancer : public LoadBalancer {
    std::atomic<int> current_index_{0};
};

// 加权轮询实现
class WeightedRoundRobinBalancer : public LoadBalancer {
    int current_weight_{0};
    int current_index_{0};
};

// 最少连接实现
class LeastConnectionsBalancer : public LoadBalancer {
    // 选择 active_connections 最少的后端
};
```

### 2.3 连接池 (ConnectionPool)

```cpp
class ConnectionPool {
public:
    struct Connection {
        int fd;                    // socket 文件描述符
        std::chrono::steady_clock::time_point created_time;  // 创建时间
        std::chrono::steady_clock::time_point last_used_time; // 最后使用时间
        bool in_use;               // 是否正在使用
    };

private:
    std::string backend_id_;
    std::vector<Connection> connections_;
    size_t max_size_;              // 最大连接数
    std::mutex mutex_;
};
```

## 三、关键算法设计

### 3.1 轮询算法 (Round Robin)

```
算法描述：
1. 维护一个全局索引 current_index
2. 每次请求到来时，选择 backends[current_index % size]
3. current_index++（使用原子操作保证线程安全）

时间复杂度：O(1)
空间复杂度：O(1)

优点：简单、公平分配
缺点：不考虑后端性能差异
```

### 3.2 加权轮询算法 (Weighted Round Robin)

```
算法描述（平滑加权轮询）：
1. 每个后端有配置权重 weight 和当前权重 current_weight
2. 每次选择 current_weight 最大的后端
3. 选中后：current_weight -= total_weight
4. 每轮：所有后端 current_weight += weight

示例（权重 5:3:2）：
  后端A: current=5, 选中后 5-10=-5
  后端B: current=3
  后端C: current=2
  → 选择 A
  → 所有加权重：A=0, B=6, C=4
  → 选择 B
  → ...

时间复杂度：O(n)（需要遍历找最大值）
空间复杂度：O(1)

优点：平滑分配、考虑权重
缺点：需要遍历后端列表
```

### 3.3 最少连接算法 (Least Connections)

```
算法描述：
1. 遍历所有健康的后端
2. 选择 active_connections 最小的后端
3. 如果有多个相同，选择第一个

时间复杂度：O(n)
空间复杂度：O(1)

优点：自适应负载
缺点：需要维护连接计数
```

### 3.4 健康检查算法

```
主动健康检查：
1. 定时器触发检查任务
2. 对每个后端发送 TCP 连接或 HTTP 请求
3. 根据响应判断健康状态
4. 连续失败 threshold 次 → 标记为 Unhealthy
5. 成功一次 → 标记为 Healthy

参数：
- check_interval: 检查间隔（默认 5 秒）
- timeout: 检查超时（默认 3 秒）
- failure_threshold: 失败阈值（默认 3 次）
- success_threshold: 成功阈值（默认 1 次）
```

## 四、接口设计

### 4.1 Server 接口

```cpp
class Server {
public:
    Server(const std::string& config_file);
    ~Server();

    // 启动服务器
    bool start();

    // 停止服务器
    void stop();

    // 添加后端服务器
    void add_backend(const std::string& host, int port, int weight = 1);

    // 设置负载均衡策略
    void set_balancer(std::unique_ptr<LoadBalancer> balancer);

    // 获取统计信息
    ServerStats get_stats() const;
};
```

### 4.2 HealthChecker 接口

```cpp
class HealthChecker {
public:
    HealthChecker(std::vector<Backend*>& backends);

    // 启动健康检查
    void start();

    // 停止健康检查
    void stop();

    // 设置检查间隔
    void set_interval(std::chrono::milliseconds interval);

    // 设置超时时间
    void set_timeout(std::chrono::milliseconds timeout);

    // 设置失败阈值
    void set_failure_threshold(int threshold);
};
```

### 4.3 ConnectionPool 接口

```cpp
class ConnectionPool {
public:
    ConnectionPool(const std::string& host, int port, size_t max_size);

    // 获取连接
    int acquire();

    // 释放连接
    void release(int fd);

    // 获取池大小
    size_t size() const;

    // 获取可用连接数
    size_t available() const;
};
```

## 五、线程模型

### 5.1 线程架构

```
┌─────────────────────────────────────────────┐
│                 主线程                       │
│  ┌─────────────────────────────────────────┐│
│  │           事件循环 (epoll)              ││
│  │  - 接受新连接                           ││
│  │  - 读取请求                             ││
│  │  - 分发到工作线程                       ││
│  └─────────────────────────────────────────┘│
│                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ 工作线程1 │ │ 工作线程2 │ │ 工作线程3 │    │
│  │ - 解析请求│ │ - 解析请求│ │ - 解析请求│    │
│  │ - 选择后端│ │ - 选择后端│ │ - 选择后端│    │
│  │ - 转发请求│ │ - 转发请求│ │ - 转发请求│    │
│  └──────────┘ └──────────┘ └──────────┘    │
│                                             │
│  ┌─────────────────────────────────────────┐│
│  │           健康检查线程                   ││
│  │  - 定期检查后端状态                      ││
│  │  - 更新后端状态                          ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

### 5.2 线程安全设计

| 共享数据 | 保护方式 | 说明 |
|----------|----------|------|
| 后端列表 | 读写锁 | 读多写少场景 |
| 后端状态 | 原子操作 | 状态标志位 |
| 连接池 | 互斥锁 | 连接获取/释放 |
| 统计计数 | 原子操作 | 计数器递增 |
| 负载均衡索引 | 原子操作 | 索引递增 |

## 六、错误处理

### 6.1 错误分类

| 错误类型 | 处理策略 | 示例 |
|----------|----------|------|
| 连接错误 | 重试其他后端 | Connection refused |
| 超时错误 | 标记后端不可用 | Read timeout |
| 协议错误 | 返回 400 Bad Request | Malformed HTTP |
| 内部错误 | 返回 500 Internal Error | Memory allocation failed |
| 无可用后端 | 返回 503 Service Unavailable | All backends down |

### 6.2 降级策略

```
当部分后端不可用时：
1. 仅使用健康的后端
2. 如果所有后端不可用，返回 503 错误
3. 记录错误日志，触发告警
```

## 七、配置设计

```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 8080,
        "worker_threads": 4
    },
    "backends": [
        {
            "host": "127.0.0.1",
            "port": 8081,
            "weight": 5
        },
        {
            "host": "127.0.0.1",
            "port": 8082,
            "weight": 3
        }
    ],
    "load_balancer": {
        "algorithm": "weighted_round_robin"
    },
    "health_checker": {
        "enabled": true,
        "interval_ms": 5000,
        "timeout_ms": 3000,
        "failure_threshold": 3
    },
    "connection_pool": {
        "max_size": 100,
        "idle_timeout_ms": 60000
    }
}
```
