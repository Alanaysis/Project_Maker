#include <iostream>
#include <cstdlib>
#include <cstring>

/**
 * @file asan_demo.cpp
 * @brief AddressSanitizer (ASan) 示例
 *
 * AddressSanitizer 是一个内存错误检测工具，可以检测:
 * - 堆缓冲区溢出
 * - 栈缓冲区溢出
 * - 全局缓冲区溢出
 * - 使用已释放的内存
 * - 内存泄漏
 * - 双重释放
 *
 * 编译方法:
 *   g++ -fsanitize=address -fno-omit-frame-pointer -g -o asan_demo asan_demo.cpp
 *
 * 注意: 以下代码故意包含内存错误，用于演示 ASan 的检测能力。
 *       实际项目中不应包含这些错误。
 */

// ============================================================================
// 1. 堆缓冲区溢出
// ============================================================================
void heap_buffer_overflow() {
    std::cout << "=== 堆缓冲区溢出示例 ===" << std::endl;
    std::cout << "（此代码会触发 ASan 报告）" << std::endl;

    // 注意: 以下代码会触发 ASan 错误
    // int* array = new int[5];
    // array[10] = 42;  // 堆缓冲区溢出
    // delete[] array;

    // 正确代码
    int* array = new int[5];
    for (int i = 0; i < 5; ++i) {
        array[i] = i;
    }
    delete[] array;
    std::cout << "堆操作正确完成" << std::endl;
}

// ============================================================================
// 2. 栈缓冲区溢出
// ============================================================================
void stack_buffer_overflow() {
    std::cout << std::endl;
    std::cout << "=== 栈缓冲区溢出示例 ===" << std::endl;

    // 注意: 以下代码会触发 ASan 错误
    // int array[5];
    // array[10] = 42;  // 栈缓冲区溢出

    // 正确代码
    int array[5];
    for (int i = 0; i < 5; ++i) {
        array[i] = i;
    }
    std::cout << "栈操作正确完成" << std::endl;
}

// ============================================================================
// 3. 使用已释放的内存
// ============================================================================
void use_after_free() {
    std::cout << std::endl;
    std::cout << "=== 使用已释放内存示例 ===" << std::endl;

    // 注意: 以下代码会触发 ASan 错误
    // int* ptr = new int(42);
    // delete ptr;
    // std::cout << *ptr << std::endl;  // 使用已释放的内存

    // 正确代码
    int* ptr = new int(42);
    std::cout << "值: " << *ptr << std::endl;
    delete ptr;
    ptr = nullptr;
    std::cout << "内存正确释放" << std::endl;
}

// ============================================================================
// 4. 内存泄漏检测
// ============================================================================
void memory_leak() {
    std::cout << std::endl;
    std::cout << "=== 内存泄漏示例 ===" << std::endl;

    // 注意: 以下代码会触发 ASan 的内存泄漏报告
    // int* ptr = new int(42);
    // 忘记 delete ptr;

    // 正确代码
    int* ptr = new int(42);
    std::cout << "值: " << *ptr << std::endl;
    delete ptr;
    std::cout << "无内存泄漏" << std::endl;
}

// ============================================================================
// 5. 双重释放
// ============================================================================
void double_free() {
    std::cout << std::endl;
    std::cout << "=== 双重释放示例 ===" << std::endl;

    // 注意: 以下代码会触发 ASan 错误
    // int* ptr = new int(42);
    // delete ptr;
    // delete ptr;  // 双重释放

    // 正确代码
    int* ptr = new int(42);
    delete ptr;
    ptr = nullptr;  // 防止悬空指针
    std::cout << "无双重释放" << std::endl;
}

int main() {
    std::cout << "=== AddressSanitizer (ASan) 示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "AddressSanitizer 可以检测:" << std::endl;
    std::cout << "  - 堆缓冲区溢出" << std::endl;
    std::cout << "  - 栈缓冲区溢出" << std::endl;
    std::cout << "  - 使用已释放的内存" << std::endl;
    std::cout << "  - 内存泄漏" << std::endl;
    std::cout << "  - 双重释放" << std::endl;
    std::cout << std::endl;

    heap_buffer_overflow();
    stack_buffer_overflow();
    use_after_free();
    memory_leak();
    double_free();

    std::cout << std::endl;
    std::cout << "编译方法:" << std::endl;
    std::cout << "  g++ -fsanitize=address -fno-omit-frame-pointer -g -o demo demo.cpp" << std::endl;

    return 0;
}
