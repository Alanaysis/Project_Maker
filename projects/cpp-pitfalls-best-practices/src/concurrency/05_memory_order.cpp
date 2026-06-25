/**
 * @file 05_memory_order.cpp
 * @brief 内存序陷阱示例
 *
 * 内存序陷阱：错误的内存序导致数据竞争和重排序问题
 * 危害：数据损坏、程序崩溃、难以调试的并发错误
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
 * 错误示例 1：使用 relaxed 内存序进行同步
 *
 * 问题：relaxed 不保证内存顺序，可能导致数据竞争
 */
std::atomic<bool> bad_flag{false};
int bad_data = 0;

void bad_relaxed_writer() {
    bad_data = 42;
    // relaxed 不保证 data 的写入在 flag 之前完成
    bad_flag.store(true, std::memory_order_relaxed);
}

void bad_relaxed_reader() {
    while (!bad_flag.load(std::memory_order_relaxed)) {}
    // 可能读到旧的 data 值
    std::cout << "data = " << bad_data << std::endl;
}

/**
 * 错误示例 2：错误的 acquire-release 配对
 *
 * 问题：acquire 必须与 release 配对使用
 */
std::atomic<int> bad_sync{0};
int bad_shared = 0;

void bad_mixed_writer() {
    bad_shared = 42;
    // 使用 release
    bad_sync.store(1, std::memory_order_release);
}

void bad_mixed_reader() {
    while (bad_sync.load(std::memory_order_acquire) == 0) {}
    // 正确：acquire 与 release 配对
    std::cout << "shared = " << bad_shared << std::endl;
}

void bad_mixed_reader_wrong() {
    // 使用 relaxed，不与 release 同步
    while (bad_sync.load(std::memory_order_relaxed) == 0) {}
    // 可能读到旧值
    std::cout << "shared = " << bad_shared << std::endl;
}

/**
 * 错误示例 3：seq_cst 与 relaxed 混用
 *
 * 问题：不同内存序混用可能导致意外行为
 */
std::atomic<int> bad_mixed_order{0};
int bad_mixed_data[2] = {0, 0};

void bad_mixed_order_writer() {
    bad_mixed_data[0] = 1;
    bad_mixed_order.store(1, std::memory_order_seq_cst);
    bad_mixed_data[1] = 2;
    bad_mixed_order.store(2, std::memory_order_relaxed);
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用 acquire-release 进行同步
 *
 * 解决方案：acquire-release 保证内存顺序
 */
std::atomic<bool> good_flag{false};
int good_data = 0;

void good_acquire_release_writer() {
    good_data = 42;
    // release 保证 data 的写入在 flag 之前完成
    good_flag.store(true, std::memory_order_release);
}

void good_acquire_release_reader() {
    // acquire 保证看到 release 之前的写入
    while (!good_flag.load(std::memory_order_acquire)) {}
    std::cout << "data = " << good_data << std::endl;
}

void good_acquire_release_example() {
    std::thread t1(good_acquire_release_writer);
    std::thread t2(good_acquire_release_reader);
    t1.join();
    t2.join();
}

/**
 * 正确示例 2：使用 seq_cst 进行全局同步
 *
 * 解决方案：seq_cst 保证全局顺序
 */
std::atomic<int> good_seq_cst{0};
int good_seq_data = 0;

void good_seq_cst_writer() {
    good_seq_data = 42;
    good_seq_cst.store(1, std::memory_order_seq_cst);
}

void good_seq_cst_reader() {
    while (good_seq_cst.load(std::memory_order_seq_cst) == 0) {}
    std::cout << "data = " << good_seq_data << std::endl;
}

void good_seq_cst_example() {
    std::thread t1(good_seq_cst_writer);
    std::thread t2(good_seq_cst_reader);
    t1.join();
    t2.join();
}

/**
 * 正确示例 3：使用 relaxed 进行计数
 *
 * 解决方案：对于独立计数，relaxed 足够
 */
std::atomic<int> good_relaxed_counter{0};

void good_relaxed_increment() {
    for (int i = 0; i < 100000; i++) {
        // relaxed 对于独立计数足够
        good_relaxed_counter.fetch_add(1, std::memory_order_relaxed);
    }
}

void good_relaxed_example() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 10; i++) {
        threads.emplace_back(good_relaxed_increment);
    }
    for (auto& t : threads) {
        t.join();
    }
    std::cout << "计数器: " << good_relaxed_counter.load() << std::endl;
}

/**
 * 正确示例 4：使用 release-consume (已弃用，用 acquire 替代)
 *
 * 解决方案：对于数据依赖，使用 acquire
 */
std::atomic<int*> good_consume_ptr{nullptr};
int good_consume_data = 0;

void good_consume_writer() {
    good_consume_data = 42;
    // release 保证 data 的写入在 ptr 之前完成
    good_consume_ptr.store(&good_consume_data, std::memory_order_release);
}

void good_consume_reader() {
    int* ptr = nullptr;
    while ((ptr = good_consume_ptr.load(std::memory_order_acquire)) == nullptr) {}
    // 数据依赖，保证看到正确的值
    std::cout << "data = " << *ptr << std::endl;
}

void good_consume_example() {
    std::thread t1(good_consume_writer);
    std::thread t2(good_consume_reader);
    t1.join();
    t2.join();
}

/**
 * 正确示例 5：使用 atomic_thread_fence
 *
 * 解决方案：使用内存屏障保证内存顺序
 */
std::atomic<bool> good_fence_flag{false};
int good_fence_data = 0;

void good_fence_writer() {
    good_fence_data = 42;
    // 内存屏障保证之前的写入完成
    std::atomic_thread_fence(std::memory_order_release);
    good_fence_flag.store(true, std::memory_order_relaxed);
}

void good_fence_reader() {
    while (!good_fence_flag.load(std::memory_order_relaxed)) {}
    // 内存屏障保证看到之前的写入
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
 * 正确示例 6：使用信号量模式
 *
 * 解决方案：使用 atomic 实现信号量
 */
class GoodSemaphore {
public:
    explicit GoodSemaphore(int count) : count_(count) {}

    void acquire() {
        int expected = count_.load(std::memory_order_acquire);
        while (expected <= 0 || !count_.compare_exchange_weak(expected, expected - 1,
                                                               std::memory_order_acq_rel)) {
            expected = count_.load(std::memory_order_acquire);
        }
    }

    void release() {
        count_.fetch_add(1, std::memory_order_release);
    }

private:
    std::atomic<int> count_;
};

void good_semaphore_example() {
    GoodSemaphore sem(1);
    std::vector<std::thread> threads;

    for (int i = 0; i < 5; i++) {
        threads.emplace_back([&sem, i]() {
            sem.acquire();
            std::cout << "线程 " << i << " 进入临界区" << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            std::cout << "线程 " << i << " 离开临界区" << std::endl;
            sem.release();
        });
    }

    for (auto& t : threads) {
        t.join();
    }
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 内存序陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 使用 relaxed 进行同步" << std::endl;
    std::cout << "问题：relaxed 不保证内存顺序" << std::endl;
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用 acquire-release" << std::endl;
    good_acquire_release_example();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 seq_cst" << std::endl;
    good_seq_cst_example();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 relaxed 计数" << std::endl;
    good_relaxed_counter = 0;
    good_relaxed_example();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 consume/acquire" << std::endl;
    good_consume_example();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用内存屏障" << std::endl;
    good_fence_example();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用信号量" << std::endl;
    good_semaphore_example();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
