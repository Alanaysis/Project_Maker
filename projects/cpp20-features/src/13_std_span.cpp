/**
 * 13_std_span.cpp - C++20 std::span
 *
 * std::span 是一个非拥有的连续内存视图，类似 string_view 但适用于任意类型。
 *
 * 核心要点：
 * 1. 非拥有语义 - 不管理内存生命周期
 * 2. 统一接口 - 数组、vector、指针+长度
 * 3. 静态和动态 extent
 * 4. 子 span 操作
 * 5. 与 STL 算法兼容
 */

#include <iostream>
#include <span>
#include <vector>
#include <array>
#include <string>
#include <algorithm>
#include <numeric>

// ============================================================
// 1. 基本用法
// ============================================================

// 接受任意连续容器
void print_span(std::span<const int> s, const std::string& label) {
    std::cout << label << ": [";
    for (size_t i = 0; i < s.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << s[i];
    }
    std::cout << "]\n";
}

// ============================================================
// 2. 修改 span 指向的数据
// ============================================================

void double_all(std::span<int> s) {
    for (auto& val : s) {
        val *= 2;
    }
}

// ============================================================
// 3. 静态 extent
// ============================================================

// 编译期已知大小
void process_fixed(std::span<int, 5> s) {
    std::cout << "固定大小 span(" << s.size() << "): ";
    for (auto v : s) std::cout << v << " ";
    std::cout << "\n";
}

// ============================================================
// 4. 子 span 操作
// ============================================================

void subspan_demo(std::span<int> s) {
    std::cout << "原始: ";
    for (auto v : s) std::cout << v << " ";
    std::cout << "\n";

    // 前 N 个元素
    auto first3 = s.first(3);
    std::cout << "first(3): ";
    for (auto v : first3) std::cout << v << " ";
    std::cout << "\n";

    // 后 N 个元素
    auto last2 = s.last(2);
    std::cout << "last(2): ";
    for (auto v : last2) std::cout << v << " ";
    std::cout << "\n";

    // 子范围
    auto sub = s.subspan(1, 3);
    std::cout << "subspan(1,3): ";
    for (auto v : sub) std::cout << v << " ";
    std::cout << "\n\n";
}

// ============================================================
// 5. 与不同容器配合
// ============================================================

void different_sources() {
    std::cout << "【5. 不同数据源】\n";

    // 从 C 数组
    int arr[] = {1, 2, 3, 4, 5};
    print_span(arr, "C数组");

    // 从 std::array
    std::array<int, 3> std_arr = {10, 20, 30};
    print_span(std_arr, "std::array");

    // 从 vector
    std::vector<int> vec = {100, 200, 300};
    print_span(vec, "vector");

    // 从指针+长度
    int* ptr = arr;
    std::span<const int> s(ptr, 3);
    print_span(s, "指针+长度");
    std::cout << "\n";
}

// ============================================================
// 6. 实际应用
// ============================================================

// 安全的子数组操作
std::span<int> get_row(std::span<int> matrix, size_t row, size_t cols) {
    return matrix.subspan(row * cols, cols);
}

// 计算平均值 - 不关心数据来源
double average(std::span<const double> data) {
    if (data.empty()) return 0.0;
    double sum = 0;
    for (auto v : data) sum += v;
    return sum / data.size();
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 std::span 示例 ===\n\n";

    // 1. 基本用法
    std::cout << "【1. 基本用法】\n";
    std::vector<int> vec = {1, 2, 3, 4, 5};
    print_span(vec, "vector");

    int arr[] = {10, 20, 30};
    print_span(arr, "数组");
    std::cout << "\n";

    // 2. 修改数据
    std::cout << "【2. 通过 span 修改数据】\n";
    std::cout << "修改前: ";
    for (auto v : vec) std::cout << v << " ";
    std::cout << "\n";
    double_all(vec);
    std::cout << "修改后: ";
    for (auto v : vec) std::cout << v << " ";
    std::cout << "\n\n";

    // 3. 静态 extent
    std::cout << "【3. 静态 extent】\n";
    std::array<int, 5> fixed_arr = {1, 2, 3, 4, 5};
    process_fixed(fixed_arr);
    std::cout << "\n";

    // 4. 子 span
    std::cout << "【4. 子 span 操作】\n";
    std::vector<int> data = {10, 20, 30, 40, 50};
    subspan_demo(data);

    // 5. 不同数据源
    different_sources();

    // 6. span 属性
    std::cout << "【6. span 属性】\n";
    std::span<const int> s(vec);
    std::cout << "size: " << s.size() << "\n";
    std::cout << "empty: " << std::boolalpha << s.empty() << "\n";
    std::cout << "front: " << s.front() << "\n";
    std::cout << "back: " << s.back() << "\n";
    std::cout << "data: " << (void*)s.data() << "\n\n";

    // 7. 实际应用
    std::cout << "【7. 实际应用】\n";
    double values[] = {1.5, 2.5, 3.5, 4.5};
    std::cout << "平均值: " << average(values) << "\n";

    std::vector<double> more_values = {10.0, 20.0, 30.0};
    std::cout << "平均值: " << average(more_values) << "\n";

    // 8. span vs 其他方式
    std::cout << "\n【8. span vs 指针+长度】\n";
    std::cout << "span 优势:\n";
    std::cout << "  - 类型安全（不混淆指针和长度）\n";
    std::cout << "  - 丰富的子 span 操作\n";
    std::cout << "  - 与 STL 兼容\n";
    std::cout << "  - 支持静态和动态大小\n";

    std::cout << "\n=== std::span 示例完成 ===\n";
    return 0;
}
