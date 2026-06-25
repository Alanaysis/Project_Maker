# C++ 常用三方库介绍

## 项目简介

本项目旨在介绍 C++ 开发中常用的三方库，涵盖容器、序列化、网络、并发、测试、日志、数学、图形、工具和构建等多个领域。通过实际代码示例，帮助开发者快速掌握这些库的使用方法。

## 快速开始

### 环境要求

- C++17/20 编译器（GCC 9+, Clang 10+, MSVC 2019+）
- CMake 3.15+
- vcpkg 或 Conan（推荐）

### 编译运行

```bash
# 克隆项目
git clone <repository-url>
cd cpp-third-party-libraries

# 创建构建目录
mkdir build && cd build

# 配置项目
cmake ..

# 编译
cmake --build .

# 运行示例
./bin/container_example
```

## 库分类

### 1. 容器和数据结构
- **Boost.Container** - 容器扩展，提供 flat_map、stable_vector 等
- **Abseil** - Google 基础库，包含 SwissTable 等高效容器
- **Folly** - Facebook 基础库，提供 F14 等高性能容器
- **EASTL** - EA 游戏容器，专为游戏开发优化

### 2. 序列化
- **Protobuf** - Google 序列化框架，跨语言支持
- **FlatBuffers** - Google 零拷贝序列化，适合游戏和性能敏感场景
- **Cap'n Proto** - 零拷贝序列化，极低延迟
- **JSON** - nlohmann/json（易用）和 RapidJSON（高性能）
- **MessagePack** - 二进制 JSON，紧凑高效

### 3. 网络
- **Boost.Asio** - 异步 I/O 框架，网络编程基石
- **cpp-httplib** - 简单易用的 HTTP 库
- **CPR** - C++ HTTP 请求库，类似 Python requests
- **libcurl** - 成熟的 URL 传输库

### 4. 并发
- **Intel TBB** - 线程构建块，任务并行框架
- **Folly Futures** - Facebook 异步编程库
- **Taskflow** - 任务并行框架，支持 DAG 调度

### 5. 测试
- **Google Test** - 单元测试框架，业界标准
- **Google Mock** - 模拟框架，配合 GTest 使用
- **Catch2** - 现代 C++ 测试框架
- **doctest** - 轻量级测试框架，编译速度快

### 6. 日志
- **spdlog** - 快速日志库，支持多种后端
- **glog** - Google 日志库，功能丰富
- **Boost.Log** - Boost 日志库，灵活可配置

### 7. 数学和科学
- **Eigen** - 线性代数库，广泛用于科学计算
- **Armadillo** - 线性代数库，类似 MATLAB
- **Boost.Math** - 数学工具库，包含特殊函数

### 8. 图形和 GUI
- **Dear ImGui** - 即时模式 GUI，适合工具开发
- **SFML** - 多媒体库，简单易用
- **SDL** - 跨平台多媒体库，底层控制

### 9. 工具库
- **Boost** - 通用工具库集合
- **Abseil** - Google 工具库，包含字符串、容器等
- **Folly** - Facebook 工具库，高性能组件
- **range-v3** - 范围库，函数式编程

### 10. 构建和包管理
- **vcpkg** - Microsoft 包管理器，Windows 友好
- **Conan** - C/C++ 包管理器，跨平台
- **FetchContent** - CMake 内置依赖管理

## 学习路径

### 初学者路径
1. **JSON** - 数据交换基础
2. **Google Test** - 测试驱动开发
3. **spdlog** - 日志记录
4. **Boost** - 通用工具

### 中级路径
1. **Protobuf** - 序列化进阶
2. **Boost.Asio** - 网络编程
3. **Intel TBB** - 并发编程
4. **Eigen** - 科学计算

### 高级路径
1. **FlatBuffers/Cap'n Proto** - 高性能序列化
2. **Folly** - 高性能工具
3. **Taskflow** - 复杂任务调度
4. **Dear ImGui** - 图形界面

## 项目结构

```
cpp-third-party-libraries/
├── README.md                    # 本文件
├── 01_RESEARCH.md              # 市场调研
├── 02_REQUIREMENTS.md          # 需求分析
├── 03_DESIGN.md                # 技术设计
├── 04_PRODUCT.md               # 产品思考
├── 05_DEVELOPMENT.md           # 开发手册
├── CMakeLists.txt              # 主 CMake 文件
├── containers/                 # 容器库示例
│   ├── boost_container/
│   ├── abseil/
│   ├── folly/
│   └── eastl/
├── serialization/              # 序列化库示例
│   ├── protobuf/
│   ├── flatbuffers/
│   ├── capnproto/
│   ├── json/
│   └── msgpack/
├── networking/                 # 网络库示例
│   ├── boost_asio/
│   ├── cpp_httplib/
│   ├── cpr/
│   └── libcurl/
├── concurrency/                # 并发库示例
│   ├── tbb/
│   ├── folly_futures/
│   └── taskflow/
├── testing/                    # 测试库示例
│   ├── gtest/
│   ├── gmock/
│   ├── catch2/
│   └── doctest/
├── logging/                    # 日志库示例
│   ├── spdlog/
│   ├── glog/
│   └── boost_log/
├── math/                       # 数学库示例
│   ├── eigen/
│   ├── armadillo/
│   └── boost_math/
├── graphics/                   # 图形库示例
│   ├── imgui/
│   ├── sfml/
│   └── sdl/
├── utils/                      # 工具库示例
│   ├── boost/
│   ├── abseil/
│   ├── folly/
│   └── range_v3/
└── build/                      # 构建工具示例
    ├── vcpkg/
    ├── conan/
    └── fetch_content/
```

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License