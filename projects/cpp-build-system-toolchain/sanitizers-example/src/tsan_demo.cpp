#include <iostream>
#include <thread>
#include <vector>
#include <atomic>
#include <mutex>

/**
 * @file tsan_demo.cpp
 * @brief ThreadSanitizer (TSan) 示例
 *
 * ThreadSanitizer 是一个数据竞争检测工具，可以检测:
 * - 数据竞争（两个线程同时访问同一内存，至少一个是写入）
 * - 死锁
 *
 * 编译方法:
 *   g++ -fsanitize=thread -g -o tsan_demo tsan_demo.cpp -lpthread
 *
 * 注意: 以下代码故意包含数据竞争，用于演示 TSan 的检测能力。
 */

// ============================================================================
// 1. 数据竞争示例（有 bug）
// ============================================================================
int shared_counter = 0;

void increment_unsafe() {
    for (int i = 0; i < 10000; ++i) {
        shared_counter++;  // 数据竞争!
    }
}

void data_race_example() {
    std::cout << "=== 数据竞争示例 ===" << std::endl;

    shared_counter = 0;
    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back(increment_unsafe);
    }
    for (auto& t : threads) {
        t.join();
    }
    std::cout << "计数器值 (有竞争): " << shared_counter << std::endl;
    std::cout << "期望值: 40000" << std::endl;
}

// ============================================================================
// 2. 使用 mutex 修复数据竞争
// ============================================================================
int safe_counter = 0;
std::mutex counter_mutex;

void increment_safe() {
    for (int i = 0; i < 10000; ++i) {
        std::lock_guard<std::mutex> lock(counter_mutex);
        safe_counter++;
    }
}

void mutex_example() {
    std::cout << std::endl;
    std::cout << "=== 使用 mutex 修复竞争 ===" << std::endl;

    safe_counter = 0;
    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back(increment_safe);
    }
    for (auto& t : threads) {
        t.join();
    }
    std::cout << "计数器值 (使用 mutex): " << safe_counter << std::endl;
}

// ============================================================================
// 3. 使用 atomic 修复数据竞争
// ============================================================================
std::atomic<int> atomic_counter{0};

void increment_atomic() {
    for (int i = 0; i < 10000; ++i) {
        atomic_counter++;
    }
}

void atomic_example() {
    std::cout << std::endl;
    std::cout << "=== 使用 atomic 修复竞争 ===" << std::endl;

    atomic_counter = 0;
    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back(increment_atomic);
    }
    for (auto& t : threads) {
        t.join();
    }
    std::cout << "计数器值 (使用 atomic): " << atomic_counter << std::endl;
}

int main() {
    std::cout << "=== ThreadSanitizer (TSan) 示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "ThreadSanitizer 可以检测:" << std::endl;
    std::cout << "  - 数据竞争" << std::endl;
    std::cout << "  - 死锁" << std::endl;
    std::cout << std::endl;

    data_race_example();
    mutex_example();
    atomic_example();

    std::cout << std::endl;
    std::cout << "编译方法:" << std::endl;
    std::cout << "  g++ -fsanitize=thread -g -o demo demo.cpp -lpthread" << std::endl;

    return 0;
}
