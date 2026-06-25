/**
 * 原子标志 (atomic_flag)
 *
 * atomic_flag 的特点：
 * 1. 唯一保证无锁的原子类型
 * 2. 只支持 test_and_set 和 clear
 * 3. 适合实现自旋锁
 * 4. C++20 增加了 test() 方法
 *
 * 编译：g++ -std=c++17 -pthread atomic_flag.cpp -o atomic_flag
 */

#include <iostream>
#include <atomic>
#include <thread>
#include <vector>
#include <chrono>

// 示例1：基本用法
void basic_atomic_flag() {
    std::cout << "=== 基本 atomic_flag 用法 ===" << std::endl;

    // 初始化为 clear 状态
    std::atomic_flag flag = ATOMIC_FLAG_INIT;

    // test_and_set：测试并设置
    bool was_set = flag.test_and_set();
    std::cout << "test_and_set: 之前=" << (was_set ? "set" : "clear")
              << ", 现在=set" << std::endl;

    // clear：清除标志
    flag.clear();
    std::cout << "clear 后: clear" << std::endl;

    // C++20: test() 方法
    #if __cplusplus >= 202002L
    flag.test_and_set();
    bool is_set = flag.test();
    std::cout << "test(): " << (is_set ? "set" : "clear") << std::endl;
    #endif
}

// 示例2：自旋锁实现
class SpinLock {
public:
    void lock() {
        while (flag_.test_and_set(std::memory_order_acquire)) {
            // 自旋等待
            #if defined(__x86_64__) || defined(__i386__)
            __builtin_ia32_pause();  // x86 优化：降低功耗
            #endif
        }
    }

    void unlock() {
        flag_.clear(std::memory_order_release);
    }

private:
    std::atomic_flag flag_ = ATOMIC_FLAG_INIT;
};

void spinlock_demo() {
    std::cout << "\n=== 自旋锁演示 ===" << std::endl;

    SpinLock mutex;
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

// 示例3：带 backoff 的自旋锁
class BackoffSpinLock {
public:
    void lock() {
        int backoff = 1;
        while (flag_.test_and_set(std::memory_order_acquire)) {
            // 指数退避
            for (int i = 0; i < backoff; ++i) {
                #if defined(__x86_64__) || defined(__i386__)
                __builtin_ia32_pause();
                #endif
            }
            backoff = std::min(backoff * 2, max_backoff_);
        }
    }

    void unlock() {
        flag_.clear(std::memory_order_release);
    }

private:
    std::atomic_flag flag_ = ATOMIC_FLAG_INIT;
    static constexpr int max_backoff_ = 1024;
};

// 示例4：TAS (Test-And-Set) 标志
class TASFlag {
public:
    bool test_and_set() {
        return flag_.test_and_set(std::memory_order_seq_cst);
    }

    void clear() {
        flag_.clear(std::memory_order_seq_cst);
    }

    bool is_set() const {
        // C++20: 使用 test()
        #if __cplusplus >= 202002L
        return flag_.test(std::memory_order_seq_cst);
        #else
        // C++17: 无法无锁地测试
        return false;
        #endif
    }

private:
    std::atomic_flag flag_ = ATOMIC_FLAG_INIT;
};

// 示例5：once_flag 实现
class SimpleOnceFlag {
public:
    void call_once(auto&& func) {
        if (!flag_.test_and_set(std::memory_order_acquire)) {
            func();
            done_.store(true, std::memory_order_release);
        } else {
            while (!done_.load(std::memory_order_acquire)) {
                // 等待初始化完成
            }
        }
    }

private:
    std::atomic_flag flag_ = ATOMIC_FLAG_INIT;
    std::atomic<bool> done_{false};
};

void once_flag_demo() {
    std::cout << "\n=== once_flag 演示 ===" << std::endl;

    SimpleOnceFlag once;
    std::atomic<int> counter{0};

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&]() {
            once.call_once([&]() {
                counter.fetch_add(1);
                std::cout << "初始化执行" << std::endl;
            });
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "初始化次数: " << counter.load() << std::endl;
}

// 示例6：性能对比
void performance_comparison() {
    std::cout << "\n=== 性能对比 ===" << std::endl;

    const int iterations = 1000000;

    // atomic_flag 自旋锁
    {
        SpinLock mutex;
        int counter = 0;
        auto start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < iterations; ++i) {
            mutex.lock();
            counter++;
            mutex.unlock();
        }
        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        std::cout << "atomic_flag 自旋锁: " << time.count() << " us" << std::endl;
    }

    // std::mutex
    {
        std::mutex mutex;
        int counter = 0;
        auto start = std::chrono::high_resolution_clock::now();
        for (int i = 0; i < iterations; ++i) {
            std::lock_guard<std::mutex> lock(mutex);
            counter++;
        }
        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        std::cout << "std::mutex: " << time.count() << " us" << std::endl;
    }
}

int main() {
    std::cout << "C++ 原子操作：atomic_flag" << std::endl;
    std::cout << "==========================\n" << std::endl;

    basic_atomic_flag();
    spinlock_demo();
    once_flag_demo();
    performance_comparison();

    return 0;
}
