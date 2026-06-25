#include <iostream>

/**
 * @file generator_expr.cpp
 * @brief Generator Expressions 示例
 *
 * 演示 CMake Generator Expressions 的使用。
 * Generator Expressions 在生成构建系统时求值，而不是在 CMake 配置时。
 *
 * 常用的 Generator Expressions:
 * - $<CONFIG:Debug>           - 检查构建配置
 * - $<PLATFORM_ID:Linux>      - 检查目标平台
 * - $<CXX_COMPILER_ID:GNU>    - 检查编译器
 * - $<TARGET_FILE:name>       - 获取目标文件路径
 * - $<BOOL:expr>              - 布尔表达式
 * - $<IF:cond,true,false>     - 条件表达式
 */

// 这些宏由 CMakeLists.txt 中的 Generator Expressions 定义
#ifndef BUILD_TYPE
#define BUILD_TYPE "Unknown"
#endif

#ifndef PLATFORM
#define PLATFORM "Unknown"
#endif

#ifndef COMPILER
#define COMPILER "Unknown"
#endif

int main() {
    std::cout << "=== Generator Expressions 示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "构建信息:" << std::endl;
    std::cout << "  构建类型: " << BUILD_TYPE << std::endl;
    std::cout << "  目标平台: " << PLATFORM << std::endl;
    std::cout << "  编译器:   " << COMPILER << std::endl;
    std::cout << std::endl;

    std::cout << "Generator Expressions 说明:" << std::endl;
    std::cout << "  - 在 CMake 生成构建系统时求值" << std::endl;
    std::cout << "  - 不能在 message() 中使用（需要生成器求值）" << std::endl;
    std::cout << "  - 可用于 target_compile_definitions 等命令" << std::endl;
    std::cout << "  - 支持条件判断、字符串操作、路径操作等" << std::endl;

    return 0;
}
