/**
 * debug_tips.cpp - 调试技巧大全
 *
 * 本文件演示 C++ 中常用的调试技术和工具，包括：
 *   1. __PRETTY_FUNCTION__ / __FUNCSIG__ 编译器内置宏
 *   2. std::source_location (C++20) 源码位置追踪
 *   3. 条件编译调试宏
 *   4. 栈追踪提示
 *   5. 自定义 assert 变体
 *
 * 编译命令:
 *   C++20: g++ -std=c++20 -g -O0 -o debug_tips debug_tips.cpp
 *   C++17: g++ -std=c++17 -g -O0 -DUSE_CPP17_SOURCE_LOC -o debug_tips debug_tips.cpp
 */

#include <iostream>
#include <string>
#include <string_view>
#include <vector>
#include <cassert>
#include <cstdlib>
#include <sstream>
#include <functional>
#include <array>
#include <cstring>
#include <chrono>
#include <thread>

// ============================================================================
// 第一部分: 函数名打印宏 (__PRETTY_FUNCTION__ / __FUNCSIG__)
// ============================================================================
// __PRETTY_FUNCTION__ 在 GCC/Clang 中打印完整的函数签名
// __FUNCSIG__ 在 MSVC 中打印完整的函数签名
// __func__ (C++11 标准) 只打印函数名，不含模板参数和返回类型

// 跨平台函数签名宏
#ifdef _MSC_VER
    #define CURRENT_FUNCTION __FUNCSIG__
#else
    #define CURRENT_FUNCTION __PRETTY_FUNCTION__
#endif

// 基础用法：打印当前函数名
void simple_function() {
    std::cout << "[基础] 当前函数: " << CURRENT_FUNCTION << std::endl;
}

// 模板函数中，__PRETTY_FUNCTION__ 能显示模板参数的具体类型
template <typename T>
void template_function(T value) {
    std::cout << "[模板] 当前函数: " << CURRENT_FUNCTION << std::endl;
    std::cout << "       T 的类型: " << typeid(T).name() << std::endl;
    (void)value;  // 避免未使用变量警告
}

// 类成员函数同样适用
class MyClass {
public:
    // 普通成员函数
    void member_func() {
        std::cout << "[成员] " << CURRENT_FUNCTION << std::endl;
    }

    // const 成员函数
    void const_member_func() const {
        std::cout << "[const成员] " << CURRENT_FUNCTION << std::endl;
    }

    // 模板成员函数
    template <typename T>
    void template_member(T&& arg) {
        std::cout << "[模板成员] " << CURRENT_FUNCTION << std::endl;
        (void)arg;
    }
};

// 演示 __PRETTY_FUNCTION__ 的各种场景
void demo_pretty_function() {
    std::cout << "========================================" << std::endl;
    std::cout << "1. 函数名打印宏 (Pretty Function)" << std::endl;
    std::cout << "========================================" << std::endl;

    simple_function();

    // 模板实例化后会显示具体类型
    template_function(42);          // T = int
    template_function(3.14);        // T = double
    template_function(std::string("hello"));  // T = std::string

    MyClass obj;
    obj.member_func();
    obj.const_member_func();
    obj.template_member(42);

    // lambda 表达式也能捕获函数签名
    auto lambda = []() {
        std::cout << "[lambda] " << CURRENT_FUNCTION << std::endl;
    };
    lambda();

    std::cout << std::endl;
}

// ============================================================================
// 第二部分: 源码位置追踪 (Source Location)
// ============================================================================
// C++20 引入了 std::source_location，替代传统的 __FILE__, __LINE__ 宏
// 优势: 类型安全、可在 constexpr 中使用、支持默认参数捕获调用位置

#ifdef USE_CPP17_SOURCE_LOC
    // C++17 回退方案：使用传统宏模拟 source_location
    struct source_location {
        const char* file;
        int line;
        const char* func;

        static source_location current(const char* file = __FILE__,
                                        int line = __LINE__,
                                        const char* func = __func__) {
            return {file, line, func};
        }
    };
#else
    #include <source_location>
    using std::source_location;
#endif

// 使用 source_location 作为默认参数，自动捕获调用位置
// 这是 source_location 最重要的使用模式：
// 调用者不需要显式传递位置信息，编译器会自动填充
void log_message(std::string_view message,
                 source_location loc = source_location::current()) {
    std::cout << "[LOG] " << loc.file_name() << ":" << loc.line()
              << " (" << loc.function_name() << ") "
              << message << std::endl;
}

// 包装函数示例：在包装层记录真实调用位置
void error_handler(std::string_view msg,
                   source_location loc = source_location::current()) {
    std::cerr << "\033[31m"  // 红色
              << "[ERROR] " << loc.file_name() << ":" << loc.line()
              << " in " << loc.function_name() << ": " << msg
              << "\033[0m" << std::endl;
}

void demo_source_location() {
    std::cout << "========================================" << std::endl;
    std::cout << "2. 源码位置追踪 (Source Location)" << std::endl;
    std::cout << "========================================" << std::endl;

    // log_message 会自动记录调用位置
    log_message("程序启动");
    log_message("初始化完成");

    // error_handler 同样自动记录位置
    error_handler("这是一个测试错误");

    // 在循环中也能正确追踪
    for (int i = 0; i < 3; ++i) {
        log_message("循环迭代: " + std::to_string(i));
    }

    std::cout << std::endl;
}

// ============================================================================
// 第三部分: 条件编译调试宏
// ============================================================================
// 通过预处理器宏控制调试代码的编译，实现零开销的生产构建

// 基础调试级别定义
enum class DebugLevel {
    NONE = 0,     // 关闭所有调试
    ERROR = 1,    // 只显示错误
    WARN = 2,     // 警告和错误
    INFO = 3,     // 信息、警告和错误
    DEBUG = 4,    // 所有调试信息
    TRACE = 5     // 详细追踪
};

// 编译时调试级别设置（可通过 -DDEBUG_LEVEL=N 修改）
#ifndef DEBUG_LEVEL
    #ifdef NDEBUG
        #define DEBUG_LEVEL 0  // Release 模式默认关闭
    #else
        #define DEBUG_LEVEL 5  // Debug 模式默认全部开启
    #endif
#endif

// 条件编译调试宏：如果编译时级别不够，整个调用会被优化掉
#define LOG_AT_LEVEL(level, msg) \
    do { \
        if constexpr (DEBUG_LEVEL >= static_cast<int>(level)) { \
            std::cout << "[" #level "] " << __FILE__ << ":" << __LINE__ \
                      << " " << __func__ << "(): " << msg << std::endl; \
        } \
    } while(0)

#define LOG_DEBUG(msg) LOG_AT_LEVEL(DebugLevel::DEBUG, msg)
#define LOG_INFO(msg)  LOG_AT_LEVEL(DebugLevel::INFO, msg)
#define LOG_WARN(msg)  LOG_AT_LEVEL(DebugLevel::WARN, msg)
#define LOG_ERROR(msg) LOG_AT_LEVEL(DebugLevel::ERROR, msg)

// 带值打印的调试宏 - 调试时经常需要打印变量名和值
#define DUMP_VAR(x) \
    do { \
        if constexpr (DEBUG_LEVEL >= 4) { \
            std::cout << "[DUMP] " << #x << " = " << (x) \
                      << " (" << __FILE__ << ":" << __LINE__ << ")" << std::endl; \
        } \
    } while(0)

// 批量变量打印
#define DUMP_VARS(...) \
    do { \
        if constexpr (DEBUG_LEVEL >= 4) { \
            std::cout << "[DUMP] "; \
            dump_impl(__VA_ARGS__); \
            std::cout << " (" << __FILE__ << ":" << __LINE__ << ")" << std::endl; \
        } \
    } while(0)

// 辅助函数：递归打印多个变量
template <typename T>
void dump_impl(const char* name, const T& value) {
    std::cout << name << "=" << value;
}

template <typename T, typename... Args>
void dump_impl(const char* name, const T& value, Args... args) {
    std::cout << name << "=" << value << ", ";
    dump_impl(args...);
}

// 带计时的性能测量宏
#define MEASURE_TIME(label, code_block) \
    do { \
        if constexpr (DEBUG_LEVEL >= 3) { \
            auto _start = std::chrono::high_resolution_clock::now(); \
            code_block; \
            auto _end = std::chrono::high_resolution_clock::now(); \
            auto _dur = std::chrono::duration_cast<std::chrono::microseconds>(_end - _start); \
            std::cout << "[PERF] " << label << ": " << _dur.count() << " us" << std::endl; \
        } else { \
            code_block; \
        } \
    } while(0)

void demo_debug_macros() {
    std::cout << "========================================" << std::endl;
    std::cout << "3. 条件编译调试宏" << std::endl;
    std::cout << "========================================" << std::endl;

    LOG_INFO("调试宏演示开始");

    int x = 42;
    double pi = 3.14159;
    std::string name = "test";

    // 打印单个变量
    DUMP_VAR(x);
    DUMP_VAR(pi);
    DUMP_VAR(name);

    // 各级别日志
    LOG_DEBUG("这是一条调试信息");
    LOG_INFO("这是一条普通信息");
    LOG_WARN("这是一条警告");
    LOG_ERROR("这是一条错误");

    // 性能测量
    MEASURE_TIME("向量填充", {
        std::vector<int> v;
        for (int i = 0; i < 100000; ++i) {
            v.push_back(i);
        }
    });

    // 注意：如果编译时 DEBUG_LEVEL < 4，DUMP_VAR 和 LOG_DEBUG 的代码
    // 会被完全优化掉，实现零运行时开销
    std::cout << "当前编译时调试级别: " << DEBUG_LEVEL << std::endl;
    std::cout << std::endl;
}

// ============================================================================
// 第四部分: 栈追踪提示
// ============================================================================
// C++23 引入了 std::stacktrace，这里展示 C++17/20 的替代方案
// 通过逐层记录调用信息来模拟栈追踪

class CallStack {
public:
    // 进入函数时调用，记录函数名和位置
    static void push(std::string_view func,
                     source_location loc = source_location::current()) {
        auto& stack = get_stack();
        stack.push_back({std::string(func),
                         std::string(loc.file_name()),
                         static_cast<int>(loc.line())});
    }

    // 退出函数时调用
    static void pop() {
        auto& stack = get_stack();
        if (!stack.empty()) {
            stack.pop_back();
        }
    }

    // 打印当前调用栈
    static void print() {
        auto& stack = get_stack();
        std::cout << "--- 调用栈 (" << stack.size() << " 层) ---" << std::endl;
        for (int i = static_cast<int>(stack.size()) - 1; i >= 0; --i) {
            std::cout << "  #" << (stack.size() - 1 - i) << " "
                      << stack[i].function << " at "
                      << stack[i].file << ":" << stack[i].line
                      << std::endl;
        }
        std::cout << "--- 栈底 ---" << std::endl;
    }

private:
    struct Frame {
        std::string function;
        std::string file;
        int line;
    };

    // 使用线程局部存储，支持多线程环境
    static std::vector<Frame>& get_stack() {
        thread_local std::vector<Frame> stack;
        return stack;
    }
};

// RAII 风格的栈帧追踪器 - 进入时 push，离开时自动 pop
class StackTracer {
public:
    explicit StackTracer(std::string_view func,
                         source_location loc = source_location::current())
        : m_func(func) {
        CallStack::push(func, loc);
    }

    ~StackTracer() {
        CallStack::pop();
    }

    // 禁止拷贝和移动
    StackTracer(const StackTracer&) = delete;
    StackTracer& operator=(const StackTracer&) = delete;

private:
    std::string m_func;
};

// 便捷宏：在函数入口自动创建栈帧追踪
#define TRACE_FUNCTION() StackTracer _tracer##__LINE__(CURRENT_FUNCTION)

// 演示多层调用的栈追踪
void level3() {
    TRACE_FUNCTION();
    std::cout << "  -> 进入 level3()" << std::endl;
    CallStack::print();
}

void level2() {
    TRACE_FUNCTION();
    std::cout << "  -> 进入 level2()" << std::endl;
    level3();
}

void level1() {
    TRACE_FUNCTION();
    std::cout << "  -> 进入 level1()" << std::endl;
    level2();
}

void demo_stack_trace() {
    std::cout << "========================================" << std::endl;
    std::cout << "4. 栈追踪提示 (Stack Trace)" << std::endl;
    std::cout << "========================================" << std::endl;

    level1();
    std::cout << std::endl;
}

// ============================================================================
// 第五部分: 自定义 Assert 变体
// ============================================================================
// 标准 assert 在 NDEBUG 模式下会被移除，自定义版本可以保留错误信息
// 并提供更丰富的诊断信息

// Assert 级别定义
enum class AssertAction {
    ABORT,    // 直接终止
    THROW,    // 抛出异常
    BREAK,    // 调试断点
    CONTINUE  // 仅记录，继续执行
};

// 当前 assert 策略（可运行时修改）
inline AssertAction g_assert_action = AssertAction::ABORT;

// 断言失败时的诊断信息结构
struct AssertInfo {
    const char* expr;       // 断言表达式
    const char* file;       // 文件名
    int line;               // 行号
    const char* function;   // 函数名
    const char* message;    // 附加消息（可选）
};

// 格式化断言失败信息
inline std::string format_assert_failure(const AssertInfo& info) {
    std::ostringstream oss;
    oss << "\n=== 断言失败 ===" << std::endl;
    oss << "  表达式: " << info.expr << std::endl;
    oss << "  位置:   " << info.file << ":" << info.line << std::endl;
    oss << "  函数:   " << info.function << std::endl;
    if (info.message && info.message[0] != '\0') {
        oss << "  消息:   " << info.message << std::endl;
    }
    oss << "================" << std::endl;
    return oss.str();
}

// 处理断言失败
inline void handle_assert_failure(const AssertInfo& info) {
    std::string msg = format_assert_failure(info);

    switch (g_assert_action) {
        case AssertAction::ABORT:
            std::cerr << msg << std::endl;
            std::abort();

        case AssertAction::THROW:
            throw std::runtime_error(msg);

        case AssertAction::BREAK:
            std::cerr << msg << "(设置断点于此)" << std::endl;
            // 在实际调试器中，这里可以触发断点
            // __builtin_debugtrap();  // GCC/Clang
            // __debugbreak();         // MSVC
            break;

        case AssertAction::CONTINUE:
            std::cerr << msg << "(继续执行)" << std::endl;
            break;
    }
}

// 基础断言宏 - 始终生效，不会被 NDEBUG 移除
#define ASSERT(expr) \
    do { \
        if (!(expr)) { \
            handle_assert_failure({#expr, __FILE__, __LINE__, \
                                   CURRENT_FUNCTION, ""}); \
        } \
    } while(0)

// 带消息的断言宏
#define ASSERT_MSG(expr, msg) \
    do { \
        if (!(expr)) { \
            handle_assert_failure({#expr, __FILE__, __LINE__, \
                                   CURRENT_FUNCTION, msg}); \
        } \
    } while(0)

// 相等性断言 - 打印比较双方的值，便于调试
#define ASSERT_EQ(a, b) \
    do { \
        if (!((a) == (b))) { \
            std::ostringstream _oss; \
            _oss << "期望相等: " << #a << "=" << (a) \
                 << ", " << #b << "=" << (b); \
            handle_assert_failure({#a " == " #b, __FILE__, __LINE__, \
                                   CURRENT_FUNCTION, \
                                   _oss.str().c_str()}); \
        } \
    } while(0)

// 范围断言 - 检查值是否在指定范围内
#define ASSERT_IN_RANGE(val, min_val, max_val) \
    do { \
        auto _v = (val); \
        if (_v < (min_val) || _v > (max_val)) { \
            std::ostringstream _oss; \
            _oss << #val << "=" << _v \
                 << " 不在范围 [" << (min_val) << ", " << (max_val) << "]"; \
            handle_assert_failure({#val " in range", __FILE__, __LINE__, \
                                   CURRENT_FUNCTION, \
                                   _oss.str().c_str()}); \
        } \
    } while(0)

// 非空指针断言
#define ASSERT_NOT_NULL(ptr) \
    ASSERT_MSG((ptr) != nullptr, #ptr " 不应为空指针")

// 异常断言 - 验证代码是否抛出了预期异常
#define ASSERT_THROWS(expr, exception_type) \
    do { \
        bool _caught = false; \
        try { \
            expr; \
        } catch (const exception_type&) { \
            _caught = true; \
        } catch (...) { \
            handle_assert_failure({#expr " throws " #exception_type, \
                                   __FILE__, __LINE__, CURRENT_FUNCTION, \
                                   "抛出了非预期类型的异常"}); \
        } \
        if (!_caught) { \
            handle_assert_failure({#expr " throws " #exception_type, \
                                   __FILE__, __LINE__, CURRENT_FUNCTION, \
                                   "未抛出预期异常"}); \
        } \
    } while(0)

// 演示自定义断言
void demo_assertions() {
    std::cout << "========================================" << std::endl;
    std::cout << "5. 自定义 Assert 变体" << std::endl;
    std::cout << "========================================" << std::endl;

    // 设置为 CONTINUE 模式，避免程序终止
    g_assert_action = AssertAction::CONTINUE;

    // 基础断言 - 通过
    int x = 42;
    ASSERT(x == 42);
    std::cout << "基础断言通过: x == 42" << std::endl;

    // 基础断言 - 失败（CONTINUE 模式不会终止）
    ASSERT(x > 100);
    std::cout << "（断言失败但继续执行）" << std::endl;

    // 相等性断言
    std::string name = "hello";
    ASSERT_EQ(name, "hello");
    std::cout << "相等性断言通过" << std::endl;

    // 范围断言
    int score = 85;
    ASSERT_IN_RANGE(score, 0, 100);
    std::cout << "范围断言通过: score in [0, 100]" << std::endl;

    // 非空指针断言
    int* ptr = &x;
    ASSERT_NOT_NULL(ptr);
    std::cout << "非空指针断言通过" << std::endl;

    // 异常断言
    ASSERT_THROWS(throw std::runtime_error("test"), std::runtime_error);
    std::cout << "异常断言通过" << std::endl;

    // 恢复为默认的 ABORT 模式
    g_assert_action = AssertAction::ABORT;

    std::cout << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================
int main() {
    std::cout << "╔══════════════════════════════════════╗" << std::endl;
    std::cout << "║    C++ 调试技巧大全 (debug_tips)     ║" << std::endl;
    std::cout << "╚══════════════════════════════════════╝" << std::endl;
    std::cout << std::endl;

    demo_pretty_function();
    demo_source_location();
    demo_debug_macros();
    demo_stack_trace();
    demo_assertions();

    std::cout << "所有调试技巧演示完成。" << std::endl;
    return 0;
}
