/**
 * @file views_join_with_example.cpp
 * @brief C++23 std::views::join_with 示例
 *
 * std::views::join_with 是 C++23 引入的连接视图。
 * 它将多个范围连接在一起，并在它们之间插入分隔符。
 *
 * 主要特点：
 * - 连接多个范围
 * - 在范围之间插入分隔符
 * - 适用于字符串连接和数据合并
 * - 支持惰性求值
 *
 * 编译命令：
 * g++ -std=c++23 -o views_join_with_example views_join_with_example.cpp
 */

#include <iostream>
#include <vector>
#include <string>
#include <ranges>
#include <algorithm>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::vector<std::vector<int>> data = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};

    // 使用分隔符连接
    auto joined = data | std::views::join_with(0);

    std::cout << "Joined with 0: ";
    for (int n : joined) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 2. 字符串连接 ==========

void string_join() {
    std::cout << "\n=== 字符串连接 ===" << std::endl;

    std::vector<std::string> words = {"Hello", "World", "C++23"};

    // 使用空格连接
    auto joined = words | std::views::join_with(' ');

    std::cout << "Joined: ";
    for (char c : joined) std::cout << c;
    std::cout << std::endl;

    // 使用逗号连接
    auto joined_comma = words | std::views::join_with(", ");

    std::cout << "Joined with comma: ";
    for (char c : joined_comma) std::cout << c;
    std::cout << std::endl;
}

// ========== 3. 实际应用：CSV 格式 ==========

void csv_format() {
    std::cout << "\n=== 实际应用：CSV 格式 ===" << std::endl;

    // CSV 行
    std::vector<std::vector<std::string>> rows = {
        {"Name", "Age", "City"},
        {"Alice", "25", "New York"},
        {"Bob", "30", "London"},
        {"Charlie", "35", "Paris"}
    };

    // 格式化为 CSV
    std::cout << "CSV output:" << std::endl;
    for (const auto& row : rows) {
        auto csv_row = row | std::views::join_with(',');
        for (char c : csv_row) std::cout << c;
        std::cout << std::endl;
    }
}

// ========== 4. 实际应用：SQL 查询 ==========

void sql_query() {
    std::cout << "\n=== 实际应用：SQL 查询 ===" << std::endl;

    // SQL 查询组件
    std::vector<std::string> select_fields = {"id", "name", "age"};
    std::vector<std::string> where_conditions = {"age > 18", "city = 'NY'"};

    // 构建 SELECT 子句
    auto select_clause = select_fields | std::views::join_with(", ");
    std::cout << "SELECT ";
    for (char c : select_clause) std::cout << c;
    std::cout << std::endl;

    // 构建 WHERE 子句
    auto where_clause = where_conditions | std::views::join_with(" AND ");
    std::cout << "WHERE ";
    for (char c : where_clause) std::cout << c;
    std::cout << std::endl;
}

// ========== 5. 实际应用：路径拼接 ==========

void path_join() {
    std::cout << "\n=== 实际应用：路径拼接 ===" << std::endl;

    std::vector<std::string> path_components = {"home", "user", "documents", "file.txt"};

    // 使用斜杠连接
    auto path = path_components | std::views::join_with('/');

    std::cout << "Path: ";
    for (char c : path) std::cout << c;
    std::cout << std::endl;
}

// ========== 6. 实际应用：URL 构建 ==========

void url_building() {
    std::cout << "\n=== 实际应用：URL 构建 ===" << std::endl;

    std::vector<std::string> url_parts = {"https://example.com", "api", "v1", "users"};

    // 使用斜杠连接
    auto url = url_parts | std::views::join_with('/');

    std::cout << "URL: ";
    for (char c : url) std::cout << c;
    std::cout << std::endl;

    // 查询参数
    std::vector<std::string> params = {"page=1", "limit=10", "sort=name"};

    auto query = params | std::views::join_with('&');

    std::cout << "Query: ?";
    for (char c : query) std::cout << c;
    std::cout << std::endl;
}

// ========== 7. 实际应用：日志格式化 ==========

void log_formatting() {
    std::cout << "\n=== 实际应用：日志格式化 ===" << std::endl;

    // 日志组件
    std::vector<std::string> log_parts = {"2024-01-01", "12:00:00", "INFO", "Application started"};

    // 使用竖线连接
    auto log_line = log_parts | std::views::join_with(" | ");

    std::cout << "Log: ";
    for (char c : log_line) std::cout << c;
    std::cout << std::endl;
}

// ========== 8. 实际应用：数据导出 ==========

void data_export() {
    std::cout << "\n=== 实际应用：数据导出 ===" << std::endl;

    // 数据记录
    std::vector<std::vector<std::string>> records = {
        {"1", "Alice", "25", "Engineer"},
        {"2", "Bob", "30", "Designer"},
        {"3", "Charlie", "35", "Manager"}
    };

    // 导出为 TSV (制表符分隔)
    std::cout << "TSV export:" << std::endl;
    for (const auto& record : records) {
        auto tsv_line = record | std::views::join_with('\t');
        for (char c : tsv_line) std::cout << c;
        std::cout << std::endl;
    }
}

// ========== 9. 实际应用：HTML 生成 ==========

void html_generation() {
    std::cout << "\n=== 实际应用：HTML 生成 ===" << std::endl;

    // HTML 列表项
    std::vector<std::string> items = {"Item 1", "Item 2", "Item 3"};

    // 生成 HTML 列表
    std::cout << "<ul>" << std::endl;
    for (const auto& item : items) {
        std::cout << "  <li>" << item << "</li>" << std::endl;
    }
    std::cout << "</ul>" << std::endl;

    // 使用逗号连接的列表
    auto list = items | std::views::join_with(", ");
    std::cout << "\nInline list: ";
    for (char c : list) std::cout << c;
    std::cout << std::endl;
}

// ========== 10. 实际应用：配置文件 ==========

void config_file() {
    std::cout << "\n=== 实际应用：配置文件 ===" << std::endl;

    // 配置项
    std::vector<std::pair<std::string, std::string>> config = {
        {"host", "localhost"},
        {"port", "8080"},
        {"debug", "true"}
    };

    // 生成配置文件格式
    std::cout << "Config file:" << std::endl;
    for (const auto& [key, value] : config) {
        std::vector<std::string> parts = {key, value};
        auto line = parts | std::views::join_with('=');
        for (char c : line) std::cout << c;
        std::cout << std::endl;
    }
}

// ========== 11. 实际应用：命令行参数 ==========

void command_line() {
    std::cout << "\n=== 实际应用：命令行参数 ===" << std::endl;

    // 命令行参数
    std::vector<std::string> args = {"program", "--input", "file.txt", "--output", "result.txt"};

    // 构建命令行
    auto command = args | std::views::join_with(' ');

    std::cout << "Command: ";
    for (char c : command) std::cout << c;
    std::cout << std::endl;
}

// ========== 12. 实际应用：数据聚合 ==========

void data_aggregation() {
    std::cout << "\n=== 实际应用：数据聚合 ===" << std::endl;

    // 多行数据
    std::vector<std::vector<int>> data = {
        {1, 2, 3},
        {4, 5, 6},
        {7, 8, 9}
    };

    // 聚合所有数据
    auto all_data = data | std::views::join_with(std::vector<int>{0});

    std::cout << "Aggregated data: ";
    for (int n : all_data) std::cout << n << " ";
    std::cout << std::endl;
}

int main() {
    std::cout << "C++23 std::views::join_with 示例\n" << std::endl;

    basic_usage();
    string_join();
    csv_format();
    sql_query();
    path_join();
    url_building();
    log_formatting();
    data_export();
    html_generation();
    config_file();
    command_line();
    data_aggregation();

    return 0;
}
