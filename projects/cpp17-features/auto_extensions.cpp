/**
 * @file auto_extensions.cpp
 * @brief C++17 auto 扩展示例
 *
 * C++17 扩展了 auto 关键字的使用范围，使其可以在更多上下文中使用。
 * 这包括模板参数、lambda 参数、结构化绑定等。
 *
 * 主要优势：
 * 1. 代码简洁 - 减少冗余的类型声明
 * 2. 灵活性 - 适用于更多场景
 * 3. 可读性 - 更直观的类型表达
 */

#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <functional>
#include <algorithm>
#include <numeric>
#include <tuple>
#include <optional>
#include <variant>

// 1. 基本 auto 使用
void basic_auto_example() {
    std::cout << "\n[基本 auto 使用]" << std::endl;

    // 变量声明
    auto x = 42;           // int
    auto y = 3.14;         // double
    auto z = "Hello";      // const char*
    auto s = std::string("World");  // std::string

    std::cout << "x: " << x << " (type: " << typeid(x).name() << ")" << std::endl;
    std::cout << "y: " << y << " (type: " << typeid(y).name() << ")" << std::endl;
    std::cout << "z: " << z << " (type: " << typeid(z).name() << ")" << std::endl;
    std::cout << "s: " << s << " (type: " << typeid(s).name() << ")" << std::endl;

    // 容器
    auto vec = std::vector<int>{1, 2, 3, 4, 5};
    auto map = std::map<std::string, int>{{"one", 1}, {"two", 2}};

    std::cout << "vec: ";
    for (auto v : vec) std::cout << v << " ";
    std::cout << std::endl;
}

// 2. auto 与模板参数
template <typename T>
auto add(T a, T b) {
    return a + b;
}

template <typename T, typename U>
auto multiply(T a, U b) {
    return a * b;
}

void template_auto_example() {
    std::cout << "\n[auto 与模板参数]" << std::endl;

    // 函数模板返回类型推导
    auto result1 = add(3, 4);
    std::cout << "add(3, 4) = " << result1 << std::endl;

    auto result2 = add(3.14, 2.86);
    std::cout << "add(3.14, 2.86) = " << result2 << std::endl;

    auto result3 = multiply(3, 4.5);
    std::cout << "multiply(3, 4.5) = " << result3 << std::endl;

    auto result4 = multiply(3.14, 2);
    std::cout << "multiply(3.14, 2) = " << result4 << std::endl;
}

// 3. auto 与 lambda
void lambda_auto_example() {
    std::cout << "\n[auto 与 lambda]" << std::endl;

    // 泛型 lambda（C++14）
    auto generic_add = [](auto a, auto b) {
        return a + b;
    };

    std::cout << "generic_add(3, 4) = " << generic_add(3, 4) << std::endl;
    std::cout << "generic_add(3.14, 2.86) = " << generic_add(3.14, 2.86) << std::endl;
    std::cout << "generic_add(\"Hello\", \" World\") = "
              << generic_add(std::string("Hello"), std::string(" World")) << std::endl;

    // auto 返回类型
    auto get_value = [](auto x) -> decltype(auto) {
        return x;
    };

    auto val1 = get_value(42);
    auto val2 = get_value(3.14);
    auto val3 = get_value(std::string("Hello"));

    std::cout << "val1: " << val1 << std::endl;
    std::cout << "val2: " << val2 << std::endl;
    std::cout << "val3: " << val3 << std::endl;

    // 复杂的 auto lambda
    auto process = [](const auto& container) {
        auto sum = std::accumulate(container.begin(), container.end(),
                                   typename std::decay_t<decltype(container)>::value_type{});
        return sum;
    };

    std::vector<int> vec = {1, 2, 3, 4, 5};
    std::cout << "Sum: " << process(vec) << std::endl;
}

// 4. auto 与结构化绑定
void structured_binding_example() {
    std::cout << "\n[auto 与结构化绑定]" << std::endl;

    // 绑定元组
    auto get_tuple = []() -> std::tuple<int, double, std::string> {
        return {42, 3.14, "Hello"};
    };

    auto [x, y, z] = get_tuple();
    std::cout << "x: " << x << ", y: " << y << ", z: " << z << std::endl;

    // 绑定 pair
    std::pair<int, std::string> p = {1, "Hello"};
    auto [key, value] = p;
    std::cout << "key: " << key << ", value: " << value << std::endl;

    // 绑定结构体
    struct Point {
        double x;
        double y;
        double z;
    };

    Point point{1.0, 2.0, 3.0};
    auto [px, py, pz] = point;
    std::cout << "Point: (" << px << ", " << py << ", " << pz << ")" << std::endl;

    // 绑定 map
    std::map<std::string, int> scores = {{"Alice", 95}, {"Bob", 87}};
    for (const auto& [name, score] : scores) {
        std::cout << name << ": " << score << std::endl;
    }
}

// 5. auto 与 if/switch
void if_switch_auto_example() {
    std::cout << "\n[auto 与 if/switch]" << std::endl;

    // if constexpr with auto
    auto process = [](auto value) {
        if constexpr (std::is_integral_v<decltype(value)>) {
            std::cout << "Integer: " << value << std::endl;
        } else if constexpr (std::is_floating_point_v<decltype(value)>) {
            std::cout << "Float: " << value << std::endl;
        } else {
            std::cout << "Other: " << value << std::endl;
        }
    };

    process(42);
    process(3.14);
    process(std::string("Hello"));

    // if with initializer (C++17)
    std::vector vec = {1, 2, 3, 4, 5};
    if (auto it = std::find(vec.begin(), vec.end(), 3); it != vec.end()) {
        std::cout << "Found: " << *it << std::endl;
    }
}

// 6. auto 与范围 for
void range_for_example() {
    std::cout << "\n[auto 与范围 for]" << std::endl;

    std::vector vec = {1, 2, 3, 4, 5};

    // 基本用法
    for (auto v : vec) {
        std::cout << v << " ";
    }
    std::cout << std::endl;

    // 引用
    for (auto& v : vec) {
        v *= 2;
    }
    std::cout << "Doubled: ";
    for (const auto& v : vec) {
        std::cout << v << " ";
    }
    std::cout << std::endl;

    // 结构化绑定
    std::map<std::string, int> map = {{"a", 1}, {"b", 2}, {"c", 3}};
    for (const auto& [key, value] : map) {
        std::cout << key << "=" << value << " ";
    }
    std::cout << std::endl;
}

// 7. auto 与返回类型
auto get_int() { return 42; }
auto get_double() { return 3.14; }
auto get_string() { return std::string("Hello"); }

template <typename T>
auto get_default() {
    if constexpr (std::is_integral_v<T>) {
        return T{0};
    } else if constexpr (std::is_floating_point_v<T>) {
        return T{0.0};
    } else {
        return T{};
    }
}

void return_type_example() {
    std::cout << "\n[auto 与返回类型]" << std::endl;

    auto x = get_int();
    auto y = get_double();
    auto z = get_string();

    std::cout << "x: " << x << std::endl;
    std::cout << "y: " << y << std::endl;
    std::cout << "z: " << z << std::endl;

    auto default_int = get_default<int>();
    auto default_double = get_default<double>();
    auto default_string = get_default<std::string>();

    std::cout << "default_int: " << default_int << std::endl;
    std::cout << "default_double: " << default_double << std::endl;
    std::cout << "default_string: \"" << default_string << "\"" << std::endl;
}

// 8. auto 与类型推导
void type_deduction_example() {
    std::cout << "\n[auto 与类型推导]" << std::endl;

    // 基本推导
    auto a = 42;           // int
    auto b = 42u;          // unsigned int
    auto c = 42L;          // long
    auto d = 42LL;         // long long
    auto e = 42.0f;        // float
    auto f = 42.0;         // double
    auto g = 42.0L;        // long double

    std::cout << "a: " << typeid(a).name() << std::endl;
    std::cout << "b: " << typeid(b).name() << std::endl;
    std::cout << "c: " << typeid(c).name() << std::endl;
    std::cout << "d: " << typeid(d).name() << std::endl;
    std::cout << "e: " << typeid(e).name() << std::endl;
    std::cout << "f: " << typeid(f).name() << std::endl;
    std::cout << "g: " << typeid(g).name() << std::endl;

    // 引用和指针
    int x = 42;
    auto& ref = x;         // int&
    auto* ptr = &x;        // int*
    auto&& rref = 42;      // int&&

    std::cout << "ref: " << typeid(ref).name() << std::endl;
    std::cout << "ptr: " << typeid(ptr).name() << std::endl;
    std::cout << "rref: " << typeid(rref).name() << std::endl;

    // const
    const int ci = 42;
    auto a1 = ci;          // int (const removed)
    const auto a2 = ci;    // const int
    auto& a3 = ci;         // const int&

    std::cout << "a1: " << typeid(a1).name() << std::endl;
    std::cout << "a2: " << typeid(a2).name() << std::endl;
    std::cout << "a3: " << typeid(a3).name() << std::endl;
}

// 9. auto 与 STL 算法
void algorithm_example() {
    std::cout << "\n[auto 与 STL 算法]" << std::endl;

    std::vector vec = {5, 3, 1, 4, 2};

    // 使用 auto 简化迭代器
    auto it = std::find(vec.begin(), vec.end(), 3);
    if (it != vec.end()) {
        std::cout << "Found: " << *it << std::endl;
    }

    // 使用 auto 与 lambda
    auto is_even = [](auto x) { return x % 2 == 0; };
    auto count = std::count_if(vec.begin(), vec.end(), is_even);
    std::cout << "Even numbers: " << count << std::endl;

    // 使用 auto 与 transform
    std::vector<int> result(vec.size());
    std::transform(vec.begin(), vec.end(), result.begin(),
                   [](auto x) { return x * 2; });

    std::cout << "Doubled: ";
    for (auto v : result) std::cout << v << " ";
    std::cout << std::endl;

    // 使用 auto 与 accumulate
    auto sum = std::accumulate(vec.begin(), vec.end(), 0);
    std::cout << "Sum: " << sum << std::endl;
}

// 10. auto 与类成员
class AutoClass {
public:
    AutoClass(int value, const std::string& name) : value_(value), name_(name) {}

    // auto 不能用于非静态成员变量
    // auto member = 42;  // 错误

    // 可以用于静态成员（C++17）
    // static auto static_member = 42;  // 需要内联

    // 可以用于成员函数返回类型
    auto get_value() const { return value_; }

    auto get_name() const { return name_; }

    // 可以用于静态成员函数
    static auto create(int value) {
        return AutoClass{value, "default"};
    }

private:
    int value_ = 42;
    std::string name_ = "AutoClass";
};

void class_member_example() {
    std::cout << "\n[auto 与类成员]" << std::endl;

    auto obj = AutoClass::create(100);
    std::cout << "value: " << obj.get_value() << std::endl;
    std::cout << "name: " << obj.get_name() << std::endl;
}

// 11. auto 与模板特化
template <typename T>
auto process_value(T value) {
    if constexpr (std::is_same_v<T, int>) {
        return value * 2;
    } else if constexpr (std::is_same_v<T, double>) {
        return value + 0.5;
    } else if constexpr (std::is_same_v<T, std::string>) {
        return value + " processed";
    } else {
        return value;
    }
}

void template_specialization_example() {
    std::cout << "\n[auto 与模板特化]" << std::endl;

    auto result1 = process_value(42);
    auto result2 = process_value(3.14);
    auto result3 = process_value(std::string("Hello"));

    std::cout << "process_value(42) = " << result1 << std::endl;
    std::cout << "process_value(3.14) = " << result2 << std::endl;
    std::cout << "process_value(\"Hello\") = " << result3 << std::endl;
}

// 12. 最佳实践
void best_practices_example() {
    std::cout << "\n[最佳实践]" << std::endl;

    std::cout << "1. 使用场景:" << std::endl;
    std::cout << "   - 类型显而易见时" << std::endl;
    std::cout << "   - 减少代码冗余" << std::endl;
    std::cout << "   - 泛型编程" << std::endl;

    std::cout << "\n2. 优势:" << std::endl;
    std::cout << "   - 代码简洁" << std::endl;
    std::cout << "   - 类型安全" << std::endl;
    std::cout << "   - 编译期推导" << std::endl;

    std::cout << "\n3. 注意事项:" << std::endl;
    std::cout << "   - 不要过度使用" << std::endl;
    std::cout << "   - 确保类型清晰" << std::endl;
    std::cout << "   - 考虑可读性" << std::endl;
    std::cout << "   - 注意类型推导规则" << std::endl;
}

// 主示例函数
void auto_extensions_example() {
    std::cout << "=== auto 扩展 ===" << std::endl;

    basic_auto_example();
    template_auto_example();
    lambda_auto_example();
    structured_binding_example();
    if_switch_auto_example();
    range_for_example();
    return_type_example();
    type_deduction_example();
    algorithm_example();
    class_member_example();
    template_specialization_example();
    best_practices_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    auto_extensions_example();
    return 0;
}
#endif
