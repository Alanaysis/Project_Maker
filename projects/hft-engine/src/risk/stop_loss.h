/**
 * @file stop_loss.h
 * @brief 止损止盈
 *
 * 实现止损止盈功能，包括固定止损、追踪止损、时间止损等。
 */

#pragma once

#include <string>
#include <unordered_map>
#include <vector>
#include <mutex>
#include <functional>

#include "position.h"
#include "order/order.h"
#include "core/logger.h"

namespace hft {

/**
 * @enum StopType
 * @brief 止损类型
 */
enum class StopType {
    FIXED,          ///< 固定止损
    TRAILING,       ///< 追踪止损
    TIME,           ///< 时间止损
    VOLATILITY      ///< 波动率止损
};

/**
 * @struct StopOrder
 * @brief 止损止盈订单
 */
struct StopOrder {
    std::string id;                 ///< 止损单 ID
    std::string symbol;             ///< 品种代码
    Side side;                      ///< 买卖方向
    StopType type;                  ///< 止损类型
    double trigger_price;           ///< 触发价格
    double trailing_offset;         ///< 追踪偏移
    int64_t quantity;               ///< 数量
    bool triggered;                 ///< 是否已触发
    Timestamp create_time;          ///< 创建时间
    Timestamp trigger_time;         ///< 触发时间

    /**
     * @brief 默认构造函数
     */
    StopOrder()
        : side(Side::BUY), type(StopType::FIXED), trigger_price(0),
          trailing_offset(0), quantity(0), triggered(false) {}
};

/**
 * @class StopLossManager
 * @brief 止损止盈管理器
 *
 * 特性：
 * - 固定止损止盈
 * - 追踪止损
 * - 时间止损
 * - 波动率止损
 */
class StopLossManager {
public:
    using TriggerCallback = std::function<void(const StopOrder&)>;

    /**
     * @brief 构造函数
     */
    StopLossManager() = default;

    /**
     * @brief 析构函数
     */
    ~StopLossManager() = default;

    /**
     * @brief 添加固定止损
     * @param symbol 品种代码
     * @param side 买卖方向
     * @param trigger_price 触发价格
     * @param quantity 数量
     * @return 止损单 ID
     */
    std::string add_fixed_stop(const std::string& symbol, Side side,
                               double trigger_price, int64_t quantity) {
        std::lock_guard<std::mutex> lock(mutex_);

        StopOrder stop;
        stop.id = generate_id();
        stop.symbol = symbol;
        stop.side = side;
        stop.type = StopType::FIXED;
        stop.trigger_price = trigger_price;
        stop.quantity = quantity;
        stop.create_time = Timestamp::now();

        stops_[stop.id] = stop;

        LOG_INFO("Fixed stop added: " + stop.id + " " + symbol +
                 " Trigger: " + std::to_string(trigger_price));
        return stop.id;
    }

    /**
     * @brief 添加追踪止损
     * @param symbol 品种代码
     * @param side 买卖方向
     * @param trailing_offset 追踪偏移
     * @param quantity 数量
     * @return 止损单 ID
     */
    std::string add_trailing_stop(const std::string& symbol, Side side,
                                  double trailing_offset, int64_t quantity) {
        std::lock_guard<std::mutex> lock(mutex_);

        StopOrder stop;
        stop.id = generate_id();
        stop.symbol = symbol;
        stop.side = side;
        stop.type = StopType::TRAILING;
        stop.trailing_offset = trailing_offset;
        stop.quantity = quantity;
        stop.create_time = Timestamp::now();

        stops_[stop.id] = stop;

        LOG_INFO("Trailing stop added: " + stop.id + " " + symbol +
                 " Offset: " + std::to_string(trailing_offset));
        return stop.id;
    }

    /**
     * @brief 更新价格并检查触发
     * @param symbol 品种代码
     * @param price 当前价格
     */
    void update_price(const std::string& symbol, double price) {
        std::lock_guard<std::mutex> lock(mutex_);

        for (auto& [id, stop] : stops_) {
            if (stop.symbol != symbol || stop.triggered) continue;

            bool should_trigger = false;

            switch (stop.type) {
                case StopType::FIXED:
                    should_trigger = check_fixed_stop(stop, price);
                    break;
                case StopType::TRAILING:
                    update_trailing_stop(stop, price);
                    should_trigger = check_trailing_stop(stop, price);
                    break;
                default:
                    break;
            }

            if (should_trigger) {
                stop.triggered = true;
                stop.trigger_time = Timestamp::now();

                LOG_INFO("Stop triggered: " + stop.id + " " + symbol +
                         " Price: " + std::to_string(price));

                if (trigger_callback_) {
                    trigger_callback_(stop);
                }
            }
        }
    }

    /**
     * @brief 移除止损单
     * @param id 止损单 ID
     */
    void remove_stop(const std::string& id) {
        std::lock_guard<std::mutex> lock(mutex_);
        stops_.erase(id);
    }

    /**
     * @brief 移除指定品种的所有止损单
     * @param symbol 品种代码
     */
    void remove_all_stops(const std::string& symbol) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = stops_.begin();
        while (it != stops_.end()) {
            if (it->second.symbol == symbol) {
                it = stops_.erase(it);
            } else {
                ++it;
            }
        }
    }

    /**
     * @brief 获取止损单
     * @param id 止损单 ID
     * @return 止损单指针
     */
    StopOrder* get_stop(const std::string& id) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = stops_.find(id);
        return (it != stops_.end()) ? &it->second : nullptr;
    }

    /**
     * @brief 获取指定品种的止损单
     * @param symbol 品种代码
     * @return 止损单列表
     */
    std::vector<StopOrder> get_stops(const std::string& symbol) const {
        std::lock_guard<std::mutex> lock(mutex_);

        std::vector<StopOrder> result;
        for (const auto& [id, stop] : stops_) {
            if (stop.symbol == symbol) {
                result.push_back(stop);
            }
        }
        return result;
    }

    /**
     * @brief 设置触发回调
     * @param callback 回调函数
     */
    void set_trigger_callback(TriggerCallback callback) {
        trigger_callback_ = std::move(callback);
    }

private:
    /**
     * @brief 生成止损单 ID
     * @return 止损单 ID
     */
    std::string generate_id() {
        return "STOP-" + std::to_string(next_id_++);
    }

    /**
     * @brief 检查固定止损
     * @param stop 止损单
     * @param price 当前价格
     * @return 触发返回 true
     */
    bool check_fixed_stop(const StopOrder& stop, double price) const {
        if (stop.side == Side::SELL) {
            // 多头止损：价格低于触发价
            return price <= stop.trigger_price;
        } else {
            // 空头止损：价格高于触发价
            return price >= stop.trigger_price;
        }
    }

    /**
     * @brief 更新追踪止损
     * @param stop 止损单
     * @param price 当前价格
     */
    void update_trailing_stop(StopOrder& stop, double price) {
        if (stop.side == Side::SELL) {
            // 多头追踪止损：更新最高价和触发价
            if (price > highest_prices_[stop.id]) {
                highest_prices_[stop.id] = price;
                stop.trigger_price = price - stop.trailing_offset;
            }
        } else {
            // 空头追踪止损：更新最低价和触发价
            if (lowest_prices_.find(stop.id) == lowest_prices_.end() ||
                price < lowest_prices_[stop.id]) {
                lowest_prices_[stop.id] = price;
                stop.trigger_price = price + stop.trailing_offset;
            }
        }
    }

    /**
     * @brief 检查追踪止损
     * @param stop 止损单
     * @param price 当前价格
     * @return 触发返回 true
     */
    bool check_trailing_stop(const StopOrder& stop, double price) const {
        if (stop.trigger_price == 0) return false;

        if (stop.side == Side::SELL) {
            return price <= stop.trigger_price;
        } else {
            return price >= stop.trigger_price;
        }
    }

    mutable std::mutex mutex_;  ///< 互斥锁
    int64_t next_id_ = 1;      ///< 下一个 ID
    std::unordered_map<std::string, StopOrder> stops_;  ///< 止损单映射

    std::unordered_map<std::string, double> highest_prices_;  ///< 最高价（多头追踪）
    std::unordered_map<std::string, double> lowest_prices_;   ///< 最低价（空头追踪）

    TriggerCallback trigger_callback_;  ///< 触发回调
};

} // namespace hft
