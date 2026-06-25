/**
 * @file stat_arb.h
 * @brief 统计套利策略
 *
 * 实现基于协整关系的统计套利策略。
 */

#pragma once

#include "strategy.h"
#include "order/order_manager.h"
#include "core/logger.h"

#include <vector>
#include <cmath>
#include <numeric>

namespace hft {

/**
 * @struct StatArbConfig
 * @brief 统计套利配置
 */
struct StatArbConfig {
    int lookback_period = 60;         ///< 回看周期
    double entry_z_score = 2.0;       ///< 入场 Z-score 阈值
    double exit_z_score = 0.5;        ///< 出场 Z-score 阈值
    double stop_z_score = 4.0;        ///< 止损 Z-score 阈值
    int64_t trade_size = 100;         ///< 交易数量
    double hedge_ratio = 1.0;         ///< 对冲比率
    int64_t max_position = 500;       ///< 最大持仓
};

/**
 * @class StatArbStrategy
 * @brief 统计套利策略
 *
 * 策略逻辑：
 * 1. 计算两个相关资产的价差
 * 2. 计算价差的 Z-score
 * 3. 当 Z-score 超过阈值时开仓
 * 4. 当 Z-score 回归时平仓
 */
class StatArbStrategy : public Strategy {
public:
    /**
     * @brief 构造函数
     * @param config 策略配置
     * @param order_manager 订单管理器
     * @param symbol1 品种 1
     * @param symbol2 品种 2
     */
    StatArbStrategy(const StatArbConfig& config, OrderManager& order_manager,
                    const std::string& symbol1, const std::string& symbol2)
        : Strategy("StatArb"), config_(config), order_manager_(order_manager),
          symbol1_(symbol1), symbol2_(symbol2),
          position1_(0), position2_(0), realized_pnl_(0) {}

    /**
     * @brief 析构函数
     */
    ~StatArbStrategy() override = default;

    // ==================== 生命周期 ====================

    void on_init() override {
        LOG_INFO("StatArbStrategy initialized: " + symbol1_ + " / " + symbol2_);
        set_state(StrategyState::INITED);
    }

    void on_start() override {
        LOG_INFO("StatArbStrategy started");
        set_state(StrategyState::RUNNING);
    }

    void on_stop() override {
        LOG_INFO("StatArbStrategy stopped");
        close_position();
        set_state(StrategyState::STOPPED);
    }

    // ==================== 数据回调 ====================

    void on_tick(const Tick& tick) override {
        if (!is_running()) return;

        // 更新价格
        prices_[tick.symbol] = tick.last_price;

        // 检查是否有足够的价格数据
        if (prices_.find(symbol1_) == prices_.end() ||
            prices_.find(symbol2_) == prices_.end()) {
            return;
        }

        // 计算价差
        double spread = calculate_spread();

        // 更新价差历史
        spreads_.push_back(spread);
        if (spreads_.size() > static_cast<size_t>(config_.lookback_period * 2)) {
            spreads_.erase(spreads_.begin());
        }

        // 计算 Z-score
        if (!update_z_score()) return;

        // 生成交易信号
        generate_signals();
    }

    void on_order(const Order& order) override {
        if (order.is_filled()) {
            LOG_INFO("StatArb order filled: " + order.to_string());
        }
    }

    void on_trade(const Trade& trade) override {
        // 更新持仓
        if (trade.symbol == symbol1_) {
            position1_ += (trade.side == Side::BUY) ? trade.quantity : -trade.quantity;
        } else if (trade.symbol == symbol2_) {
            position2_ += (trade.side == Side::BUY) ? trade.quantity : -trade.quantity;
        }

        LOG_INFO("StatArb trade: " + trade.to_string() +
                 " Position1: " + std::to_string(position1_) +
                 " Position2: " + std::to_string(position2_));
    }

    // ==================== 配置 ====================

    void set_params(const StrategyParams& params) override {
        if (params.has("lookback_period")) {
            config_.lookback_period = params.get_int("lookback_period");
        }
        if (params.has("entry_z_score")) {
            config_.entry_z_score = params.get_double("entry_z_score");
        }
        if (params.has("hedge_ratio")) {
            config_.hedge_ratio = params.get_double("hedge_ratio");
        }
    }

    StrategyParams get_params() const override {
        StrategyParams params;
        params.set("lookback_period", config_.lookback_period);
        params.set("entry_z_score", config_.entry_z_score);
        params.set("hedge_ratio", config_.hedge_ratio);
        return params;
    }

    // ==================== 查询 ====================

    /**
     * @brief 是否有持仓
     * @return 有持仓返回 true
     */
    bool has_position() const {
        return position1_ != 0 || position2_ != 0;
    }

    /**
     * @brief 获取当前 Z-score
     * @return Z-score 值
     */
    double current_z_score() const { return z_score_; }

    /**
     * @brief 获取当前价差
     * @return 价差值
     */
    double current_spread() const { return calculate_spread(); }

private:
    /**
     * @brief 计算价差
     * @return 价差值
     */
    double calculate_spread() const {
        double price1 = prices_.at(symbol1_);
        double price2 = prices_.at(symbol2_);
        return price1 - price2 * config_.hedge_ratio;
    }

    /**
     * @brief 更新 Z-score
     * @return 成功返回 true
     */
    bool update_z_score() {
        if (spreads_.size() < static_cast<size_t>(config_.lookback_period)) {
            return false;
        }

        // 计算均值
        double sum = 0;
        for (size_t i = spreads_.size() - config_.lookback_period;
             i < spreads_.size(); ++i) {
            sum += spreads_[i];
        }
        double mean = sum / config_.lookback_period;

        // 计算标准差
        double variance = 0;
        for (size_t i = spreads_.size() - config_.lookback_period;
             i < spreads_.size(); ++i) {
            double diff = spreads_[i] - mean;
            variance += diff * diff;
        }
        variance /= config_.lookback_period;
        double std_dev = std::sqrt(variance);

        // 计算 Z-score
        if (std_dev > 0) {
            z_score_ = (spreads_.back() - mean) / std_dev;
        } else {
            z_score_ = 0;
        }

        spread_mean_ = mean;
        spread_std_ = std_dev;

        return true;
    }

    /**
     * @brief 生成交易信号
     */
    void generate_signals() {
        if (!has_position()) {
            // 入场信号
            if (z_score_ > config_.entry_z_score) {
                // 价差过大，做空价差
                LOG_INFO("StatArb entry: Short spread, z-score=" + std::to_string(z_score_));
                sell(symbol1_, config_.trade_size);
                buy(symbol2_, config_.trade_size * config_.hedge_ratio);
            } else if (z_score_ < -config_.entry_z_score) {
                // 价差过小，做多价差
                LOG_INFO("StatArb entry: Long spread, z-score=" + std::to_string(z_score_));
                buy(symbol1_, config_.trade_size);
                sell(symbol2_, config_.trade_size * config_.hedge_ratio);
            }
        } else {
            // 出场信号
            if (std::abs(z_score_) < config_.exit_z_score) {
                LOG_INFO("StatArb exit: Z-score normalized");
                close_position();
            }
            // 止损信号
            else if (std::abs(z_score_) > config_.stop_z_score) {
                LOG_WARN("StatArb stop loss: Z-score=" + std::to_string(z_score_));
                close_position();
            }
        }
    }

    /**
     * @brief 买入
     * @param symbol 品种代码
     * @param quantity 数量
     */
    void buy(const std::string& symbol, int64_t quantity) {
        auto order = order_manager_.create_order(
            symbol, Side::BUY, OrderType::MARKET, 0, quantity
        );
        order_manager_.send_order(order.order_id);
    }

    /**
     * @brief 卖出
     * @param symbol 品种代码
     * @param quantity 数量
     */
    void sell(const std::string& symbol, int64_t quantity) {
        auto order = order_manager_.create_order(
            symbol, Side::SELL, OrderType::MARKET, 0, quantity
        );
        order_manager_.send_order(order.order_id);
    }

    /**
     * @brief 平仓
     */
    void close_position() {
        if (position1_ > 0) {
            sell(symbol1_, position1_);
        } else if (position1_ < 0) {
            buy(symbol1_, -position1_);
        }

        if (position2_ > 0) {
            sell(symbol2_, position2_);
        } else if (position2_ < 0) {
            buy(symbol2_, -position2_);
        }

        position1_ = 0;
        position2_ = 0;
    }

    StatArbConfig config_;                ///< 策略配置
    OrderManager& order_manager_;         ///< 订单管理器
    std::string symbol1_;                 ///< 品种 1
    std::string symbol2_;                 ///< 品种 2

    int64_t position1_ = 0;              ///< 品种 1 持仓
    int64_t position2_ = 0;              ///< 品种 2 持仓
    double realized_pnl_ = 0.0;          ///< 已实现盈亏

    std::map<std::string, double> prices_;  ///< 最新价格
    std::vector<double> spreads_;           ///< 价差历史

    double z_score_ = 0.0;               ///< 当前 Z-score
    double spread_mean_ = 0.0;           ///< 价差均值
    double spread_std_ = 0.0;            ///< 价差标准差
};

} // namespace hft
