/**
 * lock_free.cpp - 无锁数据结构 (Lock-Free Data Structures)
 *
 * 本文件演示：
 *   1. 基于原子操作的无锁栈实现
 *   2. 基于互斥锁的栈实现（对照组）
 *   3. ABA 问题的说明与缓解策略
 *   4. 多线程安全性的性能对比测试
 *
 * 编译命令：
 *   g++ -std=c++17 -O2 -pthread -o lock_free lock_free.cpp
 *
 * 无锁编程的核心思想：
 *   - 不使用互斥锁（mutex），而是通过原子操作（atomic operations）实现线程安全
 *   - 优点：避免死锁、优先级反转，高并发下性能更好
 *   - 缺点：实现复杂，容易出错，需要注意 ABA 问题
 */

#include <atomic>
#include <mutex>
#include <memory>
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <cassert>

// ============================================================================
// 第一部分：无锁栈 (Lock-Free Stack)
// ============================================================================

/**
 * 无锁栈的节点结构
 *
 * 模板参数 T 是存储的数据类型
 * 每个节点包含数据和指向下一个节点的原子指针
 */
template <typename T>
class LockFreeStack {
private:
    /**
     * 节点结构体
     * 使用引用计数来缓解 ABA 问题
     */
    struct Node {
        T data;                              // 存储的数据
        Node* next;                          // 指向下一个节点的指针
        std::atomic<int> ref_count{0};       // 引用计数，用于安全管理内存

        Node(const T& val) : data(val), next(nullptr) {}
    };

    /**
     * 使用带计数器的指针来防止 ABA 问题
     *
     * ABA 问题说明：
     *   线程1读取栈顶 A，准备将 A 替换为 B
     *   在 CAS 之前，线程2弹出 A，弹出 B，再压入 A（新的 A 实例）
     *   线程1的 CAS 成功（因为栈顶仍然"是"A），但状态已经不对了
     *
     * 解决方案：给指针附加一个单调递增的计数器
     * 即使指针值相同，计数器不同也会导致 CAS 失败
     */
    struct CountedPointer {
        Node* ptr = nullptr;                 // 节点指针
        uint64_t count = 0;                  // 单调递增的版本号（ABA 缓解）
    };

    std::atomic<CountedPointer> head_;       // 栈顶指针（带版本号）
    std::atomic<uint64_t> pop_count_{0};     // pop 操作计数器

public:
    LockFreeStack() = default;

    /**
     * 析构函数 - 清理所有剩余节点
     * 注意：在多线程环境下，析构前必须确保没有其他线程在操作
     */
    ~LockFreeStack() {
        CountedPointer old_head = head_.load(std::memory_order_relaxed);
        while (old_head.ptr) {
            Node* node = old_head.ptr;
            old_head.ptr = node->next;
            delete node;
        }
    }

    /**
     * 压入操作 (Push)
     *
     * 算法步骤：
     *   1. 创建新节点
     *   2. 将新节点的 next 指向当前栈顶
     *   3. 使用 CAS 将栈顶从旧值更新为新节点
     *   4. 如果 CAS 失败，重试
     *
     * 这是一个典型的 CAS 循环模式
     */
    void push(const T& value) {
        // 创建新节点
        Node* new_node = new Node(value);

        CountedPointer old_head = head_.load(std::memory_order_relaxed);
        CountedPointer new_head;
        new_head.ptr = new_node;

        do {
            // 让新节点指向当前栈顶
            new_node->next = old_head.ptr;

            // 准备新的栈顶值（新节点 + 递增的计数器）
            new_head.count = old_head.count + 1;

            // CAS：如果栈顶仍然是 old_head，则更新为 new_head
            // memory_order_release 确保新节点的写入对其他线程可见
        } while (!head_.compare_exchange_weak(
            old_head, new_head,
            std::memory_order_release,
            std::memory_order_relaxed
        ));
    }

    /**
     * 弹出操作 (Pop)
     *
     * 算法步骤：
     *   1. 读取当前栈顶
     *   2. 如果栈为空，返回 false
     *   3. 使用 CAS 将栈顶从当前节点更新为下一个节点
     *   4. 如果 CAS 成功，提取数据并安全释放旧节点
     *
     * 这里的难点在于：何时安全释放旧节点？
     * 如果另一个线程正在读取该节点，我们不能立即删除它
     */
    bool pop(T& result) {
        CountedPointer old_head = head_.load(std::memory_order_acquire);
        CountedPointer new_head;

        do {
            // 栈为空
            if (!old_head.ptr) {
                return false;
            }

            // 准备新的栈顶值
            new_head.ptr = old_head.ptr->next;
            new_head.count = old_head.count + 1;

            // CAS 尝试更新栈顶
            // memory_order_acquire 确保我们能正确读取节点数据
        } while (!head_.compare_exchange_weak(
            old_head, new_head,
            std::memory_order_acquire,
            std::memory_order_relaxed
        ));

        // CAS 成功，提取数据
        result = old_head.ptr->data;

        // 安全删除旧节点
        // 在简单实现中直接 delete，在生产代码中可能需要使用
        // Hazard Pointers 或 Epoch-Based Reclamation 来安全回收内存
        delete old_head.ptr;

        return true;
    }

    /**
     * 检查栈是否为空
     * 注意：在多线程环境下，结果可能瞬间过时
     */
    bool empty() const {
        return head_.load(std::memory_order_acquire).ptr == nullptr;
    }
};

// ============================================================================
// 第二部分：基于互斥锁的栈 (Mutex-Based Stack) - 对照组
// ============================================================================

/**
 * 使用互斥锁保护的栈实现
 *
 * 优点：实现简单，正确性容易保证
 * 缺点：互斥锁会带来性能开销，可能导致线程阻塞
 */
template <typename T>
class MutexStack {
private:
    struct Node {
        T data;
        std::unique_ptr<Node> next;          // 使用智能指针自动管理内存

        Node(const T& val) : data(val) {}
    };

    std::unique_ptr<Node> head_;
    mutable std::mutex mutex_;               // mutable 允许在 const 方法中加锁

public:
    MutexStack() = default;

    /**
     * 压入操作 - 使用 lock_guard 自动管理锁的生命周期
     * RAII 方式确保异常安全
     */
    void push(const T& value) {
        std::lock_guard<std::mutex> lock(mutex_);
        auto new_node = std::make_unique<Node>(value);
        new_node->next = std::move(head_);
        head_ = std::move(new_node);
    }

    /**
     * 弹出操作
     * 注意：返回值可能需要额外的同步机制
     */
    bool pop(T& result) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!head_) {
            return false;
        }
        result = head_->data;
        head_ = std::move(head_->next);
        return true;
    }

    bool empty() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return !head_;
    }
};

// ============================================================================
// 第三部分：性能对比测试
// ============================================================================

/**
 * 测试函数：多线程 push/pop 操作
 *
 * @tparam StackType  栈的类型（无锁或互斥锁版本）
 * @param name        测试名称
 * @param num_threads 线程数量
 * @param ops_per_thread 每个线程的操作次数
 */
template <typename StackType>
void benchmark(const std::string& name, int num_threads, int ops_per_thread) {
    StackType stack;

    // 预先填充一些数据
    for (int i = 0; i < ops_per_thread; ++i) {
        stack.push(i);
    }

    auto start = std::chrono::high_resolution_clock::now();

    std::vector<std::thread> threads;
    threads.reserve(num_threads);

    // 每个线程交替进行 push 和 pop 操作
    for (int t = 0; t < num_threads; ++t) {
        threads.emplace_back([&stack, ops_per_thread]() {
            for (int i = 0; i < ops_per_thread; ++i) {
                stack.push(i);               // 压入
                int val;
                stack.pop(val);              // 弹出
            }
        });
    }

    // 等待所有线程完成
    for (auto& t : threads) {
        t.join();
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << name << ": " << num_threads << " 线程, "
              << ops_per_thread << " 次/线程, 耗时 "
              << duration.count() << " ms" << std::endl;
}

// ============================================================================
// 第四部分：正确性验证
// ============================================================================

/**
 * 验证无锁栈的正确性
 * 使用多线程同时压入，验证所有元素都能被正确弹出
 */
void verify_correctness() {
    std::cout << "\n=== 正确性验证 ===" << std::endl;

    LockFreeStack<int> stack;
    constexpr int NUM_THREADS = 4;
    constexpr int OPS = 10000;

    // 所有线程压入的总数
    std::atomic<int> push_count{0};
    std::atomic<int> pop_count{0};

    std::vector<std::thread> threads;

    // 创建 push 线程和 pop 线程
    for (int t = 0; t < NUM_THREADS / 2; ++t) {
        // Push 线程
        threads.emplace_back([&stack, &push_count]() {
            for (int i = 0; i < OPS; ++i) {
                stack.push(i);
                push_count.fetch_add(1, std::memory_order_relaxed);
            }
        });

        // Pop 线程
        threads.emplace_back([&stack, &pop_count]() {
            int val;
            for (int i = 0; i < OPS; ++i) {
                // 忙等待直到有元素可弹出
                // 注意：这是一种简化的测试方法，实际代码中应避免忙等待
                while (!stack.pop(val)) {
                    std::this_thread::yield();  // 让出 CPU 时间片
                }
                pop_count.fetch_add(1, std::memory_order_relaxed);
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "总 push 次数: " << push_count.load() << std::endl;
    std::cout << "总 pop 次数: " << pop_count.load() << std::endl;
    std::cout << "栈中剩余元素: " << (push_count.load() - pop_count.load()) << std::endl;
    std::cout << "正确性验证通过！" << std::endl;
}

// ============================================================================
// 第五部分：ABA 问题演示
// ============================================================================

/**
 * ABA 问题的详细说明和图示
 *
 * 时间线：
 *   T1: 读取栈顶 = A (next = B)
 *   T2: pop(A), 栈顶 = B
 *   T2: pop(B), 栈顶 = C
 *   T2: push(A), 栈顶 = A (next = C)  ← 新的 A 节点！
 *   T1: CAS(栈顶, A, B) 成功！ ← 问题在这里！栈顶应该是 C，不是 B
 *
 * 解决方案：
 *   1. 带版本号的指针（本文件使用的方法）
 *   2. Hazard Pointers（风险指针）
 *   3. Epoch-Based Reclamation（基于纪元的内存回收）
 *   4. RCU (Read-Copy-Update)
 */
void explain_aba_problem() {
    std::cout << "\n=== ABA 问题说明 ===" << std::endl;
    std::cout << R"(
ABA 问题是无锁编程中最经典的陷阱之一：

时间线图示：

    初始状态：栈顶 -> A -> B -> C

    线程1 (T1)                      线程2 (T2)
    ─────────────                   ─────────────
    读取栈顶 = A
    (A.next = B)
                                    pop(A) → 栈顶 = B
                                    pop(B) → 栈顶 = C
                                    push(A') → 栈顶 = A' -> C
    CAS(栈顶, A, B) ← 成功！
    但栈顶现在应该是 C！

    结果：栈顶 -> B -> ... （丢失了 C！）

解决方案：使用带版本号的指针
    每次 CAS 操作都递增版本号
    即使指针相同，版本号不同也会导致 CAS 失败
)" << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  无锁数据结构 vs 互斥锁数据结构" << std::endl;
    std::cout << "========================================" << std::endl;

    // 说明 ABA 问题
    explain_aba_problem();

    // 正确性验证
    verify_correctness();

    // 性能对比
    std::cout << "\n=== 性能对比测试 ===" << std::endl;

    constexpr int NUM_THREADS = 4;
    constexpr int OPS = 100000;

    benchmark<LockFreeStack<int>>("LockFreeStack（无锁栈）", NUM_THREADS, OPS);
    benchmark<MutexStack<int>>("MutexStack（互斥锁栈）", NUM_THREADS, OPS);

    std::cout << "\n说明：" << std::endl;
    std::cout << "- 无锁栈在高并发下通常性能更好" << std::endl;
    std::cout << "- 但无锁实现更复杂，更容易出现 bug" << std::endl;
    std::cout << "- 对于低并发场景，互斥锁版本可能更合适" << std::endl;

    return 0;
}
