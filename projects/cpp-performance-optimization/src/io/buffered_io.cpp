/**
 * @file buffered_io.cpp
 * @brief 缓冲 I/O 示例
 */

#include <iostream>
#include <fstream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <cstdio>

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

void demonstrateBufferedVsUnbuffered()
{
    std::cout << "=== 缓冲 vs 无缓冲 I/O ===\n\n";

    const size_t N = 1000000;
    const std::string filename = "/tmp/test_io.bin";

    // 写入数据
    std::vector<int> data(N);
    for (size_t i = 0; i < N; ++i) data[i] = static_cast<int>(i);

    // C++ iostream (有缓冲)
    {
        Timer timer;
        std::ofstream file(filename, std::ios::binary);
        for (size_t i = 0; i < N; ++i) {
            file.write(reinterpret_cast<const char*>(&data[i]), sizeof(int));
        }
        file.close();
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "逐个写入 (ofstream): " << time << " ms\n";
    }

    // 批量写入
    {
        Timer timer;
        std::ofstream file(filename, std::ios::binary);
        file.write(reinterpret_cast<const char*>(data.data()), N * sizeof(int));
        file.close();
        double time = timer.elapsedMs();
        std::cout << "批量写入 (ofstream): " << time << " ms\n";
    }

    // C FILE (有缓冲)
    {
        Timer timer;
        FILE* f = fopen(filename.c_str(), "wb");
        fwrite(data.data(), sizeof(int), N, f);
        fclose(f);
        double time = timer.elapsedMs();
        std::cout << "批量写入 (fwrite):   " << time << " ms\n";
    }

    std::remove(filename.c_str());
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  缓冲 I/O\n";
    std::cout << "========================================\n\n";
    demonstrateBufferedVsUnbuffered();
    std::cout << "\n总结: 批量 I/O 比逐个 I/O 快得多。\n";
    return 0;
}
