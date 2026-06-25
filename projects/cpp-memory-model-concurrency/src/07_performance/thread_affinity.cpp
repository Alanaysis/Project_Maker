/**
 * 线程亲和性
 *
 * 线程亲和性的应用：
 * 1. 绑定线程到特定 CPU 核心
 * 2. 减少缓存失效
 * 3. 提高缓存命中率
 * 4. 适合 NUMA 架构
 *
 * 编译：g++ -std=c++17 -pthread thread_affinity.cpp -o thread_affinity
 */

#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <atomic>
#include <sched.h>

// 获取 CPU 核心数
int get_num_cores() {
    return std::thread::hardware_concurrency();
}

// 设置线程亲和性
bool set_thread_affinity(std::thread& thread, int core_id) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(core_id, &cpuset);

    int result = pthread_setaffinity_np(
        thread.native_handle(),
        sizeof(cpu_set_t),
        &cpuset
    );

    return result == 0;
}

// 获取当前线程的 CPU 核心
int get_current_cpu() {
    return sched_getcpu();
}

// 示例1：基本用法
void basic_affinity() {
    std::cout << "=== 基本线程亲和性 ===" << std::endl;
    std::cout << "CPU 核心数: " << get_num_cores() << std::endl;

    std::thread worker([]() {
        std::cout << "线程运行在 CPU " << get_current_cpu() << std::endl;
    });

    // 绑定到核心 0
    if (set_thread_affinity(worker, 0)) {
        std::cout << "已绑定到核心 0" << std::endl;
    }

    worker.join();
}

// 示例2：多线程亲和性
void multi_thread_affinity() {
    std::cout << "\n=== 多线程亲和性 ===" << std::endl;

    const int num_threads = 4;
    std::vector<std::thread> threads;

    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([i]() {
            std::cout << "线程 " << i << " 运行在 CPU " << get_current_cpu() << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        });

        // 绑定到不同的核心
        set_thread_affinity(threads.back(), i % get_num_cores());
    }

    for (auto& t : threads) {
        t.join();
    }
}

// 示例3：性能对比
void performance_comparison() {
    std::cout << "\n=== 性能对比 ===" << std::endl;

    const int iterations = 1000000;
    std::atomic<int> counter{0};

    // 无亲和性
    {
        auto start = std::chrono::high_resolution_clock::now();

        std::vector<std::thread> threads;
        for (int i = 0; i < 4; ++i) {
            threads.emplace_back([&]() {
                for (int j = 0; j < iterations / 4; ++j) {
                    counter.fetch_add(1, std::memory_order_relaxed);
                }
            });
        }

        for (auto& t : threads) {
            t.join();
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "无亲和性: " << time.count() << " ms" << std::endl;
    }

    // 有亲和性
    {
        counter.store(0);
        auto start = std::chrono::high_resolution_clock::now();

        std::vector<std::thread> threads;
        for (int i = 0; i < 4; ++i) {
            threads.emplace_back([&]() {
                for (int j = 0; j < iterations / 4; ++j) {
                    counter.fetch_add(1, std::memory_order_relaxed);
                }
            });
            set_thread_affinity(threads.back(), i % get_num_cores());
        }

        for (auto& t : threads) {
            t.join();
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "有亲和性: " << time.count() << " ms" << std::endl;
    }
}

int main() {
    std::cout << "C++ 性能优化：线程亲和性" << std::endl;
    std::cout << "=========================\n" << std::endl;

    basic_affinity();
    multi_thread_affinity();
    performance_comparison();

    return 0;
}
