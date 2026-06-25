/**
 * @file ranges_algorithms_example.cpp
 * @brief C++23 ranges 更多算法示例
 *
 * C++23 为 ranges 添加了更多的算法，扩展了标准库的功能。
 *
 * 主要特点：
 * - 更多的 ranges 算法
 * - 支持投影
 * - 支持自定义比较器
 * - 更简洁的语法
 *
 * 编译命令：
 * g++ -std=c++23 -o ranges_algorithms_example ranges_algorithms_example.cpp
 */

#include <iostream>
#include <vector>
#include <string>
#include <ranges>
#include <algorithm>
#include <numeric>
#include <functional>

// ========== 1. 基本算法 ==========

void basic_algorithms() {
    std::cout << "=== 基本算法 ===" << std::endl;

    std::vector<int> data = {5, 2, 8, 1, 9, 3, 7, 4, 6};

    // 排序
    auto sorted = data | std::ranges::to<std::vector>();
    std::ranges::sort(sorted);
    std::cout << "Sorted: ";
    for (int n : sorted) std::cout << n << " ";
    std::cout << std::endl;

    // 查找
    auto it = std::ranges::find(data, 8);
    if (it != data.end()) {
        std::cout << "Found 8 at index: " << std::distance(data.begin(), it) << std::endl;
    }

    // 计数
    auto count = std::ranges::count_if(data, [](int n) { return n > 5; });
    std::cout << "Count of elements > 5: " << count << std::endl;
}

// ========== 2. 实际应用：数据统计 ==========

void data_statistics() {
    std::cout << "\n=== 实际应用：数据统计 ===" << std::endl;

    std::vector<int> data = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100};

    // 最小值和最大值
    auto [min_it, max_it] = std::ranges::minmax(data);
    std::cout << "Min: " << *min_it << std::endl;
    std::cout << "Max: " << *max_it << std::endl;

    // 总和
    int sum = std::ranges::fold_left(data, 0, std::plus{});
    std::cout << "Sum: " << sum << std::endl;

    // 平均值
    double avg = static_cast<double>(sum) / data.size();
    std::cout << "Average: " << avg << std::endl;
}

// ========== 3. 实际应用：数据转换 ==========

void data_transformation() {
    std::cout << "\n=== 实际应用：数据转换 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5};

    // 转换为平方
    auto squares = data
        | std::views::transform([](int x) { return x * x; })
        | std::ranges::to<std::vector>();

    std::cout << "Original: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    std::cout << "Squares: ";
    for (int n : squares) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 4. 实际应用：数据过滤 ==========

void data_filtering() {
    std::cout << "\n=== 实际应用：数据过滤 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 过滤偶数
    auto evens = data
        | std::views::filter([](int x) { return x % 2 == 0; })
        | std::ranges::to<std::vector>();

    std::cout << "Original: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    std::cout << "Evens: ";
    for (int n : evens) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 5. 实际应用：数据聚合 ==========

void data_aggregation() {
    std::cout << "\n=== 实际应用：数据聚合 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 分组求和
    auto grouped = data
        | std::views::chunk(3)
        | std::views::transform([](auto chunk) {
            return std::ranges::fold_left(chunk, 0, std::plus{});
        })
        | std::ranges::to<std::vector>();

    std::cout << "Group sums (chunks of 3): ";
    for (int n : grouped) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 6. 实际应用：数据排序 ==========

void data_sorting() {
    std::cout << "\n=== 实际应用：数据排序 ===" << std::endl;

    std::vector<std::pair<std::string, int>> students = {
        {"Charlie", 92},
        {"Alice", 95},
        {"Bob", 87},
        {"David", 78},
        {"Eve", 88}
    };

    // 按分数排序
    std::ranges::sort(students, {}, &std::pair<std::string, int>::second);

    std::cout << "Sorted by score:" << std::endl;
    for (const auto& [name, score] : students) {
        std::cout << "  " << name << ": " << score << std::endl;
    }
}

// ========== 7. 实际应用：数据搜索 ==========

void data_search() {
    std::cout << "\n=== 实际应用：数据搜索 ===" << std::endl;

    std::vector<int> data = {1, 3, 5, 7, 9, 11, 13, 15};

    // 二分查找
    bool found = std::ranges::binary_search(data, 7);
    std::cout << "Found 7: " << (found ? "yes" : "no") << std::endl;

    found = std::ranges::binary_search(data, 6);
    std::cout << "Found 6: " << (found ? "yes" : "no") << std::endl;

    // 查找第一个大于 10 的元素
    auto it = std::ranges::upper_bound(data, 10);
    if (it != data.end()) {
        std::cout << "First element > 10: " << *it << std::endl;
    }
}

// ========== 8. 实际应用：数据比较 ==========

void data_comparison() {
    std::cout << "\n=== 实际应用：数据比较 ===" << std::endl;

    std::vector<int> data1 = {1, 2, 3, 4, 5};
    std::vector<int> data2 = {1, 2, 3, 4, 5};
    std::vector<int> data3 = {1, 2, 3, 4, 6};

    // 比较
    std::cout << "data1 == data2: " << (std::ranges::equal(data1, data2) ? "yes" : "no") << std::endl;
    std::cout << "data1 == data3: " << (std::ranges::equal(data1, data3) ? "yes" : "no") << std::endl;

    // 字典序比较
    std::cout << "data1 < data3: " << (std::ranges::lexicographical_compare(data1, data3) ? "yes" : "no") << std::endl;
}

// ========== 9. 实际应用：数据去重 ==========

void data_deduplication() {
    std::cout << "\n=== 实际应用：数据去重 ===" << std::endl;

    std::vector<int> data = {1, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5};

    // 去重
    auto unique_data = data | std::ranges::to<std::vector>();
    std::ranges::sort(unique_data);
    auto [first, last] = std::ranges::unique(unique_data);
    unique_data.erase(first, last);

    std::cout << "Original: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    std::cout << "Unique: ";
    for (int n : unique_data) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 10. 实际应用：数据分区 ==========

void data_partitioning() {
    std::cout << "\n=== 实际应用：数据分区 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 分区：偶数在前，奇数在后
    auto partitioned = data | std::ranges::to<std::vector>();
    std::ranges::partition(partitioned, [](int n) { return n % 2 == 0; });

    std::cout << "Original: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    std::cout << "Partitioned (evens first): ";
    for (int n : partitioned) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 11. 实际应用：数据堆操作 ==========

void heap_operations() {
    std::cout << "\n=== 实际应用：数据堆操作 ===" << std::endl;

    std::vector<int> data = {3, 1, 4, 1, 5, 9, 2, 6, 5, 3};

    // 创建堆
    auto heap = data | std::ranges::to<std::vector>();
    std::ranges::make_heap(heap);

    std::cout << "Heap: ";
    for (int n : heap) std::cout << n << " ";
    std::cout << std::endl;

    // 弹出最大元素
    std::ranges::pop_heap(heap);
    int max_val = heap.back();
    heap.pop_back();

    std::cout << "Popped max: " << max_val << std::endl;
    std::cout << "Heap after pop: ";
    for (int n : heap) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 12. 实际应用：数据集合操作 ==========

void set_operations() {
    std::cout << "\n=== 实际应用：数据集合操作 ===" << std::endl;

    std::vector<int> set1 = {1, 2, 3, 4, 5};
    std::vector<int> set2 = {4, 5, 6, 7, 8};

    // 并集
    std::vector<int> union_result;
    std::ranges::set_union(set1, set2, std::back_inserter(union_result));
    std::cout << "Union: ";
    for (int n : union_result) std::cout << n << " ";
    std::cout << std::endl;

    // 交集
    std::vector<int> intersection_result;
    std::ranges::set_intersection(set1, set2, std::back_inserter(intersection_result));
    std::cout << "Intersection: ";
    for (int n : intersection_result) std::cout << n << " ";
    std::cout << std::endl;

    // 差集
    std::vector<int> difference_result;
    std::ranges::set_difference(set1, set2, std::back_inserter(difference_result));
    std::cout << "Difference (set1 - set2): ";
    for (int n : difference_result) std::cout << n << " ";
    std::cout << std::endl;
}

int main() {
    std::cout << "C++23 ranges 更多算法示例\n" << std::endl;

    basic_algorithms();
    data_statistics();
    data_transformation();
    data_filtering();
    data_aggregation();
    data_sorting();
    data_search();
    data_comparison();
    data_deduplication();
    data_partitioning();
    heap_operations();
    set_operations();

    return 0;
}
