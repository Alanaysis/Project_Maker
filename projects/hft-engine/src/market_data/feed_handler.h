/**
 * @file feed_handler.h
 * @brief 行情接收器
 *
 * 接收和处理市场数据流，支持多交易所接入。
 */

#pragma once

#include <string>
#include <functional>
#include <thread>
#include <atomic>
#include <vector>
#include <memory>
#include <unordered_map>

#include "tick.h"
#include "order_book.h"
#include "core/timestamp.h"
#include "core/logger.h"

namespace hft {

/**
 * @enum FeedStatus
 * @brief 行情状态
 */
enum class FeedStatus {
    DISCONNECTED,   ///< 未连接
    CONNECTING,     ///< 连接中
    CONNECTED,      ///< 已连接
    RECONNECTING,   ///< 重连中
    ERROR           ///< 错误
};

/**
 * @struct FeedConfig
 * @brief 行情配置
 */
struct FeedConfig {
    std::string name;               ///< 行情名称
    std::string host;               ///< 主机地址
    uint16_t port;                  ///< 端口号
    std::string protocol;           ///< 协议类型（tcp/udp）
    std::vector<std::string> symbols;  ///< 订阅品种
    bool auto_reconnect;            ///< 自动重连
    int reconnect_interval_ms;      ///< 重连间隔（毫秒）
    int heartbeat_interval_ms;      ///< 心跳间隔（毫秒）

    FeedConfig()
        : port(0), protocol("tcp"), auto_reconnect(true),
          reconnect_interval_ms(1000), heartbeat_interval_ms(5000) {}
};

/**
 * @class FeedHandler
 * @brief 行情处理器
 *
 * 特性：
 * - 支持多交易所同时接入
 * - 自动重连机制
 * - 心跳检测
 * - 回调通知
 */
class FeedHandler {
public:
    using TickCallback = std::function<void(const Tick&)>;
    using StatusCallback = std::function<void(const std::string&, FeedStatus)>;

    /**
     * @brief 构造函数
     * @param config 行情配置
     */
    explicit FeedHandler(const FeedConfig& config)
        : config_(config), status_(FeedStatus::DISCONNECTED) {}

    /**
     * @brief 析构函数
     */
    virtual ~FeedHandler() {
        stop();
    }

    /**
     * @brief 启动行情接收
     * @return 成功返回 true
     */
    virtual bool start() {
        if (status_ == FeedStatus::CONNECTED) {
            return true;
        }

        LOG_INFO("Starting feed handler: " + config_.name);
        status_ = FeedStatus::CONNECTING;

        // 启动接收线程
        running_ = true;
        receive_thread_ = std::thread(&FeedHandler::receive_loop, this);

        // 启动心跳线程
        heartbeat_thread_ = std::thread(&FeedHandler::heartbeat_loop, this);

        status_ = FeedStatus::CONNECTED;
        notify_status(status_);

        return true;
    }

    /**
     * @brief 停止行情接收
     */
    virtual void stop() {
        if (status_ == FeedStatus::DISCONNECTED) {
            return;
        }

        LOG_INFO("Stopping feed handler: " + config_.name);
        running_ = false;

        if (receive_thread_.joinable()) {
            receive_thread_.join();
        }
        if (heartbeat_thread_.joinable()) {
            heartbeat_thread_.join();
        }

        status_ = FeedStatus::DISCONNECTED;
        notify_status(status_);
    }

    /**
     * @brief 订阅品种
     * @param symbol 品种代码
     */
    virtual void subscribe(const std::string& symbol) {
        config_.symbols.push_back(symbol);
    }

    /**
     * @brief 取消订阅
     * @param symbol 品种代码
     */
    virtual void unsubscribe(const std::string& symbol) {
        auto it = std::find(config_.symbols.begin(), config_.symbols.end(), symbol);
        if (it != config_.symbols.end()) {
            config_.symbols.erase(it);
        }
    }

    /**
     * @brief 设置 Tick 回调
     * @param callback 回调函数
     */
    void set_tick_callback(TickCallback callback) {
        tick_callback_ = std::move(callback);
    }

    /**
     * @brief 设置状态回调
     * @param callback 回调函数
     */
    void set_status_callback(StatusCallback callback) {
        status_callback_ = std::move(callback);
    }

    /**
     * @brief 获取行情状态
     * @return 行情状态
     */
    FeedStatus status() const {
        return status_;
    }

    /**
     * @brief 获取行情名称
     * @return 行情名称
     */
    const std::string& name() const {
        return config_.name;
    }

    /**
     * @brief 获取最后活动时间
     * @return 最后活动时间
     */
    Timestamp last_activity() const {
        return last_activity_;
    }

protected:
    /**
     * @brief 处理接收到的数据
     * @param data 数据指针
     * @param size 数据大小
     */
    virtual void process_data(const char* data, size_t size) {
        // 基类实现：解析数据并生成 Tick
        // 子类可以覆盖此方法以支持不同的协议
        (void)data;
        (void)size;
    }

    /**
     * @brief 通知 Tick
     * @param tick Tick 数据
     */
    void notify_tick(const Tick& tick) {
        last_activity_ = Timestamp::now();
        if (tick_callback_) {
            tick_callback_(tick);
        }
    }

    /**
     * @brief 通知状态变化
     * @param status 新状态
     */
    void notify_status(FeedStatus status) {
        if (status_callback_) {
            status_callback_(config_.name, status);
        }
    }

    /**
     * @brief 处理连接错误
     */
    void handle_error() {
        LOG_ERROR("Feed handler error: " + config_.name);
        status_ = FeedStatus::ERROR;
        notify_status(status_);

        if (config_.auto_reconnect) {
            reconnect();
        }
    }

    /**
     * @brief 重新连接
     */
    void reconnect() {
        LOG_INFO("Reconnecting feed handler: " + config_.name);
        status_ = FeedStatus::RECONNECTING;
        notify_status(status_);

        // 等待重连间隔
        std::this_thread::sleep_for(
            std::chrono::milliseconds(config_.reconnect_interval_ms)
        );

        // 尝试重新启动
        if (running_) {
            start();
        }
    }

    FeedConfig config_;                  ///< 行情配置
    std::atomic<FeedStatus> status_;     ///< 行情状态
    std::atomic<bool> running_{false};   ///< 运行标志
    Timestamp last_activity_;            ///< 最后活动时间

    std::thread receive_thread_;         ///< 接收线程
    std::thread heartbeat_thread_;       ///< 心跳线程

    TickCallback tick_callback_;         ///< Tick 回调
    StatusCallback status_callback_;     ///< 状态回调

private:
    /**
     * @brief 接收循环
     */
    void receive_loop() {
        while (running_) {
            // 模拟接收数据
            std::this_thread::sleep_for(std::chrono::milliseconds(1));

            // 更新最后活动时间
            last_activity_ = Timestamp::now();
        }
    }

    /**
     * @brief 心跳循环
     */
    void heartbeat_loop() {
        while (running_) {
            std::this_thread::sleep_for(
                std::chrono::milliseconds(config_.heartbeat_interval_ms)
            );

            // 检查是否超时
            auto now = Timestamp::now();
            auto elapsed = now - last_activity_;
            if (elapsed > config_.heartbeat_interval_ms * 2 * 1000000) {
                LOG_WARN("Heartbeat timeout: " + config_.name);
                handle_error();
            }
        }
    }
};

/**
 * @class SimulatedFeedHandler
 * @brief 模拟行情处理器
 *
 * 用于测试和回测的模拟行情源。
 */
class SimulatedFeedHandler : public FeedHandler {
public:
    /**
     * @brief 构造函数
     * @param name 行情名称
     */
    explicit SimulatedFeedHandler(const std::string& name = "Simulated")
        : FeedHandler(create_sim_config(name)) {}

private:
    /**
     * @brief 创建模拟配置
     */
    static FeedConfig create_sim_config(const std::string& name) {
        FeedConfig config;
        config.name = name;
        config.host = "localhost";
        config.port = 0;
        config.protocol = "simulated";
        config.auto_reconnect = false;
        config.reconnect_interval_ms = 0;
        config.heartbeat_interval_ms = 0;
        return config;
    }

public:

    /**
     * @brief 生成模拟 Tick
     * @param symbol 品种代码
     * @param base_price 基础价格
     * @return 生成的 Tick
     */
    Tick generate_tick(const std::string& symbol, double base_price) {
        Tick tick;
        tick.symbol = symbol;
        tick.timestamp = Timestamp::now();
        tick.type = TickType::TRADE;

        // 随机价格波动
        double random_change = (rand() % 100 - 50) / 10000.0;  // +/- 0.5%
        tick.last_price = base_price * (1.0 + random_change);
        tick.last_quantity = rand() % 100 + 1;

        // 生成买卖盘
        double spread = base_price * 0.001;  // 0.1% 价差
        tick.bid_price = tick.last_price - spread / 2;
        tick.ask_price = tick.last_price + spread / 2;
        tick.bid_quantity = rand() % 1000 + 100;
        tick.ask_quantity = rand() % 1000 + 100;

        tick.volume = rand() % 10000;
        tick.turnover = tick.volume * tick.last_price;

        notify_tick(tick);
        return tick;
    }
};

} // namespace hft
