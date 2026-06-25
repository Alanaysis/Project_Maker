/**
 * @file string_example.cpp
 * @brief Abseil 字符串工具示例
 * @details 展示 Abseil 的字符串处理功能
 *          Abseil 是 Google 开源的 C++ 基础库
 */

#include <iostream>
#include <string>
#include <vector>
#include "absl/strings/str_cat.h"
#include "absl/strings/str_format.h"
#include "absl/strings/str_join.h"
#include "absl/strings/str_split.h"
#include "absl/strings/strip.h"
#include "absl/strings/ascii.h"

/**
 * @brief 字符串连接示例
 * @details 展示 absl::StrCat 的使用
 */
void string_concatenation() {
    std::cout << "=== 字符串连接 ===" << std::endl;

    // 使用 StrCat 连接
    std::string result = absl::StrCat("Hello, ", "World", "!");
    std::cout << result << std::endl;

    // 连接不同类型
    result = absl::StrCat("Name: ", "Alice", ", Age: ", 30);
    std::cout << result << std::endl;

    // 使用 StrAppend 追加
    std::string str = "Hello";
    absl::StrAppend(&str, ", ", "World", "!");
    std::cout << str << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 格式化字符串示例
 * @details 展示 absl::StrFormat 的使用
 */
void string_formatting() {
    std::cout << "=== 字符串格式化 ===" << std::endl;

    // 使用 StrFormat
    std::string result = absl::StrFormat("Hello, %s! You are %d years old.", "Alice", 30);
    std::cout << result << std::endl;

    // 格式化数字
    result = absl::StrFormat("Pi is approximately %.4f", 3.14159);
    std::cout << result << std::endl;

    // 格式化对齐
    result = absl::StrFormat("%-10s %10s", "Left", "Right");
    std::cout << result << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 字符串分割示例
 * @details 展示 absl::StrSplit 的使用
 */
void string_split() {
    std::cout << "=== 字符串分割 ===" << std::endl;

    // 按分隔符分割
    std::string str = "apple,banana,cherry";
    std::vector<std::string> parts = absl::StrSplit(str, ',');

    std::cout << "Split by comma:" << std::endl;
    for (const auto& part : parts) {
        std::cout << "  " << part << std::endl;
    }

    // 按多个分隔符分割
    str = "apple,banana;cherry.date";
    parts = absl::StrSplit(str, absl::ByAnyChar(",;."));

    std::cout << "Split by multiple delimiters:" << std::endl;
    for (const auto& part : parts) {
        std::cout << "  " << part << std::endl;
    }

    // 保留空字符串
    str = "a,,b,,c";
    parts = absl::StrSplit(str, ',', absl::SkipWhitespace());

    std::cout << "Split with SkipWhitespace:" << std::endl;
    for (const auto& part : parts) {
        std::cout << "  '" << part << "'" << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief 字符串连接示例
 * @details 展示 absl::StrJoin 的使用
 */
void string_join() {
    std::cout << "=== 字符串连接 ===" << std::endl;

    // 连接字符串向量
    std::vector<std::string> parts = {"apple", "banana", "cherry"};
    std::string joined = absl::StrJoin(parts, ", ");
    std::cout << "Joined: " << joined << std::endl;

    // 连接整数向量
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    joined = absl::StrJoin(numbers, " + ");
    std::cout << "Numbers: " << joined << std::endl;

    // 使用自定义连接器
    joined = absl::StrJoin(parts, " | ",
        [](std::string* out, const std::string& s) {
            absl::StrAppend(out, "[", s, "]");
        });
    std::cout << "Custom: " << joined << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 字符串修剪示例
 * @details 展示字符串修剪功能
 */
void string_strip() {
    std::cout << "=== 字符串修剪 ===" << std::endl;

    std::string str = "  Hello, World!  ";

    // 修剪两端
    std::string stripped = absl::StripWhitespace(str);
    std::cout << "Stripped: '" << stripped << "'" << std::endl;

    // 修剪左侧
    stripped = absl::StripLeadingWhitespace(str);
    std::cout << "Left stripped: '" << stripped << "'" << std::endl;

    // 修剪右侧
    stripped = absl::StripTrailingWhitespace(str);
    std::cout << "Right stripped: '" << stripped << "'" << std::endl;

    // 修剪特定字符
    str = "***Hello***";
    stripped = absl::StripPrefix(str, "***");
    std::cout << "Strip prefix: '" << stripped << "'" << std::endl;

    stripped = absl::StripSuffix(str, "***");
    std::cout << "Strip suffix: '" << stripped << "'" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief ASCII 操作示例
 * @details 展示 ASCII 字符操作
 */
void ascii_operations() {
    std::cout << "=== ASCII 操作 ===" << std::endl;

    std::string str = "Hello, World!";

    // 转换为大写
    std::cout << "Upper: " << absl::AsciiStrToUpper(str) << std::endl;

    // 转换为小写
    std::cout << "Lower: " << absl::AsciiStrToLower(str) << std::endl;

    // 原地转换
    std::string str2 = "Hello";
    absl::AsciiStrToLower(&str2);
    std::cout << "In-place lower: " << str2 << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Abseil 字符串工具示例 ===" << std::endl;
    std::cout << std::endl;

    string_concatenation();
    string_formatting();
    string_split();
    string_join();
    string_strip();
    ascii_operations();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}