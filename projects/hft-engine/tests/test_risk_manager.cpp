/**
 * @file test_risk_manager.cpp
 * @brief 风险管理器测试
 */

#include <iostream>
#include <cassert>

#include "risk/risk_manager.h"
#include "risk/position.h"
#include "risk/margin.h"
#include "risk/stop_loss.h"

using namespace hft;

/**
 * @brief 测试风险检查
 */
void test_risk_check() {
    std::cout << "Test risk check...\n";

    RiskLimits limits;
    limits.max_position_per_symbol = 1000;
    limits.max_daily_loss = 10000;

    RiskManager manager(limits);

    // 创建测试订单
    Order order;
    order.symbol = "AAPL";
    order.side = Side::BUY;
    order.type = OrderType::LIMIT;
    order.price = 150.0;
    order.quantity = 100;

    Position position;
    position.symbol = "AAPL";
    position.quantity = 500;

    // 测试通过
    auto result = manager.check_order(order, position);
    assert(result == RiskCheckResult::PASS);

    // 测试持仓限制
    order.quantity = 600;
    result = manager.check_order(order, position);
    assert(result == RiskCheckResult::POSITION_LIMIT);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试价格检查
 */
void test_price_check() {
    std::cout << "Test price check...\n";

    RiskLimits limits;
    limits.max_price_deviation = 0.05;

    RiskManager manager(limits);

    // 设置当前价格
    std::unordered_map<std::string, double> prices;
    prices["AAPL"] = 150.0;
    manager.update_prices(prices);

    // 测试正常价格
    Order order;
    order.symbol = "AAPL";
    order.side = Side::BUY;
    order.type = OrderType::LIMIT;
    order.price = 151.0;
    order.quantity = 100;

    Position position;
    auto result = manager.check_order(order, position);
    assert(result == RiskCheckResult::PASS);

    // 测试价格偏离过大
    order.price = 200.0;
    result = manager.check_order(order, position);
    assert(result == RiskCheckResult::PRICE_LIMIT);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试熔断
 */
void test_circuit_breaker() {
    std::cout << "Test circuit breaker...\n";

    RiskManager manager;

    // 触发熔断
    manager.trigger_circuit_breaker("Test");

    Order order;
    order.symbol = "AAPL";
    order.side = Side::BUY;
    order.type = OrderType::LIMIT;
    order.price = 150.0;
    order.quantity = 100;

    Position position;
    auto result = manager.check_order(order, position);
    assert(result == RiskCheckResult::SYSTEM_ERROR);

    // 解除熔断
    manager.reset_circuit_breaker();
    result = manager.check_order(order, position);
    assert(result == RiskCheckResult::PASS);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试持仓管理
 */
void test_position() {
    std::cout << "Test position management...\n";

    PositionManager manager;

    // 买入
    Trade trade1;
    trade1.symbol = "AAPL";
    trade1.side = Side::BUY;
    trade1.price = 150.0;
    trade1.quantity = 100;
    manager.update_position(trade1);

    auto pos = manager.get_position("AAPL");
    assert(pos.quantity == 100);
    assert(pos.avg_price == 150.0);

    // 加仓
    Trade trade2;
    trade2.symbol = "AAPL";
    trade2.side = Side::BUY;
    trade2.price = 151.0;
    trade2.quantity = 100;
    manager.update_position(trade2);

    pos = manager.get_position("AAPL");
    assert(pos.quantity == 200);
    assert(pos.avg_price > 150.0);

    // 平仓
    Trade trade3;
    trade3.symbol = "AAPL";
    trade3.side = Side::SELL;
    trade3.price = 152.0;
    trade3.quantity = 200;
    manager.update_position(trade3);

    pos = manager.get_position("AAPL");
    assert(pos.quantity == 0);
    assert(pos.realized_pnl > 0);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试保证金管理
 */
void test_margin() {
    std::cout << "Test margin management...\n";

    MarginConfig config;
    config.initial_margin_rate = 0.1;

    MarginManager manager(config, 1000000.0);

    // 检查保证金
    bool ok = manager.check_margin("AAPL", 150.0, 100);
    assert(ok);

    // 分配保证金
    ok = manager.allocate_margin("AAPL", 150.0, 100);
    assert(ok);

    // 释放保证金
    manager.release_margin("AAPL", 1500.0);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试止损
 */
void test_stop_loss() {
    std::cout << "Test stop loss...\n";

    StopLossManager manager;

    bool triggered = false;
    manager.set_trigger_callback([&](const StopOrder& stop) {
        triggered = true;
    });

    // 添加止损
    std::string stop_id = manager.add_fixed_stop("AAPL", Side::SELL, 145.0, 100);
    assert(!stop_id.empty());

    // 价格未触发
    manager.update_price("AAPL", 146.0);
    assert(!triggered);

    // 价格触发
    manager.update_price("AAPL", 144.0);
    assert(triggered);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试追踪止损
 */
void test_trailing_stop() {
    std::cout << "Test trailing stop...\n";

    StopLossManager manager;

    bool triggered = false;
    manager.set_trigger_callback([&](const StopOrder& stop) {
        triggered = true;
    });

    // 添加追踪止损
    std::string stop_id = manager.add_trailing_stop("AAPL", Side::SELL, 5.0, 100);

    // 价格上涨
    manager.update_price("AAPL", 150.0);
    manager.update_price("AAPL", 155.0);
    manager.update_price("AAPL", 160.0);

    // 价格回落，触发止损
    manager.update_price("AAPL", 154.0);
    assert(triggered);

    std::cout << "  PASSED\n";
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== Risk Manager Tests ===\n";

    test_risk_check();
    test_price_check();
    test_circuit_breaker();
    test_position();
    test_margin();
    test_stop_loss();
    test_trailing_stop();

    std::cout << "\nAll tests passed!\n";
    return 0;
}
