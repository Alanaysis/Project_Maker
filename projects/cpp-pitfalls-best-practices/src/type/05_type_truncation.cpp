/**
 * @file 05_type_truncation.cpp
 * @brief 类型截断陷阱示例
 *
 * 类型截断：将大类型转换为小类型时丢失数据
 * 危害：数据丢失、精度下降、逻辑错误
 */

#include <iostream>
#include <cstdint>
#include <limits>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：int 到 short 截断
 *
 * 问题：大整数转换为小整数时高位被截断
 */
void bad_int_to_short() {
    int big = 100000;
    short small = big;  // 截断！
    std::cout << "big = " << big << ", small = " << small << std::endl;
}

/**
 * 错误示例 2：double 到 float 截断
 *
 * 问题：double 精度高于 float，转换时精度丢失
 */
void bad_double_to_float() {
    double d = 3.14159265358979323846;
    float f = d;  // 精度丢失
    std::cout << std::setprecision(20);
    std::cout << "double = " << d << std::endl;
    std::cout << "float  = " << f << std::endl;
}

/**
 * 错误示例 3：long long 到 int 截断
 *
 * 问题：64位整数转换为32位整数时截断
 */
void bad_long_to_int() {
    int64_t big = 10000000000LL;
    int small = big;  // 截断！
    std::cout << "big = " << big << ", small = " << small << std::endl;
}

/**
 * 错误示例 4：char 到 int 符号扩展
 *
 * 问题：char 可能是有符号或无符号，行为不同
 */
void bad_char_to_int() {
    char c = 255;  // 如果 char 是有符号的，值为 -1
    int i = c;     // 符号扩展
    std::cout << "c = " << static_cast<int>(c) << ", i = " << i << std::endl;
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用窄化检查
 *
 * 解决方案：转换前检查是否会丢失数据
 */
template <typename To, typename From>
To safe_narrow(From value) {
    To result = static_cast<To>(value);
    if (static_cast<From>(result) != value) {
        throw std::runtime_error("Narrowing conversion lost data");
    }
    return result;
}

void good_narrow_check() {
    try {
        int big = 100000;
        short small = safe_narrow<short>(big);
        std::cout << "small = " << small << std::endl;
    } catch (const std::exception& e) {
        std::cout << "错误: " << e.what() << std::endl;
    }
}

/**
 * 正确示例 2：使用 static_cast 显式转换
 *
 * 解决方案：显式转换，明确意图
 */
void good_explicit_cast() {
    int big = 100000;
    short small = static_cast<short>(big);  // 显式转换，明确意图
    std::cout << "small = " << small << std::endl;
}

/**
 * 正确示例 3：使用更大类型
 *
 * 解决方案：使用足够大的类型
 */
void good_larger_type() {
    int32_t a = 100000;
    int64_t b = a;  // 安全扩展
    std::cout << "b = " << b << std::endl;
}

/**
 * 正确示例 4：使用 std::numeric_limits 检查范围
 *
 * 解决方案：检查值是否在目标类型范围内
 */
template <typename To, typename From>
bool can_narrow(From value) {
    return value >= std::numeric_limits<To>::min() &&
           value <= std::numeric_limits<To>::max();
}

void good_range_check() {
    int big = 100000;

    if (can_narrow<short>(big)) {
        short small = static_cast<short>(big);
        std::cout << "small = " << small << std::endl;
    } else {
        std::cout << "值超出 short 范围" << std::endl;
    }
}

/**
 * 正确示例 5：使用 std::variant (C++17)
 *
 * 解决方案：使用 variant 表示多种可能类型
 */
#include <variant>
#include <string>

void good_variant() {
    std::variant<int, double, std::string> value;

    value = 42;
    std::cout << "int: " << std::get<int>(value) << std::endl;

    value = 3.14;
    std::cout << "double: " << std::get<double>(value) << std::endl;

    value = "hello";
    std::cout << "string: " << std::get<std::string>(value) << std::endl;
}

/**
 * 正确示例 6：使用 std::optional 表示可能失败的转换
 *
 * 解决方案：转换失败时返回 nullopt
 */
#include <optional>

std::optional<short> safe_int_to_short(int value) {
    if (value >= std::numeric_limits<short>::min() &&
        value <= std::numeric_limits<short>::max()) {
        return static_cast<short>(value);
    }
    return std::nullopt;
}

void good_optional() {
    int big = 100000;
    auto result = safe_int_to_short(big);

    if (result.has_value()) {
        std::cout << "转换成功: " << result.value() << std::endl;
    } else {
        std::cout << "转换失败: 值超出范围" << std::endl;
    }
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 类型截断陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] int 到 short 截断" << std::endl;
    bad_int_to_short();
    std::cout << "问题：大整数转换为小整数时高位被截断" << std::endl;
    std::cout << std::endl;

    std::cout << "[错误示例 2] double 到 float 截断" << std::endl;
    bad_double_to_float();
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用窄化检查" << std::endl;
    good_narrow_check();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 static_cast" << std::endl;
    good_explicit_cast();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用更大类型" << std::endl;
    good_larger_type();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 numeric_limits 检查范围" << std::endl;
    good_range_check();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用 std::variant" << std::endl;
    good_variant();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用 std::optional" << std::endl;
    good_optional();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
