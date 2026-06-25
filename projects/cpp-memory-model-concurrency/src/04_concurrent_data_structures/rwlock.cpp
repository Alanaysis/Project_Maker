/**
 * 读写锁 (Read-Write Lock)
 *
 * 读写锁的特点：
 * 1. 多个读线程可以同时访问
 * 2. 写线程独占访问
 * 3. 适合读多写少的场景
 * 4. 避免读操作的锁竞争
 *
 * 编译：g++ -std=c++17 -pthread rwlock.cpp -o rwlock
 */

#include <iostream>
#include <shared_mutex>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <vector>
#include <chrono>
#include <atomic>

// 自定义读写锁
class ReadWriteLock {
public:
    void lock_shared() {
        std::unique_lock lock(mutex_);
        readers_.wait(lock, [this]() { return !writing_; });
        ++reader_count_;
    }

    void unlock_shared() {
        std::unique_lock lock(mutex_);
        if (--reader_count_ == 0) {
            writers_.notify_one();
        }
    }

    void lock() {
        std::unique_lock lock(mutex_);
        writers_.wait(lock, [this]() { return !writing_ && reader_count_ == 0; });
        writing_ = true;
    }

    void unlock() {
        std::unique_lock lock(mutex_);
        writing_ = false;
        writers_.notify_one();
        readers_.notify_all();
    }

private:
    std::mutex mutex_;
    std::condition_variable readers_;
    std::condition_variable writers_;
    int reader_count_ = 0;
    bool writing_ = false;
};

// 共享数据
class SharedData {
public:
    SharedData(int initial = 0) : data_(initial) {}

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
    int data_;
};

// 基本测试
void basic_test() {
    std::cout << "=== 基本测试 ===" << std::endl;

    SharedData data(0);

    // 多个读线程
    auto reader = [&](int id) {
        for (int i = 0; i < 10; ++i) {
            int value = data.read();
            std::cout << "Reader " << id << ": " << value << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    };

    // 单个写线程
    auto writer = [&]() {
        for (int i = 0; i < 5; ++i) {
            data.write(i * 100);
            std::cout << "Writer: " << i * 100 << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
    };

    std::vector<std::thread> threads;
    threads.emplace_back(writer);
    for (int i = 0; i < 3; ++i) {
        threads.emplace_back(reader, i);
    }

    for (auto& t : threads) {
        t.join();
    }
}

// 性能测试
void performance_test() {
    std::cout << "\n=== 性能测试 ===" << std::endl;

    const int iterations = 100000;
    const int num_readers = 4;

    // 读写锁
    {
        SharedData data(0);
        std::atomic<int> read_count{0};

        auto start = std::chrono::high_resolution_clock::now();

        std::vector<std::thread> threads;
        for (int i = 0; i < num_readers; ++i) {
            threads.emplace_back([&]() {
                for (int j = 0; j < iterations; ++j) {
                    data.read();
                    read_count.fetch_add(1);
                }
            });
        }

        for (auto& t : threads) {
            t.join();
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "读写锁: " << time.count() << " ms, 读取次数: " << read_count.load() << std::endl;
    }

    // 互斥锁
    {
        std::mutex mutex;
        int data = 0;
        std::atomic<int> read_count{0};

        auto start = std::chrono::high_resolution_clock::now();

        std::vector<std::thread> threads;
        for (int i = 0; i < num_readers; ++i) {
            threads.emplace_back([&]() {
                for (int j = 0; j < iterations; ++j) {
                    std::lock_guard lock(mutex);
                    (void)data;
                    read_count.fetch_add(1);
                }
            });
        }

        for (auto& t : threads) {
            t.join();
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "互斥锁: " << time.count() << " ms, 读取次数: " << read_count.load() << std::endl;
    }
}

// 读多写少场景
void read_heavy_workload() {
    std::cout << "\n=== 读多写少场景 ===" << std::endl;

    SharedData data(0);
    const int read_ops = 100000;
    const int write_ops = 1000;

    std::atomic<int> reads{0};
    std::atomic<int> writes{0};

    auto start = std::chrono::high_resolution_clock::now();

    // 多个读线程
    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&]() {
            for (int j = 0; j < read_ops; ++j) {
                data.read();
                reads.fetch_add(1);
            }
        });
    }

    // 少量写线程
    threads.emplace_back([&]() {
        for (int j = 0; j < write_ops; ++j) {
            data.write(j);
            writes.fetch_add(1);
        }
    });

    for (auto& t : threads) {
        t.join();
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "读取次数: " << reads.load() << std::endl;
    std::cout << "写入次数: " << writes.load() << std::endl;
    std::cout << "耗时: " << time.count() << " ms" << std::endl;
}

int main() {
    std::cout << "C++ 并发数据结构：读写锁" << std::endl;
    std::cout << "=========================\n" << std::endl;

    basic_test();
    performance_test();
    read_heavy_workload();

    return 0;
}
