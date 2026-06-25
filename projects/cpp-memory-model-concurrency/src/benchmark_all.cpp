/**
 * 性能基准测试
 *
 * 测试所有并发原语的性能：
 * 1. 原子操作
 * 2. 互斥锁
 * 3. 无锁数据结构
 * 4. 并发模式
 *
 * 编译：g++ -std=c++17 -pthread benchmark_all.cpp -o benchmark_all
 */

#include <iostream>
#include <atomic>
#include <mutex>
#include <thread>
#include <vector>
#include <chrono>
#include <iomanip>

class Timer {
public:
    Timer() : start_(std::chrono::high_resolution_clock::now()) {}

    double elapsed_ms() const {
        auto end = std::chrono::high_resolution_clock::now();
        return std::chrono::duration<double, std::milli>(end - start_).count();
    }

private:
    std::chrono::high_resolution_clock::time_point start_;
};

void benchmark_atomic_operations() {
    std::cout << "=== 原子操作性能 ===" << std::endl;

    const int iterations = 1000000;
    std::atomic<int> counter{0};

    // relaxed
    Timer timer;
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_relaxed);
    }
    std::cout << "relaxed:    " << std::fixed << std::setprecision(2)
              << timer.elapsed_ms() << " ms" << std::endl;

    // acquire-release
    counter.store(0);
    timer = Timer();
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_acq_rel);
    }
    std::cout << "acq_rel:    " << timer.elapsed_ms() << " ms" << std::endl;

    // seq_cst
    counter.store(0);
    timer = Timer();
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_seq_cst);
    }
    std::cout << "seq_cst:    " << timer.elapsed_ms() << " ms" << std::endl;
}

void benchmark_mutex_vs_atomic() {
    std::cout << "\n=== 互斥锁 vs 原子操作 ===" << std::endl;

    const int iterations = 1000000;

    // 原子操作
    std::atomic<int> atomic_counter{0};
    Timer timer;
    for (int i = 0; i < iterations; ++i) {
        atomic_counter.fetch_add(1, std::memory_order_relaxed);
    }
    std::cout << "原子操作: " << timer.elapsed_ms() << " ms" << std::endl;

    // 互斥锁
    std::mutex mutex;
    int mutex_counter = 0;
    timer = Timer();
    for (int i = 0; i < iterations; ++i) {
        std::lock_guard<std::mutex> lock(mutex);
        mutex_counter++;
    }
    std::cout << "互斥锁:  " << timer.elapsed_ms() << " ms" << std::endl;
}

void benchmark_contention() {
    std::cout << "\n=== 多线程竞争性能 ===" << std::endl;

    const int iterations = 100000;
    const int num_threads = 4;

    // 原子操作
    {
        std::atomic<int> counter{0};
        Timer timer;

        std::vector<std::thread> threads;
        for (int i = 0; i < num_threads; ++i) {
            threads.emplace_back([&]() {
                for (int j = 0; j < iterations; ++j) {
                    counter.fetch_add(1, std::memory_order_relaxed);
                }
            });
        }

        for (auto& t : threads) {
            t.join();
        }

        std::cout << "原子操作 (" << num_threads << " 线程): "
                  << timer.elapsed_ms() << " ms" << std::endl;
    }

    // 互斥锁
    {
        std::mutex mutex;
        int counter = 0;
        Timer timer;

        std::vector<std::thread> threads;
        for (int i = 0; i < num_threads; ++i) {
            threads.emplace_back([&]() {
                for (int j = 0; j < iterations; ++j) {
                    std::lock_guard<std::mutex> lock(mutex);
                    counter++;
                }
            });
        }

        for (auto& t : threads) {
            t.join();
        }

        std::cout << "互斥锁 (" << num_threads << " 线程): "
                  << timer.elapsed_ms() << " ms" << std::endl;
    }
}

void benchmark_false_sharing() {
    std::cout << "\n=== 伪共享性能 ===" << std::endl;

    const int iterations = 1000000;

    // 伪共享
    {
        struct Shared {
            std::atomic<int> x;
            std::atomic<int> y;
        } data;

        Timer timer;
        std::thread t1([&]() {
            for (int i = 0; i < iterations; ++i) {
                data.x.fetch_add(1, std::memory_order_relaxed);
            }
        });

        std::thread t2([&]() {
            for (int i = 0; i < iterations; ++i) {
                data.y.fetch_add(1, std::memory_order_relaxed);
            }
        });

        t1.join();
        t2.join();
        std::cout << "伪共享: " << timer.elapsed_ms() << " ms" << std::endl;
    }

    // 填充后
    {
        struct Padded {
            alignas(64) std::atomic<int> x;
            alignas(64) std::atomic<int> y;
        } data;

        Timer timer;
        std::thread t1([&]() {
            for (int i = 0; i < iterations; ++i) {
                data.x.fetch_add(1, std::memory_order_relaxed);
            }
        });

        std::thread t2([&]() {
            for (int i = 0; i < iterations; ++i) {
                data.y.fetch_add(1, std::memory_order_relaxed);
            }
        });

        t1.join();
        t2.join();
        std::cout << "填充后: " << timer.elapsed_ms() << " ms" << std::endl;
    }
}

int main() {
    std::cout << "C++ 并发性能基准测试" << std::endl;
    std::cout << "=====================\n" << std::endl;

    benchmark_atomic_operations();
    benchmark_mutex_vs_atomic();
    benchmark_contention();
    benchmark_false_sharing();

    return 0;
}
