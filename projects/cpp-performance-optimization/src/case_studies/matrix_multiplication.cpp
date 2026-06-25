/**
 * @file matrix_multiplication.cpp
 * @brief 矩阵乘法优化案例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <random>

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
 * @brief 朴素矩阵乘法 O(n^3)
 */
void matmulNaive(const float* A, const float* B, float* C, size_t N)
{
    for (size_t i = 0; i < N; ++i)
        for (size_t j = 0; j < N; ++j) {
            float sum = 0;
            for (size_t k = 0; k < N; ++k)
                sum += A[i * N + k] * B[k * N + j];
            C[i * N + j] = sum;
        }
}

/**
 * @brief 循环分块矩阵乘法
 */
void matmulTiled(const float* A, const float* B, float* C, size_t N, size_t TILE = 32)
{
    for (size_t i = 0; i < N * N; ++i) C[i] = 0;

    for (size_t ii = 0; ii < N; ii += TILE)
        for (size_t jj = 0; jj < N; jj += TILE)
            for (size_t kk = 0; kk < N; kk += TILE)
                for (size_t i = ii; i < std::min(ii + TILE, N); ++i)
                    for (size_t j = jj; j < std::min(jj + TILE, N); ++j) {
                        float sum = 0;
                        for (size_t k = kk; k < std::min(kk + TILE, N); ++k)
                            sum += A[i * N + k] * B[k * N + j];
                        C[i * N + j] += sum;
                    }
}

void demonstrateMatrixMultiply()
{
    std::cout << "=== 矩阵乘法优化 ===\n\n";

    const size_t N = 512;
    std::vector<float> A(N * N), B(N * N), C(N * N);
    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(-1.0f, 1.0f);
    for (auto& v : A) v = dist(rng);
    for (auto& v : B) v = dist(rng);

    // 朴素版本
    Timer timer;
    matmulNaive(A.data(), B.data(), C.data(), N);
    double naive_time = timer.elapsedMs();

    // 分块版本
    timer.reset();
    matmulTiled(A.data(), B.data(), C.data(), N);
    double tiled_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "矩阵大小: " << N << " x " << N << "\n";
    std::cout << "朴素版本: " << naive_time << " ms\n";
    std::cout << "分块版本: " << tiled_time << " ms\n";
    std::cout << "分块快:   " << naive_time / tiled_time << "x\n";
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  矩阵乘法优化\n";
    std::cout << "========================================\n\n";
    demonstrateMatrixMultiply();
    std::cout << "\n总结: 循环分块利用缓存，可以显著提升矩阵乘法性能。\n";
    return 0;
}
