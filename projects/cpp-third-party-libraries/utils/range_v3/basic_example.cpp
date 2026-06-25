/**
 * @file basic_example.cpp
 * @brief range-v3 范围库基础示例
 * @details 展示 range-v3 的基本用法
 *          range-v3 是一个函数式编程库
 *          提供视图、动作和算法
 */

#include <iostream>
#include <vector>
#include <string>
#include <range/v3/all.hpp>

/**
 * @brief 基础视图示例
 * @details 展示 range-v3 的视图操作
 */
void basic_views() {
    std::cout << "=== 基础视图 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 过滤视图：只保留偶数
    auto evens = data | ranges::views::filter([](int x) { return x % 2 == 0; });
    std::cout << "Evens: ";
    for (int x : evens) {
        std::cout << x << " ";
    }
    std::cout << std::endl;

    // 转换视图：平方
    auto squares = data | ranges::views::transform([](int x) { return x * x; });
    std::cout << "Squares: ";
    for (int x : squares) {
        std::cout << x << " ";
    }
    std::cout << std::endl;

    // 取前 N 个
    auto first5 = data | ranges::views::take(5);
    std::cout << "First 5: ";
    for (int x : first5) {
        std::cout << x << " ";
    }
    std::cout << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 组合视图示例
 * @details 展示如何组合多个视图
 */
void combined_views() {
    std::cout << "=== 组合视图 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 链式操作：过滤偶数，然后平方，然后取前 3 个
    auto result = data
        | ranges::views::filter([](int x) { return x % 2 == 0; })
        | ranges::views::transform([](int x) { return x * x; })
        | ranges::views::take(3);

    std::cout << "Filtered, squared, first 3: ";
    for (int x : result) {
        std::cout << x << " ";
    }
    std::cout << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 生成视图示例
 * @details 展示如何生成序列
 */
void generate_views() {
    std::cout << "=== 生成视图 ===" << std::endl;

    // 生成 0-9 的序列
    auto range = ranges::views::iota(0, 10);
    std::cout << "iota(0, 10): ";
    for (int x : range) {
        std::cout << x << " ";
    }
    std::cout << std::endl;

    // 生成无限序列，取前 10 个
    auto naturals = ranges::views::iota(1) | ranges::views::take(10);
    std::cout << "First 10 naturals: ";
    for (int x : naturals) {
        std::cout << x << " ";
    }
    std::cout << std::endl;

    // 生成斐波那契数列
    auto fibonacci = ranges::views::generate([a = 0, b = 1]() mutable {
        int result = a;
        a = b;
        b = result + b;
        return result;
    }) | ranges::views::take(10);

    std::cout << "Fibonacci: ";
    for (int x : fibonacci) {
        std::cout << x << " ";
    }
    std::cout << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 算法示例
 * @details 展示 range-v3 的算法
 */
void algorithms() {
    std::cout << "=== 算法 ===" << std::endl;

    std::vector<int> data = {5, 3, 1, 4, 2};

    // 排序
    auto sorted = data | ranges::to<std::vector>();
    ranges::sort(sorted);
    std::cout << "Sorted: ";
    for (int x : sorted) {
        std::cout << x << " ";
    }
    std::cout << std::endl;

    // 查找
    auto it = ranges::find(data, 4);
    if (it != ranges::end(data)) {
        std::cout << "Found 4 at position: " << ranges::distance(data.begin(), it) << std::endl;
    }

    // 计数
    auto count = ranges::count_if(data, [](int x) { return x > 3; });
    std::cout << "Count of elements > 3: " << count << std::endl;

    // 最小值和最大值
    auto min = ranges::min(data);
    auto max = ranges::max(data);
    std::cout << "Min: " << min << ", Max: " << max << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 range-v3 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：处理学生成绩
    struct Student {
        std::string name;
        int score;
    };

    std::vector<Student> students = {
        {"Alice", 85},
        {"Bob", 92},
        {"Charlie", 78},
        {"David", 95},
        {"Eve", 88}
    };

    // 获取及格学生（score >= 80）的姓名
    auto passing_names = students
        | ranges::views::filter([](const Student& s) { return s.score >= 80; })
        | ranges::views::transform([](const Student& s) { return s.name; });

    std::cout << "Passing students: ";
    for (const auto& name : passing_names) {
        std::cout << name << " ";
    }
    std::cout << std::endl;

    // 计算平均分
    auto scores = students | ranges::views::transform([](const Student& s) { return s.score; });
    double avg = ranges::accumulate(scores, 0.0) / students.size();
    std::cout << "Average score: " << avg << std::endl;

    // 获取最高分学生
    auto top_student = ranges::max(students, ranges::less{}, &Student::score);
    std::cout << "Top student: " << top_student.name << " (" << top_student.score << ")" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== range-v3 范围库示例 ===" << std::endl;
    std::cout << std::endl;

    basic_views();
    combined_views();
    generate_views();
    algorithms();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}