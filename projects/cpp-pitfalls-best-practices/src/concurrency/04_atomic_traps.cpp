/**
 * @file 04_atomic_traps.cpp
 * @brief 原子操作陷阱示例
 *
 * 原子操作陷阱：原子操作使用不当导致的问题
 * 危害：数据竞争、性能下降、逻辑错误
 */

#include <iostream>
#include <thread>
#include <atomic>
#include <vector>
#include <chrono>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：复合操作非原子
 *
 * 问题：read-modify-write 操作不是原子的
 */
std::atomic<int> bad_counter{0};

void bad_increment() {
    for (int i = 0; i < 100000; i++) {
        // 这是原子的
        bad_counter++;
    }
}

void bad_read_modify_write() {
    // 但是这种复合操作不是原子的
    int old_val = bad_counter.load();
    // 在 load 和 store 之间，其他线程可能修改 counter
    bad_counter.store(old_val + 1);
}

/**
 * 错误示例 2：错误的内存序
 *
 * 问题：使用错误的内存序导致数据竞争
 */
std::atomic<bool> bad_flag{false};
int bad_data = 0;

void bad_writer() {
    bad_data = 42;
    bad_flag.store(true, std::memory_order_relaxed);  // 可能重排序
}

void bad_reader() {
    while (!bad_flag.load(std::memory_order_relaxed)) {}
    // 可能读到旧的 data 值
    std::cout << "data = " << bad_data << std::endl;
}

/**
 * 错误示例 3：原子操作与非原子操作混合
 *
 * 问题：原子变量的非原子访问
 */
std::atomic<int> bad_mixed{0};

void bad_mixed_access() {
    // 原子操作
    bad_mixed.store(42);
    // 非原子操作（通过指针）
    int* ptr = reinterpret_cast<int*>(&bad_mixed);
    *ptr = 100;  // 数据竞争！
}

/**
 * 错误示例 4：原子指针解引用
 *
 * 问题：原子指针的解引用不是原子的
 */
std::atomic<int*> bad_atomic_ptr{nullptr};

void bad_pointer_deref() {
    int* ptr = bad_atomic_ptr.load();
    if (ptr) {
        // 解引用不是原子的
        *ptr = 42;  // 可能与其他线程竞争
    }
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用原子 fetch_add
 *
 * 解决方案：使用原子的 read-modify-write 操作
 */
std::atomic<int> good_counter{0};

void good_increment() {
    for (int i = 0; i < 100000; i++) {
        good_counter.fetch_add(1, std::memory_order_relaxed);
    }
}

void good_fetch_add_example() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 10; i++) {
        threads.emplace_back(good_increment);
    }
    for (auto& t : threads) {
        t.join();
    }
    std::cout << "期望: 1000000, 实际: " << good_counter.load() << std::endl;
}

/**
 * 正确示例 2：使用正确的内存序
 *
 * 解决方案：根据需求选择正确的内存序
 */
std::atomic<bool> good_flag{false};
int good_data = 0;

void good_writer() {
    good_data = 42;
    // 使用 release 保证之前的写入对其他线程可见
    good_flag.store(true, std::memory_order_release);
}

void good_reader() {
    // 使用 acquire 保证看到 release 之前的写入
    while (!good_flag.load(std::memory_order_acquire)) {}
    std::cout << "data = " << good_data << std::endl;
}

void good_memory_order_example() {
    std::thread t1(good_writer);
    std::thread t2(good_reader);
    t1.join();
    t2.join();
}

/**
 * 正确示例 3：使用 compare_exchange
 *
 * 解决方案：使用 CAS 操作进行原子更新
 */
std::atomic<int> good_cas_counter{0};

void good_cas_increment() {
    int expected = good_cas_counter.load();
    while (!good_cas_counter.compare_exchange_weak(expected, expected + 1)) {
        // expected 已被更新为当前值
    }
}

void good_cas_example() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 10; i++) {
        threads.emplace_back(good_cas_increment);
    }
    for (auto& t : threads) {
        t.join();
    }
    std::cout << "CAS 计数器: " << good_cas_counter.load() << std::endl;
}

/**
 * 正确示例 4：使用 atomic_flag
 *
 * 解决方案：使用 atomic_flag 实现自旋锁
 */
std::atomic_flag good_spin_lock = ATOMIC_FLAG_INIT;

void good_spinlock_example() {
    // 自旋等待
    while (good_spin_lock.test_and_set(std::memory_order_acquire)) {
        // 忙等待
    }

    // 临界区
    std::cout << "获取锁" << std::endl;

    // 释放锁
    good_spin_lock.clear(std::memory_order_release);
}

void good_spinlock_demo() {
    std::thread t1(good_spinlock_example);
    std::thread t2(good_spinlock_example);
    t1.join();
    t2.join();
}

/**
 * 正确示例 5：使用 std::atomic_thread_fence
 *
 * 解决方案：使用内存屏障保证内存顺序
 */
std::atomic<bool> good_fence_flag{false};
int good_fence_data = 0;

void good_fence_writer() {
    good_fence_data = 42;
    std::atomic_thread_fence(std::memory_order_release);
    good_fence_flag.store(true, std::memory_order_relaxed);
}

void good_fence_reader() {
    while (!good_fence_flag.load(std::memory_order_relaxed)) {}
    std::atomic_thread_fence(std::memory_order_acquire);
    std::cout << "data = " << good_fence_data << std::endl;
}

void good_fence_example() {
    std::thread t1(good_fence_writer);
    std::thread t2(good_fence_reader);
    t1.join();
    t2.join();
}

/**
 * 正确示例 6：使用 atomic 的正确方式
 *
 * 解决方案：避免通过指针绕过原子性
 */
std::atomic<int> good_proper{0};

void good_proper_access() {
    // 始终使用原子操作
    good_proper.store(42);
    int val = good_proper.load();
    good_proper.fetch_add(1);
    std::cout << "值: " << good_proper.load() << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 原子操作陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 复合操作非原子" << std::endl;
    std::cout << "问题：read-modify-write 操作不是原子的" << std::endl;
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用 fetch_add" << std::endl;
    good_counter = 0;
    good_fetch_add_example();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用正确的内存序" << std::endl;
    good_memory_order_example();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 compare_exchange" << std::endl;
    good_cas_counter = 0;
    good_cas_example();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 atomic_flag" << std::endl;
    good_spinlock_demo();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用内存屏障" << std::endl;
    good_fence_example();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 正确的原子访问" << std::endl;
    good_proper_access();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
