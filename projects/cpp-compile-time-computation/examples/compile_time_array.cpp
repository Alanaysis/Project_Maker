// compile_time_array.cpp - 编译期数组示例
//
// 本文件展示编译期数组的用法，包括：
//   1. 基本构造和访问
//   2. 编译期算法
//   3. 编译期排序
//   4. 编译期查找
//
// 编译命令：
//   g++ -std=c++20 -I include examples/compile_time_array.cpp -o compile_time_array

#include <iostream>
#include "compile_time/array.hpp"

using compile_time::compile_time_array;

// ============================================================================
// 第一部分：基本构造和访问
// ============================================================================

// 从数组构造
constexpr compile_time_array<int, 5> arr1 = {5, 3, 1, 4, 2};

// 访问元素
constexpr int first = arr1[0];  // 5
constexpr int last = arr1[4];   // 2

// 容量
constexpr std::size_t size = arr1.size();  // 5
constexpr bool is_empty = arr1.empty();    // false

// ============================================================================
// 第二部分：编译期算法
// ============================================================================

// 编译期排序
constexpr auto sorted_arr = arr1.sorted();

// 编译期查找
constexpr std::size_t found = arr1.find(4);      // 3
constexpr std::size_t not_found = arr1.find(10);  // 5 (未找到)

// 编译期计数
constexpr std::size_t count = arr1.count(3);  // 1

// 编译期累加
constexpr int sum = arr1.sum();  // 15

// 编译期最小值和最大值
constexpr int min_val = arr1.min();  // 1
constexpr int max_val = arr1.max();  // 5

// 编译期反转
constexpr auto reversed_arr = arr1.reversed();

// ============================================================================
// 第三部分：编译期映射
// ============================================================================

// 编译期映射（转换元素）
constexpr auto squared_arr = arr1.map([](int x) { return x * x; });

// 编译期过滤计数
constexpr std::size_t even_count = arr1.count_if([](int x) { return x % 2 == 0; });

// 编译期折叠
constexpr int product = arr1.fold_left([](int acc, int x) { return acc * x; }, 1);

// ============================================================================
// 第四部分：编译期排序算法
// ============================================================================

// 自定义比较函数排序
constexpr auto desc_sorted = arr1.sorted([](int a, int b) { return a > b; });

// 浮点数数组
constexpr compile_time_array<double, 5> double_arr = {3.14, 2.71, 1.41, 1.73, 2.23};
constexpr auto sorted_doubles = double_arr.sorted();

// ============================================================================
// 第五部分：编译期数组操作
// ============================================================================

// 数组拼接
constexpr compile_time_array<int, 3> arr2 = {6, 7, 8};
constexpr auto concatenated = compile_time::concat(arr1, arr2);

// 数组填充
constexpr auto filled_array() {
    compile_time_array<int, 10> arr;
    arr.fill(42);
    return arr;
}
constexpr auto filled = filled_array();

// ============================================================================
// 第六部分：编译期断言验证
// ============================================================================

// 基本构造和访问
static_assert(first == 5);
static_assert(last == 2);
static_assert(size == 5);
static_assert(is_empty == false);

// 排序
static_assert(sorted_arr[0] == 1);
static_assert(sorted_arr[1] == 2);
static_assert(sorted_arr[2] == 3);
static_assert(sorted_arr[3] == 4);
static_assert(sorted_arr[4] == 5);

// 查找
static_assert(found == 3);
static_assert(not_found == 5);

// 计数和累加
static_assert(count == 1);
static_assert(sum == 15);
static_assert(min_val == 1);
static_assert(max_val == 5);

// 反转
static_assert(reversed_arr[0] == 2);
static_assert(reversed_arr[4] == 5);

// 映射
static_assert(squared_arr[0] == 25);
static_assert(squared_arr[4] == 4);

// 过滤
static_assert(even_count == 2);

// 折叠
static_assert(product == 120);

// 自定义排序
static_assert(desc_sorted[0] == 5);
static_assert(desc_sorted[4] == 1);

// 拼接
static_assert(concatenated.size() == 8);
static_assert(concatenated[5] == 6);

// 填充
static_assert(filled[0] == 42);
static_assert(filled[9] == 42);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期数组示例 ===" << std::endl;
    std::cout << std::endl;

    // 基本构造和访问
    std::cout << "1. 基本构造和访问:" << std::endl;
    std::cout << "   arr1 = [";
    for (std::size_t i = 0; i < arr1.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << arr1[i];
    }
    std::cout << "]" << std::endl;
    std::cout << "   arr1[0] = " << arr1[0] << std::endl;
    std::cout << "   arr1.size() = " << arr1.size() << std::endl;
    std::cout << std::endl;

    // 排序
    std::cout << "2. 编译期排序:" << std::endl;
    std::cout << "   sorted = [";
    for (std::size_t i = 0; i < sorted_arr.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << sorted_arr[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // 查找
    std::cout << "3. 编译期查找:" << std::endl;
    std::cout << "   find(4) = " << found << std::endl;
    std::cout << "   find(10) = " << not_found << " (未找到)" << std::endl;
    std::cout << std::endl;

    // 算法
    std::cout << "4. 编译期算法:" << std::endl;
    std::cout << "   sum = " << sum << std::endl;
    std::cout << "   min = " << min_val << std::endl;
    std::cout << "   max = " << max_val << std::endl;
    std::cout << "   count(3) = " << count << std::endl;
    std::cout << "   even_count = " << even_count << std::endl;
    std::cout << "   product = " << product << std::endl;
    std::cout << std::endl;

    // 映射
    std::cout << "5. 编译期映射:" << std::endl;
    std::cout << "   squared = [";
    for (std::size_t i = 0; i < squared_arr.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << squared_arr[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // 反转
    std::cout << "6. 编译期反转:" << std::endl;
    std::cout << "   reversed = [";
    for (std::size_t i = 0; i < reversed_arr.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << reversed_arr[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // 自定义排序
    std::cout << "7. 自定义排序（降序）:" << std::endl;
    std::cout << "   desc_sorted = [";
    for (std::size_t i = 0; i < desc_sorted.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << desc_sorted[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // 拼接
    std::cout << "8. 数组拼接:" << std::endl;
    std::cout << "   concatenated = [";
    for (std::size_t i = 0; i < concatenated.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << concatenated[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // 填充
    std::cout << "9. 数组填充:" << std::endl;
    std::cout << "   filled = [";
    for (std::size_t i = 0; i < filled.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << filled[i];
    }
    std::cout << "]" << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
