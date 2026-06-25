/**
 * small_buffer_optimization.cpp - 小缓冲区优化 (SBO/SSO) 演示
 *
 * 本文件演示小缓冲区优化技术，包括：
 * 1. SBO (Small Buffer Optimization) 概念
 * 2. 实现一个简单的 SBO 字符串类
 * 3. SBO 向量类实现
 * 4. 与标准堆分配版本的性能对比
 * 5. std::string 的 SSO (Small String Optimization) 演示
 * 6. 最佳缓冲区大小选择
 *
 * 编译命令:
 *   g++ -std=c++17 -O2 -o small_buffer_optimization small_buffer_optimization.cpp
 *
 * 核心思想:
 *   将小对象直接存储在栈上的固定缓冲区中，避免堆分配。
 *   只有当数据超过内联缓冲区大小时，才回退到堆分配。
 *
 * 优势:
 *   1. 避免小对象的堆分配开销 (malloc 通常需要 50-200 ns)
 *   2. 栈内存访问更快，对缓存更友好
 *   3. 减少内存碎片
 *   4. 对于短字符串/小数组，性能提升显著
 *
 * std::string 的 SSO:
 *   GCC 的 std::string 在字符串长度 <= 15 时使用栈内缓冲区 (SSO)
 *   Clang 的 libc++ 在字符串长度 <= 22 时使用 SSO
 *   MSVC 的 std::string 在字符串长度 <= 15 时使用 SSO
 */

#include <chrono>
#include <iostream>
#include <iomanip>
#include <vector>
#include <string>
#include <cstring>
#include <cassert>
#include <algorithm>
#include <new>
#include <type_traits>
#include <memory>
#include <random>
#include <numeric>

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
        std::cout << std::setw(50) << std::left << name_
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
// SBO 字符串实现
// ============================================================================

/*
 * SBO 字符串: 小字符串直接存储在对象内部的栈缓冲区中。
 *
 * 内存布局 (小字符串模式, size <= N):
 * +------------------------------------------+
 * | size_ (1 byte) | buffer_[N] (N bytes)    |
 * +------------------------------------------+
 *
 * 内存布局 (大字符串模式, size > N):
 * +------------------------------------------+
 * | size_ (1 byte) | capacity_ | heap_ptr_   |
 * +------------------------------------------+
 * 数据存储在堆上
 */

template<size_t N = 23>
class SBOString {
    static_assert(N >= 7, "内联缓冲区至少需要 7 字节");

    char buffer_[N];    // 小字符串缓冲区
    char* heapPtr_;     // 堆指针 (大字符串模式)
    uint16_t size_;     // 当前长度
    uint16_t capacity_; // 容量 (小字符串时为 N)

    // 判断是否使用内联缓冲区
    bool isSmall() const {
        return capacity_ == N;
    }

    // 获取数据指针
    char* dataPtr() {
        return isSmall() ? buffer_ : heapPtr_;
    }
    const char* dataPtr() const {
        return isSmall() ? buffer_ : heapPtr_;
    }

public:
    // 默认构造
    SBOString() : size_(0), capacity_(N) {
        buffer_[0] = '\0';
        heapPtr_ = nullptr;
    }

    // 从 C 字符串构造
    SBOString(const char* str) {
        size_t len = std::strlen(str);
        if (len <= N) {
            std::memcpy(buffer_, str, len);
            buffer_[len] = '\0';
            size_ = static_cast<uint16_t>(len);
            capacity_ = N;
            heapPtr_ = nullptr;
        } else {
            capacity_ = static_cast<uint16_t>(len + 1);
            heapPtr_ = new char[capacity_];
            std::memcpy(heapPtr_, str, len + 1);
            size_ = static_cast<uint16_t>(len);
        }
    }

    // 析构
    ~SBOString() {
        if (!isSmall() && heapPtr_) {
            delete[] heapPtr_;
        }
    }

    // 拷贝构造
    SBOString(const SBOString& other) {
        size_ = other.size_;
        capacity_ = other.capacity_;
        if (isSmall()) {
            std::memcpy(buffer_, other.buffer_, N + 1);
            heapPtr_ = nullptr;
        } else {
            heapPtr_ = new char[capacity_];
            std::memcpy(heapPtr_, other.heapPtr_, size_ + 1);
        }
    }

    // 移动构造
    SBOString(SBOString&& other) noexcept {
        size_ = other.size_;
        capacity_ = other.capacity_;
        if (isSmall()) {
            std::memcpy(buffer_, other.buffer_, N + 1);
            heapPtr_ = nullptr;
        } else {
            heapPtr_ = other.heapPtr_;
            other.heapPtr_ = nullptr;
            other.size_ = 0;
            other.capacity_ = N;
            other.buffer_[0] = '\0';
        }
    }

    // 拷贝赋值
    SBOString& operator=(const SBOString& other) {
        if (this != &other) {
            this->~SBOString();
            new (this) SBOString(other);
        }
        return *this;
    }

    // 移动赋值
    SBOString& operator=(SBOString&& other) noexcept {
        if (this != &other) {
            this->~SBOString();
            new (this) SBOString(std::move(other));
        }
        return *this;
    }

    // 访问
    const char* c_str() const { return dataPtr(); }
    size_t size() const { return size_; }
    bool empty() const { return size_ == 0; }

    // 比较
    bool operator==(const SBOString& other) const {
        return size_ == other.size_ && std::strcmp(c_str(), other.c_str()) == 0;
    }

    // 获取内联缓冲区大小
    static constexpr size_t inlineCapacity() { return N; }

    // 判断是否使用堆
    bool usesHeap() const { return !isSmall(); }
};

// ============================================================================
// SBO 向量实现
// ============================================================================

/*
 * SBO 向量: 小数组直接存储在对象内部。
 * 只有当元素数量超过内联容量时，才分配堆内存。
 */

template<typename T, size_t N = 8>
class SBOVector {
    static_assert(N > 0, "内联容量必须大于 0");

    // 对齐的内联缓冲区
    alignas(T) unsigned char inlineBuffer_[N * sizeof(T)];
    T* data_;           // 数据指针 (指向内联缓冲区或堆)
    size_t size_;       // 当前元素数量
    size_t capacity_;   // 当前容量

    bool isSmall() const {
        return data_ == reinterpret_cast<const T*>(inlineBuffer_);
    }

    void ensureCapacity(size_t newCap) {
        if (newCap <= capacity_) return;

        T* newData = static_cast<T*>(::operator new(newCap * sizeof(T)));

        // 移动现有元素
        for (size_t i = 0; i < size_; ++i) {
            new (newData + i) T(std::move(data_[i]));
            data_[i].~T();
        }

        if (!isSmall()) {
            ::operator delete(data_);
        }

        data_ = newData;
        capacity_ = newCap;
    }

public:
    // 构造
    SBOVector() : size_(0), capacity_(N) {
        data_ = reinterpret_cast<T*>(inlineBuffer_);
    }

    // 析构
    ~SBOVector() {
        clear();
        if (!isSmall()) {
            ::operator delete(data_);
        }
    }

    // 拷贝构造
    SBOVector(const SBOVector& other) : size_(0), capacity_(N) {
        data_ = reinterpret_cast<T*>(inlineBuffer_);
        reserve(other.size_);
        for (size_t i = 0; i < other.size_; ++i) {
            new (data_ + i) T(other.data_[i]);
        }
        size_ = other.size_;
    }

    // 移动构造
    SBOVector(SBOVector&& other) noexcept : size_(0), capacity_(N) {
        if (other.isSmall()) {
            data_ = reinterpret_cast<T*>(inlineBuffer_);
            for (size_t i = 0; i < other.size_; ++i) {
                new (data_ + i) T(std::move(other.data_[i]));
            }
            size_ = other.size_;
        } else {
            data_ = other.data_;
            size_ = other.size_;
            capacity_ = other.capacity_;
            other.data_ = reinterpret_cast<T*>(other.inlineBuffer_);
            other.size_ = 0;
            other.capacity_ = N;
        }
    }

    // 预分配
    void reserve(size_t newCap) {
        if (newCap > capacity_) {
            ensureCapacity(newCap);
        }
    }

    // 添加元素
    void push_back(const T& value) {
        if (size_ >= capacity_) {
            ensureCapacity(capacity_ * 2);
        }
        new (data_ + size_) T(value);
        ++size_;
    }

    void push_back(T&& value) {
        if (size_ >= capacity_) {
            ensureCapacity(capacity_ * 2);
        }
        new (data_ + size_) T(std::move(value));
        ++size_;
    }

    // 原地构造
    template<typename... Args>
    T& emplace_back(Args&&... args) {
        if (size_ >= capacity_) {
            ensureCapacity(capacity_ * 2);
        }
        new (data_ + size_) T(std::forward<Args>(args)...);
        return data_[size_++];
    }

    // 访问
    T& operator[](size_t i) { return data_[i]; }
    const T& operator[](size_t i) const { return data_[i]; }
    size_t size() const { return size_; }
    size_t capacity() const { return capacity_; }
    bool empty() const { return size_ == 0; }
    T* data() { return data_; }
    const T* data() const { return data_; }

    // 清空
    void clear() {
        for (size_t i = 0; i < size_; ++i) {
            data_[i].~T();
        }
        size_ = 0;
    }

    // 迭代器
    T* begin() { return data_; }
    T* end() { return data_ + size_; }
    const T* begin() const { return data_; }
    const T* end() const { return data_ + size_; }

    // 是否使用堆
    bool usesHeap() const { return !isSmall(); }

    // 内联容量
    static constexpr size_t inlineCapacity() { return N; }
};

// ============================================================================
// 演示 1: SBO 字符串 vs 标准字符串性能对比
// ============================================================================

constexpr int STRING_OPS = 1000000;

void benchmarkSBOString() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 1: SBO 字符串 vs 标准字符串" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    // 短字符串场景 (长度 < 16，可内联)
    std::cout << "\n  场景: 短字符串操作 (长度 <= 15)" << std::endl;

    {
        Timer t("标准 std::string (短字符串)");
        size_t totalLen = 0;
        for (int i = 0; i < STRING_OPS; ++i) {
            std::string s("hello");
            s += " world";
            totalLen += s.size();
            doNotOptimize(s);
        }
        doNotOptimize(totalLen);
    }

    {
        Timer t("SBOString<23> (短字符串)");
        size_t totalLen = 0;
        for (int i = 0; i < STRING_OPS; ++i) {
            SBOString<23> s("hello world");
            totalLen += s.size();
            doNotOptimize(s);
        }
        doNotOptimize(totalLen);
    }

    // 中等长度字符串 (16-64 字节)
    std::cout << "\n  场景: 中等长度字符串 (32-64 字节)" << std::endl;

    {
        Timer t("标准 std::string (中等长度)");
        size_t totalLen = 0;
        for (int i = 0; i < STRING_OPS / 10; ++i) {
            std::string s(32 + (i % 32), 'A');
            s += "suffix";
            totalLen += s.size();
            doNotOptimize(s);
        }
        doNotOptimize(totalLen);
    }

    {
        Timer t("SBOString<64> (中等长度)");
        size_t totalLen = 0;
        for (int i = 0; i < STRING_OPS / 10; ++i) {
            std::string src(32 + (i % 32), 'A');
            SBOString<64> s(src.c_str());
            totalLen += s.size();
            doNotOptimize(s);
        }
        doNotOptimize(totalLen);
    }

    std::cout << "\n  说明:" << std::endl;
    std::cout << "    - std::string 本身已有 SSO (通常 <= 15 字节)" << std::endl;
    std::cout << "    - 自定义 SBO 字符串可以选择更大的内联缓冲区" << std::endl;
    std::cout << "    - 对于长度分布已知的场景，优化内联大小" << std::endl;
}

// ============================================================================
// 演示 2: SBO 向量 vs 标准向量
// ============================================================================

constexpr int VECTOR_OPS = 500000;

void benchmarkSBOVector() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 2: SBO 向量 vs 标准向量" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    // 小数组场景 (元素数量 <= 8)
    std::cout << "\n  场景: 小数组操作 (1-6 个元素)" << std::endl;

    {
        Timer t("标准 std::vector (小数组)");
        size_t totalSize = 0;
        for (int i = 0; i < VECTOR_OPS; ++i) {
            std::vector<int> v;
            v.reserve(4);
            for (int j = 0; j < 4; ++j) {
                v.push_back(j);
            }
            totalSize += v.size();
            doNotOptimize(v.data());
        }
        doNotOptimize(totalSize);
    }

    {
        Timer t("SBOVector<int,8> (小数组)");
        size_t totalSize = 0;
        for (int i = 0; i < VECTOR_OPS; ++i) {
            SBOVector<int, 8> v;
            for (int j = 0; j < 4; ++j) {
                v.push_back(j);
            }
            totalSize += v.size();
            doNotOptimize(v.data());
        }
        doNotOptimize(totalSize);
    }

    // 中等数组场景
    std::cout << "\n  场景: 中等数组操作 (10-20 个元素)" << std::endl;

    {
        Timer t("标准 std::vector (中等数组)");
        size_t totalSize = 0;
        for (int i = 0; i < VECTOR_OPS / 10; ++i) {
            std::vector<int> v;
            int count = 10 + (i % 10);
            v.reserve(count);
            for (int j = 0; j < count; ++j) {
                v.push_back(j);
            }
            totalSize += v.size();
            doNotOptimize(v.data());
        }
        doNotOptimize(totalSize);
    }

    {
        Timer t("SBOVector<int,16> (中等数组)");
        size_t totalSize = 0;
        for (int i = 0; i < VECTOR_OPS / 10; ++i) {
            SBOVector<int, 16> v;
            int count = 10 + (i % 10);
            for (int j = 0; j < count; ++j) {
                v.push_back(j);
            }
            totalSize += v.size();
            doNotOptimize(v.data());
        }
        doNotOptimize(totalSize);
    }
}

// ============================================================================
// 演示 3: std::string 的 SSO 行为分析
// ============================================================================

/*
 * 不同编译器的 SSO 实现:
 * - GCC (libstdc++): SSO 阈值 = 15 字节
 * - Clang (libc++): SSO 阈值 = 22 字节 (在 64 位系统上)
 * - MSVC: SSO 阈值 = 15 字节
 */

void demonstrateSSO() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 3: std::string 的 SSO 行为分析" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::cout << "\n  sizeof(std::string) = " << sizeof(std::string) << " 字节" << std::endl;

    // 测试不同长度字符串的分配行为
    std::cout << "\n  字符串长度 vs 内存分配行为:" << std::endl;
    std::cout << "  +--------+--------------+--------------------------+" << std::endl;
    std::cout << "  | 长度   | 使用 SSO     | 说明                     |" << std::endl;
    std::cout << "  +--------+--------------+--------------------------+" << std::endl;

    for (int len : {0, 1, 5, 10, 15, 16, 20, 22, 23, 30, 50, 100}) {
        std::string s(len, 'A');
        const char* cstr = s.c_str();
        const char* strAddr = reinterpret_cast<const char*>(&s);

        bool usesSSO = (cstr >= strAddr) && (cstr < strAddr + sizeof(std::string));

        std::cout << "  | " << std::setw(6) << len << " | "
                  << std::setw(12) << (usesSSO ? "是" : "否") << " | "
                  << std::setw(24) << (usesSSO ? "栈上存储" : "堆上分配") << " |" << std::endl;
    }
    std::cout << "  +--------+--------------+--------------------------+" << std::endl;

    // 性能对比: SSO 内 vs SSO 外
    std::cout << "\n  SSO 边界附近的性能差异:" << std::endl;

    constexpr int OPS = 500000;

    // 在 SSO 范围内 (15 字节)
    {
        Timer t("创建/销毁 15 字节字符串 (SSO 范围内)");
        for (int i = 0; i < OPS; ++i) {
            std::string s("0123456789abcde");  // 15 字节
            doNotOptimize(s.c_str());
        }
    }

    // 刚超过 SSO 范围 (16 字节)
    {
        Timer t("创建/销毁 16 字节字符串 (超出 SSO)");
        for (int i = 0; i < OPS; ++i) {
            std::string s("0123456789abcdef");  // 16 字节
            doNotOptimize(s.c_str());
        }
    }

    // 远超 SSO 范围 (64 字节)
    {
        Timer t("创建/销毁 64 字节字符串 (堆分配)");
        for (int i = 0; i < OPS; ++i) {
            std::string s(64, 'X');
            doNotOptimize(s.c_str());
        }
    }
}

// ============================================================================
// 演示 4: 最佳内联缓冲区大小选择
// ============================================================================

/*
 * 选择最佳内联缓冲区大小的策略:
 * 1. 分析实际使用中的数据大小分布
 * 2. 选择覆盖 80-90% 使用场景的大小
 * 3. 考虑对象总大小对缓存的影响
 * 4. 权衡栈空间使用和性能提升
 */

void benchmarkBufferSizeSelection() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 4: 最佳内联缓冲区大小选择" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    constexpr int NUM_STRINGS = 100000;
    std::vector<size_t> lengths(NUM_STRINGS);
    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<double> dist(0.0, 1.0);
        for (int i = 0; i < NUM_STRINGS; ++i) {
            if (dist(rng) < 0.8) {
                lengths[i] = 1 + static_cast<size_t>(dist(rng) * 19);  // 1-20
            } else {
                lengths[i] = 20 + static_cast<size_t>(dist(rng) * 80);  // 20-100
            }
        }
    }

    // 统计分布
    std::cout << "\n  字符串长度分布:" << std::endl;
    int ranges[] = {0, 8, 16, 24, 32, 64, 128};
    for (size_t r = 0; r < sizeof(ranges)/sizeof(ranges[0]) - 1; ++r) {
        int count = std::count_if(lengths.begin(), lengths.end(),
            [&](size_t l) { return l >= ranges[r] && l < ranges[r+1]; });
        double pct = 100.0 * count / NUM_STRINGS;
        std::cout << "    [" << std::setw(3) << ranges[r] << "-"
                  << std::setw(3) << ranges[r+1] << "): "
                  << std::setw(6) << count << " (" << std::fixed << std::setprecision(1)
                  << pct << "%)" << std::endl;
    }

    // 准备字符串内容
    std::vector<std::string> sourceStrings(NUM_STRINGS);
    for (int i = 0; i < NUM_STRINGS; ++i) {
        sourceStrings[i] = std::string(lengths[i], 'A' + (i % 26));
    }

    // 测试不同内联大小的性能
    std::cout << "\n  不同内联缓冲区大小的性能:" << std::endl;

    {
        Timer t("std::string (基准)");
        size_t totalLen = 0;
        for (int i = 0; i < NUM_STRINGS; ++i) {
            std::string s = sourceStrings[i];
            totalLen += s.size();
            doNotOptimize(s);
        }
        doNotOptimize(totalLen);
    }

    {
        Timer t("SBOString<8>");
        size_t totalLen = 0;
        for (int i = 0; i < NUM_STRINGS; ++i) {
            SBOString<8> s(sourceStrings[i].c_str());
            totalLen += s.size();
            doNotOptimize(s);
        }
        doNotOptimize(totalLen);
    }

    {
        Timer t("SBOString<16>");
        size_t totalLen = 0;
        for (int i = 0; i < NUM_STRINGS; ++i) {
            SBOString<16> s(sourceStrings[i].c_str());
            totalLen += s.size();
            doNotOptimize(s);
        }
        doNotOptimize(totalLen);
    }

    {
        Timer t("SBOString<24>");
        size_t totalLen = 0;
        for (int i = 0; i < NUM_STRINGS; ++i) {
            SBOString<24> s(sourceStrings[i].c_str());
            totalLen += s.size();
            doNotOptimize(s);
        }
        doNotOptimize(totalLen);
    }

    {
        Timer t("SBOString<32>");
        size_t totalLen = 0;
        for (int i = 0; i < NUM_STRINGS; ++i) {
            SBOString<32> s(sourceStrings[i].c_str());
            totalLen += s.size();
            doNotOptimize(s);
        }
        doNotOptimize(totalLen);
    }

    std::cout << "\n  对象大小比较:" << std::endl;
    std::cout << "    sizeof(std::string)    = " << sizeof(std::string) << " 字节" << std::endl;
    std::cout << "    sizeof(SBOString<8>)   = " << sizeof(SBOString<8>) << " 字节" << std::endl;
    std::cout << "    sizeof(SBOString<16>)  = " << sizeof(SBOString<16>) << " 字节" << std::endl;
    std::cout << "    sizeof(SBOString<24>)  = " << sizeof(SBOString<24>) << " 字节" << std::endl;
    std::cout << "    sizeof(SBOString<32>)  = " << sizeof(SBOString<32>) << " 字节" << std::endl;
}

// ============================================================================
// 演示 5: 小对象集合中的 SBO 效果
// ============================================================================

void benchmarkSmallObjectCollections() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 5: 小对象集合中的 SBO 效果" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    constexpr int NUM_ITEMS = 100000;

    // 生成短字符串数据
    std::vector<std::string> testData(NUM_ITEMS);
    std::mt19937 rng(42);
    for (int i = 0; i < NUM_ITEMS; ++i) {
        int len = 3 + (rng() % 12);  // 3-14 字节
        testData[i].resize(len);
        for (int j = 0; j < len; ++j) {
            testData[i][j] = 'A' + (rng() % 26);
        }
    }

    // std::vector<std::string>
    {
        Timer t("std::vector<std::string> (100K 短字符串)");
        std::vector<std::string> vec;
        vec.reserve(NUM_ITEMS);
        for (int i = 0; i < NUM_ITEMS; ++i) {
            vec.push_back(testData[i]);
        }
        doNotOptimize(vec.data());
    }

    // std::vector<SBOString<16>>
    {
        Timer t("std::vector<SBOString<16>> (100K 短字符串)");
        std::vector<SBOString<16>> vec;
        vec.reserve(NUM_ITEMS);
        for (int i = 0; i < NUM_ITEMS; ++i) {
            vec.push_back(SBOString<16>(testData[i].c_str()));
        }
        doNotOptimize(vec.data());
    }

    // 测试查找性能
    std::cout << "\n  查找性能对比 (在 100K 短字符串中查找):" << std::endl;

    std::vector<std::string> targets(1000);
    for (int i = 0; i < 1000; ++i) {
        targets[i] = testData[rng() % NUM_ITEMS];
    }

    // std::string 查找
    {
        std::vector<std::string> vec(testData.begin(), testData.end());
        int found = 0;
        Timer t("std::string 查找 1000 个目标");
        for (const auto& target : targets) {
            for (const auto& s : vec) {
                if (s == target) {
                    ++found;
                    break;
                }
            }
        }
        doNotOptimize(found);
    }

    // SBOString 查找
    {
        std::vector<SBOString<16>> vec;
        vec.reserve(NUM_ITEMS);
        for (const auto& s : testData) {
            vec.push_back(SBOString<16>(s.c_str()));
        }
        int found = 0;
        Timer t("SBOString<16> 查找 1000 个目标");
        for (const auto& target : targets) {
            SBOString<16> t(target.c_str());
            for (const auto& s : vec) {
                if (s == t) {
                    ++found;
                    break;
                }
            }
        }
        doNotOptimize(found);
    }
}

// ============================================================================
// 演示 6: SBO 的栈空间考虑
// ============================================================================

void demonstrateStackConsiderations() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 6: SBO 的栈空间考虑" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::cout << "\n  各种 SBO 对象的大小:" << std::endl;
    std::cout << "    SBOString<8>:   " << sizeof(SBOString<8>) << " 字节" << std::endl;
    std::cout << "    SBOString<16>:  " << sizeof(SBOString<16>) << " 字节" << std::endl;
    std::cout << "    SBOString<23>:  " << sizeof(SBOString<23>) << " 字节" << std::endl;
    std::cout << "    SBOString<32>:  " << sizeof(SBOString<32>) << " 字节" << std::endl;
    std::cout << "    SBOString<64>:  " << sizeof(SBOString<64>) << " 字节" << std::endl;
    std::cout << "    SBOString<128>: " << sizeof(SBOString<128>) << " 字节" << std::endl;

    std::cout << "\n  SBOVector<int> 的大小:" << std::endl;
    std::cout << "    SBOVector<int,4>:  " << sizeof(SBOVector<int, 4>) << " 字节" << std::endl;
    std::cout << "    SBOVector<int,8>:  " << sizeof(SBOVector<int, 8>) << " 字节" << std::endl;
    std::cout << "    SBOVector<int,16>: " << sizeof(SBOVector<int, 16>) << " 字节" << std::endl;
    std::cout << "    SBOVector<int,32>: " << sizeof(SBOVector<int, 32>) << " 字节" << std::endl;

    std::cout << "\n  栈空间使用建议:" << std::endl;
    std::cout << "    - 默认栈大小通常为 1-8 MB" << std::endl;
    std::cout << "    - 单个 SBO 对象建议不超过 64-128 字节" << std::endl;
    std::cout << "    - 避免在递归函数中使用大 SBO 对象" << std::endl;
    std::cout << "    - 考虑对象在容器中的数量" << std::endl;

    constexpr size_t STACK_LIMIT = 1024 * 1024;  // 1 MB
    std::cout << "\n  在 1 MB 栈空间中可容纳的 SBO 对象数量:" << std::endl;
    std::cout << "    SBOString<8>:   ~" << STACK_LIMIT / sizeof(SBOString<8>) << " 个" << std::endl;
    std::cout << "    SBOString<16>:  ~" << STACK_LIMIT / sizeof(SBOString<16>) << " 个" << std::endl;
    std::cout << "    SBOString<23>:  ~" << STACK_LIMIT / sizeof(SBOString<23>) << " 个" << std::endl;
    std::cout << "    SBOString<64>:  ~" << STACK_LIMIT / sizeof(SBOString<64>) << " 个" << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "==============================================================" << std::endl;
    std::cout << "            小缓冲区优化 (SBO/SSO) 完整演示" << std::endl;
    std::cout << "==============================================================" << std::endl;

    benchmarkSBOString();
    benchmarkSBOVector();
    demonstrateSSO();
    benchmarkBufferSizeSelection();
    benchmarkSmallObjectCollections();
    demonstrateStackConsiderations();

    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "总结: 小缓冲区优化要点" << std::endl;
    std::cout << std::string(70, '=') << std::endl;
    std::cout << "  1. SBO 将小对象存储在栈上，避免堆分配开销" << std::endl;
    std::cout << "  2. std::string 已有 SSO (GCC/MSVC: <= 15 字节, Clang: <= 22 字节)" << std::endl;
    std::cout << "  3. 自定义 SBO 类可以选择更大的内联缓冲区" << std::endl;
    std::cout << "  4. 选择内联大小时分析实际数据分布" << std::endl;
    std::cout << "  5. 覆盖 80-90% 使用场景的大小通常是最佳选择" << std::endl;
    std::cout << "  6. 注意栈空间限制，单个对象建议不超过 64-128 字节" << std::endl;
    std::cout << "  7. SBO 对象的移动语义需要特殊处理" << std::endl;
    std::cout << "  8. alignas + placement new 是实现 SBO 的关键技术" << std::endl;

    return 0;
}
