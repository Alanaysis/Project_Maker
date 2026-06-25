/**
 * if_constexpr.cpp - constexpr if 条件编译
 *
 * 编译命令: g++ -std=c++17 -o if_constexpr if_constexpr.cpp
 *
 * C++17 引入的 if constexpr 是模板编程的革命性特性。
 * 与普通 if 不同，if constexpr 的条件必须是编译期常量表达式，
 * 编译器会根据条件丢弃不满足条件的分支代码。
 *
 * 主要优势:
 *   1. 替代 SFINAE，代码更清晰
 *   2. 简化递归模板的终止条件
 *   3. 实现类型相关的代码路径
 *   4. 消除编译错误（未选择的分支不参与编译）
 *
 * 重要区别:
 *   - 普通 if: 两个分支都编译，运行时选择
 *   - if constexpr: 只编译选择的分支，不满足的分支被丢弃
 */

#include <iostream>
#include <string>
#include <vector>
#include <type_traits>
#include <sstream>
#include <memory>
#include <array>
#include <cmath>
#include <cstring>

// ============================================================================
// 第一部分: 类型相关的代码路径
// ============================================================================

/**
 * 根据类型执行不同的操作
 *
 * 这是 if constexpr 最常见的用途之一:
 * 根据模板参数的类型，在编译时选择不同的代码路径。
 *
 * 传统方式需要为每种类型编写特化版本，现在可以用一个函数处理。
 */
template<typename T>
std::string to_string_custom(const T& value) {
    if constexpr (std::is_arithmetic_v<T>) {
        // 算术类型 (int, float, double 等): 直接转换
        return std::to_string(value);
    } else if constexpr (std::is_same_v<T, std::string>) {
        // std::string 类型: 直接返回
        return value;
    } else if constexpr (std::is_same_v<T, bool>) {
        // bool 类型: 返回 "true" 或 "false"
        return value ? "true" : "false";
    } else if constexpr (std::is_pointer_v<T>) {
        // 指针类型: 返回地址字符串
        std::ostringstream oss;
        oss << reinterpret_cast<const void*>(value);
        return oss.str();
    } else {
        // 其他类型: 使用 typeid 获取类型名
        return std::string("[") + typeid(T).name() + "]";
    }
}

/**
 * 根据类型计算大小
 *
 * 展示如何对不同类型的容器使用不同的大小计算方式。
 * 使用 void_t 技巧检测类型是否有 size() 成员函数。
 */

// SFINAE 辅助: 检测类型是否有 size() 成员
template<typename T, typename = void>
struct has_size_method : std::false_type {};

template<typename T>
struct has_size_method<T, std::void_t<decltype(std::declval<const T&>().size())>>
    : std::true_type {};

template<typename T>
size_t get_size(const T& container) {
    if constexpr (std::is_array_v<T>) {
        // C 风格数组: 使用 sizeof 计算
        return sizeof(T) / sizeof(T[0]);
    } else if constexpr (std::is_same_v<T, std::string>) {
        // string: 使用 size() 成员函数
        return container.size();
    } else if constexpr (has_size_method<T>::value) {
        // 有 size() 成员的容器 (vector, array, map 等)
        return container.size();
    } else {
        // 其他类型: 返回 1
        return 1;
    }
}

// ============================================================================
// 第二部分: 可变参数模板终止条件
// ============================================================================

/**
 * if constexpr 终止递归
 *
 * 在 C++17 之前，可变参数模板的递归需要一个"终止函数"。
 * 使用 if constexpr，可以在同一个函数中处理终止条件，无需额外函数。
 *
 * 这是 if constexpr 最优雅的用途之一。
 */

// C++17 之前需要两个函数:
// void print_old() { }  // 终止函数
// template<typename T, typename... Args>
// void print_old(T first, Args... rest) {
//     std::cout << first;
//     if (sizeof...(rest) > 0) std::cout << ", ";
//     print_old(rest...);  // 递归调用
// }

// C++17 使用 if constexpr 只需一个函数:
template<typename T, typename... Args>
void print(T&& first, Args&&... rest) {
    std::cout << std::forward<T>(first);

    if constexpr (sizeof...(rest) > 0) {
        // 只有当参数包非空时，这个分支才会被编译
        std::cout << ", ";
        print(std::forward<Args>(rest)...);
    } else {
        // 参数包为空时，结束递归
        std::cout << std::endl;
    }
}

/**
 * 编译期求和: 使用 if constexpr 终止递归
 */
template<typename T, typename... Args>
auto sum(T first, Args... rest) {
    if constexpr (sizeof...(rest) == 0) {
        // 基本情况: 只有一个参数
        return first;
    } else {
        // 递归情况: first + sum(rest...)
        return first + sum(rest...);
    }
}

/**
 * 编译期最大值: 使用 if constexpr
 */
template<typename T, typename... Args>
T max_value(T first, Args... rest) {
    if constexpr (sizeof...(rest) == 0) {
        return first;
    } else {
        T rest_max = max_value(rest...);
        return (first > rest_max) ? first : rest_max;
    }
}

/**
 * 编译期检查所有参数是否相等
 */
template<typename T, typename... Args>
bool all_equal(T first, Args... rest) {
    if constexpr (sizeof...(rest) == 0) {
        return true;  // 只有一个元素，trivially equal
    } else {
        // 折叠表达式: 检查 first 是否等于 rest 中的每个元素
        return ((first == rest) && ...);
    }
}

// ============================================================================
// 第三部分: SFINAE 替代
// ============================================================================

/**
 * 传统 SFINAE 方式 (C++11/14) - 复杂难读
 *
 * SFINAE (Substitution Failure Is Not An Error) 是 C++ 模板匹配的核心机制。
 * 利用 SFINAE 可以在编译期检测类型是否具有某些特性。
 * 但 SFINAE 语法复杂，错误信息难读。
 *
 * 下面展示传统 SFINAE 和 if constexpr 的对比。
 */

// 传统 SFINAE 版本 - 使用 std::enable_if
// 只有当 T 有 size() 成员函数时才启用
template<typename T>
auto get_size_sfinae(T& container) ->
    typename std::enable_if<
        !std::is_same_v<T, std::string>,
        size_t
    >::type {
    return container.size();
}

// 对 string 类型的特化
template<typename T>
auto get_size_sfinae(T& str) ->
    typename std::enable_if<
        std::is_same_v<T, std::string>,
        size_t
    >::type {
    return str.length();
}

/**
 * if constexpr 版本 - 简洁清晰
 *
 * 使用 if constexpr 替代 SFINAE，代码更易读:
 *   - 不需要 enable_if 和复杂的返回类型
 *   - 不需要为每种情况编写不同的函数签名
 *   - 错误信息更友好
 */
template<typename T>
size_t get_size_if_constexpr(const T& container) {
    if constexpr (std::is_same_v<T, std::string>) {
        return container.length();
    } else {
        return container.size();
    }
}

/**
 * 检测类型是否有特定成员函数
 *
 * 在 C++17 中，使用 void_t 技巧检测类型特性。
 * 这是 C++20 concepts 的前身，展示了从 SFINAE 到 concepts 的演进。
 */

// SFINAE 辅助: 检测类型是否有 to_string() 成员函数
template<typename T, typename = void>
struct has_to_string : std::false_type {};

template<typename T>
struct has_to_string<T, std::void_t<decltype(std::declval<const T&>().to_string())>>
    : std::true_type {};

/**
 * 使用 if constexpr 处理不同特性的类型
 *
 * 通过 SFINAE 辅助类型在编译期检测类型特性，
 * 结合 if constexpr 实现类型相关的代码路径。
 */
template<typename T>
std::string describe(const T& obj) {
    if constexpr (has_to_string<T>::value) {
        // 类型有 to_string() 成员函数
        return obj.to_string();
    } else if constexpr (std::is_arithmetic_v<T>) {
        // 算术类型: 使用 std::to_string
        return "数值: " + std::to_string(obj);
    } else {
        // 其他类型
        return "未知类型";
    }
}

// ============================================================================
// 第四部分: 编译期配置与优化
// ============================================================================

/**
 * 编译期调试开关
 *
 * 使用 if constexpr 可以在编译时完全移除调试代码，
 * 而不是依赖运行时检查或预处理器宏。
 */
enum class LogLevel { LOG_DEBUG, LOG_INFO, LOG_WARNING, LOG_ERROR };

template<LogLevel Level>
void log(const std::string& message) {
    if constexpr (Level == LogLevel::LOG_DEBUG) {
        // 只在 DEBUG 级别编译此代码
        std::cout << "[DEBUG] " << message << std::endl;
    } else if constexpr (Level == LogLevel::LOG_INFO) {
        std::cout << "[INFO] " << message << std::endl;
    } else if constexpr (Level == LogLevel::LOG_WARNING) {
        std::cout << "[WARNING] " << message << std::endl;
    } else if constexpr (Level == LogLevel::LOG_ERROR) {
        std::cerr << "[ERROR] " << message << std::endl;
    }
}

/**
 * 编译期优化选择
 *
 * 根据类型特征选择不同的算法实现。
 * 例如: 对 POD 类型使用 memcpy，对非 POD 类型使用逐元素拷贝。
 */
template<typename T>
void optimized_copy(const T* src, T* dst, size_t count) {
    if constexpr (std::is_trivially_copyable_v<T>) {
        // POD 类型: 使用 memcpy，编译器可以高度优化
        std::cout << "  使用 memcpy 优化拷贝 (POD 类型)" << std::endl;
        std::memcpy(dst, src, count * sizeof(T));
    } else {
        // 非 POD 类型: 使用逐元素拷贝构造
        std::cout << "  使用逐元素拷贝构造 (非 POD 类型)" << std::endl;
        for (size_t i = 0; i < count; ++i) {
            new (&dst[i]) T(src[i]);
        }
    }
}

// ============================================================================
// 第五部分: 模板特化替代
// ============================================================================

/**
 * 使用 if constexpr 替代模板特化
 *
 * 传统方式: 为每种类型编写单独的特化版本
 * if constexpr: 在一个函数中处理所有情况
 *
 * 展示二者的对比。
 */

// 传统特化方式 - 需要多个版本
template<typename T>
struct SerializerOld;

template<>
struct SerializerOld<int> {
    static std::string serialize(int val) { return "i:" + std::to_string(val); }
};

template<>
struct SerializerOld<double> {
    static std::string serialize(double val) { return "d:" + std::to_string(val); }
};

template<>
struct SerializerOld<std::string> {
    static std::string serialize(const std::string& val) { return "s:" + val; }
};

// if constexpr 方式 - 单一函数处理所有类型
template<typename T>
std::string serialize(const T& value) {
    if constexpr (std::is_same_v<T, int>) {
        return "i:" + std::to_string(value);
    } else if constexpr (std::is_same_v<T, double>) {
        return "d:" + std::to_string(value);
    } else if constexpr (std::is_same_v<T, std::string>) {
        return "s:" + value;
    } else if constexpr (std::is_same_v<T, bool>) {
        return "b:" + std::string(value ? "true" : "false");
    } else if constexpr (std::is_arithmetic_v<T>) {
        // 通用算术类型
        return "n:" + std::to_string(value);
    } else {
        // 不支持的类型，触发编译错误
        static_assert(std::is_arithmetic_v<T> || std::is_same_v<T, std::string>,
                      "不支持的序列化类型");
        return "";
    }
}

/**
 * 多态处理器: 使用 if constexpr 处理不同维度
 */
template<size_t Dimensions>
struct GeometryProcessor {
    static void process() {
        if constexpr (Dimensions == 1) {
            std::cout << "处理 1D: 线段/点" << std::endl;
        } else if constexpr (Dimensions == 2) {
            std::cout << "处理 2D: 三角形/矩形/圆" << std::endl;
        } else if constexpr (Dimensions == 3) {
            std::cout << "处理 3D: 四面体/立方体/球体" << std::endl;
        } else {
            std::cout << "处理 " << Dimensions << "D: 高维几何体" << std::endl;
        }
    }
};

// ============================================================================
// 第六部分: 综合示例
// ============================================================================

/**
 * 通用打印函数: 处理各种可打印类型
 */
template<typename T>
void smart_print(const T& value) {
    if constexpr (std::is_same_v<T, std::string>) {
        std::cout << "\"" << value << "\"";
    } else if constexpr (std::is_same_v<T, char>) {
        std::cout << "'" << value << "'";
    } else if constexpr (std::is_same_v<T, bool>) {
        std::cout << (value ? "true" : "false");
    } else if constexpr (std::is_arithmetic_v<T>) {
        std::cout << value;
    } else if constexpr (std::is_pointer_v<T>) {
        if (value) {
            std::cout << "0x" << std::hex << reinterpret_cast<uintptr_t>(value) << std::dec;
        } else {
            std::cout << "nullptr";
        }
    } else {
        std::cout << "[" << typeid(T).name() << "]";
    }
}

/**
 * 安全除法: 使用 if constexpr 处理不同数值类型
 */
template<typename T>
auto safe_divide(T a, T b) {
    if constexpr (std::is_floating_point_v<T>) {
        // 浮点数: 检查除以零
        if (std::abs(b) < std::numeric_limits<T>::epsilon()) {
            std::cout << "  [警告] 浮点除以接近零的值" << std::endl;
        }
        return a / b;
    } else if constexpr (std::is_integral_v<T>) {
        // 整数: 检查除以零
        if (b == 0) {
            std::cout << "  [错误] 整数除以零，返回 0" << std::endl;
            return T{0};
        }
        return a / b;
    }
}

// ============================================================================
// 主函数: 演示所有功能
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  if constexpr 条件编译演示" << std::endl;
    std::cout << "========================================" << std::endl;

    // --- 1. 类型相关的代码路径 ---
    std::cout << "\n--- 1. 类型相关的代码路径 ---" << std::endl;
    std::cout << "int(42): " << to_string_custom(42) << std::endl;
    std::cout << "double(3.14): " << to_string_custom(3.14) << std::endl;
    std::cout << "bool(true): " << to_string_custom(true) << std::endl;
    std::cout << "string(\"hello\"): " << to_string_custom(std::string("hello")) << std::endl;
    int x = 42;
    std::cout << "pointer(&x): " << to_string_custom(&x) << std::endl;

    // --- 2. 递归终止 ---
    std::cout << "\n--- 2. 可变参数递归终止 ---" << std::endl;
    std::cout << "print: ";
    print(1, 2.5, "hello", 'A', true);

    std::cout << "sum(1,2,3,4,5): " << sum(1, 2, 3, 4, 5) << std::endl;
    std::cout << "max(3,7,2,9,1): " << max_value(3, 7, 2, 9, 1) << std::endl;
    std::cout << "all_equal(1,1,1): " << std::boolalpha << all_equal(1, 1, 1) << std::endl;
    std::cout << "all_equal(1,2,1): " << std::boolalpha << all_equal(1, 2, 1) << std::endl;

    // --- 3. SFINAE 替代 ---
    std::cout << "\n--- 3. SFINAE 替代 ---" << std::endl;
    std::vector<int> vec = {1, 2, 3, 4, 5};
    std::string str = "Hello";

    std::cout << "vector size (if constexpr): " << get_size_if_constexpr(vec) << std::endl;
    std::cout << "string size (if constexpr): " << get_size_if_constexpr(str) << std::endl;

    // --- 4. 类型特性检测 ---
    std::cout << "\n--- 4. 类型特性检测 ---" << std::endl;
    std::cout << "describe(42): " << describe(42) << std::endl;
    std::cout << "describe(3.14): " << describe(3.14) << std::endl;

    // --- 5. 编译期配置 ---
    std::cout << "\n--- 5. 编译期配置 ---" << std::endl;
    log<LogLevel::LOG_DEBUG>("调试信息: 变量 x = 42");
    log<LogLevel::LOG_INFO>("系统启动完成");
    log<LogLevel::LOG_WARNING>("内存使用率 85%");
    log<LogLevel::LOG_ERROR>("连接超时");

    // --- 6. 优化选择 ---
    std::cout << "\n--- 6. 编译期优化选择 ---" << std::endl;
    int src_int[] = {1, 2, 3, 4, 5};
    int dst_int[5];
    std::cout << "拷贝 int 数组:" << std::endl;
    optimized_copy(src_int, dst_int, 5);

    struct NonTrivial {
        std::string s;
        NonTrivial(const std::string& str) : s(str) {}
        NonTrivial(const NonTrivial& other) : s(other.s) {
            std::cout << "    调用拷贝构造: " << s << std::endl;
        }
    };
    NonTrivial src_nt[] = {NonTrivial("a"), NonTrivial("b")};
    NonTrivial dst_nt[] = {NonTrivial(""), NonTrivial("")};
    std::cout << "拷贝 NonTrivial 数组:" << std::endl;
    optimized_copy(src_nt, dst_nt, 2);

    // --- 7. 序列化 ---
    std::cout << "\n--- 7. 模板特化替代 ---" << std::endl;
    std::cout << "serialize(42): " << serialize(42) << std::endl;
    std::cout << "serialize(3.14): " << serialize(3.14) << std::endl;
    std::cout << "serialize(\"hello\"): " << serialize(std::string("hello")) << std::endl;
    std::cout << "serialize(true): " << serialize(true) << std::endl;
    std::cout << "serialize('A'): " << serialize('A') << std::endl;

    // --- 8. 几何处理 ---
    std::cout << "\n--- 8. 维度相关的处理 ---" << std::endl;
    GeometryProcessor<1>::process();
    GeometryProcessor<2>::process();
    GeometryProcessor<3>::process();

    // --- 9. 智能打印 ---
    std::cout << "\n--- 9. 智能打印 ---" << std::endl;
    std::cout << "smart_print(42): ";
    smart_print(42);
    std::cout << std::endl;
    std::cout << "smart_print(\"hello\"): ";
    smart_print(std::string("hello"));
    std::cout << std::endl;
    std::cout << "smart_print(true): ";
    smart_print(true);
    std::cout << std::endl;
    std::cout << "smart_print(nullptr): ";
    smart_print(nullptr);
    std::cout << std::endl;

    // --- 10. 安全除法 ---
    std::cout << "\n--- 10. 安全除法 ---" << std::endl;
    std::cout << "10 / 3 (int): " << safe_divide(10, 3) << std::endl;
    std::cout << "10.0 / 3.0 (double): " << safe_divide(10.0, 3.0) << std::endl;
    std::cout << "10 / 0 (int): " << safe_divide(10, 0) << std::endl;

    std::cout << "\n========================================" << std::endl;
    std::cout << "  演示结束" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
