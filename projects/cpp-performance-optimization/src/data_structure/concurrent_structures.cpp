/**
 * @file concurrent_structures.cpp
 * @brief 并发数据结构示例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <thread>
#include <mutex>
#include <shared_mutex>
#include <unordered_map>
#include <atomic>

class Timer
{
public:
    using Clock = std::chrono::high_resolution_clock;
    Timer() : start_(Clock::now()) {}
    void reset() { start_ = Clock::now(); }
    double elapsedMs() const {
        return std::chrono::duration_cast<std::chrono::nanoseconds>(
            Clock::now() - start_).count() / 1e6;
    }
private:
    Clock::time_point start_;
};

/**
 * @brief 线程安全的读写锁哈希表
 */
template<typename K, typename V>
class ConcurrentHashMap
{
    std::unordered_map<K, V> map_;
    mutable std::shared_mutex mutex_;

public:
    void insert(const K& key, const V& value)
    {
        std::unique_lock lock(mutex_);
        map_[key] = value;
    }

    bool find(const K& key, V& value) const
    {
        std::shared_lock lock(mutex_);
        auto it = map_.find(key);
        if (it == map_.end()) return false;
        value = it->second;
        return true;
    }

    size_t size() const
    {
        std::shared_lock lock(mutex_);
        return map_.size();
    }
};

void demonstrateReadWriteLock()
{
    std::cout << "=== 读写锁模式 ===\n\n";

    const size_t N = 100000;
    const size_t num_threads = 4;

    ConcurrentHashMap<int, int> map;

    // 预填充数据
    for (int i = 0; i < 10000; ++i) {
        map.insert(i, i);
    }

    Timer timer;
    std::vector<std::thread> threads;

    // 读线程
    for (size_t t = 0; t < num_threads - 1; ++t) {
        threads.emplace_back([&map, N]() {
            int value;
            for (size_t i = 0; i < N; ++i) {
                map.find(static_cast<int>(i % 10000), value);
            }
        });
    }

    // 写线程
    threads.emplace_back([&map, N]() {
        for (size_t i = 0; i < N / 10; ++i) {
            map.insert(static_cast<int>(i), static_cast<int>(i));
        }
    });

    for (auto& t : threads) t.join();
    double time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "读写锁哈希表: " << time << " ms\n";
    std::cout << "最终大小: " << map.size() << "\n";
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  并发数据结构\n";
    std::cout << "========================================\n\n";
    demonstrateReadWriteLock();
    std::cout << "\n总结: 读写锁适合读多写少的场景。\n";
    return 0;
}
