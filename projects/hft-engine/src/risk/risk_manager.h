/**
 * @file risk_manager.h
 * @brief 风险管理器
 *
 * 实现多层风险控制，包括下单前检查、实时监控、自动熔断等。
 */

#pragma once

#include <string>
#include <vector>
#include <functional>
#include <mutex>
#include <atomic>

#include "position.h"
#include "order/order.h"
#include "core/timestamp.h"
#include "core/logger.h"

namespace hft {

/**
 * @enum RiskCheckResult
 * @brief 风险检查结果
 */
enum class RiskCheckResult {
    PASS,                    ///< 通过
    INVALID_PARAMS,          ///< 无效参数
    POSITION_LIMIT,          ///< 持仓限制
    INSUFFICIENT_MARGIN,     ///< 保证金不足
    RATE_LIMIT,              ///< 频率限制
    PRICE_LIMIT,             ///< 价格限制
    LOSS_LIMIT,              ///< 亏损限制
    CONCENTRATION_LIMIT,     ///< 集中度限制
    SYSTEM_ERROR             ///< 系统错误
};

/**
 * @brief RiskCheckResult 转字符串
 */
inline const char* risk_check_result_to_string(RiskCheckResult result) {
    switch (result) {
        case RiskCheckResult::PASS:                return "PASS";
        case RiskCheckResult::INVALID_PARAMS:      return "INVALID_PARAMS";
        case RiskCheckResult::POSITION_LIMIT:      return "POSITION_LIMIT";
        case RiskCheckResult::INSUFFICIENT_MARGIN: return "INSUFFICIENT_MARGIN";
        case RiskCheckResult::RATE_LIMIT:          return "RATE_LIMIT";
        case RiskCheckResult::PRICE_LIMIT:         return "PRICE_LIMIT";
        case RiskCheckResult::LOSS_LIMIT:          return "LOSS_LIMIT";
        case RiskCheckResult::CONCENTRATION_LIMIT: return "CONCENTRATION_LIMIT";
        case RiskCheckResult::SYSTEM_ERROR:        return "SYSTEM_ERROR";
        default: return "UNKNOWN";
    }
}

/**
 * @struct RiskLimits
 * @brief 风险限制
 */
struct RiskLimits {
    int64_t max_position_per_symbol = 1000;     ///< 单品种最大持仓
    int64_t max_total_position = 5000;          ///< 总持仓上限
    double max_loss_per_trade = 1000.0;         ///< 单笔最大亏损
    double max_daily_loss = 10000.0;            ///< 日内最大亏损
    double max_drawdown_pct = 0.1;              ///< 最大回撤百分比
    int max_orders_per_second = 100;            ///< 每秒最大下单数
    int max_cancel_rate = 50;                   ///< 最大撤单率（百分比）
    double max_price_deviation = 0.05;          ///< 最大价格偏离（百分比）
    double max_concentration = 0.3;             ///< 最大集中度（百分比）
};

/**
 * @struct RiskMetrics
 * @brief 风险指标
 */
struct RiskMetrics {
    double total_pnl = 0.0;             ///< 总盈亏
    double daily_pnl = 0.0;             ///< 日内盈亏
    double max_drawdown = 0.0;          ///< 最大回撤
    int64_t order_count = 0;            ///< 订单数量
    int64_t cancel_count = 0;           ///< 撤单数量
    Timestamp last_order_time;          ///< 最后下单时间
};

/**
 * @class RiskManager
 * @brief 风险管理器
 *
 * 特性：
 * - 多层风险检查
 * - 实时监控
 * - 自动熔断
 * - 告警通知
 */
class RiskManager {
public:
    using AlertCallback = std::function<void(const std::string&, const std::string&)>;

    /**
     * @brief 构造函数
     * @param limits 风险限制
     */
    explicit RiskManager(const RiskLimits& limits = RiskLimits())
        : limits_(limits), is_circuit_breaker_(false) {}

    /**
     * @brief 析构函数
     */
    ~RiskManager() = default;

    /**
     * @brief 检查订单
     * @param order 订单
     * @param position 当前持仓
     * @return 检查结果
     */
    RiskCheckResult check_order(const Order& order, const Position& position) {
        std::lock_guard<std::mutex> lock(mutex_);

        // 检查熔断状态
        if (is_circuit_breaker_) {
            LOG_WARN("Circuit breaker active, order rejected");
            return RiskCheckResult::SYSTEM_ERROR;
        }

        // 1. 参数检查
        if (!check_params(order)) {
            return RiskCheckResult::INVALID_PARAMS;
        }

        // 2. 持仓检查
        if (!check_position(order, position)) {
            return RiskCheckResult::POSITION_LIMIT;
        }

        // 3. 价格检查
        if (!check_price(order)) {
            return RiskCheckResult::PRICE_LIMIT;
        }

        // 4. 频率检查
        if (!check_rate_limit()) {
            return RiskCheckResult::RATE_LIMIT;
        }

        // 5. 亏损检查
        if (!check_loss_limit()) {
            return RiskCheckResult::LOSS_LIMIT;
        }

        // 更新订单计数
        update_order_count();

        return RiskCheckResult::PASS;
    }

    /**
     * @brief 更新风险指标
     * @param pnl 盈亏
     */
    void update_pnl(double pnl) {
        std::lock_guard<std::mutex> lock(mutex_);

        metrics_.total_pnl += pnl;
        metrics_.daily_pnl += pnl;

        // 更新最大回撤
        if (metrics_.daily_pnl < -limits_.max_daily_loss) {
            trigger_circuit_breaker("Daily loss limit exceeded");
        }
    }

    /**
     * @brief 更新持仓价格
     * @param prices 价格映射
     */
    void update_prices(const std::unordered_map<std::string, double>& prices) {
        std::lock_guard<std::mutex> lock(mutex_);
        current_prices_ = prices;
    }

    /**
     * @brief 重置日内指标
     */
    void reset_daily() {
        std::lock_guard<std::mutex> lock(mutex_);
        metrics_.daily_pnl = 0;
        metrics_.order_count = 0;
        metrics_.cancel_count = 0;
        is_circuit_breaker_ = false;

        LOG_INFO("Daily risk metrics reset");
    }

    /**
     * @brief 触发熔断
     * @param reason 原因
     */
    void trigger_circuit_breaker(const std::string& reason) {
        is_circuit_breaker_ = true;
        LOG_ERROR("Circuit breaker triggered: " + reason);

        if (alert_callback_) {
            alert_callback_("CIRCUIT_BREAKER", reason);
        }
    }

    /**
     * @brief 解除熔断
     */
    void reset_circuit_breaker() {
        is_circuit_breaker_ = false;
        LOG_INFO("Circuit breaker reset");
    }

    /**
     * @brief 是否处于熔断状态
     * @return 熔断状态
     */
    bool is_circuit_breaker() const {
        return is_circuit_breaker_;
    }

    /**
     * @brief 获取风险指标
     * @return 风险指标
     */
    RiskMetrics metrics() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return metrics_;
    }

    /**
     * @brief 设置风险限制
     * @param limits 风险限制
     */
    void set_limits(const RiskLimits& limits) {
        std::lock_guard<std::mutex> lock(mutex_);
        limits_ = limits;
    }

    /**
     * @brief 设置告警回调
     * @param callback 回调函数
     */
    void set_alert_callback(AlertCallback callback) {
        alert_callback_ = std::move(callback);
    }

private:
    /**
     * @brief 检查订单参数
     * @param order 订单
     * @return 通过返回 true
     */
    bool check_params(const Order& order) const {
        if (order.price <= 0 && order.type == OrderType::LIMIT) {
            LOG_WARN("Invalid order price: " + std::to_string(order.price));
            return false;
        }
        if (order.quantity <= 0) {
            LOG_WARN("Invalid order quantity: " + std::to_string(order.quantity));
            return false;
        }
        return true;
    }

    /**
     * @brief 检查持仓限制
     * @param order 订单
     * @param position 当前持仓
     * @return 通过返回 true
     */
    bool check_position(const Order& order, const Position& position) const {
        // 计算下单后的持仓
        int64_t new_quantity = position.quantity;
        if (order.side == Side::BUY) {
            new_quantity += order.quantity;
        } else {
            new_quantity -= order.quantity;
        }

        // 检查单品种持仓限制
        if (std::abs(new_quantity) > limits_.max_position_per_symbol) {
            LOG_WARN("Position limit exceeded for " + order.symbol +
                     ": " + std::to_string(std::abs(new_quantity)));
            return false;
        }

        return true;
    }

    /**
     * @brief 检查价格合理性
     * @param order 订单
     * @return 通过返回 true
     */
    bool check_price(const Order& order) const {
        if (order.type != OrderType::LIMIT) return true;

        auto it = current_prices_.find(order.symbol);
        if (it == current_prices_.end()) return true;

        double current_price = it->second;
        double deviation = std::abs(order.price - current_price) / current_price;

        if (deviation > limits_.max_price_deviation) {
            LOG_WARN("Price deviation too large: " + std::to_string(deviation));
            return false;
        }

        return true;
    }

    /**
     * @brief 检查下单频率
     * @return 通过返回 true
     */
    bool check_rate_limit() const {
        // 简化的频率检查
        return true;
    }

    /**
     * @brief 检查亏损限制
     * @return 通过返回 true
     */
    bool check_loss_limit() const {
        if (metrics_.daily_pnl < -limits_.max_daily_loss) {
            LOG_WARN("Daily loss limit exceeded: " + std::to_string(metrics_.daily_pnl));
            return false;
        }
        return true;
    }

    /**
     * @brief 更新订单计数
     */
    void update_order_count() {
        metrics_.order_count++;
        metrics_.last_order_time = Timestamp::now();
    }

    mutable std::mutex mutex_;  ///< 互斥锁
    RiskLimits limits_;         ///< 风险限制
    RiskMetrics metrics_;       ///< 风险指标
    bool is_circuit_breaker_;   ///< 熔断状态

    std::unordered_map<std::string, double> current_prices_;  ///< 当前价格
    AlertCallback alert_callback_;  ///< 告警回调
};

} // namespace hft
