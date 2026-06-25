/**
 * 09_lambda_improvements.cpp - C++20 Lambda 表达式改进
 *
 * C++20 对 Lambda 表达式进行了大量改进。
 *
 * 核心要点：
 * 1. 模板 Lambda - auto 和模板参数
 * 2. Lambda 捕获 this 的改进
 * 3. constexpr Lambda 改进
 * 4. [=, this] 捕获语法
 * 5. Lambda 的可默认构造和可赋值
 * 6. 括号初始化捕获
 */

#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <functional>
#include <type_traits>

// ============================================================
// 1. 模板 Lambda (Template Lambdas)
// ============================================================

void template_lambdas() {
    std::cout << "【1. 模板 Lambda】\n";

    // C++20: 使用 <typename T> 模板语法
    auto generic_add = []<typename T>(T a, T b) -> T {
        return a + b;
    };
    std::cout << "int add: " << generic_add(3, 4) << "\n";
    std::cout << "double add: " << generic_add(1.5, 2.5) << "\n";

    // 使用概念约束模板 Lambda
    auto constrained = []<typename T> requires std::integral<T>(T a, T b) {
        return a % b;
    };
    std::cout << "10 % 3 = " << constrained(10, 3) << "\n";

    // 访问模板参数的类型信息
    auto type_info = []<typename T>(T) {
        return typeid(T).name();
    };
    std::cout << "type of 42: " << type_info(42) << "\n";
    std::cout << "type of 3.14: " << type_info(3.14) << "\n\n";
}

// ============================================================
// 2. 捕获 this 的改进
// ============================================================

struct Counter {
    int count = 0;

    // C++17 方式（有问题 - 捕获的是指针副本）
    // auto get_incrementer_old() {
    //     return [*this]() { return ++count; };  // C++20: 按值捕获 this
    // }

    // C++20: [*this] 按值捕获整个对象
    auto get_incrementer_copy() {
        return [*this]() mutable { return ++count; };
    }

    // [&] 捕获 this 引用（与 C++17 相同）
    auto get_incrementer_ref() {
        return [this]() { return ++count; };
    }
};

void capture_this() {
    std::cout << "【2. 捕获 this 的改进】\n";

    Counter c{10};
    auto copy_inc = c.get_incrementer_copy();
    auto ref_inc = c.get_incrementer_ref();

    std::cout << "原始值: " << c.count << "\n";
    std::cout << "按值捕获调用: " << copy_inc() << " (不影响原始对象)\n";
    std::cout << "按引用捕获调用: " << ref_inc() << " (修改原始对象)\n";
    std::cout << "原始值: " << c.count << "\n\n";
}

// ============================================================
// 3. constexpr Lambda 改进
// ============================================================

constexpr auto constexpr_square = [](int x) { return x * x; };

void constexpr_lambdas() {
    std::cout << "【3. constexpr Lambda】\n";

    // 编译期求值
    constexpr int result = constexpr_square(5);
    std::cout << "constexpr square(5) = " << result << "\n";

    // 运行期也可以使用
    int runtime_val = 7;
    std::cout << "runtime square(7) = " << constexpr_square(runtime_val) << "\n\n";
}

// ============================================================
// 4. [=, this] 捕获语法
// ============================================================

struct Widget {
    int value = 42;

    void demonstrate() {
        // C++20: [=, this] 明确包含 this（隐式或显式）
        auto lambda = [=, this]() {
            std::cout << "value via this: " << value << "\n";
        };
        lambda();

        // C++20: [=, *this] 按值捕获 this
        auto lambda_copy = [=, *this]() mutable {
            value = 100;  // 修改副本
            std::cout << "copy value: " << value << "\n";
        };
        lambda_copy();
        std::cout << "original value: " << value << " (未改变)\n";
    }
};

void capture_syntax() {
    std::cout << "【4. [=, this] 捕获语法】\n";
    Widget w;
    w.demonstrate();
    std::cout << "\n";
}

// ============================================================
// 5. Lambda 默认构造和赋值
// ============================================================

void default_constructible() {
    std::cout << "【5. Lambda 默认构造和赋值】\n";

    // C++20: 无捕获的 Lambda 是默认构造和可赋值的
    auto square = [](int x) { return x * x; };
    using SquareType = decltype(square);

    // 默认构造
    SquareType default_constructed;
    std::cout << "默认构造 square(5) = " << default_constructed(5) << "\n";

    // 赋值
    SquareType assigned;
    assigned = square;
    std::cout << "赋值后 square(6) = " << assigned(6) << "\n\n";
}

// ============================================================
// 6. 实际应用
// ============================================================

void practical_examples() {
    std::cout << "【6. 实际应用】\n";

    // 模板 Lambda 用于多类型排序
    auto flexible_sort = []<typename Container>(Container& c) {
        std::sort(c.begin(), c.end());
    };

    std::vector<int> nums = {3, 1, 4, 1, 5};
    flexible_sort(nums);
    std::cout << "排序后: ";
    for (auto n : nums) std::cout << n << " ";
    std::cout << "\n";

    // 模板 Lambda 用于通用打印
    auto print = []<typename T>(const T& val) {
        if constexpr (std::is_arithmetic_v<T>) {
            std::cout << "数值: " << val;
        } else {
            std::cout << "其他: " << val;
        }
        std::cout << "\n";
    };
    print(42);
    print(3.14);
    print(std::string("hello"));
    std::cout << "\n";
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 Lambda 改进示例 ===\n\n";

    template_lambdas();
    capture_this();
    constexpr_lambdas();
    capture_syntax();
    default_constructible();
    practical_examples();

    std::cout << "=== Lambda 改进示例完成 ===\n";
    return 0;
}
