# 技术设计

## 文件组织

### 目录结构

```
hft-engine/
├── CMakeLists.txt
├── README.md
├── 01_RESEARCH.md
├── 02_REQUIREMENTS.md
├── 03_DESIGN.md
├── 04_PRODUCT.md
├── 05_DEVELOPMENT.md
└── src/
    ├── core/                    # 核心基础设施
    │   ├── ring_buffer.h        # 无锁环形缓冲区
    │   ├── memory_pool.h        # 内存池
    │   ├── timestamp.h          # 高精度时间戳
    │   ├── spinlock.h           # 自旋锁
    │   └── logger.h             # 日志系统
    ├── market_data/             # 市场数据处理
    │   ├── tick.h               # Tick 数据结构
    │   ├── order_book.h         # 订单簿
    │   ├── feed_handler.h       # 行情接收器
    │   ├── tick_parser.h        # 行情解析器
    │   ├── tick_store.h         # 行情存储
    │   └── data_replay.h        # 行情回放
    ├── order/                   # 订单管理
    │   ├── order.h              # 订单数据结构
    │   ├── order_manager.h      # 订单管理器
    │   ├── order_router.h       # 订单路由
    │   └── execution_report.h   # 成交回报
    ├── strategy/                # 交易策略
    │   ├── strategy.h           # 策略基类
    │   ├── market_maker.h       # 做市策略
    │   ├── arbitrage.h          # 套利策略
    │   ├── trend_follower.h     # 趋势策略
    │   └── stat_arb.h           # 统计套利
    ├── risk/                    # 风险管理
    │   ├── position.h           # 持仓管理
    │   ├── risk_manager.h       # 风险管理器
    │   ├── margin.h             # 保证金管理
    │   └── stop_loss.h          # 止损止盈
    ├── backtest/                # 回测系统
    │   ├── backtester.h         # 回测引擎
    │   ├── performance.h        # 性能分析
    │   └── risk_analyzer.h      # 风险分析
    └── main.cpp                 # 主程序
```

---

## 核心设计

### 1. 无锁环形缓冲区 (Ring Buffer)

**设计目标**：单生产者单消费者 (SPSC) 无锁队列

**数据结构**：
```cpp
template<typename T, size_t Size>
class RingBuffer {
    alignas(64) std::atomic<size_t> read_pos_{0};
    alignas(64) std::atomic<size_t> write_pos_{0};
    T buffer_[Size];
};
```

**关键特性**：
- 缓存行对齐，避免伪共享
- 无锁设计，高并发性能
- 固定大小，内存可预测
- 单生产者单消费者 (SPSC)

**应用场景**：
- 行情数据传递
- 策略信号传递
- 日志缓冲

---

### 2. 内存池 (Memory Pool)

**设计目标**：减少内存分配开销，避免内存碎片

**数据结构**：
```cpp
class MemoryPool {
    struct Block {
        Block* next;
    };
    Block* free_list_;
    std::vector<void*> chunks_;
    size_t block_size_;
    size_t chunk_size_;
};
```

**关键特性**：
- 预分配内存块
- O(1) 分配和释放
- 内存对齐
- 线程安全（可选）

**应用场景**：
- 订单对象分配
- Tick 数据分配
- 临时对象分配

---

### 3. 高精度时间戳 (Timestamp)

**设计目标**：纳秒级时间戳，低开销获取

**实现方式**：
```cpp
class Timestamp {
    int64_t nanoseconds_;

    static Timestamp now() {
        auto now = std::chrono::high_resolution_clock::now();
        return Timestamp(
            std::chrono::duration_cast<std::chrono::nanoseconds>(
                now.time_since_epoch()
            ).count()
        );
    }
};
```

**关键特性**：
- 纳秒精度
- 低开销（< 20ns）
- 单调递增
- 跨平台支持

**应用场景**：
- 行情时间戳
- 订单时间戳
- 延迟测量
- 性能分析

---

### 4. 订单簿 (Order Book)

**设计目标**：高效的价格档位管理

**数据结构**：
```cpp
class OrderBook {
    struct PriceLevel {
        double price;
        int64_t quantity;
        int32_t order_count;
    };

    // 使用跳表或红黑树维护价格档位
    std::map<double, PriceLevel, std::greater<double>> bids_;  // 买盘
    std::map<double, PriceLevel> asks_;  // 卖盘
};
```

**关键特性**：
- O(log n) 插入删除
- 快速最优价查询
- 深度查询
- 增量更新

**应用场景**：
- 行情展示
- 策略计算
- 风险监控

---

### 5. 订单状态机 (Order State Machine)

**设计目标**：清晰的订单生命周期管理

**状态转换**：
```
                    ┌─────────────┐
                    │   Created   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
              ┌─────│    Sent     │─────┐
              │     └──────┬──────┘     │
              │            │            │
       ┌──────▼──────┐     │     ┌──────▼──────┐
       │  Rejected   │     │     │   Timeout   │
       └─────────────┘     │     └─────────────┘
                    ┌──────▼──────┐
              ┌─────│ Acknowledged│─────┐
              │     └──────┬──────┘     │
              │            │            │
       ┌──────▼──────┐     │     ┌──────▼──────┐
       │  Cancelled  │     │     │   Expired   │
       └─────────────┘     │     └─────────────┘
                    ┌──────▼──────┐
              ┌─────│PartiallyFill│─────┐
              │     └──────┬──────┘     │
              │            │            │
       ┌──────▼──────┐     │            │
       │  Cancelled  │     │            │
       └─────────────┘     │            │
                    ┌──────▼──────┐     │
                    │   Filled    │     │
                    └─────────────┘     │
```

**关键特性**：
- 明确的状态转换
- 线程安全
- 状态持久化
- 事件驱动

---

### 6. 策略框架 (Strategy Framework)

**设计目标**：可扩展的策略基类

**接口设计**：
```cpp
class Strategy {
public:
    virtual ~Strategy() = default;

    // 生命周期
    virtual void on_init() = 0;
    virtual void on_start() = 0;
    virtual void on_stop() = 0;

    // 数据回调
    virtual void on_tick(const Tick& tick) = 0;
    virtual void on_bar(const Bar& bar) = 0;
    virtual void on_order(const Order& order) = 0;
    virtual void on_trade(const Trade& trade) = 0;

    // 配置
    virtual void set_params(const StrategyParams& params) = 0;
    virtual StrategyParams get_params() const = 0;
};
```

**关键特性**：
- 虚函数接口
- 事件驱动
- 参数可配置
- 状态可查询

---

### 7. 风险管理器 (Risk Manager)

**设计目标**：多层风险控制

**架构设计**：
```
订单请求
    │
    ▼
┌─────────────────┐
│   预检查层      │  - 订单参数验证
│  (Pre-Check)    │  - 价格合理性检查
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│   仓位检查层    │  - 持仓限制检查
│ (Position Check)│  - 集中度检查
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│   保证金检查层  │  - 保证金充足性
│ (Margin Check)  │  - 风险敞口检查
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│   频率检查层    │  - 下单频率限制
│ (Rate Check)    │  - 撤单频率限制
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│   通过          │  - 订单可以发送
└─────────────────┘
```

**关键特性**：
- 多层检查
- 实时监控
- 自动熔断
- 告警通知

---

### 8. 回测引擎 (Backtester)

**设计目标**：事件驱动的回测框架

**架构设计**：
```
历史数据
    │
    ▼
┌─────────────────┐
│   数据回放器    │  - 按时间顺序回放
│  (Data Player)  │  - 速度控制
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│   策略引擎      │  - 策略计算
│(Strategy Engine)│  - 信号生成
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│   订单模拟器    │  - 成交模拟
│(Order Simulator)│  - 滑点模拟
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│   性能分析器    │  - 收益计算
│(Performance)    │  - 风险计算
└─────────────────┘
```

**关键特性**：
- 事件驱动
- 真实模拟
- 性能分析
- 风险分析

---

## 示例设计

### 示例 1：做市策略实现

**策略逻辑**：
1. 计算中间价 (mid-price)
2. 根据库存调整报价
3. 根据波动率调整价差
4. 提交买卖报价
5. 监控成交，调整库存

**代码示例**：
```cpp
class MarketMaker : public Strategy {
    void on_tick(const Tick& tick) override {
        // 1. 更新中间价
        double mid_price = (tick.bid_price + tick.ask_price) / 2.0;

        // 2. 计算库存偏移
        double inventory_skew = inventory_ * skew_factor_;

        // 3. 计算波动率调整
        double volatility_adj = calculate_volatility() * vol_factor_;

        // 4. 生成报价
        double bid_price = mid_price - spread_/2.0 - inventory_skew - volatility_adj;
        double ask_price = mid_price + spread_/2.0 - inventory_skew + volatility_adj;

        // 5. 提交报价
        submit_quotes(bid_price, ask_price, quote_size_);
    }
};
```

---

### 示例 2：套利策略实现

**策略逻辑**：
1. 监控两个相关资产的价格
2. 计算价差
3. 当价差超过阈值时开仓
4. 当价差回归时平仓

**代码示例**：
```cpp
class ArbitrageStrategy : public Strategy {
    void on_tick(const Tick& tick) override {
        // 1. 更新价格
        prices_[tick.symbol] = tick.last_price;

        // 2. 计算价差
        double spread = prices_["AAPL"] - prices_["MSFT"] * hedge_ratio_;

        // 3. 生成信号
        if (spread > entry_threshold_) {
            // 价差过大，做空价差
            sell("AAPL", quantity_);
            buy("MSFT", quantity_ * hedge_ratio_);
        } else if (spread < -entry_threshold_) {
            // 价差过小，做多价差
            buy("AAPL", quantity_);
            sell("MSFT", quantity_ * hedge_ratio_);
        }

        // 4. 平仓检查
        if (has_position() && std::abs(spread) < exit_threshold_) {
            close_position();
        }
    }
};
```

---

### 示例 3：订单簿更新

**更新逻辑**：
1. 接收增量更新
2. 更新价格档位
3. 维护最优价
4. 通知策略

**代码示例**：
```cpp
class OrderBook {
    void update(const OrderBookUpdate& update) {
        // 1. 获取价格档位
        auto& levels = (update.side == Side::BUY) ? bids_ : asks_;
        auto it = levels.find(update.price);

        // 2. 更新档位
        if (update.quantity == 0) {
            // 删除档位
            if (it != levels.end()) {
                levels.erase(it);
            }
        } else {
            // 更新档位
            levels[update.price] = {
                update.price,
                update.quantity,
                update.order_count
            };
        }

        // 3. 更新最优价
        update_best_price();

        // 4. 通知策略
        notify_strategies();
    }
};
```

---

### 示例 4：风险管理检查

**检查逻辑**：
1. 检查订单参数
2. 检查持仓限制
3. 检查保证金
4. 检查频率限制

**代码示例**：
```cpp
class RiskManager {
    RiskCheckResult check_order(const Order& order) {
        // 1. 参数检查
        if (order.price <= 0 || order.quantity <= 0) {
            return RiskCheckResult::INVALID_PARAMS;
        }

        // 2. 持仓检查
        auto position = get_position(order.symbol);
        if (std::abs(position.quantity + order.quantity) > max_position_) {
            return RiskCheckResult::POSITION_LIMIT;
        }

        // 3. 保证金检查
        double required_margin = calculate_margin(order);
        if (available_margin_ < required_margin) {
            return RiskCheckResult::INSUFFICIENT_MARGIN;
        }

        // 4. 频率检查
        if (order_rate_ > max_order_rate_) {
            return RiskCheckResult::RATE_LIMIT;
        }

        return RiskCheckResult::PASS;
    }
};
```

---

## 性能优化设计

### 1. 缓存行对齐

```cpp
struct alignas(64) CacheLineAligned {
    std::atomic<int64_t> value;
    char padding[64 - sizeof(std::atomic<int64_t>)];
};
```

**目的**：避免伪共享 (False Sharing)

---

### 2. 内存预分配

```cpp
class OrderManager {
    std::vector<Order> order_pool_;
    size_t pool_index_;

    Order* allocate_order() {
        return &order_pool_[pool_index_++ % order_pool_.size()];
    }
};
```

**目的**：避免运行时内存分配

---

### 3. 分支预测提示

```cpp
#define LIKELY(x)   __builtin_expect(!!(x), 1)
#define UNLIKELY(x) __builtin_expect(!!(x), 0)

if (LIKELY(success)) {
    // 正常路径
} else {
    // 错误路径
}
```

**目的**：提高分支预测准确率

---

### 4. 数据预取

```cpp
void process_ticks(const Tick* ticks, size_t count) {
    for (size_t i = 0; i < count; ++i) {
        // 预取下一个数据
        if (i + 1 < count) {
            __builtin_prefetch(&ticks[i + 1], 0, 3);
        }
        process_tick(ticks[i]);
    }
}
```

**目的**：减少缓存未命中

---

## 线程模型

### 单线程模型

```
Main Thread
    │
    ├── 接收行情
    ├── 策略计算
    ├── 风控检查
    ├── 订单发送
    └── 状态更新
```

**优点**：简单、无锁竞争
**缺点**：无法利用多核

---

### 多线程模型

```
行情线程 ──→ [Ring Buffer] ──→ 策略线程 ──→ [Ring Buffer] ──→ 下单线程
    │                              │                              │
    └──────────────────────────────┴──────────────────────────────┘
                                   │
                              风控线程
```

**优点**：并行处理、低延迟
**缺点**：复杂、需要同步

---

### Actor 模型

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  行情 Actor  │────→│  策略 Actor  │────→│  下单 Actor  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                    ┌─────────────┐
                    │  风控 Actor  │
                    └─────────────┘
```

**优点**：解耦、可扩展
**缺点**：消息传递开销

---

## 错误处理设计

### 错误分类

| 错误类型 | 说明 | 处理方式 |
|----------|------|----------|
| 网络错误 | 连接断开、超时 | 重连、告警 |
| 数据错误 | 数据损坏、格式错误 | 丢弃、日志 |
| 订单错误 | 拒绝、超时 | 重试、告警 |
| 系统错误 | 内存不足、线程异常 | 降级、重启 |

### 错误处理策略

1. **重试机制**：网络错误、订单超时
2. **降级机制**：系统过载、资源不足
3. **熔断机制**：连续失败、风险超限
4. **告警机制**：异常状态、人工介入

---

## 监控设计

### 监控指标

| 类别 | 指标 | 阈值 |
|------|------|------|
| 性能 | 订单延迟 | < 10μs |
| 性能 | 行情延迟 | < 1μs |
| 风险 | 持仓规模 | < 上限 |
| 风险 | 日内亏损 | < 上限 |
| 系统 | CPU 使用率 | < 80% |
| 系统 | 内存使用率 | < 80% |
| 系统 | 网络延迟 | < 1ms |

### 告警级别

| 级别 | 说明 | 响应时间 |
|------|------|----------|
| P0 | 系统故障 | 立即 |
| P1 | 风险超限 | 5 分钟 |
| P2 | 性能下降 | 30 分钟 |
| P3 | 信息通知 | 24 小时 |
