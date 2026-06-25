/**
 * @file apply_example.cpp
 * @brief C++17 std::apply 示例
 *
 * std::apply 用于将元组展开为函数调用的参数。
 * 它简化了元组与函数之间的交互。
 *
 * 主要优势：
 * 1. 简化元组展开 - 无需手动 get
 * 2. 通用性 - 适用于任何可调用对象
 * 3. 类型安全 - 编译期类型检查
 */

#include <iostream>
#include <tuple>
#include <string>
#include <functional>
#include <utility>
#include <vector>
#include <numeric>
#include <map>

// 1. 基本 std::apply 使用
void basic_apply_example() {
    std::cout << "\n[基本 std::apply 使用]" << std::endl;

    // 定义函数
    auto add = [](int a, int b, int c) {
        return a + b + c;
    };

    // 创建元组
    auto args = std::make_tuple(1, 2, 3);

    // 使用 std::apply 调用函数
    int result = std::apply(add, args);
    std::cout << "add(1, 2, 3) = " << result << std::endl;

    // 使用 std::apply 调用普通函数
    auto print = [](const std::string& name, int age) {
        std::cout << "Name: " << name << ", Age: " << age << std::endl;
    };

    auto person = std::make_tuple("Alice", 30);
    std::apply(print, person);
}

// 2. 与 std::tuple 结合
void tuple_example() {
    std::cout << "\n[与 std::tuple 结合]" << std::endl;

    // 创建复杂元组
    auto config = std::make_tuple(
        std::string("localhost"),
        8080,
        true,
        30.5
    );

    // 使用 std::apply 处理元组
    auto process_config = [](const std::string& host, int port, bool ssl, double timeout) {
        std::cout << "Host: " << host << std::endl;
        std::cout << "Port: " << port << std::endl;
        std::cout << "SSL: " << (ssl ? "enabled" : "disabled") << std::endl;
        std::cout << "Timeout: " << timeout << "s" << std::endl;
    };

    std::apply(process_config, config);
}

// 3. 元组展开为函数参数
void function_call_example() {
    std::cout << "\n[元组展开为函数参数]" << std::endl;

    // 普通函数
    auto multiply = [](int a, int b) { return a * b; };

    // 元组
    auto args = std::make_tuple(5, 6);

    // 调用
    int result = std::apply(multiply, args);
    std::cout << "multiply(5, 6) = " << result << std::endl;

    // 成员函数
    struct Calculator {
        int add(int a, int b) { return a + b; }
        int subtract(int a, int b) { return a - b; }
    };

    Calculator calc;
    auto add_args = std::make_tuple(10, 5);

    // 使用 std::apply 调用成员函数
    int add_result = std::apply(
        [&calc](auto&&... args) { return calc.add(std::forward<decltype(args)>(args)...); },
        add_args
    );
    std::cout << "calc.add(10, 5) = " << add_result << std::endl;
}

// 4. 元组与算法结合
void algorithm_example() {
    std::cout << "\n[元组与算法结合]" << std::endl;

    // 创建数值元组
    auto numbers = std::make_tuple(1, 2, 3, 4, 5);

    // 计算元组元素之和
    auto sum = std::apply([](auto... args) {
        return (args + ...);
    }, numbers);
    std::cout << "Sum: " << sum << std::endl;

    // 计算元组元素之积
    auto product = std::apply([](auto... args) {
        return (args * ...);
    }, numbers);
    std::cout << "Product: " << product << std::endl;

    // 打印所有元素
    std::cout << "Elements: ";
    std::apply([](auto... args) {
        ((std::cout << args << " "), ...);
    }, numbers);
    std::cout << std::endl;
}

// 5. 元组与字符串格式化
void string_format_example() {
    std::cout << "\n[元组与字符串格式化]" << std::endl;

    // 格式化函数
    auto format = [](const std::string& format_str, auto... args) {
        std::string result = format_str;
        size_t pos = 0;
        auto replace_placeholder = [&](auto value) {
            pos = result.find("{}", pos);
            if (pos != std::string::npos) {
                result.replace(pos, 2, std::to_string(value));
                pos += std::to_string(value).length();
            }
        };
        (replace_placeholder(args), ...);
        return result;
    };

    // 使用元组展开
    auto args = std::make_tuple(42, 3.14, 100);
    std::string formatted = std::apply(
        [&](auto... args) { return format("Values: {}, {}, {}", args...); },
        args
    );
    std::cout << formatted << std::endl;
}

// 6. 元组与容器操作
void container_example() {
    std::cout << "\n[元组与容器操作]" << std::endl;

    // 创建包含容器的元组
    auto data = std::make_tuple(
        std::vector<int>{1, 2, 3},
        std::vector<int>{4, 5, 6},
        std::vector<int>{7, 8, 9}
    );

    // 合并所有容器
    std::vector<int> merged;
    std::apply([&merged](auto&... containers) {
        (merged.insert(merged.end(), containers.begin(), containers.end()), ...);
    }, data);

    std::cout << "Merged: ";
    for (int v : merged) {
        std::cout << v << " ";
    }
    std::cout << std::endl;

    // 计算总和
    int total = std::accumulate(merged.begin(), merged.end(), 0);
    std::cout << "Total: " << total << std::endl;
}

// 7. 元组与 lambda 表达式
void lambda_example() {
    std::cout << "\n[元组与 lambda 表达式]" << std::endl;

    // 创建 lambda 元组
    auto operations = std::make_tuple(
        [](int x) { return x * 2; },
        [](int x) { return x + 10; },
        [](int x) { return x * x; }
    );

    int value = 5;

    // 对值应用所有操作
    auto results = std::apply([&value](auto&... ops) {
        return std::make_tuple(ops(value)...);
    }, operations);

    std::cout << "Input: " << value << std::endl;
    std::cout << "Results: ";
    std::apply([](auto... args) {
        ((std::cout << args << " "), ...);
    }, results);
    std::cout << std::endl;
}

// 8. 元组与递归
template <typename Tuple, typename Func>
void for_each_in_tuple(Tuple&& tuple, Func&& func) {
    std::apply([&func](auto&&... args) {
        (func(std::forward<decltype(args)>(args)), ...);
    }, std::forward<Tuple>(tuple));
}

void recursive_example() {
    std::cout << "\n[元组与递归]" << std::endl;

    auto data = std::make_tuple(1, 2.5, "Hello", 'c');

    std::cout << "Tuple elements:" << std::endl;
    for_each_in_tuple(data, [](const auto& element) {
        std::cout << "  " << element << std::endl;
    });
}

// 9. 元组与类型擦除
class AnyFunction {
private:
    std::function<void()> func_;

public:
    template <typename Func, typename Tuple>
    AnyFunction(Func&& f, Tuple&& args)
        : func_([f = std::forward<Func>(f), args = std::forward<Tuple>(args)]() {
            std::apply(f, args);
        }) {}

    void operator()() {
        func_();
    }
};

void type_erasure_example() {
    std::cout << "\n[元组与类型擦除]" << std::endl;

    auto print = [](int a, const std::string& b) {
        std::cout << "a=" << a << ", b=" << b << std::endl;
    };

    auto args = std::make_tuple(42, "Hello");

    AnyFunction func(print, args);
    func();
}

// 10. 实际应用：配置解析
struct DatabaseConfig {
    std::string host;
    int port;
    std::string username;
    std::string password;
    std::string database;
};

DatabaseConfig parse_config(const std::tuple<std::string, int, std::string, std::string, std::string>& config) {
    return std::apply([](auto&&... args) {
        return DatabaseConfig{std::forward<decltype(args)>(args)...};
    }, config);
}

void config_parsing_example() {
    std::cout << "\n[配置解析]" << std::endl;

    auto config_tuple = std::make_tuple(
        std::string("localhost"),
        5432,
        std::string("admin"),
        std::string("password"),
        std::string("mydb")
    );

    auto config = parse_config(config_tuple);

    std::cout << "Host: " << config.host << std::endl;
    std::cout << "Port: " << config.port << std::endl;
    std::cout << "Username: " << config.username << std::endl;
    std::cout << "Database: " << config.database << std::endl;
}

// 11. 实际应用：事件系统
class EventSystem {
public:
    using EventHandler = std::function<void()>;

    template <typename Func, typename... Args>
    void register_event(const std::string& event_name, Func&& func, Args&&... args) {
        auto args_tuple = std::make_tuple(std::forward<Args>(args)...);
        handlers_[event_name] = [func = std::forward<Func>(func), args = std::move(args_tuple)]() {
            std::apply(func, args);
        };
    }

    void emit(const std::string& event_name) {
        auto it = handlers_.find(event_name);
        if (it != handlers_.end()) {
            it->second();
        }
    }

private:
    std::map<std::string, EventHandler> handlers_;
};

void event_system_example() {
    std::cout << "\n[事件系统]" << std::endl;

    EventSystem events;

    auto on_login = [](const std::string& username, int user_id) {
        std::cout << "User logged in: " << username << " (ID: " << user_id << ")" << std::endl;
    };

    events.register_event("login", on_login, "Alice", 42);
    events.emit("login");
}

// 12. 性能考虑
void performance_example() {
    std::cout << "\n[性能考虑]" << std::endl;

    std::cout << "std::apply 是编译期展开，没有运行时开销" << std::endl;
    std::cout << "等价于手动调用 std::get<0>(tuple), std::get<1>(tuple), ..." << std::endl;

    // 编译期展开示例
    auto args = std::make_tuple(1, 2, 3, 4, 5);

    // 这两种方式在编译后是等价的
    auto sum1 = std::apply([](auto... args) { return (args + ...); }, args);

    auto sum2 = std::get<0>(args) + std::get<1>(args) + std::get<2>(args) +
                std::get<3>(args) + std::get<4>(args);

    std::cout << "sum1 = " << sum1 << std::endl;
    std::cout << "sum2 = " << sum2 << std::endl;
}

// 主示例函数
void apply_example() {
    std::cout << "=== std::apply ===" << std::endl;

    basic_apply_example();
    tuple_example();
    function_call_example();
    algorithm_example();
    string_format_example();
    container_example();
    lambda_example();
    recursive_example();
    type_erasure_example();
    config_parsing_example();
    event_system_example();
    performance_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    apply_example();
    return 0;
}
#endif
