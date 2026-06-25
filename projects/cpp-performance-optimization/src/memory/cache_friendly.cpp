/**
 * cache_friendly.cpp - 缓存友好的数据访问模式演示
 *
 * 本文件演示了 CPU 缓存对程序性能的重大影响，包括：
 * 1. 行优先 vs 列优先矩阵遍历
 * 2. 数组 vs 链表遍历性能对比
 * 3. 缓存行填充（False Sharing / 伪共享）
 * 4. 数据局部性对查找性能的影响
 * 5. 结构体内存布局优化
 * 6. 遍历步长对缓存的影响
 *
 * 编译命令:
 *   g++ -std=c++17 -O2 -o cache_friendly cache_friendly.cpp
 *
 * 关键概念:
 *   - CPU 缓存行通常为 64 字节
 *   - 空间局部性(Spatial Locality): 访问某个地址后，其附近地址很可能被访问
 *   - 时间局部性(Temporal Locality): 最近访问的数据很可能再次被访问
 *   - L1 缓存延迟约 1-4 周期，L2 约 10-20 周期，L3 约 30-50 周期，主存约 100-300 周期
 */

#include <chrono>
#include <iostream>
#include <iomanip>
#include <vector>
#include <list>
#include <random>
#include <numeric>
#include <algorithm>
#include <cstring>
#include <cassert>

// ============================================================================
// 辅助计时工具
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
        std::cout << std::setw(40) << std::left << name_
                  << ": " << std::setw(10) << std::right << duration.count()
                  << " us" << std::endl;
    }

    long long elapsed() const {
        auto end = std::chrono::high_resolution_clock::now();
        return std::chrono::duration_cast<std::chrono::microseconds>(end - start_).count();
    }
};

// 防止编译器优化掉计算结果
template<typename T>
void doNotOptimize(T&& value) {
    asm volatile("" : : "r,m"(value) : "memory");
}

// ============================================================================
// 演示 1: 行优先 vs 列优先矩阵遍历
// ============================================================================

/*
 * C/C++ 中多维数组在内存中按行优先(Row-Major)存储。
 * 按行遍历时，内存访问是连续的，对缓存友好。
 * 按列遍历时，每次访问跳跃一整行，导致频繁的缓存未命中(Cache Miss)。
 *
 * 内存布局示例 (3x3 矩阵):
 *   行优先存储: [a00, a01, a02, a10, a11, a12, a20, a21, a22]
 *   按行访问:   a00 -> a01 -> a02 -> a10 -> a11 -> a12 (连续，缓存友好)
 *   按列访问:   a00 -> a10 -> a20 -> a01 -> a11 -> a21 (跳跃，缓存不友好)
 */

constexpr int MATRIX_SIZE = 4096;

// 使用一维数组模拟二维矩阵，避免额外的间接寻址
static std::vector<int> matrix;

void initMatrix() {
    matrix.resize(MATRIX_SIZE * MATRIX_SIZE);
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> dist(1, 100);
    for (auto& val : matrix) {
        val = dist(rng);
    }
}

// 行优先遍历（缓存友好）- 顺序访问内存
long long sumRowMajor() {
    long long sum = 0;
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        for (int j = 0; j < MATRIX_SIZE; ++j) {
            // 内存地址: base + (i * MATRIX_SIZE + j) * sizeof(int)
            // 相邻 j 值的地址相差 sizeof(int) = 4 字节，连续访问
            sum += matrix[i * MATRIX_SIZE + j];
        }
    }
    return sum;
}

// 列优先遍历（缓存不友好）- 跳跃访问内存
long long sumColumnMajor() {
    long long sum = 0;
    for (int j = 0; j < MATRIX_SIZE; ++j) {
        for (int i = 0; i < MATRIX_SIZE; ++i) {
            // 内存地址: base + (i * MATRIX_SIZE + j) * sizeof(int)
            // 相邻 i 值的地址相差 MATRIX_SIZE * sizeof(int) = 16384 字节
            // 远超缓存行大小(64字节)，导致频繁缓存未命中
            sum += matrix[i * MATRIX_SIZE + j];
        }
    }
    return sum;
}

void benchmarkMatrixTraversal() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 1: 行优先 vs 列优先矩阵遍历 (" << MATRIX_SIZE << "x" << MATRIX_SIZE << ")" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    initMatrix();

    // 预热缓存
    volatile long long warmup = sumRowMajor();
    (void)warmup;

    long long sum1, sum2;

    {
        Timer t("行优先遍历 (Row-Major)");
        sum1 = sumRowMajor();
        doNotOptimize(sum1);
    }

    {
        Timer t("列优先遍历 (Column-Major)");
        sum2 = sumColumnMajor();
        doNotOptimize(sum2);
    }

    // 验证结果一致性
    assert(sum1 == sum2);
    std::cout << "  结果验证: 两种遍历方式计算结果一致" << std::endl;
    std::cout << "  说明: 列优先遍历通常比行优先慢 3-10 倍，取决于矩阵大小和缓存层次" << std::endl;
}

// ============================================================================
// 演示 2: 数组 vs 链表遍历性能
// ============================================================================

/*
 * 链表的每个节点分散在堆内存的不同位置，遍历时指针跳跃导致:
 * 1. 缓存未命中率极高（每个节点可能在不同的缓存行）
 * 2. 硬件预取器无法预测下一个节点的位置
 * 3. 指针追踪(Pointer Chasing)成为性能瓶颈
 *
 * 而 std::vector 的元素在内存中连续存储，遍历时:
 * 1. 缓存预取(Cache Prefetch)效果极佳
 * 2. 每个缓存行(64字节)可容纳多个元素
 * 3. CPU 可以进行指令级并行优化
 */

constexpr int CONTAINER_SIZE = 1000000;

struct ListNode {
    int value;
    ListNode* next;
    // 填充到 64 字节，模拟真实场景中较大的节点
    char padding[64 - sizeof(int) - sizeof(ListNode*)];
};

void benchmarkContainerTraversal() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 2: 数组 vs 链表遍历性能 (" << CONTAINER_SIZE << " 个元素)" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    // 准备随机数据
    std::vector<int> data(CONTAINER_SIZE);
    std::mt19937 rng(42);
    std::iota(data.begin(), data.end(), 0);
    std::shuffle(data.begin(), data.end(), rng);

    // --- 创建 vector ---
    std::vector<int> vec(data.begin(), data.end());

    // --- 创建链表 ---
    std::vector<ListNode> nodePool(CONTAINER_SIZE);
    ListNode* head = nullptr;
    for (int i = CONTAINER_SIZE - 1; i >= 0; --i) {
        nodePool[i].value = data[i];
        nodePool[i].next = head;
        head = &nodePool[i];
    }

    const int ITERATIONS = 10;

    // --- 遍历 vector ---
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            long long sum = 0;
            for (int i = 0; i < CONTAINER_SIZE; ++i) {
                sum += vec[i];
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(40) << std::left << "vector 遍历 (连续内存)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // --- 遍历链表 ---
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            long long sum = 0;
            ListNode* curr = head;
            while (curr) {
                sum += curr->value;
                curr = curr->next;
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(40) << std::left << "链表遍历 (指针追踪)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    std::cout << "  说明: 即使链表节点连续分配，vector 仍然更快" << std::endl;
    std::cout << "  在真实堆分配场景下，差距可达 5-20 倍" << std::endl;
}

// ============================================================================
// 演示 3: 缓存行填充（False Sharing / 伪共享）
// ============================================================================

/*
 * 伪共享(False Sharing)是多线程编程中的性能杀手。
 * 当两个线程修改不同的变量，但这些变量恰好在同一个缓存行中时，
 * 缓存一致性协议(MESI)会导致缓存行在核之间反复无效化和传输。
 *
 * 解决方案: 使用 alignas 或填充字节确保每个变量独占一个缓存行。
 */

constexpr size_t CACHE_LINE_SIZE = 64;
constexpr int ITERATIONS_COUNTER = 10000000;

// 未对齐的计数器结构
struct UnalignedCounters {
    int64_t counter1;  // 8 字节
    int64_t counter2;  // 8 字节
};

// 缓存行对齐的计数器结构
struct AlignedCounters {
    alignas(CACHE_LINE_SIZE) int64_t counter1;
    alignas(CACHE_LINE_SIZE) int64_t counter2;
};

void benchmarkCacheLinePadding() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 3: 缓存行对齐与伪共享" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::cout << "\n  结构体大小比较:" << std::endl;
    std::cout << "    UnalignedCounters: " << sizeof(UnalignedCounters) << " 字节" << std::endl;
    std::cout << "    AlignedCounters:   " << sizeof(AlignedCounters) << " 字节" << std::endl;
    std::cout << "    缓存行大小:        " << CACHE_LINE_SIZE << " 字节" << std::endl;

    {
        AlignedCounters ac{0, 0};
        UnalignedCounters uc{0, 0};

        {
            Timer t("连续访问 (未对齐)");
            for (int i = 0; i < ITERATIONS_COUNTER; ++i) {
                uc.counter1 += 1;
                uc.counter2 += 1;
            }
            doNotOptimize(uc.counter1);
            doNotOptimize(uc.counter2);
        }

        {
            Timer t("连续访问 (缓存行对齐)");
            for (int i = 0; i < ITERATIONS_COUNTER; ++i) {
                ac.counter1 += 1;
                ac.counter2 += 1;
            }
            doNotOptimize(ac.counter1);
            doNotOptimize(ac.counter2);
        }
    }

    std::cout << "\n  说明: 在单线程场景下差异不大，但在多线程场景中:" << std::endl;
    std::cout << "    - 未对齐: 两个线程修改不同变量会导致伪共享，性能下降 5-100 倍" << std::endl;
    std::cout << "    - 对齐后: 每个线程独占缓存行，无伪共享，性能接近线性扩展" << std::endl;
}

// ============================================================================
// 演示 4: 结构体内存布局优化
// ============================================================================

/*
 * 结构体的字段排列顺序也会影响缓存效率:
 * 1. 将频繁访问的字段放在一起
 * 2. 避免不必要的填充(Padding)
 * 3. 考虑缓存行边界
 */

// 不好的设计: 字段随意排列，造成大量填充
struct BadLayout {
    char a;         // 1 字节 + 7 字节填充
    double b;       // 8 字节
    char c;         // 1 字节 + 3 字节填充
    int d;          // 4 字节
    char e;         // 1 字节 + 7 字节填充
    double f;       // 8 字节
};  // 总计: 40 字节（含 18 字节填充）

// 好的设计: 按大小排列字段，减少填充
struct GoodLayout {
    double b;       // 8 字节
    double f;       // 8 字节
    int d;          // 4 字节
    char a;         // 1 字节
    char c;         // 1 字节
    char e;         // 1 字节 + 1 字节填充
};  // 总计: 24 字节（含 1 字节填充）

// 最好的设计: 考虑访问模式 + 减少填充
struct BestLayout {
    double b;       // 8 字节 - 高频访问
    int d;          // 4 字节 - 高频访问
    char a;         // 1 字节 - 高频访问
    char c;         // 1 字节 - 中频访问
    char e;         // 1 字节 - 低频访问
    // 1 字节自然填充到 8 字节边界
    double f;       // 8 字节 - 低频访问
};  // 总计: 24 字节

void benchmarkStructLayout() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 4: 结构体内存布局优化" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::cout << "\n  结构体大小比较:" << std::endl;
    std::cout << "    BadLayout:  " << sizeof(BadLayout) << " 字节 (填充率: "
              << std::fixed << std::setprecision(1)
              << (1.0 - 22.0 / sizeof(BadLayout)) * 100 << "% 浪费)" << std::endl;
    std::cout << "    GoodLayout: " << sizeof(GoodLayout) << " 字节 (填充率: "
              << (1.0 - 22.0 / sizeof(GoodLayout)) * 100 << "% 浪费)" << std::endl;
    std::cout << "    BestLayout: " << sizeof(BestLayout) << " 字节" << std::endl;

    constexpr int STRUCT_COUNT = 1000000;
    constexpr int ACCESS_ITERATIONS = 10;

    std::vector<BadLayout> badVec(STRUCT_COUNT);
    std::vector<GoodLayout> goodVec(STRUCT_COUNT);
    std::vector<BestLayout> bestVec(STRUCT_COUNT);

    for (int i = 0; i < STRUCT_COUNT; ++i) {
        badVec[i] = {static_cast<char>(i), static_cast<double>(i),
                      static_cast<char>(i), i, static_cast<char>(i), static_cast<double>(i)};
        goodVec[i] = {static_cast<double>(i), static_cast<double>(i),
                       i, static_cast<char>(i), static_cast<char>(i), static_cast<char>(i)};
        bestVec[i] = {static_cast<double>(i), i, static_cast<char>(i),
                       static_cast<char>(i), static_cast<char>(i), static_cast<double>(i)};
    }

    // 测试: 遍历时只访问高频字段 (b 和 d)
    {
        long long sum = 0;
        Timer t("BadLayout - 访问高频字段");
        for (int iter = 0; iter < ACCESS_ITERATIONS; ++iter) {
            for (int i = 0; i < STRUCT_COUNT; ++i) {
                sum += static_cast<long long>(badVec[i].b) + badVec[i].d;
            }
        }
        doNotOptimize(sum);
    }

    {
        long long sum = 0;
        Timer t("GoodLayout - 访问高频字段");
        for (int iter = 0; iter < ACCESS_ITERATIONS; ++iter) {
            for (int i = 0; i < STRUCT_COUNT; ++i) {
                sum += static_cast<long long>(goodVec[i].b) + goodVec[i].d;
            }
        }
        doNotOptimize(sum);
    }

    {
        long long sum = 0;
        Timer t("BestLayout - 访问高频字段");
        for (int iter = 0; iter < ACCESS_ITERATIONS; ++iter) {
            for (int i = 0; i < STRUCT_COUNT; ++i) {
                sum += static_cast<long long>(bestVec[i].b) + bestVec[i].d;
            }
        }
        doNotOptimize(sum);
    }

    std::cout << "\n  优化建议:" << std::endl;
    std::cout << "    1. 按字段大小降序排列（double > int > short > char）" << std::endl;
    std::cout << "    2. 将频繁访问的字段放在结构体开头" << std::endl;
    std::cout << "    3. 使用 static_assert 检查结构体大小" << std::endl;
}

// ============================================================================
// 演示 5: 遍历步长对缓存的影响
// ============================================================================

/*
 * 即使是顺序访问，步长(Stride)也会影响缓存效率。
 * 步长为 1 时，每个缓存行(64字节)可以服务 16 个 int 元素。
 * 步长增大时，每个缓存行只能服务更少的元素，浪费带宽。
 */

constexpr int STRIDE_TEST_SIZE = 1 << 20;  // 1M 元素

void benchmarkStrideImpact() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 5: 遍历步长对缓存利用率的影响" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::vector<int> data(STRIDE_TEST_SIZE, 1);
    const int ITERATIONS = 20;

    int strides[] = {1, 2, 4, 8, 16, 32, 64, 128};

    for (int stride : strides) {
        long long totalUs = 0;
        long long sum = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            for (int i = 0; i < STRIDE_TEST_SIZE; i += stride) {
                sum += data[i];
            }
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(sum);

        double cacheLineUtil = std::min(stride, 16) / 16.0 * 100.0;  // 每个缓存行 16 个 int
        std::cout << "  步长 " << std::setw(4) << stride
                  << " | 平均耗时: " << std::setw(8) << (totalUs / ITERATIONS) << " us"
                  << " | 缓存行利用率: " << std::fixed << std::setprecision(1)
                  << cacheLineUtil << "%" << std::endl;
    }

    std::cout << "\n  说明: 步长越大，每次缓存加载的有效数据比例越低" << std::endl;
    std::cout << "  一个缓存行(64字节)可容纳 16 个 int，步长 > 16 时利用率低于 100%" << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "==============================================================" << std::endl;
    std::cout << "          CPU 缓存友好的数据访问模式演示" << std::endl;
    std::cout << "==============================================================" << std::endl;

    benchmarkMatrixTraversal();
    benchmarkContainerTraversal();
    benchmarkCacheLinePadding();
    benchmarkStructLayout();
    benchmarkStrideImpact();

    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "总结: 缓存友好的代码优化要点" << std::endl;
    std::cout << std::string(70, '=') << std::endl;
    std::cout << "  1. 优先使用连续内存容器(vector/array)而非链式容器(list/map)" << std::endl;
    std::cout << "  2. 按行优先顺序遍历多维数组" << std::endl;
    std::cout << "  3. 使用 alignas 避免多线程伪共享" << std::endl;
    std::cout << "  4. 优化结构体字段排列，减少填充并提高局部性" << std::endl;
    std::cout << "  5. 尽量使用单位步长(stride=1)访问数据" << std::endl;
    std::cout << "  6. 考虑使用 SoA(Structure of Arrays)替代 AoS(Array of Structures)" << std::endl;

    return 0;
}
