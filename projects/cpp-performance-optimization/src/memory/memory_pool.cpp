/**
 * memory_pool.cpp - 内存池实现与性能对比演示
 *
 * 本文件演示内存池(Memory Pool)技术，包括：
 * 1. 简单内存池 vs 标准 new/delete 性能对比
 * 2. 固定大小块分配器 (Fixed-Size Block Allocator)
 * 3. 小对象池分配
 * 4. 内存碎片化减少
 * 5. 交替分配/释放模式
 * 6. 粒子系统模拟
 *
 * 编译命令:
 *   g++ -std=c++17 -O2 -o memory_pool memory_pool.cpp
 *
 * 内存池的优势:
 *   1. 减少系统调用 (malloc/free) 次数
 *   2. 减少内存碎片
 *   3. 提高缓存局部性
 *   4. 可预测的分配/释放时间
 *   5. 适合频繁创建/销毁小对象的场景
 */

#include <chrono>
#include <iostream>
#include <iomanip>
#include <vector>
#include <list>
#include <memory>
#include <new>
#include <cstring>
#include <cassert>
#include <cstdlib>
#include <algorithm>
#include <random>
#include <functional>

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
// 简单内存池实现
// ============================================================================

/*
 * 简单内存池: 预分配一大块内存，通过链表管理空闲块。
 * 适用于频繁分配/释放相同大小对象的场景。
 *
 * 内存布局:
 * [块1][块2][块3]...[块N]
 *  每个块的前 8 字节存储指向下一个空闲块的指针
 *
 * 分配: 从空闲链表头部取出一个块 O(1)
 * 释放: 将块放回空闲链表头部 O(1)
 */

class SimpleMemoryPool {
    struct FreeBlock {
        FreeBlock* next;
    };

    char* memory_;          // 预分配的内存块
    FreeBlock* freeList_;   // 空闲链表
    size_t blockSize_;      // 每个块的大小
    size_t capacity_;       // 总块数
    size_t allocated_;      // 已分配数量
    size_t peakUsage_;      // 峰值使用量

public:
    SimpleMemoryPool(size_t blockSize, size_t capacity)
        : blockSize_(std::max(blockSize, sizeof(FreeBlock)))
        , capacity_(capacity)
        , allocated_(0)
        , peakUsage_(0)
    {
        // 确保块大小对齐
        blockSize_ = (blockSize_ + alignof(std::max_align_t) - 1)
                     & ~(alignof(std::max_align_t) - 1);

        // 分配一大块连续内存
        memory_ = static_cast<char*>(std::malloc(blockSize_ * capacity_));
        if (!memory_) throw std::bad_alloc();

        // 初始化空闲链表
        freeList_ = nullptr;
        for (size_t i = 0; i < capacity_; ++i) {
            auto* block = reinterpret_cast<FreeBlock*>(memory_ + i * blockSize_);
            block->next = freeList_;
            freeList_ = block;
        }
    }

    ~SimpleMemoryPool() {
        std::free(memory_);
    }

    SimpleMemoryPool(const SimpleMemoryPool&) = delete;
    SimpleMemoryPool& operator=(const SimpleMemoryPool&) = delete;

    // 分配一个块 O(1)
    void* allocate() {
        if (!freeList_) {
            throw std::bad_alloc();
        }

        FreeBlock* block = freeList_;
        freeList_ = freeList_->next;
        ++allocated_;
        peakUsage_ = std::max(peakUsage_, allocated_);

        return static_cast<void*>(block);
    }

    // 释放一个块 O(1)
    void deallocate(void* ptr) {
        if (!ptr) return;

        auto* block = static_cast<FreeBlock*>(ptr);
        block->next = freeList_;
        freeList_ = block;
        --allocated_;
    }

    size_t blockSize() const { return blockSize_; }
    size_t capacity() const { return capacity_; }
    size_t allocated() const { return allocated_; }
    size_t peakUsage() const { return peakUsage_; }
    size_t totalMemory() const { return blockSize_ * capacity_; }
};

// ============================================================================
// 固定大小块分配器 (Fixed-Size Block Allocator)
// ============================================================================

/*
 * 使用多个不同大小的内存池来处理不同大小的分配请求。
 */

class FixedSizeAllocator {
    static constexpr size_t NUM_POOLS = 6;
    static constexpr size_t POOL_SIZES[NUM_POOLS] = {8, 16, 32, 64, 128, 256};
    static constexpr size_t BLOCKS_PER_POOL = 10000;

    SimpleMemoryPool* pools_[NUM_POOLS];
    size_t allocCount_;
    size_t deallocCount_;

    size_t findPool(size_t size) const {
        for (size_t i = 0; i < NUM_POOLS; ++i) {
            if (size <= POOL_SIZES[i]) return i;
        }
        return NUM_POOLS;
    }

public:
    FixedSizeAllocator() : allocCount_(0), deallocCount_(0) {
        for (size_t i = 0; i < NUM_POOLS; ++i) {
            pools_[i] = new SimpleMemoryPool(POOL_SIZES[i], BLOCKS_PER_POOL);
        }
    }

    ~FixedSizeAllocator() {
        for (size_t i = 0; i < NUM_POOLS; ++i) {
            delete pools_[i];
        }
    }

    void* allocate(size_t size) {
        ++allocCount_;
        size_t idx = findPool(size);
        if (idx < NUM_POOLS) {
            return pools_[idx]->allocate();
        }
        return std::malloc(size);
    }

    void deallocate(void* ptr, size_t size) {
        if (!ptr) return;
        ++deallocCount_;
        size_t idx = findPool(size);
        if (idx < NUM_POOLS) {
            pools_[idx]->deallocate(ptr);
        } else {
            std::free(ptr);
        }
    }

    void printStats() const {
        std::cout << "    分配次数: " << allocCount_ << std::endl;
        std::cout << "    释放次数: " << deallocCount_ << std::endl;
        for (size_t i = 0; i < NUM_POOLS; ++i) {
            std::cout << "    Pool " << std::setw(3) << POOL_SIZES[i] << "B: "
                      << "已用 " << pools_[i]->allocated() << "/"
                      << pools_[i]->capacity() << " (峰值: "
                      << pools_[i]->peakUsage() << ")" << std::endl;
        }
    }
};

constexpr size_t FixedSizeAllocator::POOL_SIZES[NUM_POOLS];

// ============================================================================
// 对象池 (Object Pool) - 类型安全的内存池
// ============================================================================

template<typename T, size_t PoolSize = 10000>
class ObjectPool {
    SimpleMemoryPool pool_;

public:
    ObjectPool() : pool_(sizeof(T), PoolSize) {}

    template<typename... Args>
    T* construct(Args&&... args) {
        void* mem = pool_.allocate();
        return new (mem) T(std::forward<Args>(args)...);
    }

    void destroy(T* ptr) {
        if (ptr) {
            ptr->~T();
            pool_.deallocate(static_cast<void*>(ptr));
        }
    }

    size_t available() const { return pool_.capacity() - pool_.allocated(); }
    size_t capacity() const { return pool_.capacity(); }
    size_t totalMemory() const { return pool_.totalMemory(); }
};

// ============================================================================
// 演示用的测试对象
// ============================================================================

struct Particle {
    float x, y, z;
    float vx, vy, vz;
    float r, g, b, a;
    float lifetime;
    int type;

    Particle() : x(0), y(0), z(0), vx(0), vy(0), vz(0),
                 r(1), g(1), b(1), a(1), lifetime(10), type(0) {}

    Particle(float px, float py, float pz, int t)
        : x(px), y(py), z(pz), vx(0), vy(0), vz(0),
          r(1), g(1), b(1), a(1), lifetime(10), type(t) {}

    void update(float dt) {
        x += vx * dt;
        y += vy * dt;
        z += vz * dt;
        lifetime -= dt;
    }

    bool isDead() const { return lifetime <= 0; }
};

struct ListNode {
    int data;
    ListNode* next;
    ListNode(int d = 0) : data(d), next(nullptr) {}
};

// ============================================================================
// 演示 1: 基本分配/释放性能对比
// ============================================================================

constexpr int NUM_ALLOCATIONS = 1000000;

void benchmarkBasicAllocation() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 1: 基本分配/释放性能对比 (" << NUM_ALLOCATIONS << " 次)" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    constexpr size_t BLOCK_SIZE = 64;

    // 标准 new/delete
    {
        Timer t("标准 new/delete");
        std::vector<void*> ptrs(NUM_ALLOCATIONS);
        for (int i = 0; i < NUM_ALLOCATIONS; ++i) {
            ptrs[i] = ::operator new(BLOCK_SIZE);
        }
        for (int i = 0; i < NUM_ALLOCATIONS; ++i) {
            ::operator delete(ptrs[i]);
        }
    }

    // 内存池分配
    {
        SimpleMemoryPool pool(BLOCK_SIZE, NUM_ALLOCATIONS);
        Timer t("内存池分配/释放");
        std::vector<void*> ptrs(NUM_ALLOCATIONS);
        for (int i = 0; i < NUM_ALLOCATIONS; ++i) {
            ptrs[i] = pool.allocate();
        }
        for (int i = 0; i < NUM_ALLOCATIONS; ++i) {
            pool.deallocate(ptrs[i]);
        }
    }

    // malloc/free
    {
        Timer t("标准 malloc/free");
        std::vector<void*> ptrs(NUM_ALLOCATIONS);
        for (int i = 0; i < NUM_ALLOCATIONS; ++i) {
            ptrs[i] = std::malloc(BLOCK_SIZE);
        }
        for (int i = 0; i < NUM_ALLOCATIONS; ++i) {
            std::free(ptrs[i]);
        }
    }
}

// ============================================================================
// 演示 2: 交替分配/释放模式
// ============================================================================

constexpr int NUM_OPS = 500000;
constexpr int POOL_SIZE = 10000;

void benchmarkInterleavedAllocDealloc() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 2: 交替分配/释放模式" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::mt19937 rng(42);
    std::uniform_int_distribution<int> coinFlip(0, 1);

    // 标准 new/delete
    {
        Timer t("标准 new/delete (交替分配释放)");
        std::vector<Particle*> particles;
        particles.reserve(POOL_SIZE);

        for (int i = 0; i < NUM_OPS; ++i) {
            if (particles.empty() || coinFlip(rng)) {
                particles.push_back(new Particle());
            } else {
                size_t idx = rng() % particles.size();
                delete particles[idx];
                particles[idx] = particles.back();
                particles.pop_back();
            }
        }
        for (auto* p : particles) delete p;
    }

    // 对象池
    {
        ObjectPool<Particle> pool;
        Timer t("对象池 (交替分配释放)");
        std::vector<Particle*> particles;
        particles.reserve(POOL_SIZE);

        for (int i = 0; i < NUM_OPS; ++i) {
            if (particles.empty() || coinFlip(rng)) {
                particles.push_back(pool.construct());
            } else {
                size_t idx = rng() % particles.size();
                pool.destroy(particles[idx]);
                particles[idx] = particles.back();
                particles.pop_back();
            }
        }
        for (auto* p : particles) pool.destroy(p);
    }
}

// ============================================================================
// 演示 3: 粒子系统模拟
// ============================================================================

constexpr int MAX_PARTICLES = 50000;
constexpr int PARTICLES_PER_FRAME = 500;
constexpr int NUM_FRAMES = 200;

void benchmarkParticleSystem() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 3: 粒子系统模拟 (" << NUM_FRAMES << " 帧, 每帧创建 " << PARTICLES_PER_FRAME << " 个)" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    std::mt19937 rng(42);
    std::uniform_real_distribution<float> posDist(-100.0f, 100.0f);
    std::uniform_real_distribution<float> velDist(-10.0f, 10.0f);
    std::uniform_real_distribution<float> lifeDist(0.5f, 3.0f);
    float dt = 0.016f;

    // 标准 new/delete
    {
        std::vector<Particle*> particles;
        particles.reserve(MAX_PARTICLES);
        long long totalUs = 0;

        Timer t("粒子系统 (标准 new/delete)");
        for (int frame = 0; frame < NUM_FRAMES; ++frame) {
            auto start = std::chrono::high_resolution_clock::now();

            for (int i = 0; i < PARTICLES_PER_FRAME; ++i) {
                if (particles.size() < MAX_PARTICLES) {
                    auto* p = new Particle(posDist(rng), posDist(rng), posDist(rng), 0);
                    p->vx = velDist(rng);
                    p->vy = velDist(rng);
                    p->vz = velDist(rng);
                    p->lifetime = lifeDist(rng);
                    particles.push_back(p);
                }
            }

            for (auto* p : particles) p->update(dt);

            particles.erase(
                std::remove_if(particles.begin(), particles.end(),
                    [](Particle* p) {
                        if (p->isDead()) { delete p; return true; }
                        return false;
                    }),
                particles.end()
            );

            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }

        for (auto* p : particles) delete p;
        std::cout << "    总耗时: " << totalUs << " us" << std::endl;
        std::cout << "    每帧平均: " << totalUs / NUM_FRAMES << " us" << std::endl;
    }

    // 对象池
    {
        ObjectPool<Particle> pool;
        std::vector<Particle*> particles;
        particles.reserve(MAX_PARTICLES);
        long long totalUs = 0;

        Timer t("粒子系统 (对象池)");
        for (int frame = 0; frame < NUM_FRAMES; ++frame) {
            auto start = std::chrono::high_resolution_clock::now();

            for (int i = 0; i < PARTICLES_PER_FRAME; ++i) {
                if (particles.size() < MAX_PARTICLES) {
                    auto* p = pool.construct(posDist(rng), posDist(rng), posDist(rng), 0);
                    p->vx = velDist(rng);
                    p->vy = velDist(rng);
                    p->vz = velDist(rng);
                    p->lifetime = lifeDist(rng);
                    particles.push_back(p);
                }
            }

            for (auto* p : particles) p->update(dt);

            particles.erase(
                std::remove_if(particles.begin(), particles.end(),
                    [&pool](Particle* p) {
                        if (p->isDead()) { pool.destroy(p); return true; }
                        return false;
                    }),
                particles.end()
            );

            auto end = std::chrono::high_resolution_clock::now();
            totalUs += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        }

        for (auto* p : particles) pool.destroy(p);
        std::cout << "    总耗时: " << totalUs << " us" << std::endl;
        std::cout << "    每帧平均: " << totalUs / NUM_FRAMES << " us" << std::endl;
    }
}

// ============================================================================
// 演示 4: 链表操作性能
// ============================================================================

constexpr int LIST_OPS = 500000;

void benchmarkListOperations() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 4: 链表节点分配/释放" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    // 标准 new/delete
    {
        Timer t("链表操作 (标准 new/delete)");
        ListNode* head = nullptr;
        for (int i = 0; i < LIST_OPS; ++i) {
            auto* node = new ListNode(i);
            node->next = head;
            head = node;

            if (i % 10 == 0 && head) {
                ListNode* temp = head;
                head = head->next;
                delete temp;
            }
        }
        while (head) {
            ListNode* temp = head;
            head = head->next;
            delete temp;
        }
    }

    // 对象池
    {
        ObjectPool<ListNode> pool;
        Timer t("链表操作 (对象池)");
        ListNode* head = nullptr;
        for (int i = 0; i < LIST_OPS; ++i) {
            auto* node = pool.construct(i);
            node->next = head;
            head = node;

            if (i % 10 == 0 && head) {
                ListNode* temp = head;
                head = head->next;
                pool.destroy(temp);
            }
        }
        while (head) {
            ListNode* temp = head;
            head = head->next;
            pool.destroy(temp);
        }
    }
}

// ============================================================================
// 演示 5: 内存碎片化分析
// ============================================================================

void benchmarkFragmentation() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 5: 内存碎片化分析" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    constexpr int NUM_OBJECTS = 100000;
    constexpr size_t OBJ_SIZE = 48;

    std::cout << "\n  场景: 分配 " << NUM_OBJECTS << " 个对象，释放偶数索引的对象" << std::endl;

    // 标准分配器
    {
        std::vector<void*> ptrs(NUM_OBJECTS);
        for (int i = 0; i < NUM_OBJECTS; ++i) {
            ptrs[i] = std::malloc(OBJ_SIZE);
        }

        for (int i = 0; i < NUM_OBJECTS; i += 2) {
            std::free(ptrs[i]);
            ptrs[i] = nullptr;
        }

        void* bigBlock = std::malloc(OBJ_SIZE * 100);
        std::cout << "    标准分配器: 大块分配 " << (bigBlock ? "成功" : "失败") << std::endl;

        if (bigBlock) std::free(bigBlock);
        for (int i = 1; i < NUM_OBJECTS; i += 2) {
            if (ptrs[i]) std::free(ptrs[i]);
        }
    }

    // 内存池
    {
        SimpleMemoryPool pool(OBJ_SIZE, NUM_OBJECTS);
        std::vector<void*> ptrs(NUM_OBJECTS);
        for (int i = 0; i < NUM_OBJECTS; ++i) {
            ptrs[i] = pool.allocate();
        }

        for (int i = 0; i < NUM_OBJECTS; i += 2) {
            pool.deallocate(ptrs[i]);
            ptrs[i] = nullptr;
        }

        void* bigBlock = pool.allocate();
        std::cout << "    内存池:     分配 " << (bigBlock ? "成功 (无碎片)" : "失败") << std::endl;

        if (bigBlock) pool.deallocate(bigBlock);
        for (int i = 1; i < NUM_OBJECTS; i += 2) {
            if (ptrs[i]) pool.deallocate(ptrs[i]);
        }

        std::cout << "    内存池统计: 峰值使用 " << pool.peakUsage() << "/" << pool.capacity() << std::endl;
    }

    std::cout << "\n  说明: 内存池使用连续内存，释放后的块可以立即被重用，" << std::endl;
    std::cout << "  不会产生外部碎片。标准分配器在频繁分配释放后会产生碎片。" << std::endl;
}

// ============================================================================
// 演示 6: 不同大小对象的分配策略
// ============================================================================

void benchmarkMixedSizes() {
    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "演示 6: 不同大小对象的分配策略" << std::endl;
    std::cout << std::string(70, '=') << std::endl;

    constexpr int OPS = 200000;
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> sizeDist(8, 200);

    // 标准分配器
    {
        Timer t("混合大小分配 (标准 malloc/free)");
        std::vector<std::pair<void*, size_t>> allocs;
        allocs.reserve(OPS);

        for (int i = 0; i < OPS; ++i) {
            size_t size = sizeDist(rng);
            void* ptr = std::malloc(size);
            allocs.emplace_back(ptr, size);

            if (allocs.size() > 1000 && (rng() % 3 == 0)) {
                size_t idx = rng() % allocs.size();
                std::free(allocs[idx].first);
                allocs[idx] = allocs.back();
                allocs.pop_back();
            }
        }
        for (auto& [ptr, size] : allocs) std::free(ptr);
    }

    // 固定大小分配器
    {
        FixedSizeAllocator allocator;
        Timer t("混合大小分配 (固定大小分配器)");
        std::vector<std::pair<void*, size_t>> allocs;
        allocs.reserve(OPS);

        for (int i = 0; i < OPS; ++i) {
            size_t size = sizeDist(rng);
            void* ptr = allocator.allocate(size);
            allocs.emplace_back(ptr, size);

            if (allocs.size() > 1000 && (rng() % 3 == 0)) {
                size_t idx = rng() % allocs.size();
                allocator.deallocate(allocs[idx].first, allocs[idx].second);
                allocs[idx] = allocs.back();
                allocs.pop_back();
            }
        }
        for (auto& [ptr, size] : allocs) allocator.deallocate(ptr, size);

        std::cout << "    分配器统计:" << std::endl;
        allocator.printStats();
    }
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "==============================================================" << std::endl;
    std::cout << "              内存池实现与性能对比演示" << std::endl;
    std::cout << "==============================================================" << std::endl;

    benchmarkBasicAllocation();
    benchmarkInterleavedAllocDealloc();
    benchmarkParticleSystem();
    benchmarkListOperations();
    benchmarkFragmentation();
    benchmarkMixedSizes();

    std::cout << "\n" << std::string(70, '=') << std::endl;
    std::cout << "总结: 内存池使用指南" << std::endl;
    std::cout << std::string(70, '=') << std::endl;
    std::cout << "  适用场景:" << std::endl;
    std::cout << "    1. 频繁创建/销毁相同大小的对象" << std::endl;
    std::cout << "    2. 游戏引擎中的粒子系统、子弹、特效" << std::endl;
    std::cout << "    3. 网络服务器中的连接、缓冲区" << std::endl;
    std::cout << "    4. 编译器中的 AST 节点" << std::endl;
    std::cout << std::endl;
    std::cout << "  实现要点:" << std::endl;
    std::cout << "    1. 预分配连续内存，使用空闲链表管理" << std::endl;
    std::cout << "    2. 分配和释放都是 O(1) 操作" << std::endl;
    std::cout << "    3. 块大小需要对齐到合适的边界" << std::endl;
    std::cout << "    4. 考虑线程安全 (使用互斥锁或线程本地存储)" << std::endl;
    std::cout << "    5. 可以组合多个池处理不同大小的分配" << std::endl;
    std::cout << std::endl;
    std::cout << "  注意事项:" << std::endl;
    std::cout << "    1. 内存池的内存不会自动归还给操作系统" << std::endl;
    std::cout << "    2. 需要确保对象在池释放前全部归还" << std::endl;
    std::cout << "    3. 双重释放会导致空闲链表损坏" << std::endl;
    std::cout << "    4. 对象池可以结合构造/析构提供类型安全" << std::endl;

    return 0;
}
