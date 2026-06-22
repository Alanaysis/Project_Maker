# 开发手册

## 1. 环境搭建

### 系统要求

- 操作系统：Linux / macOS / Windows (WSL)
- 编译器：GCC 7+ / Clang 5+ / MSVC 2017+
- CMake：3.14+
- Google Test（可选，用于运行测试）

### 安装步骤

#### Ubuntu/Debian

```bash
# 安装编译工具
sudo apt update
sudo apt install build-essential cmake

# 安装 Google Test（可选）
sudo apt install libgtest-dev
cd /usr/src/gtest
sudo cmake .
sudo make
sudo cp lib/*.a /usr/lib
```

#### macOS

```bash
# 安装 Xcode 命令行工具
xcode-select --install

# 安装 CMake
brew install cmake

# 安装 Google Test（可选）
brew install googletest
```

#### Windows (WSL)

```bash
# 使用 Ubuntu 子系统
sudo apt update
sudo apt install build-essential cmake

# 安装 Google Test（可选）
sudo apt install libgtest-dev
```

### 编译项目

```bash
# 进入项目目录
cd projects/matching-engine

# 创建构建目录
mkdir build && cd build

# 配置项目
cmake ..

# 编译
make

# 编译并包含测试
cmake -DBUILD_TESTS=ON ..
make
```

## 2. 项目结构

```
matching-engine/
├── CMakeLists.txt           # CMake 构建配置
├── README.md                # 项目说明
├── include/                 # 头文件目录
│   ├── types.h              # 基础类型定义
│   ├── order_book.h         # 订单簿类声明
│   ├── matching_engine.h    # 撮合引擎类声明
│   └── order_manager.h      # 订单管理器类声明
├── src/                     # 源代码目录
│   ├── order_book.cpp       # 订单簿实现
│   ├── matching_engine.cpp  # 撮合引擎实现
│   └── order_manager.cpp    # 订单管理器实现
├── tests/                   # 测试目录
│   ├── test_order_book.cpp  # 订单簿单元测试
│   ├── test_matching_engine.cpp # 撮合引擎单元测试
│   └── test_main.cpp        # 测试入口
├── examples/                # 示例目录
│   ├── basic.cpp            # 基础示例
│   └── advanced.cpp         # 高级示例
├── docs/                    # 文档目录
│   ├── 01-RESEARCH.md       # 市场调研
│   ├── 02-REQUIREMENTS.md   # 需求分析
│   ├── 03-DESIGN.md         # 技术设计
│   ├── 04-PRODUCT.md        # 产品思维
│   └── 05-DEVELOPMENT.md    # 开发手册（本文件）
└── LEARNING_NOTES.md        # 学习笔记
```

## 3. 核心模块解析

### 模块1：Types（基础类型）

**文件位置**：`include/types.h`

**职责**：定义项目中使用的基础类型

**核心代码**：

```cpp
// ⭐ 重点代码 - 定点数价格类型
// 使用 int64_t 表示价格，避免浮点数精度问题
// 例如：100.50 表示为 10050（保留2位小数）
using Price = int64_t;

// ⭐ 重点代码 - 纳秒级时间戳
// 使用纳秒级时间戳，支持高精度排序
using Timestamp = std::chrono::nanoseconds;

// ⭐ 重点代码 - 订单结构
struct Order {
    OrderId id;
    Side side;
    OrderType type;
    Price price;
    Quantity quantity;
    Quantity filled_quantity;
    OrderStatus status;
    Timestamp timestamp;

    // 计算剩余数量
    Quantity remaining_quantity() const {
        return quantity - filled_quantity;
    }

    // 检查是否完全成交
    bool is_filled() const {
        return filled_quantity >= quantity;
    }
};
```

**理解要点**：
- 为什么用 `int64_t` 而不是 `float` 或 `double`？
- 为什么用纳秒级时间戳？
- `remaining_quantity()` 和 `is_filled()` 的作用是什么？

### 模块2：OrderBook（订单簿）

**文件位置**：`include/order_book.h`, `src/order_book.cpp`

**职责**：维护买卖双方的订单

**核心代码**：

```cpp
// ⭐ 重点代码 - 订单簿数据结构
class OrderBook {
    // 买单簿：价格降序排列（最高买价在前）
    // 使用 std::greater<Price> 实现降序
    std::map<Price, std::list<Order>, std::greater<Price>> bid_book_;

    // 卖单簿：价格升序排列（最低卖价在前）
    // 使用 std::less<Price> 实现升序
    std::map<Price, std::list<Order>, std::less<Price>> ask_book_;

    // 订单索引：通过ID快速查找订单
    // 使用 unordered_map 实现 O(1) 查找
    std::unordered_map<OrderId, OrderLocation> order_index_;
};
```

**理解要点**：
- 为什么买单和卖单使用不同的排序方式？
- 为什么用 `std::map` 而不是 `std::unordered_map`？
- `order_index_` 的作用是什么？

### 模块3：MatchingEngine（撮合引擎）

**文件位置**：`include/matching_engine.h`, `src/matching_engine.cpp`

**职责**：执行撮合逻辑

**核心代码**：

```cpp
// ⭐ 重点代码 - 限价单撮合逻辑
std::vector<Trade> MatchingEngine::try_match_limit_order(Order& order) {
    std::vector<Trade> trades;

    // 对于买单：
    //   - 与卖单簿中价格 <= 买单价格的订单撮合
    //   - 按卖价从低到高的顺序撮合
    //
    // 对于卖单：
    //   - 与买单簿中价格 >= 卖单价格的订单撮合
    //   - 按买价从高到低的顺序撮合

    if (order.side == Side::Buy) {
        // 买单：与卖单簿撮合
        while (!order.is_filled()) {
            Price best_ask = order_book_.best_ask();
            if (best_ask == 0 || best_ask > order.price) {
                break;  // 没有可撮合的卖单
            }
            // 执行撮合...
        }
    } else {
        // 卖单：与买单簿撮合
        // 类似逻辑...
    }

    return trades;
}
```

**理解要点**：
- 什么是价格优先原则？
- 什么是时间优先原则？
- 如何计算成交数量？

## 4. 重点难点攻克

### 难点1：订单簿数据结构设计

**问题描述**：需要设计一个高效的数据结构来维护买卖订单

**解决方案**：使用 `std::map` + `std::list` 的组合

```cpp
// ⭐ 难点攻克 - 数据结构设计
// std::map 保证价格有序性
// std::list 支持高效的插入和删除
std::map<Price, std::list<Order>, std::greater<Price>> bid_book_;
```

**关键点**：
1. `std::map` 提供 O(log n) 的有序访问
2. `std::list` 提供 O(1) 的插入删除
3. 使用模板参数控制排序方式

**学习要点**：
- 理解 `std::map` 和 `std::unordered_map` 的区别
- 理解 `std::list` 和 `std::vector` 的区别
- 理解模板参数的作用

### 难点2：撮合算法实现

**问题描述**：需要实现价格优先、时间优先的撮合逻辑

**解决方案**：分步骤实现撮合逻辑

```cpp
// ⭐ 难点攻克 - 撮合算法
// 步骤1：获取最优对手价
Price best_price = (order.side == Side::Buy) ?
    order_book_.best_ask() : order_book_.best_bid();

// 步骤2：检查价格是否匹配
bool price_match = (order.side == Side::Buy) ?
    (best_price <= order.price) : (best_price >= order.price);

// 步骤3：计算成交数量
Quantity trade_qty = std::min(order.remaining_quantity(),
                              passive_order.remaining_quantity());

// 步骤4：执行成交
// 更新订单状态，生成成交记录
```

**关键点**：
1. 理解价格优先原则
2. 理解时间优先原则
3. 理解成交数量的计算

**学习要点**：
- 理解撮合的核心逻辑
- 理解订单状态的变化
- 理解成交记录的生成

### 难点3：低延迟优化

**问题描述**：高频交易对延迟极其敏感

**解决方案**：多种优化策略

```cpp
// ⭐ 难点攻克 - 低延迟优化
// 优化1：使用定点数避免浮点运算
using Price = int64_t;  // 而不是 double

// 优化2：使用纳秒级时间戳
using Timestamp = std::chrono::nanoseconds;

// 优化3：避免不必要的内存分配
// 使用 std::list 而不是 std::vector，避免重新分配

// 优化4：使用 unordered_map 实现 O(1) 查找
std::unordered_map<OrderId, OrderLocation> order_index_;
```

**关键点**：
1. 定点数 vs 浮点数
2. 时间精度的选择
3. 数据结构的选择

**学习要点**：
- 理解金融计算的精度要求
- 理解时间戳的作用
- 理解数据结构的性能特征

## 5. 调试技巧

### 常用调试方法

1. **打印调试**
   ```cpp
   std::cout << "Order ID: " << order.id
             << " Price: " << order.price
             << " Quantity: " << order.quantity << std::endl;
   ```

2. **使用 GDB**
   ```bash
   # 编译时添加调试信息
   cmake -DCMAKE_BUILD_TYPE=Debug ..
   make

   # 使用 GDB 调试
   gdb ./examples/basic_example
   ```

3. **使用 Valgrind 检测内存问题**
   ```bash
   valgrind --leak-check=full ./examples/basic_example
   ```

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 编译错误：找不到头文件 | CMakeLists.txt 配置错误 | 检查 include_directories |
| 运行时崩溃 | 空指针或越界访问 | 使用 GDB 调试 |
| 测试失败 | 逻辑错误 | 检查测试用例和实现 |
| 性能问题 | 数据结构选择不当 | 分析瓶颈，优化数据结构 |

## 6. 性能优化

### 已优化的部分

1. **定点数价格**
   - 使用 `int64_t` 而不是 `double`
   - 避免浮点数精度问题
   - 整数运算更快

2. **高效的数据结构**
   - 使用 `std::map` 保证有序性
   - 使用 `std::list` 支持高效插入删除
   - 使用 `std::unordered_map` 支持快速查找

3. **纳秒级时间戳**
   - 支持高精度排序
   - 避免时间戳冲突

### 可优化的方向

1. **内存池**
   - 预分配订单对象，减少动态分配
   - 使用对象池模式

2. **无锁数据结构**
   - 使用原子操作替代锁
   - 支持并发访问

3. **缓存友好**
   - 使用连续内存布局
   - 减少缓存未命中

4. **编译器优化**
   - 使用 `-O2` 或 `-O3` 优化级别
   - 使用 Profile-Guided Optimization (PGO)

## 7. 扩展指南

### 如何添加新的订单类型

1. **修改类型定义**
   ```cpp
   // include/types.h
   enum class OrderType : uint8_t {
       Market = 0,
       Limit = 1,
       StopLoss = 2,      // 新增：止损单
       Iceberg = 3        // 新增：冰山单
   };
   ```

2. **修改撮合逻辑**
   ```cpp
   // src/matching_engine.cpp
   std::vector<Trade> MatchingEngine::submit_order(Order order) {
       if (order.type == OrderType::StopLoss) {
           return try_match_stop_loss_order(order);
       }
       // ...
   }
   ```

3. **添加测试**
   ```cpp
   // tests/test_matching_engine.cpp
   TEST_F(MatchingEngineTest, StopLossOrder) {
       // 测试止损单逻辑
   }
   ```

### 如何优化性能

1. **替换数据结构**
   ```cpp
   // 使用跳表替代 std::map
   template<typename K, typename V>
   class SkipList {
       // ...
   };
   ```

2. **添加内存池**
   ```cpp
   template<typename T>
   class ObjectPool {
       // ...
   };
   ```

3. **使用无锁队列**
   ```cpp
   template<typename T>
   class LockFreeQueue {
       // ...
   };
   ```

### 代码规范

- 遵循 Google C++ Style Guide
- 使用有意义的变量名
- 添加详细的注释
- 保持函数简短（不超过50行）
- 每个函数都有文档注释
