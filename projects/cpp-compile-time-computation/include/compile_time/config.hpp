#pragma once
// config.hpp - 编译期配置解析
//
// 简化的编译期配置解析器，演示编译期字符串解析的概念。
// 使用硬编码的键值对避免 constexpr 指针问题。

#include <cstddef>
#include <optional>
#include "fixed_string.hpp"

namespace compile_time {
namespace config {

// config_entry: 配置项
struct config_entry {
    const char* key;
    int int_value;
    bool bool_value;
    char str_value[32];
    enum { INT, BOOL, STR } type;
};

// simple_config: 简化的编译期配置
template<std::size_t N>
struct simple_config {
    config_entry entries[N];
    std::size_t count;

    constexpr simple_config() : count(0) {}

    constexpr int get_int(const char* key, int default_value) const {
        for (std::size_t i = 0; i < count; ++i) {
            if (entries[i].type == config_entry::INT && str_equal(entries[i].key, key)) {
                return entries[i].int_value;
            }
        }
        return default_value;
    }

    constexpr bool get_bool(const char* key, bool default_value) const {
        for (std::size_t i = 0; i < count; ++i) {
            if (entries[i].type == config_entry::BOOL && str_equal(entries[i].key, key)) {
                return entries[i].bool_value;
            }
        }
        return default_value;
    }

    constexpr bool contains(const char* key) const {
        for (std::size_t i = 0; i < count; ++i) {
            if (str_equal(entries[i].key, key)) return true;
        }
        return false;
    }

private:
    static constexpr bool str_equal(const char* a, const char* b) {
        while (*a && *b) {
            if (*a != *b) return false;
            ++a;
            ++b;
        }
        return *a == *b;
    }
};

// 辅助函数：创建配置
template<std::size_t N>
constexpr void add_int(simple_config<N>& cfg, const char* key, int value) {
    cfg.entries[cfg.count].key = key;
    cfg.entries[cfg.count].int_value = value;
    cfg.entries[cfg.count].type = config_entry::INT;
    ++cfg.count;
}

template<std::size_t N>
constexpr void add_bool(simple_config<N>& cfg, const char* key, bool value) {
    cfg.entries[cfg.count].key = key;
    cfg.entries[cfg.count].bool_value = value;
    cfg.entries[cfg.count].type = config_entry::BOOL;
    ++cfg.count;
}

// 示例：服务器配置
struct server_config {
    int port;
    int max_connections;
    int timeout;
    bool debug;
    const char* host;
};

// 编译期创建默认服务器配置
constexpr server_config make_default_server_config() {
    return server_config{
        8080,      // port
        1000,      // max_connections
        30,        // timeout
        false,     // debug
        "localhost" // host
    };
}

// 编译期验证配置
constexpr bool is_valid_port(int port) {
    return port > 0 && port < 65536;
}

constexpr bool is_valid_timeout(int timeout) {
    return timeout > 0 && timeout < 300;
}

constexpr bool is_valid_max_connections(int max_conn) {
    return max_conn > 0 && max_conn < 100000;
}

constexpr bool is_valid_config(const server_config& cfg) {
    return is_valid_port(cfg.port) &&
           is_valid_timeout(cfg.timeout) &&
           is_valid_max_connections(cfg.max_connections);
}

} // namespace config
} // namespace compile_time
