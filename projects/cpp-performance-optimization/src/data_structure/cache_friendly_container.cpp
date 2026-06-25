/**
 * @file cache_friendly_container.cpp
 * @brief 缓存友好容器示例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <map>
#include <unordered_map>
#include <algorithm>
#include <random>

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
 * @brief flat_map: 基于排序 vector 的 map
 */
template<typename K, typename V>
class FlatMap
{
    std::vector<std::pair<K, V>> data_;

public:
    void insert(const K& key, const V& value)
    {
        auto it = std::lower_bound(data_.begin(), data_.end(), key,
            [](const auto& p, const K& k) { return p.first < k; });
        if (it != data_.end() && it->first == key) {
            it->second = value;
        } else {
            data_.insert(it, {key, value});
        }
    }

    bool find(const K& key, V& value) const
    {
        auto it = std::lower_bound(data_.begin(), data_.end(), key,
            [](const auto& p, const K& k) { return p.first < k; });
        if (it != data_.end() && it->first == key) {
            value = it->second;
            return true;
        }
        return false;
    }

    size_t size() const { return data_.size(); }
};

void demonstrateFlatMapVsTreeMap()
{
    std::cout << "=== flat_map vs std::map ===\n\n";

    const size_t N = 100000;
    const size_t QUERIES = 500000;

    std::vector<int> keys(N);
    for (size_t i = 0; i < N; ++i) keys[i] = static_cast<int>(i);
    std::mt19937 rng(42);
    std::shuffle(keys.begin(), keys.end(), rng);

    std::vector<int> query_keys(QUERIES);
    for (auto& q : query_keys) q = rng() % N;

    // std::map
    {
        std::map<int, int> map;
        for (auto k : keys) map[k] = k;

        Timer timer;
        volatile int sum = 0;
        for (auto q : query_keys) {
            auto it = map.find(q);
            if (it != map.end()) sum += it->second;
        }
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "std::map 查询: " << time << " ms\n";
        (void)sum;
    }

    // flat_map
    {
        FlatMap<int, int> map;
        for (auto k : keys) map.insert(k, k);

        Timer timer;
        volatile int sum = 0;
        int value;
        for (auto q : query_keys) {
            if (map.find(q, value)) sum += value;
        }
        double time = timer.elapsedMs();
        std::cout << "flat_map 查询: " << time << " ms\n";
        (void)sum;
    }

    // unordered_map
    {
        std::unordered_map<int, int> map;
        for (auto k : keys) map[k] = k;

        Timer timer;
        volatile int sum = 0;
        for (auto q : query_keys) {
            auto it = map.find(q);
            if (it != map.end()) sum += it->second;
        }
        double time = timer.elapsedMs();
        std::cout << "unordered_map: " << time << " ms\n";
        (void)sum;
    }
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  缓存友好容器\n";
    std::cout << "========================================\n\n";
    demonstrateFlatMapVsTreeMap();
    std::cout << "\n总结: flat_map 利用连续内存，遍历性能优于树形 map。\n";
    return 0;
}
