/**
 * @file compile_time_algorithms.cpp
 * @brief 编译期算法单元测试
 */

#include <iostream>
#include "../include/compile_time/algorithms.hpp"

int tests_passed = 0;
int tests_failed = 0;

int main() {
    using namespace tmp;

    std::cout << "=== Compile-time Algorithm Tests ===" << std::endl;
    std::cout << std::endl;

    // Test bubble_sort
    std::cout << "Testing bubble_sort... ";
    {
        using sorted = bubble_sort<int, 5, 3, 8, 1, 9, 2, 7, 4, 6>;
        static_assert(is_sorted<sorted>, "Should be sorted");
        static_assert(sorted::size == 9, "Size should be 9");
        static_assert(value_at<sorted, 0> == 1, "First should be 1");
        static_assert(value_at<sorted, 8> == 9, "Last should be 9");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test selection_sort
    std::cout << "Testing selection_sort... ";
    {
        using sorted = selection_sort<int, 64, 25, 12, 22, 11>;
        static_assert(is_sorted<sorted>, "Should be sorted");
        static_assert(value_at<sorted, 0> == 11, "First should be 11");
        static_assert(value_at<sorted, 4> == 64, "Last should be 64");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test insertion_sort
    std::cout << "Testing insertion_sort... ";
    {
        using sorted = insertion_sort<int, 12, 11, 13, 5, 6>;
        static_assert(is_sorted<sorted>, "Should be sorted");
        static_assert(value_at<sorted, 0> == 5, "First should be 5");
        static_assert(value_at<sorted, 4> == 13, "Last should be 13");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test sort edge cases
    std::cout << "Testing sort edge cases... ";
    {
        using empty = bubble_sort<int>;
        static_assert(empty::size == 0, "Empty list");

        using single = bubble_sort<int, 42>;
        static_assert(value_at<single, 0> == 42, "Single element");

        using already = insertion_sort<int, 1, 2, 3>;
        static_assert(is_sorted<already>, "Already sorted");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test linear_search
    std::cout << "Testing linear_search... ";
    {
        using L = value_list<int, 10, 20, 30, 40, 50>;
        constexpr auto idx = linear_search(L{}, std::integral_constant<int, 30>{});
        static_assert(idx == 2, "Index should be 2");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test value_contains
    std::cout << "Testing value_contains... ";
    {
        using L = value_list<int, 10, 20, 30, 40, 50>;
        static_assert(value_contains<L, 30>, "Should contain 30");
        static_assert(!value_contains<L, 99>, "Should not contain 99");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test max_min_value
    std::cout << "Testing max_min_value... ";
    {
        using L = value_list<int, 3, 7, 1, 9, 4>;
        static_assert(max_value<L> == 9, "Max should be 9");
        static_assert(min_value<L> == 1, "Min should be 1");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test sum
    std::cout << "Testing sum... ";
    {
        using L = value_list<int, 1, 2, 3, 4, 5>;
        static_assert(sum<L> == 15, "Sum should be 15");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test value_take_drop
    std::cout << "Testing value_take_drop... ";
    {
        using L = value_list<int, 1, 2, 3, 4, 5>;
        using T = value_take<L, 3>;
        using D = value_drop<L, 2>;
        static_assert(T::size == 3, "Take 3 size should be 3");
        static_assert(D::size == 3, "Drop 2 size should be 3");
        static_assert(value_at<T, 0> == 1, "Take first should be 1");
        static_assert(value_at<D, 0> == 3, "Drop first should be 3");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    std::cout << std::endl;
    std::cout << "Results: " << tests_passed << " passed, "
              << tests_failed << " failed" << std::endl;

    return tests_failed > 0 ? 1 : 0;
}
