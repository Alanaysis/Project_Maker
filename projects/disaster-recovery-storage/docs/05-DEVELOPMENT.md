# 开发手册：容灾数据存储系统

## 1. 开发环境搭建

### 1.1 系统要求

| 工具 | 版本 | 用途 |
|------|------|------|
| C++编译器 | GCC 7+ / Clang 6+ | 编译C++代码 |
| CMake | 3.14+ | 构建系统 |
| Git | 2.0+ | 版本控制 |
| Python | 3.6+ | 脚本工具（可选） |

### 1.2 安装步骤

#### Ubuntu/Debian
```bash
# 安装编译工具
sudo apt update
sudo apt install build-essential cmake git

# 验证安装
g++ --version
cmake --version
```

#### CentOS/RHEL
```bash
# 安装开发工具组
sudo yum groupinstall "Development Tools"
sudo yum install cmake3 git

# 验证安装
g++ --version
cmake3 --version
```

#### macOS
```bash
# 安装Xcode命令行工具
xcode-select --install

# 安装CMake (使用Homebrew)
brew install cmake

# 验证安装
clang++ --version
cmake --version
```

### 1.3 获取代码

```bash
# 克隆项目
git clone <repository-url>
cd disaster-recovery-storage

# 或者下载压缩包
wget <release-url>
tar -xzf disaster-recovery-storage.tar.gz
cd disaster-recovery-storage
```

## 2. 构建项目

### 2.1 基本构建

```bash
# 创建构建目录
mkdir build
cd build

# 配置CMake
cmake ..

# 编译
make -j$(nproc)

# 运行测试
make test
```

### 2.2 构建选项

```bash
# Debug模式（包含调试信息）
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release模式（优化）
cmake -DCMAKE_BUILD_TYPE=Release ..

# 指定安装路径
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
```

### 2.3 常见构建问题

#### 问题1: CMake版本过低
```
CMake Error: CMake 3.14 or higher is required.
```
**解决方案**: 升级CMake或使用系统包管理器安装新版本

#### 问题2: 编译器不支持C++17
```
error: 'optional' is not a member of 'std'
```
**解决方案**: 确保编译器支持C++17，或升级编译器

#### 问题3: 依赖缺失
```
fatal error: googletest.h: No such file or directory
```
**解决方案**: CMake会自动下载Google Test，确保网络连接正常

## 3. 项目结构详解

```
disaster-recovery-storage/
├── CMakeLists.txt              # 主CMake配置
├── README.md                   # 项目说明
├── include/                    # 头文件目录
│   ├── storage/               # 存储相关头文件
│   │   ├── storage_client.h   # 客户端接口
│   │   ├── object.h           # 数据对象定义
│   │   └── types.h            # 类型定义
│   ├── ec/                    # 纠删码相关
│   │   ├── galois_field.h     # 有限域运算
│   │   ├── reed_solomon.h     # Reed-Solomon编码
│   │   └── ec_manager.h       # 纠删码管理器
│   ├── network/               # 网络相关
│   │   ├── node.h             # 节点定义
│   │   ├── rpc.h              # RPC接口
│   │   └── heartbeat.h        # 心跳检测
│   └── utils/                 # 工具类
│       ├── checksum.h         # 校验和计算
│       ├── logger.h           # 日志工具
│       └── config.h           # 配置管理
├── src/                        # 源代码目录
│   ├── core/                  # 核心实现
│   ├── ec/                    # 纠删码实现
│   ├── network/               # 网络实现
│   └── node/                  # 存储节点实现
├── tests/                      # 测试代码
│   ├── unit/                  # 单元测试
│   └── integration/           # 集成测试
├── examples/                   # 使用示例
│   ├── basic_usage.cpp        # 基本使用示例
│   ├── erasure_coding.cpp     # 纠删码示例
│   └── fault_tolerance.cpp    # 容错示例
└── docs/                       # 文档目录
```

## 4. 核心模块解析

### 4.1 纠删码模块 (EC Module)

#### 4.1.1 有限域运算 (Galois Field)

**文件**: `include/ec/galois_field.h`, `src/ec/galois_field.cpp`

**核心概念**:
- GF(2^8) 有限域包含256个元素
- 加法: XOR运算
- 乘法: 使用对数表加速

**关键代码**:
```cpp
class GaloisField {
public:
    // 初始化有限域
    void init();

    // 加法 (XOR)
    uint8_t add(uint8_t a, uint8_t b) {
        return a ^ b;
    }

    // 乘法 (查表法)
    uint8_t multiply(uint8_t a, uint8_t b) {
        if (a == 0 || b == 0) return 0;
        int log_sum = log_table_[a] + log_table_[b];
        if (log_sum >= 255) log_sum -= 255;
        return exp_table_[log_sum];
    }

private:
    uint8_t exp_table_[256];  // 反对数表
    uint8_t log_table_[256];  // 对数表
};
```

**⭐ 重点难点**:
1. 不可约多项式的选择
2. 对数表和反对数表的生成
3. 除法和求逆运算的实现

**💡 思考**:
- 为什么使用对数表而不是直接计算？
- GF(2^8)为什么选择256个元素？

---

#### 4.1.2 Reed-Solomon编码

**文件**: `include/ec/reed_solomon.h`, `src/ec/reed_solomon.cpp`

**核心概念**:
- 将数据分为k个数据块
- 生成m个校验块
- 可以容忍任意m个块丢失

**关键代码**:
```cpp
class ReedSolomon {
public:
    // 初始化编解码器
    Status init(int data_shards, int parity_shards);

    // 编码数据
    Status encode(const uint8_t* data, size_t size,
                  std::vector<std::vector<uint8_t>>& shards);

    // 解码数据
    Status decode(const std::vector<std::vector<uint8_t>>& shards,
                  const std::vector<bool>& available,
                  std::vector<uint8_t>& data);

private:
    int data_shards_;      // 数据分片数
    int parity_shards_;    // 校验分片数
    Matrix encode_matrix_; // 编码矩阵

    // 生成编码矩阵
    void buildEncodeMatrix();

    // 高斯消元求解
    std::vector<uint8_t> gaussianElimination(
        const Matrix& A, const std::vector<uint8_t>& b);
};
```

**⭐ 重点难点**:
1. 编码矩阵的构造（范德蒙德矩阵）
2. 解码时的矩阵求逆
3. 处理部分分片丢失的情况

**💡 思考**:
- 为什么使用范德蒙德矩阵？
- 编码矩阵需要满足什么条件？

---

### 4.2 数据分片模块

**文件**: `include/storage/data_sharder.h`, `src/core/data_sharder.cpp`

**核心功能**:
- 将大数据分割成固定大小的分片
- 处理最后一个分片的填充
- 管理分片元数据

**关键代码**:
```cpp
class DataSharder {
public:
    // 配置分片大小
    void configure(size_t shard_size);

    // 分片数据
    Status shard(const std::vector<uint8_t>& data,
                 std::vector<Shard>& shards);

    // 重组数据
    Status reassemble(const std::vector<Shard>& shards,
                      std::vector<uint8_t>& data);

private:
    size_t shard_size_;  // 分片大小
};
```

**⭐ 重点难点**:
1. 处理数据大小不是分片大小整数倍的情况
2. 分片元数据的设计
3. 如何高效重组数据

---

### 4.3 副本管理模块

**文件**: `include/storage/replica_manager.h`, `src/core/replica_manager.cpp`

**核心功能**:
- 管理数据副本的放置
- 实现Quorum机制
- 处理副本一致性

**关键代码**:
```cpp
class ReplicaManager {
public:
    // 配置副本策略
    void configure(int replication_factor,
                   int write_quorum,
                   int read_quorum);

    // 选择写入节点
    std::vector<NodeId> selectWriteNodes(
        const std::vector<Node>& available_nodes);

    // 选择读取节点
    std::vector<NodeId> selectReadNodes(
        const std::vector<Node>& available_nodes);

    // 检查Quorum
    bool checkWriteQuorum(const std::vector<Status>& responses);
    bool checkReadQuorum(const std::vector<Status>& responses);

private:
    int replication_factor_;
    int write_quorum_;
    int read_quorum_;
};
```

**⭐ 重点难点**:
1. NWR模型的理解和实现
2. 故障域感知的节点选择
3. 一致性保证的边界条件

**💡 思考**:
- W + R > N 为什么能保证一致性？
- 如何处理网络分区的情况？

---

### 4.4 故障检测模块

**文件**: `include/network/failure_detector.h`, `src/network/failure_detector.cpp`

**核心功能**:
- 心跳检测机制
- 节点状态管理
- 故障恢复检测

**关键代码**:
```cpp
class FailureDetector {
public:
    // 启动检测
    void start();

    // 停止检测
    void stop();

    // 注册节点
    void registerNode(const NodeId& node);

    // 移除节点
    void removeNode(const NodeId& node);

    // 获取节点状态
    NodeStatus getNodeStatus(const NodeId& node) const;

    // 心跳响应处理
    void onHeartbeatResponse(const NodeId& node);

private:
    // 心跳检测线程
    void heartbeatLoop();

    // 检查超时
    void checkTimeouts();

    std::unordered_map<NodeId, NodeInfo> nodes_;
    std::atomic<bool> running_;
};
```

**⭐ 重点难点**:
1. 如何避免误判（网络抖动 vs 真实故障）
2. 心跳间隔和超时时间的设置
3. 故障检测的及时性和准确性权衡

**💡 思考**:
- 为什么简单的超时检测不够？
- Phi Accrual Failure Detector的优势是什么？

---

### 4.5 存储节点模块

**文件**: `include/node/storage_node.h`, `src/node/storage_node.cpp`

**核心功能**:
- 本地数据存储
- 接收和处理请求
- 响应心跳

**关键代码**:
```cpp
class StorageNode {
public:
    // 初始化节点
    Status init(const NodeConfig& config);

    // 存储分片
    Status storeShard(const Shard& shard);

    // 读取分片
    Status readShard(const std::string& shard_id,
                     Shard& shard);

    // 删除分片
    Status deleteShard(const std::string& shard_id);

    // 获取节点信息
    NodeInfo getNodeInfo() const;

private:
    NodeId id_;
    std::string data_dir_;
    std::unordered_map<std::string, Shard> shards_;
};
```

**⭐ 重点难点**:
1. 本地存储引擎的设计
2. 并发访问控制
3. 数据持久化

---

## 5. 开发工作流

### 5.1 分支策略

```
main (主分支)
  │
  ├── develop (开发分支)
  │     │
  │     ├── feature/ec-module (功能分支)
  │     ├── feature/replication (功能分支)
  │     └── feature/fault-detection (功能分支)
  │
  └── release/v1.0 (发布分支)
```

### 5.2 开发流程

1. **创建功能分支**
   ```bash
   git checkout -b feature/ec-module develop
   ```

2. **开发功能**
   ```bash
   # 编写代码
   # 编写测试
   # 运行测试
   make test
   ```

3. **提交代码**
   ```bash
   git add .
   git commit -m "feat: implement Reed-Solomon encoding"
   ```

4. **合并到开发分支**
   ```bash
   git checkout develop
   git merge feature/ec-module
   ```

5. **删除功能分支**
   ```bash
   git branch -d feature/ec-module
   ```

### 5.3 提交规范

**格式**: `<type>(<scope>): <subject>`

**类型**:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat(ec): implement Reed-Solomon encoding

- Add GaloisField class for GF(2^8) operations
- Implement encode/decode methods
- Add unit tests for encoding/decoding

Closes #123
```

## 6. 测试指南

### 6.1 测试类型

#### 单元测试
- 测试单个类或函数
- 隔离测试，不依赖外部
- 快速运行

#### 集成测试
- 测试模块间交互
- 可能需要外部依赖
- 较慢运行

### 6.2 编写单元测试

**测试文件命名**: `test_<module>.cpp`

**示例**:
```cpp
#include <gtest/gtest.h>
#include "ec/galois_field.h"

class GaloisFieldTest : public ::testing::Test {
protected:
    void SetUp() override {
        gf_.init();
    }

    GaloisField gf_;
};

TEST_F(GaloisFieldTest, Addition) {
    // XOR运算
    EXPECT_EQ(gf_.add(0x53, 0xCA), 0x99);
}

TEST_F(GaloisFieldTest, Multiplication) {
    // 乘法运算
    EXPECT_EQ(gf_.multiply(0x53, 0xCA), 0x01);
}

TEST_F(GaloisFieldTest, MultiplyByZero) {
    EXPECT_EQ(gf_.multiply(0x53, 0x00), 0x00);
}

TEST_F(GaloisFieldTest, MultiplyByOne) {
    EXPECT_EQ(gf_.multiply(0x53, 0x01), 0x53);
}
```

### 6.3 运行测试

```bash
# 运行所有测试
make test

# 运行特定测试
./tests/unit_tests --gtest_filter="GaloisFieldTest.*"

# 生成测试报告
./tests/unit_tests --gtest_output=xml:test_results.xml
```

### 6.4 测试覆盖率

```bash
# 生成覆盖率报告
cmake -DCMAKE_BUILD_TYPE=Coverage ..
make
make test
make coverage

# 查看报告
# 报告位于 build/coverage/index.html
```

## 7. 调试技巧

### 7.1 使用GDB

```bash
# 编译Debug版本
cmake -DCMAKE_BUILD_TYPE=Debug ..
make

# 运行GDB
gdb ./tests/unit_tests

# GDB常用命令
(gdb) break main          # 设置断点
(gdb) run                 # 运行程序
(gdb) next                # 单步执行
(gdb) step                # 进入函数
(gdb) print variable      # 打印变量
(gdb) backtrace           # 查看调用栈
(gdb) quit                # 退出
```

### 7.2 使用Valgrind检测内存问题

```bash
# 检测内存泄漏
valgrind --leak-check=full ./tests/unit_tests

# 生成详细报告
valgrind --leak-check=full --log-file=valgrind.log ./tests/unit_tests
```

### 7.3 使用AddressSanitizer

```bash
# 编译时启用ASan
cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_ASAN=ON ..
make

# 运行程序会自动检测内存问题
./tests/unit_tests
```

### 7.4 日志调试

```cpp
#include "utils/logger.h"

void some_function() {
    LOG_DEBUG("Entering some_function");
    LOG_INFO("Processing data: {}", data.size());
    LOG_WARN("Low memory warning");
    LOG_ERROR("Failed to open file: {}", filename);
}
```

## 8. 性能优化

### 8.1 编译优化

```bash
# Release模式优化
cmake -DCMAKE_BUILD_TYPE=Release ..

# 使用LTO（链接时优化）
cmake -DCMAKE_BUILD_TYPE=Release -DENABLE_LTO=ON ..
```

### 8.2 代码优化技巧

#### 8.2.1 避免不必要的拷贝
```cpp
// 不好：拷贝整个vector
void process(std::vector<uint8_t> data);

// 好：使用const引用
void process(const std::vector<uint8_t>& data);

// 更好：使用移动语义
void process(std::vector<uint8_t>&& data);
```

#### 8.2.2 使用预留空间
```cpp
// 不好：多次重新分配
std::vector<uint8_t> result;
for (int i = 0; i < 1000; i++) {
    result.push_back(data[i]);
}

// 好：预留空间
std::vector<uint8_t> result;
result.reserve(1000);
for (int i = 0; i < 1000; i++) {
    result.push_back(data[i]);
}
```

#### 8.2.3 使用查找表
```cpp
// 不好：重复计算
for (int i = 0; i < 256; i++) {
    result[i] = slow_function(i);
}

// 好：预计算查找表
static const uint8_t lookup_table[256] = {
    // 预计算的值
};
```

### 8.3 性能测试

```bash
# 运行性能测试
./tests/performance_tests

# 生成性能报告
./tests/performance_tests --benchmark_format=json > perf.json
```

## 9. 代码规范

### 9.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `StorageClient` |
| 函数名 | camelCase | `readData()` |
| 变量名 | snake_case | `data_size` |
| 常量 | UPPER_SNAKE_CASE | `MAX_SHARD_SIZE` |
| 成员变量 | snake_case + 后缀_ | `data_size_` |

### 9.2 代码格式

```cpp
// 头文件保护
#ifndef DISASTER_RECOVERY_STORAGE_EC_GALOIS_FIELD_H_
#define DISASTER_RECOVERY_STORAGE_EC_GALOIS_FIELD_H_

#include <cstdint>

namespace disaster_recovery {
namespace ec {

class GaloisField {
public:
    GaloisField();
    ~GaloisField();

    // 初始化有限域
    void init();

    // 加法运算
    uint8_t add(uint8_t a, uint8_t b);

private:
    uint8_t exp_table_[256];
    uint8_t log_table_[256];
};

}  // namespace ec
}  // namespace disaster_recovery

#endif  // DISASTER_RECOVERY_STORAGE_EC_GALOIS_FIELD_H_
```

### 9.3 注释规范

```cpp
/**
 * @brief Reed-Solomon编码器
 *
 * 实现Reed-Solomon纠删码编码和解码功能
 * 支持可配置的数据分片数和校验分片数
 */
class ReedSolomon {
public:
    /**
     * @brief 初始化编码器
     * @param data_shards 数据分片数
     * @param parity_shards 校验分片数
     * @return 初始化状态
     */
    Status init(int data_shards, int parity_shards);

    /**
     * @brief 编码数据
     *
     * 将原始数据编码为多个分片，包括数据分片和校验分片
     *
     * @param data 原始数据
     * @param size 数据大小
     * @param shards 输出的分片列表
     * @return 编码状态
     */
    Status encode(const uint8_t* data, size_t size,
                  std::vector<std::vector<uint8_t>>& shards);
};
```

## 10. 常见问题

### 10.1 编译问题

**Q: 编译时提示找不到CMakeLists.txt**
A: 确保在项目根目录运行cmake，而不是在子目录

**Q: 编译时提示C++17特性不支持**
A: 检查编译器版本，确保支持C++17

**Q: 链接时提示undefined reference**
A: 检查是否所有源文件都已编译，库是否正确链接

### 10.2 运行问题

**Q: 运行测试时提示Segmentation Fault**
A: 使用GDB或Valgrind定位问题，检查数组越界和空指针

**Q: 程序运行缓慢**
A: 使用性能分析工具定位瓶颈，检查是否有不必要的内存分配

### 10.3 学习问题

**Q: 纠删码数学太难理解**
A: 从GF(2)开始，逐步理解有限域运算，参考在线教程

**Q: 分布式系统概念太多**
A: 先理解基本概念，再学习具体协议，循序渐进

## 11. 学习资源

### 11.1 C++学习
- [C++ Primer](https://www.amazon.com/Primer-5th-Stanley-B-Lippman/dp/0321714113)
- [Effective Modern C++](https://www.amazon.com/Effective-Modern-Specific-Ways-Improve/dp=1491903996)
- [C++ Reference](https://cppreference.com/)

### 11.2 分布式系统
- [MIT 6.824](https://pdos.csail.mit.edu/6.824/)
- [Distributed Systems](https://www.distributed-systems.net/)
- [Designing Data-Intensive Applications](https://dataintensive.net/)

### 11.3 纠删码
- [Erasure Coding for Storage](https://www.usenix.org/legacy/events/fast12/tech/full_papers/Plank.pdf)
- [Reed-Solomon Interactive Tutorial](https://research.swtch.com/field)
- [GF(2^8) Tutorial](https://www.samiam.org/galois.html)

---

*本手册将根据开发进展持续更新*
