# 技术设计文档

## 1. 架构概述

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Application)                    │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              OrderManager (订单管理器)                │  │
│  │  - 提供高层 API                                      │  │
│  │  - 管理订单生命周期                                   │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                    撮合层 (Matching)                       │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              MatchingEngine (撮合引擎)                │  │
│  │  - 接收订单                                          │  │
│  │  - 执行撮合逻辑                                      │  │
│  │  - 生成成交记录                                      │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                    数据层 (Data)                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              OrderBook (订单簿)                       │  │
│  │  - 维护买卖订单                                      │  │
│  │  - 提供价格查询                                      │  │
│  │  - 管理订单索引                                      │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 模块划分

| 模块 | 职责 | 文件位置 |
|------|------|----------|
| OrderBook | 维护订单簿数据结构 | `include/order_book.h`, `src/order_book.cpp` |
| MatchingEngine | 执行撮合逻辑 | `include/matching_engine.h`, `src/matching_engine.cpp` |
| OrderManager | 提供高层API | `include/order_manager.h`, `src/order_manager.cpp` |
| Types | 基础类型定义 | `include/types.h` |

## 2. 核心流程

### 主流程

```
订单提交
    │
    ▼
验证订单
    │
    ├── 无效 ──→ 返回拒绝
    │
    ▼
分配订单ID
    │
    ▼
判断订单类型
    │
    ├── 限价单 ──→ try_match_limit_order()
    │                   │
    │                   ▼
    │              检查对手方最优价
    │                   │
    │                   ├── 价格匹配 ──→ 执行撮合
    │                   │
    │                   └── 价格不匹配 ──→ 添加到订单簿
    │
    └── 市价单 ──→ try_match_market_order()
                        │
                        ▼
                   直接与最优价撮合
                        │
                        ├── 有对手方 ──→ 执行撮合
                        │
                        └── 无对手方 ──→ 取消订单
```

### 撮合子流程

```
获取最优对手价
    │
    ▼
计算成交数量 = min(主动方剩余, 被动方剩余)
    │
    ▼
执行成交
    │
    ├── 更新被动方订单状态
    │
    ├── 更新主动方订单状态
    │
    ├── 生成成交记录
    │
    └── 触发回调
```

## 3. 数据设计

### 核心数据结构

#### Order（订单）

```cpp
struct Order {
    OrderId id;              // 订单ID
    Side side;               // 买卖方向
    OrderType type;          // 订单类型
    Price price;             // 价格
    Quantity quantity;        // 总数量
    Quantity filled_quantity; // 已成交数量
    OrderStatus status;      // 订单状态
    Timestamp timestamp;     // 创建时间
};
```

**关键点**：
- 使用 `int64_t` 表示价格，避免浮点数精度问题
- 使用纳秒级时间戳，支持高精度排序

#### OrderBook（订单簿）

```cpp
class OrderBook {
    // 买单簿：价格降序排列
    std::map<Price, std::list<Order>, std::greater<Price>> bid_book_;

    // 卖单簿：价格升序排列
    std::map<Price, std::list<Order>, std::less<Price>> ask_book_;

    // 订单索引：快速查找
    std::unordered_map<OrderId, OrderLocation> order_index_;
};
```

**关键点**：
- 使用 `std::map` 保证价格有序性
- 使用 `std::list` 支持高效的插入和删除
- 使用 `std::unordered_map` 提供 O(1) 的订单查找

#### Trade（成交记录）

```cpp
struct Trade {
    OrderId buy_order_id;    // 买单ID
    OrderId sell_order_id;   // 卖单ID
    Price price;             // 成交价格
    Quantity quantity;        // 成交数量
    Timestamp timestamp;     // 成交时间
};
```

## 4. 接口设计

### OrderBook API

```cpp
class OrderBook {
public:
    // 订单操作
    bool add_order(const Order& order);
    bool cancel_order(OrderId order_id);
    bool amend_order(OrderId order_id, Quantity new_quantity);

    // 查询操作
    Price best_bid() const;
    Price best_ask() const;
    Price spread() const;
    std::vector<PriceLevel> bid_depth(size_t levels = 10) const;
    std::vector<PriceLevel> ask_depth(size_t levels = 10) const;
    const Order* find_order(OrderId order_id) const;

    // 快照
    Snapshot get_snapshot(size_t levels = 10) const;
};
```

### MatchingEngine API

```cpp
class MatchingEngine {
public:
    // 提交订单
    std::vector<Trade> submit_order(Order order);

    // 取消订单
    bool cancel_order(OrderId order_id);

    // 设置回调
    void set_trade_callback(TradeCallback callback);
    void set_order_callback(OrderCallback callback);

    // 获取状态
    const OrderBook& order_book() const;
    const std::vector<Trade>& trade_history() const;
};
```

## 5. 技术选型

### 选型决策

| 决策点 | 选项A | 选项B | 选项C | 最终选择 |
|--------|-------|-------|-------|----------|
| 价格存储 | float | double | int64_t | int64_t |
| 价格排序容器 | vector | map | unordered_map | map |
| 订单存储容器 | vector | list | deque | list |
| 订单查找 | map | unordered_map | 线性搜索 | unordered_map |
| 时间精度 | 秒 | 毫秒 | 纳秒 | 纳秒 |

### 选择理由

**决策1：使用 int64_t 存储价格**

**原因**：
1. 浮点数有精度误差，不适合金融计算
2. 定点数可以精确表示价格
3. 整数运算比浮点数更快

**示例**：
```cpp
// 使用定点数表示价格
// 100.50 表示为 10050（保留2位小数）
Price price = 10050;
```

**决策2：使用 std::map 存储价格层级**

**原因**：
1. 撮合需要频繁访问最优价格
2. `std::map` 提供 O(log n) 的有序访问
3. 买单和卖单需要不同的排序方式

**决策3：使用 std::list 存储订单**

**原因**：
1. 需要频繁的插入和删除操作
2. `std::list` 提供 O(1) 的插入删除
3. 不需要随机访问

## 6. 设计决策与权衡

### 决策1：单线程 vs 多线程

**背景**：交易系统需要处理大量并发订单

**方案对比**：

| 维度 | 单线程 | 多线程 |
|------|--------|--------|
| 复杂度 | 低 | 高 |
| 性能 | 一般 | 高 |
| 调试难度 | 低 | 高 |
| 学习价值 | 专注核心逻辑 | 分散注意力 |

**最终选择**：单线程

**理由**：
1. 专注于核心算法学习
2. 避免并发问题的复杂性
3. 代码更清晰易懂

**权衡**：
- 放弃了高并发处理能力
- 得到了更清晰的代码结构

### 决策2：使用 std::map 而不是自定义数据结构

**背景**：需要选择合适的数据结构存储价格层级

**方案对比**：

| 维度 | std::map | 自定义红黑树 | 跳表 |
|------|----------|--------------|------|
| 实现难度 | 低 | 高 | 中 |
| 性能 | 好 | 更好 | 好 |
| 可维护性 | 高 | 低 | 中 |
| 学习价值 | 理解STL | 理解数据结构 | 理解概率数据结构 |

**最终选择**：std::map

**理由**：
1. 标准库实现，质量有保证
2. 代码简洁，易于理解
3. 性能满足学习需求

**权衡**：
- 放弃了极致的性能优化
- 得到了更简洁的代码

## 7. 扩展性设计

### 预留的扩展点

1. **回调机制**
   - 通过 `TradeCallback` 和 `OrderCallback` 支持事件通知
   - 可以轻松添加日志、监控等功能

2. **订单类型扩展**
   - `OrderType` 枚举可以扩展支持更多订单类型
   - 如：止损单、冰山单等

3. **性能优化**
   - 可以替换 `std::map` 为自定义数据结构
   - 可以添加内存池减少分配开销

### 如何扩展

**添加新的订单类型**：

1. 在 `OrderType` 枚举中添加新类型
2. 在 `MatchingEngine` 中添加对应的处理逻辑
3. 添加单元测试验证

**优化性能**：

1. 替换 `std::map` 为跳表或自定义红黑树
2. 使用内存池预分配订单对象
3. 使用无锁数据结构支持并发
