# HTTP/2 服务器开发手册

## 1. 编译说明

### 1.1 环境要求

#### 编译器
- GCC 8+（推荐 GCC 10+）
- Clang 7+（推荐 Clang 12+）
- MSVC 2019+（Windows）

#### 构建工具
- CMake 3.16+
- Make 或 Ninja

#### 操作系统
- Linux（推荐 Ubuntu 20.04+）
- macOS（推荐 macOS 11+）
- Windows（需要 WSL 或 MinGW）

### 1.2 依赖安装

#### Ubuntu/Debian
```bash
# 安装编译工具
sudo apt update
sudo apt install build-essential cmake git

# 安装可选依赖
sudo apt install libssl-dev  # TLS 支持
```

#### CentOS/RHEL
```bash
# 安装编译工具
sudo yum groupinstall "Development Tools"
sudo yum install cmake3 git

# 安装可选依赖
sudo yum install openssl-devel
```

#### macOS
```bash
# 安装 Xcode 命令行工具
xcode-select --install

# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install cmake git
```

#### Windows (WSL)
```bash
# 安装 WSL
wsl --install

# 在 WSL 中安装依赖
sudo apt update
sudo apt install build-essential cmake git
```

### 1.3 编译步骤

#### 基本编译
```bash
# 克隆项目
git clone https://github.com/yourusername/http2-server.git
cd http2-server

# 创建构建目录
mkdir build
cd build

# 配置项目
cmake ..

# 编译
make -j$(nproc)
```

#### Debug 模式
```bash
# 配置 Debug 模式
cmake -DCMAKE_BUILD_TYPE=Debug ..

# 编译
make -j$(nproc)
```

#### Release 模式
```bash
# 配置 Release 模式
cmake -DCMAKE_BUILD_TYPE=Release ..

# 编译
make -j$(nproc)
```

#### 自定义安装路径
```bash
# 配置自定义安装路径
cmake -DCMAKE_INSTALL_PREFIX=/opt/http2-server ..

# 编译
make -j$(nproc)

# 安装
make install
```

### 1.4 编译选项

#### CMake 选项

| 选项 | 默认值 | 描述 |
|------|--------|------|
| `CMAKE_BUILD_TYPE` | Release | 构建类型（Debug/Release） |
| `CMAKE_INSTALL_PREFIX` | /usr/local | 安装路径 |
| `CMAKE_CXX_STANDARD` | 17 | C++ 标准 |
| `BUILD_TESTS` | ON | 是否构建测试 |
| `BUILD_EXAMPLES` | ON | 是否构建示例 |
| `ENABLE_TLS` | OFF | 是否启用 TLS |

#### 编译器选项

```bash
# 启用所有警告
cmake -DCMAKE_CXX_FLAGS="-Wall -Wextra -Wpedantic" ..

# 启用地址 sanitizer
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address" ..

# 启用线程 sanitizer
cmake -DCMAKE_CXX_FLAGS="-fsanitize=thread" ..
```

### 1.5 常见编译问题

#### 问题1：CMake 版本过低
```
CMake Error: CMake was unable to find a build program corresponding to "Unix Makefiles"
```

**解决方案：**
```bash
# 安装最新版本的 CMake
sudo apt install cmake
# 或者从源码编译
wget https://github.com/Kitware/CMake/releases/download/v3.21.0/cmake-3.21.0.tar.gz
tar -xzf cmake-3.21.0.tar.gz
cd cmake-3.21.0
./bootstrap
make
sudo make install
```

#### 问题2：编译器版本过低
```
error: 'optional' is not a member of 'std'
```

**解决方案：**
```bash
# 安装 GCC 10
sudo apt install gcc-10 g++-10
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 100
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-10 100
```

#### 问题3：缺少 pthread 库
```
undefined reference to `pthread_create'
```

**解决方案：**
```bash
# 确保链接 pthread 库
target_link_libraries(your_target pthread)
```

## 2. 运行方式

### 2.1 基本运行

#### 运行示例程序

```bash
# 进入构建目录
cd build

# 运行基本服务器
./http2_server_example

# 运行静态文件服务器
./static_file_server -r ./public -p 8080

# 运行 API 服务器
./api_server

# 运行 SSE 服务器
./sse_server

# 运行反向代理
./reverse_proxy -b 127.0.0.1:8081 -b 127.0.0.1:8082
```

#### 命令行参数

**http2_server_example**
```bash
./http2_server_example [options]
Options:
  -h, --host <host>    监听地址（默认：0.0.0.0）
  -p, --port <port>    监听端口（默认：8080）
  -t, --threads <n>    工作线程数（默认：4）
  --help               显示帮助
```

**static_file_server**
```bash
./static_file_server [options]
Options:
  -r, --root <dir>     根目录（默认：./public）
  -p, --port <port>    监听端口（默认：8080）
  -l, --listing        启用目录列表
  --help               显示帮助
```

**api_server**
```bash
./api_server [options]
Options:
  -p, --port <port>    监听端口（默认：8080）
  -t, --threads <n>    工作线程数（默认：4）
  --help               显示帮助
```

**reverse_proxy**
```bash
./reverse_proxy [options]
Options:
  -p, --port <port>        监听端口（默认：8080）
  -b, --backend <host:port> 添加后端服务器
  -s, --strategy <strategy> 负载均衡策略（round-robin, least-connections, random）
  --help                   显示帮助
```

### 2.2 测试运行

#### 运行所有测试
```bash
cd build
ctest
```

#### 运行特定测试
```bash
# 运行帧测试
./test_frame

# 运行 HPACK 测试
./test_hpack

# 运行流测试
./test_stream

# 运行请求/响应测试
./test_request_response
```

#### 测试输出示例
```
Running HTTP/2 Frame Tests...

Testing FrameHeader serialize...
  PASSED
Testing FrameHeader deserialize...
  PASSED
Testing SettingsFrame...
  PASSED
...

All frame tests PASSED!
```

### 2.3 性能测试

#### 使用 h2load 测试
```bash
# 安装 h2load
sudo apt install nghttp2-client

# 运行性能测试
h2load -n 10000 -c 100 -m 10 http://localhost:8080/
```

#### 使用 ab 测试
```bash
# 安装 ab
sudo apt install apache2-utils

# 运行性能测试
ab -n 10000 -c 100 http://localhost:8080/
```

#### 使用 wrk 测试
```bash
# 安装 wrk
sudo apt install wrk

# 运行性能测试
wrk -t4 -c100 -d30s http://localhost:8080/
```

### 2.4 调试运行

#### 使用 GDB 调试
```bash
# 编译 Debug 版本
cmake -DCMAKE_BUILD_TYPE=Debug ..
make

# 运行 GDB
gdb ./http2_server_example

# GDB 命令
(gdb) break main
(gdb) run
(gdb) next
(gdb) print variable
(gdb) backtrace
```

#### 使用 Valgrind 检测内存问题
```bash
# 安装 Valgrind
sudo apt install valgrind

# 运行 Valgrind
valgrind --leak-check=full ./http2_server_example
```

#### 使用 AddressSanitizer
```bash
# 编译时启用 AddressSanitizer
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address" ..
make

# 运行程序
./http2_server_example
```

### 2.5 生产部署

#### 使用 systemd 服务
```bash
# 创建服务文件
sudo nano /etc/systemd/system/http2-server.service
```

```ini
[Unit]
Description=HTTP/2 Server
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/http2-server
ExecStart=/opt/http2-server/bin/http2_server_example -p 8080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable http2-server
sudo systemctl start http2-server

# 查看状态
sudo systemctl status http2-server
```

#### 使用 Docker
```dockerfile
FROM ubuntu:20.04

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc)

EXPOSE 8080

CMD ["./build/http2_server_example", "-p", "8080"]
```

```bash
# 构建镜像
docker build -t http2-server .

# 运行容器
docker run -p 8080:8080 http2-server
```

## 3. 开发指南

### 3.1 代码结构

#### 目录说明
```
http2-server/
├── include/          # 头文件
├── src/              # 源文件
├── examples/         # 示例程序
├── tests/            # 测试文件
├── docs/             # 文档
└── CMakeLists.txt    # 构建配置
```

#### 文件命名规范
- 头文件：`http2_*.h`
- 源文件：`http2_*.cpp`
- 测试文件：`test_*.cpp`
- 示例文件：`*_server.cpp` 或 `*_example.cpp`

### 3.2 编码规范

#### 命名规范
```cpp
// 类名：PascalCase
class Http2Server { };

// 函数名：camelCase
void startServer();

// 变量名：snake_case
int connection_count;

// 常量名：UPPER_SNAKE_CASE
const int MAX_CONNECTIONS = 1000;

// 命名空间：snake_case
namespace http2 { }
```

#### 代码风格
```cpp
// 使用 4 空格缩进
void function() {
    if (condition) {
        // do something
    }
}

// 每行不超过 80 字符
auto result = some_long_function_name(
    parameter1, parameter2, parameter3);

// 使用有意义的变量名
int user_count;  // 好
int n;           // 差

// 添加必要的注释
/**
 * @brief 处理 HTTP 请求
 * @param request HTTP 请求
 * @param response HTTP 响应
 */
void handle_request(std::shared_ptr<HttpRequest> request,
                   std::shared_ptr<HttpResponse> response);
```

#### 头文件规范
```cpp
#pragma once

/**
 * @file http2_server.h
 * @brief HTTP/2 服务器
 */

#include <string>
#include <memory>

namespace http2 {

class Http2Server {
public:
    Http2Server();
    ~Http2Server();

    bool start();
    void stop();

private:
    // 成员变量
    int listen_fd_;
    bool is_running_;
};

} // namespace http2
```

### 3.3 添加新功能

#### 添加新的帧类型
1. 在 `include/http2_frame.h` 中定义帧类
2. 在 `src/http2_frame.cpp` 中实现序列化/反序列化
3. 在 `src/http2_connection.cpp` 中添加处理逻辑
4. 编写测试用例

```cpp
// 1. 定义帧类
class NewFrame : public Frame {
public:
    NewFrame(uint32_t stream_id, uint32_t data);
    uint32_t get_data() const;
};

// 2. 实现序列化
std::vector<uint8_t> NewFrame::serialize() {
    payload.resize(4);
    payload[0] = (data >> 24) & 0xFF;
    payload[1] = (data >> 16) & 0xFF;
    payload[2] = (data >> 8) & 0xFF;
    payload[3] = data & 0xFF;
    return Frame::serialize();
}

// 3. 添加处理逻辑
void Connection::handle_new_frame(const FrameHeader& header, const uint8_t* payload) {
    // 处理新帧
}

// 4. 编写测试
void test_new_frame() {
    NewFrame frame(1, 12345);
    auto data = frame.serialize();
    assert(data.size() == 13);  // 9 + 4
}
```

#### 添加新的路由
1. 在 `include/http2_server.h` 中声明路由方法
2. 在 `src/http2_server.cpp` 中实现路由逻辑
3. 在示例中使用新路由

```cpp
// 1. 声明路由方法
class Router {
public:
    void put(const std::string& path, RequestHandler handler);
    void patch(const std::string& path, RequestHandler handler);
};

// 2. 实现路由逻辑
void Router::put(const std::string& path, RequestHandler handler) {
    routes_.push_back({HttpMethod::PUT, path, handler});
}

// 3. 使用新路由
router.put("/api/users/:id", [](auto request, auto response) {
    // 处理 PUT 请求
});
```

#### 添加新的中间件
1. 定义中间件函数类型
2. 实现中间件逻辑
3. 注册中间件到路由器

```cpp
// 1. 定义中间件类型
using Middleware = std::function<bool(
    std::shared_ptr<HttpRequest>,
    std::shared_ptr<HttpResponse>,
    std::function<void()>
)>;

// 2. 实现中间件
bool logging_middleware(std::shared_ptr<HttpRequest> request,
                       std::shared_ptr<HttpResponse> response,
                       std::function<void()> next) {
    auto start = std::chrono::steady_clock::now();
    next();
    auto end = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << request->get_method_string() << " " << request->get_path()
              << " " << response->get_status_code() << " " << duration.count() << "ms"
              << std::endl;
    return true;
}

// 3. 注册中间件
router.use(logging_middleware);
```

### 3.4 调试技巧

#### 日志输出
```cpp
#include <iostream>

// 使用标准输出
std::cout << "Debug: " << value << std::endl;

// 使用条件编译
#ifdef DEBUG
#define LOG(msg) std::cout << "[DEBUG] " << msg << std::endl
#else
#define LOG(msg)
#endif
```

#### 断言检查
```cpp
#include <cassert>

void function(int value) {
    assert(value > 0 && "Value must be positive");
    // ...
}
```

#### 错误处理
```cpp
try {
    // 可能抛出异常的代码
} catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << std::endl;
    // 处理错误
}
```

### 3.5 性能优化

#### 内存优化
```cpp
// 使用移动语义
void process(std::vector<uint8_t>&& data) {
    // 使用 data
}

// 使用智能指针
auto stream = std::make_shared<Stream>(id);

// 使用对象池
class Pool {
    std::queue<std::unique_ptr<Object>> objects_;
public:
    std::unique_ptr<Object> acquire() {
        if (objects_.empty()) return std::make_unique<Object>();
        auto obj = std::move(objects_.front());
        objects_.pop();
        return obj;
    }
    void release(std::unique_ptr<Object> obj) {
        objects_.push(std::move(obj));
    }
};
```

#### I/O 优化
```cpp
// 使用非阻塞 I/O
int flags = fcntl(fd, F_GETFL, 0);
fcntl(fd, F_SETFL, flags | O_NONBLOCK);

// 使用缓冲区
class Buffer {
    std::vector<uint8_t> data_;
    size_t pos_ = 0;
public:
    void append(const uint8_t* data, size_t len) {
        data_.insert(data_.end(), data, data + len);
    }
    size_t read(uint8_t* data, size_t len) {
        size_t available = data_.size() - pos_;
        size_t to_read = std::min(len, available);
        std::memcpy(data, data_.data() + pos_, to_read);
        pos_ += to_read;
        return to_read;
    }
};
```

#### 并发优化
```cpp
// 使用原子变量
std::atomic<int> counter{0};

// 使用读写锁
std::shared_mutex mutex_;
std::map<uint32_t, std::shared_ptr<Stream>> streams_;

// 使用线程池
class ThreadPool {
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;
    std::mutex mutex_;
    std::condition_variable cv_;
    bool stop_ = false;
public:
    ThreadPool(size_t threads) {
        for (size_t i = 0; i < threads; ++i) {
            workers_.emplace_back([this] {
                while (true) {
                    std::function<void()> task;
                    {
                        std::unique_lock<std::mutex> lock(mutex_);
                        cv_.wait(lock, [this] { return stop_ || !tasks_.empty(); });
                        if (stop_ && tasks_.empty()) return;
                        task = std::move(tasks_.front());
                        tasks_.pop();
                    }
                    task();
                }
            });
        }
    }
    void enqueue(std::function<void()> task) {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            tasks_.push(std::move(task));
        }
        cv_.notify_one();
    }
};
```

## 4. 测试指南

### 4.1 单元测试

#### 编写测试
```cpp
#include "http2_frame.h"
#include <iostream>
#include <cassert>

void test_frame_serialize() {
    std::cout << "Testing frame serialize..." << std::endl;

    http2::DataFrame frame(1, {0x01, 0x02, 0x03}, true);
    auto data = frame.serialize();

    assert(data.size() == 12);  // 9 + 3
    assert(data[3] == 0x00);   // DATA 类型
    assert(data[4] & 0x01);    // END_STREAM 标志

    std::cout << "  PASSED" << std::endl;
}

int main() {
    test_frame_serialize();
    return 0;
}
```

#### 运行测试
```bash
# 编译测试
make test_frame

# 运行测试
./test_frame
```

### 4.2 集成测试

#### 测试完整流程
```cpp
void test_complete_request() {
    // 创建服务器
    http2::ServerConfig config;
    config.port = 8080;
    http2::Http2Server server(config);

    // 注册路由
    auto& router = server.get_router();
    router.get("/test", [](auto request, auto response) {
        response->set_status(http2::HttpStatusCode::OK);
        response->set_body("Hello, World!");
    });

    // 启动服务器
    server.start();

    // 发送请求
    // ...

    // 验证响应
    // ...

    // 停止服务器
    server.stop();
}
```

### 4.3 性能测试

#### 测试并发性能
```cpp
void test_concurrent_connections() {
    const int NUM_THREADS = 10;
    const int REQUESTS_PER_THREAD = 100;

    std::vector<std::thread> threads;
    std::atomic<int> success_count{0};

    for (int i = 0; i < NUM_THREADS; ++i) {
        threads.emplace_back([&success_count]() {
            for (int j = 0; j < REQUESTS_PER_THREAD; ++j) {
                // 发送请求
                // ...
                success_count++;
            }
        });
    }

    for (auto& thread : threads) {
        thread.join();
    }

    assert(success_count == NUM_THREADS * REQUESTS_PER_THREAD);
}
```

### 4.4 测试覆盖率

#### 使用 gcov
```bash
# 编译时启用覆盖率
cmake -DCMAKE_CXX_FLAGS="--coverage" ..
make

# 运行测试
./test_frame

# 生成覆盖率报告
gcov src/http2_frame.cpp
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_report
```

## 5. 文档编写

### 5.1 代码注释

#### 函数注释
```cpp
/**
 * @brief 处理 HTTP 请求
 *
 * 这个函数处理传入的 HTTP 请求，包括路由匹配、
 * 中间件执行和响应生成。
 *
 * @param request HTTP 请求对象
 * @param response HTTP 响应对象
 * @throws std::runtime_error 如果处理失败
 *
 * @code
 * auto request = std::make_shared<HttpRequest>();
 * auto response = std::make_shared<HttpResponse>();
 * handle_request(request, response);
 * @endcode
 */
void handle_request(std::shared_ptr<HttpRequest> request,
                   std::shared_ptr<HttpResponse> response);
```

#### 类注释
```cpp
/**
 * @brief HTTP/2 服务器类
 *
 * 这个类实现了一个完整的 HTTP/2 服务器，支持：
 * - HTTP/2 协议
 * - 路由系统
 * - 中间件
 * - 静态文件服务
 *
 * @example
 * ServerConfig config;
 * config.port = 8080;
 * Http2Server server(config);
 * server.start();
 */
class Http2Server {
    // ...
};
```

### 5.2 API 文档

#### 使用 Doxygen
```bash
# 安装 Doxygen
sudo apt install doxygen graphviz

# 生成文档
doxygen Doxyfile
```

#### Doxygen 配置
```bash
# Doxyfile
PROJECT_NAME           = "HTTP/2 Server"
OUTPUT_DIRECTORY       = docs/api
INPUT                  = include src
RECURSIVE              = YES
GENERATE_HTML          = YES
GENERATE_LATEX         = NO
```

## 6. 常见问题

### 6.1 编译问题

#### Q: 编译时找不到头文件
**A:** 检查 CMakeLists.txt 中的 include_directories 设置

#### Q: 链接时找不到库
**A:** 检查 target_link_libraries 设置

#### Q: 编译器版本过低
**A:** 安装更高版本的编译器

### 6.2 运行问题

#### Q: 服务器启动失败
**A:** 检查端口是否被占用，检查权限

#### Q: 连接被拒绝
**A:** 检查防火墙设置，检查服务器是否运行

#### Q: 内存泄漏
**A:** 使用 Valgrind 或 AddressSanitizer 检测

### 6.3 性能问题

#### Q: 响应延迟高
**A:** 检查网络连接，检查服务器负载

#### Q: 吞吐量低
**A:** 增加工作线程数，优化代码

#### Q: 内存使用高
**A:** 检查内存泄漏，优化内存管理

## 7. 贡献指南

### 7.1 代码贡献

1. Fork 项目
2. 创建功能分支
3. 编写代码和测试
4. 提交更改
5. 推送到分支
6. 创建 Pull Request

### 7.2 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型：**
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

**示例：**
```
feat(router): 添加 PUT 方法支持

添加了对 HTTP PUT 方法的支持，包括：
- 路由注册
- 请求处理
- 响应生成

Closes #123
```

### 7.3 问题报告

使用 GitHub Issues 报告问题，包括：
- 问题描述
- 复现步骤
- 期望行为
- 实际行为
- 环境信息

## 8. 总结

本开发手册提供了 HTTP/2 服务器的完整开发指南，包括编译、运行、测试、调试和部署等方面。通过遵循本手册，可以快速上手开发和使用 HTTP/2 服务器。

关键要点：
1. 确保环境满足要求
2. 按照步骤编译和运行
3. 使用测试验证功能
4. 遵循编码规范
5. 编写清晰的文档
