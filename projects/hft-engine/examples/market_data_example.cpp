/**
 * @file market_data_example.cpp
 * @brief 市场数据处理示例
 *
 * 演示如何使用市场数据处理模块。
 */

#include <iostream>
#include <thread>
#include <chrono>

#include "core/timestamp.h"
#include "core/logger.h"
#include "market_data/tick.h"
#include "market_data/order_book.h"
#include "market_data/feed_handler.h"
#include "market_data/tick_store.h"

using namespace hft;

/**
 * @brief 演示订单簿
 */
void demo_order_book() {
    std::cout << "\n=== Order Book Demo ===\n";

    OrderBook book("AAPL");

    // 添加买盘
    for (int i = 0; i < 5; ++i) {
        OrderBookUpdate update;
        update.symbol = "AAPL";
        update.timestamp = Timestamp::now();
        update.side = Side::BUY;
        update.price = 150.0 - i * 0.01;
        update.quantity = 1000 - i * 100;
        book.update(update);
    }

    // 添加卖盘
    for (int i = 0; i < 5; ++i) {
        OrderBookUpdate update;
        update.symbol = "AAPL";
        update.timestamp = Timestamp::now();
        update.side = Side::SELL;
        update.price = 150.01 + i * 0.01;
        update.quantity = 1000 - i * 100;
        book.update(update);
    }

    // 显示订单簿
    std::cout << "Symbol: " << book.symbol() << "\n";
    std::cout << "Best Bid: " << book.best_bid() << "\n";
    std::cout << "Best Ask: " << book.best_ask() << "\n";
    std::cout << "Mid Price: " << book.mid_price() << "\n";
    std::cout << "Spread: " << book.spread() << "\n";
    std::cout << "Bid Levels: " << book.bid_levels() << "\n";
    std::cout << "Ask Levels: " << book.ask_levels() << "\n";

    // 显示深度
    std::cout << "\nBids:\n";
    auto bids = book.get_bid_depth(5);
    for (const auto& level : bids) {
        std::cout << "  " << level.price << " x " << level.quantity << "\n";
    }

    std::cout << "Asks:\n";
    auto asks = book.get_ask_depth(5);
    for (const auto& level : asks) {
        std::cout << "  " << level.price << " x " << level.quantity << "\n";
    }
}

/**
 * @brief 演示模拟行情
 */
void demo_simulated_feed() {
    std::cout << "\n=== Simulated Feed Demo ===\n";

    SimulatedFeedHandler feed("Simulated");

    int tick_count = 0;
    feed.set_tick_callback([&](const Tick& tick) {
        tick_count++;
        std::cout << "Tick " << tick_count << ": "
                  << tick.symbol << " "
                  << tick.last_price << " x "
                  << tick.last_quantity << "\n";
    });

    // 生成模拟数据
    for (int i = 0; i < 10; ++i) {
        feed.generate_tick("AAPL", 150.0);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    std::cout << "Total ticks: " << tick_count << "\n";
}

/**
 * @brief 演示行情存储
 */
void demo_tick_store() {
    std::cout << "\n=== Tick Store Demo ===\n";

    TickStore store(1000);

    // 存储 Tick
    for (int i = 0; i < 100; ++i) {
        Tick tick;
        tick.symbol = "AAPL";
        tick.timestamp = Timestamp::now();
        tick.last_price = 150.0 + (rand() % 100 - 50) / 1000.0;
        tick.last_quantity = rand() % 1000 + 1;
        tick.bid_price = tick.last_price - 0.01;
        tick.ask_price = tick.last_price + 0.01;

        store.store(tick);
    }

    // 查询最近数据
    auto recent = store.get_recent("AAPL", 10);
    std::cout << "Recent ticks: " << recent.size() << "\n";

    for (const auto& tick : recent) {
        std::cout << "  " << tick.symbol << " "
                  << tick.last_price << " x "
                  << tick.last_quantity << "\n";
    }

    std::cout << "Cache size: " << store.cache_size("AAPL") << "\n";
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== Market Data Processing Examples ===\n";

    Logger::instance().init("", LogLevel::INFO);

    demo_order_book();
    demo_simulated_feed();
    demo_tick_store();

    Logger::instance().shutdown();

    std::cout << "\n=== All Examples Completed ===\n";
    return 0;
}
