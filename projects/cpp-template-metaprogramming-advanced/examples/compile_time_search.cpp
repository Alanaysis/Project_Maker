/**
 * @file compile_time_search.cpp
 * @brief 编译期查找算法示例
 */

#include <iostream>
#include "../include/compile_time/search.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== Compile-time Search ===" << std::endl;
    std::cout << std::endl;

    // 1. 线性查找
    std::cout << "--- 1. Linear Search ---" << std::endl;
    using my_list = value_list<int, 10, 20, 30, 40, 50>;

    constexpr auto idx1 = linear_search(my_list{}, std::integral_constant<int, 30>{});
    std::cout << "Search for 30: index = " << idx1 << std::endl;

    constexpr auto idx2 = linear_search(my_list{}, std::integral_constant<int, 99>{});
    std::cout << "Search for 99: index = " << idx2
              << " (not found = max)" << std::endl;
    std::cout << std::endl;

    // 2. 值包含检查
    std::cout << "--- 2. Value Contains ---" << std::endl;
    static_assert(value_contains<my_list, 30>, "30 should be in list");
    static_assert(!value_contains<my_list, 99>, "99 should not be in list");
    std::cout << "value_contains<list, 30> = " << value_contains<my_list, 30> << std::endl;
    std::cout << "value_contains<list, 99> = " << value_contains<my_list, 99> << std::endl;
    std::cout << std::endl;

    // 3. 二分查找（已排序序列）
    std::cout << "--- 3. Binary Search ---" << std::endl;
    using sorted_list = value_list<int, 1, 3, 5, 7, 9, 11, 13, 15>;

    constexpr auto bidx = binary_search(sorted_list{}, std::integral_constant<int, 7>{});
    std::cout << "Binary search for 7: index = " << bidx << std::endl;
    std::cout << std::endl;

    // 4. 统计值出现次数
    std::cout << "--- 4. Count Value ---" << std::endl;
    using dup_list = value_list<int, 1, 2, 3, 2, 4, 2, 5>;
    constexpr auto cnt = count_value<int, 2, dup_list>;
    std::cout << "Count of 2 in [1,2,3,2,4,2,5]: " << cnt << std::endl;
    std::cout << std::endl;

    // 5. 最大/最小值索引
    std::cout << "--- 5. Max/Min Index ---" << std::endl;
    using data = value_list<int, 3, 7, 1, 9, 4>;
    constexpr auto max_idx = max_index<data>;
    constexpr auto min_idx = min_index<data>;
    std::cout << "Max value index: " << max_idx << " (value=" << value_at<data, max_idx> << ")" << std::endl;
    std::cout << "Min value index: " << min_idx << " (value=" << value_at<data, min_idx> << ")" << std::endl;

    return 0;
}
