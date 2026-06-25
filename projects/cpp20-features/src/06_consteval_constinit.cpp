/**
 * 06_consteval_constinit.cpp - C++20 consteval 和 constinit
 *
 * consteval 和 constinit 是 C++20 引入的编译期计算增强。
 *
 * 核心要点：
 * 1. consteval - 立即函数，必须在编译期求值
 * 2. constinit - 确保变量在编译期初始化（解决 static 初始化顺序问题）
 * 3. constexpr 函数 vs consteval 函数
 * 4. constinit 解决 SIOF (Static Initialization Order Fiasco)
 */

#include <iostream>
#include <array>
#include <cstdint>
#include <string_view>

// ============================================================
// 1. consteval - 立即函数 (Immediate Functions)
// ============================================================

// consteval 函数必须在编译期求值
consteval int square(int x) {
    return x * x;
}

// consteval 可用于数组大小、case 标签等编译期常量
consteval int fibonacci(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

// consteval 函数模板
consteval auto make_array_size() {
    return 10;
}

// ============================================================
// 2. constexpr - 可以在编译期或运行期求值
// ============================================================

// constexpr 函数既可以在编译期也可以在运行期调用
constexpr int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

// ============================================================
// 3. constinit - 编译期初始化保证
// ============================================================

// 普通全局变量 - 运行时初始化，可能有初始化顺序问题
// int global_runtime = some_function();  // 运行时初始化

// constinit 保证编译期初始化 - 零初始化 + 常量初始化
constinit int global_value = 42;
constinit const char* global_str = "Hello, constinit!";

// 模拟：解决 static 初始化顺序问题
struct Config {
    int max_connections;
    int timeout_ms;
};

// 使用 constinit 确保在编译期初始化
constinit Config global_config = {100, 5000};

// ============================================================
// 4. 对比演示
// ============================================================

// constexpr - 编译期或运行期
constexpr int compile_or_runtime(int x) {
    return x * x + 1;
}

// consteval - 仅编译期
consteval int compile_only(int x) {
    return x * x + 1;
}

// ============================================================
// 5. 综合应用：编译期配置
// ============================================================

consteval int compute_buffer_size() {
    // 复杂的编译期计算
    int size = 1;
    for (int i = 0; i < 10; ++i) {
        size *= 2;
    }
    return size;  // 1024
}

// 使用 consteval 结果定义数组
constexpr int BUFFER_SIZE = compute_buffer_size();
std::array<char, BUFFER_SIZE> global_buffer{};

// 编译期字符串哈希
consteval uint32_t fnv1a_hash(std::string_view str) {
    uint32_t hash = 2166136261u;
    for (char c : str) {
        hash ^= static_cast<uint32_t>(c);
        hash *= 16777619u;
    }
    return hash;
}

// ============================================================
// 6. constinit 用于延迟初始化
// ============================================================

// constinit 变量可以运行时修改（不是 const！）
constinit int mutable_global = 0;

void update_global() {
    mutable_global = 100;  // OK: constinit 不是 const
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 consteval 和 constinit 示例 ===\n\n";

    // 1. consteval 基础
    std::cout << "【1. consteval - 立即函数】\n";
    constexpr auto sq = square(5);      // 编译期计算
    constexpr auto fib10 = fibonacci(10);
    std::cout << "square(5) = " << sq << " (编译期计算)\n";
    std::cout << "fibonacci(10) = " << fib10 << " (编译期计算)\n";

    // square(运行时变量) 会编译错误
    int runtime_val = 5;
    // auto s = square(runtime_val);  // 错误！consteval 必须编译期求值
    std::cout << "square(运行时变量) 不允许编译（consteval 要求）\n\n";

    // 2. constexpr vs consteval
    std::cout << "【2. constexpr vs consteval】\n";
    constexpr auto ce1 = compile_or_runtime(5);   // 编译期 OK
    auto ce2 = compile_or_runtime(5);              // 运行期也 OK
    constexpr auto co1 = compile_only(5);          // 编译期 OK
    // auto co2 = compile_only(runtime_val);       // 错误！运行期不行
    std::cout << "constexpr: 编译期(" << ce1 << ") 运行期(" << ce2 << ")\n";
    std::cout << "consteval: 编译期(" << co1 << ") 运行期(不允许)\n\n";

    // 3. consteval 用于数组大小
    std::cout << "【3. consteval 定义数组大小】\n";
    constexpr auto arr_size = make_array_size();
    std::array<int, arr_size> arr{};
    std::cout << "数组大小 = " << arr.size() << " (编译期确定)\n\n";

    // 4. consteval 函数 - 无运行时开销
    std::cout << "【4. 编译期哈希】\n";
    constexpr auto hash_hello = fnv1a_hash("hello");
    constexpr auto hash_world = fnv1a_hash("world");
    std::cout << "hash(\"hello\") = " << hash_hello << "\n";
    std::cout << "hash(\"world\") = " << hash_world << "\n\n";

    // 5. constinit 基础
    std::cout << "【5. constinit - 编译期初始化】\n";
    std::cout << "global_value = " << global_value << "\n";
    std::cout << "global_str = " << global_str << "\n";
    std::cout << "global_config = {max_conn=" << global_config.max_connections
              << ", timeout=" << global_config.timeout_ms << "}\n\n";

    // 6. constinit 可变性
    std::cout << "【6. constinit 可修改（非 const）】\n";
    std::cout << "修改前 mutable_global = " << mutable_global << "\n";
    update_global();
    std::cout << "修改后 mutable_global = " << mutable_global << "\n\n";

    // 7. BUFFER_SIZE
    std::cout << "【7. 编译期计算缓冲区】\n";
    std::cout << "BUFFER_SIZE = " << BUFFER_SIZE << " (2^10 = 1024)\n";
    std::cout << "global_buffer.size() = " << global_buffer.size() << "\n\n";

    // 8. 总结对比
    std::cout << "【8. 总结对比】\n";
    std::cout << "+-------------+----------------+----------------+\n";
    std::cout << "| 特性        | 编译期求值     | 运行期求值     |\n";
    std::cout << "+-------------+----------------+----------------+\n";
    std::cout << "| constexpr   | 可以           | 可以           |\n";
    std::cout << "| consteval   | 必须           | 不允许         |\n";
    std::cout << "| constinit   | 必须初始化     | 可修改         |\n";
    std::cout << "+-------------+----------------+----------------+\n";

    std::cout << "\n=== consteval/constinit 示例完成 ===\n";
    return 0;
}
