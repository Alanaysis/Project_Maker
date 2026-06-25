# 流媒体服务器开发手册

## 编译说明

### 系统要求

- **操作系统**：Linux (Ubuntu 20.04+)、macOS 10.15+
- **编译器**：GCC 9+、Clang 10+
- **构建工具**：CMake 3.16+
- **C++ 标准**：C++17 或 C++20

### 依赖安装

#### Ubuntu/Debian

```bash
# 安装基础依赖
sudo apt update
sudo apt install -y \
    build-essential \
    cmake \
    git \
    pkg-config

# 安装网络库（可选）
sudo apt install -y \
    libssl-dev \
    zlib1g-dev
```

#### CentOS/RHEL

```bash
# 安装基础依赖
sudo yum install -y \
    gcc \
    gcc-c++ \
    cmake \
    git \
    pkgconfig

# 安装开发工具
sudo yum install -y \
    openssl-devel \
    zlib-devel
```

#### macOS

```bash
# 使用 Homebrew
brew install cmake
brew install openssl
```

### 编译步骤

#### 1. 获取源码

```bash
cd /home/siok/project_copyninja/projects/streaming-server
```

#### 2. 创建构建目录

```bash
mkdir build
cd build
```

#### 3. 配置 CMake

```bash
# 基本配置
cmake ..

# 指定编译类型
cmake -DCMAKE_BUILD_TYPE=Release ..

# 指定安装路径
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..

# 启用调试
cmake -DCMAKE_BUILD_TYPE=Debug ..
```

#### 4. 编译

```bash
# 使用所有 CPU 核心
make -j$(nproc)

# 或指定核心数
make -j4
```

#### 5. 安装（可选）

```bash
sudo make install
```

### 编译选项

#### CMake 选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `CMAKE_BUILD_TYPE` | Release | 编译类型（Debug/Release） |
| `CMAKE_INSTALL_PREFIX` | /usr/local | 安装路径 |
| `ENABLE_TESTING` | ON | 启用测试 |
| `ENABLE_EXAMPLES` | ON | 启用示例 |

#### 编译类型

```bash
# Debug 模式（包含调试信息）
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release 模式（优化）
cmake -DCMAKE_BUILD_TYPE=Release ..

# RelWithDebInfo 模式（优化 + 调试信息）
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo ..
```

### 编译输出

编译完成后，输出文件位于：

```
build/
├── bin/                    # 可执行文件
│   ├── rtmp_server_example
│   ├── hls_server_example
│   ├── live_server_example
│   ├── vod_server_example
│   ├── test_protocol
│   ├── test_session
│   └── test_media
├── lib/                    # 库文件
│   └── libstreaming_lib.a
└── CMakeFiles/             # CMake 中间文件
```

## 运行方式

### 运行示例程序

#### 1. RTMP 服务器示例

```bash
# 默认端口 1935
./bin/rtmp_server_example

# 指定端口
./bin/rtmp_server_example 1935
```

使用 FFmpeg 推流测试：

```bash
# 推流
ffmpeg -re -i input.mp4 -c copy -f flv rtmp://localhost:1935/live/stream

# 使用 VLC 播放
vlc rtmp://localhost:1935/live/stream
```

#### 2. HLS 服务器示例

```bash
# 默认端口 8080
./bin/hls_server_example

# 指定端口
./bin/hls_server_example 8080
```

使用 VLC 播放 HLS 流：

```bash
vlc http://localhost:8080/live/playlist.m3u8
```

#### 3. 直播服务器示例

```bash
./bin/live_server_example
```

访问地址：
- RTMP：`rtmp://localhost:1935/live/stream`
- HLS：`http://localhost:8080/live/playlist.m3u8`

#### 4. 点播服务器示例

```bash
# 无视频文件
./bin/vod_server_example

# 指定视频文件
./bin/vod_server_example /path/to/video.mp4
```

### 运行测试

```bash
# 运行所有测试
cd build
ctest

# 运行单个测试
./bin/test_protocol
./bin/test_session
./bin/test_media
```

### 命令行参数

#### 通用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--host` | 绑定地址 | `--host 0.0.0.0` |
| `--port` | 端口号 | `--port 1935` |
| `--log-level` | 日志级别 | `--log-level debug` |
| `--config` | 配置文件 | `--config config.json` |

#### RTMP 服务器参数

```bash
./bin/rtmp_server_example [port]

# 示例
./bin/rtmp_server_example 1935
```

#### HLS 服务器参数

```bash
./bin/hls_server_example [port]

# 示例
./bin/hls_server_example 8080
```

## 配置说明

### 配置文件格式

配置文件使用 JSON 格式：

```json
{
    "server": {
        "host": "0.0.0.0",
        "rtmp_port": 1935,
        "rtsp_port": 554,
        "http_port": 8080,
        "webrtc_port": 8443,
        "max_connections": 1000,
        "max_streams": 100,
        "worker_threads": 4
    },
    "hls": {
        "segment_duration": 6,
        "segment_count": 5,
        "output_path": "./hls"
    },
    "dash": {
        "segment_duration": 4,
        "segment_count": 5,
        "output_path": "./dash"
    },
    "log": {
        "level": "info",
        "file": "streaming.log",
        "max_size": 10485760,
        "max_files": 5
    },
    "cache": {
        "memory_size": 104857600,
        "disk_size": 1073741824,
        "disk_path": "./cache"
    }
}
```

### 配置项说明

#### 服务器配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `host` | string | "0.0.0.0" | 绑定地址 |
| `rtmp_port` | int | 1935 | RTMP 端口 |
| `rtsp_port` | int | 554 | RTSP 端口 |
| `http_port` | int | 8080 | HTTP 端口 |
| `webrtc_port` | int | 8443 | WebRTC 端口 |
| `max_connections` | int | 1000 | 最大连接数 |
| `max_streams` | int | 100 | 最大流数 |
| `worker_threads` | int | 4 | 工作线程数 |

#### HLS 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `segment_duration` | float | 6.0 | 切片时长（秒） |
| `segment_count` | int | 5 | 切片数量 |
| `output_path` | string | "./hls" | 输出路径 |

#### 日志配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `level` | string | "info" | 日志级别 |
| `file` | string | "" | 日志文件 |
| `max_size` | int | 10MB | 最大文件大小 |
| `max_files` | int | 5 | 最大文件数 |

## 调试说明

### 日志级别

| 级别 | 说明 |
|------|------|
| Trace | 跟踪信息 |
| Debug | 调试信息 |
| Info | 一般信息 |
| Warn | 警告信息 |
| Error | 错误信息 |
| Fatal | 致命错误 |

### 启用调试日志

```bash
# 设置日志级别
export STREAMING_LOG_LEVEL=debug

# 或在代码中设置
LogManager::instance().initialize(LogLevel::Debug, "", true);
```

### 使用 GDB 调试

```bash
# 编译 Debug 版本
cmake -DCMAKE_BUILD_TYPE=Debug ..
make -j$(nproc)

# 使用 GDB 运行
gdb ./bin/rtmp_server_example

# 设置断点
(gdb) break main
(gdb) break RtmpServer::start

# 运行程序
(gdb) run 1935

# 查看调用栈
(gdb) bt

# 查看变量
(gdb) print host_
(gdb) print port_
```

### 使用 Valgrind 检查内存

```bash
# 检查内存泄漏
valgrind --leak-check=full ./bin/rtmp_server_example 1935

# 检查内存错误
valgrind --tool=memcheck ./bin/rtmp_server_example 1935
```

### 使用 AddressSanitizer

```bash
# 启用 AddressSanitizer
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address" ..
make -j$(nproc)

# 运行程序
./bin/rtmp_server_example 1935
```

## 常见问题

### 1. 编译错误

#### 问题：找不到 CMake

```bash
sudo apt install cmake
```

#### 问题：C++17 不支持

```bash
# 升级 GCC
sudo apt install gcc-9 g++-9
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 90
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-9 90
```

#### 问题：权限错误

```bash
chmod +x build.sh
```

### 2. 运行错误

#### 问题：端口被占用

```bash
# 查看端口占用
lsof -i :1935

# 杀死占用进程
kill -9 <PID>
```

#### 问题：权限不足

```bash
# 使用 sudo 运行
sudo ./bin/rtmp_server_example 1935

# 或使用非特权端口
./bin/rtmp_server_example 19350
```

#### 问题：内存不足

```bash
# 查看内存使用
free -h

# 增加交换空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 3. 网络问题

#### 问题：连接超时

```bash
# 检查防火墙
sudo ufw status

# 开放端口
sudo ufw allow 1935/tcp
sudo ufw allow 8080/tcp
```

#### 问题：无法访问

```bash
# 检查网络连接
ping localhost

# 检查端口监听
netstat -tlnp | grep 1935
```

## 性能调优

### 1. 系统调优

```bash
# 增加文件描述符限制
ulimit -n 65535

# 增加网络缓冲区
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216

# 启用 TCP 优化
sysctl -w net.ipv4.tcp_tw_reuse=1
sysctl -w net.ipv4.tcp_fin_timeout=30
```

### 2. 应用调优

```bash
# 增加工作线程数
./bin/rtmp_server_example --worker-threads 8

# 调整缓冲区大小
./bin/rtmp_server_example --buffer-size 65536
```

### 3. 监控指标

```bash
# 查看 CPU 使用
top -p $(pgrep rtmp_server)

# 查看内存使用
ps aux | grep rtmp_server

# 查看网络连接
ss -tlnp | grep 1935
```

## 开发指南

### 1. 添加新协议

1. 创建头文件：`include/streaming/protocol/new_protocol.hpp`
2. 创建源文件：`src/protocol/new_protocol.cpp`
3. 更新 CMakeLists.txt
4. 编写测试：`tests/test_new_protocol.cpp`

### 2. 添加新功能

1. 确定功能模块
2. 设计接口
3. 实现功能
4. 编写测试
5. 更新文档

### 3. 代码规范

- 使用 4 空格缩进
- 使用 snake_case 命名
- 添加详细注释
- 遵循 SOLID 原则

### 4. 提交规范

```bash
# 提交格式
<type>(<scope>): <subject>

# 示例
feat(protocol): add WebRTC signaling support
fix(hls): fix segment duration calculation
docs(readme): update build instructions
```
