/**
 * @file async_io.cpp
 * @brief 异步 I/O 示例
 */

#include <iostream>
#include <fstream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <future>
#include <thread>
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

void demonstrateAsyncIO()
{
    std::cout << "=== 同步 vs 异步 I/O ===\n\n";

    const size_t FILE_SIZE = 10 * 1024 * 1024; // 10MB
    const size_t NUM_FILES = 4;
    std::vector<std::string> filenames;

    // 创建测试文件
    for (size_t i = 0; i < NUM_FILES; ++i) {
        std::string name = "/tmp/test_async_" + std::to_string(i) + ".bin";
        filenames.push_back(name);
        std::vector<char> data(FILE_SIZE, static_cast<char>(i));
        std::ofstream f(name, std::ios::binary);
        f.write(data.data(), data.size());
    }

    // 同步读取
    {
        Timer timer;
        for (size_t i = 0; i < NUM_FILES; ++i) {
            std::ifstream f(filenames[i], std::ios::binary);
            std::vector<char> data(FILE_SIZE);
            f.read(data.data(), data.size());
            volatile char sum = 0;
            for (auto c : data) sum += c;
            (void)sum;
        }
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "同步读取 " << NUM_FILES << " 个文件: " << time << " ms\n";
    }

    // 异步读取
    {
        Timer timer;
        std::vector<std::future<std::vector<char>>> futures;
        for (size_t i = 0; i < NUM_FILES; ++i) {
            futures.push_back(std::async(std::launch::async, [&filenames, i]() {
                std::ifstream f(filenames[i], std::ios::binary);
                std::vector<char> data(FILE_SIZE);
                f.read(data.data(), data.size());
                return data;
            }));
        }
        for (auto& f : futures) {
            auto data = f.get();
            volatile char sum = 0;
            for (auto c : data) sum += c;
            (void)sum;
        }
        double time = timer.elapsedMs();
        std::cout << "异步读取 " << NUM_FILES << " 个文件: " << time << " ms\n";
    }

    // 清理
    for (auto& name : filenames) std::remove(name.c_str());
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  异步 I/O\n";
    std::cout << "========================================\n\n";
    demonstrateAsyncIO();
    std::cout << "\n总结: 异步 I/O 可以重叠计算和 I/O 操作。\n";
    return 0;
}
