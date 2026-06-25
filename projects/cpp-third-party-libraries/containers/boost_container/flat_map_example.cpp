/**
 * @file flat_map_example.cpp
 * @brief Boost.Container flat_map 示例
 * @details 展示 boost::container::flat_map 的使用方法
 *          flat_map 是基于排序 vector 实现的关联容器
 *          适合读多写少的场景，内存局部性好
 */

#include <iostream>
#include <string>
#include <boost/container/flat_map.hpp>

/**
 * @brief 基础用法示例
 * @details 展示 flat_map 的基本操作
 */
void basic_usage() {
    std::cout << "=== 基础用法 ===" << std::endl;

    // 创建 flat_map
    boost::container::flat_map<int, std::string> map;

    // 插入元素
    map.insert({1, "Apple"});
    map.insert({2, "Banana"});
    map.insert({3, "Cherry"});

    // 使用下标访问
    map[4] = "Date";

    // 遍历
    for (const auto& [key, value] : map) {
        std::cout << key << ": " << value << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief 查找操作示例
 * @details 展示 flat_map 的查找功能
 */
void search_operations() {
    std::cout << "=== 查找操作 ===" << std::endl;

    boost::container::flat_map<std::string, int> scores = {
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

    // 使用 lower_bound 和 upper_bound
    auto lower = scores.lower_bound("B");
    auto upper = scores.lower_bound("D");

    std::cout << "Names between B and D:" << std::endl;
    for (auto iter = lower; iter != upper; ++iter) {
        std::cout << "  " << iter->first << ": " << iter->second << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief 性能对比示例
 * @details 展示 flat_map 与 std::map 的性能差异
 */
void performance_comparison() {
    std::cout << "=== 性能特点 ===" << std::endl;

    std::cout << "flat_map 优势:" << std::endl;
    std::cout << "  - 内存连续，缓存友好" << std::endl;
    std::cout << "  - 查找性能接近二分查找" << std::endl;
    std::cout << "  - 适合读多写少的场景" << std::endl;

    std::cout << std::endl;

    std::cout << "flat_map 劣势:" << std::endl;
    std::cout << "  - 插入/删除需要移动元素" << std::endl;
    std::cout << "  - 迭代器可能失效" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 flat_map 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：配置管理
    boost::container::flat_map<std::string, std::string> config = {
        {"host", "localhost"},
        {"port", "8080"},
        {"debug", "true"},
        {"log_level", "INFO"}
    };

    // 读取配置
    auto get_config = [&config](const std::string& key, const std::string& default_value) {
        auto it = config.find(key);
        return it != config.end() ? it->second : default_value;
    };

    std::cout << "Server Configuration:" << std::endl;
    std::cout << "  Host: " << get_config("host", "0.0.0.0") << std::endl;
    std::cout << "  Port: " << get_config("port", "80") << std::endl;
    std::cout << "  Debug: " << get_config("debug", "false") << std::endl;

    // 更新配置
    config["port"] = "9090";
    std::cout << "  Updated Port: " << get_config("port", "80") << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Boost.Container flat_map 示例 ===" << std::endl;
    std::cout << std::endl;

    basic_usage();
    search_operations();
    performance_comparison();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}