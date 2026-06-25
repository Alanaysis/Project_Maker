/**
 * @file compile_time_map_filter_reduce.cpp
 * @brief 编译期 Map/Filter/Reduce 示例
 */

#include <iostream>
#include "../include/compile_time/map_filter_reduce.hpp"

// Map 函数：翻倍
template <typename T, T V>
struct double_value {
    static constexpr T value = V * 2;
};

// Filter 谓词：偶数
template <typename T, T V>
struct is_even {
    static constexpr bool value = (V % 2 == 0);
};

// Filter 谓词：大于5
template <typename T, T V>
struct greater_than_5 {
    static constexpr bool value = (V > 5);
};

// Reduce 函数：加法
template <typename T, T Acc, T V>
struct add_op {
    static constexpr T value = Acc + V;
};

// Reduce 函数：乘法
template <typename T, T Acc, T V>
struct mul_op {
    static constexpr T value = Acc * V;
};

int main() {
    using namespace tmp;

    std::cout << "=== Compile-time Map/Filter/Reduce ===" << std::endl;
    std::cout << std::endl;

    using my_list = value_list<int, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10>;

    // 1. Map: 翻倍
    std::cout << "--- 1. Map (double each) ---" << std::endl;
    using doubled = value_map<my_list, double_value>;
    std::cout << "Input:  1, 2, 3, 4, 5, 6, 7, 8, 9, 10" << std::endl;
    std::cout << "Doubled: 2, 4, 6, 8, 10, 12, 14, 16, 18, 20" << std::endl;
    static_assert(value_at<doubled, 0> == 2);
    static_assert(value_at<doubled, 4> == 10);
    static_assert(value_at<doubled, 9> == 20);
    std::cout << std::endl;

    // 2. Filter: 偶数
    std::cout << "--- 2. Filter (even numbers) ---" << std::endl;
    using evens = value_filter<my_list, is_even>;
    std::cout << "Input: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10" << std::endl;
    std::cout << "Evens: 2, 4, 6, 8, 10" << std::endl;
    static_assert(evens::size == 5);
    static_assert(value_at<evens, 0> == 2);
    static_assert(value_at<evens, 4> == 10);
    std::cout << std::endl;

    // 3. Filter: 大于5
    std::cout << "--- 3. Filter (greater than 5) ---" << std::endl;
    using gt5 = value_filter<my_list, greater_than_5>;
    std::cout << "Input: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10" << std::endl;
    std::cout << "Greater than 5: 6, 7, 8, 9, 10" << std::endl;
    static_assert(gt5::size == 5);
    std::cout << std::endl;

    // 4. Reduce: 求和
    std::cout << "--- 4. Reduce (sum) ---" << std::endl;
    constexpr auto total = value_reduce<int, my_list, add_op, 0>;
    std::cout << "Sum of 1..10 = " << total << std::endl;
    static_assert(total == 55);
    std::cout << std::endl;

    // 5. Reduce: 乘积
    std::cout << "--- 5. Reduce (product) ---" << std::endl;
    using small_list = value_list<int, 1, 2, 3, 4, 5>;
    constexpr auto prod = value_reduce<int, small_list, mul_op, 1>;
    std::cout << "Product of 1..5 = " << prod << std::endl;
    static_assert(prod == 120);
    std::cout << std::endl;

    // 6. Take / Drop
    std::cout << "--- 6. Take / Drop ---" << std::endl;
    using taken = value_take<my_list, 3>;
    using dropped = value_drop<my_list, 7>;
    std::cout << "Take 3: " << value_at<taken, 0> << ", " << value_at<taken, 1>
              << ", " << value_at<taken, 2> << std::endl;
    std::cout << "Drop 7: " << value_at<dropped, 0> << ", " << value_at<dropped, 1>
              << ", " << value_at<dropped, 2> << std::endl;
    std::cout << std::endl;

    // 7. Accumulate (fold expression)
    std::cout << "--- 7. Accumulate (fold expression) ---" << std::endl;
    constexpr auto acc = accumulate_values(my_list{}, 0);
    std::cout << "Accumulate: " << acc << std::endl;
    std::cout << std::endl;

    // 8. Product (fold expression)
    std::cout << "--- 8. Product (fold expression) ---" << std::endl;
    constexpr auto p = product_values(small_list{});
    std::cout << "Product: " << p << std::endl;

    return 0;
}
