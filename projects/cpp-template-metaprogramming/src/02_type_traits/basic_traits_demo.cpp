// =============================================================================
// basic_traits_demo.cpp - 基础类型萃取演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o basic_traits_demo basic_traits_demo.cpp
// 运行: ./basic_traits_demo
// =============================================================================

#include <iostream>
#include <string>
#include <vector>
#include "type_traits/basic_traits.hpp"
#include "type_traits/type_transform.hpp"

// 辅助函数：打印类型信息
template <typename T>
void print_type_info(const char* name) {
    std::cout << "  " << name << ":" << std::endl;
    std::cout << "    is_integral:      " << tmp::is_integral_v<T> << std::endl;
    std::cout << "    is_floating_point: " << tmp::is_floating_point_v<T> << std::endl;
    std::cout << "    is_arithmetic:     " << tmp::is_arithmetic_v<T> << std::endl;
    std::cout << "    is_pointer:        " << tmp::is_pointer_v<T> << std::endl;
    std::cout << "    is_reference:      " << tmp::is_reference_v<T> << std::endl;
    std::cout << "    is_void:           " << tmp::is_void_v<T> << std::endl;
    std::cout << "    is_array:          " << tmp::is_array_v<T> << std::endl;
    std::cout << "    is_const:          " << tmp::is_const_v<T> << std::endl;
    std::cout << "    is_function:       " << tmp::is_function_v<T> << std::endl;
    std::cout << std::endl;
}

// 示例函数：只接受整数类型
template <typename T>
tmp::enable_if_t<tmp::is_integral_v<T>, void>
process_integral(T value) {
    std::cout << "  Processing integral: " << value << std::endl;
}

// 示例函数：只接受浮点类型
template <typename T>
tmp::enable_if_t<tmp::is_floating_point_v<T>, void>
process_floating(T value) {
    std::cout << "  Processing floating: " << value << std::endl;
}

// 示例函数：根据类型选择不同实现
template <typename T>
void smart_process(T value) {
    if constexpr (tmp::is_integral_v<T>) {
        std::cout << "  [integral] " << value << std::endl;
    } else if constexpr (tmp::is_floating_point_v<T>) {
        std::cout << "  [floating] " << value << std::endl;
    } else if constexpr (tmp::is_pointer_v<T>) {
        std::cout << "  [pointer] " << *value << std::endl;
    } else {
        std::cout << "  [other] " << value << std::endl;
    }
}

// 使用类型萃取进行编译期分支
template <typename T>
auto safe_convert(T value) {
    if constexpr (tmp::is_integral_v<T>) {
        return static_cast<double>(value);
    } else if constexpr (tmp::is_floating_point_v<T>) {
        return static_cast<int>(value);
    } else {
        return value;
    }
}

// 编译期断言示例
template <typename T>
class NumericContainer {
    static_assert(tmp::is_arithmetic_v<T>, "T must be an arithmetic type");
public:
    void add(T value) { data_.push_back(value); }
private:
    std::vector<T> data_;
};

int main() {
    std::cout << "=== 基础类型萃取演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. 整数类型
    std::cout << "1. 整数类型:" << std::endl;
    print_type_info<int>("int");
    print_type_info<unsigned int>("unsigned int");
    print_type_info<long long>("long long");
    print_type_info<bool>("bool");
    print_type_info<char>("char");

    // 2. 浮点类型
    std::cout << "2. 浮点类型:" << std::endl;
    print_type_info<float>("float");
    print_type_info<double>("double");
    print_type_info<long double>("long double");

    // 3. 指针类型
    std::cout << "3. 指针类型:" << std::endl;
    print_type_info<int*>("int*");
    print_type_info<const int*>("const int*");
    print_type_info<int**>("int**");

    // 4. 引用类型
    std::cout << "4. 引用类型:" << std::endl;
    print_type_info<int&>("int&");
    print_type_info<const int&>("const int&");
    print_type_info<int&&>("int&&");

    // 5. void 类型
    std::cout << "5. void 类型:" << std::endl;
    print_type_info<void>("void");
    print_type_info<const void>("const void");

    // 6. 数组类型
    std::cout << "6. 数组类型:" << std::endl;
    print_type_info<int[5]>("int[5]");
    print_type_info<int[]>("int[]");
    print_type_info<double[10]>("double[10]");

    // 7. const 类型
    std::cout << "7. const 类型:" << std::endl;
    print_type_info<const int>("const int");
    print_type_info<const int*>("const int*");      // 指向 const 的指针
    print_type_info<int* const>("int* const");      // const 指针

    // 8. 函数类型
    std::cout << "8. 函数类型:" << std::endl;
    print_type_info<void()>("void()");
    print_type_info<int(int, int)>("int(int, int)");

    // 9. 自定义类型
    std::cout << "9. 自定义类型:" << std::endl;
    struct MyStruct { int x; };
    print_type_info<MyStruct>("MyStruct");
    print_type_info<std::string>("std::string");

    // 10. enable_if 应用
    std::cout << "10. enable_if 应用:" << std::endl;
    process_integral(42);
    process_integral(static_cast<short>(10));
    process_floating(3.14);
    process_floating(2.71f);
    // process_integral(3.14);  // 编译错误：不是整数类型
    std::cout << std::endl;

    // 11. if constexpr 应用
    std::cout << "11. if constexpr 应用:" << std::endl;
    smart_process(42);
    smart_process(3.14);
    int x = 100;
    smart_process(&x);
    std::cout << std::endl;

    // 12. 类型转换
    std::cout << "12. 类型转换:" << std::endl;
    std::cout << "  int->double: " << safe_convert(42) << std::endl;
    std::cout << "  double->int: " << safe_convert(3.14) << std::endl;
    std::cout << std::endl;

    // 13. 编译期断言
    std::cout << "13. 编译期断言:" << std::endl;
    NumericContainer<int> nc;
    nc.add(42);
    std::cout << "  NumericContainer<int> created successfully" << std::endl;
    // NumericContainer<std::string> nc2;  // 编译错误
    std::cout << std::endl;

    // 14. integral_constant 演示
    std::cout << "14. integral_constant 演示:" << std::endl;
    std::cout << "  true_type::value = " << tmp::true_type::value << std::endl;
    std::cout << "  false_type::value = " << tmp::false_type::value << std::endl;

    using MyConst = tmp::integral_constant<int, 42>;
    std::cout << "  MyConst::value = " << MyConst::value << std::endl;
    std::cout << std::endl;

    std::cout << "=== 基础类型萃取演示完成 ===" << std::endl;
    return 0;
}
