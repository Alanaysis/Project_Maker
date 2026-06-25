/**
 * @file risk_analyzer.h
 * @brief 风险分析
 *
 * 计算风险指标，包括 VaR、CVaR、压力测试等。
 */

#pragma once

#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>

#include "core/logger.h"

namespace hft {

/**
 * @class RiskAnalyzer
 * @brief 风险分析器
 *
 * 计算各种风险指标：
 * - VaR (Value at Risk)
 * - CVaR (Conditional VaR)
 * - 压力测试
 * - 情景分析
 */
class RiskAnalyzer {
public:
    /**
     * @brief 构造函数
     * @param confidence_level 置信水平
     */
    explicit RiskAnalyzer(double confidence_level = 0.95)
        : confidence_level_(confidence_level) {}

    /**
     * @brief 析构函数
     */
    ~RiskAnalyzer() = default;

    /**
     * @brief 添加收益数据
     * @param returns 收益率列表
     */
    void add_returns(const std::vector<double>& returns) {
        returns_.insert(returns_.end(), returns.begin(), returns.end());
    }

    /**
     * @brief 计算 VaR
     * @param confidence 置信水平
     * @return VaR 值
     */
    double calculate_var(double confidence = 0.0) const {
        if (returns_.empty()) return 0.0;

        double conf = (confidence > 0) ? confidence : confidence_level_;

        // 排序
        std::vector<double> sorted_returns = returns_;
        std::sort(sorted_returns.begin(), sorted_returns.end());

        // 计算分位数
        size_t index = static_cast<size_t>((1.0 - conf) * sorted_returns.size());
        if (index >= sorted_returns.size()) {
            index = sorted_returns.size() - 1;
        }

        return -sorted_returns[index];
    }

    /**
     * @brief 计算 CVaR
     * @param confidence 置信水平
     * @return CVaR 值
     */
    double calculate_cvar(double confidence = 0.0) const {
        if (returns_.empty()) return 0.0;

        double conf = (confidence > 0) ? confidence : confidence_level_;

        // 排序
        std::vector<double> sorted_returns = returns_;
        std::sort(sorted_returns.begin(), sorted_returns.end());

        // 计算分位数
        size_t index = static_cast<size_t>((1.0 - conf) * sorted_returns.size());
        if (index >= sorted_returns.size()) {
            index = sorted_returns.size() - 1;
        }

        // 计算 CVaR（VaR 以下的平均值）
        double sum = 0;
        for (size_t i = 0; i <= index; ++i) {
            sum += sorted_returns[i];
        }

        return -sum / (index + 1);
    }

    /**
     * @brief 计算波动率
     * @return 年化波动率
     */
    double calculate_volatility() const {
        if (returns_.size() < 2) return 0.0;

        // 计算标准差
        double mean = std::accumulate(returns_.begin(), returns_.end(), 0.0)
                     / returns_.size();

        double variance = 0;
        for (double r : returns_) {
            variance += (r - mean) * (r - mean);
        }
        variance /= (returns_.size() - 1);

        // 年化波动率
        return std::sqrt(variance) * std::sqrt(252.0);
    }

    /**
     * @brief 计算贝塔系数
     * @param benchmark_returns 基准收益率
     * @return 贝塔系数
     */
    double calculate_beta(const std::vector<double>& benchmark_returns) const {
        if (returns_.size() != benchmark_returns.size() || returns_.empty()) {
            return 0.0;
        }

        // 计算协方差
        double mean_return = std::accumulate(returns_.begin(), returns_.end(), 0.0)
                            / returns_.size();
        double mean_benchmark = std::accumulate(benchmark_returns.begin(),
                                               benchmark_returns.end(), 0.0)
                               / benchmark_returns.size();

        double covariance = 0;
        double benchmark_variance = 0;

        for (size_t i = 0; i < returns_.size(); ++i) {
            double diff_return = returns_[i] - mean_return;
            double diff_benchmark = benchmark_returns[i] - mean_benchmark;

            covariance += diff_return * diff_benchmark;
            benchmark_variance += diff_benchmark * diff_benchmark;
        }

        covariance /= (returns_.size() - 1);
        benchmark_variance /= (benchmark_returns.size() - 1);

        if (benchmark_variance == 0) return 0.0;

        return covariance / benchmark_variance;
    }

    /**
     * @brief 计算信息比率
     * @param benchmark_returns 基准收益率
     * @return 信息比率
     */
    double calculate_information_ratio(const std::vector<double>& benchmark_returns) const {
        if (returns_.size() != benchmark_returns.size() || returns_.empty()) {
            return 0.0;
        }

        // 计算超额收益
        std::vector<double> excess_returns;
        for (size_t i = 0; i < returns_.size(); ++i) {
            excess_returns.push_back(returns_[i] - benchmark_returns[i]);
        }

        // 计算平均超额收益
        double mean_excess = std::accumulate(excess_returns.begin(),
                                            excess_returns.end(), 0.0)
                            / excess_returns.size();

        // 计算跟踪误差
        double variance = 0;
        for (double r : excess_returns) {
            variance += (r - mean_excess) * (r - mean_excess);
        }
        variance /= (excess_returns.size() - 1);
        double tracking_error = std::sqrt(variance);

        if (tracking_error == 0) return 0.0;

        return mean_excess / tracking_error * std::sqrt(252.0);
    }

    /**
     * @brief 压力测试
     * @param scenarios 情景列表
     * @return 情景结果
     */
    std::vector<double> stress_test(const std::vector<double>& scenarios) const {
        std::vector<double> results;

        for (double scenario : scenarios) {
            // 简化实现：假设线性影响
            double impact = scenario * calculate_volatility();
            results.push_back(impact);
        }

        return results;
    }

    /**
     * @brief 生成风险报告
     * @return 报告字符串
     */
    std::string generate_report() const {
        std::ostringstream oss;
        oss << "=== Risk Analysis Report ===\n";
        oss << "Confidence Level: " << (confidence_level_ * 100) << "%\n";
        oss << "VaR (95%): " << (calculate_var(0.95) * 100) << "%\n";
        oss << "VaR (99%): " << (calculate_var(0.99) * 100) << "%\n";
        oss << "CVaR (95%): " << (calculate_cvar(0.95) * 100) << "%\n";
        oss << "CVaR (99%): " << (calculate_cvar(0.99) * 100) << "%\n";
        oss << "Volatility: " << (calculate_volatility() * 100) << "%\n";
        return oss.str();
    }

private:
    double confidence_level_;         ///< 置信水平
    std::vector<double> returns_;     ///< 收益率数据
};

} // namespace hft
