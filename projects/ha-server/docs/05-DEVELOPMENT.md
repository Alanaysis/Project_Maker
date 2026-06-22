# 05 - 开发手册

## 一、环境搭建

### 1.1 系统要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| 操作系统 | Linux | 需要 epoll 支持 |
| 编译器 | GCC 9+ 或 Clang 10+ | 支持 C++17 |
| CMake | 3.10+ | 构建系统 |
| Make | 任意版本 | 构建工具 |

### 1.2 安装依赖

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install build-essential cmake g++
```

**CentOS/RHEL:**
```bash
sudo yum groupinstall "Development Tools"
sudo yum install cmake3 gcc-c++
```

### 1.3 验证环境

```bash
# 检查编译器版本
g++ --version

# 检查 CMake 版本
cmake --version

# 检查 epoll 支持
man epoll_create
```

## 二、项目构建

### 2.1 编译步骤

```bash
# 进入项目目录
cd projects/ha-server

# 创建构建目录
mkdir -p build
cd build

# 生成 Makefile
cmake ..

# 编译
make -j$(nproc)
```

### 2.2 构建选项

```bash
# Debug 模式（包含调试信息）
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release 模式（优化）
cmake -DCMAKE_BUILD_TYPE=Release ..

# 编译测试
cmake -DBUILD_TESTS=ON ..
```

### 2.3 运行测试

```bash
# 编译并运行测试
cd build
make tests
./ha_server_tests
```

## 三、核心模块解析

### 3.1 事件循环模块 ⭐

**文件**: `src/server.cpp`, `include/server.h`

**核心原理**:
```
事件循环是高性能服务器的核心，使用 epoll 实现 I/O 多路复用。

工作流程：
1. 创建 epoll 实例
2. 将监听 socket 加入 epoll
3. 进入事件循环：
   a. 等待事件（epoll_wait）
   b. 处理新连接事件（EPOLLIN on listen socket）
   c. 处理数据事件（EPOLLIN on client socket）
   d. 处理写事件（EPOLLOUT when response ready）
```

**关键代码**:
```cpp
// 事件循环核心
void Server::event_loop() {
    while (running_) {
        int nfds = epoll_wait(epoll_fd_, events_, MAX_EVENTS, timeout_ms);
        for (int i = 0; i < nfds; i++) {
            if (events_[i].data.fd == listen_fd_) {
                accept_connection();
            } else {
                handle_connection(events_[i].data.fd, events_[i].events);
            }
        }
    }
}
```

**💡 值得思考**:
- 为什么使用 epoll 而不是 select 或 poll？
- epoll 的 ET (边缘触发) 和 LT (水平触发) 模式有什么区别？
- 如何处理大量并发连接？

### 3.2 负载均衡模块 ⭐⭐

**文件**: `src/load_balancer.cpp`, `include/load_balancer.h`

**算法实现**:

#### 轮询 (Round Robin)
```cpp
Backend* RoundRobinBalancer::select_backend(const std::vector<Backend*>& backends) {
    // 使用原子操作保证线程安全
    int index = current_index_.fetch_add(1) % backends.size();
    return backends[index];
}
```

#### 加权轮询 (Weighted Round Robin)
```cpp
Backend* WeightedRoundRobinBalancer::select_backend(const std::vector<Backend*>& backends) {
    // 平滑加权轮询算法
    Backend* best = nullptr;
    int total = 0;

    for (auto* backend : backends) {
        backend->current_weight += backend->weight;
        total += backend->weight;
        if (!best || backend->current_weight > best->current_weight) {
            best = backend;
        }
    }

    if (best) {
        best->current_weight -= total;
    }
    return best;
}
```

**💡 值得思考**:
- 平滑加权轮询相比普通加权轮询有什么优势？
- 如何动态调整权重？（根据响应时间、CPU 负载）
- 最少连接算法在什么场景下优于轮询？

### 3.3 健康检查模块 ⭐⭐

**文件**: `src/health_checker.cpp`, `include/health_checker.h`

**检查流程**:
```
1. 定时器触发
2. 遍历所有后端
3. 尝试 TCP 连接（或 HTTP 请求）
4. 根据结果更新状态：
   - 成功 → consecutive_failures = 0, status = Healthy
   - 失败 → consecutive_failures++
   - 连续失败 >= threshold → status = Unhealthy
5. 等待下一次检查
```

**关键设计**:
```cpp
void HealthChecker::check_backend(Backend& backend) {
    // 尝试 TCP 连接
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    // 设置超时
    struct timeval tv;
    tv.tv_sec = timeout_.count() / 1000;
    tv.tv_usec = (timeout_.count() % 1000) * 1000;
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    // 尝试连接
    int result = connect(fd, ...);
    close(fd);

    if (result == 0) {
        backend.consecutive_failures = 0;
        backend.status = BackendStatus::Healthy;
    } else {
        backend.consecutive_failures++;
        if (backend.consecutive_failures >= failure_threshold_) {
            backend.status = BackendStatus::Unhealthy;
        }
    }
}
```

**💡 值得思考**:
- 主动检查 vs 被动检查各有什么优缺点？
- 检查间隔设多少合适？（频率 vs 开销的权衡）
- 如何避免网络抖动导致的误判？

### 3.4 连接池模块 ⭐⭐⭐

**文件**: `src/connection_pool.cpp`, `include/connection_pool.h`

**连接池工作原理**:
```
1. 初始化时创建 min_size 个连接
2. 请求到来时：
   a. 池中有空闲连接 → 复用
   b. 池中无空闲但未达上限 → 创建新连接
   c. 池满且无空闲 → 等待或拒绝
3. 请求完成后：
   a. 连接放回池中
   b. 标记为空闲
4. 定期清理：
   a. 移除超时的空闲连接
   b. 保持最小连接数
```

**关键代码**:
```cpp
int ConnectionPool::acquire() {
    std::lock_guard<std::mutex> lock(mutex_);

    // 查找空闲连接
    for (auto& conn : connections_) {
        if (!conn.in_use) {
            conn.in_use = true;
            conn.last_used_time = std::chrono::steady_clock::now();
            return conn.fd;
        }
    }

    // 池未满，创建新连接
    if (connections_.size() < max_size_) {
        int fd = create_connection();
        connections_.push_back({fd, now(), now(), true});
        return fd;
    }

    return -1;  // 池满
}

void ConnectionPool::release(int fd) {
    std::lock_guard<std::mutex> lock(mutex_);
    for (auto& conn : connections_) {
        if (conn.fd == fd) {
            conn.in_use = false;
            conn.last_used_time = std::chrono::steady_clock::now();
            break;
        }
    }
}
```

**⭐ 重点难点**:
- 连接池大小如何确定？（Little's Law: L = λW）
- 如何处理连接超时和回收？
- 多线程环境下的连接获取如何保证安全？

**💡 值得思考**:
- 连接池 vs 长连接 vs 短连接各有什么适用场景？
- 如何检测连接是否已经断开？
- 连接池的健康检查如何实现？

## 四、调试技巧

### 4.1 日志级别

```cpp
enum class LogLevel {
    DEBUG,    // 调试信息
    INFO,     // 一般信息
    WARNING,  // 警告
    ERROR     // 错误
};
```

### 4.2 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 编译错误 | 编译器版本过低 | 升级 GCC/Clang |
| 连接超时 | 后端未启动 | 检查后端服务 |
| 内存泄漏 | 连接未正确关闭 | 检查连接释放 |
| 性能差 | 线程数不合理 | 调整 worker_threads |

### 4.3 性能分析

```bash
# 使用 perf 分析性能
perf record -g ./ha_server_example
perf report

# 使用 valgrind 检测内存泄漏
valgrind --leak-check=full ./ha_server_example
```

## 五、扩展开发

### 5.1 添加新的负载均衡算法

1. 在 `include/load_balancer.h` 中定义新类
2. 继承 `LoadBalancer` 基类
3. 实现 `select_backend()` 方法
4. 在 `src/load_balancer.cpp` 中实现
5. 编写单元测试

### 5.2 添加新的健康检查方式

1. 在 `include/health_checker.h` 中定义新检查方式
2. 实现检查逻辑
3. 集成到健康检查流程

## 六、代码规范

### 6.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `LoadBalancer` |
| 函数名 | snake_case | `select_backend()` |
| 变量名 | snake_case | `current_index_` |
| 常量 | UPPER_SNAKE_CASE | `MAX_EVENTS` |
| 文件名 | snake_case | `load_balancer.cpp` |

### 6.2 注释规范

```cpp
/**
 * @brief 选择后端服务器
 * @param backends 可用的后端列表
 * @return 选中的后端指针，如果没有可用后端返回 nullptr
 * @note 此函数是线程安全的
 */
Backend* select_backend(const std::vector<Backend*>& backends);
```
