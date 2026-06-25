# 开发手册

## 编译说明

### 环境要求

#### 操作系统
- Linux (推荐 Ubuntu 20.04+, CentOS 8+)
- macOS 11+
- Windows 10+ (MSVC 2019+)

#### 编译器
- GCC 10+ (推荐 GCC 12)
- Clang 12+ (推荐 Clang 15)
- MSVC 2019+ (Windows)

#### 构建工具
- CMake 3.16+
- Make (Linux/macOS)
- Ninja (可选)

#### 依赖库
- 无外部依赖（纯 C++ 实现）

---

### 编译步骤

#### 1. 克隆项目

```bash
cd /home/siok/project_copyninja/projects/hft-engine
```

#### 2. 创建构建目录

```bash
mkdir -p build
cd build
```

#### 3. 配置 CMake

```bash
# Release 模式（推荐，优化性能）
cmake .. -DCMAKE_BUILD_TYPE=Release

# Debug 模式（调试用）
cmake .. -DCMAKE_BUILD_TYPE=Debug

# 启用 AddressSanitizer（内存检测）
cmake .. -DCMAKE_BUILD_TYPE=Debug -DENABLE_ASAN=ON
```

#### 4. 编译

```bash
# 使用所有 CPU 核心
make -j$(nproc)

# 或指定核心数
make -j8
```

#### 5. 运行

```bash
# 运行主程序
./hft_engine

# 运行测试
ctest --output-on-failure
```

---

### 编译选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `CMAKE_BUILD_TYPE` | 构建类型 | Release |
| `ENABLE_ASAN` | 启用 AddressSanitizer | OFF |
| `ENABLE_TSAN` | 启用 ThreadSanitizer | OFF |
| `ENABLE_UBSAN` | 启用 UndefinedBehaviorSanitizer | OFF |
| `BUILD_TESTS` | 构建测试 | ON |
| `BUILD_EXAMPLES` | 构建示例 | ON |

---

### CMake 配置示例

```bash
# 完整配置示例
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_STANDARD=20 \
    -DBUILD_TESTS=ON \
    -DBUILD_EXAMPLES=ON
```

---

## 运行方式

### 1. 运行主程序

```bash
cd build
./hft_engine
```

**输出示例**：
```
=== High Frequency Trading Engine ===
Initializing system...
Loading configuration...
Starting market data feed...
Starting order management system...
Starting risk manager...
System ready.

[Market Data] AAPL: 150.25 x 150.26
[Strategy] Market Maker: Quote updated
[Order] New order: BUY 100 AAPL @ 150.25
[Order] Filled: BUY 100 AAPL @ 150.25
[Risk] Position: AAPL +100, PnL: +25.00
```

---

### 2. 运行测试

```bash
cd build
ctest --output-on-failure
```

**输出示例**：
```
Test project /home/siok/project_copyninja/projects/hft-engine/build
    Start 1: test_ring_buffer
1/5 Test #1: test_ring_buffer ................   Passed    0.01 sec
    Start 2: test_memory_pool
2/5 Test #2: test_memory_pool ................   Passed    0.01 sec
    Start 3: test_order_book
3/5 Test #3: test_order_book .................   Passed    0.02 sec
    Start 4: test_order_manager
4/5 Test #4: test_order_manager ..............   Passed    0.01 sec
    Start 5: test_risk_manager
5/5 Test #5: test_risk_manager ...............   Passed    0.01 sec

100% tests passed, 0 tests failed out of 5
```

---

### 3. 运行回测

```bash
cd build
./backtest --data ../data/historical.csv --strategy market_maker
```

**输出示例**：
```
=== Backtest System ===
Loading historical data...
Loaded 1,000,000 ticks
Running backtest...
Progress: 100%

=== Performance Report ===
Total Return: 15.23%
Annual Return: 12.50%
Sharpe Ratio: 2.15
Max Drawdown: -5.23%
Win Rate: 58.3%
Profit Factor: 1.85
```

---

### 4. 运行性能测试

```bash
cd build
./benchmark
```

**输出示例**：
```
=== Performance Benchmark ===

Ring Buffer:
  Write: 15 ns/op
  Read: 12 ns/op
  Throughput: 65M ops/sec

Memory Pool:
  Allocate: 8 ns/op
  Deallocate: 5 ns/op
  Throughput: 120M ops/sec

Order Book:
  Insert: 45 ns/op
  Delete: 38 ns/op
  Query: 15 ns/op

Order Manager:
  Create Order: 85 ns/op
  Process Fill: 65 ns/op
```

---

## 开发指南

### 1. 添加新策略

#### 步骤 1：创建策略头文件

```cpp
// src/strategy/my_strategy.h
#pragma once

#include "strategy.h"

class MyStrategy : public Strategy {
public:
    MyStrategy();
    ~MyStrategy() override;

    // 生命周期
    void on_init() override;
    void on_start() override;
    void on_stop() override;

    // 数据回调
    void on_tick(const Tick& tick) override;
    void on_bar(const Bar& bar) override;
    void on_order(const Order& order) override;
    void on_trade(const Trade& trade) override;

    // 配置
    void set_params(const StrategyParams& params) override;
    StrategyParams get_params() const override;

private:
    // 策略参数
    double param1_;
    double param2_;

    // 策略状态
    bool is_initialized_;
};
```

#### 步骤 2：实现策略逻辑

```cpp
// src/strategy/my_strategy.cpp
#include "my_strategy.h"

MyStrategy::MyStrategy()
    : param1_(0.0), param2_(0.0), is_initialized_(false) {}

MyStrategy::~MyStrategy() = default;

void MyStrategy::on_init() {
    // 初始化策略
    is_initialized_ = true;
}

void MyStrategy::on_start() {
    // 启动策略
}

void MyStrategy::on_stop() {
    // 停止策略
}

void MyStrategy::on_tick(const Tick& tick) {
    // 处理 Tick 数据
    // 实现交易逻辑
}

void MyStrategy::on_bar(const Bar& bar) {
    // 处理 K 线数据
}

void MyStrategy::on_order(const Order& order) {
    // 处理订单状态更新
}

void MyStrategy::on_trade(const Trade& trade) {
    // 处理成交回报
}

void MyStrategy::set_params(const StrategyParams& params) {
    // 设置策略参数
    param1_ = params.get<double>("param1");
    param2_ = params.get<double>("param2");
}

StrategyParams MyStrategy::get_params() const {
    // 获取策略参数
    StrategyParams params;
    params.set("param1", param1_);
    params.set("param2", param2_);
    return params;
}
```

#### 步骤 3：注册策略

```cpp
// src/main.cpp
#include "strategy/my_strategy.h"

int main() {
    // 创建策略实例
    auto strategy = std::make_unique<MyStrategy>();

    // 配置参数
    StrategyParams params;
    params.set("param1", 1.0);
    params.set("param2", 2.0);
    strategy->set_params(params);

    // 注册到引擎
    engine.register_strategy(std::move(strategy));

    return 0;
}
```

---

### 2. 添加新订单类型

#### 步骤 1：定义订单类型

```cpp
// src/order/order.h
enum class OrderType {
    MARKET,         // 市价单
    LIMIT,          // 限价单
    STOP,           // 止损单
    STOP_LIMIT,     // 止损限价单
    ICEBERG,        // 冰山单
    IOC,            // 立即成交或取消
    FOK,            // 全部成交或取消
    MY_NEW_TYPE     // 新订单类型
};
```

#### 步骤 2：实现订单处理

```cpp
// src/order/order_manager.cpp
void OrderManager::process_order(const Order& order) {
    switch (order.type) {
        case OrderType::MARKET:
            process_market_order(order);
            break;
        case OrderType::LIMIT:
            process_limit_order(order);
            break;
        case OrderType::MY_NEW_TYPE:
            process_my_new_type_order(order);
            break;
        // ...
    }
}
```

---

### 3. 添加新风控规则

#### 步骤 1：定义风控规则

```cpp
// src/risk/my_risk_rule.h
#pragma once

#include "risk_rule.h"

class MyRiskRule : public RiskRule {
public:
    MyRiskRule();
    ~MyRiskRule() override;

    RiskCheckResult check(const Order& order,
                          const Position& position,
                          const RiskMetrics& metrics) override;

private:
    double threshold_;
};
```

#### 步骤 2：实现风控逻辑

```cpp
// src/risk/my_risk_rule.cpp
#include "my_risk_rule.h"

MyRiskRule::MyRiskRule() : threshold_(1000000.0) {}

MyRiskRule::~MyRiskRule() = default;

RiskCheckResult MyRiskRule::check(const Order& order,
                                   const Position& position,
                                   const RiskMetrics& metrics) {
    // 实现风控检查逻辑
    double order_value = order.price * order.quantity;

    if (order_value > threshold_) {
        return RiskCheckResult::REJECTED;
    }

    return RiskCheckResult::PASS;
}
```

#### 步骤 3：注册风控规则

```cpp
// src/main.cpp
#include "risk/my_risk_rule.h"

int main() {
    // 创建风控管理器
    RiskManager risk_manager;

    // 注册风控规则
    risk_manager.add_rule(std::make_unique<MyRiskRule>());

    return 0;
}
```

---

## 调试指南

### 1. 使用 GDB 调试

```bash
# 编译 Debug 版本
cmake .. -DCMAKE_BUILD_TYPE=Debug
make -j$(nproc)

# 启动 GDB
gdb ./hft_engine

# 常用命令
(gdb) break main          # 设置断点
(gdb) run                 # 运行程序
(gdb) next                # 单步执行
(gdb) step                # 进入函数
(gdb) print variable      # 打印变量
(gdb) backtrace           # 查看调用栈
(gdb) continue            # 继续执行
```

---

### 2. 使用 Valgrind 检测内存问题

```bash
# 检测内存泄漏
valgrind --leak-check=full ./hft_engine

# 检测未初始化内存
valgrind --track-origins=yes ./hft_engine

# 生成性能分析报告
valgrind --tool=callgrind ./hft_engine
callgrind_annotate callgrind.out.*
```

---

### 3. 使用 AddressSanitizer

```bash
# 编译启用 ASan
cmake .. -DCMAKE_BUILD_TYPE=Debug -DENABLE_ASAN=ON
make -j$(nproc)

# 运行程序
./hft_engine
```

**ASan 可检测的问题**：
- 内存泄漏
- 越界访问
- 使用已释放内存
- 双重释放

---

### 4. 使用 ThreadSanitizer

```bash
# 编译启用 TSan
cmake .. -DCMAKE_BUILD_TYPE=Debug -DENABLE_TSAN=ON
make -j$(nproc)

# 运行程序
./hft_engine
```

**TSan 可检测的问题**：
- 数据竞争
- 死锁
- 线程安全问题

---

## 性能分析

### 1. 使用 perf 分析

```bash
# 采集性能数据
perf record -g ./hft_engine

# 查看性能报告
perf report

# 查看火焰图
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg
```

---

### 2. 使用 Google Benchmark

```cpp
// benchmark/benchmark_order_book.cpp
#include <benchmark/benchmark.h>
#include "order_book.h"

static void BM_OrderBook_Insert(benchmark::State& state) {
    OrderBook book;
    for (auto _ : state) {
        book.insert(Order{100.0, 100, Side::BUY});
    }
}
BENCHMARK(BM_OrderBook_Insert);

BENCHMARK_MAIN();
```

---

### 3. 自定义性能计数器

```cpp
#include "core/timestamp.h"

void measure_latency() {
    auto start = Timestamp::now();

    // 执行操作
    do_something();

    auto end = Timestamp::now();
    auto latency = end - start;

    std::cout << "Latency: " << latency.nanoseconds() << " ns" << std::endl;
}
```

---

## 常见问题

### Q1: 编译失败，找不到 C++20 支持

**解决方案**：
```bash
# 检查编译器版本
g++ --version

# 如果版本过低，安装新版本
sudo apt install g++-12

# 指定编译器
cmake .. -DCMAKE_CXX_COMPILER=g++-12
```

---

### Q2: 运行时出现段错误

**解决方案**：
```bash
# 使用 GDB 定位问题
gdb ./hft_engine
(gdb) run
(gdb) backtrace

# 使用 ASan 检测
cmake .. -DENABLE_ASAN=ON
make clean && make
./hft_engine
```

---

### Q3: 性能不如预期

**排查步骤**：
1. 使用 perf 找出热点函数
2. 检查是否有不必要的内存分配
3. 检查是否有锁竞争
4. 检查缓存命中率
5. 检查分支预测准确率

---

### Q4: 多线程程序出现数据竞争

**解决方案**：
```bash
# 使用 TSan 检测
cmake .. -DENABLE_TSAN=ON
make clean && make
./hft_engine

# 修复建议：
# 1. 使用原子操作
# 2. 使用无锁数据结构
# 3. 使用互斥锁保护共享数据
```

---

## 贡献指南

### 代码规范

1. **命名规范**：
   - 类名：PascalCase
   - 函数名：snake_case
   - 变量名：snake_case
   - 常量：UPPER_SNAKE_CASE

2. **注释规范**：
   - 文件头注释
   - 类注释
   - 函数注释
   - 复杂逻辑注释

3. **格式规范**：
   - 使用 4 空格缩进
   - 行宽限制 100 字符
   - 使用 clang-format 格式化

### 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

### 测试要求

- 新功能必须包含单元测试
- 测试覆盖率 > 80%
- 所有测试必须通过
