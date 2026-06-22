#pragma once

#include "types.h"
#include "order_book.h"
#include <vector>
#include <functional>
#include <iostream>

namespace hft {

/**
 * 撮合引擎类
 *
 * 负责接收订单并执行撮合逻辑
 *
 * ⭐ 重点：理解撮合的核心算法
 * 1. 价格优先：更优价格的订单优先成交
 * 2. 时间优先：同一价格的订单按提交时间排序
 * 3. 数量匹配：成交数量取买卖双方剩余数量的较小值
 */
class MatchingEngine {
public:
    MatchingEngine();
    ~MatchingEngine() = default;

    /**
     * 提交订单
     * @param order 要提交的订单
     * @return 成交记录列表
     *
     * ⭐ 核心方法：这是撮合引擎的入口
     */
    std::vector<Trade> submit_order(Order order);

    /**
     * 取消订单
     * @param order_id 要取消的订单ID
     * @return 取消是否成功
     */
    bool cancel_order(OrderId order_id);

    /**
     * 获取订单簿引用
     * @return 订单簿的常量引用
     */
    const OrderBook& order_book() const { return order_book_; }

    /**
     * 设置成交回调
     * 当有成交发生时会调用此回调
     */
    void set_trade_callback(TradeCallback callback) {
        trade_callback_ = std::move(callback);
    }

    /**
     * 设置订单状态回调
     * 当订单状态变化时会调用此回调
     */
    void set_order_callback(OrderCallback callback) {
        order_callback_ = std::move(callback);
    }

    /**
     * 获取所有成交记录
     */
    const std::vector<Trade>& trade_history() const { return trade_history_; }

    /**
     * 清空所有状态
     */
    void reset();

private:
    OrderBook order_book_;
    std::vector<Trade> trade_history_;

    // 回调函数
    TradeCallback trade_callback_;
    OrderCallback order_callback_;

    // 订单ID生成器
    OrderId next_order_id_ = 1;

    /**
     * 尝试撮合限价单
     * @param order 要撮合的订单
     * @return 成交记录列表
     *
     * ⭐ 核心算法：限价单撮合逻辑
     */
    std::vector<Trade> try_match_limit_order(Order& order);

    /**
     * 尝试撮合市价单
     * @param order 要撮合的订单
     * @return 成交记录列表
     */
    std::vector<Trade> try_match_market_order(Order& order);

    /**
     * 执行单笔成交
     * @param aggressive 主动方订单
     * @param passive 被动方订单
     * @param price 成交价格
     * @param quantity 成交数量
     * @return 成交记录
     */
    Trade execute_trade(const Order& aggressive, Order& passive,
                       Price price, Quantity quantity);

    /**
     * 获取当前时间戳
     */
    Timestamp get_timestamp() const;
};

} // namespace hft
