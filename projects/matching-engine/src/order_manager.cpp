#include "order_manager.h"
#include <iostream>
#include <iomanip>

namespace hft {

OrderManager::OrderManager() = default;

OrderId OrderManager::submit_buy_order(Price price, Quantity quantity,
                                       OrderType type) {
    Order order;
    order.id = 0;  // 将由引擎分配
    order.side = Side::Buy;
    order.type = type;
    order.price = price;
    order.quantity = quantity;
    order.filled_quantity = 0;
    order.status = OrderStatus::New;
    order.timestamp = std::chrono::duration_cast<Timestamp>(
        std::chrono::steady_clock::now().time_since_epoch()
    );

    auto trades = engine_.submit_order(order);

    // 记录订单
    orders_[order.id] = order;

    // 打印成交信息
    if (!trades.empty()) {
        std::cout << "[Trade] Buy order " << order.id
                  << " executed " << trades.size() << " trades" << std::endl;
    }

    return order.id;
}

OrderId OrderManager::submit_sell_order(Price price, Quantity quantity,
                                        OrderType type) {
    Order order;
    order.id = 0;  // 将由引擎分配
    order.side = Side::Sell;
    order.type = type;
    order.price = price;
    order.quantity = quantity;
    order.filled_quantity = 0;
    order.status = OrderStatus::New;
    order.timestamp = std::chrono::duration_cast<Timestamp>(
        std::chrono::steady_clock::now().time_since_epoch()
    );

    auto trades = engine_.submit_order(order);

    // 记录订单
    orders_[order.id] = order;

    // 打印成交信息
    if (!trades.empty()) {
        std::cout << "[Trade] Sell order " << order.id
                  << " executed " << trades.size() << " trades" << std::endl;
    }

    return order.id;
}

bool OrderManager::cancel_order(OrderId order_id) {
    auto it = orders_.find(order_id);
    if (it == orders_.end()) {
        return false;
    }

    bool result = engine_.cancel_order(order_id);
    if (result) {
        it->second.status = OrderStatus::Cancelled;
    }
    return result;
}

const Order* OrderManager::get_order(OrderId order_id) const {
    auto it = orders_.find(order_id);
    if (it == orders_.end()) {
        return nullptr;
    }
    return &(it->second);
}

OrderBook::Snapshot OrderManager::get_snapshot(size_t levels) const {
    return engine_.order_book().get_snapshot(levels);
}

void OrderManager::print_order_book() const {
    engine_.order_book().print();
}

void OrderManager::print_trade_history() const {
    const auto& trades = engine_.trade_history();
    if (trades.empty()) {
        std::cout << "No trades yet." << std::endl;
        return;
    }

    std::cout << "=== Trade History ===" << std::endl;
    std::cout << std::setw(10) << "Trade ID"
              << std::setw(12) << "Buy Order"
              << std::setw(12) << "Sell Order"
              << std::setw(10) << "Price"
              << std::setw(10) << "Quantity"
              << std::endl;
    std::cout << std::string(54, '-') << std::endl;

    for (size_t i = 0; i < trades.size(); i++) {
        const auto& trade = trades[i];
        std::cout << std::setw(10) << i + 1
                  << std::setw(12) << trade.buy_order_id
                  << std::setw(12) << trade.sell_order_id
                  << std::setw(10) << trade.price
                  << std::setw(10) << trade.quantity
                  << std::endl;
    }
    std::cout << "====================" << std::endl;
}

void OrderManager::reset() {
    engine_.reset();
    orders_.clear();
}

} // namespace hft
