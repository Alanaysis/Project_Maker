/**
 * @file basic_example.cpp
 * @brief Folly Futures 异步编程基础示例
 * @details 展示 Folly Futures 的基本用法
 *          Folly 是 Facebook 开源的 C++ 基础库
 *          Futures 提供了强大的异步编程支持
 */

#include <iostream>
#include <string>
#include <future>
#include <folly/futures/Future.h>
#include <folly/executors/ThreadedExecutor.h>

/**
 * @brief Folly Futures 概念说明
 * @details 介绍 Folly Futures 的核心概念
 */
void futures_concepts() {
    std::cout << "=== Folly Futures 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "Folly Futures 是 Facebook 开发的异步编程库。" << std::endl;
    std::cout << std::endl;

    std::cout << "核心概念：" << std::endl;
    std::cout << "  - Future: 异步操作的结果" << std::endl;
    std::cout << "  - Promise: 产生 Future 的对象" << std::endl;
    std::cout << "  - Executor: 执行任务的线程池" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  - 链式调用" << std::endl;
    std::cout << "  - 错误处理" << std::endl;
    std::cout << "  - 超时控制" << std::endl;
    std::cout << "  - 协程支持" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 基础用法示例
 * @details 展示 Future 的基本使用
 */
void basic_usage() {
    std::cout << "=== 基础用法 ===" << std::endl;

    // 创建 Promise
    folly::Promise<int> promise;
    folly::Future<int> future = promise.getFuture();

    // 设置值
    promise.setValue(42);

    // 获取值
    int value = future.get();
    std::cout << "Value: " << value << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 链式调用示例
 * @details 展示 Future 的链式调用
 */
void chaining() {
    std::cout << "=== 链式调用 ===" << std::endl;

    folly::ThreadedExecutor executor;

    // 创建异步任务
    folly::Future<int> future = folly::via(&executor).then([] {
        return 42;
    });

    // 链式处理
    folly::Future<std::string> result = future
        .then([](int value) {
            return value * 2;
        })
        .then([](int value) {
            return "Result: " + std::to_string(value);
        });

    // 获取结果
    std::cout << result.get() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 错误处理示例
 * @details 展示 Future 的错误处理
 */
void error_handling() {
    std::cout << "=== 错误处理 ===" << std::endl;

    folly::ThreadedExecutor executor;

    // 创建可能失败的异步任务
    folly::Future<int> future = folly::via(&executor).then([] {
        // 模拟错误
        throw std::runtime_error("Something went wrong");
        return 42;
    });

    // 处理错误
    folly::Future<std::string> result = future
        .then([](int value) {
            return "Success: " + std::to_string(value);
        })
        .onError([](const std::exception& e) {
            return "Error: " + std::string(e.what());
        });

    std::cout << result.get() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 多任务组合示例
 * @details 展示如何组合多个 Future
 */
void combining_futures() {
    std::cout << "=== 组合多个 Future ===" << std::endl;

    folly::ThreadedExecutor executor;

    // 创建多个异步任务
    folly::Future<int> future1 = folly::via(&executor).then([] {
        return 10;
    });

    folly::Future<int> future2 = folly::via(&executor).then([] {
        return 20;
    });

    folly::Future<int> future3 = folly::via(&executor).then([] {
        return 30;
    });

    // 等待所有任务完成
    folly::Future<int> total = folly::collectAll(
        std::move(future1),
        std::move(future2),
        std::move(future3)
    ).then([](std::tuple<folly::Try<int>, folly::Try<int>, folly::Try<int>> results) {
        int sum = 0;
        sum += std::get<0>(results).value();
        sum += std::get<1>(results).value();
        sum += std::get<2>(results).value();
        return sum;
    });

    std::cout << "Total: " << total.get() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 Folly Futures 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    folly::ThreadedExecutor executor;

    // 场景：异步数据处理
    folly::Future<std::string> data = folly::via(&executor).then([] {
        // 模拟数据获取
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        return "raw data";
    });

    folly::Future<std::string> processed = data
        .then([](const std::string& raw) {
            // 模拟数据处理
            return "processed: " + raw;
        })
        .then([](const std::string& result) {
            // 模拟格式化
            return "[" + result + "]";
        });

    std::cout << "Result: " << processed.get() << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Folly Futures 异步编程示例 ===" << std::endl;
    std::cout << std::endl;

    futures_concepts();
    basic_usage();
    chaining();
    error_handling();
    combining_futures();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}