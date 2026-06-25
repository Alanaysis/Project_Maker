/**
 * @file strategy_example.cpp
 * @brief 策略示例
 *
 * 演示如何使用交易策略模块。
 */

#include <iostream>
#include <thread>
#include <chrono>

#include "core/timestamp.h"
#include "core/logger.h"
#include "order/order_manager.h"
#include "strategy/market_maker.h"
#include "strategy/trend_follower.h"
#include "risk/risk_manager.h"

using namespace hft;

/**
 * @brief 演示做市策略
 */
void demo_market_maker() {
    std::cout << "\n=== Market Maker Strategy Demo ===\n";

    OrderManager order_manager;

    // 设置回调
    order_manager.set_order_callback([](const Order& order) {
        std::cout << "Order: " << order.to_string() << "\n";
    });

    order_manager.set_trade_callback([](const Trade& trade) {
        std::cout << "Trade: " << trade.to_string() << "\n";
    });

    // 创建做市策略
    MarketMakerConfig config;
    config.base_spread = 0.001;
    config.quote_size = 100;
    config.max_position = 500;

    MarketMaker strategy(config, order_manager);
    strategy.on_init();
    strategy.on_start();

    // 模拟行情
    for (int i = 0; i < 20; ++i) {
        Tick tick;
        tick.symbol = "AAPL";
        tick.timestamp = Timestamp::now();
        tick.last_price = 150.0 + (rand() % 100 - 50) / 1000.0;
        tick.bid_price = tick.last_price - 0.01;
        tick.ask_price = tick.last_price + 0.01;
        tick.bid_quantity = 1000;
        tick.ask_quantity = 1000;

        strategy.on_tick(tick);
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }

    // 显示结果
    std::cout << "\nStrategy Results:\n";
    std::cout << "  Inventory: " << strategy.inventory() << "\n";
    std::cout << "  Realized PnL: " << strategy.realized_pnl() << "\n";
    std::cout << "  Unrealized PnL: " << strategy.unrealized_pnl() << "\n";
    std::cout << "  Total PnL: " << strategy.total_pnl() << "\n";

    strategy.on_stop();
}

/**
 * @brief 演示趋势策略
 */
void demo_trend_follower() {
    std::cout << "\n=== Trend Follower Strategy Demo ===\n";

    OrderManager order_manager;

    // 创建趋势策略
    TrendFollowerConfig config;
    config.fast_period = 5;
    config.slow_period = 20;
    config.trade_size = 100;

    TrendFollower strategy(config, order_manager, "AAPL");
    strategy.on_init();
    strategy.on_start();

    // 生成趋势数据
    double price = 150.0;
    for (int i = 0; i < 100; ++i) {
        // 模拟上涨趋势
        price += 0.1 + (rand() % 100 - 50) / 10000.0;

        Tick tick;
        tick.symbol = "AAPL";
        tick.timestamp = Timestamp::now();
        tick.last_price = price;
        tick.bid_price = price - 0.01;
        tick.ask_price = price + 0.01;

        strategy.on_tick(tick);
    }

    // 显示结果
    std::cout << "\nStrategy Results:\n";
    std::cout << "  Position: " << strategy.position() << "\n";
    std::cout << "  Realized PnL: " << strategy.realized_pnl() << "\n";
    std::cout << "  Fast MA: " << strategy.fast_ma() << "\n";
    std::cout << "  Slow MA: " << strategy.slow_ma() << "\n";

    strategy.on_stop();
}

/**
 * @brief 演示风险管理
 */
void demo_risk_management() {
    std::cout << "\n=== Risk Management Demo ===\n";

    RiskLimits limits;
    limits.max_position_per_symbol = 1000;
    limits.max_daily_loss = 10000;
    limits.max_price_deviation = 0.05;

    RiskManager risk_manager(limits);

    // 设置告警回调
    risk_manager.set_alert_callback([](const std::string& type,
                                       const std::string& message) {
        std::cout << "ALERT [" << type << "]: " << message << "\n";
    });

    // 测试订单检查
    Order order;
    order.symbol = "AAPL";
    order.side = Side::BUY;
    order.type = OrderType::LIMIT;
    order.price = 150.0;
    order.quantity = 100;

    Position position;
    position.symbol = "AAPL";
    position.quantity = 500;

    auto result = risk_manager.check_order(order, position);
    std::cout << "Risk Check: " << risk_check_result_to_string(result) << "\n";

    // 更新盈亏
    risk_manager.update_pnl(1000);
    risk_manager.update_pnl(-500);

    auto metrics = risk_manager.metrics();
    std::cout << "Total PnL: " << metrics.total_pnl << "\n";
    std::cout << "Daily PnL: " << metrics.daily_pnl << "\n";

    // 测试熔断
    risk_manager.trigger_circuit_breaker("Test circuit breaker");
    std::cout << "Circuit Breaker: "
              << (risk_manager.is_circuit_breaker() ? "ACTIVE" : "INACTIVE") << "\n";

    risk_manager.reset_circuit_breaker();
    std::cout << "Circuit Breaker: "
              << (risk_manager.is_circuit_breaker() ? "ACTIVE" : "INACTIVE") << "\n";
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== Trading Strategy Examples ===\n";

    Logger::instance().init("", LogLevel::INFO);

    demo_market_maker();
    demo_trend_follower();
    demo_risk_management();

    Logger::instance().shutdown();

    std::cout << "\n=== All Examples Completed ===\n";
    return 0;
}
