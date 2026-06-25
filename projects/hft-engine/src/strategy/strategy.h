/**
 * @file strategy.h
 * @brief 策略基类
 *
 * 定义交易策略的基类接口，所有策略都需要继承此类。
 */

#pragma once

#include <string>
#include <unordered_map>
#include <variant>
#include <any>
#include <functional>

#include "market_data/tick.h"
#include "market_data/order_book.h"
#include "order/order.h"
#include "core/timestamp.h"

namespace hft {

/**
 * @class StrategyParams
 * @brief 策略参数
 */
class StrategyParams {
public:
    /**
     * @brief 设置整数参数
     * @param key 参数名
     * @param value 参数值
     */
    void set(const std::string& key, int value) {
        int_params_[key] = value;
    }

    /**
     * @brief 设置64位整数参数
     * @param key 参数名
     * @param value 参数值
     */
    void set(const std::string& key, int64_t value) {
        int_params_[key] = static_cast<int>(value);
    }

    /**
     * @brief 设置浮点参数
     * @param key 参数名
     * @param value 参数值
     */
    void set(const std::string& key, double value) {
        double_params_[key] = value;
    }

    /**
     * @brief 设置字符串参数
     * @param key 参数名
     * @param value 参数值
     */
    void set(const std::string& key, const std::string& value) {
        string_params_[key] = value;
    }

    /**
     * @brief 设置布尔参数
     * @param key 参数名
     * @param value 参数值
     */
    void set(const std::string& key, bool value) {
        bool_params_[key] = value;
    }

    /**
     * @brief 获取整数参数
     * @param key 参数名
     * @param default_value 默认值
     * @return 参数值
     */
    int get_int(const std::string& key, int default_value = 0) const {
        auto it = int_params_.find(key);
        return (it != int_params_.end()) ? it->second : default_value;
    }

    /**
     * @brief 获取浮点参数
     * @param key 参数名
     * @param default_value 默认值
     * @return 参数值
     */
    double get_double(const std::string& key, double default_value = 0.0) const {
        auto it = double_params_.find(key);
        return (it != double_params_.end()) ? it->second : default_value;
    }

    /**
     * @brief 获取字符串参数
     * @param key 参数名
     * @param default_value 默认值
     * @return 参数值
     */
    std::string get_string(const std::string& key, const std::string& default_value = "") const {
        auto it = string_params_.find(key);
        return (it != string_params_.end()) ? it->second : default_value;
    }

    /**
     * @brief 获取布尔参数
     * @param key 参数名
     * @param default_value 默认值
     * @return 参数值
     */
    bool get_bool(const std::string& key, bool default_value = false) const {
        auto it = bool_params_.find(key);
        return (it != bool_params_.end()) ? it->second : default_value;
    }

    /**
     * @brief 检查参数是否存在
     * @param key 参数名
     * @return 存在返回 true
     */
    bool has(const std::string& key) const {
        return int_params_.find(key) != int_params_.end() ||
               double_params_.find(key) != double_params_.end() ||
               string_params_.find(key) != string_params_.end() ||
               bool_params_.find(key) != bool_params_.end();
    }

private:
    std::unordered_map<std::string, int> int_params_;
    std::unordered_map<std::string, double> double_params_;
    std::unordered_map<std::string, std::string> string_params_;
    std::unordered_map<std::string, bool> bool_params_;
};

/**
 * @enum StrategyState
 * @brief 策略状态
 */
enum class StrategyState {
    CREATED,    ///< 已创建
    INITED,     ///< 已初始化
    RUNNING,    ///< 运行中
    PAUSED,     ///< 已暂停
    STOPPED,    ///< 已停止
    ERROR       ///< 错误
};

/**
 * @class Strategy
 * @brief 策略基类
 *
 * 所有交易策略都需要继承此类，并实现相应的虚函数。
 */
class Strategy {
public:
    /**
     * @brief 构造函数
     * @param name 策略名称
     */
    explicit Strategy(const std::string& name)
        : name_(name), state_(StrategyState::CREATED) {}

    /**
     * @brief 虚析构函数
     */
    virtual ~Strategy() = default;

    // ==================== 生命周期 ====================

    /**
     * @brief 初始化策略
     *
     * 在策略启动前调用，用于初始化资源。
     */
    virtual void on_init() = 0;

    /**
     * @brief 启动策略
     *
     * 策略开始运行。
     */
    virtual void on_start() = 0;

    /**
     * @brief 停止策略
     *
     * 策略停止运行。
     */
    virtual void on_stop() = 0;

    /**
     * @brief 暂停策略
     */
    virtual void on_pause() {
        state_ = StrategyState::PAUSED;
    }

    /**
     * @brief 恢复策略
     */
    virtual void on_resume() {
        state_ = StrategyState::RUNNING;
    }

    // ==================== 数据回调 ====================

    /**
     * @brief Tick 数据回调
     * @param tick Tick 数据
     */
    virtual void on_tick(const Tick& tick) = 0;

    /**
     * @brief K 线数据回调
     * @param bar K 线数据
     */
    virtual void on_bar(const Bar& bar) {
        (void)bar;
    }

    /**
     * @brief 订单簿更新回调
     * @param update 订单簿更新
     */
    virtual void on_order_book_update(const OrderBookUpdate& update) {
        (void)update;
    }

    /**
     * @brief 订单状态回调
     * @param order 订单
     */
    virtual void on_order(const Order& order) = 0;

    /**
     * @brief 成交回调
     * @param trade 成交记录
     */
    virtual void on_trade(const Trade& trade) = 0;

    // ==================== 配置 ====================

    /**
     * @brief 设置策略参数
     * @param params 策略参数
     */
    virtual void set_params(const StrategyParams& params) = 0;

    /**
     * @brief 获取策略参数
     * @return 策略参数
     */
    virtual StrategyParams get_params() const = 0;

    // ==================== 状态查询 ====================

    /**
     * @brief 获取策略名称
     * @return 策略名称
     */
    const std::string& name() const {
        return name_;
    }

    /**
     * @brief 获取策略状态
     * @return 策略状态
     */
    StrategyState state() const {
        return state_;
    }

    /**
     * @brief 策略是否运行中
     * @return 运行中返回 true
     */
    bool is_running() const {
        return state_ == StrategyState::RUNNING;
    }

protected:
    /**
     * @brief 设置策略状态
     * @param state 新状态
     */
    void set_state(StrategyState state) {
        state_ = state;
    }

    std::string name_;          ///< 策略名称
    StrategyState state_;       ///< 策略状态
};

/**
 * @class StrategyManager
 * @brief 策略管理器
 *
 * 管理所有策略的生命周期和事件分发。
 */
class StrategyManager {
public:
    /**
     * @brief 构造函数
     */
    StrategyManager() = default;

    /**
     * @brief 析构函数
     */
    ~StrategyManager() = default;

    /**
     * @brief 注册策略
     * @param strategy 策略指针
     */
    void register_strategy(std::unique_ptr<Strategy> strategy) {
        strategies_[strategy->name()] = std::move(strategy);
    }

    /**
     * @brief 初始化所有策略
     */
    void init_all() {
        for (auto& [name, strategy] : strategies_) {
            strategy->on_init();
        }
    }

    /**
     * @brief 启动所有策略
     */
    void start_all() {
        for (auto& [name, strategy] : strategies_) {
            strategy->on_start();
        }
    }

    /**
     * @brief 停止所有策略
     */
    void stop_all() {
        for (auto& [name, strategy] : strategies_) {
            strategy->on_stop();
        }
    }

    /**
     * @brief 分发 Tick 数据
     * @param tick Tick 数据
     */
    void on_tick(const Tick& tick) {
        for (auto& [name, strategy] : strategies_) {
            if (strategy->is_running()) {
                strategy->on_tick(tick);
            }
        }
    }

    /**
     * @brief 分发订单更新
     * @param order 订单
     */
    void on_order(const Order& order) {
        for (auto& [name, strategy] : strategies_) {
            if (strategy->is_running()) {
                strategy->on_order(order);
            }
        }
    }

    /**
     * @brief 分发成交回报
     * @param trade 成交记录
     */
    void on_trade(const Trade& trade) {
        for (auto& [name, strategy] : strategies_) {
            if (strategy->is_running()) {
                strategy->on_trade(trade);
            }
        }
    }

    /**
     * @brief 获取策略
     * @param name 策略名称
     * @return 策略指针
     */
    Strategy* get_strategy(const std::string& name) {
        auto it = strategies_.find(name);
        return (it != strategies_.end()) ? it->second.get() : nullptr;
    }

    /**
     * @brief 获取所有策略名称
     * @return 策略名称列表
     */
    std::vector<std::string> strategy_names() const {
        std::vector<std::string> names;
        for (const auto& [name, strategy] : strategies_) {
            names.push_back(name);
        }
        return names;
    }

    /**
     * @brief 获取策略数量
     * @return 策略数量
     */
    size_t count() const {
        return strategies_.size();
    }

private:
    std::unordered_map<std::string, std::unique_ptr<Strategy>> strategies_;  ///< 策略映射
};

} // namespace hft
