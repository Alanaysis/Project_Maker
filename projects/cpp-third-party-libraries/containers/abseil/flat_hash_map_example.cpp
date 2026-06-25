/**
 * @file flat_hash_map_example.cpp
 * @brief Abseil flat_hash_map 示例
 * @details 展示 Abseil 的 flat_hash_map 使用方法
 *          Abseil 是 Google 开源的 C++ 基础库
 *          flat_hash_map 是高性能的哈希表实现
 */

#include <iostream>
#include <string>
#include <vector>
#include <absl/container/flat_hash_map.h>

/**
 * @brief 基础用法示例
 * @details 展示 flat_hash_map 的基本操作
 */
void basic_usage() {
    std::cout << "=== 基础用法 ===" << std::endl;

    // 创建 flat_hash_map
    absl::flat_hash_map<int, std::string> map;

    // 插入元素
    map[1] = "Apple";
    map[2] = "Banana";
    map.insert({3, "Cherry"});
    map.emplace(4, "Date");

    // 遍历
    for (const auto& [key, value] : map) {
        std::cout << key << ": " << value << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief 查找操作示例
 * @details 展示 flat_hash_map 的查找功能
 */
void search_operations() {
    std::cout << "=== 查找操作 ===" << std::endl;

    absl::flat_hash_map<std::string, int> scores = {
        {"Alice", 95},
        {"Bob", 87},
        {"Charlie", 92},
        {"David", 78}
    };

    // 使用 find 查找
    auto it = scores.find("Bob");
    if (it != scores.end()) {
        std::cout << "Bob's score: " << it->second << std::endl;
    }

    // 使用 contains 检查存在性 (C++20)
    if (scores.find("Eve") == scores.end()) {
        std::cout << "Eve not found" << std::endl;
    }

    // 使用 count
    std::cout << "Count of Alice: " << scores.count("Alice") << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 性能特点示例
 * @details 展示 flat_hash_map 的性能优势
 */
void performance_features() {
    std::cout << "=== 性能特点 ===" << std::endl;

    std::cout << "flat_hash_map 优势：" << std::endl;
    std::cout << "  - 基于 Swiss Table 算法" << std::endl;
    std::cout << "  - 内存布局优化" << std::endl;
    std::cout << "  - 缓存友好" << std::endl;
    std::cout << "  - 查找性能优秀" << std::endl;

    std::cout << std::endl;

    std::cout << "与 std::unordered_map 对比：" << std::endl;
    std::cout << "  - 更快的查找" << std::endl;
    std::cout << "  - 更低的内存占用" << std::endl;
    std::cout << "  - 更好的缓存局部性" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 flat_hash_map 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：词频统计
    std::vector<std::string> words = {
        "hello", "world", "hello", "foo", "bar", "hello", "world"
    };

    absl::flat_hash_map<std::string, int> word_count;
    for (const auto& word : words) {
        word_count[word]++;
    }

    std::cout << "Word frequencies:" << std::endl;
    for (const auto& [word, count] : word_count) {
        std::cout << "  " << word << ": " << count << std::endl;
    }

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Abseil flat_hash_map 示例 ===" << std::endl;
    std::cout << std::endl;

    basic_usage();
    search_operations();
    performance_features();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}