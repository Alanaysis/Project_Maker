/**
 * @file expected_example.cpp
 * @brief C++23 std::expected 示例
 *
 * std::expected 是 C++23 引入的类型安全错误处理工具。
 * 它可以存储一个期望的值或一个错误值，避免使用异常或错误码。
 *
 * 主要特点：
 * - 类型安全：编译时检查错误处理
 * - 性能：避免异常开销
 * - 表达力：明确的函数契约
 * - 组合性：支持链式操作
 *
 * 编译命令：
 * g++ -std=c++23 -o expected_example expected_example.cpp
 */

#include <iostream>
#include <expected>
#include <string>
#include <vector>
#include <optional>
#include <charconv>
#include <system_error>

// ========== 1. 基本用法 ==========

// 使用 std::expected 表示可能失败的操作
std::expected<int, std::string> divide(int a, int b) {
    if (b == 0) {
        return std::unexpected("Division by zero");
    }
    return a / b;
}

// 解析字符串为整数
std::expected<int, std::string> parse_int(const std::string& str) {
    try {
        return std::stoi(str);
    } catch (const std::exception& e) {
        return std::unexpected(e.what());
    }
}

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // 成功情况
    auto result1 = divide(10, 2);
    if (result1) {
        std::cout << "10 / 2 = " << *result1 << std::endl;
    }

    // 错误情况
    auto result2 = divide(10, 0);
    if (!result2) {
        std::cout << "Error: " << result2.error() << std::endl;
    }

    // 使用 value() 方法
    auto result3 = divide(20, 4);
    std::cout << "20 / 4 = " << result3.value() << std::endl;

    // 使用 error() 方法
    auto result4 = divide(20, 0);
    std::cout << "Error: " << result4.error() << std::endl;
}

// ========== 2. 链式操作 ==========

// 使用 and_then 进行链式操作
std::expected<int, std::string> chain_operations() {
    return divide(100, 2)
        .and_then([](int val) {
            return divide(val, 5);
        })
        .and_then([](int val) {
            return divide(val, 2);
        });
}

// 使用 transform 转换值
std::expected<std::string, std::string> transform_example() {
    return divide(100, 4)
        .transform([](int val) {
            return "Result: " + std::to_string(val);
        });
}

// 使用 or_else 处理错误
std::expected<int, std::string> or_else_example() {
    return divide(100, 0)
        .or_else([](const std::string& error) -> std::expected<int, std::string> {
            std::cout << "Handling error: " << error << std::endl;
            return 0;  // 返回默认值
        });
}

void chaining_example() {
    std::cout << "\n=== 链式操作 ===" << std::endl;

    // 链式除法
    auto result1 = chain_operations();
    if (result1) {
        std::cout << "100 / 2 / 5 / 2 = " << *result1 << std::endl;
    }

    // 转换结果
    auto result2 = transform_example();
    if (result2) {
        std::cout << *result2 << std::endl;
    }

    // 错误处理
    auto result3 = or_else_example();
    if (result3) {
        std::cout << "Final result: " << *result3 << std::endl;
    }
}

// ========== 3. 与 std::optional 对比 ==========

// std::optional 只能表示有值或无值，不能携带错误信息
std::optional<int> divide_optional(int a, int b) {
    if (b == 0) {
        return std::nullopt;  // 丢失了错误信息
    }
    return a / b;
}

// std::expected 可以携带错误信息
std::expected<int, std::string> divide_expected(int a, int b) {
    if (b == 0) {
        return std::unexpected("Division by zero: " + std::to_string(a) + " / " + std::to_string(b));
    }
    return a / b;
}

void comparison_example() {
    std::cout << "\n=== 与 std::optional 对比 ===" << std::endl;

    // std::optional 的问题
    auto result1 = divide_optional(10, 0);
    if (!result1) {
        std::cout << "optional: No value (error information lost)" << std::endl;
    }

    // std::expected 的优势
    auto result2 = divide_expected(10, 0);
    if (!result2) {
        std::cout << "expected: " << result2.error() << std::endl;
    }
}

// ========== 4. 实际应用：配置文件解析 ==========

struct Config {
    std::string host;
    int port;
    std::string username;
};

std::expected<Config, std::string> parse_config(const std::string& config_str) {
    Config config;

    // 简单的配置解析示例
    if (config_str.empty()) {
        return std::unexpected("Empty config string");
    }

    // 解析 host
    auto host_pos = config_str.find("host=");
    if (host_pos == std::string::npos) {
        return std::unexpected("Missing host in config");
    }
    auto host_end = config_str.find(';', host_pos);
    config.host = config_str.substr(host_pos + 5, host_end - host_pos - 5);

    // 解析 port
    auto port_pos = config_str.find("port=");
    if (port_pos == std::string::npos) {
        return std::unexpected("Missing port in config");
    }
    auto port_end = config_str.find(';', port_pos);
    auto port_str = config_str.substr(port_pos + 5, port_end - port_pos - 5);

    auto port_result = parse_int(port_str);
    if (!port_result) {
        return std::unexpected("Invalid port: " + port_result.error());
    }
    config.port = *port_result;

    if (config.port < 1 || config.port > 65535) {
        return std::unexpected("Port out of range: " + std::to_string(config.port));
    }

    // 解析 username
    auto user_pos = config_str.find("user=");
    if (user_pos == std::string::npos) {
        return std::unexpected("Missing username in config");
    }
    auto user_end = config_str.find(';', user_pos);
    config.username = config_str.substr(user_pos + 5, user_end - user_pos - 5);

    return config;
}

void practical_example() {
    std::cout << "\n=== 实际应用：配置解析 ===" << std::endl;

    // 成功的配置
    std::string good_config = "host=localhost;port=8080;user=admin";
    auto result1 = parse_config(good_config);
    if (result1) {
        std::cout << "Config loaded: " << result1->host << ":" << result1->port
                  << " user=" << result1->username << std::endl;
    }

    // 错误的配置
    std::string bad_config = "host=localhost;port=abc;user=admin";
    auto result2 = parse_config(bad_config);
    if (!result2) {
        std::cout << "Config error: " << result2.error() << std::endl;
    }

    // 缺少字段
    std::string incomplete_config = "host=localhost";
    auto result3 = parse_config(incomplete_config);
    if (!result3) {
        std::cout << "Config error: " << result3.error() << std::endl;
    }
}

// ========== 5. expected<void> 用法 ==========

// 当只需要表示成功或失败，不需要返回值时
std::expected<void, std::string> validate_age(int age) {
    if (age < 0) {
        return std::unexpected("Age cannot be negative");
    }
    if (age > 150) {
        return std::unexpected("Age is too high");
    }
    return {};  // 成功，无返回值
}

void void_expected_example() {
    std::cout << "\n=== expected<void> 用法 ===" << std::endl;

    auto result1 = validate_age(25);
    if (result1) {
        std::cout << "Age 25 is valid" << std::endl;
    }

    auto result2 = validate_age(-5);
    if (!result2) {
        std::cout << "Validation error: " << result2.error() << std::endl;
    }

    auto result3 = validate_age(200);
    if (!result3) {
        std::cout << "Validation error: " << result3.error() << std::endl;
    }
}

// ========== 6. 与 std::expected 结合的函数式编程 ==========

// 使用 monadic 操作组合多个可能失败的操作
std::expected<double, std::string> calculate_area(double radius) {
    if (radius < 0) {
        return std::unexpected("Radius cannot be negative");
    }
    return 3.14159 * radius * radius;
}

std::expected<double, std::string> calculate_circumference(double radius) {
    if (radius < 0) {
        return std::unexpected("Radius cannot be negative");
    }
    return 2 * 3.14159 * radius;
}

void functional_example() {
    std::cout << "\n=== 函数式编程 ===" << std::endl;

    double radius = 5.0;

    // 组合操作
    auto area_result = calculate_area(radius);
    auto circumference_result = calculate_circumference(radius);

    if (area_result && circumference_result) {
        std::cout << "Circle with radius " << radius << ":" << std::endl;
        std::cout << "  Area: " << *area_result << std::endl;
        std::cout << "  Circumference: " << *circumference_result << std::endl;
    }

    // 使用 transform 组合
    auto combined = calculate_area(radius)
        .transform([&](double area) {
            return "Area: " + std::to_string(area);
        });

    if (combined) {
        std::cout << *combined << std::endl;
    }
}

int main() {
    std::cout << "C++23 std::expected 示例\n" << std::endl;

    basic_usage();
    chaining_example();
    comparison_example();
    practical_example();
    void_expected_example();
    functional_example();

    return 0;
}
