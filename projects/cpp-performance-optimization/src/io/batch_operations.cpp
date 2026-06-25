/**
 * @file batch_operations.cpp
 * @brief 批量操作优化示例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <fstream>
#include <numeric>

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

void demonstrateBatchWrite()
{
    std::cout << "=== 批量写入 vs 逐个写入 ===\n\n";

    const size_t N = 1000000;
    const std::string filename = "/tmp/test_batch.bin";
    std::vector<int> data(N);
    std::iota(data.begin(), data.end(), 0);

    // 逐个写入
    {
        Timer timer;
        std::ofstream f(filename, std::ios::binary);
        for (size_t i = 0; i < N; ++i) {
            f.write(reinterpret_cast<const char*>(&data[i]), sizeof(int));
        }
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "逐个写入: " << time << " ms\n";
    }

    // 批量写入
    {
        Timer timer;
        std::ofstream f(filename, std::ios::binary);
        f.write(reinterpret_cast<const char*>(data.data()), N * sizeof(int));
        double time = timer.elapsedMs();
        std::cout << "批量写入: " << time << " ms\n";
    }

    std::remove(filename.c_str());
}

void demonstrateBatchStringConcat()
{
    std::cout << "\n=== 批量字符串拼接 ===\n\n";

    const size_t N = 100000;

    // 逐个拼接
    {
        Timer timer;
        std::string result;
        for (size_t i = 0; i < N; ++i) {
            result += std::to_string(i) + ",";
        }
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "逐个拼接 (+):     " << time << " ms\n";
    }

    // 使用 reserve
    {
        Timer timer;
        std::string result;
        result.reserve(N * 6);
        for (size_t i = 0; i < N; ++i) {
            result += std::to_string(i) + ",";
        }
        double time = timer.elapsedMs();
        std::cout << "预留空间 (+):     " << time << " ms\n";
    }

    // 使用 ostringstream
    {
        Timer timer;
        std::ostringstream oss;
        for (size_t i = 0; i < N; ++i) {
            oss << i << ",";
        }
        std::string result = oss.str();
        double time = timer.elapsedMs();
        std::cout << "ostringstream:    " << time << " ms\n";
    }
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  批量操作优化\n";
    std::cout << "========================================\n\n";
    demonstrateBatchWrite();
    demonstrateBatchStringConcat();
    std::cout << "\n总结: 批量操作减少系统调用次数，显著提升性能。\n";
    return 0;
}
