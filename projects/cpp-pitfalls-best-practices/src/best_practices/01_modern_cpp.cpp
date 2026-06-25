/**
 * @file 01_modern_cpp.cpp
 * @brief 现代 C++ 风格示例
 *
 * 现代 C++ 最佳实践：使用 C++11/14/17/20 特性
 */

#include <iostream>
#include <vector>
#include <string>
#include <memory>
#include <algorithm>
#include <optional>
#include <variant>
#include <any>

// ============================================================================
// 传统 C++ 风格
// ============================================================================

/**
 * 传统风格 1：手动内存管理
 *
 * 问题：容易出现内存泄漏
 */
void traditional_memory() {
    int* ptr = new int(42);
    // 使用 ptr
    delete ptr;  // 容易忘记
}

/**
 * 传统风格 2：NULL 指针
 *
 * 问题：NULL 可以隐式转换为整数
 */
void traditional_null() {
    int* ptr = NULL;  // 不够类型安全
}

/**
 * 传统风格 3：C 风格数组
 *
 * 问题：不安全，不知道大小
 */
void traditional_array() {
    int arr[5] = {1, 2, 3, 4, 5};
    // 不知道大小，容易越界
}

/**
 * 传统风格 4：迭代器循环
 *
 * 问题：代码冗长
 */
void traditional_loop() {
    std::vector<int> vec = {1, 2, 3, 4, 5};
    for (std::vector<int>::iterator it = vec.begin(); it != vec.end(); ++it) {
        std::cout << *it << " ";
    }
    std::cout << std::endl;
}

// ============================================================================
// 现代 C++ 风格
// ============================================================================

/**
 * 现代风格 1：智能指针
 *
 * 优点：自动内存管理，不会泄漏
 */
void modern_smart_pointer() {
    auto ptr = std::make_unique<int>(42);
    // 使用 ptr
    // 自动释放
}

/**
 * 现代风格 2：nullptr
 *
 * 优点：类型安全
 */
void modern_nullptr() {
    int* ptr = nullptr;  // 类型安全
}

/**
 * 现代风格 3：std::array
 *
 * 优点：知道大小，更安全
 */
#include <array>

void modern_array() {
    std::array<int, 5> arr = {1, 2, 3, 4, 5};
    std::cout << "大小: " << arr.size() << std::endl;
}

/**
 * 现代风格 4：范围 for 循环
 *
 * 优点：简洁，不易出错
 */
void modern_range_for() {
    std::vector<int> vec = {1, 2, 3, 4, 5};
    for (const auto& val : vec) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

/**
 * 现代风格 5：auto 类型推导
 *
 * 优点：减少冗余，避免类型不匹配
 */
void modern_auto() {
    auto x = 42;           // int
    auto y = 3.14;         // double
    auto s = "hello";      // const char*
    auto vec = std::vector<int>{1, 2, 3};  // vector<int>

    std::cout << "x = " << x << std::endl;
    std::cout << "y = " << y << std::endl;
}

/**
 * 现代风格 6：初始化列表
 *
 * 优点：统一初始化语法
 */
void modern_initializer_list() {
    std::vector<int> vec = {1, 2, 3, 4, 5};
    std::array<int, 3> arr = {1, 2, 3};
    std::string str = "hello";

    std::cout << "vec 大小: " << vec.size() << std::endl;
}

/**
 * 现代风格 7：lambda 表达式
 *
 * 优点：简洁的匿名函数
 */
void modern_lambda() {
    std::vector<int> vec = {5, 3, 1, 4, 2};

    // 排序
    std::sort(vec.begin(), vec.end(), [](int a, int b) {
        return a < b;
    });

    // 查找
    auto it = std::find_if(vec.begin(), vec.end(), [](int x) {
        return x > 3;
    });

    if (it != vec.end()) {
        std::cout << "找到: " << *it << std::endl;
    }
}

/**
 * 现代风格 8：结构化绑定 (C++17)
 *
 * 优点：简洁地解包
 */
#include <tuple>
#include <map>

void modern_structured_binding() {
    // tuple 解包
    auto [x, y, z] = std::make_tuple(1, 2.0, "three");
    std::cout << "x = " << x << ", y = " << y << ", z = " << z << std::endl;

    // map 遍历
    std::map<std::string, int> map = {{"a", 1}, {"b", 2}};
    for (const auto& [key, value] : map) {
        std::cout << key << ": " << value << std::endl;
    }
}

/**
 * 现代风格 9：std::optional (C++17)
 *
 * 优点：表示可能无值的情况
 */
std::optional<int> find_value(bool found) {
    if (found) {
        return 42;
    }
    return std::nullopt;
}

void modern_optional() {
    auto value = find_value(true);
    if (value) {
        std::cout << "值: " << *value << std::endl;
    }
}

/**
 * 现代风格 10：std::variant (C++17)
 *
 * 优点：类型安全的联合体
 */
void modern_variant() {
    std::variant<int, double, std::string> v = 42;

    std::cout << "int: " << std::get<int>(v) << std::endl;

    v = 3.14;
    std::cout << "double: " << std::get<double>(v) << std::endl;

    v = "hello";
    std::cout << "string: " << std::get<std::string>(v) << std::endl;
}

/**
 * 现代风格 11：constexpr
 *
 * 优点：编译时计算
 */
constexpr int factorial(int n) {
    return (n <= 1) ? 1 : n * factorial(n - 1);
}

void modern_constexpr() {
    constexpr int result = factorial(5);
    std::cout << "5! = " << result << std::endl;
}

/**
 * 现代风格 12：if constexpr (C++17)
 *
 * 优点：编译时分支
 */
template <typename T>
void modern_if_constexpr(T value) {
    if constexpr (std::is_integral_v<T>) {
        std::cout << "整数: " << value << std::endl;
    } else if constexpr (std::is_floating_point_v<T>) {
        std::cout << "浮点数: " << value << std::endl;
    } else {
        std::cout << "其他类型" << std::endl;
    }
}

/**
 * 现代风格 13：字符串字面量
 *
 * 优点：更清晰的字符串操作
 */
void modern_string_literals() {
    using namespace std::string_literals;
    auto str = "hello"s + " world"s;
    std::cout << str << std::endl;
}

/**
 * 现代风格 14：移动语义
 *
 * 优点：避免不必要的拷贝
 */
void modern_move() {
    std::vector<int> vec = {1, 2, 3};
    std::vector<int> other = std::move(vec);
    std::cout << "other 大小: " << other.size() << std::endl;
}

/**
 * 现代风格 15：完美转发
 *
 * 优点：保持参数的值类别
 */
template <typename T>
void modern_perfect_forwarding(T&& arg) {
    std::vector<int> vec = std::forward<T>(arg);
    std::cout << "大小: " << vec.size() << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 现代 C++ 风格示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "[1] 智能指针" << std::endl;
    modern_smart_pointer();
    std::cout << std::endl;

    std::cout << "[2] nullptr" << std::endl;
    modern_nullptr();
    std::cout << std::endl;

    std::cout << "[3] std::array" << std::endl;
    modern_array();
    std::cout << std::endl;

    std::cout << "[4] 范围 for 循环" << std::endl;
    modern_range_for();
    std::cout << std::endl;

    std::cout << "[5] auto 类型推导" << std::endl;
    modern_auto();
    std::cout << std::endl;

    std::cout << "[6] 初始化列表" << std::endl;
    modern_initializer_list();
    std::cout << std::endl;

    std::cout << "[7] lambda 表达式" << std::endl;
    modern_lambda();
    std::cout << std::endl;

    std::cout << "[8] 结构化绑定" << std::endl;
    modern_structured_binding();
    std::cout << std::endl;

    std::cout << "[9] std::optional" << std::endl;
    modern_optional();
    std::cout << std::endl;

    std::cout << "[10] std::variant" << std::endl;
    modern_variant();
    std::cout << std::endl;

    std::cout << "[11] constexpr" << std::endl;
    modern_constexpr();
    std::cout << std::endl;

    std::cout << "[12] if constexpr" << std::endl;
    modern_if_constexpr(42);
    modern_if_constexpr(3.14);
    std::cout << std::endl;

    std::cout << "[13] 字符串字面量" << std::endl;
    modern_string_literals();
    std::cout << std::endl;

    std::cout << "[14] 移动语义" << std::endl;
    modern_move();
    std::cout << std::endl;

    std::cout << "[15] 完美转发" << std::endl;
    modern_perfect_forwarding(std::vector<int>{1, 2, 3});
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
