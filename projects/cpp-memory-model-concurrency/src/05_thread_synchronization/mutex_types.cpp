/**
 * std::mutex 类型
 *
 * C++ 互斥量类型：
 * 1. std::mutex - 基本互斥量
 * 2. std::recursive_mutex - 递归互斥量
 * 3. std::timed_mutex - 超时互斥量
 * 4. std::shared_mutex - 共享互斥量
 * 5. std::recursive_timed_mutex - 递归超时互斥量
 *
 * 编译：g++ -std=c++17 -pthread mutex_types.cpp -o mutex_types
 */

#include <iostream>
#include <mutex>
#include <shared_mutex>
#include <thread>
#include <vector>
#include <chrono>
#include <string>

// 示例1：基本互斥量
class BasicCounter {
public:
    void increment() {
        std::lock_guard<std::mutex> lock(mutex_);
        ++count_;
    }

    int get() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return count_;
    }

private:
    mutable std::mutex mutex_;
    int count_ = 0;
};

void basic_mutex() {
    std::cout << "=== 基本互斥量 ===" << std::endl;

    BasicCounter counter;
    std::vector<std::thread> threads;

    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&counter]() {
            for (int j = 0; j < 10000; ++j) {
                counter.increment();
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "最终计数: " << counter.get() << std::endl;
}

// 示例2：递归互斥量
class RecursiveCounter {
public:
    void increment() {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        ++count_;
        if (count_ < 10) {
            increment();  // 递归调用
        }
    }

    int get() const {
        std::lock_guard<std::recursive_mutex> lock(mutex_);
        return count_;
    }

private:
    mutable std::recursive_mutex mutex_;
    int count_ = 0;
};

void recursive_mutex() {
    std::cout << "\n=== 递归互斥量 ===" << std::endl;

    RecursiveCounter counter;
    counter.increment();
    std::cout << "最终计数: " << counter.get() << std::endl;
}

// 示例3：超时互斥量
class TimedCounter {
public:
    bool increment(int timeout_ms) {
        std::unique_lock<std::timed_mutex> lock(mutex_, std::chrono::milliseconds(timeout_ms));
        if (!lock.owns_lock()) {
            return false;  // 超时
        }
        ++count_;
        return true;
    }

    int get() const {
        std::lock_guard<std::timed_mutex> lock(mutex_);
        return count_;
    }

private:
    mutable std::timed_mutex mutex_;
    int count_ = 0;
};

void timed_mutex() {
    std::cout << "\n=== 超时互斥量 ===" << std::endl;

    TimedCounter counter;

    std::thread t1([&counter]() {
        for (int i = 0; i < 10; ++i) {
            if (counter.increment(100)) {
                std::cout << "Thread 1: 成功" << std::endl;
            } else {
                std::cout << "Thread 1: 超时" << std::endl;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
    });

    std::thread t2([&counter]() {
        for (int i = 0; i < 10; ++i) {
            if (counter.increment(100)) {
                std::cout << "Thread 2: 成功" << std::endl;
            } else {
                std::cout << "Thread 2: 超时" << std::endl;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(30));
        }
    });

    t1.join();
    t2.join();

    std::cout << "最终计数: " << counter.get() << std::endl;
}

// 示例4：共享互斥量
class SharedData {
public:
    int read() const {
        std::shared_lock lock(mutex_);
        return data_;
    }

    void write(int value) {
        std::unique_lock lock(mutex_);
        data_ = value;
    }

private:
    mutable std::shared_mutex mutex_;
    int data_ = 0;
};

void shared_mutex() {
    std::cout << "\n=== 共享互斥量 ===" << std::endl;

    SharedData data;
    std::atomic<int> reads{0};

    // 多个读线程
    auto reader = [&]() {
        for (int i = 0; i < 100; ++i) {
            data.read();
            reads.fetch_add(1);
        }
    };

    // 写线程
    auto writer = [&]() {
        for (int i = 0; i < 10; ++i) {
            data.write(i);
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    };

    std::vector<std::thread> threads;
    threads.emplace_back(writer);
    for (int i = 0; i < 3; ++i) {
        threads.emplace_back(reader);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "读取次数: " << reads.load() << std::endl;
}

// 示例5：锁守卫
void lock_guards() {
    std::cout << "\n=== 锁守卫 ===" << std::endl;

    std::mutex mutex;

    // lock_guard
    {
        std::lock_guard<std::mutex> lock(mutex);
        std::cout << "lock_guard: 已锁定" << std::endl;
    }
    std::cout << "lock_guard: 已解锁" << std::endl;

    // unique_lock
    {
        std::unique_lock<std::mutex> lock(mutex);
        std::cout << "unique_lock: 已锁定" << std::endl;
        lock.unlock();
        std::cout << "unique_lock: 手动解锁" << std::endl;
        lock.lock();
        std::cout << "unique_lock: 重新锁定" << std::endl;
    }

    // scoped_lock (C++17)
    {
        std::mutex m1, m2;
        std::scoped_lock lock(m1, m2);
        std::cout << "scoped_lock: 已锁定多个互斥量" << std::endl;
    }
}

// 示例6：死锁避免
void deadlock_avoidance() {
    std::cout << "\n=== 死锁避免 ===" << std::endl;

    std::mutex mutex1;
    std::mutex mutex2;

    // 错误方式：可能死锁
    // std::thread t1([&]() {
    //     std::lock_guard lock1(mutex1);
    //     std::lock_guard lock2(mutex2);
    // });

    // 正确方式：使用 std::lock
    std::thread t1([&]() {
        std::lock(mutex1, mutex2);
        std::lock_guard lock1(mutex1, std::adopt_lock);
        std::lock_guard lock2(mutex2, std::adopt_lock);
        std::cout << "Thread 1: 获取两个锁" << std::endl;
    });

    std::thread t2([&]() {
        std::lock(mutex2, mutex1);
        std::lock_guard lock1(mutex1, std::adopt_lock);
        std::lock_guard lock2(mutex2, std::adopt_lock);
        std::cout << "Thread 2: 获取两个锁" << std::endl;
    });

    t1.join();
    t2.join();
}

int main() {
    std::cout << "C++ 线程同步：std::mutex 类型" << std::endl;
    std::cout << "===============================\n" << std::endl;

    basic_mutex();
    recursive_mutex();
    timed_mutex();
    shared_mutex();
    lock_guards();
    deadlock_avoidance();

    return 0;
}
