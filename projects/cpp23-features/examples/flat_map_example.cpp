/**
 * @file flat_map_example.cpp
 * @brief C++23 std::flat_map 和 std::flat_set 示例
 *
 * std::flat_map 和 std::flat_set 是 C++23 引入的扁平容器。
 * 它们基于排序的 vector 实现，提供更好的缓存局部性。
 *
 * 主要特点：
 * - 基于排序的 vector 实现
 * - 更好的缓存局部性
 * - 更少的内存分配
 * - 与 std::map/std::set 接口兼容
 *
 * 编译命令：
 * g++ -std=c++23 -o flat_map_example flat_map_example.cpp
 */

#include <iostream>
#include <flat_map>
#include <flat_set>
#include <string>
#include <vector>
#include <algorithm>
#include <chrono>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // 创建 flat_map
    std::flat_map<std::string, int> scores;

    // 插入元素
    scores["Alice"] = 95;
    scores["Bob"] = 87;
    scores["Charlie"] = 92;
    scores.insert({"David", 88});
    scores.emplace("Eve", 91);

    // 访问元素
    std::cout << "Alice's score: " << scores["Alice"] << std::endl;
    std::cout << "Bob's score: " << scores.at("Bob") << std::endl;

    // 遍历 (按 key 排序)
    std::cout << "\nAll scores (sorted by name):" << std::endl;
    for (const auto& [name, score] : scores) {
        std::cout << "  " << name << ": " << score << std::endl;
    }

    // 检查是否存在
    if (scores.contains("Charlie")) {
        std::cout << "\nCharlie exists with score: " << scores["Charlie"] << std::endl;
    }

    // 删除元素
    scores.erase("Bob");
    std::cout << "\nAfter erasing Bob:" << std::endl;
    for (const auto& [name, score] : scores) {
        std::cout << "  " << name << ": " << score << std::endl;
    }
}

// ========== 2. flat_set 基本用法 ==========

void flat_set_basic() {
    std::cout << "\n=== flat_set 基本用法 ===" << std::endl;

    // 创建 flat_set
    std::flat_set<int> numbers = {5, 2, 8, 1, 9, 3, 7};

    // 自动排序
    std::cout << "Sorted numbers: ";
    for (int n : numbers) {
        std::cout << n << " ";
    }
    std::cout << std::endl;

    // 插入元素
    numbers.insert(4);
    numbers.insert(6);
    numbers.insert(5);  // 重复元素不会插入

    std::cout << "After inserting 4, 6, 5: ";
    for (int n : numbers) {
        std::cout << n << " ";
    }
    std::cout << std::endl;

    // 查找元素
    if (numbers.contains(5)) {
        std::cout << "5 is in the set" << std::endl;
    }

    // 删除元素
    numbers.erase(3);
    std::cout << "After erasing 3: ";
    for (int n : numbers) {
        std::cout << n << " ";
    }
    std::cout << std::endl;
}

// ========== 3. 初始化方式 ==========

void initialization() {
    std::cout << "\n=== 初始化方式 ===" << std::endl;

    // 使用 initializer_list
    std::flat_map<std::string, int> map1 = {
        {"one", 1},
        {"two", 2},
        {"three", 3}
    };

    // 使用 vector of pairs
    std::vector<std::pair<std::string, int>> pairs = {
        {"four", 4},
        {"five", 5},
        {"six", 6}
    };
    std::flat_map<std::string, int> map2(pairs.begin(), pairs.end());

    // 使用 sorted 构造
    std::vector<std::string> keys = {"seven", "eight", "nine"};
    std::vector<int> values = {7, 8, 9};
    std::flat_map<std::string, int> map3(
        std::sorted_unique,
        keys.begin(), keys.end(),
        values.begin()
    );

    // 打印结果
    std::cout << "map1: ";
    for (const auto& [k, v] : map1) std::cout << k << ":" << v << " ";
    std::cout << std::endl;

    std::cout << "map2: ";
    for (const auto& [k, v] : map2) std::cout << k << ":" << v << " ";
    std::cout << std::endl;

    std::cout << "map3: ";
    for (const auto& [k, v] : map3) std::cout << k << ":" << v << " ";
    std::cout << std::endl;
}

// ========== 4. 查找操作 ==========

void search_operations() {
    std::cout << "\n=== 查找操作 ===" << std::endl;

    std::flat_map<std::string, int> map = {
        {"apple", 1},
        {"banana", 2},
        {"cherry", 3},
        {"date", 4},
        {"elderberry", 5}
    };

    // find
    auto it = map.find("cherry");
    if (it != map.end()) {
        std::cout << "Found: " << it->first << " -> " << it->second << std::endl;
    }

    // lower_bound / upper_bound
    auto lb = map.lower_bound("b");
    auto ub = map.upper_bound("d");
    std::cout << "Range [b, d): ";
    for (auto it = lb; it != ub; ++it) {
        std::cout << it->first << " ";
    }
    std::cout << std::endl;

    // equal_range
    auto [first, last] = map.equal_range("cherry");
    std::cout << "Equal range for 'cherry': ";
    for (auto it = first; it != last; ++it) {
        std::cout << it->first << ":" << it->second << " ";
    }
    std::cout << std::endl;

    // count
    std::cout << "Count of 'apple': " << map.count("apple") << std::endl;
    std::cout << "Count of 'fig': " << map.count("fig") << std::endl;
}

// ========== 5. 容量和修改 ==========

void capacity_and_modification() {
    std::cout << "\n=== 容量和修改 ===" << std::endl;

    std::flat_map<std::string, int> map;

    // 检查是否为空
    std::cout << "Is empty: " << (map.empty() ? "yes" : "no") << std::endl;

    // 插入多个元素
    map.insert({
        {"a", 1}, {"b", 2}, {"c", 3}, {"d", 4}, {"e", 5}
    });

    std::cout << "Size: " << map.size() << std::endl;

    // 清空
    map.clear();
    std::cout << "After clear, size: " << map.size() << std::endl;

    // 重新插入
    map["x"] = 10;
    map["y"] = 20;
    map["z"] = 30;

    // 交换
    std::flat_map<std::string, int> other = {{"p", 100}, {"q", 200}};
    map.swap(other);

    std::cout << "After swap:" << std::endl;
    std::cout << "  map: ";
    for (const auto& [k, v] : map) std::cout << k << ":" << v << " ";
    std::cout << std::endl;
    std::cout << "  other: ";
    for (const auto& [k, v] : other) std::cout << k << ":" << v << " ";
    std::cout << std::endl;
}

// ========== 6. 与 std::map 性能对比 ==========

void performance_comparison() {
    std::cout << "\n=== 性能对比 ===" << std::endl;

    const int N = 10000;

    // 测试 flat_map
    auto start1 = std::chrono::high_resolution_clock::now();
    std::flat_map<int, int> flat_map;
    for (int i = 0; i < N; ++i) {
        flat_map[i] = i * 2;
    }
    for (int i = 0; i < N; ++i) {
        volatile auto val = flat_map[i];
        (void)val;
    }
    auto end1 = std::chrono::high_resolution_clock::now();
    auto duration1 = std::chrono::duration_cast<std::chrono::microseconds>(end1 - start1);

    // 测试 std::map
    auto start2 = std::chrono::high_resolution_clock::now();
    std::map<int, int> std_map;
    for (int i = 0; i < N; ++i) {
        std_map[i] = i * 2;
    }
    for (int i = 0; i < N; ++i) {
        volatile auto val = std_map[i];
        (void)val;
    }
    auto end2 = std::chrono::high_resolution_clock::now();
    auto duration2 = std::chrono::duration_cast<std::chrono::microseconds>(end2 - start2);

    std::cout << "flat_map: " << duration1.count() << " microseconds" << std::endl;
    std::cout << "std::map: " << duration2.count() << " microseconds" << std::endl;
    std::cout << "flat_map is " << static_cast<double>(duration2.count()) / duration1.count()
              << "x faster" << std::endl;
}

// ========== 7. 实际应用：缓存系统 ==========

class Cache {
private:
    std::flat_map<std::string, std::pair<std::string, std::chrono::steady_clock::time_point>> cache_;
    std::chrono::seconds ttl_;

public:
    Cache(std::chrono::seconds ttl = std::chrono::seconds(60)) : ttl_(ttl) {}

    void put(const std::string& key, const std::string& value) {
        cache_[key] = {value, std::chrono::steady_clock::now()};
    }

    std::optional<std::string> get(const std::string& key) {
        auto it = cache_.find(key);
        if (it == cache_.end()) {
            return std::nullopt;
        }

        // 检查是否过期
        auto elapsed = std::chrono::steady_clock::now() - it->second.second;
        if (elapsed > ttl_) {
            cache_.erase(it);
            return std::nullopt;
        }

        return it->second.first;
    }

    void clear_expired() {
        auto now = std::chrono::steady_clock::now();
        for (auto it = cache_.begin(); it != cache_.end();) {
            if (now - it->second.second > ttl_) {
                it = cache_.erase(it);
            } else {
                ++it;
            }
        }
    }

    size_t size() const { return cache_.size(); }
};

void cache_example() {
    std::cout << "\n=== 实际应用：缓存系统 ===" << std::endl;

    Cache cache(std::chrono::seconds(5));

    cache.put("user:1", "Alice");
    cache.put("user:2", "Bob");
    cache.put("user:3", "Charlie");

    std::cout << "Cache size: " << cache.size() << std::endl;

    // 获取缓存
    if (auto value = cache.get("user:1")) {
        std::cout << "user:1 = " << *value << std::endl;
    }

    // 获取不存在的缓存
    if (auto value = cache.get("user:99")) {
        std::cout << "user:99 = " << *value << std::endl;
    } else {
        std::cout << "user:99 not found" << std::endl;
    }
}

// ========== 8. flat_set 高级用法 ==========

void flat_set_advanced() {
    std::cout << "\n=== flat_set 高级用法 ===" << std::endl;

    // 集合操作
    std::flat_set<int> set1 = {1, 2, 3, 4, 5};
    std::flat_set<int> set2 = {4, 5, 6, 7, 8};

    // 并集
    std::flat_set<int> union_set;
    std::set_union(set1.begin(), set1.end(),
                   set2.begin(), set2.end(),
                   std::inserter(union_set, union_set.begin()));
    std::cout << "Union: ";
    for (int n : union_set) std::cout << n << " ";
    std::cout << std::endl;

    // 交集
    std::flat_set<int> intersection_set;
    std::set_intersection(set1.begin(), set1.end(),
                          set2.begin(), set2.end(),
                          std::inserter(intersection_set, intersection_set.begin()));
    std::cout << "Intersection: ";
    for (int n : intersection_set) std::cout << n << " ";
    std::cout << std::endl;

    // 差集
    std::flat_set<int> difference_set;
    std::set_difference(set1.begin(), set1.end(),
                        set2.begin(), set2.end(),
                        std::inserter(difference_set, difference_set.begin()));
    std::cout << "Difference (set1 - set2): ";
    for (int n : difference_set) std::cout << n << " ";
    std::cout << std::endl;
}

int main() {
    std::cout << "C++23 std::flat_map / std::flat_set 示例\n" << std::endl;

    basic_usage();
    flat_set_basic();
    initialization();
    search_operations();
    capacity_and_modification();
    performance_comparison();
    cache_example();
    flat_set_advanced();

    return 0;
}
