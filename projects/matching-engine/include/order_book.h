#pragma once

#include "types.h"
#include <map>
#include <list>
#include <unordered_map>
#include <vector>
#include <mutex>
#include <iostream>

namespace hft {

/**
 * 订单簿类
 *
 * 维护买卖双方的订单，按价格优先、时间优先的原则组织
 *
 * 买单簿：按价格降序排列（最高买价在前）
 * 卖单簿：按价格升序排列（最低卖价在前）
 *
 * ⭐ 重点：理解为什么买单和卖单使用不同的排序方式
 */
class OrderBook {
public:
    OrderBook();
    ~OrderBook() = default;

    // ========== 订单操作 ==========

    /**
     * 添加订单到订单簿
     * @param order 要添加的订单
     * @return 添加是否成功
     */
    bool add_order(const Order& order);

    /**
     * 取消订单
     * @param order_id 要取消的订单ID
     * @return 取消是否成功
     */
    bool cancel_order(OrderId order_id);

    /**
     * 修改订单数量
     * @param order_id 要修改的订单ID
     * @param new_quantity 新的数量
     * @return 修改是否成功
     */
    bool amend_order(OrderId order_id, Quantity new_quantity);

    // ========== 查询操作 ==========

    /**
     * 获取最优买价
     * @return 最优买价，如果没有买单返回0
     */
    Price best_bid() const;

    /**
     * 获取最优卖价
     * @return 最优卖价，如果没有卖单返回0
     */
    Price best_ask() const;

    /**
     * 获取买卖价差
     * @return 价差，如果没有对手方返回0
     */
    Price spread() const;

    /**
     * 获取买单簿深度
     * @param levels 要获取的层级数
     * @return 价格层级列表
     */
    std::vector<PriceLevel> bid_depth(size_t levels = 10) const;

    /**
     * 获取卖单簿深度
     * @param levels 要获取的层级数
     * @return 价格层级列表
     */
    std::vector<PriceLevel> ask_depth(size_t levels = 10) const;

    /**
     * 根据ID查找订单
     * @param order_id 订单ID
     * @return 订单指针，如果不存在返回nullptr
     */
    const Order* find_order(OrderId order_id) const;

    /**
     * 获取订单簿状态快照
     * @return 包含买卖双方深度的快照
     */
    struct Snapshot {
        std::vector<PriceLevel> bids;
        std::vector<PriceLevel> asks;
        Timestamp timestamp;
    };
    Snapshot get_snapshot(size_t levels = 10) const;

    // ========== 统计信息 ==========

    /**
     * 获取买单总数
     */
    size_t bid_count() const { return bid_order_count_; }

    /**
     * 获取卖单总数
     */
    size_t ask_count() const { return ask_order_count_; }

    /**
     * 清空订单簿
     */
    void clear();

    /**
     * 打印订单簿状态（调试用）
     */
    void print() const;

    /**
     * 获取最优卖价的订单列表（用于撮合）
     * @return 指向订单列表的指针，如果为空返回nullptr
     */
    std::list<Order>* get_best_ask_orders();

    /**
     * 获取最优买价的订单列表（用于撮合）
     * @return 指向订单列表的指针，如果为空返回nullptr
     */
    std::list<Order>* get_best_bid_orders();

    /**
     * 移除空的价格层级
     */
    void cleanup_empty_levels();

private:
    // ⭐ 重点：订单簿的核心数据结构

    // 买单簿：价格降序排列
    // key: 价格, value: 该价格的订单列表（FIFO）
    // 为什么用 std::map？因为需要按价格有序遍历
    // 为什么用 std::list？因为需要高效的插入和删除
    std::map<Price, std::list<Order>, std::greater<Price>> bid_book_;

    // 卖单簿：价格升序排列
    std::map<Price, std::list<Order>, std::less<Price>> ask_book_;

    // 订单索引：快速通过ID查找订单
    // 存储指向订单的迭代器，避免线性搜索
    struct OrderLocation {
        Side side;
        Price price;
        std::list<Order>::iterator iterator;
    };
    std::unordered_map<OrderId, OrderLocation> order_index_;

    // 统计信息
    size_t bid_order_count_ = 0;
    size_t ask_order_count_ = 0;

    // 辅助方法
    void update_stats(Side side, Quantity quantity, bool is_add);
};

} // namespace hft
