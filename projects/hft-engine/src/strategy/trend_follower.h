/**
 * @file trend_follower.h
 * @brief 趋势跟踪策略
 *
 * 实现基于均线的趋势跟踪策略。
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
 * @struct TrendFollowerConfig
 * @brief 趋势策略配置
 */
struct TrendFollowerConfig {
    int fast_period = 10;             ///< 快速均线周期
    int slow_period = 30;             ///< 慢速均线周期
    double entry_threshold = 0.001;   ///< 入场阈值
    double exit_threshold = 0.0005;   ///< 出场阈值
    double stop_loss_pct = 0.02;      ///< 止损百分比
    double take_profit_pct = 0.05;    ///< 止盈百分比
    int64_t trade_size = 100;         ///< 交易数量
    int64_t max_position = 500;       ///< 最大持仓
};

/**
 * @class TrendFollower
 * @brief 趋势跟踪策略
 *
 * 策略逻辑：
 * 1. 计算快速和慢速均线
 * 2. 当快速均线上穿慢速均线时做多
 * 3. 当快速均线下穿慢速均线时做空
 * 4. 使用止损止盈管理风险
 */
class TrendFollower : public Strategy {
public:
    /**
     * @brief 构造函数
     * @param config 策略配置
     * @param order_manager 订单管理器
     * @param symbol 品种代码
     */
    TrendFollower(const TrendFollowerConfig& config, OrderManager& order_manager,
                  const std::string& symbol)
        : Strategy("TrendFollower"), config_(config), order_manager_(order_manager),
          symbol_(symbol), position_(0), entry_price_(0), realized_pnl_(0) {}

    /**
     * @brief 析构函数
     */
    ~TrendFollower() override = default;

    // ==================== 生命周期 ====================

    void on_init() override {
        LOG_INFO("TrendFollower initialized: " + symbol_);
        set_state(StrategyState::INITED);
    }

    void on_start() override {
        LOG_INFO("TrendFollower started");
        set_state(StrategyState::RUNNING);
    }

    void on_stop() override {
        LOG_INFO("TrendFollower stopped");
        close_position();
        set_state(StrategyState::STOPPED);
    }

    // ==================== 数据回调 ====================

    void on_tick(const Tick& tick) override {
        if (!is_running()) return;

        // 更新价格历史
        prices_.push_back(tick.last_price);
        if (prices_.size() > static_cast<size_t>(config_.slow_period * 2)) {
            prices_.erase(prices_.begin());
        }

        // 计算均线
        if (!update_moving_averages()) return;

        // 检查止损止盈
        if (position_ != 0) {
            check_stop_loss(tick.last_price);
            check_take_profit(tick.last_price);
        }

        // 生成交易信号
        generate_signals(tick.last_price);
    }

    void on_order(const Order& order) override {
        if (order.is_filled()) {
            LOG_INFO("TrendFollower order filled: " + order.to_string());
        }
    }

    void on_trade(const Trade& trade) override {
        // 更新持仓
        if (trade.side == Side::BUY) {
            position_ += trade.quantity;
            if (position_ == trade.quantity) {
                entry_price_ = trade.price;
            }
        } else {
            position_ -= trade.quantity;
            if (position_ == 0) {
                // 计算盈亏
                double pnl = (trade.price - entry_price_) * trade.quantity;
                realized_pnl_ += pnl;
                LOG_INFO("TrendFollower trade PnL: " + std::to_string(pnl));
            }
        }

        LOG_INFO("TrendFollower trade: " + trade.to_string() +
                 " Position: " + std::to_string(position_));
    }

    // ==================== 配置 ====================

    void set_params(const StrategyParams& params) override {
        if (params.has("fast_period")) {
            config_.fast_period = params.get_int("fast_period");
        }
        if (params.has("slow_period")) {
            config_.slow_period = params.get_int("slow_period");
        }
        if (params.has("stop_loss_pct")) {
            config_.stop_loss_pct = params.get_double("stop_loss_pct");
        }
    }

    StrategyParams get_params() const override {
        StrategyParams params;
        params.set("fast_period", config_.fast_period);
        params.set("slow_period", config_.slow_period);
        params.set("stop_loss_pct", config_.stop_loss_pct);
        return params;
    }

    // ==================== 查询 ====================

    /**
     * @brief 获取当前持仓
     * @return 持仓数量
     */
    int64_t position() const { return position_; }

    /**
     * @brief 获取已实现盈亏
     * @return 已实现盈亏
     */
    double realized_pnl() const { return realized_pnl_; }

    /**
     * @brief 获取快速均线值
     * @return 快速均线值
     */
    double fast_ma() const { return fast_ma_; }

    /**
     * @brief 获取慢速均线值
     * @return 慢速均线值
     */
    double slow_ma() const { return slow_ma_; }

private:
    /**
     * @brief 计算均线
     * @return 成功返回 true
     */
    bool update_moving_averages() {
        if (prices_.size() < static_cast<size_t>(config_.slow_period)) {
            return false;
        }

        // 计算快速均线
        fast_ma_ = calculate_ma(config_.fast_period);

        // 计算慢速均线
        slow_ma_ = calculate_ma(config_.slow_period);

        return true;
    }

    /**
     * @brief 计算简单移动平均
     * @param period 周期
     * @return 均线值
     */
    double calculate_ma(int period) const {
        if (prices_.size() < static_cast<size_t>(period)) {
            return 0.0;
        }

        double sum = 0;
        for (size_t i = prices_.size() - period; i < prices_.size(); ++i) {
            sum += prices_[i];
        }
        return sum / period;
    }

    /**
     * @brief 生成交易信号
     * @param price 当前价格
     */
    void generate_signals(double price) {
        if (fast_ma_ == 0 || slow_ma_ == 0) return;

        double ma_diff = (fast_ma_ - slow_ma_) / slow_ma_;

        // 金叉：快速均线上穿慢速均线
        if (ma_diff > config_.entry_threshold && position_ <= 0) {
            // 平空仓
            if (position_ < 0) {
                buy(-position_);
            }
            // 开多仓
            if (position_ == 0) {
                buy(config_.trade_size);
            }
        }
        // 死叉：快速均线下穿慢速均线
        else if (ma_diff < -config_.entry_threshold && position_ >= 0) {
            // 平多仓
            if (position_ > 0) {
                sell(position_);
            }
            // 开空仓
            if (position_ == 0) {
                sell(config_.trade_size);
            }
        }
        // 出场信号
        else if (std::abs(ma_diff) < config_.exit_threshold && position_ != 0) {
            close_position();
        }
    }

    /**
     * @brief 检查止损
     * @param price 当前价格
     */
    void check_stop_loss(double price) {
        if (position_ == 0 || entry_price_ == 0) return;

        double pnl_pct = 0;
        if (position_ > 0) {
            pnl_pct = (price - entry_price_) / entry_price_;
        } else {
            pnl_pct = (entry_price_ - price) / entry_price_;
        }

        if (pnl_pct < -config_.stop_loss_pct) {
            LOG_WARN("TrendFollower stop loss triggered: " + std::to_string(pnl_pct));
            close_position();
        }
    }

    /**
     * @brief 检查止盈
     * @param price 当前价格
     */
    void check_take_profit(double price) {
        if (position_ == 0 || entry_price_ == 0) return;

        double pnl_pct = 0;
        if (position_ > 0) {
            pnl_pct = (price - entry_price_) / entry_price_;
        } else {
            pnl_pct = (entry_price_ - price) / entry_price_;
        }

        if (pnl_pct > config_.take_profit_pct) {
            LOG_INFO("TrendFollower take profit triggered: " + std::to_string(pnl_pct));
            close_position();
        }
    }

    /**
     * @brief 买入
     * @param quantity 数量
     */
    void buy(int64_t quantity) {
        auto order = order_manager_.create_order(
            symbol_, Side::BUY, OrderType::MARKET, 0, quantity
        );
        order_manager_.send_order(order.order_id);
    }

    /**
     * @brief 卖出
     * @param quantity 数量
     */
    void sell(int64_t quantity) {
        auto order = order_manager_.create_order(
            symbol_, Side::SELL, OrderType::MARKET, 0, quantity
        );
        order_manager_.send_order(order.order_id);
    }

    /**
     * @brief 平仓
     */
    void close_position() {
        if (position_ > 0) {
            sell(position_);
        } else if (position_ < 0) {
            buy(-position_);
        }
    }

    TrendFollowerConfig config_;          ///< 策略配置
    OrderManager& order_manager_;         ///< 订单管理器
    std::string symbol_;                  ///< 品种代码

    int64_t position_ = 0;               ///< 当前持仓
    double entry_price_ = 0.0;           ///< 入场价格
    double realized_pnl_ = 0.0;          ///< 已实现盈亏

    std::vector<double> prices_;          ///< 价格历史
    double fast_ma_ = 0.0;               ///< 快速均线
    double slow_ma_ = 0.0;               ///< 慢速均线
};

} // namespace hft
