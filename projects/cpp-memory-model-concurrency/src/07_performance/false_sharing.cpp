/**
 * 伪共享 (False Sharing)
 *
 * 伪共享的问题：
 * 1. 不同线程访问同一缓存行的不同变量
 * 2. 导致缓存行频繁失效
 * 3. 严重降低性能
 * 4. 解决方案：缓存行填充
 *
 * 编译：g++ -std=c++17 -pthread false_sharing.cpp -o false_sharing
 */

#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <atomic>
#include <new>

// 示例1：伪共享问题
struct SharedLine {
    std::atomic<int> x;
    std::atomic<int> y;
};

// 示例2：填充解决伪共享
struct PaddedLine {
    alignas(64) std::atomic<int> x;
    alignas(64) std::atomic<int> y;
};

void false_sharing_demo() {
    std::cout << "=== 伪共享演示 ===" << std::endl;

    const int iterations = 1000000;

    // 伪共享
    {
        SharedLine data;
        data.x = 0;
        data.y = 0;

        auto start = std::chrono::high_resolution_clock::now();

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

        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "伪共享: " << time.count() << " ms" << std::endl;
    }

    // 填充后
    {
        PaddedLine data;
        data.x = 0;
        data.y = 0;

        auto start = std::chrono::high_resolution_clock::now();

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

        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "填充后: " << time.count() << " ms" << std::endl;
    }
}

// 示例3：缓存行大小检测
void cache_line_size() {
    std::cout << "\n=== 缓存行大小 ===" << std::endl;

    std::cout << "硬件缓存行大小: " << std::hardware_destructive_interference_size << " bytes" << std::endl;
    std::cout << "最小并发间距: " << std::hardware_constructive_interference_size << " bytes" << std::endl;
}

// 示例4：数组中的伪共享
void array_false_sharing() {
    std::cout << "\n=== 数组中的伪共享 ===" << std::endl;

    const int num_threads = 4;
    const int iterations = 1000000;

    // 伪共享数组
    {
        std::atomic<int> counters[num_threads] = {};

        auto start = std::chrono::high_resolution_clock::now();

        std::vector<std::thread> threads;
        for (int i = 0; i < num_threads; ++i) {
            threads.emplace_back([&counters, i]() {
                for (int j = 0; j < iterations; ++j) {
                    counters[i].fetch_add(1, std::memory_order_relaxed);
                }
            });
        }

        for (auto& t : threads) {
            t.join();
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "伪共享数组: " << time.count() << " ms" << std::endl;
    }

    // 填充数组
    {
        struct PaddedCounter {
            alignas(64) std::atomic<int> value;
        };
        PaddedCounter counters[num_threads] = {};

        auto start = std::chrono::high_resolution_clock::now();

        std::vector<std::thread> threads;
        for (int i = 0; i < num_threads; ++i) {
            threads.emplace_back([&counters, i]() {
                for (int j = 0; j < iterations; ++j) {
                    counters[i].value.fetch_add(1, std::memory_order_relaxed);
                }
            });
        }

        for (auto& t : threads) {
            t.join();
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "填充数组: " << time.count() << " ms" << std::endl;
    }
}

int main() {
    std::cout << "C++ 性能优化：伪共享" << std::endl;
    std::cout << "=====================\n" << std::endl;

    false_sharing_demo();
    cache_line_size();
    array_false_sharing();

    return 0;
}
