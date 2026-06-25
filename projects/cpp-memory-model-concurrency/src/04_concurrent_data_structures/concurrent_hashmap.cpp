/**
 * 并发哈希表 (Concurrent Hash Map)
 *
 * 分段锁实现：
 * 1. 将哈希表分成多个桶
 * 2. 每个桶有独立的互斥锁
 * 3. 减少锁竞争
 * 4. 支持高并发访问
 *
 * 编译：g++ -std=c++17 -pthread concurrent_hashmap.cpp -o concurrent_hashmap
 */

#include <iostream>
#include <vector>
#include <list>
#include <mutex>
#include <shared_mutex>
#include <thread>
#include <functional>
#include <optional>
#include <chrono>

// 分段锁并发哈希表
template<typename K, typename V, typename Hash = std::hash<K>>
class ConcurrentHashMap {
private:
    struct Bucket {
        std::shared_mutex mutex;
        std::list<std::pair<K, V>> entries;
    };

    std::vector<Bucket> buckets_;
    size_t bucket_count_;
    Hash hasher_;

    Bucket& get_bucket(const K& key) {
        return buckets_[hasher_(key) % bucket_count_];
    }

    const Bucket& get_bucket(const K& key) const {
        return buckets_[hasher_(key) % bucket_count_];
    }

public:
    explicit ConcurrentHashMap(size_t bucket_count = 16)
        : buckets_(bucket_count), bucket_count_(bucket_count) {}

    // 插入或更新
    void insert(const K& key, const V& value) {
        Bucket& bucket = get_bucket(key);
        std::unique_lock lock(bucket.mutex);

        for (auto& entry : bucket.entries) {
            if (entry.first == key) {
                entry.second = value;
                return;
            }
        }
        bucket.entries.emplace_back(key, value);
    }

    // 查找
    std::optional<V> find(const K& key) const {
        const Bucket& bucket = get_bucket(key);
        std::shared_lock lock(const_cast<std::shared_mutex&>(bucket.mutex));

        for (const auto& entry : bucket.entries) {
            if (entry.first == key) {
                return entry.second;
            }
        }
        return std::nullopt;
    }

    // 删除
    bool erase(const K& key) {
        Bucket& bucket = get_bucket(key);
        std::unique_lock lock(bucket.mutex);

        for (auto it = bucket.entries.begin(); it != bucket.entries.end(); ++it) {
            if (it->first == key) {
                bucket.entries.erase(it);
                return true;
            }
        }
        return false;
    }

    // 检查是否存在
    bool contains(const K& key) const {
        return find(key).has_value();
    }

    // 获取大小
    size_t size() const {
        size_t total = 0;
        for (auto& bucket : buckets_) {
            std::shared_lock lock(const_cast<std::shared_mutex&>(bucket.mutex));
            total += bucket.entries.size();
        }
        return total;
    }

    // 遍历
    template<typename Func>
    void for_each(Func func) const {
        for (auto& bucket : buckets_) {
            std::shared_lock lock(const_cast<std::shared_mutex&>(bucket.mutex));
            for (const auto& entry : bucket.entries) {
                func(entry.first, entry.second);
            }
        }
    }
};

// 基本测试
void basic_test() {
    std::cout << "=== 基本测试 ===" << std::endl;

    ConcurrentHashMap<std::string, int> map;

    map.insert("one", 1);
    map.insert("two", 2);
    map.insert("three", 3);

    std::cout << "one: " << map.find("one").value_or(-1) << std::endl;
    std::cout << "two: " << map.find("two").value_or(-1) << std::endl;
    std::cout << "size: " << map.size() << std::endl;

    map.erase("two");
    std::cout << "after erase, two: " << (map.contains("two") ? "exists" : "not found") << std::endl;
}

// 并发测试
void concurrent_test() {
    std::cout << "\n=== 并发测试 ===" << std::endl;

    ConcurrentHashMap<int, int> map;
    const int num_threads = 4;
    const int ops_per_thread = 10000;

    auto start = std::chrono::high_resolution_clock::now();

    // 并发插入
    std::vector<std::thread> threads;
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([&map, i]() {
            for (int j = 0; j < ops_per_thread; ++j) {
                map.insert(i * ops_per_thread + j, j);
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "插入 " << map.size() << " 个元素, 耗时: " << time.count() << " ms" << std::endl;

    // 并发查找
    std::atomic<int> found{0};
    start = std::chrono::high_resolution_clock::now();

    threads.clear();
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back([&map, i, &found]() {
            for (int j = 0; j < ops_per_thread; ++j) {
                if (map.contains(i * ops_per_thread + j)) {
                    found.fetch_add(1);
                }
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    end = std::chrono::high_resolution_clock::now();
    time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "找到 " << found.load() << " 个元素, 耗时: " << time.count() << " ms" << std::endl;
}

// 性能测试
void performance_test() {
    std::cout << "\n=== 性能测试 ===" << std::endl;

    const int iterations = 100000;

    // 并发哈希表
    ConcurrentHashMap<int, int> concurrent_map;
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        concurrent_map.insert(i, i);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto concurrent_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    // 互斥哈希表
    std::mutex mutex;
    std::unordered_map<int, int> mutex_map;
    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        std::lock_guard<std::mutex> lock(mutex);
        mutex_map[i] = i;
    }
    end = std::chrono::high_resolution_clock::now();
    auto mutex_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "并发哈希表: " << concurrent_time.count() << " us" << std::endl;
    std::cout << "互斥哈希表: " << mutex_time.count() << " us" << std::endl;
}

int main() {
    std::cout << "C++ 并发数据结构：并发哈希表" << std::endl;
    std::cout << "=============================\n" << std::endl;

    basic_test();
    concurrent_test();
    performance_test();

    return 0;
}
