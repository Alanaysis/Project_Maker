/**
 * @file margin.h
 * @brief 保证金管理
 *
 * 管理交易保证金，包括保证金计算、监控、追保预警等。
 */

#pragma once

#include <string>
#include <unordered_map>
#include <mutex>

#include "position.h"
#include "core/logger.h"

namespace hft {

/**
 * @struct MarginConfig
 * @brief 保证金配置
 */
struct MarginConfig {
    double initial_margin_rate = 0.1;    ///< 初始保证金率
    double maintenance_margin_rate = 0.05;  ///< 维持保证金率
    double margin_call_rate = 0.08;      ///< 追保线
    double liquidation_rate = 0.03;      ///< 强平线
};

/**
 * @struct MarginInfo
 * @brief 保证金信息
 */
struct MarginInfo {
    std::string symbol;             ///< 品种代码
    double position_value = 0.0;    ///< 持仓价值
    double initial_margin = 0.0;    ///< 初始保证金
    double maintenance_margin = 0.0;  ///< 维持保证金
    double available_margin = 0.0;  ///< 可用保证金
    double margin_ratio = 0.0;      ///< 保证金比例
    bool margin_call = false;       ///< 是否需要追保
    bool liquidation = false;       ///< 是否需要强平
};

/**
 * @class MarginManager
 * @brief 保证金管理器
 *
 * 特性：
 * - 保证金计算
 * - 保证金监控
 * - 追保预警
 * - 强平逻辑
 */
class MarginManager {
public:
    /**
     * @brief 构造函数
     * @param config 保证金配置
     * @param total_balance 总资金
     */
    explicit MarginManager(const MarginConfig& config = MarginConfig(),
                          double total_balance = 1000000.0)
        : config_(config), total_balance_(total_balance),
          available_balance_(total_balance) {}

    /**
     * @brief 析构函数
     */
    ~MarginManager() = default;

    /**
     * @brief 计算保证金
     * @param symbol 品种代码
     * @param price 价格
     * @param quantity 数量
     * @return 所需保证金
     */
    double calculate_margin(const std::string& symbol, double price,
                           int64_t quantity) const {
        return price * quantity * config_.initial_margin_rate;
    }

    /**
     * @brief 检查保证金是否充足
     * @param symbol 品种代码
     * @param price 价格
     * @param quantity 数量
     * @return 充足返回 true
     */
    bool check_margin(const std::string& symbol, double price,
                      int64_t quantity) {
        std::lock_guard<std::mutex> lock(mutex_);

        double required_margin = calculate_margin(symbol, price, quantity);
        return available_balance_ >= required_margin;
    }

    /**
     * @brief 占用保证金
     * @param symbol 品种代码
     * @param price 价格
     * @param quantity 数量
     * @return 成功返回 true
     */
    bool allocate_margin(const std::string& symbol, double price,
                        int64_t quantity) {
        std::lock_guard<std::mutex> lock(mutex_);

        double required_margin = calculate_margin(symbol, price, quantity);
        if (available_balance_ < required_margin) {
            LOG_WARN("Insufficient margin for " + symbol);
            return false;
        }

        available_balance_ -= required_margin;
        margin_used_[symbol] += required_margin;

        LOG_INFO("Margin allocated: " + symbol +
                 " Amount: " + std::to_string(required_margin));
        return true;
    }

    /**
     * @brief 释放保证金
     * @param symbol 品种代码
     * @param amount 金额
     */
    void release_margin(const std::string& symbol, double amount) {
        std::lock_guard<std::mutex> lock(mutex_);

        available_balance_ += amount;
        margin_used_[symbol] -= amount;

        if (margin_used_[symbol] <= 0) {
            margin_used_.erase(symbol);
        }

        LOG_INFO("Margin released: " + symbol +
                 " Amount: " + std::to_string(amount));
    }

    /**
     * @brief 获取保证金信息
     * @param symbol 品种代码
     * @param position 持仓信息
     * @return 保证金信息
     */
    MarginInfo get_margin_info(const std::string& symbol,
                               const Position& position) const {
        std::lock_guard<std::mutex> lock(mutex_);

        MarginInfo info;
        info.symbol = symbol;

        if (position.quantity == 0) {
            return info;
        }

        double position_value = std::abs(position.quantity) * position.avg_price;
        info.position_value = position_value;
        info.initial_margin = position_value * config_.initial_margin_rate;
        info.maintenance_margin = position_value * config_.maintenance_margin_rate;

        auto it = margin_used_.find(symbol);
        double used_margin = (it != margin_used_.end()) ? it->second : 0;
        info.available_margin = total_balance_ - used_margin;

        if (used_margin > 0) {
            info.margin_ratio = info.available_margin / used_margin;
        }

        // 检查追保和强平
        info.margin_call = (info.margin_ratio < config_.margin_call_rate);
        info.liquidation = (info.margin_ratio < config_.liquidation_rate);

        return info;
    }

    /**
     * @brief 获取总保证金使用
     * @return 总保证金使用
     */
    double total_margin_used() const {
        std::lock_guard<std::mutex> lock(mutex_);

        double total = 0;
        for (const auto& [symbol, margin] : margin_used_) {
            total += margin;
        }
        return total;
    }

    /**
     * @brief 获取可用保证金
     * @return 可用保证金
     */
    double available_margin() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return available_balance_;
    }

    /**
     * @brief 更新总资金
     * @param balance 总资金
     */
    void update_balance(double balance) {
        std::lock_guard<std::mutex> lock(mutex_);
        total_balance_ = balance;
        available_balance_ = balance - total_margin_used();
    }

private:
    mutable std::mutex mutex_;  ///< 互斥锁
    MarginConfig config_;       ///< 保证金配置
    double total_balance_;      ///< 总资金
    double available_balance_;  ///< 可用资金
    std::unordered_map<std::string, double> margin_used_;  ///< 已用保证金
};

} // namespace hft
