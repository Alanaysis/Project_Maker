#include "order_book.h"
#include <algorithm>
#include <stdexcept>

namespace hft {

OrderBook::OrderBook() = default;

bool OrderBook::add_order(const Order& order) {
    // 检查订单是否已存在
    if (order_index_.find(order.id) != order_index_.end()) {
        return false;
    }

    // 根据订单方向添加到对应的订单簿
    if (order.side == Side::Buy) {
        auto& price_level = bid_book_[order.price];
        price_level.push_back(order);
        auto it = std::prev(price_level.end());
        order_index_[order.id] = {Side::Buy, order.price, it};
        bid_order_count_++;
    } else {
        auto& price_level = ask_book_[order.price];
        price_level.push_back(order);
        auto it = std::prev(price_level.end());
        order_index_[order.id] = {Side::Sell, order.price, it};
        ask_order_count_++;
    }

    return true;
}

bool OrderBook::cancel_order(OrderId order_id) {
    auto it = order_index_.find(order_id);
    if (it == order_index_.end()) {
        return false;
    }

    const auto& location = it->second;

    // 从对应的订单簿中移除
    if (location.side == Side::Buy) {
        auto price_it = bid_book_.find(location.price);
        if (price_it != bid_book_.end()) {
            price_it->second.erase(location.iterator);
            if (price_it->second.empty()) {
                bid_book_.erase(price_it);
            }
            bid_order_count_--;
        }
    } else {
        auto price_it = ask_book_.find(location.price);
        if (price_it != ask_book_.end()) {
            price_it->second.erase(location.iterator);
            if (price_it->second.empty()) {
                ask_book_.erase(price_it);
            }
            ask_order_count_--;
        }
    }

    order_index_.erase(it);
    return true;
}

bool OrderBook::amend_order(OrderId order_id, Quantity new_quantity) {
    auto it = order_index_.find(order_id);
    if (it == order_index_.end()) {
        return false;
    }

    auto& location = it->second;
    auto& order = *location.iterator;

    // 只能减少数量，不能增加
    if (new_quantity > order.quantity) {
        return false;
    }

    // 更新订单数量
    order.quantity = new_quantity;

    // 如果新数量小于已成交数量，则取消订单
    if (new_quantity <= order.filled_quantity) {
        order.status = OrderStatus::Cancelled;
        cancel_order(order_id);
        return true;
    }

    return true;
}

Price OrderBook::best_bid() const {
    if (bid_book_.empty()) {
        return 0;
    }
    return bid_book_.begin()->first;
}

Price OrderBook::best_ask() const {
    if (ask_book_.empty()) {
        return 0;
    }
    return ask_book_.begin()->first;
}

Price OrderBook::spread() const {
    Price bid = best_bid();
    Price ask = best_ask();
    if (bid == 0 || ask == 0) {
        return 0;
    }
    return ask - bid;
}

std::vector<PriceLevel> OrderBook::bid_depth(size_t levels) const {
    std::vector<PriceLevel> result;
    size_t count = 0;

    for (const auto& [price, orders] : bid_book_) {
        if (count >= levels) break;

        PriceLevel level(price);
        for (const auto& order : orders) {
            level.total_quantity += order.remaining_quantity();
            level.order_count++;
        }
        result.push_back(level);
        count++;
    }

    return result;
}

std::vector<PriceLevel> OrderBook::ask_depth(size_t levels) const {
    std::vector<PriceLevel> result;
    size_t count = 0;

    for (const auto& [price, orders] : ask_book_) {
        if (count >= levels) break;

        PriceLevel level(price);
        for (const auto& order : orders) {
            level.total_quantity += order.remaining_quantity();
            level.order_count++;
        }
        result.push_back(level);
        count++;
    }

    return result;
}

const Order* OrderBook::find_order(OrderId order_id) const {
    auto it = order_index_.find(order_id);
    if (it == order_index_.end()) {
        return nullptr;
    }
    return &(*(it->second.iterator));
}

OrderBook::Snapshot OrderBook::get_snapshot(size_t levels) const {
    Snapshot snapshot;
    snapshot.bids = bid_depth(levels);
    snapshot.asks = ask_depth(levels);
    snapshot.timestamp = std::chrono::duration_cast<Timestamp>(
        std::chrono::steady_clock::now().time_since_epoch()
    );
    return snapshot;
}

void OrderBook::clear() {
    bid_book_.clear();
    ask_book_.clear();
    order_index_.clear();
    bid_order_count_ = 0;
    ask_order_count_ = 0;
}

void OrderBook::print() const {
    std::cout << "=== Order Book ===" << std::endl;
    std::cout << "Bids (Buy):" << std::endl;

    for (const auto& [price, orders] : bid_book_) {
        Quantity total = 0;
        for (const auto& order : orders) {
            total += order.remaining_quantity();
        }
        std::cout << "  Price: " << price
                  << " | Quantity: " << total
                  << " | Orders: " << orders.size() << std::endl;
    }

    std::cout << "Asks (Sell):" << std::endl;
    for (const auto& [price, orders] : ask_book_) {
        Quantity total = 0;
        for (const auto& order : orders) {
            total += order.remaining_quantity();
        }
        std::cout << "  Price: " << price
                  << " | Quantity: " << total
                  << " | Orders: " << orders.size() << std::endl;
    }

    std::cout << "==================" << std::endl;
}

void OrderBook::update_stats(Side /*side*/, Quantity /*quantity*/, bool /*is_add*/) {
    // 统计信息更新（如果需要）
}

std::list<Order>* OrderBook::get_best_ask_orders() {
    if (ask_book_.empty()) {
        return nullptr;
    }
    return &(ask_book_.begin()->second);
}

std::list<Order>* OrderBook::get_best_bid_orders() {
    if (bid_book_.empty()) {
        return nullptr;
    }
    return &(bid_book_.begin()->second);
}

void OrderBook::cleanup_empty_levels() {
    // 清理空的买单价格层级
    for (auto it = bid_book_.begin(); it != bid_book_.end();) {
        if (it->second.empty()) {
            it = bid_book_.erase(it);
        } else {
            ++it;
        }
    }

    // 清理空的卖单价格层级
    for (auto it = ask_book_.begin(); it != ask_book_.end();) {
        if (it->second.empty()) {
            it = ask_book_.erase(it);
        } else {
            ++it;
        }
    }
}

} // namespace hft
