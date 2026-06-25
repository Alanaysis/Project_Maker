/**
 * @file optional_example.cpp
 * @brief C++17 std::optional 示例
 *
 * std::optional 是一个可以包含值或不包含值的容器。
 * 它用于表示可能缺失的值，替代使用特殊值（如 -1、nullptr）表示"无值"的情况。
 *
 * 主要优势：
 * 1. 类型安全 - 编译期强制处理可能缺失的值
 * 2. 语义清晰 - 明确表达"可能有值"的意图
 * 3. 避免特殊值 - 不需要使用哨兵值
 */

#include <iostream>
#include <optional>
#include <string>
#include <vector>
#include <map>
#include <functional>

/**
 * @brief 使用 optional 作为函数返回值
 *
 * 查找函数返回 optional，避免返回特殊值
 */
std::optional<int> find_value(const std::vector<int>& vec, int target) {
    for (size_t i = 0; i < vec.size(); ++i) {
        if (vec[i] == target) {
            return static_cast<int>(i);  // 返回找到的索引
        }
    }
    return std::nullopt;  // 未找到，返回空 optional
}

/**
 * @brief 使用 optional 表示可能失败的操作
 */
std::optional<double> safe_divide(double a, double b) {
    if (b == 0.0) {
        return std::nullopt;  // 除零错误
    }
    return a / b;
}

/**
 * @brief 使用 optional 进行配置解析
 */
struct Config {
    std::optional<std::string> hostname;
    std::optional<int> port;
    std::optional<bool> use_ssl;
};

/**
 * @brief 从 map 安全获取配置值
 */
template <typename T>
std::optional<T> get_config_value(const std::map<std::string, std::string>& config,
                                   const std::string& key) {
    auto it = config.find(key);
    if (it != config.end()) {
        try {
            if constexpr (std::is_same_v<T, int>) {
                return std::stoi(it->second);
            } else if constexpr (std::is_same_v<T, bool>) {
                return it->second == "true" || it->second == "1";
            } else {
                return it->second;
            }
        } catch (...) {
            return std::nullopt;
        }
    }
    return std::nullopt;
}

/**
 * @brief optional 链式操作示例
 */
std::optional<std::string> get_user_name(int user_id) {
    // 模拟数据库查询
    std::map<int, std::string> users = {
        {1, "Alice"},
        {2, "Bob"},
        {3, "Charlie"}
    };

    auto it = users.find(user_id);
    if (it != users.end()) {
        return it->second;
    }
    return std::nullopt;
}

std::optional<std::string> get_user_email(const std::string& username) {
    // 模拟数据库查询
    std::map<std::string, std::string> emails = {
        {"Alice", "alice@example.com"},
        {"Bob", "bob@example.com"}
    };

    auto it = emails.find(username);
    if (it != emails.end()) {
        return it->second;
    }
    return std::nullopt;
}

/**
 * @brief optional 的 monadic 操作（C++23 特性，这里模拟）
 */
template <typename T, typename Func>
auto and_then(const std::optional<T>& opt, Func&& func)
    -> decltype(func(*opt)) {
    if (opt.has_value()) {
        return func(*opt);
    }
    return {};
}

/**
 * @brief 主示例函数
 */
void optional_example() {
    std::cout << "=== std::optional ===" << std::endl;

    // 1. 创建 optional
    std::cout << "\n[创建 optional]" << std::endl;

    // 默认构造（空 optional）
    std::optional<int> opt1;
    std::cout << "opt1 has value: " << opt1.has_value() << std::endl;

    // 使用值构造
    std::optional<int> opt2(42);
    std::cout << "opt2 has value: " << opt2.has_value()
              << ", value: " << *opt2 << std::endl;

    // 使用 std::nullopt 构造空 optional
    std::optional<int> opt3 = std::nullopt;
    std::cout << "opt3 has value: " << opt3.has_value() << std::endl;

    // 使用 std::make_optional
    auto opt4 = std::make_optional<std::string>("Hello");
    std::cout << "opt4 has value: " << opt4.has_value()
              << ", value: " << *opt4 << std::endl;

    // 2. 访问值
    std::cout << "\n[访问值]" << std::endl;

    std::optional<int> opt(42);

    // 使用 operator* 访问
    std::cout << "value (operator*): " << *opt << std::endl;

    // 使用 value() 访问
    std::cout << "value (value()): " << opt.value() << std::endl;

    // 使用 operator-> 访问（用于对象）
    std::optional<std::string> opt_str("Hello World");
    std::cout << "length (operator->): " << opt_str->length() << std::endl;

    // 3. 状态检查
    std::cout << "\n[状态检查]" << std::endl;

    std::optional<int> empty_opt;
    std::optional<int> valid_opt(42);

    std::cout << "empty_opt has value: " << empty_opt.has_value() << std::endl;
    std::cout << "valid_opt has value: " << valid_opt.has_value() << std::endl;

    // 使用 operator bool
    if (valid_opt) {
        std::cout << "valid_opt is truthy" << std::endl;
    }

    // 4. 默认值处理
    std::cout << "\n[默认值处理]" << std::endl;

    std::optional<int> no_value;
    int default_value = no_value.value_or(100);
    std::cout << "default value: " << default_value << std::endl;

    std::optional<int> has_value(42);
    int actual_value = has_value.value_or(100);
    std::cout << "actual value: " << actual_value << std::endl;

    // 5. 修改值
    std::cout << "\n[修改值]" << std::endl;

    std::optional<int> modifiable(10);
    std::cout << "before: " << *modifiable << std::endl;

    // 赋新值
    modifiable = 20;
    std::cout << "after assignment: " << *modifiable << std::endl;

    // 重置为空
    modifiable.reset();
    std::cout << "after reset: " << modifiable.has_value() << std::endl;

    // 使用 emplace 构造新值
    modifiable.emplace(30);
    std::cout << "after emplace: " << *modifiable << std::endl;

    // 6. 函数返回值
    std::cout << "\n[函数返回值]" << std::endl;

    std::vector<int> numbers = {1, 2, 3, 4, 5};

    auto result1 = find_value(numbers, 3);
    if (result1) {
        std::cout << "Found 3 at index: " << *result1 << std::endl;
    }

    auto result2 = find_value(numbers, 6);
    if (!result2) {
        std::cout << "6 not found" << std::endl;
    }

    // 7. 安全操作
    std::cout << "\n[安全操作]" << std::endl;

    auto div1 = safe_divide(10.0, 3.0);
    if (div1) {
        std::cout << "10 / 3 = " << *div1 << std::endl;
    }

    auto div2 = safe_divide(10.0, 0.0);
    if (!div2) {
        std::cout << "Division by zero failed" << std::endl;
    }

    // 8. 配置解析
    std::cout << "\n[配置解析]" << std::endl;

    std::map<std::string, std::string> config = {
        {"hostname", "localhost"},
        {"port", "8080"}
    };

    Config app_config;
    app_config.hostname = get_config_value<std::string>(config, "hostname");
    app_config.port = get_config_value<int>(config, "port");
    app_config.use_ssl = get_config_value<bool>(config, "use_ssl");

    std::cout << "hostname: " << app_config.hostname.value_or("unknown") << std::endl;
    std::cout << "port: " << app_config.port.value_or(80) << std::endl;
    std::cout << "use_ssl: " << (app_config.use_ssl.value_or(false) ? "true" : "false") << std::endl;

    // 9. 链式操作
    std::cout << "\n[链式操作]" << std::endl;

    // 获取用户的邮箱
    auto email = and_then(get_user_name(1), get_user_email);
    if (email) {
        std::cout << "User 1 email: " << *email << std::endl;
    }

    auto email2 = and_then(get_user_name(3), get_user_email);
    if (!email2) {
        std::cout << "User 3 email not found" << std::endl;
    }

    // 10. 与 STL 算法结合
    std::cout << "\n[与 STL 算法结合]" << std::endl;

    std::vector<std::optional<int>> optionals = {1, std::nullopt, 3, std::nullopt, 5};

    // 统计有值的 optional 数量
    int count = 0;
    for (const auto& opt : optionals) {
        if (opt) {
            ++count;
        }
    }
    std::cout << "Number of values: " << count << std::endl;

    // 提取所有有值的 optional
    std::vector<int> values;
    for (const auto& opt : optionals) {
        if (opt) {
            values.push_back(*opt);
        }
    }

    std::cout << "Values: ";
    for (int v : values) {
        std::cout << v << " ";
    }
    std::cout << std::endl;

    // 11. 比较操作
    std::cout << "\n[比较操作]" << std::endl;

    std::optional<int> a(1);
    std::optional<int> b(2);
    std::optional<int> c;
    std::optional<int> d(1);

    std::cout << "a < b: " << (a < b) << std::endl;
    std::cout << "a == d: " << (a == d) << std::endl;
    std::cout << "c == std::nullopt: " << (c == std::nullopt) << std::endl;
    std::cout << "a == 1: " << (a == 1) << std::endl;

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    optional_example();
    return 0;
}
#endif
