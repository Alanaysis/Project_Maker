/**
 * @file variant_example.cpp
 * @brief C++17 std::variant 示例
 *
 * std::variant 是一个类型安全的联合体，可以存储多种类型中的一种。
 * 它是传统 union 的现代替代品，提供了类型安全的访问机制。
 *
 * 主要优势：
 * 1. 类型安全 - 编译期类型检查
 * 2. 访问者模式 - 使用 std::visit 进行类型安全访问
 * 3. 异常安全 - 提供强异常安全保证
 */

#include <iostream>
#include <variant>
#include <string>
#include <vector>
#include <map>
#include <functional>
#include <type_traits>

// 1. 基本 variant 使用
void basic_variant_example() {
    std::cout << "\n[基本 variant 使用]" << std::endl;

    // 创建 variant，可以存储 int、double 或 string
    std::variant<int, double, std::string> v1;

    // 默认初始化第一个类型
    std::cout << "v1 index: " << v1.index() << std::endl;
    std::cout << "v1 value: " << std::get<int>(v1) << std::endl;

    // 赋值不同类型的值
    v1 = 3.14;
    std::cout << "v1 index: " << v1.index() << std::endl;
    std::cout << "v1 value: " << std::get<double>(v1) << std::endl;

    v1 = "Hello";
    std::cout << "v1 index: " << v1.index() << std::endl;
    std::cout << "v1 value: " << std::get<std::string>(v1) << std::endl;
}

// 2. 类型安全访问
void type_safe_access_example() {
    std::cout << "\n[类型安全访问]" << std::endl;

    std::variant<int, double, std::string> v = 42;

    // 使用 std::get（抛出异常如果类型错误）
    try {
        int value = std::get<int>(v);
        std::cout << "int value: " << value << std::endl;

        // 这会抛出 std::bad_variant_access
        double wrong = std::get<double>(v);
        (void)wrong;  // 避免未使用警告
    } catch (const std::bad_variant_access& e) {
        std::cout << "Exception: " << e.what() << std::endl;
    }

    // 使用 std::get_if（返回指针，不抛出异常）
    if (auto* p = std::get_if<int>(&v)) {
        std::cout << "int value: " << *p << std::endl;
    } else {
        std::cout << "not an int" << std::endl;
    }

    if (auto* p = std::get_if<double>(&v)) {
        std::cout << "double value: " << *p << std::endl;
    } else {
        std::cout << "not a double" << std::endl;
    }

    // 使用 std::holds_alternative
    std::cout << "holds int: " << std::holds_alternative<int>(v) << std::endl;
    std::cout << "holds double: " << std::holds_alternative<double>(v) << std::endl;
}

// 3. 访问者模式
void visitor_pattern_example() {
    std::cout << "\n[访问者模式]" << std::endl;

    // 定义 variant 类型
    using Value = std::variant<int, double, std::string>;

    // 创建访问者（使用 lambda）
    auto visitor = [](auto&& arg) {
        using T = std::decay_t<decltype(arg)>;
        if constexpr (std::is_same_v<T, int>) {
            std::cout << "int: " << arg << std::endl;
        } else if constexpr (std::is_same_v<T, double>) {
            std::cout << "double: " << arg << std::endl;
        } else if constexpr (std::is_same_v<T, std::string>) {
            std::cout << "string: " << arg << std::endl;
        }
    };

    // 使用 std::visit
    Value v1 = 42;
    Value v2 = 3.14;
    Value v3 = "Hello";

    std::visit(visitor, v1);
    std::visit(visitor, v2);
    std::visit(visitor, v3);
}

// 4. 访问者模式 - 多 variant 访问
void multi_variant_visitor_example() {
    std::cout << "\n[多 variant 访问]" << std::endl;

    using Value = std::variant<int, double>;

    // 访问两个 variant 的组合
    auto add_visitor = [](auto&& a, auto&& b) -> Value {
        return a + b;
    };

    Value a = 10;
    Value b = 20;

    auto result = std::visit(add_visitor, a, b);
    std::cout << "10 + 20 = " << std::get<int>(result) << std::endl;

    a = 3.14;
    b = 2.86;

    result = std::visit(add_visitor, a, b);
    std::cout << "3.14 + 2.86 = " << std::get<double>(result) << std::endl;
}

// 5. variant 作为函数返回值
std::variant<int, std::string> parse_number(const std::string& input) {
    try {
        return std::stoi(input);
    } catch (...) {
        return "Invalid number: " + input;
    }
}

void function_return_example() {
    std::cout << "\n[函数返回值]" << std::endl;

    auto result1 = parse_number("42");
    auto result2 = parse_number("abc");

    auto visitor = [](auto&& arg) {
        using T = std::decay_t<decltype(arg)>;
        if constexpr (std::is_same_v<T, int>) {
            std::cout << "Parsed: " << arg << std::endl;
        } else {
            std::cout << "Error: " << arg << std::endl;
        }
    };

    std::visit(visitor, result1);
    std::visit(visitor, result2);
}

// 6. variant 在容器中的使用
void variant_in_container_example() {
    std::cout << "\n[variant 在容器中]" << std::endl;

    // 存储不同类型的值
    std::vector<std::variant<int, double, std::string>> values;
    values.push_back(42);
    values.push_back(3.14);
    values.push_back("Hello");
    values.push_back(100);
    values.push_back("World");

    // 遍历并处理
    for (const auto& v : values) {
        std::visit([](auto&& arg) {
            std::cout << arg << " ";
        }, v);
    }
    std::cout << std::endl;

    // 统计每种类型的数量
    int int_count = 0;
    int double_count = 0;
    int string_count = 0;

    for (const auto& v : values) {
        if (std::holds_alternative<int>(v)) {
            ++int_count;
        } else if (std::holds_alternative<double>(v)) {
            ++double_count;
        } else if (std::holds_alternative<std::string>(v)) {
            ++string_count;
        }
    }

    std::cout << "ints: " << int_count
              << ", doubles: " << double_count
              << ", strings: " << string_count << std::endl;
}

// 7. variant 实现状态机
enum class State { Idle, Running, Paused, Stopped };
enum class Event { Start, Pause, Resume, Stop };

struct Idle {};
struct Running { int speed; };
struct Paused { int speed; };
struct Stopped { std::string reason; };

using MachineState = std::variant<Idle, Running, Paused, Stopped>;

MachineState transition(MachineState current, Event event) {
    return std::visit([&](auto&& state) -> MachineState {
        using T = std::decay_t<decltype(state)>;

        if constexpr (std::is_same_v<T, Idle>) {
            if (event == Event::Start) {
                return Running{100};
            }
        } else if constexpr (std::is_same_v<T, Running>) {
            if (event == Event::Pause) {
                return Paused{state.speed};
            } else if (event == Event::Stop) {
                return Stopped{"User stopped"};
            }
        } else if constexpr (std::is_same_v<T, Paused>) {
            if (event == Event::Resume) {
                return Running{state.speed};
            } else if (event == Event::Stop) {
                return Stopped{"User stopped"};
            }
        }

        return current;  // 无效转换，保持当前状态
    }, current);
}

void state_machine_example() {
    std::cout << "\n[状态机示例]" << std::endl;

    MachineState state = Idle{};

    auto print_state = [](const MachineState& s) {
        std::visit([](auto&& arg) {
            using T = std::decay_t<decltype(arg)>;
            if constexpr (std::is_same_v<T, Idle>) {
                std::cout << "State: Idle" << std::endl;
            } else if constexpr (std::is_same_v<T, Running>) {
                std::cout << "State: Running (speed: " << arg.speed << ")" << std::endl;
            } else if constexpr (std::is_same_v<T, Paused>) {
                std::cout << "State: Paused (speed: " << arg.speed << ")" << std::endl;
            } else if constexpr (std::is_same_v<T, Stopped>) {
                std::cout << "State: Stopped (" << arg.reason << ")" << std::endl;
            }
        }, s);
    };

    print_state(state);

    state = transition(state, Event::Start);
    print_state(state);

    state = transition(state, Event::Pause);
    print_state(state);

    state = transition(state, Event::Resume);
    print_state(state);

    state = transition(state, Event::Stop);
    print_state(state);
}

// 8. variant 与 std::monostate
void monostate_example() {
    std::cout << "\n[std::monostate]" << std::endl;

    // monostate 用于表示空状态
    std::variant<std::monostate, int, std::string> v;

    // 默认初始化为 monostate
    std::cout << "holds monostate: "
              << std::holds_alternative<std::monostate>(v) << std::endl;

    // 赋值
    v = 42;
    std::cout << "holds int: " << std::holds_alternative<int>(v) << std::endl;

    v = std::monostate{};
    std::cout << "holds monostate: "
              << std::holds_alternative<std::monostate>(v) << std::endl;
}

// 9. variant 的比较操作
void comparison_example() {
    std::cout << "\n[比较操作]" << std::endl;

    std::variant<int, std::string> v1 = 1;
    std::variant<int, std::string> v2 = 2;
    std::variant<int, std::string> v3 = 1;
    std::variant<int, std::string> v4 = "Hello";

    std::cout << "v1 < v2: " << (v1 < v2) << std::endl;
    std::cout << "v1 == v3: " << (v1 == v3) << std::endl;
    std::cout << "v1 < v4: " << (v1 < v4) << std::endl;
}

// 主示例函数
void variant_example() {
    std::cout << "=== std::variant ===" << std::endl;

    basic_variant_example();
    type_safe_access_example();
    visitor_pattern_example();
    multi_variant_visitor_example();
    function_return_example();
    variant_in_container_example();
    state_machine_example();
    monostate_example();
    comparison_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    variant_example();
    return 0;
}
#endif
