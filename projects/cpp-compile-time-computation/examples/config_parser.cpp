// config_parser.cpp - 编译期配置解析示例
//
// 本文件展示编译期配置解析的用法，包括：
//   1. 基本配置定义
//   2. 配置验证
//   3. 配置访问
//
// 编译命令：
//   g++ -std=c++20 -I include examples/config_parser.cpp -o config_parser

#include <iostream>
#include "compile_time/config.hpp"

using namespace compile_time::config;

// ============================================================================
// 第一部分：基本配置定义
// ============================================================================

// 编译期创建服务器配置
constexpr server_config default_config = make_default_server_config();

// 自定义配置
constexpr server_config custom_config = {
    9090,        // port
    5000,        // max_connections
    60,          // timeout
    true,        // debug
    "0.0.0.0"   // host
};

// ============================================================================
// 第二部分：配置验证
// ============================================================================

// 验证默认配置
constexpr bool default_valid = is_valid_config(default_config);

// 验证自定义配置
constexpr bool custom_valid = is_valid_config(custom_config);

// 验证无效配置
constexpr server_config invalid_config = {
    -1,          // port (invalid)
    1000,        // max_connections
    30,          // timeout
    false,       // debug
    "localhost"  // host
};

constexpr bool invalid_valid = is_valid_config(invalid_config);

// ============================================================================
// 第三部分：配置访问
// ============================================================================

// 访问配置值
constexpr int default_port = default_config.port;
constexpr int default_max_conn = default_config.max_connections;
constexpr int default_timeout = default_config.timeout;
constexpr bool default_debug = default_config.debug;

// ============================================================================
// 第四部分：编译期配置表
// ============================================================================

// 编译期配置表
constexpr simple_config<10> create_config_table() {
    simple_config<10> cfg;
    add_int(cfg, "port", 8080);
    add_int(cfg, "max_connections", 1000);
    add_int(cfg, "timeout", 30);
    add_bool(cfg, "debug", false);
    return cfg;
}

constexpr auto config_table = create_config_table();

// 从配置表获取值
constexpr int table_port = config_table.get_int("port", 0);
constexpr int table_max_conn = config_table.get_int("max_connections", 0);
constexpr int table_timeout = config_table.get_int("timeout", 0);
constexpr bool table_debug = config_table.get_bool("debug", false);

// ============================================================================
// 第五部分：编译期断言验证
// ============================================================================

// 配置定义
static_assert(default_port == 8080);
static_assert(default_max_conn == 1000);
static_assert(default_timeout == 30);
static_assert(default_debug == false);

// 配置验证
static_assert(default_valid == true);
static_assert(custom_valid == true);
static_assert(invalid_valid == false);

// 配置表
static_assert(table_port == 8080);
static_assert(table_max_conn == 1000);
static_assert(table_timeout == 30);
static_assert(table_debug == false);
static_assert(config_table.contains("port") == true);
static_assert(config_table.contains("unknown") == false);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期配置解析示例 ===" << std::endl;
    std::cout << std::endl;

    // 默认配置
    std::cout << "1. 默认配置:" << std::endl;
    std::cout << "   port = " << default_config.port << std::endl;
    std::cout << "   max_connections = " << default_config.max_connections << std::endl;
    std::cout << "   timeout = " << default_config.timeout << std::endl;
    std::cout << "   debug = " << (default_config.debug ? "true" : "false") << std::endl;
    std::cout << "   host = " << default_config.host << std::endl;
    std::cout << std::endl;

    // 自定义配置
    std::cout << "2. 自定义配置:" << std::endl;
    std::cout << "   port = " << custom_config.port << std::endl;
    std::cout << "   max_connections = " << custom_config.max_connections << std::endl;
    std::cout << "   timeout = " << custom_config.timeout << std::endl;
    std::cout << "   debug = " << (custom_config.debug ? "true" : "false") << std::endl;
    std::cout << "   host = " << custom_config.host << std::endl;
    std::cout << std::endl;

    // 配置验证
    std::cout << "3. 配置验证:" << std::endl;
    std::cout << "   默认配置有效: " << (default_valid ? "是" : "否") << std::endl;
    std::cout << "   自定义配置有效: " << (custom_valid ? "是" : "否") << std::endl;
    std::cout << "   无效配置有效: " << (invalid_valid ? "是" : "否") << std::endl;
    std::cout << std::endl;

    // 配置表
    std::cout << "4. 配置表:" << std::endl;
    std::cout << "   port = " << config_table.get_int("port", 0) << std::endl;
    std::cout << "   max_connections = " << config_table.get_int("max_connections", 0) << std::endl;
    std::cout << "   timeout = " << config_table.get_int("timeout", 0) << std::endl;
    std::cout << "   debug = " << (config_table.get_bool("debug", false) ? "true" : "false") << std::endl;
    std::cout << "   contains(\"port\"): " << (config_table.contains("port") ? "是" : "否") << std::endl;
    std::cout << "   contains(\"unknown\"): " << (config_table.contains("unknown") ? "是" : "否") << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
