/**
 * @file utils.hpp
 * @brief 工具函数集
 *
 * 提供各种性能测试辅助工具
 */

#pragma once

#include <vector>
#include <random>
#include <algorithm>
#include <numeric>
#include <string>
#include <iostream>
#include <iomanip>
#include <memory>
#include <cstring>

#ifdef __linux__
#include <unistd.h>
#include <sys/sysinfo.h>
#endif

namespace perf {

/**
 * @brief 随机数生成器
 */
class RandomGenerator
{
public:
    explicit RandomGenerator(uint64_t seed = std::random_device{}())
        : engine_(seed) {}

    /**
     * @brief 生成随机整数向量
     */
    std::vector<int> randomInts(size_t count, int min = 0, int max = 1000000)
    {
        std::uniform_int_distribution<int> dist(min, max);
        std::vector<int> result(count);
        for (auto& v : result) {
            v = dist(engine_);
        }
        return result;
    }

    /**
     * @brief 生成随机浮点数向量
     */
    std::vector<float> randomFloats(size_t count, float min = 0.0f, float max = 1.0f)
    {
        std::uniform_real_distribution<float> dist(min, max);
        std::vector<float> result(count);
        for (auto& v : result) {
            v = dist(engine_);
        }
        return result;
    }

    /**
     * @brief 生成随机 double 向量
     */
    std::vector<double> randomDoubles(size_t count, double min = 0.0, double max = 1.0)
    {
        std::uniform_real_distribution<double> dist(min, max);
        std::vector<double> result(count);
        for (auto& v : result) {
            v = dist(engine_);
        }
        return result;
    }

    /**
     * @brief 生成随机字节
     */
    std::vector<uint8_t> randomBytes(size_t count)
    {
        std::uniform_int_distribution<int> dist(0, 255);
        std::vector<uint8_t> result(count);
        for (auto& v : result) {
            v = static_cast<uint8_t>(dist(engine_));
        }
        return result;
    }

    /**
     * @brief 生成随机字符串
     */
    std::string randomString(size_t length)
    {
        static const char charset[] =
            "0123456789"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz";
        std::uniform_int_distribution<size_t> dist(0, sizeof(charset) - 2);
        std::string result(length, '\0');
        for (auto& c : result) {
            c = charset[dist(engine_)];
        }
        return result;
    }

private:
    std::mt19937_64 engine_;
};

/**
 * @brief 内存对齐分配
 */
template<typename T>
class AlignedAllocator
{
public:
    using value_type = T;

    explicit AlignedAllocator(size_t alignment = 64) : alignment_(alignment) {}

    T* allocate(size_t n)
    {
        void* ptr = nullptr;
#ifdef _WIN32
        ptr = _aligned_malloc(n * sizeof(T), alignment_);
#else
        ptr = std::aligned_alloc(alignment_, ((n * sizeof(T) + alignment_ - 1) / alignment_) * alignment_);
#endif
        if (!ptr) throw std::bad_alloc();
        return static_cast<T*>(ptr);
    }

    void deallocate(T* ptr, size_t)
    {
#ifdef _WIN32
        _aligned_free(ptr);
#else
        std::free(ptr);
#endif
    }

private:
    size_t alignment_;
};

/**
 * @brief 防止编译器优化掉值
 */
template<typename T>
void doNotOptimize(T const& val)
{
#if defined(__GNUC__) || defined(__clang__)
    asm volatile("" : : "r,m"(val) : "memory");
#else
    // MSVC
    volatile void* p = &val;
    (void)p;
#endif
}

/**
 * @brief 防止编译器重排
 */
inline void clobber()
{
#if defined(__GNUC__) || defined(__clang__)
    asm volatile("" : : : "memory");
#else
    _ReadWriteBarrier();
#endif
}

/**
 * @brief 数据验证工具
 */
template<typename T>
bool verifyEqual(const std::vector<T>& a, const std::vector<T>& b)
{
    if (a.size() != b.size()) return false;
    for (size_t i = 0; i < a.size(); ++i) {
        if (a[i] != b[i]) return false;
    }
    return true;
}

template<typename T>
bool verifyClose(const std::vector<T>& a, const std::vector<T>& b, double epsilon = 1e-6)
{
    if (a.size() != b.size()) return false;
    for (size_t i = 0; i < a.size(); ++i) {
        if (std::abs(static_cast<double>(a[i]) - static_cast<double>(b[i])) > epsilon) {
            return false;
        }
    }
    return true;
}

/**
 * @brief 系统信息
 */
inline void printSystemInfo()
{
#ifdef __linux__
    std::cout << "=== 系统信息 ===\n";

    // CPU 信息
    long num_cpus = sysconf(_SC_NPROCESSORS_ONLN);
    std::cout << "CPU 核心数: " << num_cpus << "\n";

    // 页面大小
    long page_size = sysconf(_SC_PAGESIZE);
    std::cout << "页面大小: " << page_size << " bytes\n";

    // 内存信息
    struct sysinfo si;
    if (sysinfo(&si) == 0) {
        double total_ram = si.totalram * si.mem_unit / (1024.0 * 1024.0 * 1024.0);
        std::cout << "总内存: " << std::fixed << std::setprecision(1) << total_ram << " GB\n";
    }
#endif
}

/**
 * @brief 缓存行大小
 */
constexpr size_t CACHE_LINE_SIZE = 64;

/**
 * @brief 填充到缓存行大小
 */
template<typename T>
struct alignas(CACHE_LINE_SIZE) CacheLinePadded
{
    T value;
    char padding[CACHE_LINE_SIZE - sizeof(T)];

    CacheLinePadded() = default;
    CacheLinePadded(const T& v) : value(v) {}
    operator T&() { return value; }
    operator const T&() const { return value; }
};

/**
 * @brief 打印分隔线
 */
inline void printSeparator(const std::string& title = "")
{
    if (!title.empty()) {
        std::cout << "\n=== " << title << " ===\n";
    } else {
        std::cout << "\n" << std::string(50, '-') << "\n";
    }
}

/**
 * @brief 格式化数字
 */
inline std::string formatNumber(size_t n)
{
    std::string s = std::to_string(n);
    int insertPosition = s.length() - 3;
    while (insertPosition > 0) {
        s.insert(insertPosition, ",");
        insertPosition -= 3;
    }
    return s;
}

/**
 * @brief 格式化字节大小
 */
inline std::string formatBytes(size_t bytes)
{
    const char* units[] = {"B", "KB", "MB", "GB", "TB"};
    int unit = 0;
    double size = static_cast<double>(bytes);
    while (size >= 1024.0 && unit < 4) {
        size /= 1024.0;
        ++unit;
    }
    std::ostringstream oss;
    oss << std::fixed << std::setprecision(2) << size << " " << units[unit];
    return oss.str();
}

/**
 * @brief 简单的作用域内存统计
 */
class MemoryTracker
{
public:
    static MemoryTracker& instance()
    {
        static MemoryTracker tracker;
        return tracker;
    }

    void recordAllocation(size_t size)
    {
        total_allocated_ += size;
        current_allocated_ += size;
        peak_allocated_ = std::max(peak_allocated_, current_allocated_);
        ++allocation_count_;
    }

    void recordDeallocation(size_t size)
    {
        current_allocated_ -= size;
        ++deallocation_count_;
    }

    void print() const
    {
        std::cout << "=== 内存统计 ===\n";
        std::cout << "  总分配: " << formatBytes(total_allocated_) << "\n";
        std::cout << "  当前:   " << formatBytes(current_allocated_) << "\n";
        std::cout << "  峰值:   " << formatBytes(peak_allocated_) << "\n";
        std::cout << "  分配次数: " << allocation_count_ << "\n";
        std::cout << "  释放次数: " << deallocation_count_ << "\n";
    }

    void reset()
    {
        total_allocated_ = 0;
        current_allocated_ = 0;
        peak_allocated_ = 0;
        allocation_count_ = 0;
        deallocation_count_ = 0;
    }

private:
    size_t total_allocated_ = 0;
    size_t current_allocated_ = 0;
    size_t peak_allocated_ = 0;
    size_t allocation_count_ = 0;
    size_t deallocation_count_ = 0;
};

} // namespace perf