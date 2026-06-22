#include <gtest/gtest.h>
#include "order_book.h"

class OrderBookTest : public ::testing::Test {
protected:
    void SetUp() override {
        book = hft::OrderBook();
    }

    hft::OrderBook book;

    // 辅助方法：创建订单
    hft::Order create_order(hft::OrderId id, hft::Side side, hft::Price price,
                           hft::Quantity quantity) {
        hft::Order order;
        order.id = id;
        order.side = side;
        order.type = hft::OrderType::Limit;
        order.price = price;
        order.quantity = quantity;
        order.filled_quantity = 0;
        order.status = hft::OrderStatus::New;
        order.timestamp = std::chrono::duration_cast<hft::Timestamp>(
            std::chrono::steady_clock::now().time_since_epoch()
        );
        return order;
    }
};

// 测试添加订单
TEST_F(OrderBookTest, AddOrder) {
    auto order = create_order(1, hft::Side::Buy, 100, 10);
    EXPECT_TRUE(book.add_order(order));
    EXPECT_EQ(book.bid_count(), 1);
}

// 测试添加重复订单
TEST_F(OrderBookTest, AddDuplicateOrder) {
    auto order1 = create_order(1, hft::Side::Buy, 100, 10);
    auto order2 = create_order(1, hft::Side::Buy, 100, 10);
    EXPECT_TRUE(book.add_order(order1));
    EXPECT_FALSE(book.add_order(order2));
}

// 测试取消订单
TEST_F(OrderBookTest, CancelOrder) {
    auto order = create_order(1, hft::Side::Buy, 100, 10);
    book.add_order(order);

    EXPECT_TRUE(book.cancel_order(1));
    EXPECT_EQ(book.bid_count(), 0);
}

// 测试取消不存在的订单
TEST_F(OrderBookTest, CancelNonexistentOrder) {
    EXPECT_FALSE(book.cancel_order(999));
}

// 测试最优买价
TEST_F(OrderBookTest, BestBid) {
    auto order1 = create_order(1, hft::Side::Buy, 100, 10);
    auto order2 = create_order(2, hft::Side::Buy, 105, 5);
    auto order3 = create_order(3, hft::Side::Buy, 95, 15);

    book.add_order(order1);
    book.add_order(order2);
    book.add_order(order3);

    EXPECT_EQ(book.best_bid(), 105);
}

// 测试最优卖价
TEST_F(OrderBookTest, BestAsk) {
    auto order1 = create_order(1, hft::Side::Sell, 100, 10);
    auto order2 = create_order(2, hft::Side::Sell, 105, 5);
    auto order3 = create_order(3, hft::Side::Sell, 95, 15);

    book.add_order(order1);
    book.add_order(order2);
    book.add_order(order3);

    EXPECT_EQ(book.best_ask(), 95);
}

// 测试买卖价差
TEST_F(OrderBookTest, Spread) {
    auto buy = create_order(1, hft::Side::Buy, 100, 10);
    auto sell = create_order(2, hft::Side::Sell, 105, 10);

    book.add_order(buy);
    book.add_order(sell);

    EXPECT_EQ(book.spread(), 5);
}

// 测试空订单簿的价差
TEST_F(OrderBookTest, SpreadEmptyBook) {
    EXPECT_EQ(book.spread(), 0);
}

// 测试订单簿深度
TEST_F(OrderBookTest, BidDepth) {
    for (int i = 0; i < 5; i++) {
        auto order = create_order(i + 1, hft::Side::Buy, 100 + i, 10);
        book.add_order(order);
    }

    auto depth = book.bid_depth(3);
    ASSERT_EQ(depth.size(), 3);
    EXPECT_EQ(depth[0].price, 104);  // 最高价在前
    EXPECT_EQ(depth[1].price, 103);
    EXPECT_EQ(depth[2].price, 102);
}

// 测试卖单深度
TEST_F(OrderBookTest, AskDepth) {
    for (int i = 0; i < 5; i++) {
        auto order = create_order(i + 1, hft::Side::Sell, 100 + i, 10);
        book.add_order(order);
    }

    auto depth = book.ask_depth(3);
    ASSERT_EQ(depth.size(), 3);
    EXPECT_EQ(depth[0].price, 100);  // 最低价在前
    EXPECT_EQ(depth[1].price, 101);
    EXPECT_EQ(depth[2].price, 102);
}

// 测试查找订单
TEST_F(OrderBookTest, FindOrder) {
    auto order = create_order(1, hft::Side::Buy, 100, 10);
    book.add_order(order);

    auto found = book.find_order(1);
    ASSERT_NE(found, nullptr);
    EXPECT_EQ(found->id, 1);
    EXPECT_EQ(found->price, 100);
}

// 测试查找不存在的订单
TEST_F(OrderBookTest, FindNonexistentOrder) {
    EXPECT_EQ(book.find_order(999), nullptr);
}

// 测试修改订单数量
TEST_F(OrderBookTest, AmendOrder) {
    auto order = create_order(1, hft::Side::Buy, 100, 10);
    book.add_order(order);

    EXPECT_TRUE(book.amend_order(1, 5));
    auto found = book.find_order(1);
    ASSERT_NE(found, nullptr);
    EXPECT_EQ(found->quantity, 5);
}

// 测试清空订单簿
TEST_F(OrderBookTest, Clear) {
    auto order1 = create_order(1, hft::Side::Buy, 100, 10);
    auto order2 = create_order(2, hft::Side::Sell, 105, 10);
    book.add_order(order1);
    book.add_order(order2);

    book.clear();
    EXPECT_EQ(book.bid_count(), 0);
    EXPECT_EQ(book.ask_count(), 0);
    EXPECT_EQ(book.best_bid(), 0);
    EXPECT_EQ(book.best_ask(), 0);
}

// 测试订单簿快照
TEST_F(OrderBookTest, Snapshot) {
    auto buy = create_order(1, hft::Side::Buy, 100, 10);
    auto sell = create_order(2, hft::Side::Sell, 105, 10);
    book.add_order(buy);
    book.add_order(sell);

    auto snapshot = book.get_snapshot(5);
    EXPECT_FALSE(snapshot.bids.empty());
    EXPECT_FALSE(snapshot.asks.empty());
}

// 测试时间优先原则
TEST_F(OrderBookTest, TimePriority) {
    // 同一价格的订单应该按添加顺序排列
    auto order1 = create_order(1, hft::Side::Buy, 100, 10);
    auto order2 = create_order(2, hft::Side::Buy, 100, 20);
    auto order3 = create_order(3, hft::Side::Buy, 100, 30);

    book.add_order(order1);
    book.add_order(order2);
    book.add_order(order3);

    auto depth = book.bid_depth(1);
    ASSERT_EQ(depth.size(), 1);
    EXPECT_EQ(depth[0].total_quantity, 60);  // 10 + 20 + 30
    EXPECT_EQ(depth[0].order_count, 3);
}

// 测试混合买卖单
TEST_F(OrderBookTest, MixedOrders) {
    for (int i = 0; i < 10; i++) {
        hft::Side side = (i % 2 == 0) ? hft::Side::Buy : hft::Side::Sell;
        auto order = create_order(i + 1, side, 100 + i, 10);
        book.add_order(order);
    }

    EXPECT_EQ(book.bid_count(), 5);
    EXPECT_EQ(book.ask_count(), 5);
}
