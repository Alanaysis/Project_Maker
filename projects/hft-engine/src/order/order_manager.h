/**
 * @file order_manager.h
 * @brief 订单管理器
 *
 * 管理订单的完整生命周期，包括创建、发送、确认、成交、取消等。
 */

#pragma once

#include <string>
#include <unordered_map>
#include <vector>
#include <functional>
#include <mutex>
#include <memory>
#include <atomic>

#include "order.h"
#include "core/timestamp.h"
#include "core/logger.h"

namespace hft {

/**
 * @class OrderManager
 * @brief 订单管理器
 *
 * 特性：
 * - 订单生命周期管理
 * - 订单状态跟踪
 * - 成交匹配
 * - 线程安全
 */
class OrderManager {
public:
    using OrderCallback = std::function<void(const Order&)>;
    using TradeCallback = std::function<void(const Trade&)>;

    /**
     * @brief 构造函数
     */
    OrderManager() : next_order_id_(1) {}

    /**
     * @brief 析构函数
     */
    ~OrderManager() = default;

    /**
     * @brief 创建订单
     * @param symbol 品种代码
     * @param side 买卖方向
     * @param type 订单类型
     * @param price 价格
     * @param quantity 数量
     * @return 订单对象
     */
    Order create_order(const std::string& symbol, Side side, OrderType type,
                       double price, int64_t quantity) {
        std::lock_guard<std::mutex> lock(mutex_);

        Order order;
        order.order_id = generate_order_id();
        order.symbol = symbol;
        order.side = side;
        order.type = type;
        order.status = OrderStatus::CREATED;
        order.price = price;
        order.quantity = quantity;
        order.remaining_quantity = quantity;
        order.create_time = Timestamp::now();

        // 存储订单
        orders_[order.order_id] = order;

        LOG_INFO("Order created: " + order.to_string());

        // 通知回调
        if (order_callback_) {
            order_callback_(order);
        }

        return order;
    }

    /**
     * @brief 发送订单
     * @param order_id 订单 ID
     * @return 成功返回 true
     */
    bool send_order(const std::string& order_id) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = orders_.find(order_id);
        if (it == orders_.end()) {
            LOG_ERROR("Order not found: " + order_id);
            return false;
        }

        auto& order = it->second;
        if (order.status != OrderStatus::CREATED) {
            LOG_ERROR("Invalid order status for sending: " + order.to_string());
            return false;
        }

        order.status = OrderStatus::SENT;
        order.send_time = Timestamp::now();

        LOG_INFO("Order sent: " + order.to_string());

        if (order_callback_) {
            order_callback_(order);
        }

        return true;
    }

    /**
     * @brief 确认订单
     * @param order_id 订单 ID
     * @return 成功返回 true
     */
    bool acknowledge_order(const std::string& order_id) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = orders_.find(order_id);
        if (it == orders_.end()) {
            LOG_ERROR("Order not found: " + order_id);
            return false;
        }

        auto& order = it->second;
        if (order.status != OrderStatus::SENT) {
            LOG_ERROR("Invalid order status for acknowledgment: " + order.to_string());
            return false;
        }

        order.status = OrderStatus::ACKNOWLEDGED;
        order.ack_time = Timestamp::now();

        LOG_INFO("Order acknowledged: " + order.to_string());

        if (order_callback_) {
            order_callback_(order);
        }

        return true;
    }

    /**
     * @brief 处理成交回报
     * @param report 执行报告
     * @return 成功返回 true
     */
    bool process_fill(const ExecutionReport& report) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = orders_.find(report.order_id);
        if (it == orders_.end()) {
            LOG_ERROR("Order not found: " + report.order_id);
            return false;
        }

        auto& order = it->second;

        // 更新订单状态
        order.filled_quantity += report.last_quantity;
        order.remaining_quantity = order.quantity - order.filled_quantity;

        // 更新平均成交价
        if (order.avg_fill_price == 0.0) {
            order.avg_fill_price = report.last_price;
        } else {
            double total_value = order.avg_fill_price * (order.filled_quantity - report.last_quantity)
                               + report.last_price * report.last_quantity;
            order.avg_fill_price = total_value / order.filled_quantity;
        }

        // 更新状态
        if (order.remaining_quantity == 0) {
            order.status = OrderStatus::FILLED;
            order.fill_time = Timestamp::now();
        } else {
            order.status = OrderStatus::PARTIALLY_FILLED;
        }

        // 创建成交记录
        Trade trade;
        trade.trade_id = report.exec_id;
        trade.order_id = order.order_id;
        trade.symbol = order.symbol;
        trade.side = order.side;
        trade.price = report.last_price;
        trade.quantity = report.last_quantity;
        trade.timestamp = report.timestamp;

        trades_[trade.trade_id] = trade;

        LOG_INFO("Order filled: " + order.to_string());

        if (order_callback_) {
            order_callback_(order);
        }
        if (trade_callback_) {
            trade_callback_(trade);
        }

        return true;
    }

    /**
     * @brief 取消订单
     * @param order_id 订单 ID
     * @return 成功返回 true
     */
    bool cancel_order(const std::string& order_id) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = orders_.find(order_id);
        if (it == orders_.end()) {
            LOG_ERROR("Order not found: " + order_id);
            return false;
        }

        auto& order = it->second;
        if (order.is_terminal()) {
            LOG_ERROR("Cannot cancel terminal order: " + order.to_string());
            return false;
        }

        order.status = OrderStatus::CANCELLED;
        order.cancel_time = Timestamp::now();

        LOG_INFO("Order cancelled: " + order.to_string());

        if (order_callback_) {
            order_callback_(order);
        }

        return true;
    }

    /**
     * @brief 拒绝订单
     * @param order_id 订单 ID
     * @param reason 拒绝原因
     * @return 成功返回 true
     */
    bool reject_order(const std::string& order_id, const std::string& reason) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = orders_.find(order_id);
        if (it == orders_.end()) {
            LOG_ERROR("Order not found: " + order_id);
            return false;
        }

        auto& order = it->second;
        order.status = OrderStatus::REJECTED;
        order.reject_reason = reason;

        LOG_WARN("Order rejected: " + order.to_string() + " Reason: " + reason);

        if (order_callback_) {
            order_callback_(order);
        }

        return true;
    }

    /**
     * @brief 获取订单
     * @param order_id 订单 ID
     * @return 订单指针（不存在返回 nullptr）
     */
    Order* get_order(const std::string& order_id) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = orders_.find(order_id);
        return (it != orders_.end()) ? &it->second : nullptr;
    }

    /**
     * @brief 获取所有活跃订单
     * @return 活跃订单列表
     */
    std::vector<Order> get_active_orders() const {
        std::lock_guard<std::mutex> lock(mutex_);

        std::vector<Order> result;
        for (const auto& [id, order] : orders_) {
            if (order.is_active()) {
                result.push_back(order);
            }
        }
        return result;
    }

    /**
     * @brief 获取指定品种的订单
     * @param symbol 品种代码
     * @return 订单列表
     */
    std::vector<Order> get_orders_by_symbol(const std::string& symbol) const {
        std::lock_guard<std::mutex> lock(mutex_);

        std::vector<Order> result;
        for (const auto& [id, order] : orders_) {
            if (order.symbol == symbol) {
                result.push_back(order);
            }
        }
        return result;
    }

    /**
     * @brief 获取成交记录
     * @param order_id 订单 ID
     * @return 成交记录列表
     */
    std::vector<Trade> get_trades(const std::string& order_id) const {
        std::lock_guard<std::mutex> lock(mutex_);

        std::vector<Trade> result;
        for (const auto& [id, trade] : trades_) {
            if (trade.order_id == order_id) {
                result.push_back(trade);
            }
        }
        return result;
    }

    /**
     * @brief 获取所有成交记录
     * @return 成交记录列表
     */
    std::vector<Trade> get_all_trades() const {
        std::lock_guard<std::mutex> lock(mutex_);

        std::vector<Trade> result;
        for (const auto& [id, trade] : trades_) {
            result.push_back(trade);
        }
        return result;
    }

    /**
     * @brief 获取订单数量
     * @return 订单数量
     */
    size_t order_count() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return orders_.size();
    }

    /**
     * @brief 获取活跃订单数量
     * @return 活跃订单数量
     */
    size_t active_order_count() const {
        std::lock_guard<std::mutex> lock(mutex_);

        size_t count = 0;
        for (const auto& [id, order] : orders_) {
            if (order.is_active()) {
                count++;
            }
        }
        return count;
    }

    /**
     * @brief 设置订单回调
     * @param callback 回调函数
     */
    void set_order_callback(OrderCallback callback) {
        order_callback_ = std::move(callback);
    }

    /**
     * @brief 设置成交回调
     * @param callback 回调函数
     */
    void set_trade_callback(TradeCallback callback) {
        trade_callback_ = std::move(callback);
    }

    /**
     * @brief 清空所有订单
     */
    void clear() {
        std::lock_guard<std::mutex> lock(mutex_);
        orders_.clear();
        trades_.clear();
    }

private:
    /**
     * @brief 生成订单 ID
     * @return 订单 ID
     */
    std::string generate_order_id() {
        return "ORD-" + std::to_string(next_order_id_++);
    }

    mutable std::mutex mutex_;  ///< 互斥锁
    std::atomic<int64_t> next_order_id_;  ///< 下一个订单 ID

    std::unordered_map<std::string, Order> orders_;   ///< 订单映射
    std::unordered_map<std::string, Trade> trades_;   ///< 成交映射

    OrderCallback order_callback_;  ///< 订单回调
    TradeCallback trade_callback_;  ///< 成交回调
};

} // namespace hft
