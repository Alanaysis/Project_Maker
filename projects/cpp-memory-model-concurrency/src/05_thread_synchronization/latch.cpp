/**
 * std::latch (C++20)
 *
 * 闩锁的特点：
 * 1. 一次性同步原语
 * 2. 计数到零后释放所有等待线程
 * 3. 不可重置
 * 4. 适合等待多个任务完成
 *
 * 编译：g++ -std=c++20 -pthread latch.cpp -o latch
 */

#include <iostream>
#include <latch>
#include <thread>
#include <vector>
#include <chrono>

// 示例1：基本用法
void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    const int num_tasks = 4;
    std::latch latch(num_tasks);

    std::vector<std::thread> threads;
    for (int i = 0; i < num_tasks; ++i) {
        threads.emplace_back([&latch, i]() {
            std::cout << "任务 " << i << " 开始" << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(100 * (i + 1)));
            std::cout << "任务 " << i << " 完成" << std::endl;
            latch.count_down();
        });
    }

    std::cout << "等待所有任务完成..." << std::endl;
    latch.wait();
    std::cout << "所有任务已完成" << std::endl;

    for (auto& t : threads) {
        t.join();
    }
}

// 示例2：使用 arrive_and_wait
void arrive_and_wait() {
    std::cout << "\n=== arrive_and_wait ===" << std::endl;

    const int num_tasks = 4;
    std::latch latch(num_tasks);

    std::vector<std::thread> threads;
    for (int i = 0; i < num_tasks; ++i) {
        threads.emplace_back([&latch, i]() {
            std::cout << "任务 " << i << " 开始" << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(100 * (i + 1)));
            std::cout << "任务 " << i << " 完成" << std::endl;
            latch.arrive_and_wait();  // 到达并等待
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "所有任务已完成" << std::endl;
}

// 示例3：分阶段同步
void phased_sync() {
    std::cout << "\n=== 分阶段同步 ===" << std::endl;

    const int num_workers = 3;
    std::latch phase1(num_workers);
    std::latch phase2(num_workers);

    std::vector<std::thread> threads;
    for (int i = 0; i < num_workers; ++i) {
        threads.emplace_back([&]() {
            // 阶段 1
            std::cout << "阶段 1 开始" << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            phase1.arrive_and_wait();
            std::cout << "阶段 1 完成" << std::endl;

            // 阶段 2
            std::cout << "阶段 2 开始" << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            phase2.arrive_and_wait();
            std::cout << "阶段 2 完成" << std::endl;
        });
    }

    for (auto& t : threads) {
        t.join();
    }
}

// 示例4：并行初始化
class ParallelInitializer {
public:
    void initialize() {
        std::latch latch(num_components_);

        std::vector<std::thread> threads;
        for (int i = 0; i < num_components_; ++i) {
            threads.emplace_back([this, i, &latch]() {
                init_component(i);
                latch.count_down();
            });
        }

        latch.wait();

        for (auto& t : threads) {
            t.join();
        }

        std::cout << "所有组件已初始化" << std::endl;
    }

private:
    void init_component(int id) {
        std::cout << "初始化组件 " << id << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    static constexpr int num_components_ = 4;
};

void parallel_init_demo() {
    std::cout << "\n=== 并行初始化 ===" << std::endl;

    ParallelInitializer initializer;
    initializer.initialize();
}

int main() {
    std::cout << "C++ 线程同步：std::latch (C++20)" << std::endl;
    std::cout << "==================================\n" << std::endl;

    basic_usage();
    arrive_and_wait();
    phased_sync();
    parallel_init_demo();

    return 0;
}
