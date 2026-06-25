/**
 * C++11/14 auto 和 decltype 示例
 *
 * 学习目标：
 * 1. 理解 auto 类型推导规则
 * 2. 掌握 decltype 的使用
 * 3. 学会使用返回类型后置
 * 4. 理解 auto 和 decltype 的区别
 */

#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <type_traits>
#include <algorithm>
#include <functional>

// ==========================================
// 1. auto 基础
// ==========================================

void demonstrate_auto_basics() {
    std::cout << "\n=== 1. auto 基础 ===" << std::endl;

    // 基本类型推导
    auto i = 42;           // int
    auto d = 3.14;         // double
    auto c = 'A';          // char
    auto b = true;         // bool
    auto s = "Hello";      // const char*

    std::cout << "i = " << i << " (int)" << std::endl;
    std::cout << "d = " << d << " (double)" << std::endl;
    std::cout << "c = " << c << " (char)" << std::endl;
    std::cout << "b = " << b << " (bool)" << std::endl;
    std::cout << "s = " << s << " (const char*)" << std::endl;

    // 复杂类型推导
    auto vec = std::vector<int>{1, 2, 3, 4, 5};
    auto map = std::map<std::string, int>{{"one", 1}, {"two", 2}};

    std::cout << "\nvec 类型: " << typeid(vec).name() << std::endl;
    std::cout << "map 类型: " << typeid(map).name() << std::endl;
}

// ==========================================
// 2. auto 与引用和 const
// ==========================================

void demonstrate_auto_references() {
    std::cout << "\n=== 2. auto 与引用和 const ===" << std::endl;

    int x = 42;
    const int cx = 100;
    int& ref = x;
    const int& cref = cx;

    // auto 推导会去除引用和顶层 const
    auto a1 = x;      // int
    auto a2 = cx;     // int (去除 const)
    auto a3 = ref;    // int (去除引用)
    auto a4 = cref;   // int (去除 const 和引用)

    std::cout << "a1 = " << a1 << " (int)" << std::endl;
    std::cout << "a2 = " << a2 << " (int)" << std::endl;
    std::cout << "a3 = " << a3 << " (int)" << std::endl;
    std::cout << "a4 = " << a4 << " (int)" << std::endl;

    // 使用 & 保留引用
    auto& a5 = x;     // int&
    auto& a6 = cx;    // const int&
    auto& a7 = ref;   // int&
    auto& a8 = cref;  // const int&

    std::cout << "\na5 = " << a5 << " (int&)" << std::endl;
    std::cout << "a6 = " << a6 << " (const int&)" << std::endl;

    // 使用 const auto&
    const auto& a9 = x;   // const int&
    const auto& a10 = cx; // const int&

    std::cout << "\na9 = " << a9 << " (const int&)" << std::endl;
    std::cout << "a10 = " << a10 << " (const int&)" << std::endl;
}

// ==========================================
// 3. auto 与容器
// ==========================================

void demonstrate_auto_containers() {
    std::cout << "\n=== 3. auto 与容器 ===" << std::endl;

    std::vector<int> vec = {1, 2, 3, 4, 5};

    // 使用 auto 简化迭代器
    std::cout << "--- 使用 auto 简化迭代器 ---" << std::endl;
    for (auto it = vec.begin(); it != vec.end(); ++it) {
        std::cout << *it << " ";
    }
    std::cout << std::endl;

    // 使用 auto& 修改元素
    std::cout << "\n--- 使用 auto& 修改元素 ---" << std::endl;
    for (auto& elem : vec) {
        elem *= 2;
    }
    for (const auto& elem : vec) {
        std::cout << elem << " ";
    }
    std::cout << std::endl;

    // 复杂容器类型
    std::map<std::string, std::vector<int>> complex_map = {
        {"numbers", {1, 2, 3}},
        {"values", {4, 5, 6}}
    };

    std::cout << "\n--- 复杂容器类型 ---" << std::endl;
    for (const auto& pair : complex_map) {
        std::cout << pair.first << ": ";
        for (const auto& val : pair.second) {
            std::cout << val << " ";
        }
        std::cout << std::endl;
    }
}

// ==========================================
// 4. decltype 基础
// ==========================================

void demonstrate_decltype_basics() {
    std::cout << "\n=== 4. decltype 基础 ===" << std::endl;

    int x = 42;
    const int cx = 100;
    int& ref = x;

    // decltype 保留引用和 const
    decltype(x) d1 = x;      // int
    decltype(cx) d2 = cx;    // const int
    decltype(ref) d3 = ref;  // int&

    std::cout << "d1 = " << d1 << " (int)" << std::endl;
    std::cout << "d2 = " << d2 << " (const int)" << std::endl;
    std::cout << "d3 = " << d3 << " (int&)" << std::endl;

    // decltype 与表达式
    decltype(x + 1) d4 = 10;  // int
    decltype(x * 2.0) d5 = 3.14;  // double

    std::cout << "\nd4 = " << d4 << " (int)" << std::endl;
    std::cout << "d5 = " << d5 << " (double)" << std::endl;

    // decltype 与括号
    decltype((x)) d6 = x;  // int& (因为 (x) 是左值表达式)
    std::cout << "\nd6 = " << d6 << " (int&)" << std::endl;
}

// ==========================================
// 5. decltype 与函数返回类型
// ==========================================

// C++11 返回类型后置
template<typename T, typename U>
auto add_cxx11(T t, U u) -> decltype(t + u) {
    return t + u;
}

// C++14 返回类型自动推导
template<typename T, typename U>
auto add_cxx14(T t, U u) {
    return t + u;
}

// 复杂返回类型
template<typename Container>
auto get_begin(Container& c) -> decltype(c.begin()) {
    return c.begin();
}

void demonstrate_decltype_return_type() {
    std::cout << "\n=== 5. decltype 与函数返回类型 ===" << std::endl;

    // C++11 风格
    auto result1 = add_cxx11(3, 4);
    auto result2 = add_cxx11(3.14, 2.86);
    auto result3 = add_cxx11(std::string("Hello, "), std::string("World!"));

    std::cout << "add(3, 4) = " << result1 << std::endl;
    std::cout << "add(3.14, 2.86) = " << result2 << std::endl;
    std::cout << "add(\"Hello, \", \"World!\") = " << result3 << std::endl;

    // C++14 风格
    auto result4 = add_cxx14(10, 20);
    std::cout << "add(10, 20) = " << result4 << std::endl;

    // 复杂返回类型
    std::vector<int> vec = {1, 2, 3};
    auto it = get_begin(vec);
    std::cout << "get_begin(vec) = " << *it << std::endl;
}

// ==========================================
// 6. auto 与 decltype 的区别
// ==========================================

void demonstrate_auto_vs_decltype() {
    std::cout << "\n=== 6. auto 与 decltype 的区别 ===" << std::endl;

    int x = 42;
    const int& cref = x;

    // auto 去除引用和顶层 const
    auto a = cref;  // int

    // decltype 保留引用和 const
    decltype(cref) d = x;  // const int&

    std::cout << "a = " << a << " (int)" << std::endl;
    std::cout << "d = " << d << " (const int&)" << std::endl;

    // 修改 x 的值
    x = 100;
    std::cout << "\n修改 x 后:" << std::endl;
    std::cout << "a = " << a << " (不变)" << std::endl;
    std::cout << "d = " << d << " (随 x 变化)" << std::endl;

    // decltype(auto) - C++14
    // 保留表达式的类型，包括引用和 const
    decltype(auto) da = cref;  // const int&
    decltype(auto) da2 = (x); // int&

    std::cout << "\nda = " << da << " (const int&)" << std::endl;
    std::cout << "da2 = " << da2 << " (int&)" << std::endl;
}

// ==========================================
// 7. auto 与 Lambda
// ==========================================

void demonstrate_auto_lambda() {
    std::cout << "\n=== 7. auto 与 Lambda ===" << std::endl;

    // Lambda 类型是编译器生成的，无法直接写出
    auto lambda = [](int x) { return x * 2; };
    auto result = lambda(21);
    std::cout << "lambda(21) = " << result << std::endl;

    // 使用 auto 存储 Lambda
    auto add = [](auto a, auto b) { return a + b; };
    std::cout << "add(3, 4) = " << add(3, 4) << std::endl;
    std::cout << "add(3.14, 2.86) = " << add(3.14, 2.86) << std::endl;

    // 使用 std::function
    std::function<int(int)> func = [](int x) { return x * x; };
    std::cout << "func(5) = " << func(5) << std::endl;
}

// ==========================================
// 8. auto 的实际应用
// ==========================================

// 使用 auto 简化复杂类型
void demonstrate_auto_practical() {
    std::cout << "\n=== 8. auto 的实际应用 ===" << std::endl;

    // 复杂类型简化
    std::map<std::string, std::vector<std::pair<int, double>>> complex_data;

    // 不使用 auto
    // std::map<std::string, std::vector<std::pair<int, double>>>::iterator it =
    //     complex_data.begin();

    // 使用 auto
    auto it = complex_data.begin();
    (void)it;  // 避免未使用警告

    // 范围 for 循环
    std::vector<std::pair<std::string, int>> data = {
        {"Alice", 90}, {"Bob", 85}, {"Charlie", 95}
    };

    std::cout << "--- 使用 auto 遍历 ---" << std::endl;
    for (const auto& pair : data) {
        std::cout << pair.first << ": " << pair.second << std::endl;
    }

    // 使用 auto 与算法
    std::vector<int> numbers = {5, 2, 8, 1, 9, 3};
    auto max_it = std::max_element(numbers.begin(), numbers.end());
    std::cout << "\n最大值: " << *max_it << std::endl;

    // 使用 auto 与 find
    auto found = std::find(numbers.begin(), numbers.end(), 8);
    if (found != numbers.end()) {
        std::cout << "找到 8 在索引 " << std::distance(numbers.begin(), found) << std::endl;
    }
}

// ==========================================
// 9. auto 的注意事项
// ==========================================

void demonstrate_auto_caveats() {
    std::cout << "\n=== 9. auto 的注意事项 ===" << std::endl;

    // 1. auto 不能用于函数参数
    // void func(auto x) {}  // C++20 之前不行

    // 2. auto 不能用于类成员变量
    // class Foo {
    //     auto x = 42;  // 不行
    // };

    // 3. auto 推导可能不是你想要的
    auto x = {1, 2, 3};  // std::initializer_list<int>，不是 std::vector<int>
    std::cout << "x 的类型: " << typeid(x).name() << std::endl;

    // 4. 使用 auto& 保留引用
    std::vector<int> vec = {1, 2, 3};
    auto& ref = vec[0];  // int&
    ref = 100;
    std::cout << "vec[0] = " << vec[0] << std::endl;

    // 5. 使用 const auto& 避免拷贝
    const auto& cref = vec[0];  // const int&
    std::cout << "cref = " << cref << std::endl;
}

// ==========================================
// 主函数
// ==========================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "C++11/14 auto 和 decltype 示例" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. auto 基础
    demonstrate_auto_basics();

    // 2. auto 与引用和 const
    demonstrate_auto_references();

    // 3. auto 与容器
    demonstrate_auto_containers();

    // 4. decltype 基础
    demonstrate_decltype_basics();

    // 5. decltype 与函数返回类型
    demonstrate_decltype_return_type();

    // 6. auto 与 decltype 的区别
    demonstrate_auto_vs_decltype();

    // 7. auto 与 Lambda
    demonstrate_auto_lambda();

    // 8. auto 的实际应用
    demonstrate_auto_practical();

    // 9. auto 的注意事项
    demonstrate_auto_caveats();

    std::cout << "\n========================================" << std::endl;
    std::cout << "所有示例执行完毕！" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
