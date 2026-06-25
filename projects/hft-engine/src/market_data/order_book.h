/**
 * @file order_book.h
 * @brief 订单簿
 *
 * 高性能订单簿实现，支持快速的价格档位管理和深度查询。
 */

#pragma once

#include <map>
#include <unordered_map>
#include <vector>
#include <string>
#include <functional>
#include <mutex>
#include <algorithm>

#include "tick.h"
#include "core/timestamp.h"

namespace hft {

/**
 * @class OrderBook
 * @brief 订单簿
 *
 * 特性：
 * - 支持多档深度
 * - 快速的价格档位查询
 * - 增量更新
 * - 线程安全（可选）
 */
class OrderBook {
public:
    /**
     * @brief 构造函数
     * @param symbol 品种代码
     * @param max_depth 最大深度
     */
    explicit OrderBook(const std::string& symbol, size_t max_depth = 10)
        : symbol_(symbol), max_depth_(max_depth) {}

    /**
     * @brief 更新订单簿
     * @param update 更新数据
     */
    void update(const OrderBookUpdate& update) {
        if (update.side == Side::BUY) {
            update_levels(bids_, update);
        } else {
            update_levels(asks_, update);
        }
    }

    /**
     * @brief 获取最优买价
     * @return 最优买价
     */
    double best_bid() const {
        return best_bid_;
    }

    /**
     * @brief 获取最优卖价
     * @return 最优卖价
     */
    double best_ask() const {
        return best_ask_;
    }

    /**
     * @brief 获取中间价
     * @return 中间价
     */
    double mid_price() const {
        if (best_bid_ > 0 && best_ask_ > 0) {
            return (best_bid_ + best_ask_) / 2.0;
        }
        return 0.0;
    }

    /**
     * @brief 获取价差
     * @return 买卖价差
     */
    double spread() const {
        if (best_bid_ > 0 && best_ask_ > 0) {
            return best_ask_ - best_bid_;
        }
        return 0.0;
    }

    /**
     * @brief 获取买盘深度
     * @param depth 深度数量
     * @return 买盘档位列表
     */
    std::vector<PriceLevel> get_bid_depth(size_t depth = 0) const {
        if (depth == 0) depth = max_depth_;
        std::vector<PriceLevel> result;
        result.reserve(depth);

        // bids_ 使用 std::greater<double> 排序，所以 begin() 是最高价
        size_t count = 0;
        for (auto it = bids_.begin(); it != bids_.end() && count < depth; ++it, ++count) {
            result.push_back(it->second);
        }
        return result;
    }

    /**
     * @brief 获取卖盘深度
     * @param depth 深度数量
     * @return 卖盘档位列表
     */
    std::vector<PriceLevel> get_ask_depth(size_t depth = 0) const {
        if (depth == 0) depth = max_depth_;
        std::vector<PriceLevel> result;
        result.reserve(depth);

        size_t count = 0;
        for (auto it = asks_.begin(); it != asks_.end() && count < depth; ++it, ++count) {
            result.push_back(it->second);
        }
        return result;
    }

    /**
     * @brief 获取市场深度
     * @return 市场深度
     */
    MarketDepth get_market_depth() const {
        MarketDepth depth;
        depth.symbol = symbol_;
        depth.timestamp = Timestamp::now();

        auto bid_levels = get_bid_depth(MarketDepth::MAX_DEPTH);
        auto ask_levels = get_ask_depth(MarketDepth::MAX_DEPTH);

        depth.bid_depth = bid_levels.size();
        depth.ask_depth = ask_levels.size();

        for (size_t i = 0; i < bid_levels.size(); ++i) {
            depth.bids[i] = bid_levels[i];
        }
        for (size_t i = 0; i < ask_levels.size(); ++i) {
            depth.asks[i] = ask_levels[i];
        }

        return depth;
    }

    /**
     * @brief 获取指定价格的买量
     * @param price 价格
     * @return 数量
     */
    int64_t get_bid_quantity(double price) const {
        auto it = bids_.find(price);
        return (it != bids_.end()) ? it->second.quantity : 0;
    }

    /**
     * @brief 获取指定价格的卖量
     * @param price 价格
     * @return 数量
     */
    int64_t get_ask_quantity(double price) const {
        auto it = asks_.find(price);
        return (it != asks_.end()) ? it->second.quantity : 0;
    }

    /**
     * @brief 计算买盘总量
     * @return 买盘总量
     */
    int64_t total_bid_quantity() const {
        int64_t total = 0;
        for (const auto& [price, level] : bids_) {
            total += level.quantity;
        }
        return total;
    }

    /**
     * @brief 计算卖盘总量
     * @return 卖盘总量
     */
    int64_t total_ask_quantity() const {
        int64_t total = 0;
        for (const auto& [price, level] : asks_) {
            total += level.quantity;
        }
        return total;
    }

    /**
     * @brief 清空订单簿
     */
    void clear() {
        bids_.clear();
        asks_.clear();
        best_bid_ = 0.0;
        best_ask_ = 0.0;
    }

    /**
     * @brief 获取品种代码
     * @return 品种代码
     */
    const std::string& symbol() const {
        return symbol_;
    }

    /**
     * @brief 获取买盘档位数
     * @return 档位数
     */
    size_t bid_levels() const {
        return bids_.size();
    }

    /**
     * @brief 获取卖盘档位数
     * @return 档位数
     */
    size_t ask_levels() const {
        return asks_.size();
    }

    /**
     * @brief 格式化为字符串
     * @return 格式化字符串
     */
    std::string to_string() const {
        std::ostringstream oss;
        oss << "OrderBook: " << symbol_ << "\n";

        oss << "Asks:\n";
        for (auto it = asks_.begin(); it != asks_.end(); ++it) {
            oss << "  " << it->second.price << " x " << it->second.quantity << "\n";
        }

        oss << "Bids:\n";
        for (auto it = bids_.rbegin(); it != bids_.rend(); ++it) {
            oss << "  " << it->second.price << " x " << it->second.quantity << "\n";
        }

        return oss.str();
    }

private:
    /**
     * @brief 更新价格档位
     */
    template<typename MapType>
    void update_levels(MapType& levels, const OrderBookUpdate& update) {
        auto it = levels.find(update.price);

        if (update.quantity == 0) {
            // 删除档位
            if (it != levels.end()) {
                levels.erase(it);
            }
        } else {
            // 更新档位
            levels[update.price] = PriceLevel(
                update.price, update.quantity, update.order_count
            );
        }

        // 维护深度限制
        maintain_depth(levels, max_depth_);

        // 更新最优价
        update_best_prices();
    }

    /**
     * @brief 维护深度限制
     */
    template<typename MapType>
    void maintain_depth(MapType& levels, size_t max_depth) {
        while (levels.size() > max_depth) {
            levels.erase(levels.begin());
        }
    }

    /**
     * @brief 更新最优价格
     */
    void update_best_prices() {
        best_bid_ = bids_.empty() ? 0.0 : bids_.rbegin()->first;
        best_ask_ = asks_.empty() ? 0.0 : asks_.begin()->first;
    }

    std::string symbol_;                              ///< 品种代码
    size_t max_depth_;                                ///< 最大深度
    std::map<double, PriceLevel, std::greater<double>> bids_;  ///< 买盘（降序）
    std::map<double, PriceLevel> asks_;               ///< 卖盘（升序）
    double best_bid_ = 0.0;                           ///< 最优买价
    double best_ask_ = 0.0;                           ///< 最优卖价
};

/**
 * @class OrderBookManager
 * @brief 订单簿管理器
 *
 * 管理多个品种的订单簿。
 */
class OrderBookManager {
public:
    /**
     * @brief 获取或创建订单簿
     * @param symbol 品种代码
     * @return 订单簿引用
     */
    OrderBook& get_or_create(const std::string& symbol) {
        auto it = books_.find(symbol);
        if (it == books_.end()) {
            it = books_.emplace(symbol, OrderBook(symbol)).first;
        }
        return it->second;
    }

    /**
     * @brief 获取订单簿
     * @param symbol 品种代码
     * @return 订单簿指针（不存在返回 nullptr）
     */
    OrderBook* get(const std::string& symbol) {
        auto it = books_.find(symbol);
        return (it != books_.end()) ? &it->second : nullptr;
    }

    /**
     * @brief 更新订单簿
     * @param update 更新数据
     */
    void update(const OrderBookUpdate& update) {
        get_or_create(update.symbol).update(update);
    }

    /**
     * @brief 获取所有品种
     * @return 品种列表
     */
    std::vector<std::string> symbols() const {
        std::vector<std::string> result;
        result.reserve(books_.size());
        for (const auto& [symbol, book] : books_) {
            result.push_back(symbol);
        }
        return result;
    }

    /**
     * @brief 清空所有订单簿
     */
    void clear() {
        books_.clear();
    }

private:
    std::unordered_map<std::string, OrderBook> books_;  ///< 订单簿映射
};

} // namespace hft
