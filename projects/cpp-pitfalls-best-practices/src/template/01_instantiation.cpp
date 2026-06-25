/**
 * @file 01_instantiation.cpp
 * @brief 模板实例化陷阱示例
 *
 * 模板实例化问题：模板代码在实例化时才检查，可能导致延迟错误
 * 危害：编译错误难以理解、代码膨胀、链接错误
 */

#include <iostream>
#include <vector>
#include <string>
#include <type_traits>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：模板中使用不存在的成员
 *
 * 问题：模板定义时不检查，实例化时才报错
 */
template <typename T>
void bad_print_size(const T& container) {
    // 如果 T 没有 size() 方法，实例化时才报错
    std::cout << container.size() << std::endl;
}

/**
 * 错误示例 2：模板中使用不支持的操作
 *
 * 问题：某些类型可能不支持模板中的操作
 */
template <typename T>
T bad_add(const T& a, const T& b) {
    return a + b;  // 如果 T 不支持 + 运算符，实例化时才报错
}

/**
 * 错误示例 3：模板特化顺序错误
 *
 * 问题：特化必须在使用之前声明
 */
template <typename T>
void bad_order(T value) {
    std::cout << "通用版本: " << value << std::endl;
}

// 特化在使用之后，可能导致链接错误
template <>
void bad_order<int>(int value) {
    std::cout << "int 特化: " << value << std::endl;
}

/**
 * 错误示例 4：隐式实例化导致代码膨胀
 *
 * 问题：每个类型都生成一份代码
 */
template <typename T>
class BadContainer {
public:
    void add(const T& value) { data_.push_back(value); }
    void print() const {
        for (const auto& val : data_) {
            std::cout << val << " ";
        }
        std::cout << std::endl;
    }
private:
    std::vector<T> data_;
};

// 每种类型都生成一份代码
// BadContainer<int> 和 BadContainer<double> 有相同的 print 逻辑

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用 concepts (C++20) 约束模板
 *
 * 解决方案：使用 concepts 在编译时检查类型要求
 */
#if __cplusplus >= 202002L
#include <concepts>

template <typename T>
concept HasSize = requires(T t) {
    { t.size() } -> std::convertible_to<size_t>;
};

template <HasSize T>
void good_print_size(const T& container) {
    std::cout << container.size() << std::endl;
}
#else
// C++17 替代方案：使用 SFINAE
template <typename T, typename = decltype(std::declval<T>().size())>
void good_print_size(const T& container) {
    std::cout << container.size() << std::endl;
}
#endif

/**
 * 正确示例 2：使用 SFINAE 检查类型支持
 *
 * 解决方案：使用 SFINAE 在编译时检查类型是否支持操作
 */
template <typename T, typename = void>
struct supports_add : std::false_type {};

template <typename T>
struct supports_add<T, std::void_t<decltype(std::declval<T>() + std::declval<T>())>>
    : std::true_type {};

template <typename T>
typename std::enable_if<supports_add<T>::value, T>::type
good_add(const T& a, const T& b) {
    return a + b;
}

/**
 * 正确示例 3：使用类型萃取检查
 *
 * 解决方案：使用 type_traits 检查类型特性
 */
template <typename T>
void good_process(const T& value) {
    if constexpr (std::is_arithmetic_v<T>) {
        std::cout << "算术类型: " << value << std::endl;
    } else if constexpr (std::is_same_v<T, std::string>) {
        std::cout << "字符串: " << value << std::endl;
    } else {
        std::cout << "其他类型" << std::endl;
    }
}

/**
 * 正确示例 4：使用 CRTP 避免代码膨胀
 *
 * 解决方案：使用 CRTP 共享实现
 */
template <typename Derived>
class GoodContainerBase {
public:
    void print() const {
        const auto& derived = static_cast<const Derived&>(*this);
        for (const auto& val : derived.data()) {
            std::cout << val << " ";
        }
        std::cout << std::endl;
    }
};

template <typename T>
class GoodContainer : public GoodContainerBase<GoodContainer<T>> {
public:
    void add(const T& value) { data_.push_back(value); }
    const std::vector<T>& data() const { return data_; }
private:
    std::vector<T> data_;
};

/**
 * 正确示例 5：使用 extern template 减少实例化
 *
 * 解决方案：extern template 声明，延迟实例化
 */
// 在头文件中声明
// extern template class std::vector<int>;

// 在源文件中实例化
// template class std::vector<int>;

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 模板实例化陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 模板中使用不存在的成员" << std::endl;
    std::cout << "问题：模板定义时不检查，实例化时才报错" << std::endl;
    // bad_print_size(42);  // 编译错误：int 没有 size()
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用 concepts/SFINAE 约束模板" << std::endl;
    std::vector<int> vec = {1, 2, 3};
    good_print_size(vec);
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 SFINAE 检查类型支持" << std::endl;
    int a = 1, b = 2;
    std::cout << "a + b = " << good_add(a, b) << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用类型萃取检查" << std::endl;
    good_process(42);
    good_process(3.14);
    good_process(std::string("hello"));
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 CRTP 避免代码膨胀" << std::endl;
    GoodContainer<int> container;
    container.add(1);
    container.add(2);
    container.add(3);
    container.print();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
