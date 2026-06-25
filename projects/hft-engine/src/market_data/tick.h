/**
 * @file tick.h
 * @brief Tick 数据结构
 *
 * 定义市场数据的核心数据结构，包括 Tick、Bar、OrderBookUpdate 等。
 */

#pragma once

#include <cstdint>
#include <string>
#include <chrono>
#include <array>

#include "core/timestamp.h"

namespace hft {

/**
 * @enum Side
 * @brief 买卖方向
 */
enum class Side : uint8_t {
    BUY = 0,   ///< 买入
    SELL = 1   ///< 卖出
};

/**
 * @brief Side 转字符串
 */
inline const char* side_to_string(Side side) {
    return side == Side::BUY ? "BUY" : "SELL";
}

/**
 * @enum TickType
 * @brief Tick 类型
 */
enum class TickType : uint8_t {
    TRADE = 0,      ///< 成交
    BID = 1,        ///< 买盘
    ASK = 2,        ///< 卖盘
    BID_SIZE = 3,   ///< 买盘量
    ASK_SIZE = 4,   ///< 卖盘量
    OPEN = 5,       ///< 开盘价
    HIGH = 6,       ///< 最高价
    LOW = 7,        ///< 最低价
    CLOSE = 8,      ///< 收盘价
    VOLUME = 9,     ///< 成交量
    OPEN_INTEREST = 10  ///< 持仓量
};

/**
 * @struct Tick
 * @brief Tick 数据结构
 *
 * 表示一个市场数据点，包含价格、数量、时间等信息。
 */
struct Tick {
    std::string symbol;     ///< 品种代码
    Timestamp timestamp;    ///< 时间戳
    TickType type;          ///< Tick 类型
    double price;           ///< 价格
    int64_t quantity;       ///< 数量
    double bid_price;       ///< 买一价
    double ask_price;       ///< 卖一价
    int64_t bid_quantity;   ///< 买一量
    int64_t ask_quantity;   ///< 卖一量
    double last_price;      ///< 最新价
    int64_t last_quantity;  ///< 最新量
    double open_price;      ///< 开盘价
    double high_price;      ///< 最高价
    double low_price;       ///< 最低价
    double close_price;     ///< 收盘价
    int64_t volume;         ///< 成交量
    int64_t open_interest;  ///< 持仓量
    double turnover;        ///< 成交额

    /**
     * @brief 默认构造函数
     */
    Tick()
        : type(TickType::TRADE), price(0.0), quantity(0),
          bid_price(0.0), ask_price(0.0), bid_quantity(0), ask_quantity(0),
          last_price(0.0), last_quantity(0), open_price(0.0), high_price(0.0),
          low_price(0.0), close_price(0.0), volume(0), open_interest(0),
          turnover(0.0) {}

    /**
     * @brief 计算中间价
     * @return 中间价
     */
    double mid_price() const {
        if (bid_price > 0 && ask_price > 0) {
            return (bid_price + ask_price) / 2.0;
        }
        return last_price;
    }

    /**
     * @brief 计算价差
     * @return 买卖价差
     */
    double spread() const {
        if (bid_price > 0 && ask_price > 0) {
            return ask_price - bid_price;
        }
        return 0.0;
    }

    /**
     * @brief 计算价差百分比
     * @return 价差百分比
     */
    double spread_pct() const {
        double mid = mid_price();
        if (mid > 0) {
            return spread() / mid * 100.0;
        }
        return 0.0;
    }

    /**
     * @brief 格式化为字符串
     * @return 格式化字符串
     */
    std::string to_string() const {
        std::ostringstream oss;
        oss << symbol << " "
            << timestamp.to_string() << " "
            << "Last:" << last_price << "x" << last_quantity << " "
            << "Bid:" << bid_price << "x" << bid_quantity << " "
            << "Ask:" << ask_price << "x" << ask_quantity << " "
            << "Vol:" << volume;
        return oss.str();
    }
};

/**
 * @struct Bar
 * @brief K 线数据结构
 */
struct Bar {
    std::string symbol;     ///< 品种代码
    Timestamp timestamp;    ///< 时间戳
    double open;            ///< 开盘价
    double high;            ///< 最高价
    double low;             ///< 最低价
    double close;           ///< 收盘价
    int64_t volume;         ///< 成交量
    double turnover;        ///< 成交额

    /**
     * @brief 默认构造函数
     */
    Bar() : open(0), high(0), low(0), close(0), volume(0), turnover(0) {}

    /**
     * @brief 计算典型价格
     * @return (最高 + 最低 + 收盘) / 3
     */
    double typical_price() const {
        return (high + low + close) / 3.0;
    }

    /**
     * @brief 计算价格范围
     * @return 最高 - 最低
     */
    double range() const {
        return high - low;
    }

    /**
     * @brief 计算实体大小
     * @return |收盘 - 开盘|
     */
    double body() const {
        return std::abs(close - open);
    }

    /**
     * @brief 是否为阳线
     * @return 收盘 > 开盘
     */
    bool is_bullish() const {
        return close > open;
    }

    /**
     * @brief 是否为阴线
     * @return 收盘 < 开盘
     */
    bool is_bearish() const {
        return close < open;
    }
};

/**
 * @struct OrderBookUpdate
 * @brief 订单簿更新
 */
struct OrderBookUpdate {
    std::string symbol;     ///< 品种代码
    Timestamp timestamp;    ///< 时间戳
    Side side;              ///< 买卖方向
    double price;           ///< 价格
    int64_t quantity;       ///< 数量（0 表示删除）
    int32_t order_count;    ///< 订单数量
    int32_t update_type;    ///< 更新类型（0=新增，1=更新，2=删除）

    /**
     * @brief 默认构造函数
     */
    OrderBookUpdate()
        : side(Side::BUY), price(0.0), quantity(0),
          order_count(0), update_type(0) {}
};

/**
 * @struct PriceLevel
 * @brief 价格档位
 */
struct PriceLevel {
    double price;           ///< 价格
    int64_t quantity;       ///< 数量
    int32_t order_count;    ///< 订单数量

    /**
     * @brief 默认构造函数
     */
    PriceLevel() : price(0.0), quantity(0), order_count(0) {}

    /**
     * @brief 参数构造函数
     */
    PriceLevel(double p, int64_t q, int32_t c = 1)
        : price(p), quantity(q), order_count(c) {}
};

/**
 * @struct MarketDepth
 * @brief 市场深度
 */
struct MarketDepth {
    static constexpr size_t MAX_DEPTH = 10;  ///< 最大深度

    std::string symbol;                        ///< 品种代码
    Timestamp timestamp;                       ///< 时间戳
    std::array<PriceLevel, MAX_DEPTH> bids;    ///< 买盘
    std::array<PriceLevel, MAX_DEPTH> asks;    ///< 卖盘
    size_t bid_depth;                          ///< 买盘深度
    size_t ask_depth;                          ///< 卖盘深度

    /**
     * @brief 默认构造函数
     */
    MarketDepth() : bid_depth(0), ask_depth(0) {}

    /**
     * @brief 获取最优买价
     * @return 最优买价
     */
    double best_bid() const {
        return bid_depth > 0 ? bids[0].price : 0.0;
    }

    /**
     * @brief 获取最优卖价
     * @return 最优卖价
     */
    double best_ask() const {
        return ask_depth > 0 ? asks[0].price : 0.0;
    }

    /**
     * @brief 获取中间价
     * @return 中间价
     */
    double mid_price() const {
        double bid = best_bid();
        double ask = best_ask();
        if (bid > 0 && ask > 0) {
            return (bid + ask) / 2.0;
        }
        return 0.0;
    }

    /**
     * @brief 获取价差
     * @return 买卖价差
     */
    double spread() const {
        double bid = best_bid();
        double ask = best_ask();
        if (bid > 0 && ask > 0) {
            return ask - bid;
        }
        return 0.0;
    }
};

} // namespace hft
