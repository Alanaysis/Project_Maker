/**
 * 基础示例：演示撮合引擎的基本用法
 *
 * 这个示例展示了：
 * 1. 如何创建订单管理器
 * 2. 如何提交买单和卖单
 * 3. 如何查看订单簿状态
 * 4. 如何查看成交记录
 *
 * 运行方式：
 *   cd build && ./examples/basic_example
 */

#include "order_manager.h"
#include <iostream>

int main() {
    std::cout << "=== 高频交易引擎 - 基础示例 ===" << std::endl;
    std::cout << std::endl;

    // 创建订单管理器
    hft::OrderManager manager;

    // 示例1：提交限价单
    std::cout << "1. 提交限价单" << std::endl;
    std::cout << "---------------" << std::endl;

    // 提交买单：价格100，数量10
    auto buy1 = manager.submit_buy_order(100, 10);
    std::cout << "提交买单 ID: " << buy1
              << " | 价格: 100 | 数量: 10" << std::endl;

    // 提交卖单：价格105，数量5
    auto sell1 = manager.submit_sell_order(105, 5);
    std::cout << "提交卖单 ID: " << sell1
              << " | 价格: 105 | 数量: 5" << std::endl;

    // 提交更多买单
    auto buy2 = manager.submit_buy_order(99, 15);
    std::cout << "提交买单 ID: " << buy2
              << " | 价格: 99 | 数量: 15" << std::endl;

    // 提交更多卖单
    auto sell2 = manager.submit_sell_order(103, 8);
    std::cout << "提交卖单 ID: " << sell2
              << " | 价格: 103 | 数量: 8" << std::endl;

    std::cout << std::endl;

    // 示例2：查看订单簿状态
    std::cout << "2. 订单簿状态" << std::endl;
    std::cout << "---------------" << std::endl;
    manager.print_order_book();
    std::cout << std::endl;

    // 示例3：查看最优价格
    std::cout << "3. 最优价格" << std::endl;
    std::cout << "---------------" << std::endl;
    std::cout << "最优买价: " << manager.best_bid() << std::endl;
    std::cout << "最优卖价: " << manager.best_ask() << std::endl;
    std::cout << std::endl;

    // 示例4：提交可撮合的订单
    std::cout << "4. 提交可撮合的订单" << std::endl;
    std::cout << "---------------" << std::endl;

    // 提交一个价格为105的买单，可以与卖单撮合
    auto buy3 = manager.submit_buy_order(105, 3);
    std::cout << "提交买单 ID: " << buy3
              << " | 价格: 105 | 数量: 3" << std::endl;

    std::cout << std::endl;

    // 示例5：查看订单簿更新后的状态
    std::cout << "5. 更新后的订单簿" << std::endl;
    std::cout << "---------------" << std::endl;
    manager.print_order_book();
    std::cout << std::endl;

    // 示例6：取消订单
    std::cout << "6. 取消订单" << std::endl;
    std::cout << "---------------" << std::endl;
    bool cancelled = manager.cancel_order(buy2);
    std::cout << "取消订单 " << buy2 << ": "
              << (cancelled ? "成功" : "失败") << std::endl;

    std::cout << std::endl;

    // 示例7：最终状态
    std::cout << "7. 最终状态" << std::endl;
    std::cout << "---------------" << std::endl;
    manager.print_order_book();

    std::cout << std::endl;
    std::cout << "=== 示例结束 ===" << std::endl;

    return 0;
}
