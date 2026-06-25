/**
 * soa_vs_aos.cpp - Array of Structures vs Structure of Arrays 性能对比
 *
 * 本文件深入对比 AOS 和 SOA 两种数据布局方式的性能差异。
 *
 * AOS (Array of Structures):
 *   [pos.x, pos.y, pos.z, vel.x, vel.y, vel.z, color.r, color.g, color.b]
 *   [pos.x, pos.y, pos.z, vel.x, vel.y, vel.z, color.r, color.g, color.b]
 *   ... 每个粒子的所有属性连续存储
 *
 * SOA (Structure of Arrays):
 *   pos.x:  [x0, x1, x2, x3, ...]   <- 所有粒子的 x 坐标连续存储
 *   pos.y:  [y0, y1, y2, y3, ...]   <- 所有粒子的 y 坐标连续存储
 *   vel.x:  [vx0, vx1, vx2, ...]    <- 所有粒子的 x 速度连续存储
 *   ...
 *
 * 编译命令:
 *   g++ -std=c++17 -O2 -o soa_vs_aos soa_vs_aos.cpp
 *   g++ -std=c++17 -O2 -mavx2 -o soa_vs_aos soa_vs_aos.cpp  # 启用 AVX2 SIMD
 */

#include <chrono>
#include <iostream>
#include <iomanip>
#include <vector>
#include <random>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <cstring>

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
// AOS 方式: Array of Structures
// ============================================================================

/*
 * 每个粒子是一个完整的结构体，所有粒子组成一个数组。
 * 优点: 单个粒子的所有数据在一起，访问单个粒子方便。
 * 缺点: 遍历时访问特定字段会加载不需要的数据到缓存。
 */

struct ParticleAOS {
    float x, y, z;          // 位置 (12 字节)
    float vx, vy, vz;       // 速度 (12 字节)
    float r, g, b, a;       // 颜色 (16 字节)
    float mass;              // 质量 (4 字节)
    float lifetime;          // 生命周期 (4 字节)
    // 总计: 48 字节/粒子
};

static_assert(sizeof(ParticleAOS) == 48, "ParticleAOS 应该是 48 字节");

// ============================================================================
// SOA 方式: Structure of Arrays
// ============================================================================

/*
 * 每个属性是一个独立的数组。
 * 优点: 遍历特定字段时缓存效率极高，适合 SIMD 优化。
 * 缺点: 访问单个粒子需要访问多个数组。
 */

struct ParticleSOA {
    std::vector<float> x, y, z;           // 位置
    std::vector<float> vx, vy, vz;        // 速度
    std::vector<float> r, g, b, a;        // 颜色
    std::vector<float> mass;               // 质量
    std::vector<float> lifetime;           // 生命周期

    void resize(size_t n) {
        x.resize(n); y.resize(n); z.resize(n);
        vx.resize(n); vy.resize(n); vz.resize(n);
        r.resize(n); g.resize(n); b.resize(n); a.resize(n);
        mass.resize(n); lifetime.resize(n);
    }

    size_t size() const { return x.size(); }
};

// ============================================================================
// 混合方式: 将常用和不常用字段分开
// ============================================================================

/*
 * 实际项目中，可以将频繁一起访问的字段放在一起来减少缓存浪费。
 */

// 高频访问字段（物理更新时只需要这些）
struct ParticleHot {
    float x, y, z;       // 位置
    float vx, vy, vz;    // 速度
    float mass;           // 质量
    float _pad;           // 对齐到 32 字节
};

// 低频访问字段（渲染时才需要）
struct ParticleCold {
    float r, g, b, a;    // 颜色
    float lifetime;       // 生命周期
    float _pad[3];        // 对齐到 32 字节
};

static_assert(sizeof(ParticleHot) == 32, "ParticleHot 应该是 32 字节");
static_assert(sizeof(ParticleCold) == 32, "ParticleCold 应该是 32 字节");

struct ParticleHybrid {
    std::vector<ParticleHot> hot;    // 物理更新用
    std::vector<ParticleCold> cold;  // 渲染用

    void resize(size_t n) {
        hot.resize(n);
        cold.resize(n);
    }

    size_t size() const { return hot.size(); }
};

// ============================================================================
// 演示 1: 粒子物理更新（只访问位置和速度）
// ============================================================================

constexpr int NUM_PARTICLES = 500000;
constexpr float DT = 0.016f;  // 60fps 的时间步长
constexpr float GRAVITY = -9.81f;

void benchmarkPhysicsUpdate() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 1: 粒子物理更新 (只访问位置和速度字段)" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    // 初始化 AOS 数据
    std::vector<ParticleAOS> aos(NUM_PARTICLES);
    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<float> dist(-100.0f, 100.0f);
        for (auto& p : aos) {
            p = {dist(rng), dist(rng), dist(rng),
                 dist(rng), dist(rng), dist(rng),
                 dist(rng), dist(rng), dist(rng), 1.0f,
                 1.0f, 10.0f};
        }
    }

    // 初始化 SOA 数据
    ParticleSOA soa;
    soa.resize(NUM_PARTICLES);
    for (int i = 0; i < NUM_PARTICLES; ++i) {
        soa.x[i] = aos[i].x; soa.y[i] = aos[i].y; soa.z[i] = aos[i].z;
        soa.vx[i] = aos[i].vx; soa.vy[i] = aos[i].vy; soa.vz[i] = aos[i].vz;
        soa.r[i] = aos[i].r; soa.g[i] = aos[i].g;
        soa.b[i] = aos[i].b; soa.a[i] = aos[i].a;
        soa.mass[i] = aos[i].mass; soa.lifetime[i] = aos[i].lifetime;
    }

    // 初始化混合数据
    ParticleHybrid hybrid;
    hybrid.resize(NUM_PARTICLES);
    for (int i = 0; i < NUM_PARTICLES; ++i) {
        hybrid.hot[i] = {aos[i].x, aos[i].y, aos[i].z,
                         aos[i].vx, aos[i].vy, aos[i].vz,
                         aos[i].mass, 0.0f};
        hybrid.cold[i] = {aos[i].r, aos[i].g, aos[i].b, aos[i].a,
                          aos[i].lifetime, {0, 0, 0}};
    }

    const int ITERATIONS = 20;

    // AOS 物理更新
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            for (int i = 0; i < NUM_PARTICLES; ++i) {
                // 每次迭代访问 48 字节，但只使用 24 字节（位置+速度）
                // 缓存行利用率 = 24/48 = 50%
                aos[i].vy += GRAVITY * DT;
                aos[i].x += aos[i].vx * DT;
                aos[i].y += aos[i].vy * DT;
                aos[i].z += aos[i].vz * DT;
                aos[i].lifetime -= DT;
            }
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(aos[0].x);
        std::cout << std::setw(45) << std::left << "AOS 物理更新"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us (每粒子 48B, 有效 24B)" << std::endl;
    }

    // SOA 物理更新
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            for (int i = 0; i < NUM_PARTICLES; ++i) {
                // 访问 vy 数组: 连续 4 字节 * N，100% 缓存利用率
                soa.vy[i] += GRAVITY * DT;
                soa.x[i] += soa.vx[i] * DT;
                soa.y[i] += soa.vy[i] * DT;
                soa.z[i] += soa.vz[i] * DT;
                soa.lifetime[i] -= DT;
            }
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(soa.x[0]);
        std::cout << std::setw(45) << std::left << "SOA 物理更新"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us (每字段 4B, 100% 缓存利用率)" << std::endl;
    }

    // 混合方式物理更新
    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            for (int i = 0; i < NUM_PARTICLES; ++i) {
                hybrid.hot[i].vy += GRAVITY * DT;
                hybrid.hot[i].x += hybrid.hot[i].vx * DT;
                hybrid.hot[i].y += hybrid.hot[i].vy * DT;
                hybrid.hot[i].z += hybrid.hot[i].vz * DT;
            }
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(hybrid.hot[0].x);
        std::cout << std::setw(45) << std::left << "混合方式物理更新 (Hot/Cold 分离)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us (hot 32B, 全部有效)" << std::endl;
    }
}

// ============================================================================
// 演示 2: 粒子渲染（只访问位置和颜色）
// ============================================================================

void benchmarkRendering() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 2: 粒子渲染准备 (访问位置和颜色，跳过速度)" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::vector<ParticleAOS> aos(NUM_PARTICLES);
    ParticleSOA soa;
    soa.resize(NUM_PARTICLES);

    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<float> dist(0.0f, 1.0f);
        for (int i = 0; i < NUM_PARTICLES; ++i) {
            aos[i] = {dist(rng)*100, dist(rng)*100, dist(rng)*100,
                      dist(rng), dist(rng), dist(rng),
                      dist(rng), dist(rng), dist(rng), dist(rng),
                      dist(rng), dist(rng)};
            soa.x[i] = aos[i].x; soa.y[i] = aos[i].y; soa.z[i] = aos[i].z;
            soa.vx[i] = aos[i].vx; soa.vy[i] = aos[i].vy; soa.vz[i] = aos[i].vz;
            soa.r[i] = aos[i].r; soa.g[i] = aos[i].g;
            soa.b[i] = aos[i].b; soa.a[i] = aos[i].a;
            soa.mass[i] = aos[i].mass; soa.lifetime[i] = aos[i].lifetime;
        }
    }

    const int ITERATIONS = 20;

    // AOS 渲染准备
    {
        float totalBrightness = 0;
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            float brightness = 0;
            for (int i = 0; i < NUM_PARTICLES; ++i) {
                // AOS: 加载 48 字节，但只使用 28 字节（位置+颜色）
                float dist = std::sqrt(aos[i].x * aos[i].x +
                                       aos[i].y * aos[i].y +
                                       aos[i].z * aos[i].z);
                brightness += (aos[i].r + aos[i].g + aos[i].b) / (1.0f + dist);
            }
            doNotOptimize(brightness);
            totalBrightness = brightness;
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(45) << std::left << "AOS 渲染准备"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // SOA 渲染准备
    {
        float totalBrightness = 0;
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            float brightness = 0;
            for (int i = 0; i < NUM_PARTICLES; ++i) {
                float dist = std::sqrt(soa.x[i] * soa.x[i] +
                                       soa.y[i] * soa.y[i] +
                                       soa.z[i] * soa.z[i]);
                brightness += (soa.r[i] + soa.g[i] + soa.b[i]) / (1.0f + dist);
            }
            doNotOptimize(brightness);
            totalBrightness = brightness;
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(45) << std::left << "SOA 渲染准备"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }
}

// ============================================================================
// 演示 3: SIMD 友好性对比
// ============================================================================

/*
 * SOA 布局天然适合 SIMD 操作:
 * - 连续的 float 数组可以直接加载到 SIMD 寄存器
 * - 一条 SIMD 指令可以处理 4/8/16 个元素
 * - AOS 需要 Gather/Scatter 操作，效率低下
 */

void simdLikeUpdate_SOA(ParticleSOA& soa, int n) {
    for (int i = 0; i < n; ++i) {
        soa.vy[i] += GRAVITY * DT;
        soa.x[i] += soa.vx[i] * DT;
        soa.y[i] += soa.vy[i] * DT;
        soa.z[i] += soa.vz[i] * DT;
    }
}

void simdLikeUpdate_AOS(std::vector<ParticleAOS>& aos, int n) {
    for (int i = 0; i < n; ++i) {
        aos[i].vy += GRAVITY * DT;
        aos[i].x += aos[i].vx * DT;
        aos[i].y += aos[i].vy * DT;
        aos[i].z += aos[i].vz * DT;
    }
}

void benchmarkSIMDFriendliness() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 3: SIMD 向量化友好性" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::vector<ParticleAOS> aos(NUM_PARTICLES);
    ParticleSOA soa;
    soa.resize(NUM_PARTICLES);

    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<float> dist(-100.0f, 100.0f);
        for (int i = 0; i < NUM_PARTICLES; ++i) {
            aos[i] = {dist(rng), dist(rng), dist(rng),
                      dist(rng), dist(rng), dist(rng),
                      1, 1, 1, 1, 1, 10};
            soa.x[i] = aos[i].x; soa.y[i] = aos[i].y; soa.z[i] = aos[i].z;
            soa.vx[i] = aos[i].vx; soa.vy[i] = aos[i].vy; soa.vz[i] = aos[i].vz;
            soa.r[i] = 1; soa.g[i] = 1; soa.b[i] = 1; soa.a[i] = 1;
            soa.mass[i] = 1; soa.lifetime[i] = 10;
        }
    }

    const int ITERATIONS = 50;

    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            simdLikeUpdate_AOS(aos, NUM_PARTICLES);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(aos[0].x);
        std::cout << std::setw(45) << std::left << "AOS 物理更新 (SIMD 不友好)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    {
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            simdLikeUpdate_SOA(soa, NUM_PARTICLES);
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(soa.x[0]);
        std::cout << std::setw(45) << std::left << "SOA 物理更新 (SIMD 友好)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    std::cout << "\n  说明: SOA 布局允许编译器自动向量化，使用 -O2 或 -O3 时效果显著" << std::endl;
    std::cout << "  使用 -mavx2 或 -march=native 可以进一步提升 SIMD 性能" << std::endl;
}

// ============================================================================
// 演示 4: 内存占用对比
// ============================================================================

void benchmarkMemoryUsage() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 4: 内存占用与缓存行利用分析" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    size_t aosSize = NUM_PARTICLES * sizeof(ParticleAOS);
    size_t soaSize = NUM_PARTICLES * 12 * sizeof(float);
    size_t hybridSize = NUM_PARTICLES * (sizeof(ParticleHot) + sizeof(ParticleCold));

    std::cout << "\n  数据量: " << NUM_PARTICLES << " 个粒子" << std::endl;
    std::cout << "  AOS 总内存:   " << aosSize / 1024 << " KB (" << aosSize / (1024*1024) << " MB)" << std::endl;
    std::cout << "  SOA 总内存:   " << soaSize / 1024 << " KB (" << soaSize / (1024*1024) << " MB)" << std::endl;
    std::cout << "  混合总内存:   " << hybridSize / 1024 << " KB (" << hybridSize / (1024*1024) << " MB)" << std::endl;

    std::cout << "\n  缓存行(64字节)利用率分析:" << std::endl;
    std::cout << "  +-----------------------------------------------------------+" << std::endl;
    std::cout << "  | 操作类型            | AOS 利用率 | SOA 利用率 | 混合利用率 |" << std::endl;
    std::cout << "  +-----------------------------------------------------------+" << std::endl;
    std::cout << "  | 物理更新(位置+速度) |    50%     |   100%     |   100%     |" << std::endl;
    std::cout << "  | 渲染(位置+颜色)     |    58%     |   100%     |    63%     |" << std::endl;
    std::cout << "  | 全字段访问          |   100%     |   100%     |   100%     |" << std::endl;
    std::cout << "  +-----------------------------------------------------------+" << std::endl;
}

// ============================================================================
// 演示 5: 查找与过滤操作
// ============================================================================

/*
 * SOA 在过滤操作中也有优势:
 * 找出所有 lifetime < 1 的粒子时，只需要遍历 lifetime 数组，
 * 而 AOS 需要加载每个完整粒子。
 */

void benchmarkFiltering() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 5: 粒子过滤 (找出需要销毁的粒子)" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::vector<ParticleAOS> aos(NUM_PARTICLES);
    ParticleSOA soa;
    soa.resize(NUM_PARTICLES);

    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<float> dist(0.0f, 20.0f);
        for (int i = 0; i < NUM_PARTICLES; ++i) {
            float lt = dist(rng);
            aos[i] = {0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, lt};
            soa.lifetime[i] = lt;
            soa.x[i] = soa.y[i] = soa.z[i] = 0;
            soa.vx[i] = soa.vy[i] = soa.vz[i] = 0;
            soa.r[i] = soa.g[i] = soa.b[i] = soa.a[i] = 1;
            soa.mass[i] = 1;
        }
    }

    const int ITERATIONS = 50;

    // AOS 过滤
    {
        int deadCount = 0;
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            int count = 0;
            for (int i = 0; i < NUM_PARTICLES; ++i) {
                // 加载 48 字节，只检查 4 字节 (lifetime)
                if (aos[i].lifetime < 1.0f) {
                    ++count;
                }
            }
            doNotOptimize(count);
            deadCount = count;
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(45) << std::left << "AOS 过滤 (加载 48B/粒子, 用 4B)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us (销毁 " << deadCount << " 个)" << std::endl;
    }

    // SOA 过滤
    {
        int deadCount = 0;
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            auto start = std::chrono::high_resolution_clock::now();
            int count = 0;
            // 只遍历 lifetime 数组，完全不访问其他字段
            for (int i = 0; i < NUM_PARTICLES; ++i) {
                if (soa.lifetime[i] < 1.0f) {
                    ++count;
                }
            }
            doNotOptimize(count);
            deadCount = count;
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        std::cout << std::setw(45) << std::left << "SOA 过滤 (只加载 lifetime 数组)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us (销毁 " << deadCount << " 个)" << std::endl;
    }
}

// ============================================================================
// 演示 6: 排序操作对比
// ============================================================================

/*
 * 按某个字段排序时:
 * - AOS: 需要移动整个 48 字节的粒子结构
 * - SOA: 只需要移动索引或排序后的字段
 */

void benchmarkSorting() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 6: 按质量排序粒子" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    const int SORT_SIZE = 100000;

    std::vector<ParticleAOS> aos(SORT_SIZE);
    {
        std::mt19937 rng(42);
        std::uniform_real_distribution<float> dist(0.0f, 100.0f);
        for (auto& p : aos) {
            p = {dist(rng), dist(rng), dist(rng),
                 dist(rng), dist(rng), dist(rng),
                 dist(rng), dist(rng), dist(rng), 1.0f,
                 dist(rng), dist(rng)};
        }
    }

    const int ITERATIONS = 10;

    // AOS 排序: 需要交换 48 字节的完整结构体
    {
        auto aosCopy = aos;
        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            aosCopy = aos;
            auto start = std::chrono::high_resolution_clock::now();
            std::sort(aosCopy.begin(), aosCopy.end(),
                      [](const ParticleAOS& a, const ParticleAOS& b) {
                          return a.mass < b.mass;
                      });
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(aosCopy[0].mass);
        std::cout << std::setw(45) << std::left << "AOS 排序 (交换 48B 结构体)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    // SOA 排序: 使用索引数组，只交换 4 字节索引
    {
        std::vector<float> soaMass(SORT_SIZE);
        for (int i = 0; i < SORT_SIZE; ++i) soaMass[i] = aos[i].mass;

        std::vector<int> indices(SORT_SIZE);
        std::iota(indices.begin(), indices.end(), 0);

        long long totalUs = 0;
        for (int iter = 0; iter < ITERATIONS; ++iter) {
            std::iota(indices.begin(), indices.end(), 0);
            auto start = std::chrono::high_resolution_clock::now();
            std::sort(indices.begin(), indices.end(),
                      [&soaMass](int a, int b) {
                          return soaMass[a] < soaMass[b];
                      });
            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }
        doNotOptimize(indices[0]);
        std::cout << std::setw(45) << std::left << "SOA 排序 (索引排序, 交换 4B)"
                  << ": " << std::setw(10) << std::right << (totalUs / ITERATIONS)
                  << " us" << std::endl;
    }

    std::cout << "  说明: SOA 的索引排序优势在于:" << std::endl;
    std::cout << "    1. 交换的数据量小 (4B vs 48B)" << std::endl;
    std::cout << "    2. 排序键值连续存储，比较操作缓存友好" << std::endl;
    std::cout << "    3. 可以对多个字段使用同一索引排列" << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "==============================================================" << std::endl;
    std::cout << "        AOS vs SOA 数据布局性能对比" << std::endl;
    std::cout << "==============================================================" << std::endl;

    benchmarkPhysicsUpdate();
    benchmarkRendering();
    benchmarkSIMDFriendliness();
    benchmarkMemoryUsage();
    benchmarkFiltering();
    benchmarkSorting();

    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "总结: AOS vs SOA 选择指南" << std::endl;
    std::cout << std::string(70, '=') << std::endl;
    std::cout << "  选择 AOS 当:" << std::endl;
    std::cout << "    - 总是需要访问对象的所有字段" << std::endl;
    std::cout << "    - 对象数量较少" << std::endl;
    std::cout << "    - 代码简洁性优先" << std::endl;
    std::cout << std::endl;
    std::cout << "  选择 SOA 当:" << std::endl;
    std::cout << "    - 经常只访问部分字段" << std::endl;
    std::cout << "    - 需要 SIMD 向量化" << std::endl;
    std::cout << "    - 数据量大（百万级以上）" << std::endl;
    std::cout << "    - 性能关键的热路径" << std::endl;
    std::cout << std::endl;
    std::cout << "  选择混合方式当:" << std::endl;
    std::cout << "    - 有明显的冷热数据分离" << std::endl;
    std::cout << "    - 不同操作需要不同的字段子集" << std::endl;
    std::cout << "    - 需要在代码简洁性和性能之间平衡" << std::endl;

    return 0;
}
