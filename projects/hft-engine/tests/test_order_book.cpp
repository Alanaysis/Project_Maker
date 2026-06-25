/**
 * @file test_order_book.cpp
 * @brief 订单簿测试
 */

#include <iostream>
#include <cassert>

#include "market_data/order_book.h"

using namespace hft;

/**
 * @brief 测试基本功能
 */
void test_basic() {
    std::cout << "Test basic functionality...\n";

    OrderBook book("AAPL");

    // 初始状态
    assert(book.best_bid() == 0.0);
    assert(book.best_ask() == 0.0);
    assert(book.mid_price() == 0.0);

    // 添加买盘
    OrderBookUpdate update;
    update.symbol = "AAPL";
    update.timestamp = Timestamp::now();
    update.side = Side::BUY;
    update.price = 150.0;
    update.quantity = 1000;
    book.update(update);

    assert(book.best_bid() == 150.0);
    assert(book.get_bid_quantity(150.0) == 1000);

    // 添加卖盘
    update.side = Side::SELL;
    update.price = 150.01;
    update.quantity = 1000;
    book.update(update);

    assert(book.best_ask() == 150.01);
    assert(book.get_ask_quantity(150.01) == 1000);

    // 测试中间价和价差
    assert(book.mid_price() > 0);
    assert(book.spread() > 0);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试多档深度
 */
void test_depth() {
    std::cout << "Test depth...\n";

    OrderBook book("AAPL");

    // 添加多档买盘
    for (int i = 0; i < 5; ++i) {
        OrderBookUpdate update;
        update.symbol = "AAPL";
        update.timestamp = Timestamp::now();
        update.side = Side::BUY;
        update.price = 150.0 - i * 0.01;
        update.quantity = 1000 - i * 100;
        book.update(update);
    }

    // 添加多档卖盘
    for (int i = 0; i < 5; ++i) {
        OrderBookUpdate update;
        update.symbol = "AAPL";
        update.timestamp = Timestamp::now();
        update.side = Side::SELL;
        update.price = 150.01 + i * 0.01;
        update.quantity = 1000 - i * 100;
        book.update(update);
    }

    // 验证深度
    auto bids = book.get_bid_depth(5);
    assert(bids.size() == 5);

    auto asks = book.get_ask_depth(5);
    assert(asks.size() == 5);

    // 验证排序
    for (size_t i = 1; i < bids.size(); ++i) {
        assert(bids[i].price < bids[i-1].price);
    }
    for (size_t i = 1; i < asks.size(); ++i) {
        assert(asks[i].price > asks[i-1].price);
    }

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试更新和删除
 */
void test_update_delete() {
    std::cout << "Test update and delete...\n";

    OrderBook book("AAPL");

    // 添加档位
    OrderBookUpdate update;
    update.symbol = "AAPL";
    update.timestamp = Timestamp::now();
    update.side = Side::BUY;
    update.price = 150.0;
    update.quantity = 1000;
    book.update(update);

    assert(book.get_bid_quantity(150.0) == 1000);

    // 更新数量
    update.quantity = 2000;
    book.update(update);
    assert(book.get_bid_quantity(150.0) == 2000);

    // 删除档位
    update.quantity = 0;
    book.update(update);
    assert(book.get_bid_quantity(150.0) == 0);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试市场深度
 */
void test_market_depth() {
    std::cout << "Test market depth...\n";

    OrderBook book("AAPL");

    // 添加数据
    for (int i = 0; i < 5; ++i) {
        OrderBookUpdate update;
        update.symbol = "AAPL";
        update.timestamp = Timestamp::now();

        update.side = Side::BUY;
        update.price = 150.0 - i * 0.01;
        update.quantity = 1000;
        book.update(update);

        update.side = Side::SELL;
        update.price = 150.01 + i * 0.01;
        update.quantity = 1000;
        book.update(update);
    }

    // 获取市场深度
    auto depth = book.get_market_depth();
    assert(depth.symbol == "AAPL");
    assert(depth.best_bid() == 150.0);
    assert(depth.best_ask() == 150.01);
    assert(depth.mid_price() > 0);
    assert(depth.spread() > 0);

    std::cout << "  PASSED\n";
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== Order Book Tests ===\n";

    test_basic();
    test_depth();
    test_update_delete();
    test_market_depth();

    std::cout << "\nAll tests passed!\n";
    return 0;
}
