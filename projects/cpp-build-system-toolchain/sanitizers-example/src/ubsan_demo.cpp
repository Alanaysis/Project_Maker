#include <iostream>
#include <limits>
#include <cstdint>

/**
 * @file ubsan_demo.cpp
 * @brief UndefinedBehaviorSanitizer (UBSan) 示例
 *
 * UndefinedBehaviorSanitizer 是一个未定义行为检测工具，可以检测:
 * - 整数溢出
 * - 空指针解引用
 * - 除以零
 * - 数组越界
 * - 位移越界
 * - 类型转换问题
 *
 * 编译方法:
 *   g++ -fsanitize=undefined -g -o ubsan_demo ubsan_demo.cpp
 *
 * 注意: 以下代码故意包含未定义行为，用于演示 UBSan 的检测能力。
 */

// ============================================================================
// 1. 有符号整数溢出
// ============================================================================
void signed_integer_overflow() {
    std::cout << "=== 有符号整数溢出 ===" << std::endl;

    int32_t max_val = std::numeric_limits<int32_t>::max();
    std::cout << "INT32_MAX: " << max_val << std::endl;

    // 注意: 以下代码会触发 UBSan 报告
    // int32_t overflow = max_val + 1;  // 未定义行为

    // 正确做法: 使用安全的运算
    int32_t safe_val = max_val - 1;
    std::cout << "安全值: " << safe_val << std::endl;
}

// ============================================================================
// 2. 除以零
// ============================================================================
void division_by_zero() {
    std::cout << std::endl;
    std::cout << "=== 除以零 ===" << std::endl;

    int a = 42;
    int b = 0;

    // 注意: 以下代码会触发 UBSan 报告
    // int result = a / b;  // 未定义行为

    // 正确做法: 检查除数
    if (b != 0) {
        int result = a / b;
        std::cout << "结果: " << result << std::endl;
    } else {
        std::cout << "错误: 除数为零" << std::endl;
    }
}

// ============================================================================
// 3. 空指针解引用
// ============================================================================
void null_pointer_dereference() {
    std::cout << std::endl;
    std::cout << "=== 空指针解引用 ===" << std::endl;

    int* ptr = nullptr;

    // 注意: 以下代码会触发 UBSan 报告
    // *ptr = 42;  // 未定义行为

    // 正确做法: 检查指针
    if (ptr != nullptr) {
        *ptr = 42;
    } else {
        std::cout << "指针为空" << std::endl;
    }
}

// ============================================================================
// 4. 位移越界
// ============================================================================
void shift_out_of_bounds() {
    std::cout << std::endl;
    std::cout << "=== 位移越界 ===" << std::endl;

    int x = 1;

    // 注意: 以下代码会触发 UBSan 报告
    // int result = x << 32;  // 未定义行为 (int 通常是 32 位)

    // 正确做法: 检查位移量
    int shift = 31;
    if (shift >= 0 && shift < sizeof(int) * 8) {
        int result = x << shift;
        std::cout << "1 << 31 = " << result << std::endl;
    }
}

// ============================================================================
// 5. 数组越界（需要 -fsanitize=bounds）
// ============================================================================
void array_out_of_bounds() {
    std::cout << std::endl;
    std::cout << "=== 数组越界 ===" << std::endl;

    int arr[5] = {1, 2, 3, 4, 5};

    // 注意: 以下代码可能触发 UBSan 报告
    // arr[10] = 42;  // 未定义行为

    // 正确做法: 使用正确的索引
    for (int i = 0; i < 5; ++i) {
        std::cout << "arr[" << i << "] = " << arr[i] << std::endl;
    }
}

// ============================================================================
// 6. bool 值不是 0 或 1
// ============================================================================
void invalid_bool_value() {
    std::cout << std::endl;
    std::cout << "=== 无效 bool 值 ===" << std::endl;

    // 注意: 以下代码会触发 UBSan 报告
    // int x = 42;
    // bool b = *reinterpret_cast<bool*>(&x);  // 可能未定义行为

    // 正确做法: 使用合法的 bool 值
    bool b = true;
    std::cout << "bool 值: " << b << std::endl;
}

int main() {
    std::cout << "=== UndefinedBehaviorSanitizer (UBSan) 示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "UBSan 可以检测:" << std::endl;
    std::cout << "  - 有符号整数溢出" << std::endl;
    std::cout << "  - 除以零" << std::endl;
    std::cout << "  - 空指针解引用" << std::endl;
    std::cout << "  - 位移越界" << std::endl;
    std::cout << "  - 数组越界" << std::endl;
    std::cout << std::endl;

    signed_integer_overflow();
    division_by_zero();
    null_pointer_dereference();
    shift_out_of_bounds();
    array_out_of_bounds();
    invalid_bool_value();

    std::cout << std::endl;
    std::cout << "编译方法:" << std::endl;
    std::cout << "  g++ -fsanitize=undefined -g -o demo demo.cpp" << std::endl;

    return 0;
}
