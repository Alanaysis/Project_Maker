/**
 * @file assume_attribute.cpp
 * @brief C++23 [[assume]] 属性示例
 *
 * [[assume]] 是 C++23 引入的属性，用于告诉编译器某个条件总是为真。
 * 编译器可以利用这个信息进行优化。
 *
 * 主要特点：
 * - 告诉编译器某个条件总是为真
 * - 帮助编译器进行优化
 * - 用于断言和文档
 * - 不会在运行时检查
 *
 * 编译命令：
 * g++ -std=c++23 -o assume_attribute assume_attribute.cpp
 */

#include <iostream>
#include <vector>
#include <algorithm>
#include <cassert>

// ========== 1. 基本用法 ==========

int divide(int a, int b) {
    // 告诉编译器 b 永远不为 0
    [[assume(b != 0)]];
    return a / b;
}

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::cout << "10 / 2 = " << divide(10, 2) << std::endl;
    std::cout << "20 / 4 = " << divide(20, 4) << std::endl;
}

// ========== 2. 实际应用：数组访问 ==========

int get_element(const std::vector<int>& vec, size_t index) {
    // 告诉编译器索引在有效范围内
    [[assume(index < vec.size())]];
    return vec[index];
}

void array_access() {
    std::cout << "\n=== 实际应用：数组访问 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5};

    std::cout << "Element at 0: " << get_element(data, 0) << std::endl;
    std::cout << "Element at 2: " << get_element(data, 2) << std::endl;
    std::cout << "Element at 4: " << get_element(data, 4) << std::endl;
}

// ========== 3. 实际应用：数学运算 ==========

double safe_sqrt(double x) {
    // 告诉编译器 x 是非负的
    [[assume(x >= 0)]];
    return std::sqrt(x);
}

double safe_log(double x) {
    // 告诉编译器 x 是正数
    [[assume(x > 0)]];
    return std::log(x);
}

void math_operations() {
    std::cout << "\n=== 实际应用：数学运算 ===" << std::endl;

    std::cout << "sqrt(4) = " << safe_sqrt(4) << std::endl;
    std::cout << "sqrt(9) = " << safe_sqrt(9) << std::endl;
    std::cout << "log(1) = " << safe_log(1) << std::endl;
    std::cout << "log(2.718) = " << safe_log(2.718) << std::endl;
}

// ========== 4. 实际应用：范围检查 ==========

int clamp_value(int value, int min_val, int max_val) {
    // 告诉编译器 min_val <= max_val
    [[assume(min_val <= max_val)]];

    if (value < min_val) return min_val;
    if (value > max_val) return max_val;
    return value;
}

void range_checking() {
    std::cout << "\n=== 实际应用：范围检查 ===" << std::endl;

    std::cout << "clamp(5, 0, 10) = " << clamp_value(5, 0, 10) << std::endl;
    std::cout << "clamp(-5, 0, 10) = " << clamp_value(-5, 0, 10) << std::endl;
    std::cout << "clamp(15, 0, 10) = " << clamp_value(15, 0, 10) << std::endl;
}

// ========== 5. 实际应用：指针检查 ==========

void process_pointer(int* ptr) {
    // 告诉编译器指针不为空
    [[assume(ptr != nullptr)]];
    std::cout << "Value: " << *ptr << std::endl;
}

void pointer_checking() {
    std::cout << "\n=== 实际应用：指针检查 ===" << std::endl;

    int value = 42;
    process_pointer(&value);
}

// ========== 6. 实际应用：字符串处理 ==========

size_t string_length(const char* str) {
    // 告诉编译器字符串不为空
    [[assume(str != nullptr)]];

    size_t len = 0;
    while (str[len] != '\0') {
        ++len;
    }
    return len;
}

void string_processing() {
    std::cout << "\n=== 实际应用：字符串处理 ===" << std::endl;

    std::cout << "Length of 'Hello': " << string_length("Hello") << std::endl;
    std::cout << "Length of 'World': " << string_length("World") << std::endl;
}

// ========== 7. 实际应用：循环优化 ==========

int sum_array(const int* arr, size_t size) {
    // 告诉编译器数组不为空且大小大于 0
    [[assume(arr != nullptr)]];
    [[assume(size > 0)]];

    int sum = 0;
    for (size_t i = 0; i < size; ++i) {
        sum += arr[i];
    }
    return sum;
}

void loop_optimization() {
    std::cout << "\n=== 实际应用：循环优化 ===" << std::endl;

    int data[] = {1, 2, 3, 4, 5};
    std::cout << "Sum: " << sum_array(data, 5) << std::endl;
}

// ========== 8. 实际应用：条件分支 ==========

int process_value(int value) {
    // 告诉编译器值在特定范围内
    [[assume(value >= 0 && value <= 100)]];

    if (value < 50) {
        return value * 2;
    } else {
        return value * 3;
    }
}

void conditional_branches() {
    std::cout << "\n=== 实际应用：条件分支 ===" << std::endl;

    std::cout << "process(25) = " << process_value(25) << std::endl;
    std::cout << "process(75) = " << process_value(75) << std::endl;
}

// ========== 9. 实际应用：函数前置条件 ==========

void transfer_money(double amount, double& from, double& to) {
    // 前置条件
    [[assume(amount > 0)]];
    [[assume(from >= amount)]];

    from -= amount;
    to += amount;
}

void function_preconditions() {
    std::cout << "\n=== 实际应用：函数前置条件 ===" << std::endl;

    double account_a = 1000.0;
    double account_b = 500.0;

    std::cout << "Before transfer:" << std::endl;
    std::cout << "  Account A: " << account_a << std::endl;
    std::cout << "  Account B: " << account_b << std::endl;

    transfer_money(200.0, account_a, account_b);

    std::cout << "After transfer:" << std::endl;
    std::cout << "  Account A: " << account_a << std::endl;
    std::cout << "  Account B: " << account_b << std::endl;
}

// ========== 10. 实际应用：数据验证 ==========

bool validate_email(const std::string& email) {
    // 告诉编译器字符串不为空
    [[assume(!email.empty())]];

    // 简单的邮箱验证
    size_t at_pos = email.find('@');
    if (at_pos == std::string::npos) return false;

    size_t dot_pos = email.find('.', at_pos);
    if (dot_pos == std::string::npos) return false;

    return true;
}

void data_validation() {
    std::cout << "\n=== 实际应用：数据验证 ===" << std::endl;

    std::cout << "test@example.com: "
              << (validate_email("test@example.com") ? "valid" : "invalid") << std::endl;
    std::cout << "invalid-email: "
              << (validate_email("invalid-email") ? "valid" : "invalid") << std::endl;
}

int main() {
    std::cout << "C++23 [[assume]] 属性示例\n" << std::endl;

    basic_usage();
    array_access();
    math_operations();
    range_checking();
    pointer_checking();
    string_processing();
    loop_optimization();
    conditional_branches();
    function_preconditions();
    data_validation();

    return 0;
}
