#include <iostream>
#include <fmt/format.h>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_sinks.h>

/**
 * @file conan_demo.cpp
 * @brief Conan 包管理器示例
 *
 * 演示如何使用 Conan 安装和使用第三方库。
 */

int main() {
    std::cout << "=== Conan 包管理器示例 ===" << std::endl;
    std::cout << std::endl;

    // 使用 fmt 库
    std::cout << "--- fmt 库 ---" << std::endl;
    std::cout << fmt::format("Hello, {}! You are {} years old.", "World", 25) << std::endl;

    // 使用 spdlog 库
    std::cout << std::endl;
    std::cout << "--- spdlog 库 ---" << std::endl;
    auto logger = spdlog::stdout_logger_mt("console");
    logger->info("Hello from spdlog via Conan!");

    std::cout << std::endl;
    std::cout << "Conan 使用说明:" << std::endl;
    std::cout << "  1. 在 conanfile.txt 中声明依赖" << std::endl;
    std::cout << "  2. 运行 conan install 安装依赖" << std::endl;
    std::cout << "  3. 使用生成的工具链文件配置 CMake" << std::endl;

    return 0;
}
