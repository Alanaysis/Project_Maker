/**
 * @file parallelization.cpp
 * @brief 并行化优化示例
 *
 * 本文件演示多核并行计算：
 * 1. std::thread 并行
 * 2. std::async 并行
 * 3. 并行归约
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <thread>
#include <future>
#include <numeric>
#include <algorithm>
#include <functional>
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

/**
 * @brief 示例1: 并行求和
 */
void demonstrateParallelSum()
{
    std::cout << "=== 示例1: 并行求和 ===\n\n";

    const size_t N = 100000000;
    std::vector<int> data(N);
    for (size_t i = 0; i < N; ++i) {
        data[i] = static_cast<int>(i % 1000);
    }

    // 串行版本
    Timer timer;
    volatile long long serial_sum = 0;
    for (size_t iter = 0; iter < 5; ++iter) {
        long long s = 0;
        for (size_t i = 0; i < N; ++i) {
            s += data[i];
        }
        serial_sum = s;
    }
    double serial_time = timer.elapsedMs();

    // 并行版本
    const size_t num_threads = std::thread::hardware_concurrency();
    timer.reset();
    volatile long long parallel_sum = 0;
    for (size_t iter = 0; iter < 5; ++iter) {
        std::vector<std::future<long long>> futures;
        size_t chunk_size = N / num_threads;

        for (size_t t = 0; t < num_threads; ++t) {
            size_t start = t * chunk_size;
            size_t end = (t == num_threads - 1) ? N : start + chunk_size;
            futures.push_back(std::async(std::launch::async, [&data, start, end]() {
                long long s = 0;
                for (size_t i = start; i < end; ++i) {
                    s += data[i];
                }
                return s;
            }));
        }

        long long total = 0;
        for (auto& f : futures) {
            total += f.get();
        }
        parallel_sum = total;
    }
    double parallel_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "元素数量: " << N << "\n";
    std::cout << "线程数: " << num_threads << "\n";
    std::cout << "串行: " << serial_time << " ms\n";
    std::cout << "并行: " << parallel_time << " ms\n";
    std::cout << "加速比: " << serial_time / parallel_time << "x\n";
    (void)serial_sum; (void)parallel_sum;
}

/**
 * @brief 示例2: 并行变换
 */
void demonstrateParallelTransform()
{
    std::cout << "\n=== 示例2: 并行变换 ===\n\n";

    const size_t N = 50000000;
    std::vector<float> input(N), output(N);
    for (size_t i = 0; i < N; ++i) {
        input[i] = static_cast<float>(i) / N;
    }

    // 串行版本
    Timer timer;
    for (size_t i = 0; i < N; ++i) {
        output[i] = std::sin(input[i]) * std::cos(input[i]);
    }
    double serial_time = timer.elapsedMs();

    // 并行版本
    const size_t num_threads = std::thread::hardware_concurrency();
    timer.reset();
    {
        std::vector<std::thread> threads;
        size_t chunk_size = N / num_threads;

        for (size_t t = 0; t < num_threads; ++t) {
            size_t start = t * chunk_size;
            size_t end = (t == num_threads - 1) ? N : start + chunk_size;
            threads.emplace_back([&input, &output, start, end]() {
                for (size_t i = start; i < end; ++i) {
                    output[i] = std::sin(input[i]) * std::cos(input[i]);
                }
            });
        }

        for (auto& t : threads) {
            t.join();
        }
    }
    double parallel_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "元素数量: " << N << "\n";
    std::cout << "串行: " << serial_time << " ms\n";
    std::cout << "并行: " << parallel_time << " ms\n";
    std::cout << "加速比: " << serial_time / parallel_time << "x\n";
}

/**
 * @brief 示例3: Amdahl 定律
 */
void demonstrateAmdahl()
{
    std::cout << "\n=== 示例3: Amdahl 定律 ===\n\n";

    std::cout << "Amdahl 定律: 加速比 = 1 / ((1-P) + P/N)\n";
    std::cout << "P = 可并行化比例, N = 处理器数量\n\n";

    std::vector<double> parallel_ratios = {0.5, 0.75, 0.9, 0.95, 0.99};
    std::vector<size_t> thread_counts = {1, 2, 4, 8, 16, 32};

    std::cout << std::fixed << std::setprecision(2);
    std::cout << std::setw(12) << "P \\ N";
    for (size_t n : thread_counts) {
        std::cout << std::setw(8) << n;
    }
    std::cout << "\n";

    for (double p : parallel_ratios) {
        std::cout << std::setw(12) << p;
        for (size_t n : thread_counts) {
            double speedup = 1.0 / ((1.0 - p) + p / n);
            std::cout << std::setw(8) << speedup;
        }
        std::cout << "\n";
    }
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  并行化 (Parallelization)\n";
    std::cout << "========================================\n\n";

    std::cout << "说明: 利用多核 CPU 可以线性加速计算。\n";
    std::cout << "但需要注意线程创建开销和同步开销。\n";

    demonstrateParallelSum();
    demonstrateParallelTransform();
    demonstrateAmdahl();

    std::cout << "\n========================================\n";
    std::cout << "  总结\n";
    std::cout << "========================================\n";
    std::cout << "1. 并行化可以接近线性加速\n";
    std::cout << "2. 注意线程创建和同步开销\n";
    std::cout << "3. Amdahl 定律限制了最大加速比\n";
    std::cout << "4. 使用线程池减少创建开销\n";

    return 0;
}
