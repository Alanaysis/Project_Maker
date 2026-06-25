/**
 * C++11/14 Lambda 表达式示例
 *
 * 学习目标：
 * 1. 理解 Lambda 表达式的语法
 * 2. 掌握捕获列表（值捕获、引用捕获）
 * 3. 学会使用泛型 Lambda（C++14）
 * 4. 了解 Lambda 与 STL 算法的配合
 */

#include <iostream>
#include <vector>
#include <algorithm>
#include <functional>
#include <string>
#include <numeric>
#include <memory>

// ==========================================
// 1. Lambda 基础语法
// ==========================================

void demonstrate_basic_lambda() {
    std::cout << "\n=== 1. Lambda 基础语法 ===" << std::endl;

    // 最简单的 Lambda
    auto hello = []() {
        std::cout << "Hello, Lambda!" << std::endl;
    };
    hello();  // 调用 Lambda

    // 带参数的 Lambda
    auto add = [](int a, int b) -> int {
        return a + b;
    };
    std::cout << "3 + 4 = " << add(3, 4) << std::endl;

    // 返回类型自动推导
    auto multiply = [](int a, int b) { return a * b; };
    std::cout << "3 * 4 = " << multiply(3, 4) << std::endl;

    // 立即调用的 Lambda（IIFE - Immediately Invoked Function Expression）
    auto result = [](int x) { return x * x; }(5);
    std::cout << "5² = " << result << std::endl;
}

// ==========================================
// 2. 捕获列表
// ==========================================

void demonstrate_captures() {
    std::cout << "\n=== 2. 捕获列表 ===" << std::endl;

    int x = 10;
    int y = 20;
    std::string name = "C++";

    // 值捕获（拷贝）
    auto capture_by_value = [x, y]() {
        // x 和 y 是只读的副本
        std::cout << "值捕获: x=" << x << ", y=" << y << std::endl;
    };
    capture_by_value();

    // 引用捕获
    auto capture_by_ref = [&x, &y]() {
        x += 5;
        y += 10;
        std::cout << "引用捕获后: x=" << x << ", y=" << y << std::endl;
    };
    capture_by_ref();
    std::cout << "原始值: x=" << x << ", y=" << y << std::endl;

    // 隐式值捕获所有变量 [=]
    auto capture_all_value = [=]() {
        std::cout << "隐式值捕获: x=" << x << ", y=" << y
                  << ", name=" << name << std::endl;
    };
    capture_all_value();

    // 隐式引用捕获所有变量 [&]
    auto capture_all_ref = [&]() {
        x = 100;
        y = 200;
        name = "Modern C++";
    };
    capture_all_ref();
    std::cout << "修改后: x=" << x << ", y=" << y << ", name=" << name << std::endl;

    // 混合捕获
    auto mixed_capture = [=, &name]() {
        // x 和 y 是值捕获（只读）
        // name 是引用捕获（可修改）
        name = "C++11";
        std::cout << "混合捕获: x=" << x << ", name=" << name << std::endl;
    };
    mixed_capture();

    // C++14 初始化捕获（generalized capture）
    auto init_capture = [value = 42, text = std::string("Hello")]() {
        std::cout << "初始化捕获: value=" << value << ", text=" << text << std::endl;
    };
    init_capture();

    // 移动捕获（C++14）
    auto ptr = std::make_unique<int>(42);
    auto move_capture = [p = std::move(ptr)]() {
        std::cout << "移动捕获: *p=" << *p << std::endl;
    };
    move_capture();
    // ptr 现在为空
    std::cout << "ptr is " << (ptr ? "valid" : "null") << std::endl;
}

// ==========================================
// 3. Lambda 与 STL 算法
// ==========================================

void demonstrate_lambda_with_algorithms() {
    std::cout << "\n=== 3. Lambda 与 STL 算法 ===" << std::endl;

    std::vector<int> numbers = {5, 2, 8, 1, 9, 3, 7, 4, 6};

    // 排序
    std::cout << "--- 排序 ---" << std::endl;
    std::sort(numbers.begin(), numbers.end(), [](int a, int b) {
        return a < b;  // 升序
    });
    std::cout << "升序: ";
    for (int n : numbers) std::cout << n << " ";
    std::cout << std::endl;

    // 降序排序
    std::sort(numbers.begin(), numbers.end(), [](int a, int b) {
        return a > b;  // 降序
    });
    std::cout << "降序: ";
    for (int n : numbers) std::cout << n << " ";
    std::cout << std::endl;

    // 查找
    std::cout << "\n--- 查找 ---" << std::endl;
    auto it = std::find_if(numbers.begin(), numbers.end(), [](int n) {
        return n > 5;
    });
    if (it != numbers.end()) {
        std::cout << "第一个大于5的数: " << *it << std::endl;
    }

    // 计数
    std::cout << "\n--- 计数 ---" << std::endl;
    auto count = std::count_if(numbers.begin(), numbers.end(), [](int n) {
        return n % 2 == 0;  // 偶数
    });
    std::cout << "偶数个数: " << count << std::endl;

    // 转换
    std::cout << "\n--- 转换 ---" << std::endl;
    std::vector<int> squared(numbers.size());
    std::transform(numbers.begin(), numbers.end(), squared.begin(), [](int n) {
        return n * n;
    });
    std::cout << "平方: ";
    for (int n : squared) std::cout << n << " ";
    std::cout << std::endl;

    // 过滤
    std::cout << "\n--- 过滤 ---" << std::endl;
    std::vector<int> evens;
    std::copy_if(numbers.begin(), numbers.end(), std::back_inserter(evens),
        [](int n) { return n % 2 == 0; });
    std::cout << "偶数: ";
    for (int n : evens) std::cout << n << " ";
    std::cout << std::endl;

    // 累积
    std::cout << "\n--- 累积 ---" << std::endl;
    int sum = std::accumulate(numbers.begin(), numbers.end(), 0,
        [](int acc, int n) { return acc + n; });
    std::cout << "总和: " << sum << std::endl;

    // 归约
    int product = std::accumulate(numbers.begin(), numbers.end(), 1,
        [](int acc, int n) { return acc * n; });
    std::cout << "乘积: " << product << std::endl;
}

// ==========================================
// 4. Lambda 作为函数参数
// ==========================================

// 接受 Lambda 作为参数的函数
void apply_to_vector(const std::vector<int>& vec,
                     std::function<void(int)> func) {
    for (int n : vec) {
        func(n);
    }
}

// 使用模板接受 Lambda（更高效）
template<typename Func>
void apply_to_vector_template(const std::vector<int>& vec, Func func) {
    for (int n : vec) {
        func(n);
    }
}

void demonstrate_lambda_as_parameter() {
    std::cout << "\n=== 4. Lambda 作为函数参数 ===" << std::endl;

    std::vector<int> numbers = {1, 2, 3, 4, 5};

    // 使用 std::function
    std::cout << "--- 使用 std::function ---" << std::endl;
    apply_to_vector(numbers, [](int n) {
        std::cout << n * 2 << " ";
    });
    std::cout << std::endl;

    // 使用模板
    std::cout << "--- 使用模板 ---" << std::endl;
    apply_to_vector_template(numbers, [](int n) {
        std::cout << n * n << " ";
    });
    std::cout << std::endl;

    // 带捕获的 Lambda
    int multiplier = 3;
    apply_to_vector_template(numbers, [multiplier](int n) {
        std::cout << n * multiplier << " ";
    });
    std::cout << std::endl;
}

// ==========================================
// 5. Lambda 与闭包
// ==========================================

void demonstrate_closure() {
    std::cout << "\n=== 5. Lambda 与闭包 ===" << std::endl;

    // 闭包：捕获了外部变量的 Lambda
    auto create_adder = [](int base) {
        // 返回一个 Lambda，该 Lambda 捕获了 base
        return [base](int x) { return base + x; };
    };

    auto add5 = create_adder(5);
    auto add10 = create_adder(10);

    std::cout << "add5(3) = " << add5(3) << std::endl;
    std::cout << "add10(3) = " << add10(3) << std::endl;

    // 状态闭包
    auto counter = [count = 0]() mutable -> int {
        return ++count;
    };

    std::cout << "计数器: " << counter() << std::endl;
    std::cout << "计数器: " << counter() << std::endl;
    std::cout << "计数器: " << counter() << std::endl;

    // 闭包用于回调
    auto event_handler = [](const std::string& event) {
        std::cout << "处理事件: " << event << std::endl;
    };

    event_handler("click");
    event_handler("keypress");
}

// ==========================================
// 6. 泛型 Lambda（C++14）
// ==========================================

void demonstrate_generic_lambda() {
    std::cout << "\n=== 6. 泛型 Lambda（C++14）===" << std::endl;

    // 泛型 Lambda：使用 auto 参数
    auto generic_add = [](auto a, auto b) { return a + b; };

    std::cout << "int: " << generic_add(3, 4) << std::endl;
    std::cout << "double: " << generic_add(3.14, 2.86) << std::endl;
    std::cout << "string: " << generic_add(std::string("Hello, "), std::string("World!")) << std::endl;

    // 泛型 Lambda 用于打印
    auto print = [](const auto& container) {
        for (const auto& elem : container) {
            std::cout << elem << " ";
        }
        std::cout << std::endl;
    };

    std::vector<int> ints = {1, 2, 3, 4, 5};
    std::vector<std::string> strings = {"Hello", "World", "C++14"};

    std::cout << "ints: ";
    print(ints);
    std::cout << "strings: ";
    print(strings);

    // 泛型 Lambda 用于比较
    auto compare = [](const auto& a, const auto& b) {
        return a < b ? a : b;
    };

    std::cout << "min(3, 4) = " << compare(3, 4) << std::endl;
    std::cout << "min(3.14, 2.86) = " << compare(3.14, 2.86) << std::endl;
}

// ==========================================
// 7. Lambda 的实际应用
// ==========================================

void demonstrate_lambda_practical() {
    std::cout << "\n=== 7. Lambda 的实际应用 ===" << std::endl;

    // 策略模式
    std::cout << "--- 策略模式 ---" << std::endl;
    auto bubble_sort_strategy = [](std::vector<int>& vec) {
        for (size_t i = 0; i < vec.size(); ++i) {
            for (size_t j = 0; j < vec.size() - i - 1; ++j) {
                if (vec[j] > vec[j + 1]) {
                    std::swap(vec[j], vec[j + 1]);
                }
            }
        }
    };

    std::vector<int> data = {64, 34, 25, 12, 22, 11, 90};
    std::cout << "排序前: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    bubble_sort_strategy(data);

    std::cout << "排序后: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    // 事件系统
    std::cout << "\n--- 事件系统 ---" << std::endl;
    std::vector<std::function<void()>> event_handlers;

    event_handlers.push_back([]() { std::cout << "Handler 1 called" << std::endl; });
    event_handlers.push_back([]() { std::cout << "Handler 2 called" << std::endl; });
    event_handlers.push_back([]() { std::cout << "Handler 3 called" << std::endl; });

    for (auto& handler : event_handlers) {
        handler();
    }

    // 延迟计算
    std::cout << "\n--- 延迟计算 ---" << std::endl;
    auto lazy_compute = [](int x) {
        return [x]() {
            std::cout << "计算中..." << std::endl;
            return x * x;
        };
    };

    auto computation = lazy_compute(42);
    // 稍后执行
    std::cout << "结果: " << computation() << std::endl;
}

// ==========================================
// 主函数
// ==========================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "C++11/14 Lambda 表达式示例" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. 基础语法
    demonstrate_basic_lambda();

    // 2. 捕获列表
    demonstrate_captures();

    // 3. Lambda 与 STL 算法
    demonstrate_lambda_with_algorithms();

    // 4. Lambda 作为函数参数
    demonstrate_lambda_as_parameter();

    // 5. Lambda 与闭包
    demonstrate_closure();

    // 6. 泛型 Lambda（C++14）
    demonstrate_generic_lambda();

    // 7. Lambda 的实际应用
    demonstrate_lambda_practical();

    std::cout << "\n========================================" << std::endl;
    std::cout << "所有示例执行完毕！" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
