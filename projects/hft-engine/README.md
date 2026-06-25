# 高频交易引擎

> 基于 C++17/20 的高频交易引擎，涵盖市场数据处理、订单管理、交易策略、风险管理、性能优化和回测系统

---

## 项目简介

高频交易引擎是一个完整的量化交易系统实现，专注于低延迟、高吞吐量的交易场景。项目从底层数据结构到上层策略逻辑，完整覆盖高频交易的核心技术栈。

### 核心特性

- **超低延迟**：纳秒级订单处理，内存预分配，无锁数据结构
- **完整交易链路**：行情接收 → 策略计算 → 风控检查 → 订单发送 → 成交回报
- **多策略支持**：做市策略、套利策略、趋势策略、统计套利
- **生产级风控**：持仓管理、止损止盈、保证金监控、异常检测
- **高性能回测**：历史数据回放、策略评估、风险分析

---

## 快速开始

```bash
# 编译项目
cd projects/hft-engine
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)

# 运行示例
./hft_engine
```

---

## 技术分类

```
高频交易引擎
├── 市场数据处理
│   ├── 行情接收 (Market Data Feed)
│   ├── 行情解析 (Tick Parser)
│   ├── 行情存储 (Tick Storage)
│   └── 行情回放 (Data Replay)
├── 订单管理系统 (OMS)
│   ├── 订单创建 (Order Creation)
│   ├── 订单发送 (Order Routing)
│   ├── 订单确认 (Order Acknowledgment)
│   ├── 订单取消 (Order Cancel)
│   └── 状态管理 (State Machine)
├── 交易策略
│   ├── 做市策略 (Market Making)
│   ├── 套利策略 (Arbitrage)
│   ├── 趋势策略 (Trend Following)
│   └── 统计套利 (Statistical Arbitrage)
├── 风险管理
│   ├── 持仓管理 (Position Management)
│   ├── 风险控制 (Risk Control)
│   ├── 止损止盈 (Stop Loss/Take Profit)
│   └── 保证金管理 (Margin Management)
├── 性能优化
│   ├── 低延迟优化 (Low Latency)
│   ├── 无锁数据结构 (Lock-free)
│   ├── 内存优化 (Memory Optimization)
│   └── 网络优化 (Network Optimization)
└── 回测系统
    ├── 历史数据回放 (Data Replay)
    ├── 策略回测 (Strategy Backtest)
    ├── 性能分析 (Performance Analysis)
    └── 风险分析 (Risk Analysis)
```

---

## 学习路径

```
基础概念 → 数据结构 → 市场数据 → 订单管理 → 交易策略 → 风险管理 → 性能优化
    ↓          ↓          ↓          ↓          ↓          ↓          ↓
  金融基础   无锁队列   Tick处理   OMS设计   策略开发   风控系统   延迟优化
  交易规则   环形缓冲   行情解析   状态机    信号生成   仓位管理   内存池
```

### 推荐学习顺序

1. **市场数据处理** (01-04) - 理解行情数据结构和处理流程
2. **订单管理系统** (05-09) - 掌握订单生命周期管理
3. **交易策略** (10-13) - 学习经典策略实现
4. **风险管理** (14-17) - 理解风控体系设计
5. **性能优化** (18-21) - 掌握低延迟优化技巧
6. **回测系统** (22-25) - 学习策略评估方法

---

## 编译运行

### 环境要求

- C++17/20 编译器 (GCC 10+, Clang 12+, MSVC 2019+)
- CMake 3.16+
- Linux/macOS/Windows

### 编译选项

```bash
# Debug 模式（包含调试信息）
cmake .. -DCMAKE_BUILD_TYPE=Debug

# Release 模式（优化性能）
cmake .. -DCMAKE_BUILD_TYPE=Release

# 启用 AddressSanitizer（内存检测）
cmake .. -DENABLE_ASAN=ON
```

### 运行测试

```bash
# 运行所有测试
ctest --output-on-failure

# 运行特定测试
./test_market_data
./test_order_manager
```

---

## 文件结构

```
hft-engine/
├── CMakeLists.txt           # 构建配置
├── README.md                # 项目说明
├── 01_RESEARCH.md           # 市场调研
├── 02_REQUIREMENTS.md       # 需求分析
├── 03_DESIGN.md             # 技术设计
├── 04_PRODUCT.md            # 产品思考
├── 05_DEVELOPMENT.md        # 开发手册
└── src/
    ├── core/                # 核心数据结构
    │   ├── ring_buffer.h    # 无锁环形缓冲区
    │   ├── memory_pool.h    # 内存池
    │   └── timestamp.h      # 高精度时间戳
    ├── market_data/         # 市场数据处理
    │   ├── tick.h           # Tick数据结构
    │   ├── feed_handler.h   # 行情接收器
    │   └── tick_store.h     # 行情存储
    ├── order/               # 订单管理
    │   ├── order.h          # 订单数据结构
    │   ├── order_book.h     # 订单簿
    │   └── order_manager.h  # 订单管理器
    ├── strategy/            # 交易策略
    │   ├── strategy.h       # 策略基类
    │   ├── market_maker.h   # 做市策略
    │   └── arbitrage.h      # 套利策略
    ├── risk/                # 风险管理
    │   ├── position.h       # 持仓管理
    │   └── risk_manager.h   # 风险管理器
    └── main.cpp             # 主程序入口
```

---

## 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| 语言 | C++17/20 | 主要开发语言 |
| 构建 | CMake | 跨平台构建系统 |
| 数据结构 | 无锁队列 | 高并发数据交换 |
| 内存 | 内存池 | 减少分配开销 |
| 时间 | 高精度时钟 | 纳秒级时间戳 |
| 网络 | TCP/UDP | 行情和订单传输 |

---

## 许可证

MIT License
