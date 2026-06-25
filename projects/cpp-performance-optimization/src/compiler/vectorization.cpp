/**
 * @file vectorization.cpp
 * @brief 向量化优化示例
 *
 * 本文件演示 SIMD 向量化：
 * 1. 自动向量化
 * 2. SIMD 内置函数
 * 3. 向量化友好的代码模式
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <cmath>

#ifdef __SSE2__
#include <emmintrin.h>
#endif

#ifdef __AVX2__
#include <immintrin.h>
#endif

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

/**
 * @brief 示例1: 自动向量化
 *
 * 编译器可以自动向量化简单的循环。
 * 使用 -O3 -march=native 编译选项。
 */
void demonstrateAutoVectorization()
{
    std::cout << "=== 示例1: 自动向量化 ===\n\n";

    const size_t N = 10000000;
    std::vector<float> a(N), b(N), c(N);

    for (size_t i = 0; i < N; ++i) {
        a[i] = static_cast<float>(i);
        b[i] = static_cast<float>(i * 2);
    }

    constexpr size_t ITERS = 50;

    // 标量版本
    Timer timer;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            c[i] = a[i] + b[i];
        }
    }
    double scalar_time = timer.elapsedMs();

    // 使用 restrict 提示编译器无别名
    timer.reset();
    float* __restrict pa = a.data();
    float* __restrict pb = b.data();
    float* __restrict pc = c.data();
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            pc[i] = pa[i] + pb[i];
        }
    }
    double restrict_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "元素数量: " << N << "\n";
    std::cout << "标量版本: " << scalar_time << " ms\n";
    std::cout << "restrict: " << restrict_time << " ms\n";
}

/**
 * @brief 示例2: SSE2 向量化
 *
 * 手动使用 SSE2 内置函数进行向量化。
 */
#ifdef __SSE2__
void demonstrateSSE2()
{
    std::cout << "\n=== 示例2: SSE2 向量化 ===\n\n";

    const size_t N = 10000000;
    // 对齐分配
    std::vector<float> a(N), b(N), c(N);
    for (size_t i = 0; i < N; ++i) {
        a[i] = static_cast<float>(i);
        b[i] = static_cast<float>(i * 2);
    }

    constexpr size_t ITERS = 50;

    // 标量版本
    Timer timer;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            c[i] = a[i] + b[i];
        }
    }
    double scalar_time = timer.elapsedMs();

    // SSE2 版本（每次处理 4 个 float）
    timer.reset();
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; i += 4) {
            __m128 va = _mm_loadu_ps(&a[i]);
            __m128 vb = _mm_loadu_ps(&b[i]);
            __m128 vc = _mm_add_ps(va, vb);
            _mm_storeu_ps(&c[i], vc);
        }
    }
    double sse_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "元素数量: " << N << "\n";
    std::cout << "标量版本: " << scalar_time << " ms\n";
    std::cout << "SSE2:     " << sse_time << " ms\n";
    std::cout << "SSE2 快:  " << scalar_time / sse_time << "x\n";
}
#endif

/**
 * @brief 示例3: 向量化点积
 */
void demonstrateDotProduct()
{
    std::cout << "\n=== 示例3: 向量化点积 ===\n\n";

    const size_t N = 10000000;
    std::vector<float> a(N), b(N);
    for (size_t i = 0; i < N; ++i) {
        a[i] = static_cast<float>(i) / N;
        b[i] = static_cast<float>(i * 2) / N;
    }

    constexpr size_t ITERS = 50;

    // 标量版本
    Timer timer;
    volatile float sum1 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        float s = 0;
        for (size_t i = 0; i < N; ++i) {
            s += a[i] * b[i];
        }
        sum1 = s;
    }
    double scalar_time = timer.elapsedMs();

#ifdef __SSE2__
    // SSE2 版本
    timer.reset();
    volatile float sum2 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        __m128 vsum = _mm_setzero_ps();
        for (size_t i = 0; i < N; i += 4) {
            __m128 va = _mm_loadu_ps(&a[i]);
            __m128 vb = _mm_loadu_ps(&b[i]);
            vsum = _mm_add_ps(vsum, _mm_mul_ps(va, vb));
        }
        // 水平求和
        float temp[4];
        _mm_storeu_ps(temp, vsum);
        sum2 = temp[0] + temp[1] + temp[2] + temp[3];
    }
    double sse_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "标量版本: " << scalar_time << " ms\n";
    std::cout << "SSE2:     " << sse_time << " ms\n";
    std::cout << "SSE2 快:  " << scalar_time / sse_time << "x\n";
#else
    std::cout << "SSE2 不可用\n";
#endif
    (void)sum1;
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  向量化 (Vectorization)\n";
    std::cout << "========================================\n\n";

    std::cout << "说明: SIMD (Single Instruction Multiple Data) 可以\n";
    std::cout << "同时处理多个数据，显著提升数值计算性能。\n";
    std::cout << "SSE2: 4 个 float, AVX: 8 个 float, AVX-512: 16 个 float\n";

    demonstrateAutoVectorization();
#ifdef __SSE2__
    demonstrateSSE2();
#endif
    demonstrateDotProduct();

    std::cout << "\n========================================\n";
    std::cout << "  总结\n";
    std::cout << "========================================\n";
    std::cout << "1. 使用 -O3 -march=native 启用自动向量化\n";
    std::cout << "2. 使用 __restrict 消除别名\n";
    std::cout << "3. 保持数据对齐\n";
    std::cout << "4. 手动 SIMD 可以获得更好效果\n";

    return 0;
}
