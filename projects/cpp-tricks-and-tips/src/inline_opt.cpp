/**
 * inline_opt.cpp - 内联优化技巧
 *
 * 核心思想：内联（inline）将函数体直接展开到调用处，消除函数调用开销。
 * 现代编译器会自动决定是否内联，但程序员可以通过关键字和属性来引导编译器。
 *
 * 编译：g++ -std=c++17 -O2 -o inline_opt inline_opt.cpp
 *       g++ -std=c++17 -O2 -flto -o inline_opt inline_opt.cpp  (启用 LTO)
 */

#include <iostream>
#include <chrono>
#include <cmath>
#include <array>
#include <functional>
#include <numeric>
#include <iomanip>

// ============================================================================
// 1. inline 函数 —— 基本内联提示
// ============================================================================
// inline 关键字是给编译器的建议，不是强制命令。
// 现代编译器（-O2 及以上）会自行判断是否内联，可能忽略 inline 提示。
// inline 的另一个重要作用：允许多个翻译单元中定义相同的函数（避免 ODR 违规）。

// 简单的内联函数 —— 适合内联（函数体小，调用频繁）
constexpr inline int square(int x) {
    return x * x;
}

// 内联函数 —— 简单的数学运算
inline double fast_inverse_sqrt(double x) {
    // 卡马克快速逆平方根的简化版（仅示意，实际用于 float）
    return 1.0 / std::sqrt(x);
}

// 内联的 getter/setter —— 典型的内联应用场景
class Point3D {
    double x_, y_, z_;
public:
    constexpr Point3D(double x = 0, double y = 0, double z = 0)
        : x_(x), y_(y), z_(z) {}

    // 这些简单的访问器非常适合内联
    inline double x() const { return x_; }
    inline double y() const { return y_; }
    inline double z() const { return z_; }

    inline void set_x(double v) { x_ = v; }
    inline void set_y(double v) { y_ = v; }
    inline void set_z(double v) { z_ = v; }

    // 内联的距离计算
    inline double distance_to(const Point3D& other) const {
        double dx = x_ - other.x_;
        double dy = y_ - other.y_;
        double dz = z_ - other.z_;
        return std::sqrt(dx * dx + dy * dy + dz * dz);
    }
};

// ============================================================================
// 2. 编译器特定的强制内联属性
// ============================================================================
// 当你确定内联能带来性能提升时，可以强制编译器内联。
// 注意：强制内联可能导致代码膨胀，反而降低性能（指令缓存不友好）。

// GCC/Clang 的强制内联属性
#if defined(__GNUC__) || defined(__clang__)
    #define FORCE_INLINE __attribute__((always_inline)) inline
#elif defined(_MSC_VER)
    #define FORCE_INLINE __forceinline
#else
    #define FORCE_INLINE inline
#endif

// 强制内联的小函数 —— 热路径上的微小操作
FORCE_INLINE uint32_t fast_mod_pow2(uint32_t value, uint32_t power_of_2) {
    // 用位运算代替取模（仅适用于 2 的幂次）
    return value & (power_of_2 - 1);
}

// 强制内联的条件选择 —— 避免分支
FORCE_INLINE int branchless_max(int a, int b) {
    // 无分支最大值：利用条件移动指令
    return (a > b) ? a : b;
}

// 强制内联的饱和加法（防止溢出）
FORCE_INLINE uint8_t saturating_add(uint8_t a, uint8_t b) {
    uint16_t sum = static_cast<uint16_t>(a) + static_cast<uint16_t>(b);
    return (sum > 255) ? 255 : static_cast<uint8_t>(sum);
}

// ============================================================================
// 3. 不适合内联的情况 —— 展示内联的负面影响
// ============================================================================

// 大函数不应内联 —— 会导致代码膨胀，占用指令缓存
// 使用 noinline 属性明确告诉编译器不要内联
#if defined(__GNUC__) || defined(__clang__)
    #define NO_INLINE __attribute__((noinline))
#elif defined(_MSC_VER)
    #define NO_INLINE __declspec(noinline)
#else
    #define NO_INLINE
#endif

// 复杂的排序算法 —— 函数体大，内联会导致严重的代码膨胀
NO_INLINE void insertion_sort(int* arr, size_t n) {
    for (size_t i = 1; i < n; ++i) {
        int key = arr[i];
        size_t j = i;
        while (j > 0 && arr[j - 1] > key) {
            arr[j] = arr[j - 1];
            --j;
        }
        arr[j] = key;
    }
}

// 递归函数通常不适合内联（编译器一般会自动拒绝）
NO_INLINE long long recursive_fib(int n) {
    if (n <= 1) return n;
    return recursive_fib(n - 1) + recursive_fib(n - 2);
}

// ============================================================================
// 4. 内联与模板 —— 模板天然适合内联
// ============================================================================
// 模板函数在实例化时会生成专门的代码，编译器更容易做出内联决策。

// 泛型 clamp 模板 —— 编译器可以针对每种类型优化
template <typename T>
FORCE_INLINE T clamp(T value, T low, T high) {
    return (value < low) ? low : ((value > high) ? high : value);
}

// 泛型交换模板
template <typename T>
FORCE_INLINE void fast_swap(T& a, T& b) noexcept {
    T temp = std::move(a);
    a = std::move(b);
    b = std::move(temp);
}

// 多态内联 —— 通过 CRTP 实现编译期多态（避免虚函数调用开销）
// CRTP: Curiously Recurring Template Pattern（奇异递归模板模式）
template <typename Derived>
class Shape {
public:
    // 静态多态：编译期确定调用哪个实现，可以内联
    FORCE_INLINE double area() const {
        return static_cast<const Derived*>(this)->compute_area();
    }

    FORCE_INLINE double perimeter() const {
        return static_cast<const Derived*>(this)->compute_perimeter();
    }
};

class Circle : public Shape<Circle> {
    double radius_;
public:
    constexpr Circle(double r) : radius_(r) {}

    double compute_area() const {
        return 3.14159265358979 * radius_ * radius_;
    }

    double compute_perimeter() const {
        return 2 * 3.14159265358979 * radius_;
    }
};

class Rectangle : public Shape<Rectangle> {
    double w_, h_;
public:
    constexpr Rectangle(double w, double h) : w_(w), h_(h) {}

    double compute_area() const {
        return w_ * h_;
    }

    double compute_perimeter() const {
        return 2 * (w_ + h_);
    }
};

// ============================================================================
// 5. 编译器内联决策的观察 —— 使用 volatile 防止优化
// ============================================================================

// 普通函数（编译器可能内联也可能不内联）
int normal_function(int x) {
    return x * x + 2 * x + 1;
}

// 明确不内联的函数
NO_INLINE int noinline_function(int x) {
    return x * x + 2 * x + 1;
}

// ============================================================================
// 辅助：微基准测试框架
// ============================================================================

// 防止编译器优化掉计算结果
template <typename T>
void do_not_optimize(T const& val) {
    // 使用 volatile 内联汇编阻止编译器优化
    #if defined(__GNUC__) || defined(__clang__)
        asm volatile("" : : "r,m"(val) : "memory");
    #else
        volatile T sink = val;
        (void)sink;
    #endif
}

// 测量函数执行时间
template <typename Func>
double measure_ns(Func&& func, int iterations = 1000000) {
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        func(i);
    }
    auto end = std::chrono::high_resolution_clock::now();
    return static_cast<double>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count()
    ) / iterations;
}

// ============================================================================
// 主函数 —— 展示内联优化的各种场景
// ============================================================================

int main() {
    std::cout << "========================================\n";
    std::cout << "  内联优化技巧演示 (C++17)\n";
    std::cout << "========================================\n\n";

    // --- 1. 基本 inline 函数 ---
    std::cout << "【1. inline 函数基本用法】\n";

    constexpr int n = 15;
    constexpr int sq = square(n);  // 编译期计算，运行时零开销
    std::cout << "  square(" << n << ") = " << sq << " [constexpr 编译期计算]\n";

    // 运行时调用 —— 编译器很可能内联展开
    int runtime_val = 42;
    int runtime_sq = square(runtime_val);  // 编译器可能内联
    std::cout << "  square(" << runtime_val << ") = " << runtime_sq << " [可能被内联]\n\n";

    // --- 2. Point3D 内联方法 ---
    std::cout << "【2. 类方法内联】\n";

    Point3D p1(1.0, 2.0, 3.0);
    Point3D p2(4.0, 5.0, 6.0);
    double dist = p1.distance_to(p2);
    std::cout << "  Point3D(1,2,3) 到 Point3D(4,5,6) 的距离 = "
              << std::setprecision(4) << dist << "\n";
    std::cout << "  getter/setter 方法适合内联，消除函数调用开销\n\n";

    // --- 3. 强制内联的效果 ---
    std::cout << "【3. 强制内联 (__attribute__((always_inline)))】\n";

    std::cout << "  fast_mod_pow2(17, 16) = " << fast_mod_pow2(17, 16) << "\n";
    std::cout << "  branchless_max(10, 20) = " << branchless_max(10, 20) << "\n";
    std::cout << "  saturating_add(200, 100) = " << static_cast<int>(saturating_add(200, 100)) << "\n";
    std::cout << "  高频调用的微小函数适合强制内联\n\n";

    // --- 4. 内联与非内联的性能对比 ---
    std::cout << "【4. 内联 vs 非内联性能对比】\n";

    const int ITERATIONS = 10000000;

    // 测试内联函数 (square)
    double inline_time = measure_ns([](int i) {
        int result = square(i);
        do_not_optimize(result);
    }, ITERATIONS);

    // 测试强制内联函数
    double force_inline_time = measure_ns([](int i) {
        int result = fast_mod_pow2(i, 1024);
        do_not_optimize(result);
    }, ITERATIONS);

    // 测试非内联函数
    double noinline_time = measure_ns([](int i) {
        int result = noinline_function(i);
        do_not_optimize(result);
    }, ITERATIONS);

    // 测试普通函数（可能内联也可能不内联）
    double normal_time = measure_ns([](int i) {
        int result = normal_function(i);
        do_not_optimize(result);
    }, ITERATIONS);

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "  " << ITERATIONS << " 次调用的平均耗时:\n";
    std::cout << "    inline square():         " << inline_time << " ns/次\n";
    std::cout << "    FORCE_INLINE fast_mod:    " << force_inline_time << " ns/次\n";
    std::cout << "    normal_function():        " << normal_time << " ns/次\n";
    std::cout << "    NO_INLINE function():     " << noinline_time << " ns/次\n\n";

    double speedup = noinline_time / inline_time;
    std::cout << "  内联 vs 非内联加速比: " << std::setprecision(1) << speedup << "x\n";
    std::cout << "  （注：现代编译器在 -O2 下差异可能很小，因为自动内联已经很智能）\n\n";

    // --- 5. CRTP 静态多态 vs 虚函数 ---
    std::cout << "【5. CRTP 静态多态（可内联）vs 虚函数（不可内联）】\n";

    // CRTP 版本 —— 编译期多态，可以内联
    Circle circle(5.0);
    Rectangle rect(4.0, 6.0);

    std::cout << "  CRTP Circle 面积: " << std::setprecision(4) << circle.area()
              << ", 周长: " << circle.perimeter() << "\n";
    std::cout << "  CRTP Rectangle 面积: " << rect.area()
              << ", 周长: " << rect.perimeter() << "\n";

    // 性能对比：CRTP vs 虚函数
    {
        const int N = 10000000;

        // CRTP 版本
        auto start = std::chrono::high_resolution_clock::now();
        double sum_crtp = 0;
        for (int i = 0; i < N; ++i) {
            if (i % 2 == 0) {
                sum_crtp += circle.area();
            } else {
                sum_crtp += rect.area();
            }
        }
        auto end = std::chrono::high_resolution_clock::now();
        auto crtp_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
        do_not_optimize(sum_crtp);

        std::cout << "  CRTP 静态多态 (" << N << " 次): " << crtp_ns / 1000.0 << " μs\n";
        std::cout << "  （每次调用 area() 都可以被内联展开）\n\n";
    }

    // --- 6. 何时不应该内联 ---
    std::cout << "【6. 何时不应该内联】\n";
    std::cout << "  以下情况应避免内联（使用 __attribute__((noinline))）：\n";
    std::cout << "  1. 函数体过大（> 100 行）—— 导致代码膨胀，指令缓存不友好\n";
    std::cout << "  2. 递归函数 —— 编译器无法内联递归\n";
    std::cout << "  3. 函数很少被调用 —— 内联收益微乎其微\n";
    std::cout << "  4. 通过函数指针调用 —— 编译期无法确定目标\n";
    std::cout << "  5. 虚函数的动态调用 —— 运行时才确定目标\n\n";

    // --- 总结 ---
    std::cout << "========================================\n";
    std::cout << "  总结：内联优化的最佳实践\n";
    std::cout << "========================================\n";
    std::cout << "  1. 简单的 getter/setter/数学运算 → 使用 inline\n";
    std::cout << "  2. 热路径上的微小函数 → 使用 __attribute__((always_inline))\n";
    std::cout << "  3. 大函数/递归函数 → 使用 __attribute__((noinline))\n";
    std::cout << "  4. 需要多态但又要内联 → 使用 CRTP 模式\n";
    std::cout << "  5. 启用 LTO (-flto) 让跨文件内联成为可能\n";
    std::cout << "  6. 信任编译器 —— -O2 下自动内联通常足够好\n";

    return 0;
}
