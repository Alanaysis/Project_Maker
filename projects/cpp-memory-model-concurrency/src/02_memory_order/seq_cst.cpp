/**
 * memory_order_seq_cst
 *
 * 最强的内存序（默认）：
 * 1. 保证全局一致的顺序
 * 2. 所有线程看到相同的操作顺序
 * 3. 性能最差，但最安全
 * 4. 适合需要严格顺序的场景
 *
 * 编译：g++ -std=c++17 -pthread seq_cst.cpp -o seq_cst
 */

#include <iostream>
#include <atomic>
#include <thread>
#include <vector>
#include <cassert>

// 示例1：基本用法
void basic_seq_cst() {
    std::cout << "=== 基本 seq_cst 用法 ===" << std::endl;

    std::atomic<int> counter{0};

    auto increment = [&counter](int n) {
        for (int i = 0; i < n; ++i) {
            // seq_cst 是默认内存序
            counter.fetch_add(1, std::memory_order_seq_cst);
        }
    };

    std::thread t1(increment, 100000);
    std::thread t2(increment, 100000);

    t1.join();
    t2.join();

    std::cout << "最终计数: " << counter.load() << std::endl;
    std::cout << "期望值: 200000" << std::endl;
}

// 示例2：seq_cst 保证全局顺序
void global_ordering() {
    std::cout << "\n=== seq_cst 保证全局顺序 ===" << std::endl;

    std::atomic<int> x{0};
    std::atomic<int> y{0};

    // 使用 seq_cst 时，不可能出现 x=1, y=1 但两个线程都读到 0
    std::atomic<int> r1{0};
    std::atomic<int> r2{0};

    // 线程 1：写 x，读 y
    std::thread t1([&]() {
        x.store(1, std::memory_order_seq_cst);
        r1.store(y.load(std::memory_order_seq_cst), std::memory_order_seq_cst);
    });

    // 线程 2：写 y，读 x
    std::thread t2([&]() {
        y.store(1, std::memory_order_seq_cst);
        r2.store(x.load(std::memory_order_seq_cst), std::memory_order_seq_cst);
    });

    t1.join();
    t2.join();

    std::cout << "r1 = " << r1.load() << ", r2 = " << r2.load() << std::endl;
    std::cout << "使用 seq_cst，至少一个线程能看到对方的写入" << std::endl;
    std::cout << "不可能出现 r1=0 且 r2=0" << std::endl;
}

// 示例3：seq_cst vs acquire-release
void compare_seq_cst_acq_rel() {
    std::cout << "\n=== seq_cst vs acquire-release ===" << std::endl;

    const int iterations = 1000000;
    std::atomic<int> counter{0};

    // seq_cst
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_seq_cst);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto seq_cst_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    // acquire-release
    counter.store(0);
    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_acq_rel);
    }
    end = std::chrono::high_resolution_clock::now();
    auto acq_rel_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    // relaxed
    counter.store(0);
    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_relaxed);
    }
    end = std::chrono::high_resolution_clock::now();
    auto relaxed_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "seq_cst:     " << seq_cst_time.count() << " us" << std::endl;
    std::cout << "acq_rel:     " << acq_rel_time.count() << " us" << std::endl;
    std::cout << "relaxed:     " << relaxed_time.count() << " us" << std::endl;
}

// 示例4：seq_cst 实现互斥锁
class SeqCstMutex {
public:
    void lock() {
        while (flag_.exchange(true, std::memory_order_seq_cst)) {
            // 自旋等待
        }
    }

    void unlock() {
        flag_.store(false, std::memory_order_seq_cst);
    }

private:
    std::atomic<bool> flag_{false};
};

void seq_cst_mutex_demo() {
    std::cout << "\n=== seq_cst 实现互斥锁 ===" << std::endl;

    SeqCstMutex mutex;
    int counter = 0;

    auto increment = [&]() {
        for (int i = 0; i < 10000; ++i) {
            mutex.lock();
            counter++;
            mutex.unlock();
        }
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back(increment);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "最终计数: " << counter << std::endl;
    std::cout << "期望值: 40000" << std::endl;
}

// 示例5：seq_cst 实现信号量
class SeqCstSemaphore {
public:
    SeqCstSemaphore(int initial) : count_(initial) {}

    void acquire() {
        while (true) {
            int current = count_.load(std::memory_order_seq_cst);
            if (current > 0) {
                if (count_.compare_exchange_weak(current, current - 1,
                    std::memory_order_seq_cst)) {
                    return;
                }
            }
        }
    }

    void release() {
        count_.fetch_add(1, std::memory_order_seq_cst);
    }

private:
    std::atomic<int> count_;
};

void seq_cst_semaphore_demo() {
    std::cout << "\n=== seq_cst 实现信号量 ===" << std::endl;

    SeqCstSemaphore semaphore(2);  // 最多 2 个并发
    std::atomic<int> active{0};
    std::atomic<int> max_active{0};

    auto worker = [&](int id) {
        semaphore.acquire();

        int current = active.fetch_add(1) + 1;
        // 更新最大并发数
        int expected = max_active.load();
        while (current > expected &&
               !max_active.compare_exchange_weak(expected, current)) {}

        std::cout << "Worker " << id << " 开始 (活跃: " << current << ")" << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        std::cout << "Worker " << id << " 结束" << std::endl;

        active.fetch_sub(1);
        semaphore.release();
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < 5; ++i) {
        threads.emplace_back(worker, i);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "最大并发数: " << max_active.load() << std::endl;
}

int main() {
    std::cout << "C++ 内存序：memory_order_seq_cst" << std::endl;
    std::cout << "==================================\n" << std::endl;

    basic_seq_cst();
    global_ordering();
    compare_seq_cst_acq_rel();
    seq_cst_mutex_demo();
    seq_cst_semaphore_demo();

    return 0;
}
