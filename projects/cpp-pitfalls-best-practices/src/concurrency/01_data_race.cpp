/**
 * @file 01_data_race.cpp
 * @brief 数据竞争陷阱示例
 *
 * 数据竞争 (Data Race)：多个线程同时访问共享数据，至少一个在写
 * 危害：未定义行为、数据损坏、程序崩溃
 */

#include <iostream>
#include <thread>
#include <vector>
#include <atomic>
#include <mutex>
#include <chrono>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：无保护的共享变量
 *
 * 问题：多个线程同时修改共享变量，无同步
 */
int bad_shared_counter = 0;

void bad_increment() {
    for (int i = 0; i < 100000; i++) {
        bad_shared_counter++;  // 数据竞争！
    }
}

void bad_data_race() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 10; i++) {
        threads.emplace_back(bad_increment);
    }
    for (auto& t : threads) {
        t.join();
    }
    std::cout << "期望: 1000000, 实际: " << bad_shared_counter << std::endl;
}

/**
 * 错误示例 2：读写竞争
 *
 * 问题：一个线程读，另一个线程写
 */
int bad_shared_data = 0;
bool bad_ready = false;

void bad_writer() {
    bad_shared_data = 42;
    bad_ready = true;  // 无同步，可能重排序
}

void bad_reader() {
    while (!bad_ready) {}  // 忙等待
    std::cout << "data = " << bad_shared_data << std::endl;
    // 可能读到旧值
}

/**
 * 错误示例 3：容器并发修改
 *
 * 问题：多个线程同时修改容器
 */
std::vector<int> bad_vector;

void bad_push_back() {
    for (int i = 0; i < 1000; i++) {
        bad_vector.push_back(i);  // 数据竞争！
    }
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用 mutex 保护
 *
 * 解决方案：使用互斥锁保护共享数据
 */
int good_counter = 0;
std::mutex counter_mutex;

void good_increment_mutex() {
    for (int i = 0; i < 100000; i++) {
        std::lock_guard<std::mutex> lock(counter_mutex);
        good_counter++;
    }
}

void good_mutex_example() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 10; i++) {
        threads.emplace_back(good_increment_mutex);
    }
    for (auto& t : threads) {
        t.join();
    }
    std::cout << "期望: 1000000, 实际: " << good_counter << std::endl;
}

/**
 * 正确示例 2：使用原子操作
 *
 * 解决方案：使用 atomic 进行无锁操作
 */
std::atomic<int> good_atomic_counter{0};

void good_increment_atomic() {
    for (int i = 0; i < 100000; i++) {
        good_atomic_counter++;
    }
}

void good_atomic_example() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 10; i++) {
        threads.emplace_back(good_increment_atomic);
    }
    for (auto& t : threads) {
        t.join();
    }
    std::cout << "期望: 1000000, 实际: " << good_atomic_counter.load() << std::endl;
}

/**
 * 正确示例 3：使用条件变量
 *
 * 解决方案：使用条件变量进行线程同步
 */
std::mutex good_mutex;
std::condition_variable good_cv;
int good_data = 0;
bool good_ready = false;

void good_writer() {
    {
        std::lock_guard<std::mutex> lock(good_mutex);
        good_data = 42;
        good_ready = true;
    }
    good_cv.notify_one();
}

void good_reader() {
    std::unique_lock<std::mutex> lock(good_mutex);
    good_cv.wait(lock, [] { return good_ready; });
    std::cout << "data = " << good_data << std::endl;
}

void good_condition_variable_example() {
    std::thread writer(good_writer);
    std::thread reader(good_reader);
    writer.join();
    reader.join();
}

/**
 * 正确示例 4：使用 shared_mutex (C++17)
 *
 * 解决方案：读写锁，允许多个读者
 */
#include <shared_mutex>

std::shared_mutex good_shared_mutex;
int good_shared_data = 0;

void good_reader_shared() {
    std::shared_lock<std::shared_mutex> lock(good_shared_mutex);
    std::cout << "读取: " << good_shared_data << std::endl;
}

void good_writer_shared() {
    std::unique_lock<std::shared_mutex> lock(good_shared_mutex);
    good_shared_data++;
    std::cout << "写入: " << good_shared_data << std::endl;
}

void good_shared_mutex_example() {
    std::vector<std::thread> readers;
    std::vector<std::thread> writers;

    for (int i = 0; i < 5; i++) {
        readers.emplace_back(good_reader_shared);
    }
    for (int i = 0; i < 2; i++) {
        writers.emplace_back(good_writer_shared);
    }

    for (auto& t : readers) t.join();
    for (auto& t : writers) t.join();
}

/**
 * 正确示例 5：使用 std::call_once
 *
 * 解决方案：确保初始化只执行一次
 */
std::once_flag good_once_flag;

void good_init() {
    std::call_once(good_once_flag, []() {
        std::cout << "只初始化一次" << std::endl;
    });
}

void good_call_once_example() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 10; i++) {
        threads.emplace_back(good_init);
    }
    for (auto& t : threads) {
        t.join();
    }
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 数据竞争陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 无保护的共享变量" << std::endl;
    std::cout << "问题：多个线程同时修改共享变量" << std::endl;
    // bad_data_race();  // 注释掉，避免未定义行为
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用 mutex 保护" << std::endl;
    good_counter = 0;
    good_mutex_example();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用原子操作" << std::endl;
    good_atomic_counter = 0;
    good_atomic_example();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用条件变量" << std::endl;
    good_condition_variable_example();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 shared_mutex" << std::endl;
    good_shared_mutex_example();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用 call_once" << std::endl;
    good_call_once_example();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
