/**
 * memory_pool.cpp - 内存池 (Memory Pool)
 *
 * 本文件演示了固定大小内存池的实现，包括：
 *   1. 基于链表的固定大小内存池
 *   2. 分配/释放性能对比（池 vs 标准 new/delete）
 *   3. 池统计信息
 *   4. 内存碎片分析
 *
 * 编译: g++ -std=c++17 -O2 -o memory_pool memory_pool.cpp
 *
 * 内存池的核心思想：
 *   - 预先分配一大块连续内存
 *   - 将其切分为固定大小的块
 *   - 用空闲链表管理可用块
 *   - 分配时从链表头取一个块，O(1) 时间
 *   - 释放时将块放回链表头，O(1) 时间
 *   - 没有系统调用开销，没有内存碎片
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <cassert>
#include <cstring>
#include <iomanip>
#include <stdexcept>
#include <algorithm>

// ============================================================================
// 第一部分：固定大小内存池实现
// ============================================================================

/**
 * FixedSizeMemoryPool - 固定大小内存池
 *
 * 设计要点：
 *   - 每个块的大小固定为 BlockSize 字节
 *   - 使用侵入式空闲链表管理空闲块（零额外开销）
 *   - 空闲块本身存储 next 指针，不需要额外空间
 *   - 支持动态扩展：当当前内存块用完时，自动分配新的大块
 *
 * 内存布局：
 *   [已分配|已分配|空闲|已分配|空闲|空闲|...]
 *                    |
 *                    v  (空闲链表)
 *                   [空闲] -> [空闲] -> [空闲] -> nullptr
 *
 * 空闲块内部存储结构：
 *   [next指针 | 未使用空间...]
 */
class FixedSizeMemoryPool {
public:
    /**
     * 构造函数
     *
     * @param block_size     每个内存块的大小（字节）
     * @param blocks_per_chunk  每次扩展时分配的块数量
     */
    explicit FixedSizeMemoryPool(size_t block_size, size_t blocks_per_chunk = 1024)
        : block_size_(std::max(block_size, sizeof(FreeNode)))  // 至少要能存一个指针
        , blocks_per_chunk_(blocks_per_chunk)
        , total_allocated_(0)
        , total_freed_(0)
        , active_blocks_(0)
        , total_blocks_(0) {

        // 验证参数合理性
        if (blocks_per_chunk_ == 0) {
            throw std::invalid_argument("每个内存块的块数不能为 0");
        }

        // 分配第一个内存块
        allocate_chunk();
    }

    /**
     * 析构函数 - 释放所有分配的内存块
     */
    ~FixedSizeMemoryPool() {
        for (auto* chunk : chunks_) {
            std::free(chunk);
        }
    }

    // 禁止拷贝（拥有独占的内存资源）
    FixedSizeMemoryPool(const FixedSizeMemoryPool&) = delete;
    FixedSizeMemoryPool& operator=(const FixedSizeMemoryPool&) = delete;

    // 允许移动
    FixedSizeMemoryPool(FixedSizeMemoryPool&& other) noexcept
        : block_size_(other.block_size_)
        , blocks_per_chunk_(other.blocks_per_chunk_)
        , free_list_(other.free_list_)
        , chunks_(std::move(other.chunks_))
        , total_allocated_(other.total_allocated_)
        , total_freed_(other.total_freed_)
        , active_blocks_(other.active_blocks_)
        , total_blocks_(other.total_blocks_) {
        other.free_list_ = nullptr;
        other.total_allocated_ = 0;
        other.total_freed_ = 0;
        other.active_blocks_ = 0;
        other.total_blocks_ = 0;
    }

    /**
     * allocate - 从池中分配一个内存块
     *
     * @return 指向分配内存的指针
     *
     * 时间复杂度: O(1)，除非需要扩展池（此时为 O(blocks_per_chunk)）
     */
    void* allocate() {
        // 如果空闲链表为空，需要扩展池
        if (!free_list_) {
            allocate_chunk();
        }

        // 从空闲链表头取出一个块
        FreeNode* block = free_list_;
        free_list_ = block->next;

        total_allocated_++;
        active_blocks_++;

        return static_cast<void*>(block);
    }

    /**
     * deallocate - 将内存块归还给池
     *
     * @param ptr 要归还的指针
     *
     * 时间复杂度: O(1)
     *
     * 注意：调用者必须确保 ptr 确实是从本池分配的，
     * 否则会导致未定义行为。
     */
    void deallocate(void* ptr) {
        if (!ptr) return;

        // 将归还的块加入空闲链表头部
        // 这里利用了"侵入式链表"技巧：空闲块本身存储 next 指针
        auto* node = static_cast<FreeNode*>(ptr);
        node->next = free_list_;
        free_list_ = node;

        total_freed_++;
        active_blocks_--;
    }

    /**
     * get_stats - 获取池的统计信息
     */
    struct PoolStats {
        size_t block_size;        // 每个块的大小
        size_t total_blocks;      // 总块数
        size_t active_blocks;     // 正在使用的块数
        size_t free_blocks;       // 空闲块数
        size_t total_allocations; // 累计分配次数
        size_t total_frees;       // 累计释放次数
        size_t chunks;            // 内存块数量
        size_t memory_usage;      // 总内存使用量（字节）
    };

    PoolStats get_stats() const {
        return PoolStats{
            block_size_,
            total_blocks_,
            active_blocks_,
            total_blocks_ - active_blocks_,
            total_allocated_,
            total_freed_,
            chunks_.size(),
            chunks_.size() * blocks_per_chunk_ * block_size_
        };
    }

    void print_stats() const {
        auto stats = get_stats();
        std::cout << "  块大小:       " << stats.block_size << " 字节\n"
                  << "  总块数:       " << stats.total_blocks << "\n"
                  << "  活跃块:       " << stats.active_blocks << "\n"
                  << "  空闲块:       " << stats.free_blocks << "\n"
                  << "  累计分配:     " << stats.total_allocations << "\n"
                  << "  累计释放:     " << stats.total_frees << "\n"
                  << "  内存块数:     " << stats.chunks << "\n"
                  << "  总内存使用:   " << stats.memory_usage << " 字节 ("
                  << std::fixed << std::setprecision(2)
                  << stats.memory_usage / 1024.0 << " KB)\n";
    }

private:
    // 空闲链表节点 - 侵入式设计，不占用额外空间
    struct FreeNode {
        FreeNode* next;
    };

    // 分配一个新的内存块（chunk），将其切分为多个块并加入空闲链表
    void allocate_chunk() {
        // 使用 aligned_alloc 确保内存对齐
        // 对齐到 block_size_ 的整数倍，保证任何类型的对象都能正确对齐
        size_t chunk_bytes = block_size_ * blocks_per_chunk_;

        // std::malloc 返回的内存至少满足 max_align_t 对齐
        void* chunk = std::malloc(chunk_bytes);
        if (!chunk) {
            throw std::bad_alloc();
        }

        chunks_.push_back(chunk);

        // 将大块切分为小块，串成空闲链表
        auto* raw = static_cast<char*>(chunk);
        for (size_t i = 0; i < blocks_per_chunk_; ++i) {
            auto* node = reinterpret_cast<FreeNode*>(raw + i * block_size_);
            node->next = free_list_;
            free_list_ = node;
        }

        total_blocks_ += blocks_per_chunk_;
    }

    size_t block_size_;           // 每个块的大小
    size_t blocks_per_chunk_;     // 每个 chunk 中的块数
    FreeNode* free_list_ = nullptr;  // 空闲链表头
    std::vector<void*> chunks_;   // 所有分配的内存块（用于析构时释放）

    // 统计信息
    size_t total_allocated_;
    size_t total_freed_;
    size_t active_blocks_;
    size_t total_blocks_;
};

// ============================================================================
// 第二部分：对象池（类型安全的内存池包装）
// ============================================================================

/**
 * ObjectPool - 类型安全的对象池
 *
 * 在 FixedSizeMemoryPool 之上添加类型安全的构造/析构支持。
 * 模板参数 T 决定了每个块的大小。
 */
template <typename T>
class ObjectPool {
public:
    explicit ObjectPool(size_t initial_blocks = 1024)
        : pool_(sizeof(T), initial_blocks) {}

    /**
     * construct - 从池中分配并构造对象
     *
     * @param args  传递给 T 构造函数的参数
     * @return      指向新构造对象的指针
     */
    template <typename... Args>
    T* construct(Args&&... args) {
        void* mem = pool_.allocate();
        try {
            // placement new: 在已分配的内存上构造对象
            return ::new(mem) T(std::forward<Args>(args)...);
        } catch (...) {
            // 构造失败时归还内存
            pool_.deallocate(mem);
            throw;
        }
    }

    /**
     * destroy - 析构对象并归还内存给池
     */
    void destroy(T* ptr) {
        if (ptr) {
            ptr->~T();               // 调用析构函数
            pool_.deallocate(ptr);   // 归还内存
        }
    }

    void print_stats() const { pool_.print_stats(); }

private:
    FixedSizeMemoryPool pool_;
};

// ============================================================================
// 第三部分：性能对比测试
// ============================================================================

// 用于计时的辅助类
class Timer {
public:
    using Clock = std::chrono::high_resolution_clock;

    void start() { start_time_ = Clock::now(); }

    double elapsed_ms() const {
        auto end = Clock::now();
        return std::chrono::duration<double, std::milli>(end - start_time_).count();
    }

private:
    Clock::time_point start_time_;
};

// 测试用的结构体
struct TestObject {
    int id;
    double value;
    char data[48];

    TestObject() : id(0), value(0.0) { std::memset(data, 0, sizeof(data)); }
    TestObject(int i, double v) : id(i), value(v) { std::memset(data, i % 256, sizeof(data)); }
};

void print_section(const char* title) {
    std::cout << "\n========================================\n"
              << title << "\n"
              << "========================================\n";
}

int main() {
    std::cout << "===== C++ 内存池演示 =====\n";

    const int NUM_OBJECTS = 100000;
    const int NUM_ITERATIONS = 10;

    // ---- 演示 1: 内存池基本操作 ----
    print_section("1. 内存池基本操作");

    {
        // 创建一个块大小为 64 字节的内存池
        FixedSizeMemoryPool pool(64, 256);

        std::cout << "初始状态:\n";
        pool.print_stats();

        // 分配一些内存块
        std::vector<void*> ptrs;
        for (int i = 0; i < 100; ++i) {
            ptrs.push_back(pool.allocate());
        }

        std::cout << "\n分配 100 个块后:\n";
        pool.print_stats();

        // 释放一半
        for (int i = 0; i < 50; ++i) {
            pool.deallocate(ptrs.back());
            ptrs.pop_back();
        }

        std::cout << "\n释放 50 个块后:\n";
        pool.print_stats();

        // 释放剩余
        for (auto* ptr : ptrs) {
            pool.deallocate(ptr);
        }

        std::cout << "\n全部释放后:\n";
        pool.print_stats();
    }

    // ---- 演示 2: 对象池使用 ----
    print_section("2. 对象池 (ObjectPool) 使用");

    {
        ObjectPool<TestObject> pool(1024);

        // 从池中构造对象
        std::vector<TestObject*> objects;

        for (int i = 0; i < 10; ++i) {
            auto* obj = pool.construct(i, i * 3.14);
            objects.push_back(obj);
        }

        std::cout << "构造的对象:\n";
        for (const auto* obj : objects) {
            std::cout << "  id=" << obj->id << " value=" << obj->value << "\n";
        }

        std::cout << "\n池统计:\n";
        pool.print_stats();

        // 销毁对象
        for (auto* obj : objects) {
            pool.destroy(obj);
        }

        std::cout << "\n销毁对象后:\n";
        pool.print_stats();
    }

    // ---- 演示 3: 性能对比 - 内存池 vs 标准 new/delete ----
    print_section("3. 性能对比: 内存池 vs 标准 new/delete");

    Timer timer;
    double pool_total = 0.0;
    double new_total = 0.0;

    // 测试内存池
    for (int iter = 0; iter < NUM_ITERATIONS; ++iter) {
        FixedSizeMemoryPool pool(sizeof(TestObject), NUM_OBJECTS);

        timer.start();

        std::vector<void*> ptrs;
        ptrs.reserve(NUM_OBJECTS);

        // 分配阶段
        for (int i = 0; i < NUM_OBJECTS; ++i) {
            void* p = pool.allocate();
            // 使用 placement new 构造（模拟实际使用）
            ::new(p) TestObject(i, i * 1.1);
            ptrs.push_back(p);
        }

        // 释放阶段
        for (auto* p : ptrs) {
            static_cast<TestObject*>(p)->~TestObject();
            pool.deallocate(p);
        }

        pool_total += timer.elapsed_ms();
    }

    // 测试标准 new/delete
    for (int iter = 0; iter < NUM_ITERATIONS; ++iter) {
        timer.start();

        std::vector<TestObject*> ptrs;
        ptrs.reserve(NUM_OBJECTS);

        // 分配阶段
        for (int i = 0; i < NUM_OBJECTS; ++i) {
            auto* p = new TestObject(i, i * 1.1);
            ptrs.push_back(p);
        }

        // 释放阶段
        for (auto* p : ptrs) {
            delete p;
        }

        new_total += timer.elapsed_ms();
    }

    double pool_avg = pool_total / NUM_ITERATIONS;
    double new_avg = new_total / NUM_ITERATIONS;

    std::cout << std::fixed << std::setprecision(3);
    std::cout << "测试规模: " << NUM_OBJECTS << " 个对象 x " << NUM_ITERATIONS << " 轮\n\n";
    std::cout << "内存池 (allocate/deallocate):     " << pool_avg << " ms\n";
    std::cout << "标准 new/delete:                  " << new_avg << " ms\n";
    std::cout << "性能提升:                         "
              << std::setprecision(1) << (new_avg / pool_avg) << "x\n";

    // ---- 演示 4: 交替分配释放模式 ----
    print_section("4. 交替分配释放模式");

    {
        // 内存池在交替分配释放模式下优势更明显
        FixedSizeMemoryPool pool(sizeof(TestObject), 1024);

        double pool_time, new_time;

        // 池版本
        {
            timer.start();
            void* ptrs[1000];

            for (int round = 0; round < 100; ++round) {
                // 分配
                for (int i = 0; i < 1000; ++i) {
                    ptrs[i] = pool.allocate();
                }
                // 释放
                for (int i = 0; i < 1000; ++i) {
                    pool.deallocate(ptrs[i]);
                }
            }
            pool_time = timer.elapsed_ms();
        }

        // new/delete 版本
        {
            timer.start();
            TestObject* ptrs[1000];

            for (int round = 0; round < 100; ++round) {
                // 分配
                for (int i = 0; i < 1000; ++i) {
                    ptrs[i] = new TestObject;
                }
                // 释放
                for (int i = 0; i < 1000; ++i) {
                    delete ptrs[i];
                }
            }
            new_time = timer.elapsed_ms();
        }

        std::cout << "交替分配释放 100 轮 x 1000 个对象:\n";
        std::cout << std::fixed << std::setprecision(3);
        std::cout << "  内存池: " << pool_time << " ms\n";
        std::cout << "  new/delete: " << new_time << " ms\n";
        std::cout << "  性能提升: " << std::setprecision(1)
                  << (new_time / pool_time) << "x\n";
    }

    // ---- 演示 5: 内存碎片分析 ----
    print_section("5. 内存碎片分析");

    {
        std::cout << "内存池的优势之一是减少内存碎片。\n\n";

        FixedSizeMemoryPool pool(32, 100);

        // 模拟碎片化场景：分配很多块，然后每隔一个释放
        std::vector<void*> ptrs;
        for (int i = 0; i < 100; ++i) {
            ptrs.push_back(pool.allocate());
        }

        std::cout << "分配 100 个块后:\n";
        pool.print_stats();

        // 释放偶数索引的块
        for (size_t i = 0; i < ptrs.size(); i += 2) {
            pool.deallocate(ptrs[i]);
        }

        std::cout << "\n每隔一个释放后（模拟碎片化）:\n";
        pool.print_stats();
        std::cout << "  注意: 虽然有 50 个空闲块，但它们不连续\n";
        std::cout << "  内存池仍然可以正常分配新块（无外部碎片）\n";

        // 重新分配
        for (size_t i = 0; i < ptrs.size(); i += 2) {
            ptrs[i] = pool.allocate();
        }

        std::cout << "\n重新分配后:\n";
        pool.print_stats();
    }

    // ---- 演示 6: 对象池性能测试 ----
    print_section("6. 对象池性能测试");

    {
        ObjectPool<TestObject> obj_pool(4096);

        double obj_pool_time, std_time;

        // 对象池版本
        {
            timer.start();
            std::vector<TestObject*> ptrs;
            ptrs.reserve(NUM_OBJECTS);

            for (int i = 0; i < NUM_OBJECTS; ++i) {
                ptrs.push_back(obj_pool.construct(i, i * 0.5));
            }
            for (auto* p : ptrs) {
                obj_pool.destroy(p);
            }
            obj_pool_time = timer.elapsed_ms();
        }

        // 标准版本
        {
            timer.start();
            std::vector<TestObject*> ptrs;
            ptrs.reserve(NUM_OBJECTS);

            for (int i = 0; i < NUM_OBJECTS; ++i) {
                ptrs.push_back(new TestObject(i, i * 0.5));
            }
            for (auto* p : ptrs) {
                delete p;
            }
            std_time = timer.elapsed_ms();
        }

        std::cout << std::fixed << std::setprecision(3);
        std::cout << NUM_OBJECTS << " 个对象的构造/析构:\n";
        std::cout << "  对象池:     " << obj_pool_time << " ms\n";
        std::cout << "  new/delete: " << std_time << " ms\n";
        std::cout << "  性能提升:   " << std::setprecision(1)
                  << (std_time / obj_pool_time) << "x\n";

        std::cout << "\n对象池统计:\n";
        obj_pool.print_stats();
    }

    // ---- 总结 ----
    print_section("总结: 何时使用内存池");

    std::cout <<
        "适用场景:\n"
        "  1. 频繁分配/释放相同大小的对象（如网络包、游戏实体）\n"
        "  2. 对延迟敏感的实时系统（避免 new/delete 的不确定性）\n"
        "  3. 需要减少内存碎片的场景\n"
        "  4. 大量小对象的分配\n\n"
        "不适用场景:\n"
        "  1. 对象大小差异很大（需要不同大小的池）\n"
        "  2. 分配模式不可预测\n"
        "  3. 内存紧张，无法预分配大块内存\n";

    std::cout << "\n===== 演示结束 =====\n";
    return 0;
}
