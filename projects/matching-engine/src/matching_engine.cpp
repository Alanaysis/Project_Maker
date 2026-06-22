#include "matching_engine.h"
#include <algorithm>
#include <chrono>

namespace hft {

MatchingEngine::MatchingEngine() = default;

std::vector<Trade> MatchingEngine::submit_order(Order order) {
    std::vector<Trade> trades;

    // 验证订单
    if (!order.is_valid()) {
        order.status = OrderStatus::Rejected;
        if (order_callback_) {
            order_callback_(order);
        }
        return trades;
    }

    // 设置订单ID和时间戳
    order.id = next_order_id_++;
    order.timestamp = get_timestamp();
    order.filled_quantity = 0;
    order.status = OrderStatus::New;

    // 根据订单类型执行撮合
    if (order.type == OrderType::Market) {
        trades = try_match_market_order(order);
    } else {
        trades = try_match_limit_order(order);
    }

    // 如果订单未完全成交，添加到订单簿
    if (!order.is_filled() && order.status != OrderStatus::Cancelled) {
        order_book_.add_order(order);
    }

    // 通知订单状态变化
    if (order_callback_) {
        order_callback_(order);
    }

    return trades;
}

bool MatchingEngine::cancel_order(OrderId order_id) {
    return order_book_.cancel_order(order_id);
}

std::vector<Trade> MatchingEngine::try_match_limit_order(Order& order) {
    std::vector<Trade> trades;

    // ⭐ 核心算法：限价单撮合逻辑
    //
    // 对于买单：
    //   - 与卖单簿中价格 <= 买单价格的订单撮合
    //   - 按卖价从低到高的顺序撮合
    //
    // 对于卖单：
    //   - 与买单簿中价格 >= 卖单价格的订单撮合
    //   - 按买价从高到低的顺序撮合

    if (order.side == Side::Buy) {
        // 买单：与卖单簿撮合
        while (!order.is_filled()) {
            Price best_ask = order_book_.best_ask();
            if (best_ask == 0 || best_ask > order.price) {
                break;  // 没有可撮合的卖单
            }

            // 获取最优卖价的订单列表
            auto& ask_book = const_cast<std::map<Price, std::list<Order>, std::less<Price>>&>(
                order_book_.ask_depth(1).empty() ?
                *reinterpret_cast<const std::map<Price, std::list<Order>, std::less<Price>>*>(&order_book_) :
                *reinterpret_cast<const std::map<Price, std::list<Order>, std::less<Price>>*>(&order_book_)
            );

            // 简化实现：直接访问订单簿内部
            // 在实际实现中，应该提供更好的接口
            break;  // 暂时简化处理
        }
    } else {
        // 卖单：与买单簿撮合
        while (!order.is_filled()) {
            Price best_bid = order_book_.best_bid();
            if (best_bid == 0 || best_bid < order.price) {
                break;  // 没有可撮合的买单
            }

            break;  // 暂时简化处理
        }
    }

    return trades;
}

std::vector<Trade> MatchingEngine::try_match_market_order(Order& order) {
    std::vector<Trade> trades;

    // 市价单：直接与最优对手价撮合
    // 注意：市价单没有价格限制，直接以对手方的价格成交

    if (order.side == Side::Buy) {
        // 买单：与最优卖价撮合
        while (!order.is_filled()) {
            Price best_ask = order_book_.best_ask();
            if (best_ask == 0) {
                break;  // 没有卖单
            }

            // 简化处理：市价单如果没有对手方则取消
            break;
        }
    } else {
        // 卖单：与最优买价撮合
        while (!order.is_filled()) {
            Price best_bid = order_book_.best_bid();
            if (best_bid == 0) {
                break;  // 没有买单
            }

            break;
        }
    }

    return trades;
}

Trade MatchingEngine::execute_trade(const Order& aggressive, Order& passive,
                                   Price price, Quantity quantity) {
    Trade trade;
    trade.price = price;
    trade.quantity = quantity;
    trade.timestamp = get_timestamp();

    if (aggressive.side == Side::Buy) {
        trade.buy_order_id = aggressive.id;
        trade.sell_order_id = passive.id;
    } else {
        trade.buy_order_id = passive.id;
        trade.sell_order_id = aggressive.id;
    }

    return trade;
}

Timestamp MatchingEngine::get_timestamp() const {
    return std::chrono::duration_cast<Timestamp>(
        std::chrono::steady_clock::now().time_since_epoch()
    );
}

void MatchingEngine::reset() {
    order_book_.clear();
    trade_history_.clear();
    next_order_id_ = 1;
}

} // namespace hft
