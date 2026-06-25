/**
 * 并发调试技巧
 *
 * 并发调试的方法：
 * 1. ThreadSanitizer 检测数据竞争
 * 2. 日志记录
 * 3. 断言检查
 * 4. 死锁检测
 *
 * 编译：g++ -std=c++17 -pthread -fsanitize=thread debug_techniques.cpp -o debug_techniques
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <vector>
#include <atomic>
#include <sstream>
#include <chrono>
#include <cassert>

// 线程安全的日志
class ThreadSafeLog {
public:
    static ThreadSafeLog& instance() {
        static ThreadSafeLog instance;
        return instance;
    }

    void log(const std::string& message) {
        std::lock_guard lock(mutex_);
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        std::cout << "[" << std::this_thread::get_id() << "] "
                  << message << std::endl;
    }

private:
    std::mutex mutex_;
};

#define LOG(msg) ThreadSafeLog::instance().log(msg)

// 示例1：数据竞争检测
void data_race_detection() {
    std::cout << "=== 数据竞争检测 ===" << std::endl;
    std::cout << "使用 ThreadSanitizer 编译:" << std::endl;
    std::cout << "  g++ -fsanitize=thread -g debug_techniques.cpp" << std::endl;

    // 故意的数据竞争（用于演示）
    // 正常情况下应该使用原子操作或互斥量
    std::atomic<int> safe_counter{0};

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&safe_counter]() {
            for (int j = 0; j < 1000; ++j) {
                safe_counter.fetch_add(1, std::memory_order_relaxed);
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "安全计数器: " << safe_counter.load() << std::endl;
}

// 示例2：死锁检测
void deadlock_detection() {
    std::cout << "\n=== 死锁检测 ===" << std::endl;

    std::mutex mutex1;
    std::mutex mutex2;

    // 使用 std::lock 避免死锁
    auto safe_lock = [&]() {
        std::lock(mutex1, mutex2);
        std::lock_guard lock1(mutex1, std::adopt_lock);
        std::lock_guard lock2(mutex2, std::adopt_lock);
        LOG("安全地获取了两个锁");
    };

    std::thread t1(safe_lock);
    std::thread t2(safe_lock);

    t1.join();
    t2.join();
}

// 示例3：断言检查
void assertion_checks() {
    std::cout << "\n=== 断言检查 ===" << std::endl;

    std::mutex mutex;
    int shared_data = 0;

    auto check_invariant = [&]() {
        std::lock_guard lock(mutex);
        // 检查不变量
        assert(shared_data >= 0 && "shared_data 不能为负");
        shared_data++;
        LOG("shared_data = " + std::to_string(shared_data));
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&]() {
            for (int j = 0; j < 100; ++j) {
                check_invariant();
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "最终值: " << shared_data << std::endl;
}

// 示例4：状态转储
class StateDumper {
public:
    void update(int value) {
        std::lock_guard lock(mutex_);
        state_ = value;
        dump("update");
    }

    int get() const {
        std::lock_guard lock(mutex_);
        dump("get");
        return state_;
    }

    void dump(const std::string& action) const {
        LOG(action + ": state=" + std::to_string(state_));
    }

private:
    mutable std::mutex mutex_;
    int state_ = 0;
};

void state_dump_demo() {
    std::cout << "\n=== 状态转储 ===" << std::endl;

    StateDumper dumper;

    std::vector<std::thread> threads;
    for (int i = 0; i < 3; ++i) {
        threads.emplace_back([&dumper, i]() {
            for (int j = 0; j < 5; ++j) {
                dumper.update(i * 100 + j);
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }
}

int main() {
    std::cout << "C++ 并发调试技巧" << std::endl;
    std::cout << "==================\n" << std::endl;

    data_race_detection();
    deadlock_detection();
    assertion_checks();
    state_dump_demo();

    return 0;
}
