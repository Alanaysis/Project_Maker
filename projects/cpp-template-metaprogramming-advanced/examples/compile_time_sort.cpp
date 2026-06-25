/**
 * @file compile_time_sort.cpp
 * @brief 编译期排序算法示例
 *
 * 所有排序在编译期完成，运行时零开销。
 */

#include <iostream>
#include <array>
#include "../include/compile_time/sort.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== Compile-time Sorting ===" << std::endl;
    std::cout << std::endl;

    // 1. 冒泡排序
    std::cout << "--- 1. Bubble Sort ---" << std::endl;
    using unsorted1 = value_list<int, 5, 3, 8, 1, 9, 2, 7, 4, 6>;
    using sorted1 = bubble_sort<int, 5, 3, 8, 1, 9, 2, 7, 4, 6>;

    static_assert(is_sorted<sorted1>, "Should be sorted");
    static_assert(sorted1::size == 9, "Size should be preserved");

    // 验证排序结果
    constexpr auto v0 = value_at<sorted1, 0>;
    constexpr auto v1 = value_at<sorted1, 1>;
    constexpr auto v2 = value_at<sorted1, 2>;
    constexpr auto v8 = value_at<sorted1, 8>;

    std::cout << "Input:  5, 3, 8, 1, 9, 2, 7, 4, 6" << std::endl;
    std::cout << "Sorted: " << v0 << ", " << v1 << ", " << v2
              << ", ..., " << v8 << std::endl;
    std::cout << std::endl;

    // 2. 选择排序
    std::cout << "--- 2. Selection Sort ---" << std::endl;
    using sorted2 = selection_sort<int, 64, 25, 12, 22, 11>;

    static_assert(is_sorted<sorted2>, "Should be sorted");
    constexpr auto s0 = value_at<sorted2, 0>;
    constexpr auto s1 = value_at<sorted2, 1>;
    constexpr auto s2 = value_at<sorted2, 2>;
    constexpr auto s3 = value_at<sorted2, 3>;
    constexpr auto s4 = value_at<sorted2, 4>;

    std::cout << "Input:  64, 25, 12, 22, 11" << std::endl;
    std::cout << "Sorted: " << s0 << ", " << s1 << ", " << s2
              << ", " << s3 << ", " << s4 << std::endl;
    std::cout << std::endl;

    // 3. 插入排序
    std::cout << "--- 3. Insertion Sort ---" << std::endl;
    using sorted3 = insertion_sort<int, 12, 11, 13, 5, 6>;

    static_assert(is_sorted<sorted3>, "Should be sorted");
    constexpr auto i0 = value_at<sorted3, 0>;
    constexpr auto i1 = value_at<sorted3, 1>;
    constexpr auto i2 = value_at<sorted3, 2>;
    constexpr auto i3 = value_at<sorted3, 3>;
    constexpr auto i4 = value_at<sorted3, 4>;

    std::cout << "Input:  12, 11, 13, 5, 6" << std::endl;
    std::cout << "Sorted: " << i0 << ", " << i1 << ", " << i2
              << ", " << i3 << ", " << i4 << std::endl;
    std::cout << std::endl;

    // 4. 边界情况
    std::cout << "--- 4. Edge Cases ---" << std::endl;

    // 空列表
    using empty_sorted = bubble_sort<int>;
    static_assert(empty_sorted::size == 0, "Empty list");

    // 单元素
    using single_sorted = bubble_sort<int, 42>;
    static_assert(value_at<single_sorted, 0> == 42, "Single element");

    // 已排序
    using already_sorted = insertion_sort<int, 1, 2, 3, 4, 5>;
    static_assert(is_sorted<already_sorted>, "Already sorted");

    // 逆序
    using reverse_sorted = selection_sort<int, 5, 4, 3, 2, 1>;
    static_assert(is_sorted<reverse_sorted>, "Reverse sorted");

    std::cout << "Edge cases passed!" << std::endl;
    std::cout << std::endl;

    // 5. 编译期统计
    std::cout << "--- 5. Compile-time Statistics ---" << std::endl;
    constexpr auto max_val = max_value<sorted1>;
    constexpr auto min_val = min_value<sorted1>;
    constexpr auto total = sum<sorted1>;

    std::cout << "Max value: " << max_val << std::endl;
    std::cout << "Min value: " << min_val << std::endl;
    std::cout << "Sum: " << total << std::endl;

    return 0;
}
