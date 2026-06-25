/**
 * @file 05_dependent_type.cpp
 * @brief 依赖类型问题示例
 *
 * 依赖类型问题：模板中的依赖类型可能导致解析错误
 * 危害：编译错误、类型推导失败
 */

#include <iostream>
#include <vector>
#include <string>
#include <type_traits>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：缺少 typename
 *
 * 问题：依赖类型需要 typename 关键字
 */
template <typename T>
void bad_missing_typename() {
    // T::iterator 是依赖类型，需要 typename
    // T::iterator it;  // 编译错误
}

/**
 * 错误示例 2：依赖类型作为基类
 *
 * 问题：依赖类型作为基类需要特殊处理
 */
template <typename T>
struct BadBase : T::type {  // 编译错误
    // T::type 是依赖类型
};

/**
 * 错误示例 3：依赖类型在模板参数中
 *
 * 问题：依赖类型作为模板参数需要 typename
 */
template <typename T>
void bad_template_param() {
    // std::vector<T::type> vec;  // 编译错误
}

/**
 * 错误示例 4：嵌套依赖类型
 *
 * 问题：嵌套的依赖类型更复杂
 */
template <typename T>
void bad_nested_dependent() {
    // T::template Inner<int> obj;  // 需要 template 关键字
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用 typename
 *
 * 解决方案：使用 typename 关键字
 */
template <typename T>
void good_typename() {
    typename T::iterator it;  // 正确：使用 typename
    std::cout << "使用 typename" << std::endl;
}

/**
 * 正确示例 2：使用 typename 定义依赖类型
 *
 * 解决方案：使用 typename 定义依赖类型别名
 */
template <typename T>
void good_typename_alias() {
    using Iterator = typename T::iterator;  // 正确
    std::cout << "使用 typename 定义别名" << std::endl;
}

/**
 * 正确示例 3：使用 template 关键字
 *
 * 解决方案：依赖模板需要 template 关键字
 */
template <typename T>
void good_template_keyword() {
    typename T::template Inner<int> obj;  // 正确：使用 template
    std::cout << "使用 template 关键字" << std::endl;
}

/**
 * 正确示例 4：使用 decltype 和 declval
 *
 * 解决方案：使用 decltype 推导依赖类型
 */
template <typename T>
auto good_decltype() -> decltype(std::declval<T>().begin()) {
    std::cout << "使用 decltype" << std::endl;
    return std::declval<T>().begin();
}

/**
 * 正确示例 5：使用类型萃取
 *
 * 解决方案：使用 type_traits 获取类型信息
 */
template <typename T>
void good_type_traits() {
    using ValueType = typename T::value_type;  // 正确
    std::cout << "值类型" << std::endl;
}

/**
 * 正确示例 6：使用 concepts (C++20)
 *
 * 解决方案：使用 concepts 简化依赖类型约束
 */
#if __cplusplus >= 202002L
#include <concepts>

template <typename T>
concept HasIterator = requires {
    typename T::iterator;
    typename T::value_type;
};

template <HasIterator T>
void good_concepts() {
    typename T::iterator it;  // 安全：concepts 已检查
    std::cout << "使用 concepts" << std::endl;
}
#endif

/**
 * 正确示例 7：使用 auto 简化
 *
 * 解决方案：使用 auto 自动推导类型
 */
template <typename T>
void good_auto(const T& container) {
    auto it = container.begin();  // 自动推导类型
    std::cout << "使用 auto" << std::endl;
}

// ============================================================================
// 辅助类
// ============================================================================

struct MyContainer {
    using iterator = int*;
    using value_type = int;

    template <typename U>
    struct Inner {
        U value;
    };

    int* begin() { return nullptr; }
    int* end() { return nullptr; }
};

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 依赖类型问题示例 ===" << std::endl;
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用 typename" << std::endl;
    good_typename<MyContainer>();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 typename 定义别名" << std::endl;
    good_typename_alias<MyContainer>();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 template 关键字" << std::endl;
    good_template_keyword<MyContainer>();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 decltype" << std::endl;
    good_decltype<MyContainer>();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用类型萃取" << std::endl;
    good_type_traits<MyContainer>();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用 auto" << std::endl;
    std::vector<int> vec = {1, 2, 3};
    good_auto(vec);
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
