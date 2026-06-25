/**
 * @file arbitrage.h
 * @brief 套利策略
 *
 * 实现跨市场套利和跨期套利策略。
 */

#pragma once

#include "strategy.h"
#include "order/order_manager.h"
#include "market_data/order_book.h"
#include "core/logger.h"

#include <cmath>
#include <map>

namespace hft {

/**
 * @struct ArbitrageConfig
 * @brief 套利策略配置
 */
struct ArbitrageConfig {
    double entry_threshold = 0.002;   ///< 入场阈值（价差百分比）
    double exit_threshold = 0.0005;   ///< 出场阈值
    double stop_loss_threshold = 0.01;  ///< 止损阈值
    int64_t max_position = 500;       ///< 最大持仓
    double max_loss = 5000.0;         ///< 最大亏损
    double hedge_ratio = 1.0;         ///< 对冲比率
    int64_t trade_size = 100;         ///< 交易数量
};

/**
 * @class ArbitrageStrategy
 * @brief 套利策略
 *
 * 策略逻辑：
 * 1. 监控两个相关资产的价格
 * 2. 计算价差
 * 3. 当价差超过阈值时开仓
 * 4. 当价差回归时平仓
 */
class ArbitrageStrategy : public Strategy {
public:
    /**
     * @brief 构造函数
     * @param config 策略配置
     * @param order_manager 订单管理器
     * @param symbol1 品种 1
     * @param symbol2 品种 2
     */
    ArbitrageStrategy(const ArbitrageConfig& config, OrderManager& order_manager,
                      const std::string& symbol1, const std::string& symbol2)
        : Strategy("Arbitrage"), config_(config), order_manager_(order_manager),
          symbol1_(symbol1), symbol2_(symbol2),
          position1_(0), position2_(0), realized_pnl_(0) {}

    /**
     * @brief 析构函数
     */
    ~ArbitrageStrategy() override = default;

    // ==================== 生命周期 ====================

    void on_init() override {
        LOG_INFO("ArbitrageStrategy initialized: " + symbol1_ + " / " + symbol2_);
        set_state(StrategyState::INITED);
    }

    void on_start() override {
        LOG_INFO("ArbitrageStrategy started");
        set_state(StrategyState::RUNNING);
    }

    void on_stop() override {
        LOG_INFO("ArbitrageStrategy stopped");
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
        double price1 = prices_[symbol1_];
        double price2 = prices_[symbol2_];
        double spread = price1 - price2 * config_.hedge_ratio;
        double spread_pct = spread / price1;

        // 更新价差历史
        spread_history_.push_back(spread_pct);
        if (spread_history_.size() > 1000) {
            spread_history_.erase(spread_history_.begin());
        }

        // 计算统计量
        update_statistics();

        // 生成交易信号
        if (!has_position()) {
            check_entry_signal(spread_pct);
        } else {
            check_exit_signal(spread_pct);
            check_stop_loss(spread_pct);
        }
    }

    void on_order(const Order& order) override {
        if (order.is_filled()) {
            LOG_INFO("Arbitrage order filled: " + order.to_string());
        }
    }

    void on_trade(const Trade& trade) override {
        // 更新持仓
        if (trade.symbol == symbol1_) {
            position1_ += (trade.side == Side::BUY) ? trade.quantity : -trade.quantity;
        } else if (trade.symbol == symbol2_) {
            position2_ += (trade.side == Side::BUY) ? trade.quantity : -trade.quantity;
        }

        LOG_INFO("Arbitrage trade: " + trade.to_string() +
                 " Position1: " + std::to_string(position1_) +
                 " Position2: " + std::to_string(position2_));
    }

    // ==================== 配置 ====================

    void set_params(const StrategyParams& params) override {
        if (params.has("entry_threshold")) {
            config_.entry_threshold = params.get_double("entry_threshold");
        }
        if (params.has("exit_threshold")) {
            config_.exit_threshold = params.get_double("exit_threshold");
        }
        if (params.has("hedge_ratio")) {
            config_.hedge_ratio = params.get_double("hedge_ratio");
        }
    }

    StrategyParams get_params() const override {
        StrategyParams params;
        params.set("entry_threshold", config_.entry_threshold);
        params.set("exit_threshold", config_.exit_threshold);
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
     * @brief 获取当前价差
     * @return 当前价差百分比
     */
    double current_spread() const {
        if (prices_.find(symbol1_) == prices_.end() ||
            prices_.find(symbol2_) == prices_.end()) {
            return 0.0;
        }
        double price1 = prices_.at(symbol1_);
        double price2 = prices_.at(symbol2_);
        return (price1 - price2 * config_.hedge_ratio) / price1;
    }

private:
    /**
     * @brief 更新统计量
     */
    void update_statistics() {
        if (spread_history_.size() < 20) return;

        // 计算均值和标准差
        double sum = 0;
        for (double s : spread_history_) {
            sum += s;
        }
        spread_mean_ = sum / spread_history_.size();

        double variance = 0;
        for (double s : spread_history_) {
            variance += (s - spread_mean_) * (s - spread_mean_);
        }
        spread_std_ = std::sqrt(variance / spread_history_.size());
    }

    /**
     * @brief 检查入场信号
     * @param spread_pct 价差百分比
     */
    void check_entry_signal(double spread_pct) {
        if (spread_history_.size() < 20) return;

        // 计算 Z-score
        double z_score = (spread_pct - spread_mean_) / spread_std_;

        // 价差过大，做空价差
        if (z_score > config_.entry_threshold / spread_std_) {
            LOG_INFO("Arbitrage entry: Short spread, z-score=" + std::to_string(z_score));
            sell(symbol1_, config_.trade_size);
            buy(symbol2_, config_.trade_size * config_.hedge_ratio);
        }
        // 价差过小，做多价差
        else if (z_score < -config_.entry_threshold / spread_std_) {
            LOG_INFO("Arbitrage entry: Long spread, z-score=" + std::to_string(z_score));
            buy(symbol1_, config_.trade_size);
            sell(symbol2_, config_.trade_size * config_.hedge_ratio);
        }
    }

    /**
     * @brief 检查出场信号
     * @param spread_pct 价差百分比
     */
    void check_exit_signal(double spread_pct) {
        // 价差回归到正常范围，平仓
        if (std::abs(spread_pct - spread_mean_) < config_.exit_threshold) {
            LOG_INFO("Arbitrage exit: Spread normalized");
            close_position();
        }
    }

    /**
     * @brief 检查止损
     * @param spread_pct 价差百分比
     */
    void check_stop_loss(double spread_pct) {
        // 价差继续扩大，触发止损
        if (std::abs(spread_pct) > config_.stop_loss_threshold) {
            LOG_WARN("Arbitrage stop loss triggered");
            close_position();
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

    ArbitrageConfig config_;              ///< 策略配置
    OrderManager& order_manager_;         ///< 订单管理器
    std::string symbol1_;                 ///< 品种 1
    std::string symbol2_;                 ///< 品种 2

    int64_t position1_ = 0;              ///< 品种 1 持仓
    int64_t position2_ = 0;              ///< 品种 2 持仓
    double realized_pnl_ = 0.0;          ///< 已实现盈亏

    std::map<std::string, double> prices_;  ///< 最新价格
    std::vector<double> spread_history_;    ///< 价差历史

    double spread_mean_ = 0.0;           ///< 价差均值
    double spread_std_ = 0.0;            ///< 价差标准差
};

} // namespace hft
