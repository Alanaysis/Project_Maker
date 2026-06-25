/**
 * cache_friendly.cpp - 缓存友好的数据结构设计
 *
 * 核心思想：CPU 访问内存的速度远慢于计算速度。
 * L1 缓存命中约 1-4 周期，L2 约 10-20 周期，L3 约 40-75 周期，主存约 100-300 周期。
 * 通过优化数据布局和访问模式，最大化缓存命中率，可以大幅提升性能。
 *
 * 编译：g++ -std=c++17 -O2 -o cache_friendly cache_friendly.cpp
 */

#include <iostream>
#include <chrono>
#include <vector>
#include <numeric>
#include <random>
#include <algorithm>
#include <cstring>
#include <iomanip>
#include <new>  // for std::hardware_destructive_interference_size

// ============================================================================
// 1. Array of Structs (AoS) vs Struct of Arrays (SoA)
// ============================================================================
// 这是缓存优化中最经典的对比。

// AoS（结构体数组）—— 传统方式，面向对象风格
struct Particle_AoS {
    float x, y, z;      // 位置（12 字节）
    float vx, vy, vz;   // 速度（12 字节）
    float mass;          // 质量（4 字节）
    int id;              // ID（4 字节）
    // 总共 32 字节
};

// SoA（数组结构体）—— 缓存友好的布局
struct Particles_SoA {
    std::vector<float> x, y, z;       // 所有粒子的 x 坐标连续存储
    std::vector<float> vx, vy, vz;    // 所有粒子的 x 速度连续存储
    std::vector<float> mass;
    std::vector<int> id;

    void resize(size_t n) {
        x.resize(n); y.resize(n); z.resize(n);
        vx.resize(n); vy.resize(n); vz.resize(n);
        mass.resize(n); id.resize(n);
    }

    size_t size() const { return x.size(); }
};

// ============================================================================
// 2. 数据局部性示例 —— 行优先 vs 列优先访问
// ============================================================================
// C++ 的二维数组是行优先存储的（row-major）。
// 按行访问时缓存命中率高，按列访问时缓存命中率低。

constexpr int MATRIX_SIZE = 4096;

// 按行遍历（缓存友好）
long long sum_row_major(const int* matrix, int rows, int cols) {
    long long sum = 0;
    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < cols; ++j) {
            sum += matrix[i * cols + j];  // 连续内存访问
        }
    }
    return sum;
}

// 按列遍历（缓存不友好）
long long sum_col_major(const int* matrix, int rows, int cols) {
    long long sum = 0;
    for (int j = 0; j < cols; ++j) {
        for (int i = 0; i < rows; ++i) {
            sum += matrix[i * cols + j];  // 跳跃式内存访问，每次跳一整行
        }
    }
    return sum;
}

// ============================================================================
// 3. 缓存行对齐 —— 避免伪共享 (False Sharing)
// ============================================================================
// 缓存行通常为 64 字节。当两个线程修改同一缓存行中的不同变量时，
// 会导致缓存行在 CPU 核心之间反复失效，这就是"伪共享"。

// 未对齐的结构体 —— 可能导致伪共享
struct BadCounter {
    long long counter_a;  // 线程 A 修改
    long long counter_b;  // 线程 B 修改
    // 两个计数器可能在同一个缓存行中！
};

// 对齐的结构体 —— 避免伪共享
struct alignas(64) GoodCounter {
    long long counter_a;  // 线程 A 修改（独占一个缓存行）
};

struct alignas(64) GoodCounterB {
    long long counter_b;  // 线程 B 修改（独占另一个缓存行）
};

// C++17 提供的标准常量
#ifdef __cpp_lib_hardware_interference_size
    constexpr size_t CACHE_LINE_SIZE = std::hardware_destructive_interference_size;
#else
    constexpr size_t CACHE_LINE_SIZE = 64;  // 常见的缓存行大小
#endif

// 使用 C++17 标准方式对齐的计数器
struct alignas(CACHE_LINE_SIZE) AlignedCounter {
    long long value = 0;
    // 填充到缓存行大小
    char padding[CACHE_LINE_SIZE - sizeof(long long)];
};

// ============================================================================
// 4. 预取（Prefetch）提示
// ============================================================================
// 告诉 CPU 即将访问的内存地址，让 CPU 提前将数据加载到缓存。

#if defined(__GNUC__) || defined(__clang__)
    #define PREFETCH_READ(addr)  __builtin_prefetch((addr), 0, 3)
    #define PREFETCH_WRITE(addr) __builtin_prefetch((addr), 1, 3)
#else
    #define PREFETCH_READ(addr)  ((void)0)
    #define PREFETCH_WRITE(addr) ((void)0)
#endif

// 使用预取的数组求和
long long sum_with_prefetch(const int* arr, size_t n) {
    long long sum = 0;
    const size_t PREFETCH_DISTANCE = 64;  // 提前预取 64 个元素

    for (size_t i = 0; i < n; ++i) {
        // 提前预取未来的数据
        if (i + PREFETCH_DISTANCE < n) {
            PREFETCH_READ(&arr[i + PREFETCH_DISTANCE]);
        }
        sum += arr[i];
    }
    return sum;
}

// 不使用预取的数组求和
long long sum_without_prefetch(const int* arr, size_t n) {
    long long sum = 0;
    for (size_t i = 0; i < n; ++i) {
        sum += arr[i];
    }
    return sum;
}

// 预取在链表遍历中的应用
struct ListNode {
    int value;
    ListNode* next;
};

// 使用预取的链表求和
long long linked_list_sum_with_prefetch(ListNode* head) {
    long long sum = 0;
    ListNode* current = head;

    while (current != nullptr) {
        // 预取下一个节点（当 CPU 处理当前节点时，下一个节点已经在加载）
        if (current->next != nullptr) {
            PREFETCH_READ(current->next);
        }
        sum += current->value;
        current = current->next;
    }
    return sum;
}

// ============================================================================
// 5. 结构体打包 —— 减少内存占用，提高缓存利用率
// ============================================================================
// 通过合理排列结构体成员，减少内存对齐带来的填充浪费。

// 浪费空间的布局
struct BadLayout {
    char a;       // 1 字节 + 7 字节填充
    double b;     // 8 字节
    char c;       // 1 字节 + 3 字节填充
    int d;        // 4 字节
    char e;       // 1 字节 + 7 字节填充
    double f;     // 8 字节
    // 总共: 40 字节（含 18 字节填充）
};

// 优化后的布局（按大小降序排列）
struct GoodLayout {
    double b;     // 8 字节
    double f;     // 8 字节
    int d;        // 4 字节
    char a;       // 1 字节
    char c;       // 1 字节
    char e;       // 1 字节 + 1 字节填充
    // 总共: 24 字节（仅 1 字节填充）
};

// ============================================================================
// 6. 缓存友好的矩阵分块乘法
// ============================================================================
// 朴素矩阵乘法对缓存极不友好（大量 cache miss）。
// 分块（tiling/blocking）技术通过提高数据重用率来优化缓存性能。

// 朴素矩阵乘法（缓存不友好）
void matrix_multiply_naive(const float* A, const float* B, float* C, int N) {
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            float sum = 0;
            for (int k = 0; k < N; ++k) {
                sum += A[i * N + k] * B[k * N + j];  // B 的访问是列优先，缓存不友好
            }
            C[i * N + j] = sum;
        }
    }
}

// 分块矩阵乘法（缓存友好）
void matrix_multiply_blocked(const float* A, const float* B, float* C, int N) {
    constexpr int BLOCK_SIZE = 64;  // 分块大小（应适配 L1 缓存）

    // 先清零结果矩阵
    std::memset(C, 0, N * N * sizeof(float));

    for (int ii = 0; ii < N; ii += BLOCK_SIZE) {
        for (int jj = 0; jj < N; jj += BLOCK_SIZE) {
            for (int kk = 0; kk < N; kk += BLOCK_SIZE) {
                // 在分块内计算
                int i_end = std::min(ii + BLOCK_SIZE, N);
                int j_end = std::min(jj + BLOCK_SIZE, N);
                int k_end = std::min(kk + BLOCK_SIZE, N);

                for (int i = ii; i < i_end; ++i) {
                    for (int k = kk; k < k_end; ++k) {
                        float a_ik = A[i * N + k];
                        for (int j = jj; j < j_end; ++j) {
                            C[i * N + j] += a_ik * B[k * N + j];
                        }
                    }
                }
            }
        }
    }
}

// ============================================================================
// 辅助函数
// ============================================================================

template <typename T>
void do_not_optimize(T const& val) {
    #if defined(__GNUC__) || defined(__clang__)
        asm volatile("" : : "r,m"(val) : "memory");
    #else
        volatile T sink = val;
        (void)sink;
    #endif
}

// ============================================================================
// 主函数 —— 展示缓存友好的各种优化技巧
// ============================================================================

int main() {
    std::cout << "========================================\n";
    std::cout << "  缓存友好设计优化演示 (C++17)\n";
    std::cout << "========================================\n\n";

    // 显示缓存信息
    std::cout << "  缓存行大小: " << CACHE_LINE_SIZE << " 字节\n\n";

    // --- 1. AoS vs SoA ---
    std::cout << "【1. AoS vs SoA 性能对比】\n";

    const size_t NUM_PARTICLES = 10000000;

    // 初始化 AoS 数据
    std::vector<Particle_AoS> aos_particles(NUM_PARTICLES);
    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<float> dist(0.0f, 100.0f);
        for (auto& p : aos_particles) {
            p.x = dist(rng); p.y = dist(rng); p.z = dist(rng);
            p.vx = dist(rng); p.vy = dist(rng); p.vz = dist(rng);
            p.mass = dist(rng);
            p.id = static_cast<int>(dist(rng));
        }
    }

    // 初始化 SoA 数据
    Particles_SoA soa_particles;
    soa_particles.resize(NUM_PARTICLES);
    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<float> dist(0.0f, 100.0f);
        for (size_t i = 0; i < NUM_PARTICLES; ++i) {
            soa_particles.x[i] = dist(rng);
            soa_particles.y[i] = dist(rng);
            soa_particles.z[i] = dist(rng);
            soa_particles.vx[i] = dist(rng);
            soa_particles.vy[i] = dist(rng);
            soa_particles.vz[i] = dist(rng);
            soa_particles.mass[i] = dist(rng);
            soa_particles.id[i] = static_cast<int>(dist(rng));
        }
    }

    // 测试 AoS：更新所有粒子的位置（只需要 x, y, z）
    volatile float sink_f = 0;
    auto start = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < NUM_PARTICLES; ++i) {
        // AoS: 访问 x 时，缓存行中还加载了 vx, vy, vz, mass, id（浪费带宽）
        aos_particles[i].x += aos_particles[i].vx * 0.016f;
        aos_particles[i].y += aos_particles[i].vy * 0.016f;
        aos_particles[i].z += aos_particles[i].vz * 0.016f;
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto aos_ns = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
    sink_f = aos_particles[0].x;

    // 测试 SoA：更新所有粒子的位置
    start = std::chrono::high_resolution_clock::now();
    for (size_t i = 0; i < NUM_PARTICLES; ++i) {
        // SoA: 访问 x 时，缓存行中加载的全是 x 值（高效利用带宽）
        soa_particles.x[i] += soa_particles.vx[i] * 0.016f;
        soa_particles.y[i] += soa_particles.vy[i] * 0.016f;
        soa_particles.z[i] += soa_particles.vz[i] * 0.016f;
    }
    end = std::chrono::high_resolution_clock::now();
    auto soa_ns = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
    sink_f = soa_particles.x[0];

    std::cout << "  粒子位置更新（" << NUM_PARTICLES << " 个粒子）:\n";
    std::cout << "    AoS（结构体数组）: " << aos_ns << " ms\n";
    std::cout << "    SoA（数组结构体）: " << soa_ns << " ms\n";
    std::cout << "    加速比: " << std::setprecision(2)
              << static_cast<double>(aos_ns) / soa_ns << "x\n";
    std::cout << "  原因: SoA 布局下，x/y/z 坐标连续存储，缓存预取更高效\n\n";

    // --- 2. 行优先 vs 列优先 ---
    std::cout << "【2. 矩阵遍历：行优先 vs 列优先】\n";

    const int MAT_N = 2048;
    std::vector<int> matrix(MAT_N * MAT_N);
    std::iota(matrix.begin(), matrix.end(), 0);

    start = std::chrono::high_resolution_clock::now();
    long long sum_row = sum_row_major(matrix.data(), MAT_N, MAT_N);
    end = std::chrono::high_resolution_clock::now();
    auto row_ns = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

    start = std::chrono::high_resolution_clock::now();
    long long sum_col = sum_col_major(matrix.data(), MAT_N, MAT_N);
    end = std::chrono::high_resolution_clock::now();
    auto col_ns = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

    std::cout << "  " << MAT_N << "x" << MAT_N << " 矩阵求和:\n";
    std::cout << "    行优先遍历: " << row_ns << " ms (sum=" << sum_row << ")\n";
    std::cout << "    列优先遍历: " << col_ns << " ms (sum=" << sum_col << ")\n";
    std::cout << "    加速比: " << std::setprecision(2)
              << static_cast<double>(col_ns) / row_ns << "x\n";
    std::cout << "  原因: C++ 行优先存储，按行访问连续内存，按列访问每次跳跃一整行\n\n";

    // --- 3. 伪共享 ---
    std::cout << "【3. 伪共享 (False Sharing) 与缓存行对齐】\n";
    std::cout << "  sizeof(BadCounter)  = " << sizeof(BadCounter) << " 字节\n";
    std::cout << "  sizeof(GoodCounter) = " << sizeof(GoodCounter) << " 字节 (alignas(64))\n";
    std::cout << "  sizeof(AlignedCounter) = " << sizeof(AlignedCounter) << " 字节\n\n";

    std::cout << "  内存布局对比:\n";
    std::cout << "    BadCounter:  counter_a 和 counter_b 可能在同一缓存行\n";
    std::cout << "                 → 多线程修改时互相干扰\n";
    std::cout << "    GoodCounter: 每个计数器独占一个缓存行 (64 字节)\n";
    std::cout << "                 → 多线程修改时互不干扰\n\n";

    // 模拟伪共享的影响
    {
        BadCounter bad{};
        GoodCounter good_a{};
        GoodCounterB good_b{};
        const int ITERATIONS = 100000000;

        // 模拟"伪共享"场景（单线程，但展示布局差异）
        start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < ITERATIONS; ++i) {
            bad.counter_a += 1;
            bad.counter_b += 1;
        }
        end = std::chrono::high_resolution_clock::now();
        auto bad_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
        do_not_optimize(bad);

        start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < ITERATIONS; ++i) {
            good_a.counter_a += 1;
            good_b.counter_b += 1;
        }
        end = std::chrono::high_resolution_clock::now();
        auto good_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
        do_not_optimize(good_a);
        do_not_optimize(good_b);

        std::cout << "  单线程性能对比（" << ITERATIONS << " 次操作）:\n";
        std::cout << "    未对齐: " << bad_ns / 1000000.0 << " ms\n";
        std::cout << "    已对齐: " << good_ns / 1000000.0 << " ms\n";
        std::cout << "  （多线程场景下差异会更显著）\n\n";
    }

    // --- 4. 预取 ---
    std::cout << "【4. 内存预取 (Prefetch) 技巧】\n";

    const size_t PREFETCH_N = 50000000;
    std::vector<int> prefetch_data(PREFETCH_N);
    std::iota(prefetch_data.begin(), prefetch_data.end(), 1);

    start = std::chrono::high_resolution_clock::now();
    long long sum1 = sum_without_prefetch(prefetch_data.data(), PREFETCH_N);
    end = std::chrono::high_resolution_clock::now();
    auto no_prefetch_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();

    start = std::chrono::high_resolution_clock::now();
    long long sum2 = sum_with_prefetch(prefetch_data.data(), PREFETCH_N);
    end = std::chrono::high_resolution_clock::now();
    auto with_prefetch_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();

    std::cout << "  数组求和（" << PREFETCH_N << " 个元素）:\n";
    std::cout << "    无预取: " << no_prefetch_ns / 1000000.0 << " ms\n";
    std::cout << "    有预取: " << with_prefetch_ns / 1000000.0 << " ms\n";
    std::cout << "    结果一致: " << (sum1 == sum2 ? "是" : "否") << "\n";
    std::cout << "  预取在顺序访问时帮助较小（硬件预取器已足够智能）\n";
    std::cout << "  预取在随机访问/链表遍历时帮助更大\n\n";

    // --- 5. 结构体布局 ---
    std::cout << "【5. 结构体内存布局优化】\n";
    std::cout << "  sizeof(BadLayout)  = " << sizeof(BadLayout) << " 字节\n";
    std::cout << "  sizeof(GoodLayout) = " << sizeof(GoodLayout) << " 字节\n";
    std::cout << "  节省: " << sizeof(BadLayout) - sizeof(GoodLayout) << " 字节 ("
              << std::setprecision(0)
              << (1.0 - static_cast<double>(sizeof(GoodLayout)) / sizeof(BadLayout)) * 100
              << "%)\n";
    std::cout << "  原则: 将大成员放在前面，减少对齐填充\n\n";

    // --- 6. 矩阵乘法分块 ---
    std::cout << "【6. 矩阵乘法分块优化】\n";

    const int BLOCK_N = 512;  // 使用较小尺寸以便快速完成
    std::vector<float> A(BLOCK_N * BLOCK_N), B(BLOCK_N * BLOCK_N), C(BLOCK_N * BLOCK_N);

    // 初始化矩阵
    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        for (auto& a : A) a = dist(rng);
        for (auto& b : B) b = dist(rng);
    }

    start = std::chrono::high_resolution_clock::now();
    matrix_multiply_naive(A.data(), B.data(), C.data(), BLOCK_N);
    end = std::chrono::high_resolution_clock::now();
    auto naive_mult_ns = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

    start = std::chrono::high_resolution_clock::now();
    matrix_multiply_blocked(A.data(), B.data(), C.data(), BLOCK_N);
    end = std::chrono::high_resolution_clock::now();
    auto blocked_mult_ns = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();

    std::cout << "  " << BLOCK_N << "x" << BLOCK_N << " 矩阵乘法:\n";
    std::cout << "    朴素算法:   " << naive_mult_ns << " ms\n";
    std::cout << "    分块算法:   " << blocked_mult_ns << " ms\n";
    std::cout << "    加速比: " << std::setprecision(2)
              << static_cast<double>(naive_mult_ns) / blocked_mult_ns << "x\n";
    std::cout << "  分块大小: " << 64 << "（适配 L1 缓存大小）\n\n";

    // --- 总结 ---
    std::cout << "========================================\n";
    std::cout << "  总结：缓存友好的设计原则\n";
    std::cout << "========================================\n";
    std::cout << "  1. SoA 优于 AoS —— 当只需要访问部分字段时\n";
    std::cout << "  2. 按行优先遍历 —— 与 C++ 内存布局一致\n";
    std::cout << "  3. 避免伪共享   —— 多线程变量用 alignas(64) 隔离\n";
    std::cout << "  4. 使用预取     —— 在随机访问/链表遍历时提前加载数据\n";
    std::cout << "  5. 优化结构体布局 —— 按成员大小降序排列，减少填充\n";
    std::cout << "  6. 矩阵分块     —— 提高数据重用率，减少缓存失效\n";
    std::cout << "\n  记住: L1 缓存 ~4 周期, 主存 ~200+ 周期, 差距 50 倍！\n";

    (void)sink_f;
    return 0;
}
