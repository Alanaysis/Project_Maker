/**
 * custom_allocator.cpp - 自定义分配器 (Custom Allocator)
 *
 * 本文件演示了 C++ 中自定义内存分配器的实现和使用，包括：
 *   1. 计数分配器 (Counting Allocator) - 统计内存分配次数和总量
 *   2. 简易池分配器概念 (Pool Allocator Concept) - 预分配内存块
 *   3. 与 std::vector 等容器配合使用
 *   4. 分配器传播 (Allocator Propagation) - C++11/17 特性
 *
 * 编译: g++ -std=c++17 -O2 -o custom_allocator custom_allocator.cpp
 */

#include <iostream>
#include <vector>
#include <list>
#include <memory>
#include <type_traits>
#include <cassert>
#include <cstring>

// ============================================================================
// 第一部分：计数分配器 (Counting Allocator)
// ============================================================================
// 计数分配器是一个"装饰器"模式的分配器，它包装了标准分配器，
// 在每次分配/释放时记录统计信息。这在调试内存泄漏和分析内存使用模式时非常有用。

// 全局统计结构，用于记录所有 CountingAllocator 实例的分配信息
struct AllocationStats {
    size_t total_allocated = 0;      // 累计分配的总字节数
    size_t total_deallocated = 0;    // 累计释放的总字节数
    size_t allocation_count = 0;     // 分配次数
    size_t deallocation_count = 0;   // 释放次数
    size_t current_usage = 0;        // 当前正在使用的字节数
    size_t peak_usage = 0;           // 峰值内存使用量

    void reset() {
        total_allocated = 0;
        total_deallocated = 0;
        allocation_count = 0;
        deallocation_count = 0;
        current_usage = 0;
        peak_usage = 0;
    }

    void print() const {
        std::cout << "  分配次数: " << allocation_count << "\n"
                  << "  释放次数: " << deallocation_count << "\n"
                  << "  累计分配: " << total_allocated << " 字节\n"
                  << "  累计释放: " << total_deallocated << " 字节\n"
                  << "  当前使用: " << current_usage << " 字节\n"
                  << "  峰值使用: " << peak_usage << " 字节\n";
    }
};

// 全局统计实例
static AllocationStats g_stats;

/**
 * CountingAllocator - 计数分配器
 *
 * 模板参数:
 *   T - 分配器管理的元素类型
 *
 * 这个分配器遵循 C++ Allocator 要求 (AllocatorRequirements)，
 * 可以直接用于 std::vector, std::list, std::map 等标准容器。
 *
 * 关键设计点:
 *   - rebind 成员：允许容器为内部节点类型（如链表节点）分配内存
 *   - propagate_on_container_move_assignment：控制分配器在容器移动时的行为
 *   - operator== 和 operator!=：比较两个分配器是否等价
 */
template <typename T>
class CountingAllocator {
public:
    // 必须定义的类型别名，满足 Allocator 要求
    using value_type = T;
    using pointer = T*;
    using const_pointer = const T*;
    using reference = T&;
    using const_reference = const T&;
    using size_type = std::size_t;
    using difference_type = std::ptrdiff_t;

    // rebind 成员模板：允许容器为其他类型分配内存
    // 例如 std::list<T> 内部需要为 list_node<T> 分配内存，而不是 T 本身
    template <typename U>
    struct rebind {
        using other = CountingAllocator<U>;
    };

    // 分配器传播控制 traits（C++11 起）
    // 当容器复制/移动/交换时，是否也复制/移动/交换分配器
    using propagate_on_container_copy_assignment = std::false_type;
    using propagate_on_container_move_assignment = std::true_type;
    using propagate_on_container_swap = std::true_type;

    // 默认构造
    CountingAllocator() noexcept = default;

    // 从其他类型转换的构造函数（rebind 时使用）
    template <typename U>
    CountingAllocator(const CountingAllocator<U>&) noexcept {}

    /**
     * allocate - 分配内存
     *
     * @param n  需要分配的元素个数
     * @return   指向分配内存的指针
     *
     * 注意：这里使用 ::operator new 进行底层分配，
     * 它只分配原始内存，不调用构造函数。
     */
    T* allocate(size_type n) {
        if (n == 0) return nullptr;

        size_t bytes = n * sizeof(T);

        // 使用标准分配函数获取原始内存
        // static_cast<T*> 是安全的，因为 ::operator new 返回 void*
        T* ptr = static_cast<T*>(::operator new(bytes));

        // 更新统计信息
        g_stats.total_allocated += bytes;
        g_stats.allocation_count++;
        g_stats.current_usage += bytes;
        if (g_stats.current_usage > g_stats.peak_usage) {
            g_stats.peak_usage = g_stats.current_usage;
        }

        return ptr;
    }

    /**
     * deallocate - 释放内存
     *
     * @param ptr  要释放的指针
     * @param n    原始分配时的元素个数（用于统计）
     *
     * 注意：n 参数在标准分配器中可能不被使用，
     * 但自定义分配器可以利用它来优化释放策略。
     */
    void deallocate(T* ptr, size_type n) {
        if (!ptr) return;

        size_t bytes = n * sizeof(T);

        // 释放原始内存
        ::operator delete(ptr);

        // 更新统计信息
        g_stats.total_deallocated += bytes;
        g_stats.deallocation_count++;
        g_stats.current_usage -= bytes;
    }

    /**
     * construct - 在已分配的内存上构造对象（C++11/14 风格）
     *
     * C++20 中分配器不再需要 construct/destroy，
     * 容器会直接使用 std::allocator_traits::construct。
     * 这里保留是为了兼容性和演示目的。
     */
    template <typename U, typename... Args>
    void construct(U* ptr, Args&&... args) {
        // placement new：在已有内存上构造对象
        ::new(static_cast<void*>(ptr)) U(std::forward<Args>(args)...);
    }

    /**
     * destroy - 析构对象但不释放内存
     */
    template <typename U>
    void destroy(U* ptr) {
        ptr->~U();
    }

    // 两个 CountingAllocator 实例总是等价的（无状态分配器）
    // 这意味着一个分配器分配的内存可以被另一个同类型的分配器释放
    template <typename U>
    bool operator==(const CountingAllocator<U>&) const noexcept { return true; }

    template <typename U>
    bool operator!=(const CountingAllocator<U>&) const noexcept { return false; }
};

// ============================================================================
// 第二部分：简易池分配器概念 (Pool Allocator Concept)
// ============================================================================
// 池分配器预先分配一大块内存，然后从中切分小块给使用者。
// 优点：减少系统调用次数，提高分配速度，减少内存碎片。
// 这里展示的是概念演示，完整的池分配器实现在 memory_pool.cpp 中。

template <typename T, size_t BlockSize = 1024>
class SimplePoolAllocator {
public:
    using value_type = T;
    using size_type = std::size_t;

    template <typename U>
    struct rebind {
        using other = SimplePoolAllocator<U, BlockSize>;
    };

private:
    // 内存块结构：每个块包含一个固定大小的内存区域
    struct Block {
        alignas(T) char data[BlockSize * sizeof(T)];  // 确保对齐
        size_t used = 0;   // 已使用的元素个数
        Block* next = nullptr;

        T* allocate_slot() {
            if (used >= BlockSize) return nullptr;
            // 计算下一个可用位置
            T* slot = reinterpret_cast<T*>(data) + used;
            used++;
            return slot;
        }
    };

    Block* current_block_ = nullptr;  // 当前正在使用的内存块
    size_t total_blocks_ = 0;

    // 分配一个新的内存块
    void allocate_new_block() {
        Block* new_block = new Block;
        new_block->next = current_block_;
        current_block_ = new_block;
        total_blocks_++;
    }

public:
    SimplePoolAllocator() = default;

    template <typename U>
    SimplePoolAllocator(const SimplePoolAllocator<U, BlockSize>&) noexcept {}

    ~SimplePoolAllocator() {
        // 释放所有内存块
        Block* current = current_block_;
        while (current) {
            Block* next = current->next;
            delete current;
            current = next;
        }
    }

    T* allocate(size_type n) {
        // 池分配器通常只处理单个元素的分配
        // 对于批量分配，回退到标准分配
        if (n > 1) {
            return static_cast<T*>(::operator new(n * sizeof(T)));
        }

        // 如果当前块已满或不存在，分配新块
        if (!current_block_ || current_block_->used >= BlockSize) {
            allocate_new_block();
        }

        return current_block_->allocate_slot();
    }

    void deallocate(T* ptr, size_type) {
        // 池分配器通常不单独释放内存块
        // 内存会在分配器析构时统一释放
        // 这就是为什么池分配器能显著提高性能
        (void)ptr;  // 标记为有意不使用
    }

    // 获取池统计信息
    size_t block_count() const { return total_blocks_; }
    size_t capacity() const { return total_blocks_ * BlockSize; }

    template <typename U>
    bool operator==(const SimplePoolAllocator<U, BlockSize>&) const noexcept { return true; }

    template <typename U>
    bool operator!=(const SimplePoolAllocator<U, BlockSize>&) const noexcept { return false; }
};

// ============================================================================
// 第三部分：演示和测试
// ============================================================================

// 辅助函数：打印分隔线
void print_section(const char* title) {
    std::cout << "\n========================================\n"
              << title << "\n"
              << "========================================\n";
}

int main() {
    std::cout << "===== C++ 自定义分配器演示 =====\n";

    // ---- 演示 1: 计数分配器基本使用 ----
    print_section("1. 计数分配器 - 基本使用");

    g_stats.reset();

    {
        // 创建一个使用计数分配器的 vector
        std::vector<int, CountingAllocator<int>> vec;

        // 预分配空间，观察分配行为
        std::cout << "reserve(100) 前的统计:\n";
        g_stats.print();

        vec.reserve(100);
        std::cout << "\nreserve(100) 后的统计:\n";
        g_stats.print();

        // 添加元素（不会触发新的分配，因为已经 reserve 了）
        for (int i = 0; i < 100; ++i) {
            vec.push_back(i);
        }
        std::cout << "\n添加 100 个元素后的统计:\n";
        g_stats.print();
    }

    std::cout << "\nvector 销毁后的统计:\n";
    g_stats.print();

    // ---- 演示 2: 计数分配器 - 观察重新分配 ----
    print_section("2. 计数分配器 - 观察动态扩容");

    g_stats.reset();

    {
        std::vector<int, CountingAllocator<int>> vec;

        // 不预分配，观察扩容过程
        for (int i = 0; i < 10; ++i) {
            vec.push_back(i);
            std::cout << "size=" << vec.size()
                      << " capacity=" << vec.capacity()
                      << " 分配次数=" << g_stats.allocation_count
                      << " 当前使用=" << g_stats.current_usage << " 字节\n";
        }
    }

    // ---- 演示 3: 计数分配器 - 用于不同容器 ----
    print_section("3. 计数分配器 - 用于 std::list");

    g_stats.reset();

    {
        // std::list 内部节点包含前后指针，所以每个节点比 sizeof(T) 更大
        // 通过 rebind 机制，分配器可以为这些内部节点分配内存
        std::list<int, CountingAllocator<int>> lst;

        for (int i = 0; i < 10; ++i) {
            lst.push_back(i);
        }

        std::cout << "list 添加 10 个元素后:\n";
        g_stats.print();
        std::cout << "注意: list 的每次 push_back 都需要分配一个节点\n"
                  << "节点大小通常 > sizeof(int)，因为包含前后指针\n";
    }

    // ---- 演示 4: 池分配器概念 ----
    print_section("4. 池分配器概念演示");

    g_stats.reset();

    {
        SimplePoolAllocator<int, 64> pool_alloc;
        std::vector<int, SimplePoolAllocator<int, 64>> vec(pool_alloc);

        for (int i = 0; i < 200; ++i) {
            vec.push_back(i);
        }

        std::cout << "池分配器状态:\n"
                  << "  内存块数: " << pool_alloc.block_count() << "\n"
                  << "  总容量: " << pool_alloc.capacity() << " 个元素\n";

        std::cout << "\n全局分配器统计（池分配器不使用全局分配器）:\n";
        g_stats.print();
    }

    // ---- 演示 5: 分配器传播 ----
    print_section("5. 分配器传播行为");

    g_stats.reset();

    {
        // 创建源 vector
        std::vector<int, CountingAllocator<int>> source;
        for (int i = 0; i < 10; ++i) {
            source.push_back(i * 10);
        }

        std::cout << "源 vector 创建后:\n";
        g_stats.print();

        size_t alloc_count_before = g_stats.allocation_count;

        // 移动语义：propagate_on_container_move_assignment = true
        // 意味着移动赋值时，分配器也会被移动
        std::vector<int, CountingAllocator<int>> dest;
        dest = std::move(source);

        std::cout << "\n移动赋值后:\n";
        std::cout << "  移动赋值触发的分配次数: "
                  << (g_stats.allocation_count - alloc_count_before) << "\n";
        std::cout << "  （无状态分配器移动时不会触发新分配，直接接管内存指针）\n";

        // 验证数据已正确移动
        std::cout << "  dest 的内容: ";
        for (const auto& v : dest) {
            std::cout << v << " ";
        }
        std::cout << "\n  source 的大小: " << source.size()
                  << " （移动后为空）\n";
    }

    // ---- 演示 6: 自定义类型的分配器 ----
    print_section("6. 自定义类型 + 计数分配器");

    g_stats.reset();

    {
        struct LargeObject {
            char data[256];
            int id;

            LargeObject() : id(0) { std::memset(data, 0, sizeof(data)); }
            explicit LargeObject(int i) : id(i) { std::memset(data, i, sizeof(data)); }

            ~LargeObject() {
                // 析构函数中可以做清理工作
            }
        };

        std::cout << "LargeObject 大小: " << sizeof(LargeObject) << " 字节\n\n";

        std::vector<LargeObject, CountingAllocator<LargeObject>> objects;
        objects.reserve(10);

        for (int i = 0; i < 10; ++i) {
            objects.emplace_back(i);
        }

        std::cout << "创建 10 个 LargeObject 后:\n";
        g_stats.print();
    }

    std::cout << "\n===== 演示结束 =====\n";
    return 0;
}
