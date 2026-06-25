// constinit.cpp - C++20 constinit 示例
//
// 本文件展示 C++20 constinit 的用法，包括：
//   1. constinit 的基本用法
//   2. 静态初始化顺序问题（SIOF）
//   3. constinit 的解决方案
//   4. constinit 与 constexpr 的配合
//
// 编译命令：
//   g++ -std=c++20 examples/constinit.cpp -o constinit

#include <iostream>
#include <string>
#include <array>

// ============================================================================
// 第一部分：constinit 基本用法
// ============================================================================

// constinit：保证常量初始化（但变量可以修改）
constinit int global_value = 42;
constinit double global_pi = 3.14159265358979323846;
constinit bool global_flag = true;

// constinit 数组
constinit int global_array[5] = {1, 2, 3, 4, 5};

// ============================================================================
// 第二部分：静态初始化顺序问题（SIOF）
// ============================================================================

// 问题示例：全局变量的初始化顺序是未定义的

// 这两个全局变量可能以任意顺序初始化
int global_a = 10;
int global_b = global_a + 5;  // 可能在 global_a 之前初始化！

// ============================================================================
// 第三部分：constinit 解决 SIOF
// ============================================================================

// 使用 constinit 保证编译期初始化
constexpr int safe_global_a = 10;  // 使用 constexpr 保证编译期常量
constinit int safe_global_b = safe_global_a + 5;  // 使用 constinit 保证初始化

// constinit 与 constexpr 的配合
constexpr int compute_value() {
    return 42 * 42;
}

constinit int computed_global = compute_value();  // 编译期计算

// constinit 用于静态局部变量
void function_with_static() {
    constinit static int counter = 0;  // 保证编译期初始化
    ++counter;
    std::cout << "Counter: " << counter << std::endl;
}

// ============================================================================
// 第四部分：constinit 的使用场景
// ============================================================================

// 场景 1：单例模式（线程安全）
class Singleton {
public:
    static Singleton& instance() {
        constinit static Singleton instance;  // C++11 保证线程安全
        return instance;
    }

    void do_something() {
        std::cout << "Singleton::do_something()" << std::endl;
    }

private:
    Singleton() = default;
    ~Singleton() = default;
    Singleton(const Singleton&) = delete;
    Singleton& operator=(const Singleton&) = delete;
};

// 场景 2：编译期配置
struct ServerConfig {
    int port;
    int max_connections;
    int timeout;
    const char* log_level;
};

constexpr ServerConfig make_server_config() {
    return ServerConfig{
        8080,
        1000,
        30,
        "INFO"
    };
}

// 使用 constexpr 保证编译期常量
constexpr ServerConfig server_config = make_server_config();

// 场景 3：编译期查找表
constexpr auto make_lookup_table() {
    std::array<int, 256> table{};
    for (int i = 0; i < 256; ++i) {
        table[i] = i * i;
    }
    return table;
}

constexpr auto lookup_table = make_lookup_table();

// 场景 4：编译期状态
enum class State {
    Idle,
    Running,
    Stopped
};

struct StateMachine {
    State current_state;
    int counter;
};

constinit StateMachine global_state_machine = {
    State::Idle,
    0
};

// 场景 5：编译期字符串
constexpr const char* greeting = "Hello, World!";

// ============================================================================
// 第五部分：constinit 与 constexpr 的区别
// ============================================================================

// constexpr：编译期常量，不能修改
constexpr int constexpr_value = 42;

// constinit：保证常量初始化，但可以修改
constinit int constinit_value = 42;

// constexpr 变量必须在编译期初始化
// constexpr int constexpr_maybe = get_runtime_value();  // 编译错误

// constinit 变量可以在运行时修改
void modify_constinit() {
    constinit_value = 100;  // OK：constinit 变量可以修改
}

// ============================================================================
// 第六部分：编译期断言验证
// ============================================================================

// 验证 constexpr 变量（可以用于 static_assert）
static_assert(safe_global_a == 10);
static_assert(server_config.port == 8080);
static_assert(server_config.max_connections == 1000);
static_assert(server_config.timeout == 30);

// 验证编译期查找表
static_assert(lookup_table[0] == 0);
static_assert(lookup_table[10] == 100);
static_assert(lookup_table[255] == 65025);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== C++20 constinit 示例 ===" << std::endl;
    std::cout << std::endl;

    // constinit 基本用法
    std::cout << "1. constinit 基本用法:" << std::endl;
    std::cout << "   global_value = " << global_value << std::endl;
    std::cout << "   global_pi = " << global_pi << std::endl;
    std::cout << "   global_flag = " << (global_flag ? "true" : "false") << std::endl;
    std::cout << "   global_array = [";
    for (int i = 0; i < 5; ++i) {
        if (i > 0) std::cout << ", ";
        std::cout << global_array[i];
    }
    std::cout << "]" << std::endl;
    std::cout << std::endl;

    // SIOF 问题
    std::cout << "2. 静态初始化顺序问题:" << std::endl;
    std::cout << "   global_a = " << global_a << std::endl;
    std::cout << "   global_b = " << global_b << " (可能不正确)" << std::endl;
    std::cout << "   safe_global_a = " << safe_global_a << std::endl;
    std::cout << "   safe_global_b = " << safe_global_b << " (使用 constinit 保证正确)" << std::endl;
    std::cout << std::endl;

    // 编译期配置
    std::cout << "3. 编译期配置:" << std::endl;
    std::cout << "   server_config.port = " << server_config.port << std::endl;
    std::cout << "   server_config.max_connections = " << server_config.max_connections << std::endl;
    std::cout << "   server_config.timeout = " << server_config.timeout << std::endl;
    std::cout << "   server_config.log_level = " << server_config.log_level << std::endl;
    std::cout << std::endl;

    // 编译期查找表
    std::cout << "4. 编译期查找表:" << std::endl;
    std::cout << "   lookup_table[10] = " << lookup_table[10] << std::endl;
    std::cout << "   lookup_table[100] = " << lookup_table[100] << std::endl;
    std::cout << "   lookup_table[255] = " << lookup_table[255] << std::endl;
    std::cout << std::endl;

    // 编译期状态
    std::cout << "5. 编译期状态:" << std::endl;
    std::cout << "   global_state_machine.current_state = "
              << static_cast<int>(global_state_machine.current_state) << std::endl;
    std::cout << "   global_state_machine.counter = " << global_state_machine.counter << std::endl;
    std::cout << std::endl;

    // constinit 与 constexpr 的区别
    std::cout << "6. constinit 与 constexpr 的区别:" << std::endl;
    std::cout << "   constexpr_value = " << constexpr_value << " (不可修改)" << std::endl;
    std::cout << "   constinit_value = " << constinit_value << " (可修改)" << std::endl;

    // 修改 constinit 变量
    modify_constinit();
    std::cout << "   修改后 constinit_value = " << constinit_value << std::endl;
    std::cout << std::endl;

    // 静态局部变量
    std::cout << "7. 静态局部变量:" << std::endl;
    function_with_static();
    function_with_static();
    function_with_static();
    std::cout << std::endl;

    // 单例模式
    std::cout << "8. 单例模式:" << std::endl;
    Singleton::instance().do_something();
    std::cout << std::endl;

    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
