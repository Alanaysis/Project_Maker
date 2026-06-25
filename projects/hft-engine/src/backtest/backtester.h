/**
 * @file backtester.h
 * @brief 回测引擎
 *
 * 事件驱动的回测框架，支持策略回测和性能分析。
 */

#pragma once

#include <string>
#include <vector>
#include <functional>
#include <memory>
#include <unordered_map>

#include "market_data/tick.h"
#include "market_data/data_replay.h"
#include "order/order_manager.h"
#include "strategy/strategy.h"
#include "risk/risk_manager.h"
#include "core/logger.h"

namespace hft {

/**
 * @struct BacktestConfig
 * @brief 回测配置
 */
struct BacktestConfig {
    std::string data_file;          ///< 数据文件
    Timestamp start_time;           ///< 开始时间
    Timestamp end_time;             ///< 结束时间
    double initial_capital = 1000000.0;  ///< 初始资金
    double commission_rate = 0.001; ///< 手续费率
    double slippage = 0.0001;       ///< 滑点
    bool enable_short = true;       ///< 允许做空
};

/**
 * @struct BacktestResult
 * @brief 回测结果
 */
struct BacktestResult {
    double total_return = 0.0;      ///< 总收益率
    double annual_return = 0.0;     ///< 年化收益率
    double sharpe_ratio = 0.0;      ///< 夏普比率
    double max_drawdown = 0.0;      ///< 最大回撤
    double win_rate = 0.0;          ///< 胜率
    double profit_factor = 0.0;     ///< 盈亏比
    int64_t total_trades = 0;       ///< 总交易次数
    int64_t winning_trades = 0;     ///< 盈利次数
    int64_t losing_trades = 0;      ///< 亏损次数
    double avg_win = 0.0;           ///< 平均盈利
    double avg_loss = 0.0;          ///< 平均亏损
    double max_consecutive_wins = 0;  ///< 最大连续盈利
    double max_consecutive_losses = 0;  ///< 最大连续亏损
};

/**
 * @class Backtester
 * @brief 回测引擎
 *
 * 特性：
 * - 事件驱动回测
 * - 真实模拟（滑点、手续费）
 * - 性能分析
 * - 风险分析
 */
class Backtester {
public:
    /**
     * @brief 构造函数
     * @param config 回测配置
     */
    explicit Backtester(const BacktestConfig& config)
        : config_(config), current_capital_(config.initial_capital),
          peak_capital_(config.initial_capital) {}

    /**
     * @brief 析构函数
     */
    ~Backtester() = default;

    /**
     * @brief 设置策略
     * @param strategy 策略指针
     */
    void set_strategy(std::unique_ptr<Strategy> strategy) {
        strategy_ = std::move(strategy);
    }

    /**
     * @brief 运行回测
     * @return 回测结果
     */
    BacktestResult run() {
        LOG_INFO("Starting backtest...");

        // 初始化
        if (strategy_) {
            strategy_->on_init();
            strategy_->on_start();
        }

        // 创建数据回放引擎
        ReplayConfig replay_config;
        replay_config.data_file = config_.data_file;
        replay_config.start_time = config_.start_time;
        replay_config.end_time = config_.end_time;

        DataReplayEngine replay(replay_config);

        // 设置回调
        replay.set_tick_callback([this](const Tick& tick) {
            on_tick(tick);
        });

        replay.set_completion_callback([this]() {
            on_backtest_complete();
        });

        // 运行回放
        replay.start();

        // 等待完成
        while (replay.is_running()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }

        // 停止策略
        if (strategy_) {
            strategy_->on_stop();
        }

        // 计算结果
        return calculate_result();
    }

    /**
     * @brief 获取当前资金
     * @return 当前资金
     */
    double current_capital() const {
        return current_capital_;
    }

    /**
     * @brief 获取交易记录
     * @return 交易记录列表
     */
    std::vector<Trade> trades() const {
        return trades_;
    }

private:
    /**
     * @brief 处理 Tick 数据
     * @param tick Tick 数据
     */
    void on_tick(const Tick& tick) {
        // 更新价格
        current_prices_[tick.symbol] = tick.last_price;

        // 分发给策略
        if (strategy_) {
            strategy_->on_tick(tick);
        }
    }

    /**
     * @brief 处理订单
     * @param order 订单
     */
    void on_order(const Order& order) {
        if (order.is_filled()) {
            // 模拟成交
            Trade trade;
            trade.trade_id = "T-" + std::to_string(trades_.size() + 1);
            trade.order_id = order.order_id;
            trade.symbol = order.symbol;
            trade.side = order.side;
            trade.price = order.price * (1.0 + (order.side == Side::BUY ?
                                                 config_.slippage : -config_.slippage));
            trade.quantity = order.quantity;
            trade.commission = trade.price * trade.quantity * config_.commission_rate;
            trade.timestamp = Timestamp::now();

            // 更新资金
            double trade_value = trade.price * trade.quantity;
            if (trade.side == Side::BUY) {
                current_capital_ -= trade_value + trade.commission;
            } else {
                current_capital_ += trade_value - trade.commission;
            }

            // 记录交易
            trades_.push_back(trade);

            // 分发给策略
            if (strategy_) {
                strategy_->on_trade(trade);
            }
        }
    }

    /**
     * @brief 回测完成回调
     */
    void on_backtest_complete() {
        LOG_INFO("Backtest completed");
    }

    /**
     * @brief 计算回测结果
     * @return 回测结果
     */
    BacktestResult calculate_result() const {
        BacktestResult result;

        if (trades_.empty()) {
            return result;
        }

        // 计算总收益
        result.total_return = (current_capital_ - config_.initial_capital) /
                             config_.initial_capital;

        // 计算交易统计
        result.total_trades = trades_.size();

        double total_profit = 0;
        double total_loss = 0;
        int consecutive_wins = 0;
        int consecutive_losses = 0;
        int max_consecutive_wins = 0;
        int max_consecutive_losses = 0;

        for (const auto& trade : trades_) {
            double pnl = 0;
            if (trade.side == Side::SELL) {
                pnl = trade.price * trade.quantity - trade.commission;
            } else {
                pnl = -(trade.price * trade.quantity + trade.commission);
            }

            if (pnl > 0) {
                result.winning_trades++;
                total_profit += pnl;
                consecutive_wins++;
                consecutive_losses = 0;
                max_consecutive_wins = std::max(max_consecutive_wins, consecutive_wins);
            } else {
                result.losing_trades++;
                total_loss += std::abs(pnl);
                consecutive_losses++;
                consecutive_wins = 0;
                max_consecutive_losses = std::max(max_consecutive_losses, consecutive_losses);
            }
        }

        // 计算胜率
        if (result.total_trades > 0) {
            result.win_rate = static_cast<double>(result.winning_trades) /
                             result.total_trades;
        }

        // 计算盈亏比
        if (total_loss > 0) {
            result.profit_factor = total_profit / total_loss;
        }

        // 计算平均盈亏
        if (result.winning_trades > 0) {
            result.avg_win = total_profit / result.winning_trades;
        }
        if (result.losing_trades > 0) {
            result.avg_loss = total_loss / result.losing_trades;
        }

        result.max_consecutive_wins = max_consecutive_wins;
        result.max_consecutive_losses = max_consecutive_losses;

        return result;
    }

    BacktestConfig config_;           ///< 回测配置
    std::unique_ptr<Strategy> strategy_;  ///< 策略
    double current_capital_;          ///< 当前资金
    double peak_capital_;             ///< 峰值资金
    std::vector<Trade> trades_;       ///< 交易记录
    std::unordered_map<std::string, double> current_prices_;  ///< 当前价格
};

} // namespace hft
