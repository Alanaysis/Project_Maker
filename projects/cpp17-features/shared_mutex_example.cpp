/**
 * @file shared_mutex_example.cpp
 * @brief C++17 std::shared_mutex 示例
 *
 * std::shared_mutex 提供了共享/独占锁机制。
 * 它允许多个读取者同时访问资源，但写入者需要独占访问。
 *
 * 主要优势：
 * 1. 读写分离 - 提升读多写少场景的性能
 * 2. 标准化 - 无需依赖第三方库
 * 3. 灵活性 - 支持共享锁和独占锁
 */

#include <iostream>
#include <shared_mutex>
#include <mutex>
#include <thread>
#include <vector>
#include <string>
#include <chrono>
#include <atomic>
#include <functional>
#include <map>

// 1. 基本使用
void basic_example() {
    std::cout << "\n[基本使用]" << std::endl;

    std::shared_mutex mtx;
    int shared_data = 0;

    // 读取线程
    auto reader = [&]() {
        std::shared_lock<std::shared_mutex> lock(mtx);
        std::cout << "Reader: " << shared_data << std::endl;
    };

    // 写入线程
    auto writer = [&](int value) {
        std::unique_lock<std::shared_mutex> lock(mtx);
        shared_data = value;
        std::cout << "Writer: " << value << std::endl;
    };

    // 启动线程
    std::vector<std::thread> threads;

    // 多个读取者
    for (int i = 0; i < 3; ++i) {
        threads.emplace_back(reader);
    }

    // 一个写入者
    threads.emplace_back(writer, 42);

    // 更多读取者
    for (int i = 0; i < 3; ++i) {
        threads.emplace_back(reader);
    }

    // 等待所有线程完成
    for (auto& t : threads) {
        t.join();
    }
}

// 2. 线程安全的容器
template <typename T>
class ThreadSafeVector {
public:
    void push_back(const T& value) {
        std::unique_lock<std::shared_mutex> lock(mutex_);
        data_.push_back(value);
    }

    T get(size_t index) const {
        std::shared_lock<std::shared_mutex> lock(mutex_);
        return data_.at(index);
    }

    size_t size() const {
        std::shared_lock<std::shared_mutex> lock(mutex_);
        return data_.size();
    }

    void clear() {
        std::unique_lock<std::shared_mutex> lock(mutex_);
        data_.clear();
    }

private:
    mutable std::shared_mutex mutex_;
    std::vector<T> data_;
};

void thread_safe_container_example() {
    std::cout << "\n[线程安全的容器]" << std::endl;

    ThreadSafeVector<int> vec;

    // 写入线程
    auto writer = [&](int start, int count) {
        for (int i = 0; i < count; ++i) {
            vec.push_back(start + i);
        }
    };

    // 读取线程
    auto reader = [&]() {
        size_t size = vec.size();
        if (size > 0) {
            std::cout << "Reader: size=" << size << ", last=" << vec.get(size - 1) << std::endl;
        }
    };

    // 启动线程
    std::vector<std::thread> threads;

    // 写入者
    threads.emplace_back(writer, 0, 100);
    threads.emplace_back(writer, 100, 100);

    // 读取者
    for (int i = 0; i < 5; ++i) {
        threads.emplace_back(reader);
    }

    // 等待完成
    for (auto& t : threads) {
        t.join();
    }

    std::cout << "Final size: " << vec.size() << std::endl;
}

// 3. 读写锁模式
class ReadWriteLock {
public:
    void read_lock() {
        mutex_.lock_shared();
    }

    void read_unlock() {
        mutex_.unlock_shared();
    }

    void write_lock() {
        mutex_.lock();
    }

    void write_unlock() {
        mutex_.unlock();
    }

private:
    std::shared_mutex mutex_;
};

void read_write_lock_example() {
    std::cout << "\n[读写锁模式]" << std::endl;

    ReadWriteLock rwlock;
    int data = 0;
    std::atomic<int> read_count{0};
    std::atomic<int> write_count{0};

    // 读取函数
    auto reader = [&]() {
        rwlock.read_lock();
        ++read_count;
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        --read_count;
        rwlock.read_unlock();
    };

    // 写入函数
    auto writer = [&](int value) {
        rwlock.write_lock();
        ++write_count;
        data = value;
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        --write_count;
        rwlock.write_unlock();
    };

    // 启动线程
    std::vector<std::thread> threads;

    // 多个读取者
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back(reader);
    }

    // 写入者
    threads.emplace_back(writer, 42);

    // 更多读取者
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back(reader);
    }

    // 等待完成
    for (auto& t : threads) {
        t.join();
    }

    std::cout << "Final data: " << data << std::endl;
}

// 4. 缓存系统
class Cache {
public:
    std::string get(const std::string& key) const {
        std::shared_lock<std::shared_mutex> lock(mutex_);
        auto it = cache_.find(key);
        if (it != cache_.end()) {
            return it->second;
        }
        return "";
    }

    void put(const std::string& key, const std::string& value) {
        std::unique_lock<std::shared_mutex> lock(mutex_);
        cache_[key] = value;
    }

    bool contains(const std::string& key) const {
        std::shared_lock<std::shared_mutex> lock(mutex_);
        return cache_.find(key) != cache_.end();
    }

    void clear() {
        std::unique_lock<std::shared_mutex> lock(mutex_);
        cache_.clear();
    }

private:
    mutable std::shared_mutex mutex_;
    std::map<std::string, std::string> cache_;
};

void cache_example() {
    std::cout << "\n[缓存系统]" << std::endl;

    Cache cache;

    // 写入线程
    auto writer = [&]() {
        for (int i = 0; i < 10; ++i) {
            std::string key = "key" + std::to_string(i);
            std::string value = "value" + std::to_string(i);
            cache.put(key, value);
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    };

    // 读取线程
    auto reader = [&]() {
        for (int i = 0; i < 5; ++i) {
            std::string key = "key" + std::to_string(i);
            std::string value = cache.get(key);
            if (!value.empty()) {
                std::cout << "Read: " << key << " = " << value << std::endl;
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        }
    };

    // 启动线程
    std::vector<std::thread> threads;
    threads.emplace_back(writer);
    threads.emplace_back(reader);
    threads.emplace_back(reader);

    // 等待完成
    for (auto& t : threads) {
        t.join();
    }

    std::cout << "Cache contains 'key5': "
              << (cache.contains("key5") ? "true" : "false") << std::endl;
}

// 5. 配置管理器
class ConfigManager {
public:
    std::string get(const std::string& key) const {
        std::shared_lock<std::shared_mutex> lock(mutex_);
        auto it = config_.find(key);
        return it != config_.end() ? it->second : "";
    }

    void set(const std::string& key, const std::string& value) {
        std::unique_lock<std::shared_mutex> lock(mutex_);
        config_[key] = value;
    }

    void load(const std::map<std::string, std::string>& new_config) {
        std::unique_lock<std::shared_mutex> lock(mutex_);
        for (const auto& [key, value] : new_config) {
            config_[key] = value;
        }
    }

    std::map<std::string, std::string> snapshot() const {
        std::shared_lock<std::shared_mutex> lock(mutex_);
        return config_;
    }

private:
    mutable std::shared_mutex mutex_;
    std::map<std::string, std::string> config_;
};

void config_manager_example() {
    std::cout << "\n[配置管理器]" << std::endl;

    ConfigManager config;

    // 初始配置
    config.set("host", "localhost");
    config.set("port", "8080");

    // 读取线程
    auto reader = [&]() {
        for (int i = 0; i < 5; ++i) {
            std::cout << "Host: " << config.get("host")
                      << ", Port: " << config.get("port") << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
    };

    // 写入线程
    auto writer = [&]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        config.set("host", "example.com");
        config.set("port", "443");
        std::cout << "Config updated" << std::endl;
    };

    // 启动线程
    std::vector<std::thread> threads;
    threads.emplace_back(reader);
    threads.emplace_back(reader);
    threads.emplace_back(writer);

    // 等待完成
    for (auto& t : threads) {
        t.join();
    }

    // 获取快照
    auto snapshot = config.snapshot();
    std::cout << "Config snapshot:" << std::endl;
    for (const auto& [key, value] : snapshot) {
        std::cout << "  " << key << " = " << value << std::endl;
    }
}

// 6. 性能对比
void performance_comparison_example() {
    std::cout << "\n[性能对比]" << std::endl;

    const int iterations = 100000;
    const int num_readers = 10;
    const int num_writers = 2;

    // 使用 std::mutex
    std::mutex regular_mutex;
    int data1 = 0;

    auto start = std::chrono::high_resolution_clock::now();

    std::vector<std::thread> threads1;
    for (int i = 0; i < num_readers; ++i) {
        threads1.emplace_back([&]() {
            for (int j = 0; j < iterations; ++j) {
                std::lock_guard<std::mutex> lock(regular_mutex);
                volatile int val = data1;
                (void)val;
            }
        });
    }
    for (int i = 0; i < num_writers; ++i) {
        threads1.emplace_back([&]() {
            for (int j = 0; j < iterations; ++j) {
                std::lock_guard<std::mutex> lock(regular_mutex);
                ++data1;
            }
        });
    }
    for (auto& t : threads1) t.join();

    auto end = std::chrono::high_resolution_clock::now();
    auto duration_mutex = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // 使用 std::shared_mutex
    std::shared_mutex shared_mutex;
    int data2 = 0;

    start = std::chrono::high_resolution_clock::now();

    std::vector<std::thread> threads2;
    for (int i = 0; i < num_readers; ++i) {
        threads2.emplace_back([&]() {
            for (int j = 0; j < iterations; ++j) {
                std::shared_lock<std::shared_mutex> lock(shared_mutex);
                volatile int val = data2;
                (void)val;
            }
        });
    }
    for (int i = 0; i < num_writers; ++i) {
        threads2.emplace_back([&]() {
            for (int j = 0; j < iterations; ++j) {
                std::unique_lock<std::shared_mutex> lock(shared_mutex);
                ++data2;
            }
        });
    }
    for (auto& t : threads2) t.join();

    end = std::chrono::high_resolution_clock::now();
    auto duration_shared = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Readers: " << num_readers << ", Writers: " << num_writers << std::endl;
    std::cout << "Iterations: " << iterations << std::endl;
    std::cout << "std::mutex: " << duration_mutex.count() << " ms" << std::endl;
    std::cout << "std::shared_mutex: " << duration_shared.count() << " ms" << std::endl;
    std::cout << "Speedup: "
              << static_cast<double>(duration_mutex.count()) / duration_shared.count() << "x" << std::endl;
}

// 7. 最佳实践
void best_practices_example() {
    std::cout << "\n[最佳实践]" << std::endl;

    std::cout << "1. 使用场景:" << std::endl;
    std::cout << "   - 读多写少的场景" << std::endl;
    std::cout << "   - 缓存系统" << std::endl;
    std::cout << "   - 配置管理" << std::endl;

    std::cout << "\n2. 锁的选择:" << std::endl;
    std::cout << "   - 读取：std::shared_lock" << std::endl;
    std::cout << "   - 写入：std::unique_lock" << std::endl;

    std::cout << "\n3. 注意事项:" << std::endl;
    std::cout << "   - 避免死锁" << std::endl;
    std::cout << "   - 避免优先级反转" << std::endl;
    std::cout << "   - 考虑锁的粒度" << std::endl;

    std::cout << "\n4. 性能考虑:" << std::endl;
    std::cout << "   - 读多写少时性能更好" << std::endl;
    std::cout << "   - 写操作频繁时可能更慢" << std::endl;
    std::cout << "   - 需要实际测试" << std::endl;
}

// 主示例函数
void shared_mutex_example() {
    std::cout << "=== std::shared_mutex ===" << std::endl;

    basic_example();
    thread_safe_container_example();
    read_write_lock_example();
    cache_example();
    config_manager_example();
    performance_comparison_example();
    best_practices_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    shared_mutex_example();
    return 0;
}
#endif
