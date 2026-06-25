#include <iostream>
#include <fmt/format.h>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_sinks.h>
#include <nlohmann/json.hpp>

/**
 * @file vcpkg_demo.cpp
 * @brief vcpkg 包管理器示例
 *
 * 演示如何使用 vcpkg 安装和使用第三方库。
 * 本示例使用了 fmt、spdlog 和 nlohmann-json 三个库。
 */

int main() {
    std::cout << "=== vcpkg 包管理器示例 ===" << std::endl;
    std::cout << std::endl;

    // 使用 fmt 库
    std::cout << "--- fmt 库 ---" << std::endl;
    std::cout << fmt::format("Hello, {}! You are {} years old.", "World", 25) << std::endl;
    std::cout << fmt::format("Pi = {:.6f}", 3.14159265358979) << std::endl;

    // 使用 spdlog 库
    std::cout << std::endl;
    std::cout << "--- spdlog 库 ---" << std::endl;
    auto logger = spdlog::stdout_logger_mt("console");
    logger->info("Hello from spdlog!");
    logger->warn("This is a warning");

    // 使用 nlohmann-json 库
    std::cout << std::endl;
    std::cout << "--- nlohmann-json 库 ---" << std::endl;
    nlohmann::json j;
    j["name"] = "vcpkg-example";
    j["version"] = "1.0.0";
    j["dependencies"] = {"fmt", "spdlog", "nlohmann-json"};
    std::cout << j.dump(2) << std::endl;

    std::cout << std::endl;
    std::cout << "vcpkg 使用说明:" << std::endl;
    std::cout << "  1. 在 vcpkg.json 中声明依赖" << std::endl;
    std::cout << "  2. 使用 -DCMAKE_TOOLCHAIN_FILE 指定 vcpkg 工具链" << std::endl;
    std::cout << "  3. CMake 会自动查找和链接依赖" << std::endl;

    return 0;
}
