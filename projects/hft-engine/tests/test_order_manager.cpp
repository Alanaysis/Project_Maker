/**
 * @file test_order_manager.cpp
 * @brief 订单管理器测试
 */

#include <iostream>
#include <cassert>

#include "order/order_manager.h"

using namespace hft;

/**
 * @brief 测试订单创建
 */
void test_create() {
    std::cout << "Test order creation...\n";

    OrderManager manager;

    auto order = manager.create_order("AAPL", Side::BUY, OrderType::LIMIT, 150.0, 100);

    assert(!order.order_id.empty());
    assert(order.symbol == "AAPL");
    assert(order.side == Side::BUY);
    assert(order.type == OrderType::LIMIT);
    assert(order.price == 150.0);
    assert(order.quantity == 100);
    assert(order.status == OrderStatus::CREATED);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试订单生命周期
 */
void test_lifecycle() {
    std::cout << "Test order lifecycle...\n";

    OrderManager manager;

    // 创建订单
    auto order = manager.create_order("AAPL", Side::BUY, OrderType::LIMIT, 150.0, 100);
    assert(order.status == OrderStatus::CREATED);

    // 发送订单
    assert(manager.send_order(order.order_id));
    auto* updated = manager.get_order(order.order_id);
    assert(updated->status == OrderStatus::SENT);

    // 确认订单
    assert(manager.acknowledge_order(order.order_id));
    updated = manager.get_order(order.order_id);
    assert(updated->status == OrderStatus::ACKNOWLEDGED);

    // 模拟成交
    ExecutionReport report;
    report.order_id = order.order_id;
    report.exec_id = "EXEC-1";
    report.status = OrderStatus::FILLED;
    report.last_price = 150.0;
    report.last_quantity = 100;
    report.timestamp = Timestamp::now();

    assert(manager.process_fill(report));
    updated = manager.get_order(order.order_id);
    assert(updated->status == OrderStatus::FILLED);
    assert(updated->filled_quantity == 100);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试订单取消
 */
void test_cancel() {
    std::cout << "Test order cancel...\n";

    OrderManager manager;

    auto order = manager.create_order("AAPL", Side::BUY, OrderType::LIMIT, 150.0, 100);
    manager.send_order(order.order_id);

    // 取消订单
    assert(manager.cancel_order(order.order_id));
    auto* updated = manager.get_order(order.order_id);
    assert(updated->status == OrderStatus::CANCELLED);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试订单拒绝
 */
void test_reject() {
    std::cout << "Test order reject...\n";

    OrderManager manager;

    auto order = manager.create_order("AAPL", Side::BUY, OrderType::LIMIT, 150.0, 100);

    // 拒绝订单
    assert(manager.reject_order(order.order_id, "Insufficient margin"));
    auto* updated = manager.get_order(order.order_id);
    assert(updated->status == OrderStatus::REJECTED);
    assert(updated->reject_reason == "Insufficient margin");

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试部分成交
 */
void test_partial_fill() {
    std::cout << "Test partial fill...\n";

    OrderManager manager;

    auto order = manager.create_order("AAPL", Side::BUY, OrderType::LIMIT, 150.0, 100);
    manager.send_order(order.order_id);
    manager.acknowledge_order(order.order_id);

    // 部分成交
    ExecutionReport report;
    report.order_id = order.order_id;
    report.exec_id = "EXEC-1";
    report.status = OrderStatus::PARTIALLY_FILLED;
    report.last_price = 150.0;
    report.last_quantity = 50;
    report.timestamp = Timestamp::now();

    assert(manager.process_fill(report));
    auto* updated = manager.get_order(order.order_id);
    assert(updated->status == OrderStatus::PARTIALLY_FILLED);
    assert(updated->filled_quantity == 50);
    assert(updated->remaining_quantity == 50);

    // 完全成交
    report.exec_id = "EXEC-2";
    report.last_quantity = 50;
    assert(manager.process_fill(report));
    updated = manager.get_order(order.order_id);
    assert(updated->status == OrderStatus::FILLED);
    assert(updated->filled_quantity == 100);
    assert(updated->remaining_quantity == 0);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试查询功能
 */
void test_query() {
    std::cout << "Test query functions...\n";

    OrderManager manager;

    // 创建多个订单
    manager.create_order("AAPL", Side::BUY, OrderType::LIMIT, 150.0, 100);
    manager.create_order("AAPL", Side::SELL, OrderType::LIMIT, 151.0, 200);
    manager.create_order("MSFT", Side::BUY, OrderType::LIMIT, 300.0, 50);

    assert(manager.order_count() == 3);

    // 按品种查询
    auto aapl_orders = manager.get_orders_by_symbol("AAPL");
    assert(aapl_orders.size() == 2);

    auto msft_orders = manager.get_orders_by_symbol("MSFT");
    assert(msft_orders.size() == 1);

    // 活跃订单查询
    auto active = manager.get_active_orders();
    assert(active.size() == 3);

    std::cout << "  PASSED\n";
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== Order Manager Tests ===\n";

    test_create();
    test_lifecycle();
    test_cancel();
    test_reject();
    test_partial_fill();
    test_query();

    std::cout << "\nAll tests passed!\n";
    return 0;
}
