/**
 * std::stop_token (C++20)
 *
 * 协作取消机制：
 * 1. 线程请求停止
 * 2. 线程检查停止请求
 * 3. 支持回调
 * 4. jthread 自动管理
 *
 * 编译：g++ -std=c++20 -pthread stop_token.cpp -o stop_token
 */

#include <iostream>
#include <thread>
#include <chrono>
#include <vector>
#include <atomic>
#include <queue>
#include <mutex>
#include <condition_variable>

// 示例1：基本用法
void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::jthread worker([](std::stop_token token) {
        int count = 0;
        while (!token.stop_requested()) {
            std::cout << "工作中: " << count++ << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        std::cout << "收到停止请求" << std::endl;
    });

    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    worker.request_stop();
    // jthread 析构时自动 join
}

// 示例2：stop_callback
void stop_callback_demo() {
    std::cout << "\n=== stop_callback ===" << std::endl;

    std::jthread worker([](std::stop_token token) {
        // 注册回调
        std::stop_callback callback(token, []() {
            std::cout << "停止回调被调用" << std::endl;
        });

        while (!token.stop_requested()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        std::cout << "工作线程退出" << std::endl;
    });

    std::this_thread::sleep_for(std::chrono::milliseconds(300));
    worker.request_stop();
}

// 示例3：多线程协作取消
void cooperative_cancellation() {
    std::cout << "\n=== 多线程协作取消 ===" << std::endl;

    std::stop_source source;
    std::stop_token token = source.get_token();

    std::vector<std::jthread> workers;
    for (int i = 0; i < 3; ++i) {
        workers.emplace_back([token, i]() {
            int count = 0;
            while (!token.stop_requested()) {
                std::cout << "Worker " << i << ": " << count++ << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }
            std::cout << "Worker " << i << " 停止" << std::endl;
        });
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    source.request_stop();

    // jthread 析构时自动 join
}

// 示例4：生产者-消费者取消
void producer_consumer_cancellation() {
    std::cout << "\n=== 生产者-消费者取消 ===" << std::endl;

    std::stop_source source;
    std::stop_token token = source.get_token();

    std::queue<int> queue;
    std::mutex mutex;
    std::condition_variable cv;
    std::atomic<int> produced{0};

    // 生产者
    std::jthread producer([&]() {
        int i = 0;
        while (!token.stop_requested()) {
            {
                std::lock_guard lock(mutex);
                queue.push(i++);
            }
            cv.notify_one();
            produced.fetch_add(1);
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
        std::cout << "生产者停止" << std::endl;
    });

    // 消费者
    std::jthread consumer([&]() {
        while (!token.stop_requested()) {
            std::unique_lock lock(mutex);
            cv.wait_for(lock, std::chrono::milliseconds(100),
                [&]() { return !queue.empty() || token.stop_requested(); });

            while (!queue.empty()) {
                int item = queue.front();
                queue.pop();
                std::cout << "消费: " << item << std::endl;
            }
        }
        std::cout << "消费者停止" << std::endl;
    });

    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    source.request_stop();
    cv.notify_all();

    std::cout << "生产总数: " << produced.load() << std::endl;
}

int main() {
    std::cout << "C++ 线程同步：std::stop_token (C++20)" << std::endl;
    std::cout << "=======================================\n" << std::endl;

    basic_usage();
    stop_callback_demo();
    cooperative_cancellation();
    producer_consumer_cancellation();

    return 0;
}
