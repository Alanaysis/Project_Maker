#include <iostream>
#include <cstdlib>
#include <cstring>
#include <vector>

/**
 * @file valgrind_demo.cpp
 * @brief Valgrind 动态分析示例
 *
 * Valgrind 是一个强大的动态分析工具套件，包括:
 * - memcheck: 内存错误检测
 * - cachegrind: 缓存分析
 * - callgrind: 函数调用分析
 * - helgrind: 线程错误检测
 *
 * 使用方法:
 *   valgrind --leak-check=full ./valgrind_demo
 */

// ============================================================================
// 1. 正确的内存管理
// ============================================================================
void correct_memory_management() {
    std::cout << "=== 正确的内存管理 ===" << std::endl;

    // 分配内存
    int* ptr = new int(42);
    std::cout << "值: " << *ptr << std::endl;

    // 释放内存
    delete ptr;
    ptr = nullptr;

    // 数组分配
    int* arr = new int[5];
    for (int i = 0; i < 5; ++i) {
        arr[i] = i;
    }
    delete[] arr;

    std::cout << "内存管理正确" << std::endl;
}

// ============================================================================
// 2. 使用 RAII 避免内存泄漏
// ============================================================================
void raii_example() {
    std::cout << std::endl;
    std::cout << "=== RAII 示例 ===" << std::endl;

    // 使用智能指针
    auto ptr = std::make_unique<int>(42);
    std::cout << "值: " << *ptr << std::endl;

    // 使用 vector 管理数组
    std::vector<int> vec = {1, 2, 3, 4, 5};
    std::cout << "vector 大小: " << vec.size() << std::endl;

    // 离开作用域时自动释放
}

// ============================================================================
// 3. 使用 Valgrind 检测内存泄漏
// ============================================================================
void memory_leak_detection() {
    std::cout << std::endl;
    std::cout << "=== 内存泄漏检测 ===" << std::endl;

    // 注意: 以下代码会触发 Valgrind 的内存泄漏报告
    // int* leaked = new int(42);
    // 忘记 delete leaked;

    // 正确做法
    int* ptr = new int(42);
    std::cout << "值: " << *ptr << std::endl;
    delete ptr;
}

// ============================================================================
// 4. 使用 Valgrind 检测未初始化内存
// ============================================================================
void uninitialized_memory() {
    std::cout << std::endl;
    std::cout << "=== 未初始化内存检测 ===" << std::endl;

    // 注意: 以下代码会触发 Valgrind 的未初始化内存报告
    // int x;
    // if (x > 0) { ... }  // 使用未初始化的变量

    // 正确做法
    int x = 0;
    if (x > 0) {
        std::cout << "x > 0" << std::endl;
    } else {
        std::cout << "x <= 0" << std::endl;
    }
}

// ============================================================================
// 5. Valgrind 工具介绍
// ============================================================================
void valgrind_tools() {
    std::cout << std::endl;
    std::cout << "=== Valgrind 工具 ===" << std::endl;
    std::cout << "1. memcheck: 内存错误检测" << std::endl;
    std::cout << "   valgrind --leak-check=full ./program" << std::endl;
    std::cout << std::endl;
    std::cout << "2. cachegrind: 缓存分析" << std::endl;
    std::cout << "   valgrind --tool=cachegrind ./program" << std::endl;
    std::cout << std::endl;
    std::cout << "3. callgrind: 函数调用分析" << std::endl;
    std::cout << "   valgrind --tool=callgrind ./program" << std::endl;
    std::cout << "   kcachegrind callgrind.out.*" << std::endl;
    std::cout << std::endl;
    std::cout << "4. helgrind: 线程错误检测" << std::endl;
    std::cout << "   valgrind --tool=helgrind ./program" << std::endl;
}

int main() {
    std::cout << "=== Valgrind 动态分析示例 ===" << std::endl;
    std::cout << std::endl;

    correct_memory_management();
    raii_example();
    memory_leak_detection();
    uninitialized_memory();
    valgrind_tools();

    return 0;
}
