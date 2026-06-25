/**
 * @file vector_operations.cpp
 * @brief 向量运算优化案例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <cmath>
#include <random>

#ifdef __SSE2__
#include <emmintrin.h>
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
 * @brief 标量向量加法
 */
void vectorAddScalar(const float* a, const float* b, float* c, size_t n)
{
    for (size_t i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

/**
 * @brief SSE2 向量加法
 */
#ifdef __SSE2__
void vectorAddSSE(const float* a, const float* b, float* c, size_t n)
{
    for (size_t i = 0; i < n; i += 4) {
        __m128 va = _mm_loadu_ps(&a[i]);
        __m128 vb = _mm_loadu_ps(&b[i]);
        __m128 vc = _mm_add_ps(va, vb);
        _mm_storeu_ps(&c[i], vc);
    }
}
#endif

void demonstrateVectorAdd()
{
    std::cout << "=== 向量加法优化 ===\n\n";

    const size_t N = 10000000;
    std::vector<float> a(N), b(N), c(N);
    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(-1.0f, 1.0f);
    for (size_t i = 0; i < N; ++i) {
        a[i] = dist(rng); b[i] = dist(rng);
    }

    constexpr size_t ITERS = 50;

    Timer timer;
    for (size_t iter = 0; iter < ITERS; ++iter)
        vectorAddScalar(a.data(), b.data(), c.data(), N);
    double scalar_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "标量版本: " << scalar_time << " ms\n";

#ifdef __SSE2__
    timer.reset();
    for (size_t iter = 0; iter < ITERS; ++iter)
        vectorAddSSE(a.data(), b.data(), c.data(), N);
    double sse_time = timer.elapsedMs();
    std::cout << "SSE2版本: " << sse_time << " ms\n";
    std::cout << "SSE2快:   " << scalar_time / sse_time << "x\n";
#endif
}

/**
 * @brief 向量点积优化
 */
void demonstrateDotProduct()
{
    std::cout << "\n=== 向量点积优化 ===\n\n";

    const size_t N = 10000000;
    std::vector<float> a(N), b(N);
    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(-1.0f, 1.0f);
    for (size_t i = 0; i < N; ++i) {
        a[i] = dist(rng); b[i] = dist(rng);
    }

    constexpr size_t ITERS = 50;

    // 标量版本
    Timer timer;
    volatile float sum1 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        float s = 0;
        for (size_t i = 0; i < N; ++i) s += a[i] * b[i];
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
        float temp[4];
        _mm_storeu_ps(temp, vsum);
        sum2 = temp[0] + temp[1] + temp[2] + temp[3];
    }
    double sse_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "标量版本: " << scalar_time << " ms\n";
    std::cout << "SSE2版本: " << sse_time << " ms\n";
    std::cout << "SSE2快:   " << scalar_time / sse_time << "x\n";
#endif
    (void)sum1;
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  向量运算优化\n";
    std::cout << "========================================\n\n";
    demonstrateVectorAdd();
    demonstrateDotProduct();
    std::cout << "\n总结: SIMD 指令可以显著加速向量运算。\n";
    return 0;
}
