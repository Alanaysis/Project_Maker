#include <iostream>
#include <fmt/format.h>
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_sinks.h>
#include <nlohmann/json.hpp>

/**
 * @file fetchcontent_demo.cpp
 * @brief FetchContent 示例
 *
 * 演示如何使用 CMake FetchContent 拉取多个第三方库。
 */

int main() {
    std::cout << "=== FetchContent 示例 ===" << std::endl;
    std::cout << std::endl;

    // fmt 库
    std::cout << "--- fmt 库 ---" << std::endl;
    std::cout << fmt::format("Hello, {}!", "FetchContent") << std::endl;

    // spdlog 库
    std::cout << std::endl;
    std::cout << "--- spdlog 库 ---" << std::endl;
    auto logger = spdlog::stdout_logger_mt("console");
    logger->info("Hello from spdlog!");

    // nlohmann-json 库
    std::cout << std::endl;
    std::cout << "--- nlohmann-json 库 ---" << std::endl;
    nlohmann::json j;
    j["name"] = "FetchContent Example";
    j["libraries"] = {"fmt", "spdlog", "nlohmann-json", "googletest"};
    std::cout << j.dump(2) << std::endl;

    std::cout << std::endl;
    std::cout << "FetchContent 说明:" << std::endl;
    std::cout << "  - FetchContent_Declare(): 声明依赖" << std::endl;
    std::cout << "  - FetchContent_MakeAvailable(): 拉取并配置" << std::endl;
    std::cout << "  - 支持 Git、URL、SVN 等源" << std::endl;
    std::cout << "  - 与主项目一起编译，无需预安装" << std::endl;

    return 0;
}
