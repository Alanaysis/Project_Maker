#include <iostream>
#include <fmt/format.h>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_sinks.h>

/**
 * @file fetchcontent_demo.cpp
 * @brief FetchContent 示例
 *
 * 演示如何使用 CMake FetchContent 拉取第三方库。
 * 本示例拉取了 fmt 和 spdlog 两个库。
 */

int main() {
    std::cout << "=== FetchContent 示例 ===" << std::endl;
    std::cout << std::endl;

    // 使用 fmt 库
    std::cout << "--- fmt 库示例 ---" << std::endl;
    std::string message = fmt::format("Hello, {}! You are {} years old.", "World", 25);
    std::cout << message << std::endl;

    // 格式化数字
    std::cout << fmt::format("Pi = {:.6f}", 3.14159265358979) << std::endl;
    std::cout << fmt::format("Hex: {:#x}", 255) << std::endl;
    std::cout << fmt::format("Binary: {:#b}", 42) << std::endl;
    std::cout << std::endl;

    // 使用 spdlog 库
    std::cout << "--- spdlog 库示例 ---" << std::endl;
    auto logger = spdlog::stdout_logger_mt("console");
    logger->set_level(spdlog::level::debug);

    logger->debug("Debug message");
    logger->info("Info message");
    logger->warn("Warning message");
    logger->error("Error message");

    // 格式化日志
    logger->info("User {} logged in from {}", "admin", "192.168.1.1");

    std::cout << std::endl;
    std::cout << "FetchContent 说明:" << std::endl;
    std::cout << "  - FetchContent_Declare() 声明依赖" << std::endl;
    std::cout << "  - FetchContent_MakeAvailable() 拉取并添加" << std::endl;
    std::cout << "  - 支持 Git、URL、SVN 等源" << std::endl;
    std::cout << "  - 推荐用于中小型依赖" << std::endl;

    return 0;
}
