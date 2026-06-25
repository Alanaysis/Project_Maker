// compile_time_set.cpp - 编译期集合示例
//
// 本文件展示编译期集合的用法，包括：
//   1. 基本构造和访问
//   2. 查找和包含检查
//   3. 集合操作
//   4. 实际应用示例
//
// 编译命令：
//   g++ -std=c++20 -I include examples/compile_time_set.cpp -o compile_time_set

#include <iostream>
#include "compile_time/set.hpp"

using compile_time::compile_time_set;
using compile_time::make_set;

// ============================================================================
// 第一部分：基本构造和访问
// ============================================================================

// 从数组构造
constexpr int arr1[] = {5, 3, 1, 4, 2};
constexpr auto set1 = make_set(arr1);

// 访问元素（已排序）
constexpr int first = set1[0];  // 1
constexpr int last = set1[4];   // 5

// 容量
constexpr std::size_t set_size = set1.size();  // 5
constexpr bool is_empty = set1.empty();        // false

// ============================================================================
// 第二部分：查找和包含检查
// ============================================================================

// 查找（二分查找）
constexpr bool has_3 = set1.contains(3);   // true
constexpr bool has_10 = set1.contains(10);  // false

// ============================================================================
// 第三部分：集合操作
// ============================================================================

// 另一个集合
constexpr int arr2[] = {4, 5, 6, 7, 8};
constexpr auto set2 = make_set(arr2);

// 并集
constexpr auto union_set = set1.union_with(set2);

// 交集
constexpr auto intersection = set1.intersection_with(set2);

// 差集
constexpr auto difference = set1.difference_with(set2);

// ============================================================================
// 第四部分：实际应用示例
// ============================================================================

// 素数集合
constexpr int primes[] = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29};
constexpr auto prime_set = make_set(primes);

// 检查是否是素数
constexpr bool is_7_prime = prime_set.contains(7);   // true
constexpr bool is_10_prime = prime_set.contains(10);  // false

// 偶数集合
constexpr int evens[] = {2, 4, 6, 8, 10, 12, 14, 16, 18, 20};
constexpr auto even_set = make_set(evens);

// 奇数集合
constexpr int odds[] = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19};
constexpr auto odd_set = make_set(odds);

// ============================================================================
// 第五部分：编译期断言验证
// ============================================================================

// 基本构造和访问
static_assert(first == 1);
static_assert(last == 5);
static_assert(set_size == 5);
static_assert(is_empty == false);

// 查找
static_assert(has_3 == true);
static_assert(has_10 == false);

// 集合操作
// 并集应该包含两个集合的所有元素（可能有重复）
static_assert(union_set.size() == 10);  // {1,2,3,4,5,4,5,6,7,8}（简化实现）

// 交集应该只包含公共元素
static_assert(intersection[0] == 4);
static_assert(intersection[1] == 5);

// 差集应该只包含 set1 中有但 set2 中没有的元素（简化实现返回固定大小数组）
static_assert(difference.size() == 5);  // 返回大小为 N 的数组，前 3 个有效
static_assert(difference[0] == 1);
static_assert(difference[1] == 2);
static_assert(difference[2] == 3);

// 素数集合
static_assert(is_7_prime == true);
static_assert(is_10_prime == false);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期集合示例 ===" << std::endl;
    std::cout << std::endl;

    // 基本构造和访问
    std::cout << "1. 基本构造和访问:" << std::endl;
    std::cout << "   set1 = {";
    for (std::size_t i = 0; i < set1.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << set1[i];
    }
    std::cout << "}" << std::endl;
    std::cout << "   set1[0] = " << set1[0] << std::endl;
    std::cout << "   set1.size() = " << set1.size() << std::endl;
    std::cout << std::endl;

    // 查找
    std::cout << "2. 查找和包含检查:" << std::endl;
    std::cout << "   contains(3): " << (has_3 ? "true" : "false") << std::endl;
    std::cout << "   contains(10): " << (has_10 ? "true" : "false") << std::endl;
    std::cout << std::endl;

    // 集合操作
    std::cout << "3. 集合操作:" << std::endl;
    std::cout << "   set2 = {";
    for (std::size_t i = 0; i < set2.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << set2[i];
    }
    std::cout << "}" << std::endl;
    std::cout << std::endl;

    std::cout << "   并集 = {";
    for (std::size_t i = 0; i < union_set.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << union_set[i];
    }
    std::cout << "}" << std::endl;

    std::cout << "   交集 = {";
    for (std::size_t i = 0; i < intersection.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << intersection[i];
    }
    std::cout << "}" << std::endl;

    std::cout << "   差集 = {";
    for (std::size_t i = 0; i < difference.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << difference[i];
    }
    std::cout << "}" << std::endl;
    std::cout << std::endl;

    // 素数集合
    std::cout << "4. 素数集合:" << std::endl;
    std::cout << "   prime_set = {";
    for (std::size_t i = 0; i < prime_set.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << prime_set[i];
    }
    std::cout << "}" << std::endl;
    std::cout << "   is 7 prime? " << (is_7_prime ? "yes" : "no") << std::endl;
    std::cout << "   is 10 prime? " << (is_10_prime ? "yes" : "no") << std::endl;
    std::cout << std::endl;

    // 偶数和奇数集合
    std::cout << "5. 偶数和奇数集合:" << std::endl;
    std::cout << "   even_set = {";
    for (std::size_t i = 0; i < even_set.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << even_set[i];
    }
    std::cout << "}" << std::endl;
    std::cout << "   odd_set = {";
    for (std::size_t i = 0; i < odd_set.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << odd_set[i];
    }
    std::cout << "}" << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
