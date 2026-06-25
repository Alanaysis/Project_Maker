/**
 * @file 02_specialization.cpp
 * @brief 模板特化陷阱示例
 *
 * 模板特化陷阱：特化使用不当导致意外行为
 * 危害：调用错误版本、编译错误、链接错误
 */

#include <iostream>
#include <string>
#include <vector>
#include <type_traits>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：特化顺序错误
 *
 * 问题：特化必须在使用之前声明
 */
template <typename T>
void bad_order(T value) {
    std::cout << "通用版本: " << value << std::endl;
}

// 如果在使用之后特化，可能导致链接错误
template <>
void bad_order<int>(int value) {
    std::cout << "int 特化: " << value << std::endl;
}

/**
 * 错误示例 2：部分特化函数模板
 *
 * 问题：函数模板不支持部分特化
 */
template <typename T, typename U>
void bad_partial(T a, U b) {
    std::cout << "通用版本" << std::endl;
}

// 错误！函数模板不支持部分特化
// template <typename T>
// void bad_partial<T, int>(T a, int b) {
//     std::cout << "部分特化" << std::endl;
// }

/**
 * 错误示例 3：特化与重载混淆
 *
 * 问题：特化和重载的解析规则不同
 */
template <typename T>
void bad_overload(T value) {
    std::cout << "模板版本: " << value << std::endl;
}

// 这是重载，不是特化
void bad_overload(int value) {
    std::cout << "非模板版本: " << value << std::endl;
}

template <>
void bad_overload<double>(double value) {
    std::cout << "double 特化: " << value << std::endl;
}

/**
 * 错误示例 4：特化类模板的成员函数
 *
 * 问题：特化整个类时需要重新定义所有成员
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
protected:
    std::vector<T> data_;
};

// 特化 bool 类型
template <>
class BadContainer<bool> {
public:
    void add(bool value) { data_.push_back(value); }
    // 忘记定义 print()，导致编译错误
protected:
    std::vector<bool> data_;
};

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：正确顺序的特化
 *
 * 解决方案：先声明通用模板，再特化
 */
template <typename T>
void good_order(T value) {
    std::cout << "通用版本: " << value << std::endl;
}

// 特化在使用之前
template <>
void good_order<int>(int value) {
    std::cout << "int 特化: " << value << std::endl;
}

/**
 * 正确示例 2：使用重载代替函数特化
 *
 * 解决方案：函数模板使用重载而非特化
 */
template <typename T>
void good_overload(T value) {
    std::cout << "模板版本: " << value << std::endl;
}

// 重载而非特化
void good_overload(int value) {
    std::cout << "int 重载: " << value << std::endl;
}

/**
 * 正确示例 3：使用标签分发
 *
 * 解决方案：使用标签分发实现部分特化效果
 */
struct IntTag {};
struct DoubleTag {};
struct StringTag {};

template <typename T>
struct Tag {
    using type = void;  // 默认标签
};

template <>
struct Tag<int> {
    using type = IntTag;
};

template <>
struct Tag<double> {
    using type = DoubleTag;
};

template <>
struct Tag<std::string> {
    using type = StringTag;
};

void good_dispatch(int value, IntTag) {
    std::cout << "int 版本: " << value << std::endl;
}

void good_dispatch(double value, DoubleTag) {
    std::cout << "double 版本: " << value << std::endl;
}

void good_dispatch(const std::string& value, StringTag) {
    std::cout << "string 版本: " << value << std::endl;
}

template <typename T>
void good_dispatch(T value) {
    good_dispatch(value, typename Tag<T>::type{});
}

/**
 * 正确示例 4：使用 if constexpr (C++17)
 *
 * 解决方案：使用 if constexpr 实现编译时分支
 */
template <typename T>
void good_if_constexpr(T value) {
    if constexpr (std::is_same_v<T, int>) {
        std::cout << "int 版本: " << value << std::endl;
    } else if constexpr (std::is_same_v<T, double>) {
        std::cout << "double 版本: " << value << std::endl;
    } else if constexpr (std::is_same_v<T, std::string>) {
        std::cout << "string 版本: " << value << std::endl;
    } else {
        std::cout << "通用版本: " << value << std::endl;
    }
}

/**
 * 正确示例 5：特化整个类模板
 *
 * 解决方案：特化时重新定义所有成员
 */
template <typename T>
class GoodContainer {
public:
    void add(const T& value) { data_.push_back(value); }
    void print() const {
        for (const auto& val : data_) {
            std::cout << val << " ";
        }
        std::cout << std::endl;
    }
protected:
    std::vector<T> data_;
};

// 特化 bool 类型，重新定义所有成员
template <>
class GoodContainer<bool> {
public:
    void add(bool value) { data_.push_back(value); }
    void print() const {
        for (const auto& val : data_) {
            std::cout << (val ? "true" : "false") << " ";
        }
        std::cout << std::endl;
    }
protected:
    std::vector<bool> data_;
};

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 模板特化陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 正确顺序的特化" << std::endl;
    good_order(42);
    good_order(3.14);
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用重载代替函数特化" << std::endl;
    good_overload(42);
    good_overload(3.14);
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用标签分发" << std::endl;
    good_dispatch(42);
    good_dispatch(3.14);
    good_dispatch(std::string("hello"));
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 if constexpr" << std::endl;
    good_if_constexpr(42);
    good_if_constexpr(3.14);
    good_if_constexpr(std::string("hello"));
    std::cout << std::endl;

    std::cout << "[正确示例 5] 特化整个类模板" << std::endl;
    GoodContainer<int> int_container;
    int_container.add(1);
    int_container.add(2);
    int_container.print();

    GoodContainer<bool> bool_container;
    bool_container.add(true);
    bool_container.add(false);
    bool_container.print();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
