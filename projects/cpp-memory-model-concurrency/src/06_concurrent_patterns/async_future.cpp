/**
 * 异步编程 (std::async, std::future)
 *
 * 异步编程的特点：
 * 1. std::async 启动异步任务
 * 2. std::future 获取结果
 * 3. std::promise 设置值
 * 4. std::packaged_task 打包任务
 *
 * 编译：g++ -std=c++17 -pthread async_future.cpp -o async_future
 */

#include <iostream>
#include <future>
#include <thread>
#include <vector>
#include <chrono>
#include <numeric>

// 示例1：基本用法
void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // std::async 启动异步任务
    auto future = std::async(std::launch::async, []() {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        return 42;
    });

    std::cout << "等待结果..." << std::endl;
    int result = future.get();
    std::cout << "结果: " << result << std::endl;
}

// 示例2：多个异步任务
void multiple_async() {
    std::cout << "\n=== 多个异步任务 ===" << std::endl;

    std::vector<std::future<int>> futures;

    for (int i = 0; i < 5; ++i) {
        futures.emplace_back(std::async(std::launch::async, [i]() {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            return i * i;
        }));
    }

    for (auto& future : futures) {
        std::cout << future.get() << " ";
    }
    std::cout << std::endl;
}

// 示例3：std::promise
void promise_demo() {
    std::cout << "\n=== std::promise ===" << std::endl;

    std::promise<int> promise;
    std::future<int> future = promise.get_future();

    std::thread producer([&promise]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        promise.set_value(42);
    });

    std::cout << "等待 promise..." << std::endl;
    std::cout << "结果: " << future.get() << std::endl;

    producer.join();
}

// 示例4：std::packaged_task
void packaged_task_demo() {
    std::cout << "\n=== std::packaged_task ===" << std::endl;

    std::packaged_task<int(int, int)> task([](int a, int b) {
        return a + b;
    });

    std::future<int> future = task.get_future();

    std::thread worker([&task]() {
        task(3, 4);
    });

    std::cout << "结果: " << future.get() << std::endl;
    worker.join();
}

// 示例5：异常处理
void exception_handling() {
    std::cout << "\n=== 异常处理 ===" << std::endl;

    auto future = std::async(std::launch::async, []() -> int {
        throw std::runtime_error("异步任务出错");
        return 0;
    });

    try {
        future.get();
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
}

// 示例6：并行累加
int parallel_sum(const std::vector<int>& data, int num_threads) {
    size_t chunk_size = data.size() / num_threads;
    std::vector<std::future<int>> futures;

    for (int i = 0; i < num_threads; ++i) {
        size_t start = i * chunk_size;
        size_t end = (i == num_threads - 1) ? data.size() : start + chunk_size;

        futures.emplace_back(std::async(std::launch::async, [&data, start, end]() {
            return std::accumulate(data.begin() + start, data.begin() + end, 0);
        }));
    }

    int total = 0;
    for (auto& future : futures) {
        total += future.get();
    }
    return total;
}

void parallel_sum_demo() {
    std::cout << "\n=== 并行累加 ===" << std::endl;

    std::vector<int> data(1000000);
    std::iota(data.begin(), data.end(), 1);

    auto start = std::chrono::high_resolution_clock::now();
    int result = parallel_sum(data, 4);
    auto end = std::chrono::high_resolution_clock::now();
    auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "结果: " << result << std::endl;
    std::cout << "期望: " << 1000000LL * 1000001 / 2 << std::endl;
    std::cout << "耗时: " << time.count() << " ms" << std::endl;
}

int main() {
    std::cout << "C++ 并发模式：异步编程" << std::endl;
    std::cout << "=======================\n" << std::endl;

    basic_usage();
    multiple_async();
    promise_demo();
    packaged_task_demo();
    exception_handling();
    parallel_sum_demo();

    return 0;
}
