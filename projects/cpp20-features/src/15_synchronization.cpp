/**
 * 15_synchronization.cpp - C++20 同步原语
 *
 * C++20 引入了多种新的同步原语。
 *
 * 核心要点：
 * 1. std::latch - 一次性同步屏障（等待 N 个事件）
 * 2. std::barrier - 可重复使用的同步屏障
 * 3. std::counting_semaphore - 计数信号量
 * 4. std::binary_semaphore - 二值信号量
 */

#include <iostream>
#include <thread>
#include <vector>
#include <latch>
#include <barrier>
#include <semaphore>
#include <string>
#include <chrono>
#include <functional>

using namespace std::chrono_literals;

// ============================================================
// 1. std::latch - 一次性同步屏障
// ============================================================

void latch_demo() {
    std::cout << "【1. std::latch - 一次性同步屏障】\n";

    constexpr int num_workers = 3;
    std::latch ready(num_workers);  // 等待 3 个事件
    std::latch done(1);             // 通知完成

    std::vector<std::jthread> workers;

    for (int i = 0; i < num_workers; ++i) {
        workers.emplace_back([i, &ready, &done]() {
            // 准备工作
            std::this_thread::sleep_for(100ms * (i + 1));
            std::cout << "  Worker-" << i << " 准备完成\n";
            ready.count_down();  // 减少计数

            // 等待所有 worker 准备好
            ready.wait();
            std::cout << "  Worker-" << i << " 开始执行任务\n";

            std::this_thread::sleep_for(200ms);
            std::cout << "  Worker-" << i << " 任务完成\n";
        });
    }

    // 主线程等待所有 worker 完成
    std::this_thread::sleep_for(1s);
    std::cout << "  所有任务已完成\n\n";
}

// ============================================================
// 2. std::barrier - 可重复同步屏障
// ============================================================

void barrier_demo() {
    std::cout << "【2. std::barrier - 可重复同步屏障】\n";

    constexpr int num_threads = 3;
    constexpr int num_rounds = 2;

    // 到达屏障时执行的回调
    auto on_completion = []() noexcept {
        static int round = 0;
        std::cout << "  [屏障] 第 " << ++round << " 轮同步完成\n";
    };

    std::barrier sync_point(num_threads, on_completion);
    std::vector<std::jthread> threads;

    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([i, &sync_point]() {
            for (int round = 0; round < num_rounds; ++round) {
                // 执行工作
                std::this_thread::sleep_for(100ms * (i + 1));
                std::cout << "  Thread-" << i << " 第 " << round << " 轮完成\n";

                // 等待所有线程到达屏障
                sync_point.arrive_and_wait();
            }
        });
    }
    // 线程析构自动 join
}

// ============================================================
// 3. std::counting_semaphore - 计数信号量
// ============================================================

void semaphore_demo() {
    std::cout << "\n【3. std::counting_semaphore - 计数信号量】\n";

    // 最多允许 2 个并发访问
    std::counting_semaphore<2> sem(2);
    std::atomic<int> active_count{0};

    std::vector<std::jthread> threads;

    for (int i = 0; i < 5; ++i) {
        threads.emplace_back([i, &sem, &active_count]() {
            std::cout << "  Task-" << i << " 等待获取信号量\n";
            sem.acquire();  // 获取信号量（可能阻塞）

            int active = ++active_count;
            std::cout << "  Task-" << i << " 开始执行 (当前并发: " << active << ")\n";

            std::this_thread::sleep_for(300ms);

            active = --active_count;
            std::cout << "  Task-" << i << " 完成 (当前并发: " << active << ")\n";
            sem.release();  // 释放信号量
        });
    }
    // 线程析构自动 join
}

// ============================================================
// 4. std::binary_semaphore - 二值信号量
// ============================================================

void binary_semaphore_demo() {
    std::cout << "\n【4. std::binary_semaphore - 二值信号量】\n";

    std::binary_semaphore sem(0);  // 初始为 0（不可用）
    std::string shared_data;

    // 生产者线程
    std::jthread producer([&sem, &shared_data]() {
        std::this_thread::sleep_for(300ms);
        shared_data = "Hello from producer!";
        std::cout << "  生产者: 数据已准备好\n";
        sem.release();  // 通知消费者
    });

    // 消费者线程
    std::jthread consumer([&sem, &shared_data]() {
        std::cout << "  消费者: 等待数据...\n";
        sem.acquire();  // 等待生产者
        std::cout << "  消费者: 收到数据 = \"" << shared_data << "\"\n";
    });
}

// ============================================================
// 5. 超时等待
// ============================================================

void timeout_demo() {
    std::cout << "\n【5. 超时等待】\n";

    std::counting_semaphore<1> sem(0);

    std::jthread t([&sem]() {
        std::this_thread::sleep_for(500ms);
        sem.release();
        std::cout << "  Worker: 已释放信号量\n";
    });

    // 尝试获取信号量，超时 200ms
    if (sem.try_acquire_for(200ms)) {
        std::cout << "  主线程: 成功获取信号量\n";
    } else {
        std::cout << "  主线程: 超时，继续等待...\n";
        sem.acquire();  // 阻塞等待
        std::cout << "  主线程: 最终获取信号量\n";
    }
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 同步原语示例 ===\n\n";

    latch_demo();
    barrier_demo();
    semaphore_demo();
    binary_semaphore_demo();
    timeout_demo();

    std::cout << "\n=== 同步原语示例完成 ===\n";
    return 0;
}
