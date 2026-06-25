/**
 * @file hash_table.cpp
 * @brief 哈希表优化案例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <unordered_map>
#include <map>
#include <algorithm>
#include <random>
#include <functional>

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
 * @brief 开放寻址哈希表
 */
template<typename K, typename V>
class OpenAddressingMap
{
    struct Entry {
        K key;
        V value;
        bool occupied = false;
        bool deleted = false;
    };

    std::vector<Entry> table_;
    size_t size_ = 0;
    double load_factor_ = 0.7;

    size_t hash(const K& key) const {
        return std::hash<K>{}(key) % table_.size();
    }

public:
    explicit OpenAddressingMap(size_t capacity = 16) : table_(capacity) {}

    void insert(const K& key, const V& value)
    {
        if (size_ > table_.size() * load_factor_) {
            rehash();
        }
        size_t idx = hash(key);
        while (table_[idx].occupied && table_[idx].key != key) {
            idx = (idx + 1) % table_.size();
        }
        table_[idx] = {key, value, true, false};
        ++size_;
    }

    bool find(const K& key, V& value) const
    {
        size_t idx = hash(key);
        size_t start = idx;
        while (table_[idx].occupied || table_[idx].deleted) {
            if (table_[idx].occupied && table_[idx].key == key) {
                value = table_[idx].value;
                return true;
            }
            idx = (idx + 1) % table_.size();
            if (idx == start) break;
        }
        return false;
    }

    void rehash()
    {
        std::vector<Entry> old = std::move(table_);
        table_.resize(old.size() * 2);
        size_ = 0;
        for (auto& e : old) {
            if (e.occupied) insert(e.key, e.value);
        }
    }

    size_t size() const { return size_; }
};

void demonstrateHashTables()
{
    std::cout << "=== 哈希表实现对比 ===\n\n";

    const size_t N = 1000000;
    const size_t QUERIES = 500000;

    std::vector<int> keys(N);
    for (size_t i = 0; i < N; ++i) keys[i] = static_cast<int>(i);
    std::mt19937 rng(42);
    std::shuffle(keys.begin(), keys.end(), rng);

    std::vector<int> query_keys(QUERIES);
    for (auto& q : query_keys) q = rng() % N;

    // std::unordered_map
    {
        std::unordered_map<int, int> map;
        Timer timer;
        for (auto k : keys) map[k] = k;
        double insert_time = timer.elapsedMs();

        timer.reset();
        volatile int sum = 0;
        for (auto q : query_keys) {
            auto it = map.find(q);
            if (it != map.end()) sum += it->second;
        }
        double query_time = timer.elapsedMs();

        std::cout << std::fixed << std::setprecision(2);
        std::cout << "unordered_map - 插入: " << insert_time << " ms, 查询: " << query_time << " ms\n";
        (void)sum;
    }

    // 开放寻址哈希表
    {
        OpenAddressingMap<int, int> map(N * 2);
        Timer timer;
        for (auto k : keys) map.insert(k, k);
        double insert_time = timer.elapsedMs();

        timer.reset();
        volatile int sum = 0;
        int value;
        for (auto q : query_keys) {
            if (map.find(q, value)) sum += value;
        }
        double query_time = timer.elapsedMs();

        std::cout << "开放寻址哈希表 - 插入: " << insert_time << " ms, 查询: " << query_time << " ms\n";
        (void)sum;
    }

    // std::map (红黑树)
    {
        std::map<int, int> map;
        Timer timer;
        for (auto k : keys) map[k] = k;
        double insert_time = timer.elapsedMs();

        timer.reset();
        volatile int sum = 0;
        for (auto q : query_keys) {
            auto it = map.find(q);
            if (it != map.end()) sum += it->second;
        }
        double query_time = timer.elapsedMs();

        std::cout << "std::map - 插入: " << insert_time << " ms, 查询: " << query_time << " ms\n";
        (void)sum;
    }
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  哈希表优化\n";
    std::cout << "========================================\n\n";
    demonstrateHashTables();
    std::cout << "\n总结: 开放寻址哈希表缓存友好，通常比链式哈希表更快。\n";
    return 0;
}
