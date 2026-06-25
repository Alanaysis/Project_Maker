#include <iostream>
#include "version_info.h"

/**
 * @file custom_command_demo.cpp
 * @brief Custom Commands 示例
 *
 * 演示 CMake 自定义命令生成的头文件。
 * version_info.h 是由 CMake 自定义命令自动生成的。
 */

int main() {
    std::cout << "=== Custom Commands 示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "版本信息（由 CMake 自动生成）:" << std::endl;
    std::cout << "  项目名称: " << PROJECT_NAME << std::endl;
    std::cout << "  项目版本: " << PROJECT_VERSION << std::endl;
    std::cout << std::endl;

    std::cout << "Custom Commands 说明:" << std::endl;
    std::cout << "  - add_custom_command(): 生成文件的命令" << std::endl;
    std::cout << "  - add_custom_target(): 执行不生成文件的命令" << std::endl;
    std::cout << "  - 可用于代码生成、文件处理等" << std::endl;

    return 0;
}
