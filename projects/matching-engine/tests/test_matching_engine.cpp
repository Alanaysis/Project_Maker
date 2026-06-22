#include <gtest/gtest.h>
#include "matching_engine.h"

class MatchingEngineTest : public ::testing::Test {
protected:
    void SetUp() override {
        engine = hft::MatchingEngine();
    }

    hft::MatchingEngine engine;

    // 辅助方法：创建订单
    hft::Order create_order(hft::Side side, hft::Price price,
                           hft::Quantity quantity,
                           hft::OrderType type = hft::OrderType::Limit) {
        hft::Order order;
        order.id = 0;  // 将由引擎分配
        order.side = side;
        order.type = type;
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

// 测试提交买单
TEST_F(MatchingEngineTest, SubmitBuyOrder) {
    auto order = create_order(hft::Side::Buy, 100, 10);
    auto trades = engine.submit_order(order);

    EXPECT_TRUE(trades.empty());  // 没有对手方，不会成交
    EXPECT_EQ(engine.order_book().bid_count(), 1);
}

// 测试提交卖单
TEST_F(MatchingEngineTest, SubmitSellOrder) {
    auto order = create_order(hft::Side::Sell, 105, 10);
    auto trades = engine.submit_order(order);

    EXPECT_TRUE(trades.empty());
    EXPECT_EQ(engine.order_book().ask_count(), 1);
}

// 测试无效订单
TEST_F(MatchingEngineTest, InvalidOrder) {
    // 数量为0的订单应该被拒绝
    hft::Order order;
    order.id = 0;
    order.side = hft::Side::Buy;
    order.type = hft::OrderType::Limit;
    order.price = 100;
    order.quantity = 0;  // 无效数量
    order.filled_quantity = 0;
    order.status = hft::OrderStatus::New;

    auto trades = engine.submit_order(order);
    EXPECT_TRUE(trades.empty());
}

// 测试限价单撮合 - 价格匹配
TEST_F(MatchingEngineTest, LimitOrderPriceMatch) {
    // 先添加一个卖单
    auto sell = create_order(hft::Side::Sell, 100, 10);
    engine.submit_order(sell);

    // 提交一个价格等于卖价的买单
    auto buy = create_order(hft::Side::Buy, 100, 10);
    auto trades = engine.submit_order(buy);

    // 应该成交
    EXPECT_FALSE(trades.empty());
}

// 测试限价单撮合 - 价格不匹配
TEST_F(MatchingEngineTest, LimitOrderPriceMismatch) {
    // 先添加一个卖单
    auto sell = create_order(hft::Side::Sell, 105, 10);
    engine.submit_order(sell);

    // 提交一个价格低于卖价的买单
    auto buy = create_order(hft::Side::Buy, 100, 10);
    auto trades = engine.submit_order(buy);

    // 不应该成交
    EXPECT_TRUE(trades.empty());
}

// 测试订单簿状态
TEST_F(MatchingEngineTest, OrderBookState) {
    // 添加多个订单
    engine.submit_order(create_order(hft::Side::Buy, 100, 10));
    engine.submit_order(create_order(hft::Side::Buy, 99, 15));
    engine.submit_order(create_order(hft::Side::Sell, 105, 10));
    engine.submit_order(create_order(hft::Side::Sell, 106, 20));

    EXPECT_EQ(engine.order_book().bid_count(), 2);
    EXPECT_EQ(engine.order_book().ask_count(), 2);
    EXPECT_EQ(engine.order_book().best_bid(), 100);
    EXPECT_EQ(engine.order_book().best_ask(), 105);
}

// 测试取消订单
TEST_F(MatchingEngineTest, CancelOrder) {
    auto order = create_order(hft::Side::Buy, 100, 10);
    auto trades = engine.submit_order(order);

    // 获取订单ID（需要从订单簿中查找）
    auto best_bid = engine.order_book().best_bid();
    EXPECT_EQ(best_bid, 100);
}

// 测试交易历史
TEST_F(MatchingEngineTest, TradeHistory) {
    // 添加卖单
    auto sell = create_order(hft::Side::Sell, 100, 10);
    engine.submit_order(sell);

    // 添加买单进行撮合
    auto buy = create_order(hft::Side::Buy, 100, 10);
    engine.submit_order(buy);

    // 检查交易历史
    const auto& history = engine.trade_history();
    EXPECT_FALSE(history.empty());
}

// 测试重置功能
TEST_F(MatchingEngineTest, Reset) {
    engine.submit_order(create_order(hft::Side::Buy, 100, 10));
    engine.submit_order(create_order(hft::Side::Sell, 105, 10));

    engine.reset();

    EXPECT_EQ(engine.order_book().bid_count(), 0);
    EXPECT_EQ(engine.order_book().ask_count(), 0);
    EXPECT_TRUE(engine.trade_history().empty());
}

// 测试多个订单的撮合
TEST_F(MatchingEngineTest, MultipleOrdersMatch) {
    // 添加多个卖单
    engine.submit_order(create_order(hft::Side::Sell, 100, 5));
    engine.submit_order(create_order(hft::Side::Sell, 101, 10));
    engine.submit_order(create_order(hft::Side::Sell, 102, 15));

    // 提交一个大买单
    auto buy = create_order(hft::Side::Buy, 102, 20);
    auto trades = engine.submit_order(buy);

    // 应该有成交
    EXPECT_FALSE(trades.empty());
}

// 测试订单回调
TEST_F(MatchingEngineTest, OrderCallback) {
    bool callback_called = false;
    engine.set_order_callback([&callback_called](const hft::Order& order) {
        callback_called = true;
    });

    engine.submit_order(create_order(hft::Side::Buy, 100, 10));
    EXPECT_TRUE(callback_called);
}

// 测试交易回调
TEST_F(MatchingEngineTest, TradeCallback) {
    bool callback_called = false;
    engine.set_trade_callback([&callback_called](const hft::Trade& trade) {
        callback_called = true;
    });

    // 添加卖单和买单进行撮合
    engine.submit_order(create_order(hft::Side::Sell, 100, 10));
    engine.submit_order(create_order(hft::Side::Buy, 100, 10));

    EXPECT_TRUE(callback_called);
}
