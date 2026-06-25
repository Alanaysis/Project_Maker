/**
 * @file performance.h
 * @brief 性能分析
 *
 * 计算回测的性能指标，包括夏普比率、最大回撤等。
 */

#pragma once

#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>

#include "order/order.h"
#include "core/logger.h"

namespace hft {

/**
 * @class PerformanceAnalyzer
 * @brief 性能分析器
 *
 * 计算各种性能指标：
 * - 收益率
 * - 夏普比率
 * - 最大回撤
 * - 胜率
 * - 盈亏比
 */
class PerformanceAnalyzer {
public:
    /**
     * @brief 构造函数
     * @param initial_capital 初始资金
     * @param risk_free_rate 无风险利率
     */
    explicit PerformanceAnalyzer(double initial_capital = 1000000.0,
                                double risk_free_rate = 0.03)
        : initial_capital_(initial_capital), risk_free_rate_(risk_free_rate) {}

    /**
     * @brief 析构函数
     */
    ~PerformanceAnalyzer() = default;

    /**
     * @brief 添加每日收益
     * @param daily_return 每日收益率
     */
    void add_daily_return(double daily_return) {
        daily_returns_.push_back(daily_return);

        // 更新资金曲线
        double capital = capital_curve_.empty() ? initial_capital_ : capital_curve_.back();
        capital_curve_.push_back(capital * (1.0 + daily_return));
    }

    /**
     * @brief 添加交易记录
     * @param trade 交易记录
     */
    void add_trade(const Trade& trade) {
        trades_.push_back(trade);
    }

    /**
     * @brief 计算总收益率
     * @return 总收益率
     */
    double total_return() const {
        if (capital_curve_.empty()) return 0.0;
        return (capital_curve_.back() - initial_capital_) / initial_capital_;
    }

    /**
     * @brief 计算年化收益率
     * @return 年化收益率
     */
    double annual_return() const {
        if (daily_returns_.empty()) return 0.0;

        double total = total_return();
        double years = daily_returns_.size() / 252.0;  // 假设 252 个交易日

        if (years <= 0) return 0.0;
        return std::pow(1.0 + total, 1.0 / years) - 1.0;
    }

    /**
     * @brief 计算夏普比率
     * @return 夏普比率
     */
    double sharpe_ratio() const {
        if (daily_returns_.size() < 2) return 0.0;

        // 计算平均收益
        double mean = std::accumulate(daily_returns_.begin(), daily_returns_.end(), 0.0)
                     / daily_returns_.size();

        // 计算标准差
        double variance = 0;
        for (double r : daily_returns_) {
            variance += (r - mean) * (r - mean);
        }
        variance /= (daily_returns_.size() - 1);
        double std_dev = std::sqrt(variance);

        if (std_dev == 0) return 0.0;

        // 年化夏普比率
        double daily_rf = risk_free_rate_ / 252.0;
        return (mean - daily_rf) / std_dev * std::sqrt(252.0);
    }

    /**
     * @brief 计算索提诺比率
     * @return 索提诺比率
     */
    double sortino_ratio() const {
        if (daily_returns_.size() < 2) return 0.0;

        // 计算平均收益
        double mean = std::accumulate(daily_returns_.begin(), daily_returns_.end(), 0.0)
                     / daily_returns_.size();

        // 计算下行标准差
        double downside_variance = 0;
        int downside_count = 0;
        for (double r : daily_returns_) {
            if (r < 0) {
                downside_variance += r * r;
                downside_count++;
            }
        }

        if (downside_count == 0) return 0.0;

        downside_variance /= downside_count;
        double downside_std = std::sqrt(downside_variance);

        if (downside_std == 0) return 0.0;

        // 年化索提诺比率
        double daily_rf = risk_free_rate_ / 252.0;
        return (mean - daily_rf) / downside_std * std::sqrt(252.0);
    }

    /**
     * @brief 计算最大回撤
     * @return 最大回撤（百分比）
     */
    double max_drawdown() const {
        if (capital_curve_.empty()) return 0.0;

        double peak = capital_curve_[0];
        double max_dd = 0.0;

        for (double capital : capital_curve_) {
            if (capital > peak) {
                peak = capital;
            }
            double dd = (peak - capital) / peak;
            if (dd > max_dd) {
                max_dd = dd;
            }
        }

        return max_dd;
    }

    /**
     * @brief 计算卡尔玛比率
     * @return 卡尔玛比率
     */
    double calmar_ratio() const {
        double dd = max_drawdown();
        if (dd == 0) return 0.0;
        return annual_return() / dd;
    }

    /**
     * @brief 计算胜率
     * @return 胜率
     */
    double win_rate() const {
        if (trades_.empty()) return 0.0;

        int wins = 0;
        // 简化计算：假设配对交易
        for (size_t i = 0; i < trades_.size(); i += 2) {
            if (i + 1 < trades_.size()) {
                double entry_price = trades_[i].price;
                double exit_price = trades_[i + 1].price;

                if (trades_[i].side == Side::BUY) {
                    if (exit_price > entry_price) wins++;
                } else {
                    if (exit_price < entry_price) wins++;
                }
            }
        }

        return static_cast<double>(wins) / (trades_.size() / 2);
    }

    /**
     * @brief 计算盈亏比
     * @return 盈亏比
     */
    double profit_factor() const {
        double total_profit = 0;
        double total_loss = 0;

        for (size_t i = 0; i < trades_.size(); i += 2) {
            if (i + 1 < trades_.size()) {
                double pnl = 0;
                if (trades_[i].side == Side::BUY) {
                    pnl = (trades_[i + 1].price - trades_[i].price) * trades_[i].quantity;
                } else {
                    pnl = (trades_[i].price - trades_[i + 1].price) * trades_[i].quantity;
                }

                if (pnl > 0) {
                    total_profit += pnl;
                } else {
                    total_loss += std::abs(pnl);
                }
            }
        }

        if (total_loss == 0) return 0.0;
        return total_profit / total_loss;
    }

    /**
     * @brief 获取资金曲线
     * @return 资金曲线
     */
    const std::vector<double>& capital_curve() const {
        return capital_curve_;
    }

    /**
     * @brief 获取每日收益
     * @return 每日收益列表
     */
    const std::vector<double>& daily_returns() const {
        return daily_returns_;
    }

    /**
     * @brief 生成报告
     * @return 报告字符串
     */
    std::string generate_report() const {
        std::ostringstream oss;
        oss << "=== Performance Report ===\n";
        oss << "Total Return: " << (total_return() * 100) << "%\n";
        oss << "Annual Return: " << (annual_return() * 100) << "%\n";
        oss << "Sharpe Ratio: " << sharpe_ratio() << "\n";
        oss << "Sortino Ratio: " << sortino_ratio() << "\n";
        oss << "Max Drawdown: " << (max_drawdown() * 100) << "%\n";
        oss << "Calmar Ratio: " << calmar_ratio() << "\n";
        oss << "Win Rate: " << (win_rate() * 100) << "%\n";
        oss << "Profit Factor: " << profit_factor() << "\n";
        oss << "Total Trades: " << trades_.size() << "\n";
        return oss.str();
    }

private:
    double initial_capital_;          ///< 初始资金
    double risk_free_rate_;           ///< 无风险利率
    std::vector<double> daily_returns_;  ///< 每日收益
    std::vector<double> capital_curve_;  ///< 资金曲线
    std::vector<Trade> trades_;       ///< 交易记录
};

} // namespace hft
