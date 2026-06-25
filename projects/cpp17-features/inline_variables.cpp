/**
 * @file inline_variables.cpp
 * @brief C++17 内联变量示例
 *
 * 内联变量允许在头文件中定义变量而不会导致重复定义错误。
 * 它解决了 C++ 中"一次定义规则"（ODR）的限制。
 *
 * 主要优势：
 * 1. 简化头文件 - 可以在头文件中定义变量
 * 2. 避免重复定义 - 内联变量在所有翻译单元中共享
 * 3. 性能优化 - 编译器可以内联访问
 */

#include <iostream>
#include <string>
#include <vector>
#include <map>

// 1. 基本内联变量
// 在头文件中定义（这里模拟头文件环境）
inline int global_counter = 0;
inline std::string app_name = "Cpp17App";
inline const double pi = 3.14159265358979323846;

void basic_inline_example() {
    std::cout << "\n[基本内联变量]" << std::endl;

    std::cout << "global_counter: " << global_counter << std::endl;
    std::cout << "app_name: " << app_name << std::endl;
    std::cout << "pi: " << pi << std::endl;

    // 修改内联变量
    global_counter++;
    std::cout << "global_counter (after increment): " << global_counter << std::endl;
}

// 2. 内联静态成员变量
class Config {
public:
    // 内联静态成员变量（C++17 之前需要在类外定义）
    inline static int max_connections = 100;
    inline static std::string default_host = "localhost";
    inline static bool debug_mode = false;

    static void print() {
        std::cout << "max_connections: " << max_connections << std::endl;
        std::cout << "default_host: " << default_host << std::endl;
        std::cout << "debug_mode: " << (debug_mode ? "true" : "false") << std::endl;
    }
};

// C++17 之前需要在类外定义：
// int Config::max_connections = 100;
// std::string Config::default_host = "localhost";
// bool Config::debug_mode = false;

void static_member_example() {
    std::cout << "\n[内联静态成员变量]" << std::endl;

    Config::print();

    // 修改静态成员
    Config::max_connections = 200;
    Config::debug_mode = true;

    std::cout << "\nAfter modification:" << std::endl;
    Config::print();
}

// 3. 内联常量
class MathConstants {
public:
    inline static const double PI = 3.14159265358979323846;
    inline static const double E = 2.71828182845904523536;
    inline static const double SQRT2 = 1.41421356237309504880;
};

void constants_example() {
    std::cout << "\n[内联常量]" << std::endl;

    std::cout << "PI: " << MathConstants::PI << std::endl;
    std::cout << "E: " << MathConstants::E << std::endl;
    std::cout << "SQRT2: " << MathConstants::SQRT2 << std::endl;
}

// 4. 内联变量与模板
template <typename T>
class TypeTraits {
public:
    inline static const char* name = "unknown";
    inline static constexpr bool is_numeric = false;
};

template <>
class TypeTraits<int> {
public:
    inline static const char* name = "int";
    inline static constexpr bool is_numeric = true;
};

template <>
class TypeTraits<double> {
public:
    inline static const char* name = "double";
    inline static constexpr bool is_numeric = true;
};

template <>
class TypeTraits<std::string> {
public:
    inline static const char* name = "string";
    inline static constexpr bool is_numeric = false;
};

void template_example() {
    std::cout << "\n[内联变量与模板]" << std::endl;

    std::cout << "int: name=" << TypeTraits<int>::name
              << ", is_numeric=" << TypeTraits<int>::is_numeric << std::endl;
    std::cout << "double: name=" << TypeTraits<double>::name
              << ", is_numeric=" << TypeTraits<double>::is_numeric << std::endl;
    std::cout << "string: name=" << TypeTraits<std::string>::name
              << ", is_numeric=" << TypeTraits<std::string>::is_numeric << std::endl;
}

// 5. 内联变量与命名空间
namespace App {
    inline int version_major = 1;
    inline int version_minor = 0;
    inline int version_patch = 0;
    inline std::string version_string = "1.0.0";

    inline void print_version() {
        std::cout << "Version: " << version_string << std::endl;
    }
}

void namespace_example() {
    std::cout << "\n[内联变量与命名空间]" << std::endl;

    std::cout << "App version: " << App::version_major << "."
              << App::version_minor << "." << App::version_patch << std::endl;
    App::print_version();
}

// 6. 内联变量与单例模式
class Logger {
public:
    static Logger& instance() {
        static Logger instance;
        return instance;
    }

    void log(const std::string& message) {
        std::cout << "[LOG] " << message << std::endl;
    }

private:
    Logger() = default;
    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;
};

// 使用内联变量实现单例
inline Logger& get_logger() {
    return Logger::instance();
}

void singleton_example() {
    std::cout << "\n[内联变量与单例模式]" << std::endl;

    get_logger().log("Application started");
    get_logger().log("Processing data");
    get_logger().log("Application finished");
}

// 7. 内联变量与注册表
class PluginRegistry {
public:
    struct PluginInfo {
        std::string name;
        std::string version;
        bool enabled;
    };

    static PluginRegistry& instance() {
        static PluginRegistry registry;
        return registry;
    }

    void register_plugin(const std::string& name, const std::string& version) {
        plugins_[name] = {name, version, true};
    }

    void print_plugins() const {
        for (const auto& [name, info] : plugins_) {
            std::cout << "  " << name << " v" << info.version
                      << " (" << (info.enabled ? "enabled" : "disabled") << ")" << std::endl;
        }
    }

private:
    std::map<std::string, PluginInfo> plugins_;
};

// 使用内联变量注册插件
inline void register_plugins() {
    auto& registry = PluginRegistry::instance();
    registry.register_plugin("auth", "1.0.0");
    registry.register_plugin("database", "2.1.0");
    registry.register_plugin("cache", "1.5.0");
}

void registry_example() {
    std::cout << "\n[内联变量与注册表]" << std::endl;

    register_plugins();
    std::cout << "Registered plugins:" << std::endl;
    PluginRegistry::instance().print_plugins();
}

// 8. 内联变量与配置
class AppConfig {
public:
    struct DatabaseConfig {
        inline static std::string host = "localhost";
        inline static int port = 5432;
        inline static std::string name = "mydb";
    };

    struct ServerConfig {
        inline static std::string address = "0.0.0.0";
        inline static int port = 8080;
        inline static int max_threads = 4;
    };

    static void print() {
        std::cout << "Database: " << DatabaseConfig::host << ":"
                  << DatabaseConfig::port << "/" << DatabaseConfig::name << std::endl;
        std::cout << "Server: " << ServerConfig::address << ":"
                  << ServerConfig::port << " (threads: " << ServerConfig::max_threads << ")" << std::endl;
    }
};

void config_example() {
    std::cout << "\n[内联变量与配置]" << std::endl;

    AppConfig::print();

    // 修改配置
    AppConfig::DatabaseConfig::host = "db.example.com";
    AppConfig::ServerConfig::port = 443;

    std::cout << "\nAfter modification:" << std::endl;
    AppConfig::print();
}

// 9. 内联变量与计数器
class ObjectCounter {
public:
    ObjectCounter() {
        ++count_;
        std::cout << "Object created. Total: " << count_ << std::endl;
    }

    ~ObjectCounter() {
        --count_;
        std::cout << "Object destroyed. Total: " << count_ << std::endl;
    }

    static int count() {
        return count_;
    }

private:
    inline static int count_ = 0;
};

void counter_example() {
    std::cout << "\n[内联变量与计数器]" << std::endl;

    std::cout << "Initial count: " << ObjectCounter::count() << std::endl;

    {
        ObjectCounter obj1;
        ObjectCounter obj2;
        ObjectCounter obj3;

        std::cout << "Current count: " << ObjectCounter::count() << std::endl;
    }

    std::cout << "Final count: " << ObjectCounter::count() << std::endl;
}

// 10. 内联变量的优势对比
void comparison_example() {
    std::cout << "\n[内联变量的优势对比]" << std::endl;

    std::cout << "C++17 之前:" << std::endl;
    std::cout << "  - 头文件中只能声明变量，不能定义" << std::endl;
    std::cout << "  - 需要在 .cpp 文件中定义静态成员" << std::endl;
    std::cout << "  - 常量需要 extern const 声明" << std::endl;

    std::cout << "\nC++17 内联变量:" << std::endl;
    std::cout << "  - 可以在头文件中直接定义变量" << std::endl;
    std::cout << "  - 静态成员可以直接初始化" << std::endl;
    std::cout << "  - 避免重复定义错误" << std::endl;
    std::cout << "  - 简化代码组织" << std::endl;
}

// 主示例函数
void inline_variables_example() {
    std::cout << "=== 内联变量 ===" << std::endl;

    basic_inline_example();
    static_member_example();
    constants_example();
    template_example();
    namespace_example();
    singleton_example();
    registry_example();
    config_example();
    counter_example();
    comparison_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    inline_variables_example();
    return 0;
}
#endif
