/**
 * memory_alignment.cpp - 内存对齐优化演示
 *
 * 本文件演示内存对齐对性能的影响，包括：
 * 1. alignas 说明符的使用
 * 2. 对齐分配 (std::align_val_t)
 * 3. SIMD 操作中的对齐要求
 * 4. 结构体布局优化与填充
 * 5. 对齐 vs 未对齐访问的性能差异
 *
 * 编译命令:
 *   g++ -std=c++17 -O2 -o memory_alignment memory_alignment.cpp
 *   g++ -std=c++17 -O2 -mavx2 -o memory_alignment memory_alignment.cpp  # 启用 AVX2
 *
 * 关键概念:
 *   - 对齐(Alignment): 数据地址是某个值的整数倍
 *   - 自然对齐: 数据地址是其自身大小的整数倍
 *   - 对齐访问通常比未对齐访问快，尤其是 SIMD 操作
 *   - 未对齐访问可能跨越缓存行边界，导致额外的缓存操作
 */

#include <chrono>
#include <iostream>
#include <iomanip>
#include <vector>
#include <new>         // std::align_val_t
#include <memory>
#include <cstring>
#include <cstdlib>
#include <cassert>
#include <numeric>
#include <algorithm>
#include <random>
#include <type_traits>

// ============================================================================
// 辅助工具
// ============================================================================

class Timer {
    std::chrono::high_resolution_clock::time_point start_;
    std::string name_;
public:
    explicit Timer(const std::string& name)
        : start_(std::chrono::high_resolution_clock::now()), name_(name) {}

    ~Timer() {
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start_);
        std::cout << std::setw(45) << std::left << name_
                  << ": " << std::setw(10) << std::right << duration.count()
                  << " us" << std::endl;
    }

    long long elapsed() const {
        auto end = std::chrono::high_resolution_clock::now();
        return std::chrono::duration_cast<std::chrono::microseconds>(end - start_).count();
    }
};

template<typename T>
void doNotOptimize(T&& value) {
    asm volatile("" : : "r,m"(value) : "memory");
}

// ============================================================================
// 演示 1: alignas 说明符基础用法
// ============================================================================

/*
 * alignas 指定变量或类型的对齐要求。
 * 对齐值必须是 2 的幂（1, 2, 4, 8, 16, 32, 64, ...）。
 *
 * 常见对齐值:
 *   4  - float, int32
 *   8  - double, int64, 指针(64位)
 *   16 - SSE 向量类型 (__m128)
 *   32 - AVX 向量类型 (__m256)
 *   64 - 缓存行大小，避免伪共享
 */

// 默认对齐的结构体
struct DefaultAligned {
    char a;      // 1 字节
    double b;    // 8 字节
    char c;      // 1 字节
    int d;       // 4 字节
};
// 大小: 24 字节 (含 10 字节填充)

// 指定 64 字节对齐的结构体（缓存行对齐）
struct CacheLineAligned {
    alignas(64) char a;
    alignas(64) double b;
    alignas(64) char c;
    alignas(64) int d;
};
// 大小: 256 字节 (每个字段独占一个缓存行)

// 指定 32 字节对齐（AVX 对齐）
struct AVXAligned {
    alignas(32) float values[8];  // 32 字节，刚好一个 AVX 寄存器
};

void demonstrateAlignas() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 1: alignas 说明符基础用法" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::cout << "\n  基本类型对齐要求:" << std::endl;
    std::cout << "    alignof(char)   = " << alignof(char) << " 字节" << std::endl;
    std::cout << "    alignof(int)    = " << alignof(int) << " 字节" << std::endl;
    std::cout << "    alignof(double) = " << alignof(double) << " 字节" << std::endl;
    std::cout << "    alignof(void*)  = " << alignof(void*) << " 字节" << std::endl;

    std::cout << "\n  结构体对齐和大小:" << std::endl;
    std::cout << "    DefaultAligned:    size=" << sizeof(DefaultAligned)
              << "  align=" << alignof(DefaultAligned) << std::endl;
    std::cout << "    CacheLineAligned:  size=" << sizeof(CacheLineAligned)
              << "  align=" << alignof(CacheLineAligned) << std::endl;
    std::cout << "    AVXAligned:        size=" << sizeof(AVXAligned)
              << "  align=" << alignof(AVXAligned) << std::endl;

    // 验证地址对齐
    alignas(64) CacheLineAligned cla;
    std::cout << "\n  CacheLineAligned 实例地址验证:" << std::endl;
    std::cout << "    &cla   = " << (void*)&cla
              << " (64对齐: " << (reinterpret_cast<uintptr_t>(&cla) % 64 == 0 ? "是" : "否") << ")" << std::endl;
    std::cout << "    &cla.a = " << (void*)&cla.a
              << " (64对齐: " << (reinterpret_cast<uintptr_t>(&cla.a) % 64 == 0 ? "是" : "否") << ")" << std::endl;
    std::cout << "    &cla.b = " << (void*)&cla.b
              << " (64对齐: " << (reinterpret_cast<uintptr_t>(&cla.b) % 64 == 0 ? "是" : "否") << ")" << std::endl;

    std::cout << "\n  使用建议:" << std::endl;
    std::cout << "    - alignas(64): 避免多线程伪共享" << std::endl;
    std::cout << "    - alignas(32): AVX 向量操作" << std::endl;
    std::cout << "    - alignas(16): SSE 向量操作" << std::endl;
    std::cout << "    - alignas(std::hardware_destructive_interference_size): C++17 标准方式" << std::endl;
}

// ============================================================================
// 演示 2: 对齐分配 (Aligned Allocation)
// ============================================================================

/*
 * C++17 引入了对齐版本的 new/delete:
 *   operator new(size_t, std::align_val_t)
 *   operator delete(void*, size_t, std::align_val_t)
 *
 * 也可以使用 aligned_alloc (C++17) 或 posix_memalign (POSIX)
 */

// 自定义对齐分配器 (需要在命名空间作用域定义)
template<typename T, size_t Alignment>
struct AlignedAllocator {
    using value_type = T;

    // std::vector 需要的 rebind 机制
    template<typename U>
    struct rebind {
        using other = AlignedAllocator<U, Alignment>;
    };

    AlignedAllocator() noexcept {}

    template<typename U>
    AlignedAllocator(const AlignedAllocator<U, Alignment>&) noexcept {}

    T* allocate(size_t n) {
        size_t size = ((n * sizeof(T) + Alignment - 1) / Alignment) * Alignment;
        void* ptr = std::aligned_alloc(Alignment, size);
        if (!ptr) throw std::bad_alloc();
        return static_cast<T*>(ptr);
    }

    void deallocate(T* ptr, size_t) noexcept {
        std::free(ptr);
    }

    template<typename U>
    bool operator==(const AlignedAllocator<U, Alignment>&) const { return true; }
    template<typename U>
    bool operator!=(const AlignedAllocator<U, Alignment>&) const { return false; }
};

void demonstrateAlignedAllocation() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 2: 对齐内存分配" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    constexpr size_t ALIGNMENT = 64;  // 缓存行对齐
    constexpr size_t COUNT = 1000;

    // 方法 1: C++17 对齐 new
    std::cout << "\n  方法 1: C++17 对齐 new (推荐)" << std::endl;
    {
        float* ptr = new (std::align_val_t{ALIGNMENT}) float[COUNT];
        std::cout << "    地址: " << (void*)ptr
                  << " (对齐: " << (reinterpret_cast<uintptr_t>(ptr) % ALIGNMENT == 0 ? "正确" : "错误") << ")" << std::endl;
        for (size_t i = 0; i < COUNT; ++i) ptr[i] = static_cast<float>(i);
        ::operator delete[](ptr, std::align_val_t{ALIGNMENT});
    }

    // 方法 2: std::aligned_alloc (C++17)
    std::cout << "\n  方法 2: std::aligned_alloc (C++17)" << std::endl;
    {
        size_t size = ((COUNT * sizeof(float) + ALIGNMENT - 1) / ALIGNMENT) * ALIGNMENT;
        void* ptr = std::aligned_alloc(ALIGNMENT, size);
        std::cout << "    地址: " << ptr
                  << " (对齐: " << (reinterpret_cast<uintptr_t>(ptr) % ALIGNMENT == 0 ? "正确" : "错误") << ")" << std::endl;
        std::free(ptr);
    }

    // 方法 3: 使用 aligned_allocator 的 vector
    std::cout << "\n  方法 3: 使用对齐分配器的 vector" << std::endl;
    {
        std::vector<float, AlignedAllocator<float, 64>> alignedVec(COUNT);
        for (size_t i = 0; i < COUNT; ++i) alignedVec[i] = static_cast<float>(i);
        std::cout << "    地址: " << (void*)alignedVec.data()
                  << " (对齐: " << (reinterpret_cast<uintptr_t>(alignedVec.data()) % 64 == 0 ? "正确" : "错误") << ")" << std::endl;
    }
}

// ============================================================================
// 演示 3: SIMD 操作中的对齐影响
// ============================================================================

/*
 * SIMD 指令对内存对齐有严格要求:
 * - SSE (_mm_load_ps): 要求 16 字节对齐
 * - AVX (_mm256_load_ps): 要求 32 字节对齐
 * - 未对齐加载 (_mm_loadu_ps) 通常更慢
 */

constexpr int SIMD_SIZE = 1000000;

void vectorAddAligned(const float* a, const float* b, float* c, int n) {
    for (int i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

void vectorAddUnaligned(const float* a, const float* b, float* c, int n) {
    for (int i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

void benchmarkSIMDAlignment() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 3: SIMD 操作中的对齐影响" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    const int ITERATIONS = 50;

    // 分配对齐内存 (32 字节对齐，兼容 AVX)
    float* a_aligned = new (std::align_val_t{32}) float[SIMD_SIZE];
    float* b_aligned = new (std::align_val_t{32}) float[SIMD_SIZE];
    float* c_aligned = new (std::align_val_t{32}) float[SIMD_SIZE];

    // 分配未对齐内存 (故意偏移 1 字节)
    char* raw_a = new char[SIMD_SIZE * sizeof(float) + 1];
    char* raw_b = new char[SIMD_SIZE * sizeof(float) + 1];
    char* raw_c = new char[SIMD_SIZE * sizeof(float) + 1];
    float* a_unaligned = reinterpret_cast<float*>(raw_a + 1);
    float* b_unaligned = reinterpret_cast<float*>(raw_b + 1);
    float* c_unaligned = reinterpret_cast<float*>(raw_c + 1);

    // 初始化数据
    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(0.0f, 1.0f);
    for (int i = 0; i < SIMD_SIZE; ++i) {
        a_aligned[i] = a_unaligned[i] = dist(rng);
        b_aligned[i] = b_unaligned[i] = dist(rng);
    }

    // 测试对齐版本
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            vectorAddAligned(a_aligned, b_aligned, c_aligned, SIMD_SIZE);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(c_aligned[0]);
        std::cout << std::setw(45) << std::left << "向量加法 (32字节对齐)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // 测试未对齐版本
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            vectorAddUnaligned(a_unaligned, b_unaligned, c_unaligned, SIMD_SIZE);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(c_unaligned[0]);
        std::cout << std::setw(45) << std::left << "向量加法 (1字节偏移未对齐)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // 清理
    ::operator delete[](a_aligned, std::align_val_t{32});
    ::operator delete[](b_aligned, std::align_val_t{32});
    ::operator delete[](c_aligned, std::align_val_t{32});
    delete[] raw_a;
    delete[] raw_b;
    delete[] raw_c;

    std::cout << "\n  说明: 对齐的影响取决于:" << std::endl;
    std::cout << "    - 编译器是否生成了对齐/未对齐指令" << std::endl;
    std::cout << "    - 是否跨越缓存行边界" << std::endl;
    std::cout << "    - SIMD 指令集的要求" << std::endl;
    std::cout << "    使用 -O2 或更高优化级别时，编译器通常能处理好对齐" << std::endl;
}

// ============================================================================
// 演示 4: 结构体填充优化
// ============================================================================

/*
 * 编译器会在结构体字段之间插入填充字节以满足对齐要求。
 * 合理排列字段可以显著减少内存浪费。
 */

// 最差排列: 大小交替，产生大量填充
struct WorstPadding {
    char a;       // 1 + 7 填充 = 8
    double b;     // 8
    char c;       // 1 + 3 填充 = 4
    int d;        // 4
    char e;       // 1 + 7 填充 = 8
    double f;     // 8
    char g;       // 1 + 3 填充 = 4
    int h;        // 4
};  // 总计: 48 字节 (数据 30 字节, 填充 18 字节)

// 最佳排列: 大到小排列
struct OptimalLayout {
    double b;     // 8 字节 - 高频访问
    double f;     // 8 字节
    int d;        // 4 字节
    int h;        // 4 字节
    char a;       // 1 字节
    char c;       // 1 字节
    char e;       // 1 字节
    char g;       // 1 字节
};  // 32 字节

void demonstrateStructPadding() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 4: 结构体填充优化" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::cout << "\n  结构体大小对比:" << std::endl;
    std::cout << "    WorstPadding:  " << sizeof(WorstPadding) << " 字节" << std::endl;
    std::cout << "    OptimalLayout: " << sizeof(OptimalLayout) << " 字节" << std::endl;
    std::cout << "    节省: " << (sizeof(WorstPadding) - sizeof(OptimalLayout)) << " 字节 ("
              << std::fixed << std::setprecision(1)
              << (1.0 - (double)sizeof(OptimalLayout) / sizeof(WorstPadding)) * 100 << "%)" << std::endl;

    // 详细分析内存布局
    std::cout << "\n  WorstPadding 内存布局:" << std::endl;
    std::cout << "    偏移 0:  a (char, 1字节)" << std::endl;
    std::cout << "    偏移 1-7: [填充 7 字节]" << std::endl;
    std::cout << "    偏移 8:  b (double, 8字节)" << std::endl;
    std::cout << "    偏移 16: c (char, 1字节)" << std::endl;
    std::cout << "    偏移 17-19: [填充 3 字节]" << std::endl;
    std::cout << "    偏移 20: d (int, 4字节)" << std::endl;
    std::cout << "    偏移 24: e (char, 1字节)" << std::endl;
    std::cout << "    偏移 25-31: [填充 7 字节]" << std::endl;
    std::cout << "    偏移 32: f (double, 8字节)" << std::endl;
    std::cout << "    偏移 40: g (char, 1字节)" << std::endl;
    std::cout << "    偏移 41-43: [填充 3 字节]" << std::endl;
    std::cout << "    偏移 44: h (int, 4字节)" << std::endl;

    std::cout << "\n  OptimalLayout 内存布局:" << std::endl;
    std::cout << "    偏移 0:  b (double, 8字节)" << std::endl;
    std::cout << "    偏移 8:  f (double, 8字节)" << std::endl;
    std::cout << "    偏移 16: d (int, 4字节)" << std::endl;
    std::cout << "    偏移 20: h (int, 4字节)" << std::endl;
    std::cout << "    偏移 24: a, c, e, g (char x 4, 4字节)" << std::endl;
    std::cout << "    偏移 28: [填充 4 字节到对齐边界]" << std::endl;

    // 性能影响: 数组中更多元素能放入缓存
    constexpr int ARRAY_SIZE = 1000000;
    std::cout << "\n  存储 " << ARRAY_SIZE << " 个元素时:" << std::endl;
    std::cout << "    WorstPadding:  " << (ARRAY_SIZE * sizeof(WorstPadding)) / (1024*1024) << " MB" << std::endl;
    std::cout << "    OptimalLayout: " << (ARRAY_SIZE * sizeof(OptimalLayout)) / (1024*1024) << " MB" << std::endl;
    std::cout << "    节省: " << (ARRAY_SIZE * (sizeof(WorstPadding) - sizeof(OptimalLayout))) / (1024*1024) << " MB" << std::endl;
}

// ============================================================================
// 演示 5: 对齐对缓存行跨越的影响
// ============================================================================

/*
 * 当数据结构跨越缓存行边界时:
 * 1. 需要加载两个缓存行而不是一个
 * 2. 原子操作可能无法在硬件级别完成
 * 3. 性能下降
 */

constexpr int CACHE_LINE = 64;

void benchmarkCacheLineCrossing() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 5: 缓存行跨越的影响" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    constexpr size_t BUFFER_SIZE = 1024 * 1024;  // 1MB
    char* buffer = new char[BUFFER_SIZE + CACHE_LINE];

    for (size_t i = 0; i < BUFFER_SIZE + CACHE_LINE; ++i) {
        buffer[i] = static_cast<char>(i & 0xFF);
    }

    constexpr int NUM_ACCESSES = 10000000;
    const int ITERATIONS = 20;

    // 对齐访问
    {
        long long sum = 0;
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            const int64_t* ptr = reinterpret_cast<const int64_t*>(buffer);
            for (int i = 0; i < NUM_ACCESSES / 8; ++i) {
                sum += ptr[i % (BUFFER_SIZE / 8)];
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(45) << std::left << "对齐的 int64 访问"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // 未对齐访问
    {
        long long sum = 0;
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            const int64_t* ptr = reinterpret_cast<const int64_t*>(buffer + 1);
            for (int i = 0; i < NUM_ACCESSES / 8; ++i) {
                sum += ptr[i % (BUFFER_SIZE / 8)];
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(45) << std::left << "未对齐的 int64 访问 (偏移1字节)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // 跨缓存行边界访问
    {
        long long sum = 0;
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            const int64_t* ptr = reinterpret_cast<const int64_t*>(buffer + CACHE_LINE - 4);
            for (int i = 0; i < NUM_ACCESSES / 8; ++i) {
                sum += ptr[i % (BUFFER_SIZE / 8)];
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(45) << std::left << "跨缓存行边界访问"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    delete[] buffer;
}

// ============================================================================
// 演示 6: 对齐友好的矩阵类
// ============================================================================

class AlignedMatrix {
    float* data_;
    size_t rows_, cols_;
    size_t padded_cols_;

public:
    AlignedMatrix(size_t rows, size_t cols)
        : rows_(rows), cols_(cols)
    {
        padded_cols_ = (cols + 7) & ~7;
        data_ = new (std::align_val_t{32}) float[rows * padded_cols_];
        std::memset(data_, 0, rows * padded_cols_ * sizeof(float));
    }

    ~AlignedMatrix() {
        ::operator delete[](data_, std::align_val_t{32});
    }

    AlignedMatrix(const AlignedMatrix&) = delete;
    AlignedMatrix& operator=(const AlignedMatrix&) = delete;

    float& operator()(size_t i, size_t j) { return data_[i * padded_cols_ + j]; }
    const float& operator()(size_t i, size_t j) const { return data_[i * padded_cols_ + j]; }

    float* row(size_t i) { return data_ + i * padded_cols_; }
    const float* row(size_t i) const { return data_ + i * padded_cols_; }

    size_t rows() const { return rows_; }
    size_t cols() const { return cols_; }
    size_t padded_cols() const { return padded_cols_; }

    static void multiply(const AlignedMatrix& a, const AlignedMatrix& b, AlignedMatrix& c) {
        assert(a.cols() == b.rows());
        assert(c.rows() == a.rows() && c.cols() == b.cols());

        for (size_t i = 0; i < a.rows(); ++i) {
            for (size_t k = 0; k < a.cols(); ++k) {
                float a_ik = a(i, k);
                for (size_t j = 0; j < b.cols(); ++j) {
                    c(i, j) += a_ik * b(k, j);
                }
            }
        }
    }
};

void benchmarkAlignedMatrix() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 6: 对齐友好的矩阵类" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    constexpr size_t N = 256;
    AlignedMatrix a(N, N), b(N, N), c(N, N);

    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(0.0f, 1.0f);
    for (size_t i = 0; i < N; ++i) {
        for (size_t j = 0; j < N; ++j) {
            a(i, j) = dist(rng);
            b(i, j) = dist(rng);
        }
    }

    std::cout << "  矩阵大小: " << N << "x" << N << std::endl;
    std::cout << "  填充列数: " << a.padded_cols() << " (原始: " << N << ")" << std::endl;
    std::cout << "  内存对齐: 32 字节 (兼容 AVX)" << std::endl;

    const int ITERATIONS = 5;

    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            for (size_t i = 0; i < N; ++i)
                for (size_t j = 0; j < N; ++j) c(i, j) = 0;

            auto start = std::chrono::high_resolution_clock::now();
            AlignedMatrix::multiply(a, b, c);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(c(0, 0));
        std::cout << std::setw(45) << std::left << "对齐矩阵乘法"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }
}

// ============================================================================
// 演示 7: std::assume_aligned (C++20)
// ============================================================================

void demonstrateAssumeAligned() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 7: std::assume_aligned (C++20)" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

#if __cplusplus >= 202002L
    constexpr size_t N = 1000000;
    float* data = new (std::align_val_t{32}) float[N];
    for (size_t i = 0; i < N; ++i) data[i] = static_cast<float>(i);

    float* p = std::assume_aligned<32>(data);

    float sum = 0;
    for (size_t i = 0; i < N; ++i) {
        sum += p[i];
    }
    doNotOptimize(sum);

    std::cout << "  std::assume_aligned<32> 已使用" << std::endl;
    std::cout << "  编译器可以利用对齐提示生成更高效的 SIMD 代码" << std::endl;

    ::operator delete[](data, std::align_val_t{32});
#else
    std::cout << "  当前编译器不支持 C++20，跳过此演示" << std::endl;
    std::cout << "  使用 -std=c++20 编译以启用此功能" << std::endl;
#endif
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "==============================================================" << std::endl;
    std::cout << "              内存对齐优化完整演示" << std::endl;
    std::cout << "==============================================================" << std::endl;

    demonstrateAlignas();
    demonstrateAlignedAllocation();
    benchmarkSIMDAlignment();
    demonstrateStructPadding();
    benchmarkCacheLineCrossing();
    benchmarkAlignedMatrix();
    demonstrateAssumeAligned();

    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "总结: 内存对齐优化要点" << std::endl;
    std::cout << std::string(70, '=') << std::endl;
    std::cout << "  1. 使用 alignas 确保关键数据结构的对齐" << std::endl;
    std::cout << "  2. 使用 C++17 对齐分配 (std::align_val_t) 分配对齐内存" << std::endl;
    std::cout << "  3. 按字段大小降序排列结构体成员，减少填充" << std::endl;
    std::cout << "  4. SIMD 操作需要特定的对齐 (SSE: 16B, AVX: 32B)" << std::endl;
    std::cout << "  5. 缓存行对齐 (64B) 可以避免伪共享" << std::endl;
    std::cout << "  6. C++20 的 std::assume_aligned 可以帮助编译器优化" << std::endl;
    std::cout << "  7. 对齐的内存访问可以避免跨缓存行边界的性能损失" << std::endl;

    return 0;
}
