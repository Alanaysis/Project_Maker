/**
 * @file f14_hashmap_example.cpp
 * @brief Folly F14HashMap 示例
 * @details 展示 Folly 的 F14HashMap 使用方法
 *          Folly 是 Facebook 开源的 C++ 基础库
 *          F14HashMap 是高性能的哈希表实现
 */

#include <iostream>
#include <string>
#include <folly/container/F14Map.h>

/**
 * @brief 基础用法示例
 * @details 展示 F14HashMap 的基本操作
 */
void basic_usage() {
    std::cout << "=== 基础用法 ===" << std::endl;

    // 创建 F14HashMap
    folly::F14FastMap<int, std::string> map;

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
 * @details 展示 F14HashMap 的查找功能
 */
void search_operations() {
    std::cout << "=== 查找操作 ===" << std::endl;

    folly::F14FastMap<std::string, int> scores = {
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

    // 使用 count 检查存在性
    if (scores.count("Eve") == 0) {
        std::cout << "Eve not found" << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief 性能特点示例
 * @details 展示 F14HashMap 的性能优势
 */
void performance_features() {
    std::cout << "=== 性能特点 ===" << std::endl;

    std::cout << "F14HashMap 优势：" << std::endl;
    std::cout << "  - 14 项优化" << std::endl;
    std::cout << "  - 内存布局优化" << std::endl;
    std::cout << "  - 缓存友好" << std::endl;
    std::cout << "  - 查找性能优秀" << std::endl;

    std::cout << std::endl;

    std::cout << "F14 变体：" << std::endl;
    std::cout << "  - F14FastMap: 通用场景" << std::endl;
    std::cout << "  - F14NodeMap: 节点稳定" << std::endl;
    std::cout << "  - F14ValueMap: 值语义" << std::endl;
    std::cout << "  - F14VectorMap: 小集合优化" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 F14HashMap 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：词频统计
    std::vector<std::string> words = {
        "hello", "world", "hello", "foo", "bar", "hello", "world"
    };

    folly::F14FastMap<std::string, int> word_count;
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
    std::cout << "=== Folly F14HashMap 示例 ===" << std::endl;
    std::cout << std::endl;

    basic_usage();
    search_operations();
    performance_features();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}