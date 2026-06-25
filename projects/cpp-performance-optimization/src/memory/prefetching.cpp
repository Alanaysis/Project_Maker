/**
 * prefetching.cpp - 软件预取与硬件预取器优化演示
 *
 * 本文件演示 CPU 预取机制对内存密集型程序的影响，包括：
 * 1. 软件预取 (__builtin_prefetch) 的使用
 * 2. 顺序访问 vs 随机访问模式
 * 3. 预取距离的优化
 * 4. 硬件预取器的行为特征
 * 5. 预取在链表遍历中的应用
 *
 * 编译命令:
 *   g++ -std=c++17 -O2 -o prefetching prefetching.cpp
 *
 * 关键概念:
 *   - 硬件预取器: CPU 自动检测访问模式并提前加载数据
 *   - 软件预取: 程序员显式提示 CPU 提前加载数据
 *   - 预取距离: 提前多少次迭代进行预取
 *   - 预取指令不会阻塞执行，但如果预取太早或太晚都会失效
 *
 * __builtin_prefetch 语法:
 *   __builtin_prefetch(addr, rw, locality)
 *   - addr: 预取地址
 *   - rw: 0=读取(默认), 1=写入
 *   - locality: 0=无时间局部性, 1=低, 2=中, 3=高(默认)
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
#include <cstdint>

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
// 演示 1: 顺序访问中的软件预取
// ============================================================================

/*
 * 对于顺序访问，硬件预取器通常能够很好地工作。
 * 但在某些情况下，软件预取仍然有帮助:
 * 1. 每次迭代的计算量较大时
 * 2. 数据量超过硬件预取器的工作范围
 * 3. 需要访问非连续的内存区域
 */

constexpr int ARRAY_SIZE = 10000000;  // 10M 元素

void benchmarkSequentialPrefetch() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 1: 顺序访问中的软件预取" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::vector<float> data(ARRAY_SIZE);
    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(0.0f, 1.0f);
    for (int i = 0; i < ARRAY_SIZE; ++i) {
        data[i] = dist(rng);
    }

    const int ITERATIONS = 10;

    // 无预取: 依赖硬件预取器
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            float sum = 0;
            for (int i = 0; i < ARRAY_SIZE; ++i) {
                sum += data[i] * data[i];
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(50) << std::left << "顺序访问 (无软件预取，依赖硬件预取器)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // 有软件预取: 提前预取数据
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            float sum = 0;
            constexpr int PREFETCH_DISTANCE = 64;
            for (int i = 0; i < ARRAY_SIZE; ++i) {
                if (i + PREFETCH_DISTANCE < ARRAY_SIZE) {
                    __builtin_prefetch(&data[i + PREFETCH_DISTANCE], 0, 3);
                }
                sum += data[i] * data[i];
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(50) << std::left << "顺序访问 (软件预取距离=64)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    std::cout << "\n  说明: 对于简单的顺序访问，硬件预取器通常足够高效。" << std::endl;
    std::cout << "  软件预取在计算密集的循环中可能带来额外收益。" << std::endl;
}

// ============================================================================
// 演示 2: 随机访问中的预取效果
// ============================================================================

/*
 * 随机访问模式下，硬件预取器无法预测下一个访问地址。
 * 此时软件预取可以通过分析访问模式来提前加载数据。
 */

constexpr int RANDOM_SIZE = 1000000;
constexpr int NUM_RANDOM_LOOKUPS = 500000;

void benchmarkRandomAccess() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 2: 随机访问中的预取效果" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::vector<int> indices(NUM_RANDOM_LOOKUPS);
    {
        std::mt19937 rng(42);
        std::uniform_int_distribution<int> dist(0, RANDOM_SIZE - 1);
        for (int i = 0; i < NUM_RANDOM_LOOKUPS; ++i) {
            indices[i] = dist(rng);
        }
    }

    std::vector<double> data(RANDOM_SIZE);
    for (int i = 0; i < RANDOM_SIZE; ++i) data[i] = static_cast<double>(i);

    const int ITERATIONS = 20;

    // 无预取的随机访问
    {
        double sum = 0;
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            double s = 0;
            for (int i = 0; i < NUM_RANDOM_LOOKUPS; ++i) {
                s += data[indices[i]];
            }
            doNotOptimize(s);
            sum = s;
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(50) << std::left << "随机访问 (无预取)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // 有预取的随机访问
    {
        double sum = 0;
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            double s = 0;
            constexpr int PREFETCH_AHEAD = 8;
            for (int i = 0; i < std::min(PREFETCH_AHEAD, NUM_RANDOM_LOOKUPS); ++i) {
                __builtin_prefetch(&data[indices[i]], 0, 0);
            }
            for (int i = 0; i < NUM_RANDOM_LOOKUPS; ++i) {
                if (i + PREFETCH_AHEAD < NUM_RANDOM_LOOKUPS) {
                    __builtin_prefetch(&data[indices[i + PREFETCH_AHEAD]], 0, 0);
                }
                s += data[indices[i]];
            }
            doNotOptimize(s);
            sum = s;
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(50) << std::left << "随机访问 (软件预取距离=8)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // 预排序
    {
        auto sorted_indices = indices;
        std::sort(sorted_indices.begin(), sorted_indices.end());

        double sum = 0;
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            double s = 0;
            for (int i = 0; i < NUM_RANDOM_LOOKUPS; ++i) {
                s += data[sorted_indices[i]];
            }
            doNotOptimize(s);
            sum = s;
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(50) << std::left << "排序后的顺序访问 (硬件预取器友好)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }
}

// ============================================================================
// 演示 3: 预取距离优化
// ============================================================================

/*
 * 预取距离是软件预取的关键参数:
 * - 太近: 数据已经在缓存中，预取无效
 * - 太远: 预取的数据可能在使用前被驱逐出缓存
 * - 最佳距离取决于内存延迟和每次迭代的计算时间
 */

constexpr int PREFETCH_TEST_SIZE = 5000000;

void benchmarkPrefetchDistance() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 3: 预取距离对性能的影响" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::vector<float> data(PREFETCH_TEST_SIZE);
    std::mt19937 rng(42);
    for (int i = 0; i < PREFETCH_TEST_SIZE; ++i) {
        data[i] = static_cast<float>(rng()) / rng.max();
    }

    const int ITERATIONS = 15;
    int distances[] = {0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512};

    std::cout << "\n  模拟计算密集型操作 (每个元素做多次运算)" << std::endl;

    for (int dist : distances) {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            float sum = 0;
            for (int i = 0; i < PREFETCH_TEST_SIZE; ++i) {
                if (dist > 0 && i + dist < PREFETCH_TEST_SIZE) {
                    __builtin_prefetch(&data[i + dist], 0, 3);
                }
                float v = data[i];
                sum += v * v + v;
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }

        std::string label = (dist == 0) ? "无预取"
                            : "预取距离=" + std::to_string(dist);
        std::cout << "  " << std::setw(25) << std::left << label
                  << " 平均: " << std::setw(8) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    std::cout << "\n  说明: 最佳预取距离取决于:" << std::endl;
    std::cout << "    - 内存延迟 (L3 ~100 周期, 主存 ~300 周期)" << std::endl;
    std::cout << "    - 每次迭代的计算量" << std::endl;
    std::cout << "    - 数据大小和缓存容量" << std::endl;
    std::cout << "    通常需要通过实验找到最佳值" << std::endl;
}

// ============================================================================
// 演示 4: 链表遍历中的预取优化
// ============================================================================

/*
 * 链表遍历是指针追踪(Pointer Chasing)的典型场景。
 * 每个节点的位置不可预测，硬件预取器无能为力。
 * 软件预取可以在处理当前节点时预取下一个节点。
 */

struct PrefetchNode {
    int value;
    PrefetchNode* next;
    char data[48];  // 填充到 64 字节，模拟真实节点大小
};

constexpr int LIST_SIZE = 100000;

void benchmarkLinkedListPrefetch() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 4: 链表遍历中的预取优化" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    // 创建随机顺序的链表节点池
    std::vector<PrefetchNode> nodePool(LIST_SIZE);
    {
        for (int i = 0; i < LIST_SIZE; ++i) {
            nodePool[i].value = i;
            nodePool[i].next = nullptr;
        }
        std::vector<int> order(LIST_SIZE);
        std::iota(order.begin(), order.end(), 0);
        std::mt19937 rng(42);
        std::shuffle(order.begin(), order.end(), rng);

        for (int i = 0; i < LIST_SIZE - 1; ++i) {
            nodePool[order[i]].next = &nodePool[order[i + 1]];
        }
        nodePool[order[LIST_SIZE - 1]].next = nullptr;
    }

    PrefetchNode* head = &nodePool[0];

    const int ITERATIONS = 100;

    // 无预取的链表遍历
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            long long sum = 0;
            PrefetchNode* curr = head;
            while (curr) {
                sum += curr->value;
                curr = curr->next;
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(50) << std::left << "链表遍历 (无预取)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // 有预取的链表遍历
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            long long sum = 0;
            PrefetchNode* curr = head;
            while (curr) {
                if (curr->next) {
                    __builtin_prefetch(curr->next, 0, 1);
                    if (curr->next->next) {
                        __builtin_prefetch(curr->next->next, 0, 0);
                    }
                }
                sum += curr->value;
                curr = curr->next;
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(50) << std::left << "链表遍历 (预取 next 和 next->next)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // 连续内存链表
    {
        std::vector<PrefetchNode> contiguousPool(LIST_SIZE);
        for (int i = 0; i < LIST_SIZE; ++i) {
            contiguousPool[i].value = i;
            contiguousPool[i].next = (i + 1 < LIST_SIZE) ? &contiguousPool[i + 1] : nullptr;
        }

        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            long long sum = 0;
            PrefetchNode* curr = &contiguousPool[0];
            while (curr) {
                sum += curr->value;
                curr = curr->next;
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(50) << std::left << "连续内存链表遍历 (硬件预取器友好)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }
}

// ============================================================================
// 演示 5: 写入预取
// ============================================================================

constexpr int WRITE_TEST_SIZE = 5000000;

void benchmarkWritePrefetch() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 5: 写入预取优化" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::vector<int> src(WRITE_TEST_SIZE);
    std::vector<int> dst(WRITE_TEST_SIZE);
    std::mt19937 rng(42);
    for (int i = 0; i < WRITE_TEST_SIZE; ++i) {
        src[i] = rng();
    }

    const int ITERATIONS = 20;

    // 无预取的写入
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            for (int i = 0; i < WRITE_TEST_SIZE; ++i) {
                dst[i] = src[i] * 2 + 1;
            }
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(dst[0]);
        std::cout << std::setw(50) << std::left << "批量写入 (无预取)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // 有预取的写入
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            constexpr int PF_DIST = 64;
            for (int i = 0; i < WRITE_TEST_SIZE; ++i) {
                if (i + PF_DIST < WRITE_TEST_SIZE) {
                    __builtin_prefetch(&src[i + PF_DIST], 0, 1);
                    __builtin_prefetch(&dst[i + PF_DIST], 1, 1);
                }
                dst[i] = src[i] * 2 + 1;
            }
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(dst[0]);
        std::cout << std::setw(50) << std::left << "批量写入 (预取 src 和 dst，距离=64)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }
}

// ============================================================================
// 演示 6: 矩阵运算中的预取
// ============================================================================

constexpr int MAT_SIZE = 512;

void benchmarkMatrixPrefetch() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 6: 矩阵运算中的预取优化" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::vector<std::vector<float>> A(MAT_SIZE, std::vector<float>(MAT_SIZE));
    std::vector<std::vector<float>> B(MAT_SIZE, std::vector<float>(MAT_SIZE));
    std::vector<std::vector<float>> C(MAT_SIZE, std::vector<float>(MAT_SIZE, 0));

    std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(0.0f, 1.0f);
    for (int i = 0; i < MAT_SIZE; ++i) {
        for (int j = 0; j < MAT_SIZE; ++j) {
            A[i][j] = dist(rng);
            B[i][j] = dist(rng);
        }
    }

    const int ITERATIONS = 3;

    // 标准矩阵乘法
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            for (int i = 0; i < MAT_SIZE; ++i)
                for (int j = 0; j < MAT_SIZE; ++j) C[i][j] = 0;

            auto start = std::chrono::high_resolution_clock::now();
            for (int i = 0; i < MAT_SIZE; ++i) {
                for (int k = 0; k < MAT_SIZE; ++k) {
                    float a_ik = A[i][k];
                    for (int j = 0; j < MAT_SIZE; ++j) {
                        C[i][j] += a_ik * B[k][j];
                    }
                }
            }
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(C[0][0]);
        std::cout << std::setw(50) << std::left << "矩阵乘法 (标准 ikj 顺序)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // 带预取的分块矩阵乘法
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            for (int i = 0; i < MAT_SIZE; ++i)
                for (int j = 0; j < MAT_SIZE; ++j) C[i][j] = 0;

            auto start = std::chrono::high_resolution_clock::now();
            constexpr int BLOCK = 32;
            for (int i = 0; i < MAT_SIZE; i += BLOCK) {
                for (int k = 0; k < MAT_SIZE; k += BLOCK) {
                    for (int j = 0; j < MAT_SIZE; j += BLOCK) {
                        int iEnd = std::min(i + BLOCK, MAT_SIZE);
                        int kEnd = std::min(k + BLOCK, MAT_SIZE);
                        int jEnd = std::min(j + BLOCK, MAT_SIZE);

                        for (int ii = i; ii < iEnd; ++ii) {
                            for (int kk = k; kk < kEnd; ++kk) {
                                if (kk + BLOCK < kEnd) {
                                    __builtin_prefetch(&A[ii][kk + BLOCK], 0, 3);
                                    __builtin_prefetch(&B[kk + BLOCK][j], 0, 3);
                                }
                                float a_ik = A[ii][kk];
                                for (int jj = j; jj < jEnd; ++jj) {
                                    C[ii][jj] += a_ik * B[kk][jj];
                                }
                            }
                        }
                    }
                }
            }
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(C[0][0]);
        std::cout << std::setw(50) << std::left << "矩阵乘法 (分块+预取, BLOCK=32)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }
}

// ============================================================================
// 演示 7: 预取的局部性提示
// ============================================================================

/*
 * __builtin_prefetch 的第三个参数 locality 控制数据在缓存中的保留策略:
 * - 0: 无时间局部性 (Non-temporal)，使用后立即驱逐
 * - 1: 低时间局部性
 * - 2: 中等时间局部性
 * - 3: 高时间局部性 (默认)
 */

constexpr int LOCALITY_TEST_SIZE = 5000000;

void benchmarkLocalityHints() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 7: 预取局部性提示" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::vector<double> data(LOCALITY_TEST_SIZE);
    std::mt19937 rng(42);
    for (int i = 0; i < LOCALITY_TEST_SIZE; ++i) {
        data[i] = static_cast<double>(rng()) / rng.max();
    }

    const int ITERATIONS = 15;

    // locality=0
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            double sum = 0;
            for (int i = 0; i < LOCALITY_TEST_SIZE; ++i) {
                if (i + 32 < LOCALITY_TEST_SIZE) {
                    __builtin_prefetch(&data[i + 32], 0, 0);
                }
                sum += data[i];
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(50) << std::left << "locality=0 (Non-temporal，不污染缓存)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // locality=3
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            double sum = 0;
            for (int i = 0; i < LOCALITY_TEST_SIZE; ++i) {
                if (i + 32 < LOCALITY_TEST_SIZE) {
                    __builtin_prefetch(&data[i + 32], 0, 3);
                }
                sum += data[i];
            }
            doNotOptimize(sum);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(50) << std::left << "locality=3 (高时间局部性，保留在缓存)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    std::cout << "\n  局部性提示使用建议:" << std::endl;
    std::cout << "    - 单次扫描数据: locality=0，避免污染工作集缓存" << std::endl;
    std::cout << "    - 会被多次访问的数据: locality=3，尽可能保留在 L1/L2" << std::endl;
    std::cout << "    - 介于两者之间: locality=1 或 2" << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "==============================================================" << std::endl;
    std::cout << "            软件预取与硬件预取器优化演示" << std::endl;
    std::cout << "==============================================================" << std::endl;

    benchmarkSequentialPrefetch();
    benchmarkRandomAccess();
    benchmarkPrefetchDistance();
    benchmarkLinkedListPrefetch();
    benchmarkWritePrefetch();
    benchmarkMatrixPrefetch();
    benchmarkLocalityHints();

    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "总结: 预取优化要点" << std::endl;
    std::cout << std::string(70, '=') << std::endl;
    std::cout << "  1. 顺序访问: 依赖硬件预取器，软件预取收益有限" << std::endl;
    std::cout << "  2. 随机访问: 软件预取可以提前 8-64 个元素" << std::endl;
    std::cout << "  3. 链表遍历: 预取 next 节点可提升 20-50% 性能" << std::endl;
    std::cout << "  4. 预取距离: 需要实验确定，通常 16-128" << std::endl;
    std::cout << "  5. 写入预取: rw=1 可预取即将写入的内存" << std::endl;
    std::cout << "  6. 局部性提示: 单次访问用 locality=0，重用数据用 locality=3" << std::endl;
    std::cout << "  7. 过度预取会浪费缓存带宽，适度使用" << std::endl;

    return 0;
}
