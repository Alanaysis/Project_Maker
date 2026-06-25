/**
 * @file main.cpp
 * @brief 高频交易引擎主程序
 *
 * 演示高频交易引擎的核心功能，包括：
 * - 市场数据处理
 * - 订单管理
 * - 交易策略
 * - 风险管理
 * - 回测系统
 */

#include <iostream>
#include <memory>
#include <thread>
#include <chrono>

#include "core/timestamp.h"
#include "core/logger.h"
#include "core/ring_buffer.h"
#include "core/memory_pool.h"

#include "market_data/tick.h"
#include "market_data/order_book.h"
#include "market_data/feed_handler.h"
#include "market_data/tick_store.h"

#include "order/order.h"
#include "order/order_manager.h"
#include "order/order_router.h"

#include "strategy/strategy.h"
#include "strategy/market_maker.h"
#include "strategy/arbitrage.h"
#include "strategy/trend_follower.h"
#include "strategy/stat_arb.h"

#include "risk/position.h"
#include "risk/risk_manager.h"
#include "risk/margin.h"
#include "risk/stop_loss.h"

#include "backtest/backtester.h"
#include "backtest/performance.h"
#include "backtest/risk_analyzer.h"

using namespace hft;

/**
 * @brief 演示市场数据处理
 */
void demo_market_data() {
    std::cout << "\n=== Market Data Demo ===\n";

    // 创建订单簿
    OrderBook order_book("AAPL");

    // 模拟订单簿更新
    OrderBookUpdate update;
    update.symbol = "AAPL";
    update.timestamp = Timestamp::now();

    // 添加买盘
    update.side = Side::BUY;
    for (int i = 0; i < 5; ++i) {
        update.price = 150.0 - i * 0.01;
        update.quantity = 1000 - i * 100;
        order_book.update(update);
    }

    // 添加卖盘
    update.side = Side::SELL;
    for (int i = 0; i < 5; ++i) {
        update.price = 150.01 + i * 0.01;
        update.quantity = 1000 - i * 100;
        order_book.update(update);
    }

    // 显示订单簿
    std::cout << "Order Book:\n";
    std::cout << "  Best Bid: " << order_book.best_bid() << "\n";
    std::cout << "  Best Ask: " << order_book.best_ask() << "\n";
    std::cout << "  Mid Price: " << order_book.mid_price() << "\n";
    std::cout << "  Spread: " << order_book.spread() << "\n";

    // 创建模拟行情源
    SimulatedFeedHandler feed("Simulated");
    feed.set_tick_callback([](const Tick& tick) {
        std::cout << "Tick: " << tick.symbol << " "
                  << tick.last_price << " x " << tick.last_quantity << "\n";
    });

    // 生成模拟数据
    for (int i = 0; i < 5; ++i) {
        feed.generate_tick("AAPL", 150.0);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

/**
 * @brief 演示订单管理
 */
void demo_order_management() {
    std::cout << "\n=== Order Management Demo ===\n";

    // 创建订单管理器
    OrderManager order_manager;

    // 设置回调
    order_manager.set_order_callback([](const Order& order) {
        std::cout << "Order Update: " << order.to_string() << "\n";
    });

    order_manager.set_trade_callback([](const Trade& trade) {
        std::cout << "Trade: " << trade.to_string() << "\n";
    });

    // 创建订单
    auto order = order_manager.create_order(
        "AAPL", Side::BUY, OrderType::LIMIT, 150.0, 100
    );
    std::cout << "Created: " << order.to_string() << "\n";

    // 发送订单
    order_manager.send_order(order.order_id);

    // 确认订单
    order_manager.acknowledge_order(order.order_id);

    // 模拟成交
    ExecutionReport report;
    report.order_id = order.order_id;
    report.exec_id = "EXEC-1";
    report.status = OrderStatus::FILLED;
    report.last_price = 150.0;
    report.last_quantity = 100;
    report.timestamp = Timestamp::now();

    order_manager.process_fill(report);

    // 显示统计
    std::cout << "Total Orders: " << order_manager.order_count() << "\n";
    std::cout << "Active Orders: " << order_manager.active_order_count() << "\n";
}

/**
 * @brief 演示做市策略
 */
void demo_market_maker() {
    std::cout << "\n=== Market Maker Demo ===\n";

    OrderManager order_manager;

    // 创建做市策略
    MarketMakerConfig config;
    config.base_spread = 0.001;
    config.quote_size = 100;
    config.max_position = 500;

    MarketMaker strategy(config, order_manager);
    strategy.on_init();
    strategy.on_start();

    // 模拟 Tick 数据
    for (int i = 0; i < 10; ++i) {
        Tick tick;
        tick.symbol = "AAPL";
        tick.timestamp = Timestamp::now();
        tick.last_price = 150.0 + (rand() % 100 - 50) / 1000.0;
        tick.bid_price = tick.last_price - 0.01;
        tick.ask_price = tick.last_price + 0.01;
        tick.bid_quantity = 1000;
        tick.ask_quantity = 1000;

        strategy.on_tick(tick);
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    // 显示策略状态
    std::cout << "Inventory: " << strategy.inventory() << "\n";
    std::cout << "Realized PnL: " << strategy.realized_pnl() << "\n";
    std::cout << "Unrealized PnL: " << strategy.unrealized_pnl() << "\n";

    strategy.on_stop();
}

/**
 * @brief 演示风险管理
 */
void demo_risk_management() {
    std::cout << "\n=== Risk Management Demo ===\n";

    // 创建风险管理器
    RiskLimits limits;
    limits.max_position_per_symbol = 1000;
    limits.max_daily_loss = 10000;

    RiskManager risk_manager(limits);

    // 创建持仓管理器
    PositionManager position_manager;

    // 创建保证金管理器
    MarginManager margin_manager;

    // 创建止损管理器
    StopLossManager stop_loss_manager;

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

    // 测试保证金检查
    bool margin_ok = margin_manager.check_margin("AAPL", 150.0, 100);
    std::cout << "Margin Check: " << (margin_ok ? "PASS" : "FAIL") << "\n";

    // 测试止损
    std::string stop_id = stop_loss_manager.add_fixed_stop(
        "AAPL", Side::SELL, 145.0, 100
    );
    std::cout << "Stop Loss Added: " << stop_id << "\n";

    // 模拟价格更新
    stop_loss_manager.update_price("AAPL", 144.0);
}

/**
 * @brief 演示回测系统
 */
void demo_backtest() {
    std::cout << "\n=== Backtest Demo ===\n";

    // 创建性能分析器
    PerformanceAnalyzer analyzer(1000000.0);

    // 模拟每日收益
    for (int i = 0; i < 252; ++i) {
        double daily_return = (rand() % 200 - 100) / 10000.0;
        analyzer.add_daily_return(daily_return);
    }

    // 显示性能报告
    std::cout << analyzer.generate_report();

    // 创建风险分析器
    RiskAnalyzer risk_analyzer(0.95);

    // 添加收益数据
    std::vector<double> returns;
    for (int i = 0; i < 1000; ++i) {
        returns.push_back((rand() % 200 - 100) / 10000.0);
    }
    risk_analyzer.add_returns(returns);

    // 显示风险报告
    std::cout << risk_analyzer.generate_report();
}

/**
 * @brief 演示性能测试
 */
void demo_performance() {
    std::cout << "\n=== Performance Demo ===\n";

    // 测试环形缓冲区
    {
        RingBuffer<int, 1024> buffer;

        auto start = Timestamp::now();

        for (int i = 0; i < 1000000; ++i) {
            buffer.try_push(i);
            buffer.try_pop();
        }

        auto end = Timestamp::now();
        int64_t duration_ns = end - start;

        std::cout << "Ring Buffer (1M operations): "
                  << duration_ns / 1000000 << " ms\n";
    }

    // 测试内存池
    {
        MemoryPool<int> pool;

        auto start = Timestamp::now();

        for (int i = 0; i < 1000000; ++i) {
            int* ptr = pool.allocate();
            *ptr = i;
            pool.deallocate(ptr);
        }

        auto end = Timestamp::now();
        int64_t duration_ns = end - start;

        std::cout << "Memory Pool (1M allocations): "
                  << duration_ns / 1000000 << " ms\n";
    }
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== High Frequency Trading Engine ===\n";
    std::cout << "Version 1.0.0\n";
    std::cout << "C++ Standard: " << __cplusplus << "\n";

    // 初始化日志
    Logger::instance().init("", LogLevel::INFO);

    try {
        // 运行各个演示
        demo_market_data();
        demo_order_management();
        demo_market_maker();
        demo_risk_management();
        demo_backtest();
        demo_performance();

        std::cout << "\n=== All Demos Completed ===\n";
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    // 关闭日志
    Logger::instance().shutdown();

    return 0;
}
