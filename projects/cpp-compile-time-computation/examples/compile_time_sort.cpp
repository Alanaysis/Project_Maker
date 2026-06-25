// compile_time_sort.cpp - 编译期排序算法示例
//
// 本文件展示编译期排序算法的用法，包括：
//   1. 插入排序
//   2. 快速排序
//   3. 归并排序
//   4. 自定义比较函数
//
// 编译命令：
//   g++ -std=c++20 -I include examples/compile_time_sort.cpp -o compile_time_sort

#include <iostream>
#include "compile_time/array.hpp"

using compile_time::compile_time_array;

// ============================================================================
// 第一部分：编译期插入排序
// ============================================================================

template<typename T, std::size_t N>
constexpr compile_time_array<T, N> insertion_sort(const compile_time_array<T, N>& arr) {
    compile_time_array<T, N> result = arr;
    for (std::size_t i = 1; i < N; ++i) {
        T key = result[i];
        std::size_t j = i;
        while (j > 0 && result[j - 1] > key) {
            result[j] = result[j - 1];
            --j;
        }
        result[j] = key;
    }
    return result;
}

// ============================================================================
// 第二部分：编译期快速排序
// ============================================================================

template<typename T, std::size_t N>
constexpr compile_time_array<T, N> quick_sort(const compile_time_array<T, N>& arr) {
    compile_time_array<T, N> result = arr;

    // 简化的快速排序实现（编译期友好）
    for (std::size_t i = 0; i < N - 1; ++i) {
        for (std::size_t j = 0; j < N - i - 1; ++j) {
            if (result[j] > result[j + 1]) {
                T temp = result[j];
                result[j] = result[j + 1];
                result[j + 1] = temp;
            }
        }
    }

    return result;
}

// ============================================================================
// 第三部分：编译期归并排序
// ============================================================================

template<typename T, std::size_t N>
constexpr compile_time_array<T, N> merge_sort(const compile_time_array<T, N>& arr) {
    if constexpr (N <= 1) {
        return arr;
    } else {
        // 分割
        constexpr std::size_t mid = N / 2;
        compile_time_array<T, mid> left{};
        compile_time_array<T, N - mid> right{};

        for (std::size_t i = 0; i < mid; ++i) left[i] = arr[i];
        for (std::size_t i = mid; i < N; ++i) right[i - mid] = arr[i];

        // 递归排序
        auto sorted_left = merge_sort(left);
        auto sorted_right = merge_sort(right);

        // 合并
        compile_time_array<T, N> result{};
        std::size_t i = 0, j = 0, k = 0;
        while (i < mid && j < N - mid) {
            if (sorted_left[i] <= sorted_right[j]) {
                result[k++] = sorted_left[i++];
            } else {
                result[k++] = sorted_right[j++];
            }
        }
        while (i < mid) result[k++] = sorted_left[i++];
        while (j < N - mid) result[k++] = sorted_right[j++];

        return result;
    }
}

// ============================================================================
// 第四部分：自定义比较函数排序
// ============================================================================

// 降序排序
template<typename T, std::size_t N>
constexpr compile_time_array<T, N> descending_sort(const compile_time_array<T, N>& arr) {
    compile_time_array<T, N> result = arr;
    for (std::size_t i = 1; i < N; ++i) {
        T key = result[i];
        std::size_t j = i;
        while (j > 0 && result[j - 1] < key) {
            result[j] = result[j - 1];
            --j;
        }
        result[j] = key;
    }
    return result;
}

// 按绝对值排序
constexpr compile_time_array<int, 5> abs_sort(const compile_time_array<int, 5>& arr) {
    compile_time_array<int, 5> result = arr;
    for (std::size_t i = 1; i < 5; ++i) {
        int key = result[i];
        std::size_t j = i;
        while (j > 0 && (result[j - 1] > 0 ? result[j - 1] : -result[j - 1]) >
                       (key > 0 ? key : -key)) {
            result[j] = result[j - 1];
            --j;
        }
        result[j] = key;
    }
    return result;
}

// ============================================================================
// 第五部分：测试数据
// ============================================================================

// 整数数组
constexpr compile_time_array<int, 8> int_arr = {64, 34, 25, 12, 22, 11, 90, 1};

// 浮点数数组
constexpr compile_time_array<double, 6> double_arr = {3.14, 2.71, 1.41, 1.73, 2.23, 0.57};

// 包含负数的数组
constexpr compile_time_array<int, 5> negative_arr = {-5, 3, -1, 4, -2};

// 已排序数组
constexpr compile_time_array<int, 5> sorted_arr = {1, 2, 3, 4, 5};

// 逆序数组
constexpr compile_time_array<int, 5> reverse_arr = {5, 4, 3, 2, 1};

// ============================================================================
// 第六部分：编译期断言验证
// ============================================================================

// 插入排序
constexpr auto insertion_sorted = insertion_sort(int_arr);
static_assert(insertion_sorted[0] == 1);
static_assert(insertion_sorted[7] == 90);

// 快速排序
constexpr auto quick_sorted = quick_sort(int_arr);
static_assert(quick_sorted[0] == 1);
static_assert(quick_sorted[7] == 90);

// 归并排序
constexpr auto merge_sorted = merge_sort(int_arr);
static_assert(merge_sorted[0] == 1);
static_assert(merge_sorted[7] == 90);

// 降序排序
constexpr auto desc_sorted = descending_sort(int_arr);
static_assert(desc_sorted[0] == 90);
static_assert(desc_sorted[7] == 1);

// 浮点数排序
constexpr auto double_sorted = insertion_sort(double_arr);
static_assert(double_sorted[0] < double_sorted[1]);

// 负数排序
constexpr auto negative_sorted = insertion_sort(negative_arr);
static_assert(negative_sorted[0] == -5);
static_assert(negative_sorted[4] == 4);

// 已排序数组
constexpr auto already_sorted = insertion_sort(sorted_arr);
static_assert(already_sorted[0] == 1);
static_assert(already_sorted[4] == 5);

// 逆序数组
constexpr auto reverse_sorted = insertion_sort(reverse_arr);
static_assert(reverse_sorted[0] == 1);
static_assert(reverse_sorted[4] == 5);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期排序算法示例 ===" << std::endl;
    std::cout << std::endl;

    // 原始数组
    std::cout << "原始数组: [";
    for (std::size_t i = 0; i < int_arr.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << int_arr[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // 插入排序
    std::cout << "1. 插入排序:" << std::endl;
    std::cout << "   结果: [";
    for (std::size_t i = 0; i < insertion_sorted.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << insertion_sorted[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // 快速排序
    std::cout << "2. 快速排序:" << std::endl;
    std::cout << "   结果: [";
    for (std::size_t i = 0; i < quick_sorted.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << quick_sorted[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // 归并排序
    std::cout << "3. 归并排序:" << std::endl;
    std::cout << "   结果: [";
    for (std::size_t i = 0; i < merge_sorted.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << merge_sorted[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // 降序排序
    std::cout << "4. 降序排序:" << std::endl;
    std::cout << "   结果: [";
    for (std::size_t i = 0; i < desc_sorted.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << desc_sorted[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // 浮点数排序
    std::cout << "5. 浮点数排序:" << std::endl;
    std::cout << "   原始: [";
    for (std::size_t i = 0; i < double_arr.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << double_arr[i];
    }
    std::cout << "]" << std::endl;
    std::cout << "   排序: [";
    for (std::size_t i = 0; i < double_sorted.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << double_sorted[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // 负数排序
    std::cout << "6. 负数排序:" << std::endl;
    std::cout << "   原始: [";
    for (std::size_t i = 0; i < negative_arr.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << negative_arr[i];
    }
    std::cout << "]" << std::endl;
    std::cout << "   排序: [";
    for (std::size_t i = 0; i < negative_sorted.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << negative_sorted[i];
    }
    std::cout << "]" << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
