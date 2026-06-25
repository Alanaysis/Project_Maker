/**
 * std::barrier (C++20)
 *
 * 屏障的特点：
 * 1. 可重用的同步原语
 * 2. 所有线程到达后重置
 * 3. 支持完成函数
 * 4. 适合迭代算法
 *
 * 编译：g++ -std=c++20 -pthread barrier.cpp -o barrier
 */

#include <iostream>
#include <barrier>
#include <thread>
#include <vector>
#include <chrono>

// 示例1：基本用法
void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    const int num_threads = 4;
    std::barrier barrier(num_threads);

    std::vector<std::thread> threads;
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([&barrier, i]() {
            for (int iter = 0; iter < 3; ++iter) {
                std::cout << "线程 " << i << " 迭代 " << iter << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(100 * (i + 1)));
                barrier.arrive_and_wait();
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }
}

// 示例2：带完成函数
void with_completion() {
    std::cout << "\n=== 带完成函数 ===" << std::endl;

    const int num_threads = 4;
    int phase = 0;

    auto completion = [&phase]() noexcept {
        ++phase;
        std::cout << "=== 阶段 " << phase << " 完成 ===" << std::endl;
    };

    std::barrier barrier(num_threads, completion);

    std::vector<std::thread> threads;
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([&barrier, i]() {
            for (int iter = 0; iter < 3; ++iter) {
                std::cout << "线程 " << i << " 工作中" << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(100 * (i + 1)));
                barrier.arrive_and_wait();
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }
}

// 示例3：迭代计算
void iterative_computation() {
    std::cout << "\n=== 迭代计算 ===" << std::endl;

    const int num_threads = 4;
    const int num_iterations = 5;
    std::vector<int> values(num_threads, 0);

    auto completion = [&values]() noexcept {
        int sum = 0;
        for (int v : values) sum += v;
        std::cout << "迭代完成，总和: " << sum << std::endl;
    };

    std::barrier barrier(num_threads, completion);

    std::vector<std::thread> threads;
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([&barrier, &values, i, num_iterations]() {
            for (int iter = 0; iter < num_iterations; ++iter) {
                // 计算
                values[i] = (iter + 1) * (i + 1);
                std::cout << "线程 " << i << " 计算值: " << values[i] << std::endl;
                barrier.arrive_and_wait();
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }
}

// 示例4：并行搜索
void parallel_search() {
    std::cout << "\n=== 并行搜索 ===" << std::endl;

    const int num_threads = 4;
    const int data_size = 1000;
    std::vector<int> data(data_size);
    for (int i = 0; i < data_size; ++i) data[i] = i;

    int target = 777;
    std::atomic<int> found_index{-1};

    auto completion = [&found_index]() noexcept {
        if (found_index >= 0) {
            std::cout << "找到目标在索引: " << found_index.load() << std::endl;
        }
    };

    std::barrier barrier(num_threads, completion);
    int chunk_size = data_size / num_threads;

    std::vector<std::thread> threads;
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([&]() {
            int start = i * chunk_size;
            int end = (i == num_threads - 1) ? data_size : start + chunk_size;

            for (int j = start; j < end; ++j) {
                if (data[j] == target) {
                    found_index.store(j);
                    break;
                }
            }

            barrier.arrive_and_wait();
        });
    }

    for (auto& t : threads) {
        t.join();
    }
}

int main() {
    std::cout << "C++ 线程同步：std::barrier (C++20)" << std::endl;
    std::cout << "====================================\n" << std::endl;

    basic_usage();
    with_completion();
    iterative_computation();
    parallel_search();

    return 0;
}
