/**
 * @file if_constexpr_example.cpp
 * @brief C++17 if constexpr 示例
 *
 * if constexpr 是编译期的 if 语句，条件必须是常量表达式。
 * 它用于模板元编程，简化编译期条件判断。
 *
 * 主要优势：
 * 1. 简化模板代码 - 替代 SFINAE
 * 2. 编译期优化 - 不满足条件的分支不会被编译
 * 3. 可读性好 - 更直观的条件判断
 */

#include <iostream>
#include <type_traits>
#include <string>
#include <vector>
#include <array>
#include <memory>
#include <algorithm>

// 1. 基本 if constexpr
void basic_if_constexpr_example() {
    std::cout << "\n[基本 if constexpr]" << std::endl;

    // 编译期常量
    constexpr int x = 10;

    if constexpr (x > 5) {
        std::cout << "x is greater than 5" << std::endl;
    } else {
        std::cout << "x is not greater than 5" << std::endl;
    }

    // 编译期条件
    constexpr bool debug = true;
    if constexpr (debug) {
        std::cout << "Debug mode enabled" << std::endl;
    }
}

// 2. 模板中的 if constexpr
template <typename T>
auto get_value(T t) {
    if constexpr (std::is_integral_v<T>) {
        return t * 2;  // 整数类型：乘以2
    } else if constexpr (std::is_floating_point_v<T>) {
        return t + 0.5;  // 浮点类型：加0.5
    } else {
        return t;  // 其他类型：原样返回
    }
}

void template_example() {
    std::cout << "\n[模板中的 if constexpr]" << std::endl;

    std::cout << "get_value(10): " << get_value(10) << std::endl;
    std::cout << "get_value(3.14): " << get_value(3.14) << std::endl;
    std::cout << "get_value(\"Hello\"): " << get_value(std::string("Hello")) << std::endl;
}

// 3. 替代 SFINAE
// 传统 SFINAE 方式（复杂）
template <typename T, typename = void>
struct has_size_sfinae : std::false_type {};

template <typename T>
struct has_size_sfinae<T, std::void_t<decltype(std::declval<T>().size())>> : std::true_type {};

// 使用 if constexpr（简洁）
template <typename T, typename = void>
struct has_size : std::false_type {};

template <typename T>
struct has_size<T, std::void_t<decltype(std::declval<T>().size())>> : std::true_type {};

template <typename T>
auto get_size(T& container) {
    if constexpr (has_size<T>::value) {
        return container.size();
    } else {
        return 0;
    }
}

void sfinae_replacement_example() {
    std::cout << "\n[替代 SFINAE]" << std::endl;

    std::vector<int> vec = {1, 2, 3, 4, 5};
    int x = 42;

    std::cout << "vector size: " << get_size(vec) << std::endl;
    std::cout << "int size: " << get_size(x) << std::endl;
}

// 4. 类型特征检查
template <typename T>
void process_type(T value) {
    if constexpr (std::is_arithmetic_v<T>) {
        std::cout << "Arithmetic type: " << value << std::endl;
    } else if constexpr (std::is_same_v<T, std::string>) {
        std::cout << "String type: " << value << std::endl;
    } else if constexpr (std::is_pointer_v<T>) {
        std::cout << "Pointer type: " << *value << std::endl;
    } else {
        std::cout << "Other type" << std::endl;
    }
}

void type_check_example() {
    std::cout << "\n[类型特征检查]" << std::endl;

    process_type(42);
    process_type(3.14);
    process_type(std::string("Hello"));

    int x = 100;
    process_type(&x);
}

// 5. 编译期算法选择
template <typename Iterator>
auto sort_if_possible(Iterator begin, Iterator end) {
    if constexpr (std::is_same_v<typename Iterator::value_type, int>) {
        // 整数类型：使用计数排序
        std::cout << "Using counting sort for integers" << std::endl;
        std::sort(begin, end);
    } else {
        // 其他类型：使用标准排序
        std::cout << "Using standard sort" << std::endl;
        std::sort(begin, end);
    }
}

void algorithm_selection_example() {
    std::cout << "\n[编译期算法选择]" << std::endl;

    std::vector<int> int_vec = {3, 1, 4, 1, 5};
    std::vector<std::string> str_vec = {"banana", "apple", "cherry"};

    sort_if_possible(int_vec.begin(), int_vec.end());
    sort_if_possible(str_vec.begin(), str_vec.end());
}

// 6. 递归模板简化
// 传统递归模板（复杂）
template <typename T, typename... Args>
T sum_traditional(T first, Args... rest) {
    if constexpr (sizeof...(rest) == 0) {
        return first;
    } else {
        return first + sum_traditional(rest...);
    }
}

// 使用折叠表达式（C++17 更简洁）
template <typename... Args>
auto sum_fold(Args... args) {
    return (args + ...);
}

void recursive_template_example() {
    std::cout << "\n[递归模板简化]" << std::endl;

    std::cout << "sum_traditional(1, 2, 3, 4, 5): " << sum_traditional(1, 2, 3, 4, 5) << std::endl;
    std::cout << "sum_fold(1, 2, 3, 4, 5): " << sum_fold(1, 2, 3, 4, 5) << std::endl;
}

// 7. 条件编译
template <typename T>
class Container {
public:
    void add(const T& item) {
        if constexpr (std::is_same_v<T, std::string>) {
            // 字符串特殊处理
            std::cout << "Adding string: " << item << std::endl;
            data_.push_back(item);
        } else {
            // 其他类型通用处理
            std::cout << "Adding item" << std::endl;
            data_.push_back(item);
        }
    }

    void print() const {
        for (const auto& item : data_) {
            std::cout << item << " ";
        }
        std::cout << std::endl;
    }

private:
    std::vector<T> data_;
};

void conditional_compilation_example() {
    std::cout << "\n[条件编译]" << std::endl;

    Container<int> int_container;
    int_container.add(1);
    int_container.add(2);
    int_container.print();

    Container<std::string> str_container;
    str_container.add("Hello");
    str_container.add("World");
    str_container.print();
}

// 8. 编译期断言
template <typename T>
void validate_type() {
    static_assert(std::is_default_constructible_v<T>,
                  "Type must be default constructible");
    static_assert(std::is_copy_constructible_v<T>,
                  "Type must be copy constructible");

    if constexpr (std::is_arithmetic_v<T>) {
        std::cout << "T is arithmetic" << std::endl;
    }
}

void compile_time_assert_example() {
    std::cout << "\n[编译期断言]" << std::endl;

    validate_type<int>();
    validate_type<std::string>();
    // validate_type<std::unique_ptr<int>>();  // 编译错误：不可拷贝
}

// 9. 类型擦除
class AnyFunction {
private:
    struct Base {
        virtual ~Base() = default;
        virtual void call() = 0;
    };

    template <typename F>
    struct Derived : Base {
        F func;
        Derived(F f) : func(f) {}
        void call() override {
            if constexpr (std::is_invocable_v<F>) {
                func();
            }
        }
    };

    std::unique_ptr<Base> ptr_;

public:
    template <typename F>
    AnyFunction(F f) : ptr_(std::make_unique<Derived<F>>(f)) {}

    void operator()() {
        if (ptr_) {
            ptr_->call();
        }
    }
};

void type_erasure_example() {
    std::cout << "\n[类型擦除]" << std::endl;

    AnyFunction f1 = []() { std::cout << "Lambda 1" << std::endl; };
    AnyFunction f2 = []() { std::cout << "Lambda 2" << std::endl; };

    f1();
    f2();
}

// 10. 实际应用：配置解析
template <typename T>
T parse_value(const std::string& str) {
    if constexpr (std::is_same_v<T, int>) {
        return std::stoi(str);
    } else if constexpr (std::is_same_v<T, double>) {
        return std::stod(str);
    } else if constexpr (std::is_same_v<T, bool>) {
        return str == "true" || str == "1";
    } else {
        return str;
    }
}

void config_parsing_example() {
    std::cout << "\n[配置解析]" << std::endl;

    std::cout << "parse_value<int>(\"42\"): " << parse_value<int>("42") << std::endl;
    std::cout << "parse_value<double>(\"3.14\"): " << parse_value<double>("3.14") << std::endl;
    std::cout << "parse_value<bool>(\"true\"): " << parse_value<bool>("true") << std::endl;
    std::cout << "parse_value<std::string>(\"Hello\"): " << parse_value<std::string>("Hello") << std::endl;
}

// 主示例函数
void if_constexpr_example() {
    std::cout << "=== if constexpr ===" << std::endl;

    basic_if_constexpr_example();
    template_example();
    sfinae_replacement_example();
    type_check_example();
    algorithm_selection_example();
    recursive_template_example();
    conditional_compilation_example();
    compile_time_assert_example();
    type_erasure_example();
    config_parsing_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    if_constexpr_example();
    return 0;
}
#endif
