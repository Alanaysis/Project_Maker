/**
 * @file 01_implicit_conversion.cpp
 * @brief 隐式转换陷阱示例
 *
 * 隐式转换陷阱：编译器自动进行的类型转换可能导致意外行为
 * 危害：数据丢失、精度下降、逻辑错误
 */

#include <iostream>
#include <string>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：int 到 bool 隐式转换
 *
 * 问题：任何非零值都转换为 true
 */
void bad_int_to_bool() {
    int value = 42;
    if (value) {  // 隐式转换为 bool
        std::cout << "value 为真" << std::endl;
    }
    // 意图可能是检查 value != 0
}

/**
 * 错误示例 2：double 到 int 隐式转换
 *
 * 问题：小数部分被截断
 */
void bad_double_to_int() {
    double d = 3.7;
    int i = d;  // 隐式转换，i = 3
    std::cout << "d = " << d << ", i = " << i << std::endl;
}

/**
 * 错误示例 3：构造函数隐式转换
 *
 * 问题：单参数构造函数允许隐式转换
 */
class BadString {
public:
    BadString(int size) : data_(new char[size]) {}  // 隐式转换
    ~BadString() { delete[] data_; }
private:
    char* data_;
};

void bad_constructor_conversion() {
    BadString str = 100;  // 隐式转换：int -> BadString
}

/**
 * 错误示例 4：运算符重载隐式转换
 *
 * 问题：运算符重载可能导致意外转换
 */
class BadNumber {
public:
    BadNumber(double val) : value_(val) {}
    operator double() const { return value_; }  // 隐式转换
private:
    double value_;
};

void bad_operator_conversion() {
    BadNumber num(3.14);
    double d = num;  // 隐式转换
    int i = num;     // 隐式转换为 double，再转换为 int
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用 explicit 关键字
 *
 * 解决方案：explicit 禁止隐式转换
 */
class GoodString {
public:
    explicit GoodString(int size) : data_(new char[size]) {}  // explicit
    ~GoodString() { delete[] data_; }
private:
    char* data_;
};

void good_explicit() {
    // GoodString str = 100;  // 编译错误！
    GoodString str(100);  // 必须显式构造
}

/**
 * 正确示例 2：使用 static_cast 显式转换
 *
 * 解决方案：使用显式类型转换
 */
void good_static_cast() {
    double d = 3.7;
    int i = static_cast<int>(d);  // 显式转换
    std::cout << "d = " << d << ", i = " << i << std::endl;
}

/**
 * 正确示例 3：使用窄化检查
 *
 * 解决方案：使用 gsl::narrow 或自定义检查
 */
#include <stdexcept>

template <typename To, typename From>
To narrow_cast(From value) {
    To result = static_cast<To>(value);
    if (static_cast<From>(result) != value) {
        throw std::runtime_error("Narrowing conversion failed");
    }
    return result;
}

void good_narrow_check() {
    double d = 3.7;
    try {
        int i = narrow_cast<int>(d);
        std::cout << "i = " << i << std::endl;
    } catch (const std::exception& e) {
        std::cout << "错误: " << e.what() << std::endl;
    }
}

/**
 * 正确示例 4：使用列表初始化防止窄化
 *
 * 解决方案：列表初始化禁止窄化转换
 */
void good_list_initialization() {
    double d = 3.7;
    // int i{d};  // 编译错误！窄化转换
    int i = static_cast<int>(d);  // 必须显式转换
}

/**
 * 正确示例 5：明确比较类型
 *
 * 解决方案：使用显式比较，避免隐式转换
 */
void good_explicit_comparison() {
    int a = 0;
    int b = 42;

    // 明确比较意图
    if (a != 0) {
        std::cout << "a 非零" << std::endl;
    }

    if (b > 0) {
        std::cout << "b 为正" << std::endl;
    }
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 隐式转换陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] int 到 bool 隐式转换" << std::endl;
    bad_int_to_bool();
    std::cout << "问题：任何非零值都转换为 true" << std::endl;
    std::cout << std::endl;

    std::cout << "[错误示例 2] double 到 int 隐式转换" << std::endl;
    bad_double_to_int();
    std::cout << "问题：小数部分被截断" << std::endl;
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用 explicit 关键字" << std::endl;
    good_explicit();
    std::cout << "explicit 禁止隐式转换" << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 static_cast" << std::endl;
    good_static_cast();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用窄化检查" << std::endl;
    good_narrow_check();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用列表初始化" << std::endl;
    good_list_initialization();
    std::cout << "列表初始化禁止窄化转换" << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 5] 明确比较类型" << std::endl;
    good_explicit_comparison();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
