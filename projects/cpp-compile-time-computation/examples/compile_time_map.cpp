// compile_time_map.cpp - 编译期映射示例
//
// 本文件展示编译期映射的用法，包括：
//   1. 基本构造和访问
//   2. 查找和包含检查
//   3. 键值操作
//   4. 实际应用示例
//
// 编译命令：
//   g++ -std=c++20 -I include examples/compile_time_map.cpp -o compile_time_map

#include <iostream>
#include <string_view>
#include "compile_time/map.hpp"

using compile_time::compile_time_map;
using compile_time::pair;
using compile_time::make_map;

// ============================================================================
// 第一部分：基本构造和访问
// ============================================================================

// 从数组构造
constexpr pair<int, const char*> entries[] = {
    {1, "one"},
    {2, "two"},
    {3, "three"},
    {4, "four"},
    {5, "five"}
};

constexpr auto number_map = make_map(entries);

// 访问元素
constexpr const char* value1 = number_map.at(1);  // "one"
constexpr const char* value3 = number_map.at(3);  // "three"

// 容量
constexpr std::size_t map_size = number_map.size();  // 5
constexpr bool is_empty = number_map.empty();        // false

// ============================================================================
// 第二部分：查找和包含检查
// ============================================================================

// 查找
constexpr bool has_3 = number_map.contains(3);   // true
constexpr bool has_10 = number_map.contains(10);  // false

// 安全访问
constexpr auto opt_value = number_map.try_at(2);   // optional("two")
constexpr auto opt_missing = number_map.try_at(10); // nullopt

// ============================================================================
// 第三部分：键值操作
// ============================================================================

// 获取所有键
constexpr auto keys = number_map.keys();

// 获取所有值
constexpr auto values = number_map.values();

// 映射（转换值）
constexpr auto upper_map = number_map.map_values([](const char* s) {
    // 简化：返回原字符串
    return s;
});

// ============================================================================
// 第四部分：实际应用示例
// ============================================================================

// HTTP 状态码映射
constexpr pair<int, const char*> http_status_entries[] = {
    {200, "OK"},
    {301, "Moved Permanently"},
    {302, "Found"},
    {400, "Bad Request"},
    {401, "Unauthorized"},
    {403, "Forbidden"},
    {404, "Not Found"},
    {500, "Internal Server Error"},
    {502, "Bad Gateway"},
    {503, "Service Unavailable"}
};

constexpr auto http_status_map = make_map(http_status_entries);

// 配置映射
struct ConfigEntry {
    const char* key;
    int value;
};

constexpr pair<const char*, int> config_entries[] = {
    {"port", 8080},
    {"max_connections", 1000},
    {"timeout", 30},
    {"buffer_size", 4096}
};

constexpr auto config_map = make_map(config_entries);

// ============================================================================
// 第五部分：编译期断言验证
// ============================================================================

// 基本构造和访问
static_assert(value1[0] == 'o');
static_assert(value3[0] == 't');
static_assert(map_size == 5);
static_assert(is_empty == false);

// 查找
static_assert(has_3 == true);
static_assert(has_10 == false);

// HTTP 状态码
static_assert(http_status_map.at(200)[0] == 'O');
static_assert(http_status_map.at(404)[0] == 'N');
static_assert(http_status_map.contains(200) == true);
static_assert(http_status_map.contains(999) == false);

// 配置映射
static_assert(config_map.at("port") == 8080);
static_assert(config_map.at("max_connections") == 1000);
static_assert(config_map.at("timeout") == 30);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期映射示例 ===" << std::endl;
    std::cout << std::endl;

    // 基本构造和访问
    std::cout << "1. 基本构造和访问:" << std::endl;
    std::cout << "   number_map.at(1) = " << number_map.at(1) << std::endl;
    std::cout << "   number_map.at(3) = " << number_map.at(3) << std::endl;
    std::cout << "   number_map.size() = " << number_map.size() << std::endl;
    std::cout << std::endl;

    // 查找
    std::cout << "2. 查找和包含检查:" << std::endl;
    std::cout << "   contains(3): " << (has_3 ? "true" : "false") << std::endl;
    std::cout << "   contains(10): " << (has_10 ? "true" : "false") << std::endl;
    std::cout << "   try_at(2).has_value(): " << (opt_value.has_value() ? "true" : "false") << std::endl;
    std::cout << "   try_at(10).has_value(): " << (opt_missing.has_value() ? "true" : "false") << std::endl;
    std::cout << std::endl;

    // 键值操作
    std::cout << "3. 键值操作:" << std::endl;
    std::cout << "   keys = [";
    for (std::size_t i = 0; i < keys.size(); ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << keys[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // HTTP 状态码
    std::cout << "4. HTTP 状态码映射:" << std::endl;
    std::cout << "   200: " << http_status_map.at(200) << std::endl;
    std::cout << "   404: " << http_status_map.at(404) << std::endl;
    std::cout << "   500: " << http_status_map.at(500) << std::endl;
    std::cout << std::endl;

    // 配置映射
    std::cout << "5. 配置映射:" << std::endl;
    std::cout << "   port = " << config_map.at("port") << std::endl;
    std::cout << "   max_connections = " << config_map.at("max_connections") << std::endl;
    std::cout << "   timeout = " << config_map.at("timeout") << std::endl;
    std::cout << "   buffer_size = " << config_map.at("buffer_size") << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
