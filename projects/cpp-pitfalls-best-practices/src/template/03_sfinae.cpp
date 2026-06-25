/**
 * @file 03_sfinae.cpp
 * @brief SFINAE 陷阱示例
 *
 * SFINAE (Substitution Failure Is Not An Error)：替换失败不是错误
 * 危害：难以调试的编译错误、意外的重载决议
 */

#include <iostream>
#include <type_traits>
#include <vector>
#include <string>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：SFINAE 失败导致意外行为
 *
 * 问题：SFINAE 失败时，函数被静默移除
 */
template <typename T>
typename T::type bad_sfinae(T value) {
    return value;
}

// 如果 T 没有 type 成员，这个函数被移除
// 调用 bad_sfinae(42) 会链接错误

/**
 * 错误示例 2：复杂的 SFINAE 表达式
 *
 * 问题：复杂的 SFINAE 表达式难以理解和维护
 */
template <typename T>
auto bad_complex_sfinae(T value) -> decltype(std::declval<T>() + std::declval<T>()) {
    return value + value;
}

/**
 * 错误示例 3：SFINAE 与重载冲突
 *
 * 问题：多个 SFINAE 约束的重载可能冲突
 */
template <typename T>
typename std::enable_if<std::is_integral<T>::value, void>::type
bad_overload(T value) {
    std::cout << "integral: " << value << std::endl;
}

template <typename T>
typename std::enable_if<std::is_floating_point<T>::value, void>::type
bad_overload(T value) {
    std::cout << "floating: " << value << std::endl;
}

// 没有处理其他类型的情况

/**
 * 错误示例 4：SFINAE 在类模板中的问题
 *
 * 问题：类模板的 SFINAE 需要额外技巧
 */
template <typename T, typename Enable = void>
class BadProcessor {
public:
    void process(const T& value) {
        std::cout << "通用处理: " << value << std::endl;
    }
};

// 特化版本
template <typename T>
class BadProcessor<T, typename std::enable_if<std::is_arithmetic<T>::value>::type> {
public:
    void process(const T& value) {
        std::cout << "算术处理: " << value << std::endl;
    }
};

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用 void_t 简化 SFINAE
 *
 * 解决方案：使用 void_t 简化类型检查
 */
template <typename T, typename = void>
struct has_size : std::false_type {};

template <typename T>
struct has_size<T, std::void_t<decltype(std::declval<T>().size())>> : std::true_type {};

template <typename T>
typename std::enable_if<has_size<T>::value, size_t>::type
good_get_size(const T& container) {
    return container.size();
}

/**
 * 正确示例 2：使用 concepts (C++20)
 *
 * 解决方案：使用 concepts 提供更清晰的约束
 */
#if __cplusplus >= 202002L
#include <concepts>

template <typename T>
concept Addable = requires(T a, T b) {
    { a + b } -> std::convertible_to<T>;
};

template <Addable T>
T good_add(T a, T b) {
    return a + b;
}
#else
// C++17 替代方案
template <typename T>
auto good_add(T a, T b) -> decltype(a + b) {
    return a + b;
}
#endif

/**
 * 正确示例 3：使用 constexpr if (C++17)
 *
 * 解决方案：使用 constexpr if 替代 SFINAE
 */
template <typename T>
void good_process(T value) {
    if constexpr (std::is_arithmetic_v<T>) {
        std::cout << "算术类型: " << value << std::endl;
    } else if constexpr (std::is_same_v<T, std::string>) {
        std::cout << "字符串: " << value << std::endl;
    } else {
        std::cout << "其他类型" << std::endl;
    }
}

/**
 * 正确示例 4：使用标签分发
 *
 * 解决方案：使用标签分发替代 SFINAE
 */
struct ArithmeticTag {};
struct StringTag {};
struct OtherTag {};

template <typename T>
struct TypeTag {
    using type = OtherTag;
};

template <>
struct TypeTag<int> {
    using type = ArithmeticTag;
};

template <>
struct TypeTag<double> {
    using type = ArithmeticTag;
};

template <>
struct TypeTag<std::string> {
    using type = StringTag;
};

void good_dispatch_impl(int value, ArithmeticTag) {
    std::cout << "算术类型: " << value << std::endl;
}

void good_dispatch_impl(double value, ArithmeticTag) {
    std::cout << "算术类型: " << value << std::endl;
}

void good_dispatch_impl(const std::string& value, StringTag) {
    std::cout << "字符串: " << value << std::endl;
}

template <typename T>
void good_dispatch(T value) {
    good_dispatch_impl(value, typename TypeTag<T>::type{});
}

/**
 * 正确示例 5：使用类型萃取
 *
 * 解决方案：使用 type_traits 进行类型检查
 */
template <typename T>
void good_type_check(T value) {
    if constexpr (std::is_pointer_v<T>) {
        std::cout << "指针类型" << std::endl;
    } else if constexpr (std::is_reference_v<T>) {
        std::cout << "引用类型" << std::endl;
    } else {
        std::cout << "值类型" << std::endl;
    }
}

/**
 * 正确示例 6：使用 std::invoke (C++17)
 *
 * 解决方案：使用 std::invoke 统一调用
 */
#include <functional>

template <typename F, typename... Args>
auto good_invoke(F&& f, Args&&... args) -> decltype(std::invoke(std::forward<F>(f), std::forward<Args>(args)...)) {
    return std::invoke(std::forward<F>(f), std::forward<Args>(args)...);
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== SFINAE 陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用 void_t 简化 SFINAE" << std::endl;
    std::vector<int> vec = {1, 2, 3};
    std::cout << "size: " << good_get_size(vec) << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 concepts/decltype" << std::endl;
    std::cout << "a + b = " << good_add(1, 2) << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 constexpr if" << std::endl;
    good_process(42);
    good_process(3.14);
    good_process(std::string("hello"));
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用标签分发" << std::endl;
    good_dispatch(42);
    good_dispatch(3.14);
    good_dispatch(std::string("hello"));
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用类型萃取" << std::endl;
    int val = 42;
    good_type_check(val);
    good_type_check(&val);
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用 std::invoke" << std::endl;
    auto lambda = [](int x) { return x * 2; };
    std::cout << "invoke: " << good_invoke(lambda, 21) << std::endl;
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
