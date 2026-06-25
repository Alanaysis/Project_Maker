/**
 * concepts.cpp - C++20 概念 (Concepts)
 *
 * 编译命令: g++ -std=c++20 -o concepts concepts.cpp
 *
 * C++20 引入的 Concepts 是对模板约束机制的重大改进。
 * 概念 (Concept) 是一组命名的约束条件，用于限制模板参数必须满足的条件。
 *
 * 核心优势:
 *   1. 清晰的错误信息: 不满足约束时，编译器会指出具体哪个约束失败
 *   2. 代码自文档化: 概念名称直接表达模板参数的要求
 *   3. 重载决议: 概念可以用于选择更特化的模板版本
 *   4. 替代 SFINAE: 比 enable_if 更简洁、更易读
 *
 * 关键语法:
 *   - concept: 定义命名的约束
 *   - requires: 定义约束表达式
 *   - requires clause: 作为模板约束使用
 */

#include <iostream>
#include <string>
#include <vector>
#include <list>
#include <concepts>
#include <type_traits>
#include <iterator>
#include <numeric>
#include <algorithm>
#include <memory>
#include <array>

// ============================================================================
// 第一部分: 基础概念定义
// ============================================================================

/**
 * 定义最简单的概念: 基于类型特征
 *
 * 概念的定义语法:
 *   template<模板参数列表>
 *   concept 概念名 = 约束表达式;
 *
 * 约束表达式必须是一个布尔常量表达式。
 * 可以使用:
 *   - 标准类型特征 (如 std::is_arithmetic_v<T>)
 *   - requires 表达式
 *   - 其他概念的组合
 */

// 概念: 算术类型 (int, float, double 等)
// 使用标准库的类型特征作为约束
template<typename T>
concept Arithmetic = std::is_arithmetic_v<T>;

// 概念: 可以使用 + 运算符的类型
template<typename T>
concept Addable = requires(T a, T b) {
    { a + b } -> std::same_as<T>;  // 结果类型必须与操作数相同
};

// 概念: 可以使用 < 运算符比较的类型
template<typename T>
concept Comparable = requires(const T& a, const T& b) {
    { a < b } -> std::convertible_to<bool>;
};

// 概念: 可以使用 == 运算符比较的类型
template<typename T>
concept EqualityComparable = requires(const T& a, const T& b) {
    { a == b } -> std::convertible_to<bool>;
};

// 概念: 可以转换为字符串的类型
template<typename T>
concept StringConvertible = requires(const T& t) {
    { std::to_string(t) } -> std::same_as<std::string>;
} || std::is_same_v<T, std::string>;

// ============================================================================
// 第二部分: requires 表达式详解
// ============================================================================

/**
 * requires 表达式的三种形式:
 *
 * 1. 简单需求 (Simple requirements):
 *    检查表达式是否有效，不检查表达式的类型
 *    requires(T t) { t.foo(); }
 *
 * 2. 类型需求 (Type requirements):
 *    检查类型是否存在
 *    requires { typename T::value_type; }
 *
 * 3. 复合需求 (Compound requirements):
 *    检查表达式是否有效，且满足类型/异常约束
 *    requires(T t) { { t.size() } -> std::convertible_to<size_t>; }
 *
 * 4. 嵌套需求 (Nested requirements):
 *    在 requires 块中使用概念约束
 *    requires(T t) { requires std::is_same_v<decltype(t), int>; }
 */

// 概念: 有 size() 成员函数
template<typename T>
concept HasSize = requires(const T& t) {
    { t.size() } -> std::convertible_to<size_t>;
};

// 概念: 有 begin() 和 end() 成员函数 (范围)
template<typename T>
concept Range = requires(T& t) {
    { t.begin() } -> std::input_or_output_iterator;
    { t.end() } -> std::input_or_output_iterator;
};

// 概念: 有 push_back() 成员函数 (可动态增长的容器)
template<typename T>
concept HasPushBack = requires(T& t, typename T::value_type v) {
    { t.push_back(v) };
};

// 概念: 有 value_type 类型别名的容器
template<typename T>
concept HasValueType = requires {
    typename T::value_type;
};

// 概念: 可以被打印到输出流
template<typename T>
concept Printable = requires(std::ostream& os, const T& t) {
    { os << t } -> std::same_as<std::ostream&>;
};

// 概念: 智能指针类型
template<typename T>
concept SmartPointer = requires {
    typename T::element_type;
    requires requires(T t) {
        { t.get() } -> std::same_as<typename T::element_type*>;
        { *t } -> std::same_as<typename T::element_type&>;
    };
};

// 概念: 有默认构造函数的类型
template<typename T>
concept DefaultConstructible = requires {
    { T{} };
    { T() };
};

// ============================================================================
// 第三部分: 受约束的模板
// ============================================================================

/**
 * 使用概念约束模板参数
 *
 * 方式一: requires 子句
 *   template<typename T>
 *   requires Concept<T>
 *   void func(T t);
 *
 * 方式二: 简写语法 (C++20)
 *   void func(Concept auto t);
 *
 * 方式三: 约束 auto 参数
 *   void func(Concept auto t);
 */

// 方式一: 使用 requires 子句
template<typename T>
requires Arithmetic<T>
T add_requires(T a, T b) {
    std::cout << "  [requires 子句] ";
    return a + b;
}

// 方式二: 概念作为模板参数约束
template<Arithmetic T>
T add_concept(T a, T b) {
    std::cout << "  [概念约束] ";
    return a + b;
}

// 方式三: 缩写语法 (最简洁)
auto add_short(Arithmetic auto a, Arithmetic auto b) {
    std::cout << "  [缩写语法] ";
    return a + b;
}

/**
 * 受约束的函数: 打印容器
 */
template<Range Container>
void print_container(const Container& c, const std::string& name = "") {
    if (!name.empty()) {
        std::cout << name << ": ";
    }
    std::cout << "[";
    bool first = true;
    for (const auto& elem : c) {
        if (!first) std::cout << ", ";
        std::cout << elem;
        first = false;
    }
    std::cout << "]" << std::endl;
}

/**
 * 受约束的函数: 容器求和
 * 要求容器的元素类型是算术类型
 */
template<Range Container>
    requires Arithmetic<typename Container::value_type>
auto sum_container(const Container& c) {
    using T = typename Container::value_type;
    T result = T{};
    for (const auto& elem : c) {
        result += elem;
    }
    return result;
}

/**
 * 受约束的函数: 在容器中查找元素
 */
template<Range Container>
    requires EqualityComparable<typename Container::value_type>
auto find_in_container(const Container& c, const typename Container::value_type& target) {
    return std::find(c.begin(), c.end(), target);
}

// ============================================================================
// 第四部分: 概念组合与子概念
// ============================================================================

/**
 * 概念的组合:
 *   - 合取 (Conjunction): C1<T> && C2<T>  (两个概念都满足)
 *   - 析取 (Disjunction): C1<T> || C2<T>  (至少一个概念满足)
 *   - 否定 (Negation): !C<T>              (概念不满足)
 */

// 概念: 排序容器 (有 begin/end 且元素可比较)
template<typename T>
concept SortableRange = Range<T> && Comparable<typename T::value_type>;

// 概念: 可求和的容器 (有 begin/end 且元素可加)
template<typename T>
concept SummableRange = Range<T> && Addable<typename T::value_type>;

// 概念: 数值容器 (范围 + 算术元素)
template<typename T>
concept NumericRange = Range<T> && Arithmetic<typename T::value_type>;

// 概念: 可哈希类型 (有 std::hash 特化)
template<typename T>
concept Hashable = requires(const T& t) {
    { std::hash<T>{}(t) } -> std::convertible_to<size_t>;
};

// 概念: 完整的容器操作 (有 size, begin, end, push_back)
template<typename T>
concept FullContainer = HasSize<T> && Range<T> && HasPushBack<T>;

/**
 * 受约束的排序函数
 */
template<SortableRange Container>
void sort_container(Container& c) {
    std::sort(c.begin(), c.end());
}

/**
 * 受约束的求和函数
 */
template<SummableRange Container>
auto range_sum(const Container& c) {
    using T = typename Container::value_type;
    T result = T{};
    for (const auto& elem : c) {
        result = result + elem;
    }
    return result;
}

// ============================================================================
// 第五部分: requires 表达式与 SFINAE 对比
// ============================================================================

/**
 * 展示 SFINAE 和 Concepts 的对比
 *
 * SFINAE 方式 (C++11/14):
 *   template<typename T>
 *   auto func(T t) -> std::enable_if_t<condition, ReturnType>;
 *
 * Concepts 方式 (C++20):
 *   template<typename T>
 *   requires Concept<T>
 *   ReturnType func(T t);
 *
 * Concepts 的优势:
 *   - 错误信息更清晰
 *   - 代码更易读
 *   - 编译速度更快
 *   - 可以组合和重用
 */

// SFINAE 方式: 检测是否有 serialize() 成员函数
template<typename T, typename = void>
struct HasSerializeOld : std::false_type {};

template<typename T>
struct HasSerializeOld<T, std::void_t<decltype(std::declval<T>().serialize())>>
    : std::true_type {};

// SFINAE 方式: 只有有 serialize() 时才启用
template<typename T>
auto serialize_sfinae(const T& obj) ->
    typename std::enable_if<HasSerializeOld<T>::value, std::string>::type
{
    return obj.serialize();
}

// Concepts 方式: 更简洁清晰
template<typename T>
concept HasSerialize = requires(const T& t) {
    { t.serialize() } -> std::convertible_to<std::string>;
};

template<HasSerialize T>
std::string serialize_concepts(const T& obj) {
    return obj.serialize();
}

// ============================================================================
// 第六部分: 高级概念应用
// ============================================================================

/**
 * 概念用于类模板
 */
template<typename T>
concept Numeric = std::is_arithmetic_v<T> && !std::is_same_v<T, bool>;

/**
 * 受约束的数值包装器类
 */
template<Numeric T>
class NumericWrapper {
private:
    T value_;

public:
    explicit NumericWrapper(T value) : value_(value) {}

    T get() const { return value_; }

    // 只有当内部类型支持时才定义这些运算符
    NumericWrapper operator+(const NumericWrapper& other) const {
        return NumericWrapper(value_ + other.value_);
    }

    NumericWrapper operator*(const NumericWrapper& other) const {
        return NumericWrapper(value_ * other.value_);
    }

    // 比较运算符
    bool operator==(const NumericWrapper& other) const = default;
    auto operator<=>(const NumericWrapper& other) const = default;

    friend std::ostream& operator<<(std::ostream& os, const NumericWrapper& nw) {
        return os << nw.value_;
    }
};

/**
 * 概念约束的算法: 查找最大元素
 */
template<Range Container>
    requires Comparable<typename Container::value_type>
auto max_element_constrained(const Container& c) {
    if (c.begin() == c.end()) {
        throw std::runtime_error("容器为空");
    }

    auto max_it = c.begin();
    for (auto it = c.begin(); it != c.end(); ++it) {
        if (*max_it < *it) {
            max_it = it;
        }
    }
    return max_it;
}

/**
 * 概念约束的转换函数
 * 将一个容器的元素转换为另一种类型
 */
template<typename U, Range Container>
    requires requires(typename Container::value_type v) {
        { static_cast<U>(v) };
    }
auto convert_container(const Container& c) {
    std::vector<U> result;
    result.reserve(c.size());
    for (const auto& elem : c) {
        result.push_back(static_cast<U>(elem));
    }
    return result;
}

/**
 * 概念约束的过滤函数
 */
template<Range Container, typename Predicate>
    requires requires(Predicate pred, typename Container::value_type v) {
        { pred(v) } -> std::convertible_to<bool>;
    }
auto filter_container(const Container& c, Predicate pred) {
    std::vector<typename Container::value_type> result;
    for (const auto& elem : c) {
        if (pred(elem)) {
            result.push_back(elem);
        }
    }
    return result;
}

/**
 * 概念约束的映射函数
 */
template<typename Func, Range Container>
auto map_container(const Container& c, Func func) {
    using ResultType = decltype(func(*c.begin()));
    std::vector<ResultType> result;
    result.reserve(c.size());
    for (const auto& elem : c) {
        result.push_back(func(elem));
    }
    return result;
}

// ============================================================================
// 第七部分: 概念重载决议
// ============================================================================

/**
 * 使用概念进行重载决议
 *
 * 当多个重载版本都匹配时，编译器会选择约束最严格的版本。
 * 这允许我们为不同类型提供不同精度的实现。
 *
 * 注意: std::integral 和 std::floating_point 是 std::arithmetic 的子概念，
 * 但它们之间互不包含，因此可以作为独立的重载候选。
 * 不能同时保留 Arithmetic 重载，否则会产生歧义。
 */

// 整数类型: 使用 std::integral 概念
template<std::integral T>
T compute(T value) {
    std::cout << "  [整数特化] ";
    return value * 2 + 1;
}

// 浮点类型: 使用 std::floating_point 概念
template<std::floating_point T>
T compute(T value) {
    std::cout << "  [浮点特化] ";
    return value * 2.5;
}

/**
 * 使用概念选择不同的容器操作策略
 */
template<Range Container>
void process_container(Container& c) {
    if constexpr (HasPushBack<Container>) {
        std::cout << "  [可增长容器] ";
        c.push_back(typename Container::value_type{});
    } else {
        std::cout << "  [固定容器] ";
    }
}

// ============================================================================
// 第八部分: 综合示例
// ============================================================================

/**
 * 概念约束的数学库
 */
namespace math_lib {

    // 概念: 可求和
    template<typename T>
    concept Summable = requires(T a, T b) {
        { a + b } -> std::same_as<T>;
        { T{} };  // 需要默认构造
    };

    // 概念: 可相乘
    template<typename T>
    concept Multipliable = requires(T a, T b) {
        { a * b } -> std::same_as<T>;
        { T{1} };  // 需要单位元
    };

    // 概念: 完全数值类型
    template<typename T>
    concept FullyNumeric = Summable<T> && Multipliable<T> && std::is_arithmetic_v<T>;

    // 受约束的求和
    template<Summable T>
    T sum(const std::vector<T>& values) {
        T result = T{};
        for (const auto& v : values) {
            result = result + v;
        }
        return result;
    }

    // 受约束的求积
    template<Multipliable T>
    T product(const std::vector<T>& values) {
        T result = T{1};
        for (const auto& v : values) {
            result = result * v;
        }
        return result;
    }

    // 受约束的点积
    template<FullyNumeric T>
    T dot_product(const std::vector<T>& a, const std::vector<T>& b) {
        if (a.size() != b.size()) {
            throw std::invalid_argument("向量长度不匹配");
        }
        T result = T{};
        for (size_t i = 0; i < a.size(); ++i) {
            result = result + a[i] * b[i];
        }
        return result;
    }

} // namespace math_lib

// ============================================================================
// 主函数: 演示所有功能
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  C++20 Concepts (概念) 演示" << std::endl;
    std::cout << "========================================" << std::endl;

    // --- 1. 基础概念使用 ---
    std::cout << "\n--- 1. 基础概念 ---" << std::endl;
    std::cout << "int 是否为 Arithmetic: " << std::boolalpha << Arithmetic<int> << std::endl;
    std::cout << "string 是否为 Arithmetic: " << std::boolalpha << Arithmetic<std::string> << std::endl;
    std::cout << "int 是否为 Comparable: " << std::boolalpha << Comparable<int> << std::endl;

    // --- 2. 受约束的模板 ---
    std::cout << "\n--- 2. 受约束的模板 ---" << std::endl;
    std::cout << "add_requires(3, 4): " << add_requires(3, 4) << std::endl;
    std::cout << "add_concept(3.5, 4.5): " << add_concept(3.5, 4.5) << std::endl;
    std::cout << "add_short(10, 20): " << add_short(10, 20) << std::endl;

    // 编译错误示例 (取消注释查看):
    // add_requires("hello", "world");  // 错误: const char* 不满足 Arithmetic

    // --- 3. 容器操作 ---
    std::cout << "\n--- 3. 容器操作 ---" << std::endl;
    std::vector<int> vec = {5, 2, 8, 1, 9, 3};
    std::list<double> lst = {1.1, 2.2, 3.3, 4.4};

    print_container(vec, "vector");
    print_container(lst, "list");

    std::cout << "vector 求和: " << sum_container(vec) << std::endl;
    std::cout << "list 求和: " << sum_container(lst) << std::endl;

    // --- 4. 概念组合 ---
    std::cout << "\n--- 4. 概念组合 ---" << std::endl;
    sort_container(vec);
    std::cout << "排序后 vector: ";
    print_container(vec);

    std::cout << "range_sum(vector): " << range_sum(vec) << std::endl;
    std::cout << "range_sum(list): " << range_sum(lst) << std::endl;

    // --- 5. 概念重载决议 ---
    std::cout << "\n--- 5. 概念重载决议 ---" << std::endl;
    std::cout << "compute(3): ";
    auto r1 = compute(3);
    std::cout << "-> " << r1 << std::endl;

    std::cout << "compute(3.14): ";
    auto r2 = compute(3.14);
    std::cout << "-> " << r2 << std::endl;

    std::cout << "compute(3.14f): ";
    auto r3 = compute(3.14f);
    std::cout << "-> " << r3 << std::endl;

    // --- 6. 类型检测 ---
    std::cout << "\n--- 6. 类型特性检测 ---" << std::endl;
    std::cout << "vector 有 size(): " << HasSize<std::vector<int>> << std::endl;
    std::cout << "int 有 size(): " << HasSize<int> << std::endl;
    std::cout << "vector 是 Range: " << Range<std::vector<int>> << std::endl;
    std::cout << "int 是 Range: " << Range<int> << std::endl;

    // --- 7. 概念约束的类 ---
    std::cout << "\n--- 7. 概念约束的类 ---" << std::endl;
    NumericWrapper<int> a(10), b(20);
    std::cout << "a + b = " << (a + b) << std::endl;
    std::cout << "a * b = " << (a * b) << std::endl;
    std::cout << "a == b: " << std::boolalpha << (a == b) << std::endl;
    std::cout << "a < b: " << std::boolalpha << (a < b) << std::endl;

    // --- 8. 高级算法 ---
    std::cout << "\n--- 8. 概念约束的算法 ---" << std::endl;

    // 最大元素
    auto max_it = max_element_constrained(vec);
    std::cout << "最大元素: " << *max_it << std::endl;

    // 类型转换
    auto doubles = convert_container<double>(vec);
    std::cout << "int->double 转换: ";
    print_container(doubles);

    // 过滤
    auto evens = filter_container(vec, [](int x) { return x % 2 == 0; });
    std::cout << "偶数过滤: ";
    print_container(evens);

    // 映射
    auto squares = map_container(vec, [](int x) { return x * x; });
    std::cout << "平方映射: ";
    print_container(squares);

    // --- 9. 数学库 ---
    std::cout << "\n--- 9. 概念约束的数学库 ---" << std::endl;
    std::vector<int> v1 = {1, 2, 3};
    std::vector<int> v2 = {4, 5, 6};

    std::cout << "sum(v1): " << math_lib::sum(v1) << std::endl;
    std::cout << "product(v1): " << math_lib::product(v1) << std::endl;
    std::cout << "dot_product(v1, v2): " << math_lib::dot_product(v1, v2) << std::endl;

    // --- 10. 概念检查 ---
    std::cout << "\n--- 10. 概念约束检查 ---" << std::endl;
    std::cout << "vector<int> 是 FullContainer: "
              << FullContainer<std::vector<int>> << std::endl;
    std::cout << "int 是 FullContainer: "
              << FullContainer<int> << std::endl;
    std::cout << "int 是 Hashable: "
              << Hashable<int> << std::endl;
    std::cout << "string 是 Printable: "
              << Printable<std::string> << std::endl;

    std::cout << "\n========================================" << std::endl;
    std::cout << "  演示结束" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
