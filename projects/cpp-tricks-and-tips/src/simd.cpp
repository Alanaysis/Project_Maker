/**
 * simd.cpp - SIMD 向量化优化技巧
 *
 * 核心思想：SIMD（Single Instruction, Multiple Data）让一条指令同时处理多个数据。
 * 现代 CPU 支持 SSE（128 位）、AVX2（256 位）、AVX-512（512 位）等指令集。
 * 一条 AVX2 指令可以同时处理 8 个 float 或 4 个 double。
 *
 * 编译：g++ -std=c++17 -O2 -mavx2 -o simd simd.cpp
 *       g++ -std=c++17 -O2 -march=native -o simd simd.cpp  (使用本机所有指令集)
 */

#include <iostream>
#include <chrono>
#include <vector>
#include <random>
#include <numeric>
#include <cmath>
#include <cstring>
#include <iomanip>
#include <algorithm>

// 检测 SIMD 支持
#if defined(__AVX512F__)
    #define SIMD_WIDTH "AVX-512 (512-bit)"
    #define SIMD_FLOATS 16
#elif defined(__AVX2__)
    #define SIMD_WIDTH "AVX2 (256-bit)"
    #define SIMD_FLOATS 8
#elif defined(__SSE2__)
    #define SIMD_WIDTH "SSE2 (128-bit)"
    #define SIMD_FLOATS 4
#else
    #define SIMD_WIDTH "无 SIMD"
    #define SIMD_FLOATS 1
#endif

// ============================================================================
// 1. 自动向量化 —— 让编译器自动生成 SIMD 代码
// ============================================================================
// 编译器在 -O2/-O3 下会自动尝试向量化简单的循环。
// 关键是写出"对编译器友好"的循环模式。

// 编译器可以自动向量化的简单循环
void vector_add_auto(const float* a, const float* b, float* c, size_t n) {
    // 这个循环的模式非常适合自动向量化：
    // - 无循环依赖
    // - 连续内存访问
    // - 简单的算术运算
    for (size_t i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

// 编译器可能无法自动向量化的版本（有循环依赖）
void vector_add_dependency(const float* a, const float* b, float* c, size_t n) {
    // 前缀和：c[i] 依赖于 c[i-1]，编译器无法向量化
    c[0] = a[0] + b[0];
    for (size_t i = 1; i < n; ++i) {
        c[i] = c[i - 1] + a[i] + b[i];  // 循环依赖！
    }
}

// 手动消除循环依赖后可以向量化
void vector_add_no_dependency(const float* a, const float* b, float* c, size_t n) {
    // 先计算独立的加法（可向量化）
    for (size_t i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
    // 再计算前缀和（必须串行）
    for (size_t i = 1; i < n; ++i) {
        c[i] += c[i - 1];
    }
}

// ============================================================================
// 2. 编译器向量化提示
// ============================================================================

// GCC/Clang 的向量化提示
#if defined(__GNUC__) || defined(__clang__)
    // 提示编译器循环可以安全向量化（无别名问题）
    #define ASSUME_ALIGNED(ptr, align) __builtin_assume_aligned(ptr, align)
    #define RESTRICT __restrict__
#else
    #define ASSUME_ALIGNED(ptr, align) (ptr)
    #define RESTRICT
#endif

// 使用 restrict 指针和对齐提示的向量加法
void vector_add_hinted(const float* RESTRICT a,
                       const float* RESTRICT b,
                       float* RESTRICT c,
                       size_t n) {
    // restrict 告诉编译器：a, b, c 不会指向重叠的内存
    // 这让编译器可以安全地进行向量化

    // 确保指针对齐（假设调用者已对齐分配）
    a = static_cast<const float*>(ASSUME_ALIGNED(a, 32));
    b = static_cast<const float*>(ASSUME_ALIGNED(b, 32));
    c = static_cast<float*>(ASSUME_ALIGNED(c, 32));

    for (size_t i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

// OpenMP 向量化提示
void vector_add_omp(const float* a, const float* b, float* c, size_t n) {
    #pragma omp simd
    for (size_t i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

// ============================================================================
// 3. 常见的 SIMD 优化模式
// ============================================================================

// 模式 1：向量点积
float dot_product_scalar(const float* a, const float* b, size_t n) {
    float sum = 0;
    for (size_t i = 0; i < n; ++i) {
        sum += a[i] * b[i];
    }
    return sum;
}

// 模式 2：向量乘加 (FMA) —— a[i] * b[i] + c[i]
void vector_fma(const float* a, const float* b, const float* c, float* result, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        result[i] = a[i] * b[i] + c[i];  // 编译器可能生成 FMA 指令
    }
}

// 模式 3：向量归约（求和）
float vector_sum(const float* arr, size_t n) {
    float sum = 0;
    // 使用多个累加器来打破依赖链，提高向量化效率
    float sum0 = 0, sum1 = 0, sum2 = 0, sum3 = 0;
    size_t i = 0;

    // 主循环：4 路展开
    for (; i + 3 < n; i += 4) {
        sum0 += arr[i];
        sum1 += arr[i + 1];
        sum2 += arr[i + 2];
        sum3 += arr[i + 3];
    }

    // 处理剩余元素
    for (; i < n; ++i) {
        sum0 += arr[i];
    }

    return sum0 + sum1 + sum2 + sum3;
}

// 简单的标量求和（用于对比）
float vector_sum_scalar(const float* arr, size_t n) {
    float sum = 0;
    for (size_t i = 0; i < n; ++i) {
        sum += arr[i];
    }
    return sum;
}

// 模式 4：向量距离计算
float euclidean_distance(const float* a, const float* b, size_t n) {
    float sum = 0;
    for (size_t i = 0; i < n; ++i) {
        float diff = a[i] - b[i];
        sum += diff * diff;
    }
    return std::sqrt(sum);
}

// 模式 5：向量缩放和平移
void vector_scale_add(const float* src, float scale, float offset, float* dst, size_t n) {
    for (size_t i = 0; i < n; ++i) {
        dst[i] = src[i] * scale + offset;
    }
}

// ============================================================================
// 4. 手动 SIMD 编程（使用编译器内建函数）
// ============================================================================
// 当自动向量化不够时，可以使用 intrinsics 手动编写 SIMD 代码。
// 这里展示概念，实际使用需要包含 <immintrin.h> 等头文件。

// 手动 AVX2 向量加法的伪代码（注释形式展示）
/*
#include <immintrin.h>

void vector_add_avx2(const float* a, const float* b, float* c, size_t n) {
    size_t i = 0;

    // 处理 8 个 float 一组（256 位）
    for (; i + 8 <= n; i += 8) {
        __m256 va = _mm256_loadu_ps(&a[i]);   // 加载 8 个 float
        __m256 vb = _mm256_loadu_ps(&b[i]);   // 加载 8 个 float
        __m256 vc = _mm256_add_ps(va, vb);    // 8 个加法同时执行
        _mm256_storeu_ps(&c[i], vc);           // 存储 8 个结果
    }

    // 处理剩余元素
    for (; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}
*/

// ============================================================================
// 5. SIMD 友好的数据布局
// ============================================================================
// 数据布局对 SIMD 效率影响很大。

// 结构体数组 (AoS) —— SIMD 不友好
struct Color_AoS {
    float r, g, b, a;
};

// 数组结构体 (SoA) —— SIMD 友好
struct Colors_SoA {
    std::vector<float> r, g, b, a;

    void resize(size_t n) {
        r.resize(n); g.resize(n); b.resize(n); a.resize(n);
    }
};

// AoS 版本的颜色亮度调整
void adjust_brightness_AoS(Color_AoS* colors, size_t n, float factor) {
    for (size_t i = 0; i < n; ++i) {
        colors[i].r *= factor;
        colors[i].g *= factor;
        colors[i].b *= factor;
        // alpha 不变
    }
}

// SoA 版本的颜色亮度调整（SIMD 友好）
void adjust_brightness_SoA(Colors_SoA& colors, size_t n, float factor) {
    // 每个颜色通道都是连续的，编译器可以轻松向量化
    for (size_t i = 0; i < n; ++i) {
        colors.r[i] *= factor;
    }
    for (size_t i = 0; i < n; ++i) {
        colors.g[i] *= factor;
    }
    for (size_t i = 0; i < n; ++i) {
        colors.b[i] *= factor;
    }
}

// ============================================================================
// 6. 条件处理的 SIMD 优化 —— 使用掩码代替分支
// ============================================================================

// 有分支版本
void threshold_branched(float* data, size_t n, float threshold, float replacement) {
    for (size_t i = 0; i < n; ++i) {
        if (data[i] < threshold) {
            data[i] = replacement;
        }
    }
}

// 无分支版本（SIMD 友好）
void threshold_branchless(float* data, size_t n, float threshold, float replacement) {
    for (size_t i = 0; i < n; ++i) {
        // 使用比较结果作为掩码，避免分支
        float mask = (data[i] < threshold) ? 1.0f : 0.0f;
        // 混合：如果 mask=1 则用 replacement，否则保持原值
        data[i] = data[i] * (1.0f - mask) + replacement * mask;
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

// 对齐内存分配（SIMD 需要对齐的内存访问）
class AlignedAllocator {
public:
    static float* allocate(size_t n) {
        void* ptr = nullptr;
        #if defined(_MSC_VER)
            ptr = _aligned_malloc(n * sizeof(float), 32);
        #else
            posix_memalign(&ptr, 32, n * sizeof(float));
        #endif
        return static_cast<float*>(ptr);
    }

    static void deallocate(float* ptr) {
        #if defined(_MSC_VER)
            _aligned_free(ptr);
        #else
            free(ptr);
        #endif
    }
};

// ============================================================================
// 主函数 —— 展示 SIMD 向量化的各种技巧
// ============================================================================

int main() {
    std::cout << "========================================\n";
    std::cout << "  SIMD 向量化优化演示 (C++17)\n";
    std::cout << "========================================\n\n";

    std::cout << "  检测到的 SIMD 指令集: " << SIMD_WIDTH << "\n";
    std::cout << "  每条指令处理 " << SIMD_FLOATS << " 个 float\n\n";

    const size_t N = 10000000;

    // 分配对齐内存
    float* a = AlignedAllocator::allocate(N);
    float* b = AlignedAllocator::allocate(N);
    float* c = AlignedAllocator::allocate(N);

    // 初始化数据
    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        for (size_t i = 0; i < N; ++i) {
            a[i] = dist(rng);
            b[i] = dist(rng);
        }
    }

    auto start = std::chrono::high_resolution_clock::now();
    auto end = std::chrono::high_resolution_clock::now();

    // --- 1. 自动向量化 ---
    std::cout << "【1. 自动向量化】\n";

    // 基础向量加法（编译器自动向量化）
    start = std::chrono::high_resolution_clock::now();
    vector_add_auto(a, b, c, N);
    end = std::chrono::high_resolution_clock::now();
    auto auto_vec_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    do_not_optimize(c[0]);

    // 带提示的向量加法
    start = std::chrono::high_resolution_clock::now();
    vector_add_hinted(a, b, c, N);
    end = std::chrono::high_resolution_clock::now();
    auto hinted_vec_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    do_not_optimize(c[0]);

    std::cout << "  向量加法（" << N << " 个 float）:\n";
    std::cout << "    自动向量化:    " << auto_vec_ns / 1000.0 << " μs\n";
    std::cout << "    带提示向量化:  " << hinted_vec_ns / 1000.0 << " μs\n\n";

    // --- 2. 多路展开求和 ---
    std::cout << "【2. 多路展开归约（打破依赖链）】\n";

    start = std::chrono::high_resolution_clock::now();
    float sum_scalar = vector_sum_scalar(a, N);
    end = std::chrono::high_resolution_clock::now();
    auto sum_scalar_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    do_not_optimize(sum_scalar);

    start = std::chrono::high_resolution_clock::now();
    float sum_unrolled = vector_sum(a, N);
    end = std::chrono::high_resolution_clock::now();
    auto sum_unrolled_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    do_not_optimize(sum_unrolled);

    std::cout << "  数组求和（" << N << " 个 float）:\n";
    std::cout << "    标量版本:      " << sum_scalar_ns / 1000.0 << " μs\n";
    std::cout << "    4路展开版本:   " << sum_unrolled_ns / 1000.0 << " μs\n";
    std::cout << "    加速比: " << std::setprecision(2)
              << static_cast<double>(sum_scalar_ns) / sum_unrolled_ns << "x\n";
    std::cout << "    结果: scalar=" << sum_scalar << ", unrolled=" << sum_unrolled << "\n\n";

    // --- 3. 向量点积 ---
    std::cout << "【3. 向量点积（乘法+归约）】\n";

    start = std::chrono::high_resolution_clock::now();
    float dot = dot_product_scalar(a, b, N);
    end = std::chrono::high_resolution_clock::now();
    auto dot_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    do_not_optimize(dot);

    std::cout << "  点积（" << N << " 个 float）: " << dot_ns / 1000.0 << " μs\n";
    std::cout << "  结果: " << dot << "\n";
    std::cout << "  编译器会自动生成 FMA (Fused Multiply-Add) 指令\n\n";

    // --- 4. FMA 运算 ---
    std::cout << "【4. 向量乘加 (FMA)】\n";

    start = std::chrono::high_resolution_clock::now();
    vector_fma(a, b, a, c, N);
    end = std::chrono::high_resolution_clock::now();
    auto fma_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    do_not_optimize(c[0]);

    std::cout << "  FMA c[i] = a[i]*b[i] + a[i]（" << N << " 个 float）: "
              << fma_ns / 1000.0 << " μs\n";
    std::cout << "  FMA 指令比分离的乘法+加法更快且更精确\n\n";

    // --- 5. AoS vs SoA 颜色处理 ---
    std::cout << "【5. SIMD 友好的数据布局 (AoS vs SoA)】\n";

    const size_t NUM_COLORS = 5000000;

    // AoS 版本
    std::vector<Color_AoS> aos_colors(NUM_COLORS);
    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        for (auto& c : aos_colors) {
            c.r = dist(rng); c.g = dist(rng); c.b = dist(rng); c.a = 1.0f;
        }
    }

    // SoA 版本
    Colors_SoA soa_colors;
    soa_colors.resize(NUM_COLORS);
    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        for (size_t i = 0; i < NUM_COLORS; ++i) {
            soa_colors.r[i] = dist(rng);
            soa_colors.g[i] = dist(rng);
            soa_colors.b[i] = dist(rng);
            soa_colors.a[i] = 1.0f;
        }
    }

    start = std::chrono::high_resolution_clock::now();
    adjust_brightness_AoS(aos_colors.data(), NUM_COLORS, 1.5f);
    end = std::chrono::high_resolution_clock::now();
    auto aos_color_ns = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
    do_not_optimize(aos_colors[0]);

    start = std::chrono::high_resolution_clock::now();
    adjust_brightness_SoA(soa_colors, NUM_COLORS, 1.5f);
    end = std::chrono::high_resolution_clock::now();
    auto soa_color_ns = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
    do_not_optimize(soa_colors.r[0]);

    std::cout << "  颜色亮度调整（" << NUM_COLORS << " 个颜色）:\n";
    std::cout << "    AoS 版本: " << aos_color_ns << " ms\n";
    std::cout << "    SoA 版本: " << soa_color_ns << " ms\n";
    std::cout << "    加速比: " << std::setprecision(2)
              << static_cast<double>(aos_color_ns) / soa_color_ns << "x\n";
    std::cout << "  SoA 布局让每个通道的数据连续存储，SIMD 友好\n\n";

    // --- 6. 阈值处理 ---
    std::cout << "【6. 条件处理：分支 vs 无分支】\n";

    const size_t THRESHOLD_N = 10000000;
    std::vector<float> data1(THRESHOLD_N), data2(THRESHOLD_N);
    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        for (size_t i = 0; i < THRESHOLD_N; ++i) {
            float val = dist(rng);
            data1[i] = val;
            data2[i] = val;
        }
    }

    start = std::chrono::high_resolution_clock::now();
    threshold_branched(data1.data(), THRESHOLD_N, 0.5f, 0.0f);
    end = std::chrono::high_resolution_clock::now();
    auto thresh_branched_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    do_not_optimize(data1[0]);

    start = std::chrono::high_resolution_clock::now();
    threshold_branchless(data2.data(), THRESHOLD_N, 0.5f, 0.0f);
    end = std::chrono::high_resolution_clock::now();
    auto thresh_branchless_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    do_not_optimize(data2[0]);

    std::cout << "  阈值处理（" << THRESHOLD_N << " 个元素）:\n";
    std::cout << "    有分支版本:   " << thresh_branched_ns / 1000.0 << " μs\n";
    std::cout << "    无分支版本:   " << thresh_branchless_ns / 1000.0 << " μs\n";
    std::cout << "    加速比: " << std::setprecision(2)
              << static_cast<double>(thresh_branched_ns) / thresh_branchless_ns << "x\n\n";

    // --- 7. 欧氏距离 ---
    std::cout << "【7. 向量距离计算】\n";

    start = std::chrono::high_resolution_clock::now();
    float dist_result = euclidean_distance(a, b, N);
    end = std::chrono::high_resolution_clock::now();
    auto dist_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
    do_not_optimize(dist_result);

    std::cout << "  欧氏距离（" << N << " 维）: " << dist_ns / 1000.0 << " μs\n";
    std::cout << "  结果: " << std::setprecision(6) << dist_result << "\n\n";

    // --- 总结 ---
    std::cout << "========================================\n";
    std::cout << "  总结：SIMD 优化的最佳实践\n";
    std::cout << "========================================\n";
    std::cout << "  1. 写简单的循环 —— 让编译器自动向量化\n";
    std::cout << "  2. 消除循环依赖 —— 打破依赖链，使用多路展开\n";
    std::cout << "  3. 使用 SoA 布局 —— 让数据连续存储\n";
    std::cout << "  4. 使用 restrict  —— 告诉编译器指针不重叠\n";
    std::cout << "  5. 无分支编程    —— 用算术代替条件分支\n";
    std::cout << "  6. 对齐内存分配  —— 使用 aligned_alloc\n";
    std::cout << "  7. 编译时启用    —— -O2 -march=native -mavx2\n";
    std::cout << "\n  AVX2 可同时处理 8 个 float，理论加速比 8x！\n";
    std::cout << "  实际加速取决于内存带宽、缓存等因素。\n";

    // 清理
    AlignedAllocator::deallocate(a);
    AlignedAllocator::deallocate(b);
    AlignedAllocator::deallocate(c);

    return 0;
}
