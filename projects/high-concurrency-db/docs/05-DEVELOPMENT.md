# 开发手册

## 1. 环境搭建

### 1.1 系统要求

| 依赖 | 版本 | 用途 |
|------|------|------|
| C++ 编译器 | GCC 9+ / Clang 10+ | 编译 C++ 代码 |
| CMake | 3.14+ | 构建系统 |
| Git | 2.0+ | 版本控制 |

### 1.2 Ubuntu/Debian

```bash
# 安装基础工具
sudo apt-get update
sudo apt-get install -y build-essential cmake git

# 验证安装
g++ --version
cmake --version
```

### 1.3 macOS

```bash
# 安装 Xcode Command Line Tools
xcode-select --install

# 安装 CMake (使用 Homebrew)
brew install cmake

# 验证
cmake --version
```

### 1.4 克隆项目

```bash
git clone <repository-url>
cd high-concurrency-db
```

## 2. 构建项目

### 2.1 标准构建

```bash
# 创建构建目录
mkdir build && cd build

# 配置
cmake ..

# 编译
make -j$(nproc)

# 运行测试
./minidb_tests

# 运行示例
./minidb_example
```

### 2.2 Debug 构建

```bash
mkdir build-debug && cd build-debug
cmake -DCMAKE_BUILD_TYPE=Debug ..
make -j$(nproc)
```

### 2.3 Release 构建

```bash
mkdir build-release && cd build-release
cmake -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
```

## 3. 项目结构详解

```
high-concurrency-db/
├── CMakeLists.txt              # 顶层 CMake 配置
├── README.md                   # 项目说明
├── LEARNING_NOTES.md           # 学习笔记模板
│
├── include/                    # 头文件目录
│   ├── core/                   # 核心类型定义
│   │   ├── common.h            # 通用类型和常量
│   │   ├── config.h            # 配置常量
│   │   └── status.h            # 状态码
│   │
│   ├── sql/                    # SQL 解析器
│   │   ├── tokenizer.h         # 词法分析器
│   │   ├── parser.h            # 语法分析器
│   │   ├── ast.h               # 抽象语法树
│   │   └── expression.h        # 表达式
│   │
│   ├── storage/                # 存储引擎
│   │   ├── disk_manager.h      # 磁盘管理器
│   │   ├── buffer_pool.h       # 缓冲池管理器
│   │   ├── page.h              # 页面
│   │   ├── table.h             # 表
│   │   └── bplus_tree.h        # B+ 树索引
│   │
│   ├── concurrency/            # 并发控制
│   │   ├── lock_manager.h      # 锁管理器
│   │   └── transaction.h       # 事务
│   │
│   └── cache/                  # 缓存管理
│       └── lru_cache.h         # LRU 缓存
│
├── src/                        # 源文件目录
│   ├── core/
│   │   └── status.cpp
│   ├── sql/
│   │   ├── tokenizer.cpp
│   │   ├── parser.cpp
│   │   └── ast.cpp
│   ├── storage/
│   │   ├── disk_manager.cpp
│   │   ├── buffer_pool.cpp
│   │   ├── page.cpp
│   │   ├── table.cpp
│   │   └── bplus_tree.cpp
│   ├── concurrency/
│   │   ├── lock_manager.cpp
│   │   └── transaction.cpp
│   └── cache/
│       └── lru_cache.cpp
│
├── tests/                      # 测试目录
│   ├── test_tokenizer.cpp
│   ├── test_parser.cpp
│   ├── test_bplus_tree.cpp
│   ├── test_buffer_pool.cpp
│   ├── test_disk_manager.cpp
│   └── test_concurrency.cpp
│
├── examples/                   # 示例目录
│   ├── simple_crud.cpp         # 简单增删改查
│   └── concurrent_access.cpp   # 并发访问示例
│
└── docs/                       # 文档目录
    ├── 01-RESEARCH.md
    ├── 02-REQUIREMENTS.md
    ├── 03-DESIGN.md
    ├── 04-PRODUCT.md
    └── 05-DEVELOPMENT.md
```

## 4. 核心模块解析

### 4.1 磁盘管理器 (Disk Manager)

**职责**: 管理数据库文件的读写操作

**关键实现**:
```cpp
class DiskManager {
public:
    // 从磁盘读取页面
    void readPage(page_id_t page_id, char* page_data) {
        // 计算文件偏移
        size_t offset = page_id * PAGE_SIZE;
        db_io_.seekp(offset);
        db_io_.read(page_data, PAGE_SIZE);
    }

    // 写入页面到磁盘
    void writePage(page_id_t page_id, const char* page_data) {
        size_t offset = page_id * PAGE_SIZE;
        db_io_.seekp(offset);
        db_io_.write(page_data, PAGE_SIZE);
    }
};
```

**学习要点**:
- 文件 I/O 操作
- 页面对齐
- 错误处理

### 4.2 缓冲池管理器 (Buffer Pool Manager)

**职责**: 管理内存中的页面缓存

**核心算法**:
```
fetchPage(page_id):
    1. 检查 page_table_ 是否已缓存
    2. 如果命中，更新 LRU，返回页面
    3. 如果未命中：
       a. 检查 free_list_ 是否有空闲帧
       b. 如果没有，调用 replacer_ 获取可替换帧
       c. 如果替换帧是脏页，先写回磁盘
       d. 从磁盘读取页面
       e. 更新 page_table_
    4. 返回页面
```

**学习要点**:
- 缓存替换策略 (LRU)
- 脏页管理
- 并发安全

### 4.3 B+ 树索引

**职责**: 提供高效的键值查找

**核心操作**:

**查找**:
```
search(key):
    1. 从根节点开始
    2. 在内部节点中找到合适的子节点
    3. 递归向下直到叶子节点
    4. 在叶子节点中查找 key
    5. 返回结果
```

**插入**:
```
insert(key, value):
    1. 找到应该插入的叶子节点
    2. 如果叶子节点有空间，直接插入
    3. 如果叶子节点已满：
       a. 分裂叶子节点
       b. 将中间 key 提升到父节点
       c. 如果父节点也满，递归分裂
```

**学习要点**:
- B+ 树的性质
- 节点分裂和合并
- 页内查找（二分搜索）

### 4.4 SQL 解析器

**职责**: 将 SQL 文本转换为 AST

**词法分析**:
```cpp
Token Tokenizer::nextToken() {
    skipWhitespace();
    if (isdigit(current())) {
        return readNumber();
    } else if (isalpha(current())) {
        return readIdentifier();
    } else if (current() == '\'') {
        return readString();
    }
    // ... 处理运算符和分隔符
}
```

**语法分析** (递归下降):
```cpp
unique_ptr<Statement> Parser::parse() {
    switch (currentToken().type) {
        case TokenType::SELECT:
            return parseSelect();
        case TokenType::INSERT:
            return parseInsert();
        case TokenType::CREATE:
            return parseCreateTable();
        // ...
    }
}
```

**学习要点**:
- 词法分析原理
- 递归下降解析
- AST 设计

### 4.5 查询执行器

**职责**: 执行查询计划，返回结果

**Volcano 模型**:
```cpp
class AbstractExecutor {
public:
    virtual void init() = 0;
    virtual bool next(Row* row) = 0;
};

// 调用方式
executor->init();
Row row;
while (executor->next(&row)) {
    // 处理 row
}
```

**学习要点**:
- Iterator 模型
- 算子组合
- 执行计划树

### 4.6 锁管理器

**职责**: 管理并发访问的锁

**锁获取流程**:
```
lockShared(txn, resource):
    1. 获取 lock_table_latch_
    2. 查找或创建 resource 的 LockRequestQueue
    3. 检查是否与现有锁冲突
    4. 如果不冲突，授予锁
    5. 如果冲突，等待或回滚（死锁预防）
```

**学习要点**:
- 锁兼容矩阵
- 死锁预防
- 条件变量

## 5. 开发流程

### 5.1 添加新功能

1. **设计**
   - 在 `docs/03-DESIGN.md` 中添加设计
   - 确定接口和数据结构

2. **实现**
   - 在 `include/` 中添加头文件
   - 在 `src/` 中实现
   - 添加单元测试

3. **测试**
   - 运行所有测试
   - 确保无内存泄漏

4. **文档**
   - 更新 README.md
   - 添加代码注释

### 5.2 代码规范

**命名规范**:
- 类名：PascalCase (如 `BufferPoolManager`)
- 函数名：camelCase (如 `fetchPage`)
- 变量名：snake_case (如 `page_id`)
- 常量：UPPER_SNAKE_CASE (如 `PAGE_SIZE`)
- 枚举值：PascalCase (如 `TokenType::SELECT`)

**注释规范**:
```cpp
/**
 * @brief 从缓冲池获取页面
 *
 * @param page_id 页面 ID
 * @return Page* 页面指针，如果不存在返回 nullptr
 *
 * @note 调用者需要在使用完毕后调用 unpinPage
 */
Page* fetchPage(page_id_t page_id);
```

### 5.3 错误处理

使用 Status 类返回错误：
```cpp
Status status = someOperation();
if (!status.ok()) {
    std::cerr << "Error: " << status.message() << std::endl;
    return status;
}
```

## 6. 调试技巧

### 6.1 GDB 调试

```bash
# 编译 Debug 版本
cd build-debug
cmake -DCMAKE_BUILD_TYPE=Debug ..
make

# 运行 GDB
gdb ./minidb_tests

# 常用命令
(gdb) break BPlusTree::insert  # 设置断点
(gdb) run                      # 运行
(gdb) next                     # 单步
(gdb) print variable           # 打印变量
(gdb) backtrace                # 调用栈
```

### 6.2 AddressSanitizer

```bash
cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZER=ON ..
make
./minidb_tests
```

### 6.3 日志输出

```cpp
#ifdef DEBUG
#define LOG(msg) std::cout << "[DEBUG] " << msg << std::endl
#else
#define LOG(msg)
#endif
```

## 7. 性能分析

### 7.1 gprof

```bash
cmake -DCMAKE_CXX_FLAGS="-pg" ..
make
./minidb_tests
gprof minidb_tests gmon.out > analysis.txt
```

### 7.2 perf

```bash
perf record ./minidb_tests
perf report
```

## 8. 常见问题

### Q1: 编译错误 "C++17 required"
**解决**: 确保 CMakeLists.txt 中设置了 `CMAKE_CXX_STANDARD 17`

### Q2: 段错误
**解决**: 使用 AddressSanitizer 定位问题

### Q3: 测试失败
**解决**: 检查日志输出，使用 GDB 单步调试

### Q4: 性能问题
**解决**: 使用 gprof 或 perf 分析热点

## 9. 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 创建 Pull Request
5. 等待 Code Review

## 10. 学习资源

### 书籍
- 《Database Internals》
- 《CMU 15-445 Course Notes》
- 《The Art of Computer Programming, Vol. 3》

### 视频
- CMU 15-445 (YouTube)
- MIT 6.830

### 在线课程
- [CMU 15-445](https://15445.courses.cs.cmu.edu/)
- [Stanford CS346](https://web.stanford.edu/class/cs346/)
