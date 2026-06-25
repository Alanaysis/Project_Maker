/**
 * @file static_operator.cpp
 * @brief C++23 static operator() 和 static operator[] 示例
 *
 * C++23 允许将 operator() 和 operator[] 声明为 static。
 * 这使得可以在不创建对象的情况下调用这些运算符。
 *
 * 主要特点：
 * - operator() 可以是 static
 * - operator[] 可以是 static
 * - 无需创建对象即可调用
 * - 适用于函数对象和策略模式
 *
 * 编译命令：
 * g++ -std=c++23 -o static_operator static_operator.cpp
 */

#include <iostream>
#include <vector>
#include <algorithm>
#include <string>
#include <functional>

// ========== 1. 基本的 static operator() ==========

// 使用 static operator() 的函数对象
struct Square {
    static constexpr int operator()(int x) {
        return x * x;
    }
};

struct Add {
    static constexpr int operator()(int a, int b) {
        return a + b;
    }
};

void basic_static_operator() {
    std::cout << "=== 基本的 static operator() ===" << std::endl;

    // 无需创建对象即可调用
    std::cout << "Square(5) = " << Square::operator()(5) << std::endl;
    std::cout << "Add(3, 4) = " << Add::operator()(3, 4) << std::endl;

    // 也可以通过对象调用
    Square sq;
    std::cout << "sq(5) = " << sq(5) << std::endl;
}

// ========== 2. static operator[] ==========

// 使用 static operator[] 的查找表
struct LookupTable {
    static constexpr int operator[](int index) {
        // 简单的查找表
        constexpr int table[] = {0, 1, 4, 9, 16, 25, 36, 49, 64, 81};
        if (index >= 0 && index < 10) {
            return table[index];
        }
        return -1;
    }
};

void static_subscript() {
    std::cout << "\n=== static operator[] ===" << std::endl;

    // 无需创建对象即可使用
    std::cout << "LookupTable[3] = " << LookupTable::operator[](3) << std::endl;
    std::cout << "LookupTable[7] = " << LookupTable::operator[](7) << std::endl;
}

// ========== 3. 实际应用：策略模式 ==========

// 排序策略
struct AscendingSort {
    static bool operator()(int a, int b) {
        return a < b;
    }
};

struct DescendingSort {
    static bool operator()(int a, int b) {
        return a > b;
    }
};

// 使用策略的排序函数
template<typename SortStrategy>
void sort_with_strategy(std::vector<int>& vec) {
    std::sort(vec.begin(), vec.end(), SortStrategy::operator());
}

void strategy_pattern() {
    std::cout << "\n=== 实际应用：策略模式 ===" << std::endl;

    std::vector<int> data = {5, 2, 8, 1, 9, 3};

    std::cout << "Original: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    // 使用升序策略
    auto ascending_data = data;
    sort_with_strategy<AscendingSort>(ascending_data);
    std::cout << "Ascending: ";
    for (int n : ascending_data) std::cout << n << " ";
    std::cout << std::endl;

    // 使用降序策略
    auto descending_data = data;
    sort_with_strategy<DescendingSort>(descending_data);
    std::cout << "Descending: ";
    for (int n : descending_data) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 4. 实际应用：函数组合 ==========

// 函数组合器
struct Compose {
    template<typename F, typename G>
    static auto operator()(F f, G g) {
        return [f, g](auto x) { return f(g(x)); };
    }
};

void function_composition() {
    std::cout << "\n=== 实际应用：函数组合 ===" << std::endl;

    auto double_it = [](int x) { return x * 2; };
    auto add_one = [](int x) { return x + 1; };

    // 组合函数
    auto composed = Compose::operator()(double_it, add_one);

    std::cout << "composed(5) = " << composed(5) << std::endl;  // (5 + 1) * 2 = 12
}

// ========== 5. 实际应用：数学运算 ==========

// 数学运算库
struct MathOps {
    static constexpr double add(double a, double b) { return a + b; }
    static constexpr double subtract(double a, double b) { return a - b; }
    static constexpr double multiply(double a, double b) { return a * b; }
    static constexpr double divide(double a, double b) { return b != 0 ? a / b : 0; }

    // 使用 static operator() 的通用运算
    static constexpr double operator()(double a, double b, char op) {
        switch (op) {
            case '+': return add(a, b);
            case '-': return subtract(a, b);
            case '*': return multiply(a, b);
            case '/': return divide(a, b);
            default: return 0;
        }
    }
};

void math_operations() {
    std::cout << "\n=== 实际应用：数学运算 ===" << std::endl;

    std::cout << "3 + 4 = " << MathOps::operator()(3, 4, '+') << std::endl;
    std::cout << "10 - 3 = " << MathOps::operator()(10, 3, '-') << std::endl;
    std::cout << "5 * 6 = " << MathOps::operator()(5, 6, '*') << std::endl;
    std::cout << "20 / 4 = " << MathOps::operator()(20, 4, '/') << std::endl;
}

// ========== 6. 实际应用：缓存系统 ==========

// 缓存键生成器
struct CacheKeyGenerator {
    static std::string operator()(const std::string& prefix, int id) {
        return prefix + ":" + std::to_string(id);
    }
};

void cache_system() {
    std::cout << "\n=== 实际应用：缓存系统 ===" << std::endl;

    // 生成缓存键
    std::string key1 = CacheKeyGenerator::operator()("user", 123);
    std::string key2 = CacheKeyGenerator::operator()("product", 456);

    std::cout << "Cache key 1: " << key1 << std::endl;
    std::cout << "Cache key 2: " << key2 << std::endl;
}

// ========== 7. 实际应用：事件系统 ==========

// 事件处理器
struct EventHandler {
    static void operator()(const std::string& event, const std::string& data) {
        std::cout << "Event: " << event << ", Data: " << data << std::endl;
    }
};

void event_system() {
    std::cout << "\n=== 实际应用：事件系统 ===" << std::endl;

    // 处理事件
    EventHandler::operator()("click", "button1");
    EventHandler::operator()("keypress", "Enter");
    EventHandler::operator()("scroll", "down");
}

// ========== 8. 实际应用：日志系统 ==========

// 日志记录器
struct Logger {
    enum class Level { DEBUG, INFO, WARNING, ERROR };

    static void operator()(Level level, const std::string& message) {
        std::string level_str;
        switch (level) {
            case Level::DEBUG:   level_str = "DEBUG"; break;
            case Level::INFO:    level_str = "INFO"; break;
            case Level::WARNING: level_str = "WARN"; break;
            case Level::ERROR:   level_str = "ERROR"; break;
        }
        std::cout << "[" << level_str << "] " << message << std::endl;
    }
};

void logging_system() {
    std::cout << "\n=== 实际应用：日志系统 ===" << std::endl;

    Logger::operator()(Logger::Level::INFO, "Application started");
    Logger::operator()(Logger::Level::DEBUG, "Loading configuration");
    Logger::operator()(Logger::Level::WARNING, "Config file not found");
    Logger::operator()(Logger::Level::ERROR, "Failed to connect");
}

// ========== 9. 实际应用：验证器 ==========

// 数据验证器
struct Validator {
    static bool operator()(const std::string& value, int min_length, int max_length) {
        return value.length() >= static_cast<size_t>(min_length) &&
               value.length() <= static_cast<size_t>(max_length);
    }
};

void validation_example() {
    std::cout << "\n=== 实际应用：验证器 ===" << std::endl;

    std::string password = "mypassword123";

    bool valid = Validator::operator()(password, 8, 20);
    std::cout << "Password '" << password << "' is "
              << (valid ? "valid" : "invalid") << std::endl;

    std::string short_pw = "abc";
    bool invalid = Validator::operator()(short_pw, 8, 20);
    std::cout << "Password '" << short_pw << "' is "
              << (invalid ? "valid" : "invalid") << std::endl;
}

// ========== 10. 实际应用：转换器 ==========

// 类型转换器
struct Converter {
    static std::string operator()(int value) {
        return std::to_string(value);
    }

    static std::string operator()(double value) {
        return std::to_string(value);
    }

    static std::string operator()(bool value) {
        return value ? "true" : "false";
    }
};

void conversion_example() {
    std::cout << "\n=== 实际应用：转换器 ===" << std::endl;

    std::cout << "Int to string: " << Converter::operator()(42) << std::endl;
    std::cout << "Double to string: " << Converter::operator()(3.14) << std::endl;
    std::cout << "Bool to string: " << Converter::operator()(true) << std::endl;
}

int main() {
    std::cout << "C++23 static operator() / static operator[] 示例\n" << std::endl;

    basic_static_operator();
    static_subscript();
    strategy_pattern();
    function_composition();
    math_operations();
    cache_system();
    event_system();
    logging_system();
    validation_example();
    conversion_example();

    return 0;
}
