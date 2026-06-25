/**
 * @file 02_static_analysis.cpp
 * @brief 静态分析工具示例
 *
 * 静态分析：在编译时或不运行代码的情况下检查代码质量
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <cstring>

// ============================================================================
// 静态分析工具介绍
// ============================================================================

/**
 * 工具 1：Clang-Tidy
 *
 * 功能：C++ 静态分析工具，提供代码风格检查和自动修复
 *
 * 使用方法：
 * clang-tidy file.cpp -- -std=c++17
 *
 * 常见检查：
 * - modernize-use-nullptr
 * - modernize-use-auto
 * - modernize-use-override
 * - readability-identifier-naming
 * - bugprone-*
 * - performance-*
 */

/**
 * 工具 2：Cppcheck
 *
 * 功能：开源 C/C++ 静态分析工具
 *
 * 使用方法：
 * cppcheck --enable=all file.cpp
 *
 * 常见检查：
 * - 内存泄漏
 * - 空指针解引用
 * - 缓冲区溢出
 * - 未初始化变量
 */

/**
 * 工具 3：PVS-Studio
 *
 * 功能：商业静态分析工具，深度代码分析
 *
 * 特点：
 * - 高精度检测
 * - 支持多种 IDE
 * - 详细的错误报告
 */

/**
 * 工具 4：SonarQube
 *
 * 功能：代码质量平台，支持多种语言
 *
 * 特点：
 * - 持续集成
 * - 代码覆盖率
 * - 技术债务管理
 */

// ============================================================================
// 静态分析常见问题示例
// ============================================================================

/**
 * 问题 1：未初始化变量
 *
 * Clang-Tidy 检查：cppcoreguidelines-init-variables
 */
void uninitialized_variable() {
    int x;  // 未初始化
    // std::cout << x << std::endl;  // 未定义行为

    // 修复
    int y = 0;  // 初始化
    std::cout << y << std::endl;
}

/**
 * 问题 2：空指针解引用
 *
 * Cppcheck 检查：nullPointer
 */
void null_pointer() {
    int* ptr = nullptr;
    // *ptr = 42;  // 空指针解引用

    // 修复
    if (ptr != nullptr) {
        *ptr = 42;
    }
}

/**
 * 问题 3：内存泄漏
 *
 * Cppcheck 检查：memleak
 */
void memory_leak() {
    int* ptr = new int(42);
    // 忘记 delete

    // 修复
    auto smart_ptr = std::make_unique<int>(42);
}

/**
 * 问题 4：缓冲区溢出
 *
 * Cppcheck 检查：bufferAccessOutOfBounds
 */
void buffer_overflow() {
    char buffer[10];
    strcpy(buffer, "This is a very long string");  // 溢出

    // 修复
    char safe_buffer[10];
    strncpy(safe_buffer, "This is", sizeof(safe_buffer) - 1);
    safe_buffer[sizeof(safe_buffer) - 1] = '\0';
}

/**
 * 问题 5：隐式转换
 *
 * Clang-Tidy 检查：bugprone-narrowing-conversions
 */
void implicit_conversion() {
    double d = 3.14;
    int i = d;  // 隐式转换

    // 修复
    int j = static_cast<int>(d);  // 显式转换
}

/**
 * 问题 6：未使用变量
 *
 * Clang-Tidy 检查：unused-variable
 */
void unused_variable() {
    int unused = 42;  // 未使用
    std::cout << "hello" << std::endl;

    // 修复：删除未使用的变量
}

/**
 * 问题 7：魔法数字
 *
 * Clang-Tidy 检查：readability-magic-numbers
 */
void magic_numbers() {
    for (int i = 0; i < 100; i++) {  // 100 是魔法数字
        std::cout << i << " ";
    }
    std::cout << std::endl;

    // 修复
    const int max_count = 100;
    for (int i = 0; i < max_count; i++) {
        std::cout << i << " ";
    }
    std::cout << std::endl;
}

/**
 * 问题 8：缺少 const
 *
 * Clang-Tidy 检查：misc-const-correctness
 */
void missing_const() {
    std::string str = "hello";  // 应该是 const
    std::cout << str << std::endl;

    // 修复
    const std::string const_str = "hello";
    std::cout << const_str << std::endl;
}

/**
 * 问题 9：使用 C 风格数组
 *
 * Clang-Tidy 检查：modernize-avoid-c-arrays
 */
void c_style_array() {
    int arr[5] = {1, 2, 3, 4, 5};  // C 风格数组

    // 修复
    std::array<int, 5> modern_arr = {1, 2, 3, 4, 5};
}

/**
 * 问题 10：使用 NULL 而不是 nullptr
 *
 * Clang-Tidy 检查：modernize-use-nullptr
 */
void use_null() {
    int* ptr = NULL;  // 使用 NULL

    // 修复
    int* modern_ptr = nullptr;  // 使用 nullptr
}

// ============================================================================
// Clang-Tidy 配置示例
// ============================================================================

/**
 * .clang-tidy 配置文件示例
 *
 * Checks: >
 *   -*,
 *   modernize-*,
 *   readability-*,
 *   bugprone-*,
 *   performance-*,
 *   cppcoreguidelines-*
 *
 * CheckOptions:
 *   - key: readability-identifier-naming.ClassCase
 *     value: CamelCase
 *   - key: readability-identifier-naming.FunctionCase
 *     value: camelBack
 *   - key: readability-identifier-naming.VariableCase
 *     value: camelBack
 */

// ============================================================================
// CMake 集成示例
// ============================================================================

/**
 * CMakeLists.txt 集成静态分析
 *
 * # 启用 Clang-Tidy
 * set(CMAKE_CXX_CLANG_TIDY "clang-tidy")
 *
 * # 或者在构建时运行
 * find_program(CLANG_TIDY clang-tidy)
 * if(CLANG_TIDY)
 *   set(CMAKE_CXX_CLANG_TIDY ${CLANG_TIDY})
 * endif()
 */

// ============================================================================
// CI/CD 集成示例
// ============================================================================

/**
 * GitHub Actions 集成示例
 *
 * name: Static Analysis
 * on: [push, pull_request]
 * jobs:
 *   analyze:
 *     runs-on: ubuntu-latest
 *     steps:
 *       - uses: actions/checkout@v3
 *       - name: Install tools
 *         run: |
 *           sudo apt-get update
 *           sudo apt-get install -y clang-tidy cppcheck
 *       - name: Run clang-tidy
 *         run: |
 *           cmake -B build -DCMAKE_CXX_CLANG_TIDY=clang-tidy .
 *           cmake --build build
 *       - name: Run cppcheck
 *         run: cppcheck --enable=all src/
 */

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 静态分析工具示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "[1] 未初始化变量" << std::endl;
    uninitialized_variable();
    std::cout << std::endl;

    std::cout << "[2] 空指针解引用" << std::endl;
    null_pointer();
    std::cout << std::endl;

    std::cout << "[3] 内存泄漏" << std::endl;
    memory_leak();
    std::cout << std::endl;

    std::cout << "[4] 缓冲区溢出" << std::endl;
    buffer_overflow();
    std::cout << std::endl;

    std::cout << "[5] 隐式转换" << std::endl;
    implicit_conversion();
    std::cout << std::endl;

    std::cout << "[6] 魔法数字" << std::endl;
    magic_numbers();
    std::cout << std::endl;

    std::cout << "[7] 缺少 const" << std::endl;
    missing_const();
    std::cout << std::endl;

    std::cout << "[8] C 风格数组" << std::endl;
    c_style_array();
    std::cout << std::endl;

    std::cout << "[9] 使用 nullptr" << std::endl;
    use_null();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
