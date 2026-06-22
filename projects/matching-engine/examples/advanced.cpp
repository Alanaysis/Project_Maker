/**
 * 高级示例：演示撮合引擎的高级用法
 *
 * 这个示例展示了：
 * 1. 市价单的处理
 * 2. 批量订单提交
 * 3. 订单簿深度分析
 * 4. 性能测试
 *
 * 运行方式：
 *   cd build && ./examples/advanced_example
 */

#include "matching_engine.h"
#include "order_manager.h"
#include <iostream>
#include <chrono>
#include <vector>
#include <random>

// 辅助函数：生成随机订单
hft::Order generate_random_order(std::mt19937& gen, hft::OrderId id) {
    std::uniform_int_distribution<> side_dist(0, 1);
    std::uniform_int_distribution<> price_dist(90, 110);
    std::uniform_int_distribution<> quantity_dist(1, 100);

    hft::Order order;
    order.id = id;
    order.side = side_dist(gen) == 0 ? hft::Side::Buy : hft::Side::Sell;
    order.type = hft::OrderType::Limit;
    order.price = price_dist(gen);
    order.quantity = quantity_dist(gen);
    order.filled_quantity = 0;
    order.status = hft::OrderStatus::New;
    order.timestamp = std::chrono::duration_cast<hft::Timestamp>(
        std::chrono::steady_clock::now().time_since_epoch()
    );

    return order;
}

void demo_market_orders() {
    std::cout << "=== 市价单演示 ===" << std::endl;
    std::cout << std::endl;

    hft::MatchingEngine engine;

    // 先添加一些限价单作为流动性
    hft::Order sell1;
    sell1.id = 1;
    sell1.side = hft::Side::Sell;
    sell1.type = hft::OrderType::Limit;
    sell1.price = 100;
    sell1.quantity = 10;
    sell1.filled_quantity = 0;
    sell1.status = hft::OrderStatus::New;
    sell1.timestamp = std::chrono::duration_cast<hft::Timestamp>(
        std::chrono::steady_clock::now().time_since_epoch()
    );

    hft::Order sell2;
    sell2.id = 2;
    sell2.side = hft::Side::Sell;
    sell2.type = hft::OrderType::Limit;
    sell2.price = 101;
    sell2.quantity = 15;
    sell2.filled_quantity = 0;
    sell2.status = hft::OrderStatus::New;
    sell2.timestamp = std::chrono::duration_cast<hft::Timestamp>(
        std::chrono::steady_clock::now().time_since_epoch()
    );

    engine.submit_order(sell1);
    engine.submit_order(sell2);

    std::cout << "添加卖单后订单簿:" << std::endl;
    engine.order_book().print();
    std::cout << std::endl;

    // 提交市价买单
    hft::Order market_buy;
    market_buy.id = 3;
    market_buy.side = hft::Side::Buy;
    market_buy.type = hft::OrderType::Market;
    market_buy.price = 0;  // 市价单不需要价格
    market_buy.quantity = 12;
    market_buy.filled_quantity = 0;
    market_buy.status = hft::OrderStatus::New;
    market_buy.timestamp = std::chrono::duration_cast<hft::Timestamp>(
        std::chrono::steady_clock::now().time_since_epoch()
    );

    auto trades = engine.submit_order(market_buy);

    std::cout << "提交市价买单后:" << std::endl;
    std::cout << "成交数量: " << trades.size() << std::endl;

    std::cout << std::endl;
}

void demo_batch_orders() {
    std::cout << "=== 批量订单演示 ===" << std::endl;
    std::cout << std::endl;

    hft::MatchingEngine engine;
    std::mt19937 gen(42);  // 固定种子以便复现

    // 批量提交订单
    const int num_orders = 100;
    auto start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < num_orders; i++) {
        auto order = generate_random_order(gen, i + 1);
        engine.submit_order(order);
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "提交 " << num_orders << " 个订单" << std::endl;
    std::cout << "耗时: " << duration.count() << " 微秒" << std::endl;
    std::cout << "平均每个订单: " << duration.count() / num_orders << " 微秒" << std::endl;
    std::cout << std::endl;

    // 显示订单簿状态
    std::cout << "订单簿状态:" << std::endl;
    engine.order_book().print();

    std::cout << std::endl;
}

void demo_order_book_depth() {
    std::cout << "=== 订单簿深度分析 ===" << std::endl;
    std::cout << std::endl;

    hft::OrderManager manager;

    // 创建一个有深度的订单簿
    for (int price = 95; price <= 105; price++) {
        manager.submit_buy_order(price, 10 * (price - 94));
        manager.submit_sell_order(price + 10, 10 * (106 - price));
    }

    std::cout << "订单簿:" << std::endl;
    manager.print_order_book();
    std::cout << std::endl;

    // 获取深度信息
    auto snapshot = manager.get_snapshot(5);

    std::cout << "买方深度 (前5层):" << std::endl;
    for (const auto& level : snapshot.bids) {
        std::cout << "  价格: " << level.price
                  << " | 数量: " << level.total_quantity
                  << " | 订单数: " << level.order_count << std::endl;
    }

    std::cout << std::endl;

    std::cout << "卖方深度 (前5层):" << std::endl;
    for (const auto& level : snapshot.asks) {
        std::cout << "  价格: " << level.price
                  << " | 数量: " << level.total_quantity
                  << " | 订单数: " << level.order_count << std::endl;
    }

    std::cout << std::endl;
}

void demo_performance_test() {
    std::cout << "=== 性能测试 ===" << std::endl;
    std::cout << std::endl;

    hft::MatchingEngine engine;
    std::mt19937 gen(123);

    const int num_orders = 10000;
    std::vector<hft::Order> orders;

    // 预生成订单
    for (int i = 0; i < num_orders; i++) {
        orders.push_back(generate_random_order(gen, i + 1));
    }

    // 测试提交性能
    auto start = std::chrono::high_resolution_clock::now();

    for (auto& order : orders) {
        engine.submit_order(order);
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "提交 " << num_orders << " 个订单" << std::endl;
    std::cout << "总耗时: " << duration.count() << " 微秒" << std::endl;
    std::cout << "平均延迟: " << static_cast<double>(duration.count()) / num_orders
              << " 微秒/订单" << std::endl;
    std::cout << "吞吐量: " << (num_orders * 1000000.0) / duration.count()
              << " 订单/秒" << std::endl;
    std::cout << std::endl;

    std::cout << "成交记录数: " << engine.trade_history().size() << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== 高频交易引擎 - 高级示例 ===" << std::endl;
    std::cout << std::endl;

    demo_market_orders();
    demo_batch_orders();
    demo_order_book_depth();
    demo_performance_test();

    std::cout << "=== 所有示例完成 ===" << std::endl;

    return 0;
}
