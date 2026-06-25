/**
 * @file position.h
 * @brief 持仓管理
 *
 * 管理交易持仓，包括持仓计算、盈亏计算等。
 */

#pragma once

#include <string>
#include <unordered_map>
#include <vector>
#include <mutex>

#include "market_data/tick.h"
#include "order/order.h"
#include "core/timestamp.h"
#include "core/logger.h"

namespace hft {

/**
 * @struct Position
 * @brief 持仓信息
 */
struct Position {
    std::string symbol;         ///< 品种代码
    int64_t quantity = 0;       ///< 持仓数量（正为多头，负为空头）
    double avg_price = 0.0;     ///< 平均成本
    double unrealized_pnl = 0.0;  ///< 未实现盈亏
    double realized_pnl = 0.0;   ///< 已实现盈亏
    double margin_used = 0.0;   ///< 占用保证金
    Timestamp last_update;      ///< 最后更新时间

    /**
     * @brief 计算持仓价值
     * @param current_price 当前价格
     * @return 持仓价值
     */
    double value(double current_price) const {
        return quantity * current_price;
    }

    /**
     * @brief 计算盈亏
     * @param current_price 当前价格
     * @return 盈亏
     */
    double pnl(double current_price) const {
        return realized_pnl + unrealized_pnl;
    }

    /**
     * @brief 更新未实现盈亏
     * @param current_price 当前价格
     */
    void update_unrealized_pnl(double current_price) {
        if (quantity != 0) {
            unrealized_pnl = (current_price - avg_price) * quantity;
        } else {
            unrealized_pnl = 0.0;
        }
    }

    /**
     * @brief 是否有多头持仓
     * @return 有多头持仓返回 true
     */
    bool is_long() const {
        return quantity > 0;
    }

    /**
     * @brief 是否有空头持仓
     * @return 有空头持仓返回 true
     */
    bool is_short() const {
        return quantity < 0;
    }

    /**
     * @brief 是否有持仓
     * @return 有持仓返回 true
     */
    bool has_position() const {
        return quantity != 0;
    }

    /**
     * @brief 格式化为字符串
     * @return 格式化字符串
     */
    std::string to_string() const {
        std::ostringstream oss;
        oss << "Position[" << symbol << "] "
            << "Qty:" << quantity << " "
            << "AvgPrice:" << avg_price << " "
            << "PnL:" << (realized_pnl + unrealized_pnl);
        return oss.str();
    }
};

/**
 * @class PositionManager
 * @brief 持仓管理器
 *
 * 特性：
 * - 实时持仓计算
 * - 多品种持仓汇总
 * - 盈亏计算
 * - 保证金计算
 * - 线程安全
 */
class PositionManager {
public:
    /**
     * @brief 构造函数
     */
    PositionManager() = default;

    /**
     * @brief 析构函数
     */
    ~PositionManager() = default;

    /**
     * @brief 更新持仓（基于成交）
     * @param trade 成交记录
     */
    void update_position(const Trade& trade) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto& pos = positions_[trade.symbol];
        pos.symbol = trade.symbol;

        int64_t old_quantity = pos.quantity;
        int64_t trade_quantity = (trade.side == Side::BUY) ?
                                 trade.quantity : -trade.quantity;

        // 计算新的平均成本
        if (pos.quantity == 0) {
            // 新开仓
            pos.avg_price = trade.price;
            pos.quantity = trade_quantity;
        } else if ((pos.quantity > 0 && trade.side == Side::BUY) ||
                   (pos.quantity < 0 && trade.side == Side::SELL)) {
            // 加仓
            double total_value = pos.avg_price * std::abs(pos.quantity) +
                               trade.price * trade.quantity;
            pos.quantity += trade_quantity;
            pos.avg_price = total_value / std::abs(pos.quantity);
        } else {
            // 减仓或平仓
            if (std::abs(trade_quantity) >= std::abs(pos.quantity)) {
                // 平仓或反手
                double pnl = (trade.price - pos.avg_price) * pos.quantity;
                pos.realized_pnl += pnl;

                int64_t remaining = trade_quantity + pos.quantity;
                if (remaining != 0) {
                    // 反手
                    pos.quantity = remaining;
                    pos.avg_price = trade.price;
                } else {
                    // 完全平仓
                    pos.quantity = 0;
                    pos.avg_price = 0.0;
                }
            } else {
                // 部分减仓
                double pnl = (trade.price - pos.avg_price) * (-trade_quantity);
                pos.realized_pnl += pnl;
                pos.quantity += trade_quantity;
            }
        }

        pos.last_update = Timestamp::now();

        LOG_INFO("Position updated: " + pos.to_string());
    }

    /**
     * @brief 获取指定品种的持仓
     * @param symbol 品种代码
     * @return 持仓信息
     */
    Position get_position(const std::string& symbol) const {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = positions_.find(symbol);
        if (it != positions_.end()) {
            return it->second;
        }
        return Position{symbol};
    }

    /**
     * @brief 获取所有持仓
     * @return 持仓列表
     */
    std::vector<Position> get_all_positions() const {
        std::lock_guard<std::mutex> lock(mutex_);

        std::vector<Position> result;
        for (const auto& [symbol, pos] : positions_) {
            if (pos.has_position()) {
                result.push_back(pos);
            }
        }
        return result;
    }

    /**
     * @brief 获取总持仓数量
     * @return 总持仓数量
     */
    int64_t total_quantity() const {
        std::lock_guard<std::mutex> lock(mutex_);

        int64_t total = 0;
        for (const auto& [symbol, pos] : positions_) {
            total += std::abs(pos.quantity);
        }
        return total;
    }

    /**
     * @brief 获取总已实现盈亏
     * @return 总已实现盈亏
     */
    double total_realized_pnl() const {
        std::lock_guard<std::mutex> lock(mutex_);

        double total = 0;
        for (const auto& [symbol, pos] : positions_) {
            total += pos.realized_pnl;
        }
        return total;
    }

    /**
     * @brief 获取总未实现盈亏
     * @return 总未实现盈亏
     */
    double total_unrealized_pnl() const {
        std::lock_guard<std::mutex> lock(mutex_);

        double total = 0;
        for (const auto& [symbol, pos] : positions_) {
            total += pos.unrealized_pnl;
        }
        return total;
    }

    /**
     * @brief 更新所有持仓的未实现盈亏
     * @param prices 当前价格映射
     */
    void update_unrealized_pnl(const std::unordered_map<std::string, double>& prices) {
        std::lock_guard<std::mutex> lock(mutex_);

        for (auto& [symbol, pos] : positions_) {
            auto it = prices.find(symbol);
            if (it != prices.end()) {
                pos.update_unrealized_pnl(it->second);
            }
        }
    }

    /**
     * @brief 清空所有持仓
     */
    void clear() {
        std::lock_guard<std::mutex> lock(mutex_);
        positions_.clear();
    }

private:
    mutable std::mutex mutex_;  ///< 互斥锁
    std::unordered_map<std::string, Position> positions_;  ///< 持仓映射
};

} // namespace hft
