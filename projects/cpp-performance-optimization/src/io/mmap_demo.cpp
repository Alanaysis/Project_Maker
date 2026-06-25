/**
 * @file mmap_demo.cpp
 * @brief 内存映射文件示例
 */

#include <iostream>
#include <fstream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <cstring>

#ifdef __linux__
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
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

#ifdef __linux__
void demonstrateMmap()
{
    std::cout << "=== mmap vs 标准 I/O ===\n\n";

    const size_t FILE_SIZE = 100 * 1024 * 1024; // 100MB
    const std::string filename = "/tmp/test_mmap.bin";

    // 创建测试文件
    {
        std::ofstream f(filename, std::ios::binary);
        std::vector<char> data(FILE_SIZE, 'A');
        f.write(data.data(), data.size());
    }

    // 标准 I/O 读取
    {
        Timer timer;
        std::ifstream f(filename, std::ios::binary);
        std::vector<char> data(FILE_SIZE);
        f.read(data.data(), data.size());

        volatile long long sum = 0;
        for (size_t i = 0; i < FILE_SIZE; i += 4096) {
            sum += data[i];
        }
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "标准 I/O 读取: " << time << " ms\n";
        (void)sum;
    }

    // mmap 读取
    {
        Timer timer;
        int fd = open(filename.c_str(), O_RDONLY);
        void* mapped = mmap(nullptr, FILE_SIZE, PROT_READ, MAP_PRIVATE, fd, 0);

        volatile long long sum = 0;
        const char* data = static_cast<const char*>(mapped);
        for (size_t i = 0; i < FILE_SIZE; i += 4096) {
            sum += data[i];
        }

        munmap(mapped, FILE_SIZE);
        close(fd);
        double time = timer.elapsedMs();
        std::cout << "mmap 读取:      " << time << " ms\n";
        (void)sum;
    }

    std::remove(filename.c_str());
}
#endif

int main()
{
    std::cout << "========================================\n";
    std::cout << "  内存映射文件 (mmap)\n";
    std::cout << "========================================\n\n";

#ifdef __linux__
    demonstrateMmap();
#else
    std::cout << "mmap 仅在 Linux/macOS 上可用\n";
#endif

    std::cout << "\n总结: mmap 避免数据拷贝，适合大文件随机访问。\n";
    return 0;
}
