#pragma once

#include "types.h"
#include "matching_engine.h"
#include <unordered_map>
#include <vector>
#include <string>
#include <iostream>

namespace hft {

/**
 * 订单管理器类
 *
 * 提供更高层次的订单管理功能
 * 封装了撮合引擎，提供更友好的接口
 *
 * 职责：
 * 1. 管理订单生命周期
 * 2. 记录交易历史
 * 3. 提供查询接口
 */
class OrderManager {
public:
    OrderManager();
    ~OrderManager() = default;

    /**
     * 提交买单
     * @param price 价格
     * @param quantity 数量
     * @param type 订单类型
     * @return 订单ID
     */
    OrderId submit_buy_order(Price price, Quantity quantity,
                            OrderType type = OrderType::Limit);

    /**
     * 提交卖单
     * @param price 价格
     * @param quantity 数量
     * @param type 订单类型
     * @return 订单ID
     */
    OrderId submit_sell_order(Price price, Quantity quantity,
                             OrderType type = OrderType::Limit);

    /**
     * 取消订单
     * @param order_id 订单ID
     * @return 取消是否成功
     */
    bool cancel_order(OrderId order_id);

    /**
     * 获取订单信息
     * @param order_id 订单ID
     * @return 订单指针，如果不存在返回nullptr
     */
    const Order* get_order(OrderId order_id) const;

    /**
     * 获取订单簿快照
     */
    OrderBook::Snapshot get_snapshot(size_t levels = 10) const;

    /**
     * 获取最优买价
     */
    Price best_bid() const { return engine_.order_book().best_bid(); }

    /**
     * 获取最优卖价
     */
    Price best_ask() const { return engine_.order_book().best_ask(); }

    /**
     * 获取所有成交记录
     */
    const std::vector<Trade>& trade_history() const {
        return engine_.trade_history();
    }

    /**
     * 打印订单簿状态
     */
    void print_order_book() const;

    /**
     * 打印交易历史
     */
    void print_trade_history() const;

    /**
     * 重置管理器
     */
    void reset();

private:
    MatchingEngine engine_;
    std::unordered_map<OrderId, Order> orders_;
};

} // namespace hft
