#pragma once
/**
 * @file visitor.hpp
 * @brief 编译期访问者模式
 *
 * 使用模板元编程实现编译期多态的访问者模式，
 * 避免虚函数调用开销。
 *
 * 包含：
 *   - 类型列表访问者
 *   - variant 访问者
 *   - 编译期 double dispatch
 */

#include <variant>
#include <string>
#include <iostream>
#include <vector>
#include <type_traits>
#include <tuple>
#include <functional>

namespace tmp {

// ============================================================================
// 1. 基于 std::variant 的访问者
// ============================================================================

/**
 * @brief 多态访问者 - 对 std::variant 执行操作
 *
 * 使用方法:
 *   std::variant<int, double, std::string> v = 42;
 *   visit(overloaded{
 *       [](int i) { ... },
 *       [](double d) { ... },
 *       [](const std::string& s) { ... }
 *   }, v);
 */

/**
 * @brief overloaded 辅助类 - 将多个 lambda 合并为一个访问者
 */
template <typename... Ts>
struct overloaded : Ts... {
    using Ts::operator()...;
};

/// @brief C++17 推导指引
template <typename... Ts>
overloaded(Ts...) -> overloaded<Ts...>;

// ============================================================================
// 2. 编译期类型访问者
// ============================================================================

/**
 * @brief 类型列表访问者 - 遍历类型列表并执行操作
 */
template <typename TypeList>
class TypeVisitor;

template <typename... Types>
class TypeVisitor<std::tuple<Types...>> {
public:
    /**
     * @brief 对每个类型执行操作
     */
    template <typename F>
    static void for_each_type(F&& func) {
        (func.template operator()<Types>(), ...);
    }

    /**
     * @brief 查找第一个满足条件的类型
     */
    template <template <typename> class Pred>
    static constexpr bool any_of() {
        return (Pred<Types>::value || ...);
    }

    /**
     * @brief 检查所有类型是否满足条件
     */
    template <template <typename> class Pred>
    static constexpr bool all_of() {
        return (Pred<Types>::value && ...);
    }

    /**
     * @brief 统计满足条件的类型数量
     */
    template <template <typename> class Pred>
    static constexpr std::size_t count_if() {
        return ((Pred<Types>::value ? 1 : 0) + ...);
    }
};

// ============================================================================
// 3. 编译期 Double Dispatch
// ============================================================================

/**
 * @brief 编译期 double dispatch 实现
 * 使用类型对(type pair)在编译期分派到正确的函数
 */
template <typename T1, typename T2>
struct TypePair {
    using first_type = T1;
    using second_type = T2;
};

/**
 * @brief dispatch 表 - 存储类型对到函数的映射
 */
template <typename... Pairs>
class DispatchTable;

template <typename... T1s, typename... T2s>
class DispatchTable<TypePair<T1s, T2s>...> {
    std::tuple<std::function<void()> (*)()> handlers_;

public:
    template <typename T1, typename T2, typename F>
    void register_handler(F&& func) {
        // 编译期注册处理函数
    }
};

// ============================================================================
// 4. 表达式访问者 (AST Visitor)
// ============================================================================

/**
 * @brief AST 节点类型
 */
struct NumberNode {
    double value;
};

// 简化的 AST 节点，避免递归定义问题
struct BinaryExprNode {
    double left;
    double right;
    char op;
};

/**
 * @brief AST 访问者基类
 */
template <typename ReturnType>
class ASTVisitor {
public:
    virtual ~ASTVisitor() = default;
    virtual ReturnType visit(const NumberNode& node) = 0;
    virtual ReturnType visit(const BinaryExprNode& node) = 0;
};

// ============================================================================
// 5. 编译期访问者 - 完全静态分派
// ============================================================================

/**
 * @brief 编译期访问者 - 使用模板递归实现
 * 无需虚函数，完全在编译期解析
 */
template <typename Derived>
class StaticVisitor {
public:
    template <typename Node>
    auto visit(const Node& node) {
        return static_cast<Derived*>(this)->visit_impl(node);
    }
};

/**
 * @brief 求值访问者示例
 */
class EvalVisitor : public StaticVisitor<EvalVisitor> {
public:
    double visit_impl(const NumberNode& node) {
        return node.value;
    }
};

// ============================================================================
// 6. 类型擦除访问者
// ============================================================================

/**
 * @brief 类型擦除的访问者接口
 * 在运行时根据 variant 中存储的类型分派
 */
template <typename ReturnType, typename... Types>
class TypeErasedVisitor {
public:
    virtual ~TypeErasedVisitor() = default;

    ReturnType dispatch(const std::variant<Types...>& v) {
        return std::visit([this](const auto& value) -> ReturnType {
            return this->visit_impl(value);
        }, v);
    }

protected:
    virtual ReturnType visit_impl(const Types&...) = 0;
};

// ============================================================================
// 7. 编译期属性访问者
// ============================================================================

/**
 * @brief 属性收集访问者 - 收集对象的所有属性
 */
template <typename T>
class PropertyCollector {
    std::vector<std::pair<std::string, std::string>> properties_;

public:
    void add_property(const std::string& name, const std::string& value) {
        properties_.emplace_back(name, value);
    }

    void add_property(const std::string& name, const char* value) {
        properties_.emplace_back(name, std::string(value));
    }

    template <typename U>
    std::enable_if_t<std::is_arithmetic_v<U>>
    add_property(const std::string& name, const U& value) {
        properties_.emplace_back(name, std::to_string(value));
    }

    const std::vector<std::pair<std::string, std::string>>&
    get_properties() const {
        return properties_;
    }

    void print() const {
        for (const auto& [name, value] : properties_) {
            std::cout << name << " = " << value << std::endl;
        }
    }
};

// ============================================================================
// 8. 验证访问者
// ============================================================================

/**
 * @brief 验证访问者 - 检查对象状态是否有效
 */
template <typename T>
class ValidationVisitor {
    std::vector<std::string> errors_;

public:
    void add_error(const std::string& error) {
        errors_.push_back(error);
    }

    bool is_valid() const {
        return errors_.empty();
    }

    const std::vector<std::string>& get_errors() const {
        return errors_;
    }

    std::string get_error_message() const {
        std::string result;
        for (const auto& error : errors_) {
            if (!result.empty()) result += "\n";
            result += error;
        }
        return result;
    }
};

}  // namespace tmp
