/**
 * @file 02_integer_overflow.cpp
 * @brief 整数溢出陷阱示例
 *
 * 整数溢出：算术运算结果超出类型表示范围
 * 危害：数据错误、逻辑错误、安全漏洞
 */

#include <iostream>
#include <limits>
#include <cstdint>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：有符号整数溢出
 *
 * 问题：有符号整数溢出是未定义行为
 */
void bad_signed_overflow() {
    int max = std::numeric_limits<int>::max();
    int result = max + 1;  // 未定义行为！
    std::cout << "max + 1 = " << result << std::endl;
}

/**
 * 错误示例 2：无符号整数溢出
 *
 * 问题：无符号整数溢出会回绕
 */
void bad_unsigned_overflow() {
    unsigned int max = std::numeric_limits<unsigned int>::max();
    unsigned int result = max + 1;  // 回绕到 0
    std::cout << "max + 1 = " << result << std::endl;
}

/**
 * 错误示例 3：乘法溢出
 *
 * 问题：乘法更容易溢出
 */
void bad_multiplication_overflow() {
    int a = 100000;
    int b = 100000;
    int result = a * b;  // 溢出！
    std::cout << "a * b = " << result << std::endl;
}

/**
 * 错误示例 4：循环计数器溢出
 *
 * 问题：循环计数器溢出导致无限循环
 */
void bad_loop_overflow() {
    // unsigned int 不会为负，循环条件永远为真
    for (unsigned int i = 10; i >= 0; i--) {
        // 无限循环！
        // i 从 10 递减到 0，然后溢出到 UINT_MAX
        std::cout << i << " ";
    }
    std::cout << std::endl;
}

/**
 * 错误示例 5：类型转换溢出
 *
 * 问题：大类型转换为小类型时溢出
 */
void bad_type_conversion() {
    int64_t big = 1000000000000LL;
    int small = big;  // 溢出！
    std::cout << "small = " << small << std::endl;
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：检查溢出
 *
 * 解决方案：运算前检查是否会导致溢出
 */
bool will_add_overflow(int a, int b) {
    if (b > 0 && a > std::numeric_limits<int>::max() - b) {
        return true;  // 会溢出
    }
    if (b < 0 && a < std::numeric_limits<int>::min() - b) {
        return true;  // 会下溢
    }
    return false;
}

void good_check_overflow() {
    int a = std::numeric_limits<int>::max();
    int b = 1;

    if (will_add_overflow(a, b)) {
        std::cout << "会溢出！" << std::endl;
    } else {
        std::cout << "a + b = " << a + b << std::endl;
    }
}

/**
 * 正确示例 2：使用安全整数库
 *
 * 解决方案：使用安全整数运算库
 */
#include <stdexcept>

class SafeInt {
public:
    explicit SafeInt(int val) : value_(val) {}

    SafeInt operator+(SafeInt other) const {
        if (will_add_overflow(value_, other.value_)) {
            throw std::overflow_error("Integer overflow");
        }
        return SafeInt(value_ + other.value_);
    }

    int get() const { return value_; }

private:
    int value_;
    static bool will_add_overflow(int a, int b) {
        if (b > 0 && a > std::numeric_limits<int>::max() - b) return true;
        if (b < 0 && a < std::numeric_limits<int>::min() - b) return true;
        return false;
    }
};

void good_safe_int() {
    try {
        SafeInt a(std::numeric_limits<int>::max());
        SafeInt b(1);
        SafeInt result = a + b;
        std::cout << "result = " << result.get() << std::endl;
    } catch (const std::overflow_error& e) {
        std::cout << "错误: " << e.what() << std::endl;
    }
}

/**
 * 正确示例 3：使用更大类型
 *
 * 解决方案：使用更大的整数类型
 */
void good_larger_type() {
    int32_t a = 100000;
    int32_t b = 100000;
    int64_t result = static_cast<int64_t>(a) * b;  // 转换为更大类型
    std::cout << "a * b = " << result << std::endl;
}

/**
 * 正确示例 4：修复循环计数器
 *
 * 解决方案：使用正确的循环条件
 */
void good_loop() {
    // 使用 int 类型
    for (int i = 10; i >= 0; i--) {
        std::cout << i << " ";
    }
    std::cout << std::endl;
}

/**
 * 正确示例 5：使用窄化检查
 *
 * 解决方案：转换前检查是否会溢出
 */
template <typename To, typename From>
To safe_cast(From value) {
    if (value > std::numeric_limits<To>::max() ||
        value < std::numeric_limits<To>::min()) {
        throw std::overflow_error("Type conversion overflow");
    }
    return static_cast<To>(value);
}

void good_safe_cast() {
    try {
        int64_t big = 1000000000000LL;
        int small = safe_cast<int>(big);
        std::cout << "small = " << small << std::endl;
    } catch (const std::overflow_error& e) {
        std::cout << "错误: " << e.what() << std::endl;
    }
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 整数溢出陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 有符号整数溢出" << std::endl;
    std::cout << "问题：有符号整数溢出是未定义行为" << std::endl;
    // bad_signed_overflow();  // 注释掉，避免未定义行为
    std::cout << std::endl;

    std::cout << "[错误示例 2] 无符号整数溢出" << std::endl;
    bad_unsigned_overflow();
    std::cout << "问题：无符号整数溢出会回绕" << std::endl;
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 检查溢出" << std::endl;
    good_check_overflow();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用安全整数库" << std::endl;
    good_safe_int();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用更大类型" << std::endl;
    good_larger_type();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 修复循环计数器" << std::endl;
    good_loop();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用窄化检查" << std::endl;
    good_safe_cast();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
