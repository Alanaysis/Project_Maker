/**
 * @file order_router.h
 * @brief 订单路由
 *
 * 订单路由和交易所连接管理。
 */

#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <functional>
#include <memory>
#include <mutex>

#include "order.h"
#include "core/logger.h"

namespace hft {

/**
 * @enum ExchangeType
 * @brief 交易所类型
 */
enum class ExchangeType {
    STOCK,      ///< 股票交易所
    FUTURES,    ///< 期货交易所
    OPTIONS,    ///< 期权交易所
    FOREX,      ///< 外汇交易所
    CRYPTO      ///< 加密货币交易所
};

/**
 * @struct ExchangeConfig
 * @brief 交易所配置
 */
struct ExchangeConfig {
    std::string name;           ///< 交易所名称
    ExchangeType type;          ///< 交易所类型
    std::string host;           ///< 主机地址
    uint16_t port;              ///< 端口号
    std::string protocol;       ///< 协议类型
    std::string account;        ///< 账户
    std::string api_key;        ///< API Key
    std::string api_secret;     ///< API Secret
    bool enabled;               ///< 是否启用

    ExchangeConfig()
        : type(ExchangeType::STOCK), port(0), enabled(true) {}
};

/**
 * @class ExchangeConnection
 * @brief 交易所连接
 */
class ExchangeConnection {
public:
    /**
     * @brief 构造函数
     * @param config 交易所配置
     */
    explicit ExchangeConnection(const ExchangeConfig& config)
        : config_(config), connected_(false) {}

    /**
     * @brief 连接交易所
     * @return 成功返回 true
     */
    virtual bool connect() {
        LOG_INFO("Connecting to exchange: " + config_.name);
        connected_ = true;
        return true;
    }

    /**
     * @brief 断开连接
     */
    virtual void disconnect() {
        LOG_INFO("Disconnecting from exchange: " + config_.name);
        connected_ = false;
    }

    /**
     * @brief 发送订单
     * @param order 订单
     * @return 成功返回 true
     */
    virtual bool send_order(const Order& order) {
        if (!connected_) {
            LOG_ERROR("Not connected to exchange: " + config_.name);
            return false;
        }

        LOG_INFO("Sending order to " + config_.name + ": " + order.to_string());
        return true;
    }

    /**
     * @brief 取消订单
     * @param order_id 订单 ID
     * @return 成功返回 true
     */
    virtual bool cancel_order(const std::string& order_id) {
        if (!connected_) {
            LOG_ERROR("Not connected to exchange: " + config_.name);
            return false;
        }

        LOG_INFO("Cancelling order on " + config_.name + ": " + order_id);
        return true;
    }

    /**
     * @brief 是否已连接
     * @return 连接状态
     */
    bool is_connected() const {
        return connected_;
    }

    /**
     * @brief 获取配置
     * @return 配置引用
     */
    const ExchangeConfig& config() const {
        return config_;
    }

protected:
    ExchangeConfig config_;          ///< 交易所配置
    bool connected_;                 ///< 连接状态
};

/**
 * @class OrderRouter
 * @brief 订单路由器
 *
 * 根据策略和市场条件选择最优的交易所进行订单路由。
 */
class OrderRouter {
public:
    using ExecutionCallback = std::function<void(const ExecutionReport&)>;

    /**
     * @brief 构造函数
     */
    OrderRouter() = default;

    /**
     * @brief 析构函数
     */
    ~OrderRouter() = default;

    /**
     * @brief 添加交易所连接
     * @param config 交易所配置
     * @return 成功返回 true
     */
    bool add_exchange(const ExchangeConfig& config) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto connection = std::make_shared<ExchangeConnection>(config);
        if (!connection->connect()) {
            LOG_ERROR("Failed to connect to exchange: " + config.name);
            return false;
        }

        exchanges_[config.name] = connection;
        LOG_INFO("Added exchange: " + config.name);
        return true;
    }

    /**
     * @brief 移除交易所连接
     * @param name 交易所名称
     */
    void remove_exchange(const std::string& name) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = exchanges_.find(name);
        if (it != exchanges_.end()) {
            it->second->disconnect();
            exchanges_.erase(it);
            LOG_INFO("Removed exchange: " + name);
        }
    }

    /**
     * @brief 路由订单
     * @param order 订单
     * @param exchange_name 交易所名称（可选）
     * @return 成功返回 true
     */
    bool route_order(const Order& order, const std::string& exchange_name = "") {
        std::lock_guard<std::mutex> lock(mutex_);

        // 选择交易所
        std::shared_ptr<ExchangeConnection> exchange;
        if (!exchange_name.empty()) {
            auto it = exchanges_.find(exchange_name);
            if (it == exchanges_.end()) {
                LOG_ERROR("Exchange not found: " + exchange_name);
                return false;
            }
            exchange = it->second;
        } else {
            exchange = select_best_exchange(order);
        }

        if (!exchange) {
            LOG_ERROR("No available exchange for order: " + order.order_id);
            return false;
        }

        // 发送订单
        return exchange->send_order(order);
    }

    /**
     * @brief 取消订单
     * @param order_id 订单 ID
     * @param exchange_name 交易所名称
     * @return 成功返回 true
     */
    bool cancel_order(const std::string& order_id, const std::string& exchange_name) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = exchanges_.find(exchange_name);
        if (it == exchanges_.end()) {
            LOG_ERROR("Exchange not found: " + exchange_name);
            return false;
        }

        return it->second->cancel_order(order_id);
    }

    /**
     * @brief 获取所有交易所
     * @return 交易所名称列表
     */
    std::vector<std::string> get_exchanges() const {
        std::lock_guard<std::mutex> lock(mutex_);

        std::vector<std::string> result;
        for (const auto& [name, exchange] : exchanges_) {
            result.push_back(name);
        }
        return result;
    }

    /**
     * @brief 获取交易所连接
     * @param name 交易所名称
     * @return 连接指针
     */
    std::shared_ptr<ExchangeConnection> get_exchange(const std::string& name) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = exchanges_.find(name);
        return (it != exchanges_.end()) ? it->second : nullptr;
    }

    /**
     * @brief 设置执行回调
     * @param callback 回调函数
     */
    void set_execution_callback(ExecutionCallback callback) {
        execution_callback_ = std::move(callback);
    }

private:
    /**
     * @brief 选择最优交易所
     * @param order 订单
     * @return 最优交易所连接
     */
    std::shared_ptr<ExchangeConnection> select_best_exchange(const Order& order) {
        // 简单实现：返回第一个可用的交易所
        // 实际实现需要考虑延迟、费用、流动性等因素
        for (const auto& [name, exchange] : exchanges_) {
            if (exchange->is_connected()) {
                return exchange;
            }
        }
        return nullptr;
    }

    mutable std::mutex mutex_;  ///< 互斥锁
    std::unordered_map<std::string, std::shared_ptr<ExchangeConnection>> exchanges_;  ///< 交易所连接
    ExecutionCallback execution_callback_;  ///< 执行回调
};

} // namespace hft
