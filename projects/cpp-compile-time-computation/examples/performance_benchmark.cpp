// performance_benchmark.cpp - 编译期 vs 运行时性能对比
//
// 本文件对比编译期计算和运行时计算的性能差异，包括：
//   1. 编译期 vs 运行时计算时间
//   2. 编译期查找表 vs 运行时计算
//   3. 编译期排序 vs 运行时排序
//   4. 编译期哈希 vs 运行时哈希
//
// 编译命令：
//   g++ -std=c++20 -O2 -I include examples/performance_benchmark.cpp -o performance_benchmark

#include <iostream>
#include <chrono>
#include <iomanip>
#include <algorithm>
#include <numeric>
#include <vector>
#include <array>
#include <cstring>

#include "compile_time/math.hpp"
#include "compile_time/lookup.hpp"
#include "compile_time/hash.hpp"

using namespace compile_time;

// ============================================================================
// 辅助函数：测量执行时间
// ============================================================================

template<typename Func>
double measure_time(Func func, int iterations = 1000000) {
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        func();
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
    return static_cast<double>(duration.count()) / iterations;
}

// ============================================================================
// 第一部分：编译期 vs 运行时数学计算
// ============================================================================

// 编译期计算
constexpr double compile_time_sqrt = math::sqrt(2.0);
constexpr double compile_time_sin = math::sin(1.0);
constexpr double compile_time_exp = math::exp(1.0);

// 运行时计算
double runtime_sqrt(double x) {
    double guess = x / 2.0;
    for (int i = 0; i < 100; ++i) {
        guess = (guess + x / guess) / 2.0;
    }
    return guess;
}

double runtime_sin(double x) {
    while (x > math::pi) x -= 2 * math::pi;
    while (x < -math::pi) x += 2 * math::pi;

    double result = 0;
    double term = x;
    for (int n = 1; n <= 20; ++n) {
        result += term;
        term *= -x * x / ((2 * n) * (2 * n + 1));
    }
    return result;
}

double runtime_exp(double x) {
    double result = 1.0;
    double term = 1.0;
    for (int n = 1; n < 30; ++n) {
        term *= x / n;
        result += term;
    }
    return result;
}

// ============================================================================
// 第二部分：编译期查找表 vs 运行时计算
// ============================================================================

// 编译期查找表
constexpr auto compile_time_sine_table = lookup::make_sine_table();

// 运行时查找表
double runtime_sine_table[360];
void init_runtime_sine_table() {
    for (int i = 0; i < 360; ++i) {
        runtime_sine_table[i] = math::sin(i * math::pi / 180.0);
    }
}

// ============================================================================
// 第三部分：编译期排序 vs 运行时排序
// ============================================================================

// 编译期排序
constexpr auto compile_time_sorted = []() {
    compile_time::compile_time_array<int, 100> arr;
    for (int i = 0; i < 100; ++i) {
        arr[i] = (i * 7 + 13) % 100;
    }
    return arr.sorted();
}();

// 运行时排序
std::array<int, 100> runtime_sorted;
void init_runtime_sorted() {
    for (int i = 0; i < 100; ++i) {
        runtime_sorted[i] = (i * 7 + 13) % 100;
    }
    std::sort(runtime_sorted.begin(), runtime_sorted.end());
}

// ============================================================================
// 第四部分：编译期哈希 vs 运行时哈希
// ============================================================================

// 编译期哈希
constexpr std::size_t compile_time_hash = hash::fnv1a("hello world");

// 运行时哈希
std::size_t runtime_hash(const char* str) {
    std::size_t hash = 14695981039346656037ULL;
    while (*str) {
        hash ^= static_cast<std::size_t>(*str++);
        hash *= 1099511628211ULL;
    }
    return hash;
}

// ============================================================================
// 第五部分：性能测试函数
// ============================================================================

void benchmark_math() {
    std::cout << "=== 数学计算性能对比 ===" << std::endl;
    std::cout << std::fixed << std::setprecision(2);

    // 编译期版本（运行时直接使用结果）
    double ct_time = measure_time([]() {
        volatile double result = compile_time_sqrt;
        (void)result;
    });

    // 运行时版本
    double rt_time = measure_time([]() {
        volatile double result = runtime_sqrt(2.0);
        (void)result;
    });

    std::cout << "  sqrt(2.0):" << std::endl;
    std::cout << "    编译期: " << ct_time << " ns (使用编译期结果)" << std::endl;
    std::cout << "    运行时: " << rt_time << " ns" << std::endl;
    std::cout << "    加速比: " << (rt_time / ct_time) << "x" << std::endl;
    std::cout << std::endl;

    // sin
    ct_time = measure_time([]() {
        volatile double result = compile_time_sin;
        (void)result;
    });

    rt_time = measure_time([]() {
        volatile double result = runtime_sin(1.0);
        (void)result;
    });

    std::cout << "  sin(1.0):" << std::endl;
    std::cout << "    编译期: " << ct_time << " ns" << std::endl;
    std::cout << "    运行时: " << rt_time << " ns" << std::endl;
    std::cout << "    加速比: " << (rt_time / ct_time) << "x" << std::endl;
    std::cout << std::endl;

    // exp
    ct_time = measure_time([]() {
        volatile double result = compile_time_exp;
        (void)result;
    });

    rt_time = measure_time([]() {
        volatile double result = runtime_exp(1.0);
        (void)result;
    });

    std::cout << "  exp(1.0):" << std::endl;
    std::cout << "    编译期: " << ct_time << " ns" << std::endl;
    std::cout << "    运行时: " << rt_time << " ns" << std::endl;
    std::cout << "    加速比: " << (rt_time / ct_time) << "x" << std::endl;
    std::cout << std::endl;
}

void benchmark_lookup_table() {
    std::cout << "=== 查找表性能对比 ===" << std::endl;
    std::cout << std::fixed << std::setprecision(2);

    init_runtime_sine_table();

    // 编译期查找表
    double ct_time = measure_time([]() {
        volatile double result = compile_time_sine_table[45];
        (void)result;
    });

    // 运行时查找表
    double rt_time = measure_time([]() {
        volatile double result = runtime_sine_table[45];
        (void)result;
    });

    // 运行时计算
    double calc_time = measure_time([]() {
        volatile double result = math::sin(45.0 * math::pi / 180.0);
        (void)result;
    });

    std::cout << "  sin(45°):" << std::endl;
    std::cout << "    编译期查找表: " << ct_time << " ns" << std::endl;
    std::cout << "    运行时查找表: " << rt_time << " ns" << std::endl;
    std::cout << "    运行时计算:   " << calc_time << " ns" << std::endl;
    std::cout << std::endl;
}

void benchmark_sort() {
    std::cout << "=== 排序性能对比 ===" << std::endl;
    std::cout << std::fixed << std::setprecision(2);

    init_runtime_sorted();

    // 编译期排序（直接使用结果）
    double ct_time = measure_time([]() {
        volatile int result = compile_time_sorted[50];
        (void)result;
    });

    // 运行时排序
    double rt_time = measure_time([]() {
        std::array<int, 100> arr;
        for (int i = 0; i < 100; ++i) {
            arr[i] = (i * 7 + 13) % 100;
        }
        std::sort(arr.begin(), arr.end());
        volatile int result = arr[50];
        (void)result;
    });

    std::cout << "  排序 100 个元素:" << std::endl;
    std::cout << "    编译期排序: " << ct_time << " ns (直接使用结果)" << std::endl;
    std::cout << "    运行时排序: " << rt_time << " ns" << std::endl;
    std::cout << "    加速比: " << (rt_time / ct_time) << "x" << std::endl;
    std::cout << std::endl;
}

void benchmark_hash() {
    std::cout << "=== 哈希性能对比 ===" << std::endl;
    std::cout << std::fixed << std::setprecision(2);

    const char* str = "hello world";

    // 编译期哈希（直接使用结果）
    double ct_time = measure_time([]() {
        volatile std::size_t result = compile_time_hash;
        (void)result;
    });

    // 运行时哈希
    double rt_time = measure_time([str]() {
        volatile std::size_t result = runtime_hash(str);
        (void)result;
    });

    std::cout << "  fnv1a(\"hello world\"):" << std::endl;
    std::cout << "    编译期哈希: " << ct_time << " ns (直接使用结果)" << std::endl;
    std::cout << "    运行时哈希: " << rt_time << " ns" << std::endl;
    std::cout << "    加速比: " << (rt_time / ct_time) << "x" << std::endl;
    std::cout << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期 vs 运行时性能对比 ===" << std::endl;
    std::cout << std::endl;

    benchmark_math();
    benchmark_lookup_table();
    benchmark_sort();
    benchmark_hash();

    std::cout << "=== 总结 ===" << std::endl;
    std::cout << "编译期计算的优势:" << std::endl;
    std::cout << "  1. 运行时零开销（直接使用编译期结果）" << std::endl;
    std::cout << "  2. 类型安全（编译期错误检查）" << std::endl;
    std::cout << "  3. 代码可读性（使用普通函数语法）" << std::endl;
    std::cout << std::endl;
    std::cout << "编译期计算的代价:" << std::endl;
    std::cout << "  1. 编译时间增加" << std::endl;
    std::cout << "  2. 调试困难" << std::endl;
    std::cout << "  3. 限制较多（不能使用堆内存、虚函数等）" << std::endl;
    std::cout << std::endl;
    std::cout << "最佳实践:" << std::endl;
    std::cout << "  1. 只在确实需要时使用编译期计算" << std::endl;
    std::cout << "  2. 优先考虑可读性和维护性" << std::endl;
    std::cout << "  3. 测量实际性能，根据数据做决策" << std::endl;

    return 0;
}
