/**
 * @file loop_unrolling.cpp
 * @brief 循环展开示例
 *
 * 本文件演示循环展开技术：
 * 1. 手动循环展开
 * 2. 编译器自动展开
 * 3. 模板元编程展开
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>

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
 * @brief 示例1: 基本循环展开
 *
 * 循环展开减少循环控制开销（比较、跳转），
 * 但会增加代码大小。
 */
void demonstrateBasicUnrolling()
{
    std::cout << "=== 示例1: 基本循环展开 ===\n\n";

    const size_t N = 10000000;
    std::vector<int> data(N);
    for (size_t i = 0; i < N; ++i) data[i] = static_cast<int>(i);

    constexpr size_t ITERS = 50;

    // 未展开
    Timer timer;
    volatile long long sum1 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            sum1 += data[i];
        }
    }
    double normal_time = timer.elapsedMs();

    // 展开 4 次
    timer.reset();
    volatile long long sum2 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        size_t i = 0;
        for (; i + 4 <= N; i += 4) {
            sum2 += data[i];
            sum2 += data[i + 1];
            sum2 += data[i + 2];
            sum2 += data[i + 3];
        }
        for (; i < N; ++i) {
            sum2 += data[i];
        }
    }
    double unroll4_time = timer.elapsedMs();

    // 展开 8 次
    timer.reset();
    volatile long long sum3 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        size_t i = 0;
        for (; i + 8 <= N; i += 8) {
            sum3 += data[i];
            sum3 += data[i + 1];
            sum3 += data[i + 2];
            sum3 += data[i + 3];
            sum3 += data[i + 4];
            sum3 += data[i + 5];
            sum3 += data[i + 6];
            sum3 += data[i + 7];
        }
        for (; i < N; ++i) {
            sum3 += data[i];
        }
    }
    double unroll8_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "元素数量: " << N << "\n";
    std::cout << "未展开:   " << normal_time << " ms\n";
    std::cout << "展开 4x:  " << unroll4_time << " ms\n";
    std::cout << "展开 8x:  " << unroll8_time << " ms\n";
    (void)sum1; (void)sum2; (void)sum3;
}

/**
 * @brief 示例2: 多累加器展开
 *
 * 使用多个累加器可以利用指令级并行，
 * 减少数据依赖。
 */
void demonstrateMultiAccumulator()
{
    std::cout << "\n=== 示例2: 多累加器展开 ===\n\n";

    const size_t N = 10000000;
    std::vector<int> data(N);
    for (size_t i = 0; i < N; ++i) data[i] = static_cast<int>(i);

    constexpr size_t ITERS = 50;

    // 单累加器
    Timer timer;
    volatile long long sum1 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            sum1 += data[i];
        }
    }
    double single_time = timer.elapsedMs();

    // 4 累加器
    timer.reset();
    volatile long long sum2 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        long long s0 = 0, s1 = 0, s2 = 0, s3 = 0;
        size_t i = 0;
        for (; i + 4 <= N; i += 4) {
            s0 += data[i];
            s1 += data[i + 1];
            s2 += data[i + 2];
            s3 += data[i + 3];
        }
        for (; i < N; ++i) {
            s0 += data[i];
        }
        sum2 = s0 + s1 + s2 + s3;
    }
    double multi_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "元素数量: " << N << "\n";
    std::cout << "单累加器: " << single_time << " ms\n";
    std::cout << "4累加器:  " << multi_time << " ms\n";
    std::cout << "提升: " << single_time / multi_time << "x\n";
    (void)sum1; (void)sum2;
}

/**
 * @brief 示例3: Duff's Device
 *
 * Duff's Device 是一种经典的循环展开技术，
 * 结合了 switch 语句和循环。
 */
void demonstrateDuffsDevice()
{
    std::cout << "\n=== 示例3: Duff's Device ===\n\n";

    const size_t N = 10000000;
    std::vector<int> src(N), dst(N);
    for (size_t i = 0; i < N; ++i) src[i] = static_cast<int>(i);

    constexpr size_t ITERS = 50;

    // 普通拷贝
    Timer timer;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            dst[i] = src[i];
        }
    }
    double normal_time = timer.elapsedMs();

    // Duff's Device (展开 8 次)
    timer.reset();
    for (size_t iter = 0; iter < ITERS; ++iter) {
        size_t count = N;
        size_t n = (count + 7) / 8;
        size_t* s = reinterpret_cast<size_t*>(src.data());
        size_t* d = reinterpret_cast<size_t*>(dst.data());
        switch (count % 8) {
            case 0: do { *d++ = *s++;
            case 7:      *d++ = *s++;
            case 6:      *d++ = *s++;
            case 5:      *d++ = *s++;
            case 4:      *d++ = *s++;
            case 3:      *d++ = *s++;
            case 2:      *d++ = *s++;
            case 1:      *d++ = *s++;
                    } while (--n > 0);
        }
    }
    double duffs_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "元素数量: " << N << "\n";
    std::cout << "普通拷贝: " << normal_time << " ms\n";
    std::cout << "Duff's Device: " << duffs_time << " ms\n";
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  循环展开 (Loop Unrolling)\n";
    std::cout << "========================================\n\n";

    std::cout << "说明: 循环展开减少循环控制开销，\n";
    std::cout << "但会增加代码大小，可能影响指令缓存。\n";

    demonstrateBasicUnrolling();
    demonstrateMultiAccumulator();
    demonstrateDuffsDevice();

    std::cout << "\n========================================\n";
    std::cout << "  总结\n";
    std::cout << "========================================\n";
    std::cout << "1. 循环展开减少控制开销\n";
    std::cout << "2. 多累加器利用指令级并行\n";
    std::cout << "3. 注意代码大小和指令缓存\n";
    std::cout << "4. 通常让编译器自动展开\n";

    return 0;
}
