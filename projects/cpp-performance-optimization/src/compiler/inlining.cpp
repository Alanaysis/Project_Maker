/**
 * @file inlining.cpp
 * @brief 内联优化示例
 *
 * 本文件演示函数内联的效果：
 * 1. inline 关键字使用
 * 2. 函数调用开销测量
 * 3. 编译器内联决策
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <cmath>

class Timer
{
public:
    using Clock = std::chrono::high_resolution_clock;
    Timer() : start_(Clock::now()) {}
    void reset() { start_ = Clock::now(); }
    double elapsedMs() const {
        return std::chrono::duration_cast<std::chrono::nanoseconds>(
            Clock::now() - start_).count() / 1e6;
    }
private:
    Clock::time_point start_;
};

// 普通函数（可能不内联）
int squareNormal(int x)
{
    return x * x;
}

// 内联函数（建议编译器内联）
inline int squareInline(int x)
{
    return x * x;
}

// 强制内联（GCC/Clang）
__attribute__((always_inline))
inline int squareForceInline(int x)
{
    return x * x;
}

// 禁止内联
__attribute__((noinline))
int squareNoInline(int x)
{
    return x * x;
}

/**
 * @brief 示例1: 内联 vs 非内联性能对比
 */
void demonstrateInlining()
{
    std::cout << "=== 示例1: 内联 vs 非内联性能对比 ===\n\n";

    const size_t N = 100000000;
    volatile int result = 0;

    // 普通函数
    Timer timer;
    for (size_t i = 0; i < N; ++i) {
        result = squareNormal(static_cast<int>(i));
    }
    double normal_time = timer.elapsedMs();

    // 内联函数
    timer.reset();
    for (size_t i = 0; i < N; ++i) {
        result = squareInline(static_cast<int>(i));
    }
    double inline_time = timer.elapsedMs();

    // 强制内联
    timer.reset();
    for (size_t i = 0; i < N; ++i) {
        result = squareForceInline(static_cast<int>(i));
    }
    double force_inline_time = timer.elapsedMs();

    // 禁止内联
    timer.reset();
    for (size_t i = 0; i < N; ++i) {
        result = squareNoInline(static_cast<int>(i));
    }
    double noinline_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "调用次数: " << N << "\n";
    std::cout << "普通函数:     " << normal_time << " ms\n";
    std::cout << "inline 函数:  " << inline_time << " ms\n";
    std::cout << "强制内联:     " << force_inline_time << " ms\n";
    std::cout << "禁止内联:     " << noinline_time << " ms\n";
    (void)result;
}

/**
 * @brief 示例2: 复杂函数内联
 */
namespace ComplexExample {

struct Point {
    double x, y, z;
};

// 简单访问器（适合内联）
inline double getX(const Point& p) { return p.x; }
inline double getY(const Point& p) { return p.y; }
inline double getZ(const Point& p) { return p.z; }

// 简单计算（适合内联）
inline double dotProduct(const Point& a, const Point& b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

// 复杂计算（可能不适合内联）
__attribute__((noinline))
double complexCalculation(const Point& a, const Point& b, const Point& c)
{
    double d1 = dotProduct(a, b);
    double d2 = dotProduct(b, c);
    double d3 = dotProduct(a, c);
    return std::sqrt(d1 * d1 + d2 * d2 + d3 * d3);
}

} // namespace ComplexExample

void demonstrateComplexInlining()
{
    std::cout << "\n=== 示例2: 复杂函数内联 ===\n\n";

    const size_t N = 10000000;
    ComplexExample::Point a{1.0, 2.0, 3.0};
    ComplexExample::Point b{4.0, 5.0, 6.0};
    ComplexExample::Point c{7.0, 8.0, 9.0};

    volatile double result = 0;

    // 内联版本
    Timer timer;
    for (size_t i = 0; i < N; ++i) {
        result = ComplexExample::dotProduct(a, b);
    }
    double inline_time = timer.elapsedMs();

    // 非内联版本（手动调用）
    timer.reset();
    for (size_t i = 0; i < N; ++i) {
        result = ComplexExample::complexCalculation(a, b, c);
    }
    double complex_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "内联 dotProduct: " << inline_time << " ms\n";
    std::cout << "复杂计算:        " << complex_time << " ms\n";
    (void)result;
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  内联优化 (Inlining)\n";
    std::cout << "========================================\n\n";

    std::cout << "说明: 内联消除函数调用开销，但可能增加代码大小。\n";
    std::cout << "编译器会自动决定是否内联，但我们可以提供建议。\n";

    demonstrateInlining();
    demonstrateComplexInlining();

    std::cout << "\n========================================\n";
    std::cout << "  总结\n";
    std::cout << "========================================\n";
    std::cout << "1. 小函数适合内联\n";
    std::cout << "2. inline 是建议，不是强制\n";
    std::cout << "3. __attribute__((always_inline)) 强制内联\n";
    std::cout << "4. __attribute__((noinline)) 禁止内联\n";
    std::cout << "5. 信任编译器的内联决策\n";

    return 0;
}
