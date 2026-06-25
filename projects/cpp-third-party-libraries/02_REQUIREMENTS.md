# 需求分析

## 项目目标

创建一个全面的 C++ 三方库介绍项目，帮助开发者：
1. 了解常用三方库的功能和特点
2. 掌握库的基本使用方法
3. 学会在实际项目中集成和使用这些库
4. 做出合理的库选择决策

## 功能需求

### 1. 容器和数据结构

#### Boost.Container
- **flat_map/flat_set** - 基于排序 vector 的容器
- **stable_vector** - 稳定引用的容器
- **small_vector** - 小对象优化的 vector
- **static_vector** - 固定容量的 vector

#### Abseil
- **flat_hash_map** - 高性能哈希表
- **node_hash_map** - 节点稳定的哈希表
- **btree_map** - B 树容器
- **InlinedVector** - 内联向量

#### Folly
- **F14HashMap** - 14 项优化的哈希表
- **small_vector** - 小对象优化
- **FBVector** - Facebook 优化的 vector

#### EASTL
- **fixed_vector** - 固定容量向量
- **fixed_map** - 固定容量映射
- **hashtable** - 通用哈希表

### 2. 序列化

#### Protobuf
- 消息定义和生成
- 序列化和反序列化
- 版本演进
- 跨语言支持

#### FlatBuffers
- Schema 定义
- 零拷贝访问
- 嵌套对象
- 向量和字符串

#### Cap'n Proto
- Schema 定义
- 零拷贝序列化
- 动态消息
- RPC 框架

#### JSON
- nlohmann/json
  - 解析和生成
  - JSON Pointer
  - 自定义类型转换
- RapidJSON
  - DOM 解析
  - SAX 解析
  - 内存池

#### MessagePack
- 二进制格式
- 类型映射
- 流式处理

### 3. 网络

#### Boost.Asio
- 同步/异步 I/O
- TCP/UDP 套接字
- 定时器
- 信号处理
- 协程支持

#### cpp-httplib
- HTTP 服务器
- HTTP 客户端
- SSL 支持
- 文件上传

#### CPR
- GET/POST 请求
- 参数处理
- 文件上传
- 会话管理

#### libcurl
- URL 传输
- 多协议支持
- 回调函数
- 多句柄

### 4. 并发

#### Intel TBB
- parallel_for
- parallel_reduce
- task_group
- 流水线
- 并发容器

#### Folly Futures
- Future/Promise
- 链式调用
- 错误处理
- 协程集成

#### Taskflow
- 任务图定义
- 条件任务
- 动态任务
- GPU 任务

### 5. 测试

#### Google Test
- 测试宏
- 断言
- 测试夹具
- 参数化测试
- 死亡测试

#### Google Mock
- Mock 类
- 期望设置
- 参数匹配
- 动作定义

#### Catch2
- SECTION 测试
- BDD 风格
- 自定义匹配器
- 基准测试

#### doctest
- 轻量级测试
- 快速编译
- 子测试
- 测试套件

### 6. 日志

#### spdlog
- 多后端支持
- 异步日志
- 格式化
- 日志轮转

#### glog
- 日志级别
- 条件日志
- 详细日志
- 信号处理

#### Boost.Log
- 日志源
- 过滤器
- 格式化器
- 后端

### 7. 数学和科学

#### Eigen
- 矩阵运算
- 向量运算
- 线性代数
- 几何变换
- 稀疏矩阵

#### Armadillo
- 矩阵类
- 线性代数
- 统计函数
- 信号处理

#### Boost.Math
- 特殊函数
- 统计分布
- 数值积分
- 多精度

### 8. 图形和 GUI

#### Dear ImGui
- 窗口控件
- 绘制原语
- 自定义控件
- 多后端

#### SFML
- 窗口管理
- 图形绘制
- 音频播放
- 网络通信

#### SDL
- 窗口管理
- 事件处理
- 渲染器
- 音频

### 9. 工具库

#### Boost
- 字符串算法
- 文件系统
- 正则表达式
- 智能指针
- 日期时间

#### Abseil
- 字符串工具
- 容器
- 时间
- 随机数

#### Folly
- 字符串格式化
- 容器
- 并发原语
- 内存管理

#### range-v3
- 视图
- 动作
- 算法
- 概念

### 10. 构建和包管理

#### vcpkg
- 包安装
- 版本管理
- 集成方式
- 自定义端口

#### Conan
- 包创建
- 依赖解析
- 配置文件
- 远程仓库

#### FetchContent
- 依赖声明
- 版本锁定
- 子目录添加
- 配置传递

## 非功能需求

### 1. 代码质量

- **可编译** - 所有示例必须可编译运行
- **有注释** - 关键代码有详细注释
- **最佳实践** - 展示库的最佳使用方式
- **错误处理** - 展示正确的错误处理

### 2. 文档质量

- **完整性** - 涵盖所有主要功能
- **准确性** - 信息准确无误
- **可读性** - 结构清晰，易于理解
- **实用性** - 包含实际使用场景

### 3. 项目结构

- **模块化** - 每个库独立目录
- **一致性** - 统一的命名和结构
- **可扩展** - 易于添加新库
- **易导航** - 清晰的目录结构

## 库清单

### 必须包含（30 个）

| 分类 | 库 | 优先级 |
|------|-----|--------|
| 容器 | Boost.Container | 高 |
| 容器 | Abseil | 高 |
| 容器 | Folly | 中 |
| 容器 | EASTL | 中 |
| 序列化 | Protobuf | 高 |
| 序列化 | FlatBuffers | 高 |
| 序列化 | Cap'n Proto | 中 |
| 序列化 | nlohmann/json | 高 |
| 序列化 | RapidJSON | 高 |
| 序列化 | MessagePack | 中 |
| 网络 | Boost.Asio | 高 |
| 网络 | cpp-httplib | 高 |
| 网络 | CPR | 高 |
| 网络 | libcurl | 高 |
| 并发 | Intel TBB | 高 |
| 并发 | Folly Futures | 中 |
| 并发 | Taskflow | 高 |
| 测试 | Google Test | 高 |
| 测试 | Google Mock | 高 |
| 测试 | Catch2 | 高 |
| 测试 | doctest | 中 |
| 日志 | spdlog | 高 |
| 日志 | glog | 高 |
| 日志 | Boost.Log | 中 |
| 数学 | Eigen | 高 |
| 数学 | Armadillo | 高 |
| 数学 | Boost.Math | 中 |
| 图形 | Dear ImGui | 高 |
| 图形 | SFML | 高 |
| 图形 | SDL | 高 |
| 工具 | Boost | 高 |
| 工具 | Abseil | 高 |
| 工具 | Folly | 中 |
| 工具 | range-v3 | 高 |
| 构建 | vcpkg | 高 |
| 构建 | Conan | 高 |
| 构建 | FetchContent | 高 |

### 可选扩展（10 个）

| 分类 | 库 | 优先级 |
|------|-----|--------|
| 序列化 | cereal | 低 |
| 网络 | Beast (Boost) | 低 |
| 并发 | libunifex | 低 |
| 测试 | Boost.Test | 低 |
| 日志 | easylogging++ | 低 |
| 数学 | VTK | 低 |
| 图形 | Qt | 低 |
| 工具 | Poco | 低 |
| 构建 | Bazel | 低 |
| 构建 | Meson | 低 |

## 交付物

### 文档
- [x] README.md
- [x] 01_RESEARCH.md
- [x] 02_REQUIREMENTS.md
- [x] 03_DESIGN.md
- [x] 04_PRODUCT.md
- [x] 05_DEVELOPMENT.md

### 代码示例
- [ ] 30+ 个库的示例代码
- [ ] 每个库至少 3 个示例
- [ ] CMakeLists.txt 配置
- [ ] 构建和运行说明

### 测试
- [ ] 编译测试
- [ ] 运行测试
- [ ] 跨平台测试

## 验收标准

1. **完整性** - 所有必须包含的库都有示例
2. **可编译** - 所有示例可成功编译
3. **可运行** - 所有示例可正常运行
4. **有文档** - 每个示例有说明文档
5. **有注释** - 关键代码有详细注释