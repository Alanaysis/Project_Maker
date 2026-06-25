/**
 * @file execution_report.h
 * @brief 执行报告
 *
 * 定义执行报告相关的数据结构。
 */

#pragma once

#include <cstdint>
#include <string>
#include <sstream>

#include "core/timestamp.h"
#include "market_data/tick.h"
#include "order.h"

namespace hft {

/**
 * @enum ExecType
 * @brief 执行类型
 */
enum class ExecType : uint8_t {
    NEW = 0,            ///< 新订单确认
    PARTIAL_FILL = 1,   ///< 部分成交
    FILL = 2,           ///< 全部成交
    CANCELLED = 3,      ///< 已取消
    REJECTED = 4,       ///< 已拒绝
    EXPIRED = 5,        ///< 已过期
    REPLACE = 6,        ///< 订单修改
    PENDING_CANCEL = 7, ///< 待取消
    PENDING_REPLACE = 8 ///< 待修改
};

/**
 * @brief ExecType 转字符串
 */
inline const char* exec_type_to_string(ExecType type) {
    switch (type) {
        case ExecType::NEW:            return "NEW";
        case ExecType::PARTIAL_FILL:   return "PARTIAL_FILL";
        case ExecType::FILL:           return "FILL";
        case ExecType::CANCELLED:      return "CANCELLED";
        case ExecType::REJECTED:       return "REJECTED";
        case ExecType::EXPIRED:        return "EXPIRED";
        case ExecType::REPLACE:        return "REPLACE";
        case ExecType::PENDING_CANCEL: return "PENDING_CANCEL";
        case ExecType::PENDING_REPLACE: return "PENDING_REPLACE";
        default: return "UNKNOWN";
    }
}

/**
 * @struct DetailedExecutionReport
 * @brief 详细执行报告
 */
struct DetailedExecutionReport {
    std::string order_id;           ///< 订单 ID
    std::string exec_id;            ///< 执行 ID
    std::string exec_ref_id;        ///< 执行引用 ID
    ExecType exec_type;             ///< 执行类型
    OrderStatus ord_status;         ///< 订单状态

    std::string symbol;             ///< 品种代码
    Side side;                      ///< 买卖方向
    double order_qty;               ///< 订单数量
    double price;                   ///< 价格
    double stop_price;              ///< 止损价格

    double last_price;              ///< 最新成交价
    double last_qty;                ///< 最新成交量
    double cum_qty;                 ///< 累计成交量
    double leaves_qty;              ///< 剩余数量
    double avg_price;               ///< 平均成交价

    double commission;              ///< 手续费
    std::string commission_type;    ///< 手续费类型

    std::string exchange;           ///< 交易所
    std::string account;            ///< 账户

    Timestamp transact_time;        ///< 交易时间
    Timestamp send_time;            ///< 发送时间

    std::string text;               ///< 文本说明
    int reject_reason;              ///< 拒绝原因代码

    /**
     * @brief 默认构造函数
     */
    DetailedExecutionReport()
        : exec_type(ExecType::NEW), ord_status(OrderStatus::CREATED),
          side(Side::BUY), order_qty(0), price(0), stop_price(0),
          last_price(0), last_qty(0), cum_qty(0), leaves_qty(0),
          avg_price(0), commission(0), reject_reason(0) {}

    /**
     * @brief 格式化为字符串
     * @return 格式化字符串
     */
    std::string to_string() const {
        std::ostringstream oss;
        oss << "ExecReport["
            << order_id << "]["
            << exec_id << "] "
            << exec_type_to_string(exec_type) << " "
            << symbol << " "
            << (side == Side::BUY ? "BUY" : "SELL") << " "
            << cum_qty << "/" << order_qty << " @ " << avg_price;
        return oss.str();
    }
};

} // namespace hft
