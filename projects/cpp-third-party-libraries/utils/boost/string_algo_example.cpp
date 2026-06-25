/**
 * @file string_algo_example.cpp
 * @brief Boost 字符串算法示例
 * @details 展示 Boost 字符串算法库的使用
 *          提供丰富的字符串处理功能
 */

#include <iostream>
#include <string>
#include <vector>
#include <boost/algorithm/string.hpp>

/**
 * @brief 字符串转换示例
 * @details 展示字符串大小写转换
 */
void string_conversion() {
    std::cout << "=== 字符串转换 ===" << std::endl;

    std::string str = "Hello, World!";

    // 转换为大写
    std::cout << "Upper: " << boost::to_upper_copy(str) << std::endl;

    // 转换为小写
    std::cout << "Lower: " << boost::to_lower_copy(str) << std::endl;

    // 原地转换
    std::string str2 = "Hello";
    boost::to_upper(str2);
    std::cout << "In-place upper: " << str2 << std::endl;

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
    std::cout << "Trimmed: '" << boost::trim_copy(str) << "'" << std::endl;

    // 修剪左侧
    std::cout << "Left trimmed: '" << boost::trim_left_copy(str) << "'" << std::endl;

    // 修剪右侧
    std::cout << "Right trimmed: '" << boost::trim_right_copy(str) << "'" << std::endl;

    // 原地修剪
    boost::trim(str);
    std::cout << "In-place trimmed: '" << str << "'" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 字符串查找和替换示例
 * @details 展示字符串查找和替换功能
 */
void string_find_replace() {
    std::cout << "=== 查找和替换 ===" << std::endl;

    std::string str = "Hello, World! Hello, C++!";

    // 替换所有
    std::string replaced = boost::replace_all_copy(str, "Hello", "Hi");
    std::cout << "Replaced: " << replaced << std::endl;

    // 替换第一个
    replaced = boost::replace_first_copy(str, "Hello", "Hi");
    std::cout << "Replace first: " << replaced << std::endl;

    // 替换最后一个
    replaced = boost::replace_last_copy(str, "Hello", "Hi");
    std::cout << "Replace last: " << replaced << std::endl;

    // 查找
    bool found = boost::contains(str, "World");
    std::cout << "Contains 'World': " << (found ? "Yes" : "No") << std::endl;

    // 开头检查
    bool starts = boost::starts_with(str, "Hello");
    std::cout << "Starts with 'Hello': " << (starts ? "Yes" : "No") << std::endl;

    // 结尾检查
    bool ends = boost::ends_with(str, "C++!");
    std::cout << "Ends with 'C++!': " << (ends ? "Yes" : "No") << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 字符串分割示例
 * @details 展示字符串分割功能
 */
void string_split() {
    std::cout << "=== 字符串分割 ===" << std::endl;

    std::string str = "apple,banana,cherry,date";

    // 按逗号分割
    std::vector<std::string> parts;
    boost::split(parts, str, boost::is_any_of(","));

    std::cout << "Split by comma:" << std::endl;
    for (const auto& part : parts) {
        std::cout << "  " << part << std::endl;
    }

    // 按多个分隔符分割
    str = "apple,banana;cherry.date";
    boost::split(parts, str, boost::is_any_of(",;."));

    std::cout << "Split by multiple delimiters:" << std::endl;
    for (const auto& part : parts) {
        std::cout << "  " << part << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief 字符串连接示例
 * @details 展示字符串连接功能
 */
void string_join() {
    std::cout << "=== 字符串连接 ===" << std::endl;

    std::vector<std::string> parts = {"apple", "banana", "cherry", "date"};

    // 连接
    std::string joined = boost::join(parts, ", ");
    std::cout << "Joined: " << joined << std::endl;

    // 使用自定义连接符
    joined = boost::join(parts, " | ");
    std::cout << "Joined with '|': " << joined << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示字符串算法在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：处理 CSV 数据
    std::string csv_line = "  Alice , 25 , New York  ";

    // 修剪和分割
    boost::trim(csv_line);
    std::vector<std::string> fields;
    boost::split(fields, csv_line, boost::is_any_of(","));

    // 修剪每个字段
    for (auto& field : fields) {
        boost::trim(field);
    }

    std::cout << "Parsed CSV:" << std::endl;
    for (size_t i = 0; i < fields.size(); ++i) {
        std::cout << "  Field " << i << ": " << fields[i] << std::endl;
    }

    // 场景：验证邮箱格式
    std::string email = "user@example.com";
    bool is_valid = boost::contains(email, "@") && boost::contains(email, ".");
    std::cout << "\nEmail '" << email << "' is "
              << (is_valid ? "valid" : "invalid") << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Boost 字符串算法示例 ===" << std::endl;
    std::cout << std::endl;

    string_conversion();
    string_trim();
    string_find_replace();
    string_split();
    string_join();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}