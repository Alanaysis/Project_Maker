#include <iostream>

/**
 * @file presets_demo.cpp
 * @brief CMake Presets 示例
 *
 * 演示 CMake Presets 的使用。
 * CMake Presets 允许在 CMakePresets.json 中定义构建配置，
 * 简化了命令行参数。
 *
 * 使用方法:
 *   cmake --preset debug
 *   cmake --build --preset debug
 *   ctest --preset default
 */

int main() {
    std::cout << "=== CMake Presets 示例 ===" << std::endl;
    std::cout << std::endl;

#ifdef DEBUG_MODE
    std::cout << "当前模式: Debug" << std::endl;
#else
    std::cout << "当前模式: Release" << std::endl;
#endif

    std::cout << std::endl;
    std::cout << "CMake Presets 使用方法:" << std::endl;
    std::cout << "  1. 配置: cmake --preset <preset-name>" << std::endl;
    std::cout << "  2. 构建: cmake --build --preset <preset-name>" << std::endl;
    std::cout << "  3. 测试: ctest --preset <preset-name>" << std::endl;
    std::cout << std::endl;
    std::cout << "可用的预设:" << std::endl;
    std::cout << "  - default: 默认配置 (Ninja, Release)" << std::endl;
    std::cout << "  - debug: 调试配置 (Ninja, Debug, Sanitizers)" << std::endl;
    std::cout << "  - release: 发布配置 (Ninja, Release, O3)" << std::endl;
    std::cout << "  - clang: 使用 Clang 编译器" << std::endl;
    std::cout << "  - gcc: 使用 GCC 编译器" << std::endl;

    return 0;
}
