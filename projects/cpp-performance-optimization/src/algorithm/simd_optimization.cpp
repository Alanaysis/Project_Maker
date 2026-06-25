/**
 * @file simd_optimization.cpp
 * @brief SIMD 优化示例
 *
 * 本文件演示 SIMD 指令优化：
 * 1. SSE2 向量运算
 * 2. 向量点积计算
 * 3. 向量归一化
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
 * @brief 示例1: 向量加法
 */
void demonstrateVectorAdd()
{
    std::cout << "=== 示例1: 向量加法 ===\n\n";

    const size_t N = 10000000;
    std::vector<float> a(N), b(N), c(N);
    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(-1.0f, 1.0f);
    for (size_t i = 0; i < N; ++i) {
        a[i] = dist(rng);
        b[i] = dist(rng);
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

#ifdef __SSE2__
    // SSE2 版本
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
    std::cout << "标量: " << scalar_time << " ms\n";
    std::cout << "SSE2: " << sse_time << " ms\n";
    std::cout << "SSE2 快: " << scalar_time / sse_time << "x\n";
#else
    std::cout << "SSE2 不可用\n";
#endif
}

/**
 * @brief 示例2: 向量点积
 */
void demonstrateDotProduct()
{
    std::cout << "\n=== 示例2: 向量点积 ===\n\n";

    const size_t N = 10000000;
    std::vector<float> a(N), b(N);
    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(-1.0f, 1.0f);
    for (size_t i = 0; i < N; ++i) {
        a[i] = dist(rng);
        b[i] = dist(rng);
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
        float temp[4];
        _mm_storeu_ps(temp, vsum);
        sum2 = temp[0] + temp[1] + temp[2] + temp[3];
    }
    double sse_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "标量: " << scalar_time << " ms\n";
    std::cout << "SSE2: " << sse_time << " ms\n";
    std::cout << "SSE2 快: " << scalar_time / sse_time << "x\n";
#else
    std::cout << "SSE2 不可用\n";
#endif
    (void)sum1;
}

/**
 * @brief 示例3: 向量归一化
 */
void demonstrateNormalization()
{
    std::cout << "\n=== 示例3: 向量归一化 ===\n\n";

    const size_t N = 1000000;
    const size_t VEC_SIZE = 3; // 3D 向量

    std::vector<float> data(N * VEC_SIZE);
    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(-1.0f, 1.0f);
    for (auto& v : data) v = dist(rng);

    constexpr size_t ITERS = 100;

    // 标量版本
    Timer timer;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            float x = data[i * 3];
            float y = data[i * 3 + 1];
            float z = data[i * 3 + 2];
            float len = std::sqrt(x * x + y * y + z * z);
            if (len > 0) {
                data[i * 3] = x / len;
                data[i * 3 + 1] = y / len;
                data[i * 3 + 2] = z / len;
            }
        }
    }
    double scalar_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "向量数量: " << N << "\n";
    std::cout << "标量归一化: " << scalar_time << " ms\n";
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  SIMD 优化\n";
    std::cout << "========================================\n\n";

    std::cout << "说明: SIMD 可以同时处理多个数据。\n";
    std::cout << "SSE2: 4 个 float (128 bits)\n";
    std::cout << "AVX:  8 个 float (256 bits)\n";

    demonstrateVectorAdd();
    demonstrateDotProduct();
    demonstrateNormalization();

    std::cout << "\n========================================\n";
    std::cout << "  总结\n";
    std::cout << "========================================\n";
    std::cout << "1. SIMD 提升 2-8 倍性能\n";
    std::cout << "2. 保持数据对齐\n";
    std::cout << "3. 使用 -march=native 启用 AVX\n";
    std::cout << "4. 考虑使用 SIMD 库\n";

    return 0;
}
