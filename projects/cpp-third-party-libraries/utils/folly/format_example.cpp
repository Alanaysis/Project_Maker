/**
 * @file format_example.cpp
 * @brief Folly 字符串格式化示例
 * @details 展示 Folly 的字符串格式化功能
 *          Folly 是 Facebook 开源的 C++ 基础库
 */

#include <iostream>
#include <string>
#include <vector>
#include <folly/String.h>

/**
 * @brief 基础格式化示例
 * @details 展示 folly::format 的基本用法
 */
void basic_formatting() {
    std::cout << "=== 基础格式化 ===" << std::endl;

    // 使用 folly::format
    std::string result = folly::format("Hello, {}! You are {} years old.", "Alice", 30);
    std::cout << result << std::endl;

    // 格式化数字
    result = folly::format("Pi is approximately {:.4f}", 3.14159);
    std::cout << result << std::endl;

    // 格式化对齐
    result = folly::format("{:<10} {:>10}", "Left", "Right");
    std::cout << result << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 字符串分割示例
 * @details 展示 folly::split 的用法
 */
void string_split() {
    std::cout << "=== 字符串分割 ===" << std::endl;

    // 按分隔符分割
    std::string str = "apple,banana,cherry";
    std::vector<std::string> parts;
    folly::split(',', str, parts);

    std::cout << "Split by comma:" << std::endl;
    for (const auto& part : parts) {
        std::cout << "  " << part << std::endl;
    }

    // 按多个分隔符分割
    str = "apple,banana;cherry.date";
    folly::split(",;.", str, parts, true);

    std::cout << "Split by multiple delimiters:" << std::endl;
    for (const auto& part : parts) {
        std::cout << "  " << part << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief 字符串连接示例
 * @details 展示 folly::join 的用法
 */
void string_join() {
    std::cout << "=== 字符串连接 ===" << std::endl;

    // 连接字符串向量
    std::vector<std::string> parts = {"apple", "banana", "cherry"};
    std::string joined = folly::join(", ", parts);
    std::cout << "Joined: " << joined << std::endl;

    // 连接整数向量
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    joined = folly::join(" + ", numbers);
    std::cout << "Numbers: " << joined << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 字符串修剪示例
 * @details 展示字符串修剪功能
 */
void string_trim() {
    std::cout << "=== 字符串修剪 ===" << std::endl;

    std::string str = "  Hello, World!  ";

    // 修剪两端
    std::string trimmed = folly::trimWhitespace(str);
    std::cout << "Trimmed: '" << trimmed << "'" << std::endl;

    // 修剪左侧
    trimmed = folly::ltrimWhitespace(str);
    std::cout << "Left trimmed: '" << trimmed << "'" << std::endl;

    // 修剪右侧
    trimmed = folly::rtrimWhitespace(str);
    std::cout << "Right trimmed: '" << trimmed << "'" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief Folly 概念说明
 * @details 介绍 Folly 的核心概念
 */
void folly_concepts() {
    std::cout << "=== Folly 概念 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "Folly 是 Facebook 开源的 C++ 基础库。" << std::endl;
    std::cout << std::endl;

    std::cout << "主要组件：" << std::endl;
    std::cout << "  - String: 字符串处理" << std::endl;
    std::cout << "  - Container: 高性能容器" << std::endl;
    std::cout << "  - Futures: 异步编程" << std::endl;
    std::cout << "  - Memory: 内存管理" << std::endl;
    std::cout << std::endl;

    std::cout << "主要特点：" << std::endl;
    std::cout << "  - 高性能" << std::endl;
    std::cout << "  - 现代 C++" << std::endl;
    std::cout << "  - 生产环境验证" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Folly 字符串格式化示例 ===" << std::endl;
    std::cout << std::endl;

    folly_concepts();
    basic_formatting();
    string_split();
    string_join();
    string_trim();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}