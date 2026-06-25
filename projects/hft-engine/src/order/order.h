/**
 * @file order.h
 * @brief 订单数据结构
 *
 * 定义订单的核心数据结构和相关枚举类型。
 */

#pragma once

#include <cstdint>
#include <string>
#include <sstream>

#include "market_data/tick.h"
#include "core/timestamp.h"

namespace hft {

/**
 * @enum OrderType
 * @brief 订单类型
 */
enum class OrderType : uint8_t {
    MARKET = 0,       ///< 市价单
    LIMIT = 1,        ///< 限价单
    STOP = 2,         ///< 止损单
    STOP_LIMIT = 3,   ///< 止损限价单
    ICEBERG = 4,      ///< 冰山单
    IOC = 5,          ///< 立即成交或取消
    FOK = 6           ///< 全部成交或取消
};

/**
 * @brief OrderType 转字符串
 */
inline const char* order_type_to_string(OrderType type) {
    switch (type) {
        case OrderType::MARKET:     return "MARKET";
        case OrderType::LIMIT:      return "LIMIT";
        case OrderType::STOP:       return "STOP";
        case OrderType::STOP_LIMIT: return "STOP_LIMIT";
        case OrderType::ICEBERG:    return "ICEBERG";
        case OrderType::IOC:        return "IOC";
        case OrderType::FOK:        return "FOK";
        default: return "UNKNOWN";
    }
}

/**
 * @enum OrderStatus
 * @brief 订单状态
 */
enum class OrderStatus : uint8_t {
    CREATED = 0,        ///< 已创建
    SENT = 1,           ///< 已发送
    ACKNOWLEDGED = 2,   ///< 已确认
    PARTIALLY_FILLED = 3,  ///< 部分成交
    FILLED = 4,         ///< 全部成交
    CANCELLED = 5,      ///< 已取消
    REJECTED = 6,       ///< 已拒绝
    EXPIRED = 7,        ///< 已过期
    PENDING_CANCEL = 8  ///< 待取消
};

/**
 * @brief OrderStatus 转字符串
 */
inline const char* order_status_to_string(OrderStatus status) {
    switch (status) {
        case OrderStatus::CREATED:          return "CREATED";
        case OrderStatus::SENT:             return "SENT";
        case OrderStatus::ACKNOWLEDGED:     return "ACKNOWLEDGED";
        case OrderStatus::PARTIALLY_FILLED: return "PARTIALLY_FILLED";
        case OrderStatus::FILLED:           return "FILLED";
        case OrderStatus::CANCELLED:        return "CANCELLED";
        case OrderStatus::REJECTED:         return "REJECTED";
        case OrderStatus::EXPIRED:          return "EXPIRED";
        case OrderStatus::PENDING_CANCEL:   return "PENDING_CANCEL";
        default: return "UNKNOWN";
    }
}

/**
 * @enum TimeInForce
 * @brief 订单有效期
 */
enum class TimeInForce : uint8_t {
    GTC = 0,  ///< 撤销前有效
    IOC = 1,  ///< 立即成交或取消
    FOK = 2,  ///< 全部成交或取消
    DAY = 3,  ///< 当日有效
    GTX = 4   ///< 收盘前有效
};

/**
 * @struct Order
 * @brief 订单数据结构
 */
struct Order {
    std::string order_id;       ///< 订单 ID
    std::string symbol;         ///< 品种代码
    Side side;                  ///< 买卖方向
    OrderType type;             ///< 订单类型
    OrderStatus status;         ///< 订单状态
    TimeInForce time_in_force;  ///< 有效期

    double price;               ///< 价格
    double stop_price;          ///< 止损价格
    int64_t quantity;           ///< 订单数量
    int64_t filled_quantity;    ///< 已成交数量
    int64_t remaining_quantity; ///< 剩余数量

    double avg_fill_price;      ///< 平均成交价
    double commission;          ///< 手续费

    Timestamp create_time;      ///< 创建时间
    Timestamp send_time;        ///< 发送时间
    Timestamp ack_time;         ///< 确认时间
    Timestamp fill_time;        ///< 成交时间
    Timestamp cancel_time;      ///< 取消时间

    std::string exchange;       ///< 交易所
    std::string account;        ///< 账户
    std::string strategy_id;    ///< 策略 ID
    std::string reject_reason;  ///< 拒绝原因

    /**
     * @brief 默认构造函数
     */
    Order()
        : side(Side::BUY), type(OrderType::LIMIT), status(OrderStatus::CREATED),
          time_in_force(TimeInForce::GTC), price(0.0), stop_price(0.0),
          quantity(0), filled_quantity(0), remaining_quantity(0),
          avg_fill_price(0.0), commission(0.0) {}

    /**
     * @brief 是否已完结
     * @return 已完结返回 true
     */
    bool is_terminal() const {
        return status == OrderStatus::FILLED ||
               status == OrderStatus::CANCELLED ||
               status == OrderStatus::REJECTED ||
               status == OrderStatus::EXPIRED;
    }

    /**
     * @brief 是否活跃
     * @return 活跃返回 true
     */
    bool is_active() const {
        return !is_terminal();
    }

    /**
     * @brief 是否已成交
     * @return 已成交返回 true
     */
    bool is_filled() const {
        return status == OrderStatus::FILLED;
    }

    /**
     * @brief 是否部分成交
     * @return 部分成交返回 true
     */
    bool is_partially_filled() const {
        return status == OrderStatus::PARTIALLY_FILLED;
    }

    /**
     * @brief 是否已取消
     * @return 已取消返回 true
     */
    bool is_cancelled() const {
        return status == OrderStatus::CANCELLED;
    }

    /**
     * @brief 计算成交百分比
     * @return 成交百分比
     */
    double fill_percentage() const {
        if (quantity == 0) return 0.0;
        return static_cast<double>(filled_quantity) / quantity * 100.0;
    }

    /**
     * @brief 计算订单价值
     * @return 订单价值
     */
    double value() const {
        return price * quantity;
    }

    /**
     * @brief 计算已成交价值
     * @return 已成交价值
     */
    double filled_value() const {
        return avg_fill_price * filled_quantity;
    }

    /**
     * @brief 计算盈亏
     * @param current_price 当前价格
     * @return 盈亏
     */
    double pnl(double current_price) const {
        if (filled_quantity == 0) return 0.0;

        double direction = (side == Side::BUY) ? 1.0 : -1.0;
        return direction * (current_price - avg_fill_price) * filled_quantity;
    }

    /**
     * @brief 格式化为字符串
     * @return 格式化字符串
     */
    std::string to_string() const {
        std::ostringstream oss;
        oss << "Order[" << order_id << "] "
            << symbol << " "
            << side_to_string(side) << " "
            << order_type_to_string(type) << " "
            << quantity << " @ " << price << " "
            << order_status_to_string(status) << " "
            << "Filled:" << filled_quantity << "/" << quantity;
        return oss.str();
    }
};

/**
 * @struct Trade
 * @brief 成交记录
 */
struct Trade {
    std::string trade_id;       ///< 成交 ID
    std::string order_id;       ///< 订单 ID
    std::string symbol;         ///< 品种代码
    Side side;                  ///< 买卖方向
    double price;               ///< 成交价格
    int64_t quantity;           ///< 成交数量
    double commission;          ///< 手续费
    Timestamp timestamp;        ///< 成交时间
    std::string exchange;       ///< 交易所

    /**
     * @brief 默认构造函数
     */
    Trade()
        : side(Side::BUY), price(0.0), quantity(0), commission(0.0) {}

    /**
     * @brief 计算成交价值
     * @return 成交价值
     */
    double value() const {
        return price * quantity;
    }

    /**
     * @brief 格式化为字符串
     * @return 格式化字符串
     */
    std::string to_string() const {
        std::ostringstream oss;
        oss << "Trade[" << trade_id << "] "
            << order_id << " "
            << symbol << " "
            << side_to_string(side) << " "
            << quantity << " @ " << price;
        return oss.str();
    }
};

/**
 * @struct ExecutionReport
 * @brief 执行报告
 */
struct ExecutionReport {
    std::string order_id;       ///< 订单 ID
    std::string exec_id;        ///< 执行 ID
    OrderStatus status;         ///< 订单状态
    double last_price;          ///< 最新成交价
    int64_t last_quantity;      ///< 最新成交量
    double avg_price;           ///< 平均成交价
    int64_t cum_quantity;       ///< 累计成交量
    int64_t leaves_quantity;    ///< 剩余数量
    std::string reject_reason;  ///< 拒绝原因
    Timestamp timestamp;        ///< 时间戳

    /**
     * @brief 默认构造函数
     */
    ExecutionReport()
        : status(OrderStatus::CREATED), last_price(0.0), last_quantity(0),
          avg_price(0.0), cum_quantity(0), leaves_quantity(0) {}
};

} // namespace hft
