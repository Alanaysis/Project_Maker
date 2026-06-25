/**
 * branch_prediction.cpp - 分支预测优化技巧
 *
 * 核心思想：CPU 流水线遇到条件分支时需要预测执行方向。
 * 预测正确时流水线顺畅；预测错误时需要清空流水线，代价高昂（~15-20 周期）。
 * 通过提示编译器哪个分支更可能执行，可以帮助生成更高效的代码。
 *
 * 编译：g++ -std=c++17 -O2 -o branch_prediction branch_prediction.cpp
 */

#include <iostream>
#include <chrono>
#include <vector>
#include <algorithm>
#include <random>
#include <numeric>
#include <iomanip>
#include <cstring>

// ============================================================================
// 1. [[likely]] / [[unlikely]] 属性 (C++20)
// ============================================================================
// 从 C++20 开始，可以使用标准属性 [[likely]] 和 [[unlikely]]
// 来提示编译器哪个分支更可能被执行。
// 编译器会据此调整代码布局，将 likely 分支放在"直线"路径上。

// 示例：带分支预测提示的绝对值函数
int abs_with_hint(int x) {
    if (x >= 0) [[likely]] {
        // 大多数情况下 x 是非负的（更可能的路径）
        return x;
    } else [[unlikely]] {
        // 负数情况较少见（不太可能的路径）
        return -x;
    }
}

// 示例：带分支预测提示的数组访问
int safe_access(const int* arr, size_t size, size_t index) {
    if (index < size) [[likely]] {
        // 正常访问（大多数情况）
        return arr[index];
    } else [[unlikely]] {
        // 越界保护（异常情况）
        return -1;
    }
}

// 示例：带分支预测提示的错误处理模式
struct Result {
    int value;
    bool success;
};

Result process_data(int input) {
    if (input >= 0 && input <= 1000) [[likely]] {
        // 有效输入（常见情况）
        return {input * 2, true};
    } else [[unlikely]] {
        // 无效输入（罕见情况）
        return {0, false};
    }
}

// ============================================================================
// 2. __builtin_expect —— GCC/Clang 的分支预测内建函数
// ============================================================================
// 这是 C++20 之前常用的分支预测提示方式。
// __builtin_expect(expr, value) 告诉编译器 expr 大概率等于 value。

// 使用 __builtin_expect 的条件判断
int process_with_builtin_expect(int x) {
    // __builtin_expect(条件, 期望值)
    // 告诉编译器：条件表达式的结果大概率是 1 (true)
    if (__builtin_expect(x > 0, 1)) {
        return x * 2;    // 热路径
    } else {
        return 0;        // 冷路径
    }
}

// 常见的 LIKELY/UNLIKELY 宏定义（跨编译器兼容）
#if defined(__GNUC__) || defined(__clang__)
    #define LIKELY(x)   __builtin_expect(!!(x), 1)
    #define UNLIKELY(x) __builtin_expect(!!(x), 0)
#elif defined(_MSC_VER)
    // MSVC 没有直接的等价物，但可以通过 __assume 提示
    #define LIKELY(x)   (x)
    #define UNLIKELY(x) (x)
#else
    #define LIKELY(x)   (x)
    #define UNLIKELY(x) (x)
#endif

// 使用宏的版本 —— 更简洁
int process_with_macros(int x) {
    if (LIKELY(x > 0)) {
        return x * 2;
    } else {
        return 0;
    }
}

// ============================================================================
// 3. 分支预测对排序算法的影响
// ============================================================================
// 经典演示：对"有序"和"无序"数组排序的速度差异。
// 当数据有序时，分支预测器能准确预测比较结果，排序更快。

// 带分支预测提示的比较函数
bool compare_with_hint(int a, int b) {
    if (a < b) [[likely]] {
        return true;   // 升序排列中，a < b 是常见情况
    } else [[unlikely]] {
        return false;
    }
}

// ============================================================================
// 4. 无分支编程 —— 消除分支来避免预测失败
// ============================================================================
// 有时候最好的优化是完全消除分支。

// 有分支版本
int max_with_branch(int a, int b) {
    if (a > b) {
        return a;
    } else {
        return b;
    }
}

// 无分支版本 —— 使用三元运算符（编译器可能生成条件移动指令 cmov）
int max_branchless(int a, int b) {
    return (a > b) ? a : b;
}

// 无分支绝对值（对于 int）
int abs_branchless(int x) {
    // 利用算术右移的特性：
    // 负数右移得到全 1（-1），非负数右移得到全 0
    int mask = x >> (sizeof(int) * 8 - 1);
    return (x + mask) ^ mask;
}

// 无分支 clamp
int clamp_branchless(int value, int low, int high) {
    // 先限制下界，再限制上界
    value = (value < low) ? low : value;
    value = (value > high) ? high : value;
    return value;
}

// 无分支条件求和
int conditional_sum_branchless(const int* arr, size_t n) {
    int sum = 0;
    for (size_t i = 0; i < n; ++i) {
        // 使用算术代替分支：将条件转换为 0 或 1 的乘数
        int mask = -(arr[i] > 0);  // arr[i] > 0 时 mask = -1 (全1)，否则 = 0
        sum += arr[i] & mask;       // 等价于 if (arr[i] > 0) sum += arr[i];
    }
    return sum;
}

// 有分支版本的条件求和
int conditional_sum_branched(const int* arr, size_t n) {
    int sum = 0;
    for (size_t i = 0; i < n; ++i) {
        if (arr[i] > 0) {
            sum += arr[i];
        }
    }
    return sum;
}

// ============================================================================
// 5. Profile-Guided Optimization (PGO) 提示
// ============================================================================
// PGO 通过实际运行数据来指导编译器优化分支布局。
// 编译步骤：
//   1. g++ -O2 -fprofile-generate -o prog_gen prog.cpp
//   2. ./prog_gen  (运行程序收集 profile 数据)
//   3. g++ -O2 -fprofile-use -o prog_opt prog.cpp

// 模拟 PGO 的分支频率标注
#if defined(__GNUC__) || defined(__clang__)
    // GCC 属性标注函数的"冷热"性质
    __attribute__((cold))  // 标注为冷函数（很少被调用）
    void error_handler(const char* msg) {
        std::cerr << "错误: " << msg << std::endl;
    }

    __attribute__((hot))   // 标注为热函数（频繁被调用）
    int hot_function(int x) {
        return x * x + 2 * x + 1;
    }
#else
    void error_handler(const char* msg) {
        std::cerr << "错误: " << msg << std::endl;
    }

    int hot_function(int x) {
        return x * x + 2 * x + 1;
    }
#endif

// ============================================================================
// 6. 查找表替代分支 —— 用空间换时间
// ============================================================================
// 当分支很多（如 switch-case）时，查找表可能比分支预测更高效。

// 用 switch-case 实现（分支多时预测困难）
int grade_switch(int score) {
    if (score >= 90) return 4;      // A
    else if (score >= 80) return 3; // B
    else if (score >= 70) return 2; // C
    else if (score >= 60) return 1; // D
    else return 0;                  // F
}

// 用查找表实现（无分支）
int grade_table(int score) {
    // 构建查找表：score/10 映射到等级
    static const int table[] = {
        0, 0, 0, 0, 0, 0,  // 0-59: F
        1,                  // 60-69: D
        2,                  // 70-79: C
        3,                  // 80-89: B
        4                   // 90-100: A
    };
    int index = score / 10;
    // 边界检查
    if (index < 0) index = 0;
    if (index > 10) index = 10;
    return table[index];
}

// ============================================================================
// 辅助函数
// ============================================================================

// 防止编译器优化掉计算结果
template <typename T>
void do_not_optimize(T const& val) {
    #if defined(__GNUC__) || defined(__clang__)
        asm volatile("" : : "r,m"(val) : "memory");
    #else
        volatile T sink = val;
        (void)sink;
    #endif
}

// 生成指定模式的测试数据
std::vector<int> generate_sorted_data(size_t n) {
    std::vector<int> data(n);
    std::iota(data.begin(), data.end(), 0);  // 0, 1, 2, ...
    return data;
}

std::vector<int> generate_random_data(size_t n) {
    std::vector<int> data(n);
    std::mt19937 rng(42);  // 固定种子，确保可重现
    std::uniform_int_distribution<int> dist(0, 100000);
    for (auto& x : data) {
        x = dist(rng);
    }
    return data;
}

// ============================================================================
// 主函数 —— 展示分支预测优化的各种技巧
// ============================================================================

int main() {
    std::cout << "========================================\n";
    std::cout << "  分支预测优化技巧演示 (C++17/20)\n";
    std::cout << "========================================\n\n";

    // --- 1. [[likely]] / [[unlikely]] 属性 ---
    std::cout << "【1. [[likely]] / [[unlikely]] 属性 (C++20)】\n";
    std::cout << "  abs_with_hint(42)  = " << abs_with_hint(42) << "\n";
    std::cout << "  abs_with_hint(-7)  = " << abs_with_hint(-7) << "\n";

    int arr[] = {10, 20, 30, 40, 50};
    std::cout << "  safe_access(arr, 5, 3) = " << safe_access(arr, 5, 3) << "\n";
    std::cout << "  safe_access(arr, 5, 10) = " << safe_access(arr, 5, 10) << " (越界)\n";

    auto [val, ok] = process_data(42);
    std::cout << "  process_data(42)  = {" << val << ", " << ok << "}\n";
    auto [val2, ok2] = process_data(-1);
    std::cout << "  process_data(-1)  = {" << val2 << ", " << ok2 << "}\n\n";

    // --- 2. __builtin_expect 和宏 ---
    std::cout << "【2. __builtin_expect 和 LIKELY/UNLIKELY 宏】\n";
    std::cout << "  process_with_builtin_expect(10) = " << process_with_builtin_expect(10) << "\n";
    std::cout << "  process_with_macros(-5) = " << process_with_macros(-5) << "\n";
    std::cout << "  宏版本在 GCC/Clang 下展开为 __builtin_expect，其他编译器下无操作\n\n";

    // --- 3. 排序时的分支预测效果 ---
    std::cout << "【3. 分支预测对排序的影响（经典演示）】\n";

    const size_t SORT_SIZE = 1000000;
    auto sorted_data = generate_sorted_data(SORT_SIZE);
    auto random_data = generate_random_data(SORT_SIZE);

    // 对有序数据排序
    auto sorted_copy = sorted_data;
    auto start = std::chrono::high_resolution_clock::now();
    std::sort(sorted_copy.begin(), sorted_copy.end());
    auto end = std::chrono::high_resolution_clock::now();
    auto sorted_ns = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

    // 对无序数据排序
    auto random_copy = random_data;
    start = std::chrono::high_resolution_clock::now();
    std::sort(random_copy.begin(), random_copy.end());
    end = std::chrono::high_resolution_clock::now();
    auto random_ns = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

    std::cout << "  排序 " << SORT_SIZE << " 个元素:\n";
    std::cout << "    已排序数据: " << sorted_ns << " ms\n";
    std::cout << "    随机数据:   " << random_ns << " ms\n";
    std::cout << "    比率: " << std::setprecision(2)
              << static_cast<double>(random_ns) / sorted_ns << "x\n";
    std::cout << "  （已排序数据的比较结果更容易被分支预测器准确预测）\n\n";

    // --- 4. 有分支 vs 无分支性能对比 ---
    std::cout << "【4. 有分支 vs 无分支性能对比】\n";

    const size_t N = 10000000;
    auto test_data = generate_random_data(N);
    volatile int sink = 0;

    // 测试有分支的条件求和
    start = std::chrono::high_resolution_clock::now();
    int sum_branched = conditional_sum_branched(test_data.data(), N);
    end = std::chrono::high_resolution_clock::now();
    auto branched_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    sink = sum_branched;

    // 测试无分支的条件求和
    start = std::chrono::high_resolution_clock::now();
    int sum_branchless = conditional_sum_branchless(test_data.data(), N);
    end = std::chrono::high_resolution_clock::now();
    auto branchless_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    sink = sum_branchless;

    std::cout << "  条件求和（对正数求和，" << N << " 个元素）:\n";
    std::cout << "    有分支版本:   " << branched_ns / 1000.0 << " μs\n";
    std::cout << "    无分支版本:   " << branchless_ns / 1000.0 << " μs\n";
    std::cout << "    结果: sum_branched=" << sum_branched
              << ", sum_branchless=" << sum_branchless << "\n\n";

    // 测试 max 函数
    {
        const int MAX_ITER = 10000000;
        auto data = generate_random_data(MAX_ITER);
        volatile int max_result = 0;

        start = std::chrono::high_resolution_clock::now();
        int current_max = 0;
        for (size_t i = 0; i < data.size(); ++i) {
            current_max = max_with_branch(current_max, data[i]);
        }
        max_result = current_max;
        end = std::chrono::high_resolution_clock::now();
        auto max_branched_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();

        start = std::chrono::high_resolution_clock::now();
        current_max = 0;
        for (size_t i = 0; i < data.size(); ++i) {
            current_max = max_branchless(current_max, data[i]);
        }
        max_result = current_max;
        end = std::chrono::high_resolution_clock::now();
        auto max_branchless_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();

        std::cout << "  求最大值（" << MAX_ITER << " 个元素）:\n";
        std::cout << "    有分支 max(): " << max_branched_ns / 1000.0 << " μs\n";
        std::cout << "    无分支 max(): " << max_branchless_ns / 1000.0 << " μs\n\n";
    }

    // --- 5. 查找表替代分支 ---
    std::cout << "【5. 查找表替代多路分支】\n";

    const int GRADE_ITER = 10000000;
    auto scores = generate_random_data(GRADE_ITER);
    for (auto& s : scores) s = s % 101;  // 映射到 0-100

    // switch-case 版本
    start = std::chrono::high_resolution_clock::now();
    int grade_sum1 = 0;
    for (size_t i = 0; i < scores.size(); ++i) {
        grade_sum1 += grade_switch(scores[i]);
    }
    end = std::chrono::high_resolution_clock::now();
    auto switch_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    sink = grade_sum1;

    // 查找表版本
    start = std::chrono::high_resolution_clock::now();
    int grade_sum2 = 0;
    for (size_t i = 0; i < scores.size(); ++i) {
        grade_sum2 += grade_table(scores[i]);
    }
    end = std::chrono::high_resolution_clock::now();
    auto table_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    sink = grade_sum2;

    std::cout << "  成绩等级转换（" << GRADE_ITER << " 次）:\n";
    std::cout << "    if-else 分支: " << switch_ns / 1000.0 << " μs\n";
    std::cout << "    查找表:       " << table_ns / 1000.0 << " μs\n";
    std::cout << "    结果一致: " << (grade_sum1 == grade_sum2 ? "是" : "否") << "\n\n";

    // --- 6. PGO 提示 ---
    std::cout << "【6. Profile-Guided Optimization (PGO)】\n";
    std::cout << "  PGO 编译步骤:\n";
    std::cout << "    第 1 步: g++ -O2 -fprofile-generate -o prog prog.cpp\n";
    std::cout << "    第 2 步: ./prog  (运行收集 profile 数据)\n";
    std::cout << "    第 3 步: g++ -O2 -fprofile-use -o prog prog.cpp\n";
    std::cout << "  PGO 可以让编译器根据实际运行数据优化分支布局\n";
    std::cout << "  典型收益: 5%-15% 的性能提升\n\n";

    std::cout << "  __attribute__((hot)) 和 __attribute__((cold)) 标注:\n";
    std::cout << "    hot 函数: 编译器会积极优化，可能内联\n";
    std::cout << "    cold 函数: 编译器不优先优化，减少代码膨胀\n";
    std::cout << "    hot_function(5) = " << hot_function(5) << "\n\n";

    // --- 总结 ---
    std::cout << "========================================\n";
    std::cout << "  总结：分支预测优化的最佳实践\n";
    std::cout << "========================================\n";
    std::cout << "  1. 使用 [[likely]]/[[unlikely]] 提示常见/罕见分支\n";
    std::cout << "  2. 使用 __builtin_expect 或 LIKELY/UNLIKELY 宏\n";
    std::cout << "  3. 将错误处理/边界检查放在 [[unlikely]] 分支\n";
    std::cout << "  4. 考虑无分支编程来完全消除预测失败\n";
    std::cout << "  5. 用查找表替代复杂的多路分支\n";
    std::cout << "  6. 使用 PGO 让编译器根据实际数据优化\n";
    std::cout << "  7. 将热函数标记为 __attribute__((hot))\n";
    std::cout << "\n  记住：分支预测失败的代价约 15-20 个 CPU 周期！\n";

    (void)sink;  // 消除未使用警告
    return 0;
}
