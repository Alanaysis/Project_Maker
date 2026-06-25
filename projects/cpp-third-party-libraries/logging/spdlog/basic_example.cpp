/**
 * @file basic_example.cpp
 * @brief spdlog 日志库基础示例
 * @details 展示 spdlog 的基本用法
 *          spdlog 是一个快速的 C++ 日志库
 *          支持多种后端（控制台、文件、syslog 等）
 */

#include <iostream>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/basic_file_sink.h>

/**
 * @brief 基础日志示例
 * @details 展示 spdlog 的基本日志功能
 */
void basic_logging() {
    std::cout << "=== 基础日志 ===" << std::endl;

    // 设置日志级别
    spdlog::set_level(spdlog::level::debug);

    // 使用默认 logger
    spdlog::trace("This is a trace message");
    spdlog::debug("This is a debug message");
    spdlog::info("This is an info message");
    spdlog::warn("This is a warning message");
    spdlog::error("This is an error message");
    spdlog::critical("This is a critical message");

    std::cout << std::endl;
}

/**
 * @brief 格式化日志示例
 * @details 展示 spdlog 的格式化功能
 */
void formatted_logging() {
    std::cout << "=== 格式化日志 ===" << std::endl;

    // 使用 fmt 格式化
    spdlog::info("Hello, {}!", "World");
    spdlog::info("The answer is {}", 42);
    spdlog::info("Pi is approximately {:.2f}", 3.14159);

    // 多参数
    spdlog::info("User {} logged in from {}", "Alice", "192.168.1.1");

    // 命名参数
    spdlog::info("Server started on port {port}", fmt::arg("port", 8080));

    std::cout << std::endl;
}

/**
 * @brief 自定义 logger 示例
 * @details 展示如何创建和配置自定义 logger
 */
void custom_logger() {
    std::cout << "=== 自定义 Logger ===" << std::endl;

    // 创建控制台 logger
    auto console_logger = spdlog::stdout_color_mt("console");
    console_logger->set_level(spdlog::level::debug);
    console_logger->info("Console logger created");

    // 创建文件 logger
    auto file_logger = spdlog::basic_logger_mt("file", "logs/app.log");
    file_logger->set_level(spdlog::level::info);
    file_logger->info("File logger created");

    // 使用不同的 logger
    console_logger->debug("This goes to console");
    file_logger->info("This goes to file");

    std::cout << std::endl;
}

/**
 * @brief 日志级别示例
 * @details 展示如何使用不同的日志级别
 */
void log_levels() {
    std::cout << "=== 日志级别 ===" << std::endl;

    // 设置全局日志级别
    spdlog::set_level(spdlog::level::info);

    // 这些不会显示（级别低于 info）
    spdlog::trace("Trace: detailed debugging");
    spdlog::debug("Debug: debugging info");

    // 这些会显示
    spdlog::info("Info: general information");
    spdlog::warn("Warn: potential issues");
    spdlog::error("Error: error conditions");
    spdlog::critical("Critical: severe errors");

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 spdlog 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 创建应用 logger
    auto logger = spdlog::stdout_color_mt("app");
    logger->set_level(spdlog::level::debug);

    // 模拟应用启动
    logger->info("Application starting...");

    // 模拟配置加载
    logger->debug("Loading configuration from config.json");
    logger->info("Configuration loaded successfully");

    // 模拟数据库连接
    logger->info("Connecting to database...");
    logger->info("Database connected");

    // 模拟错误处理
    try {
        // 模拟一个错误
        throw std::runtime_error("Connection timeout");
    } catch (const std::exception& e) {
        logger->error("Database connection failed: {}", e.what());
    }

    // 模拟性能日志
    auto start = std::chrono::high_resolution_clock::now();
    // 模拟一些工作
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    logger->info("Operation completed in {} microseconds", duration.count());

    logger->info("Application shutdown");

    std::cout << std::endl;
}

int main() {
    std::cout << "=== spdlog 日志库示例 ===" << std::endl;
    std::cout << std::endl;

    basic_logging();
    formatted_logging();
    custom_logger();
    log_levels();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}