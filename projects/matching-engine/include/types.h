#pragma once

#include <cstdint>
#include <chrono>
#include <string>
#include <functional>

namespace hft {

// 时间戳类型
using Timestamp = std::chrono::nanoseconds;

// 订单ID类型
using OrderId = uint64_t;

// 价格类型（使用定点数避免浮点误差）
using Price = int64_t;

// 数量类型
using Quantity = uint64_t;

// 方向枚举
enum class Side : uint8_t {
    Buy = 0,
    Sell = 1
};

// 订单类型枚举
enum class OrderType : uint8_t {
    Market = 0,  // 市价单
    Limit = 1    // 限价单
};

// 订单状态枚举
enum class OrderStatus : uint8_t {
    New = 0,        // 新订单
    Partial = 1,    // 部分成交
    Filled = 2,     // 完全成交
    Cancelled = 3,  // 已取消
    Rejected = 4    // 已拒绝
};

// 成交记录结构
struct Trade {
    OrderId buy_order_id;
    OrderId sell_order_id;
    Price price;
    Quantity quantity;
    Timestamp timestamp;
};

// 订单结构
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

    // 检查是否有效
    bool is_valid() const {
        return quantity > 0 && (type == OrderType::Market || price > 0);
    }
};

// 订单簿层级
struct PriceLevel {
    Price price;
    Quantity total_quantity;
    uint32_t order_count;

    PriceLevel() : price(0), total_quantity(0), order_count(0) {}
    PriceLevel(Price p) : price(p), total_quantity(0), order_count(0) {}
};

// 回调函数类型定义
using TradeCallback = std::function<void(const Trade&)>;
using OrderCallback = std::function<void(const Order&)>;

} // namespace hft
