/**
 * @file async_example.cpp
 * @brief spdlog 异步日志示例
 * @details 展示 spdlog 的异步日志功能
 */

#include <iostream>
#include <string>
#include <thread>
#include <vector>
#include <spdlog/spdlog.h>
#include <spdlog/async.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/basic_file_sink.h>

/**
 * @brief 异步日志基础示例
 * @details 展示如何使用异步日志
 */
void async_basic() {
    std::cout << "=== 异步日志基础 ===" << std::endl;

    // 创建异步 logger
    auto async_logger = spdlog::stdout_color_mt<spdlog::async_factory>("async_logger");
    async_logger->set_level(spdlog::level::debug);

    // 使用异步 logger
    async_logger->info("This is an async log message");
    async_logger->debug("Debug message");
    async_logger->warn("Warning message");

    // 等待日志写入
    spdlog::shutdown();

    std::cout << std::endl;
}

/**
 * @brief 多线程异步日志示例
 * @details 展示多线程环境下的异步日志
 */
void async_multithreaded() {
    std::cout << "=== 多线程异步日志 ===" << std::endl;

    // 创建异步 logger
    auto async_logger = spdlog::stdout_color_mt<spdlog::async_factory>("async_mt");
    async_logger->set_level(spdlog::level::debug);

    // 多线程写入日志
    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&async_logger, i] {
            for (int j = 0; j < 10; ++j) {
                async_logger->info("Thread {} - Message {}", i, j);
            }
        });
    }

    // 等待所有线程完成
    for (auto& thread : threads) {
        thread.join();
    }

    // 等待日志写入
    spdlog::shutdown();

    std::cout << std::endl;
}

/**
 * @brief 异步文件日志示例
 * @details 展示异步文件日志的使用
 */
void async_file_logging() {
    std::cout << "=== 异步文件日志 ===" << std::endl;

    // 创建异步文件 logger
    auto async_logger = spdlog::basic_logger_mt<spdlog::async_factory>("async_file", "logs/async.log");
    async_logger->set_level(spdlog::level::info);

    // 写入日志
    for (int i = 0; i < 100; ++i) {
        async_logger->info("Log message {}", i);
    }

    // 等待日志写入
    spdlog::shutdown();

    std::cout << "Log messages written to logs/async.log" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 异步日志性能示例
 * @details 展示异步日志的性能优势
 */
void async_performance() {
    std::cout << "=== 异步日志性能 ===" << std::endl;

    std::cout << "异步日志优势：" << std::endl;
    std::cout << "  - 非阻塞写入" << std::endl;
    std::cout << "  - 高吞吐量" << std::endl;
    std::cout << "  - 适合高并发场景" << std::endl;
    std::cout << std::endl;

    std::cout << "使用场景：" << std::endl;
    std::cout << "  - 高并发服务器" << std::endl;
    std::cout << "  - 实时系统" << std::endl;
    std::cout << "  - 日志量大的应用" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief spdlog 异步日志概念
 * @details 介绍 spdlog 异步日志的核心概念
 */
void async_concepts() {
    std::cout << "=== spdlog 异步日志概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "核心概念：" << std::endl;
    std::cout << "  - async_factory: 异步 logger 工厂" << std::endl;
    std::cout << "  - 线程池: 后台日志处理线程" << std::endl;
    std::cout << "  - 队列: 日志消息队列" << std::endl;
    std::cout << std::endl;

    std::cout << "配置选项：" << std::endl;
    std::cout << "  - 队列大小" << std::endl;
    std::cout << "  - 线程数量" << std::endl;
    std::cout << "  - 超时设置" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== spdlog 异步日志示例 ===" << std::endl;
    std::cout << std::endl;

    async_concepts();
    async_performance();
    // async_basic();  // 取消注释以运行
    // async_multithreaded();  // 取消注释以运行
    // async_file_logging();  // 取消注释以运行

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}