/**
 * 类型萃取 (Type Traits) 技术演示
 *
 * 类型萃取是 C++ 模板元编程的基础，它允许我们在编译期查询和修改类型信息。
 *
 * 核心概念：
 *   - 特征类 (Trait Class)：包含类型信息的模板类
 *   - 编译期计算：使用 constexpr 和模板特化
 *   - 类型变换：使用 std::add_const, std::remove_reference 等
 *
 * 标准库中的类型萃取：
 *   - <type_traits> 头文件提供了丰富的类型萃取工具
 *   - 包括类型查询、类型变换、类型关系等
 *
 * 编译命令：g++ -std=c++17 -O2 -o type_traits type_traits.cpp
 */

#include <iostream>
#include <vector>
#include <list>
#include <map>
#include <string>
#include <type_traits>
#include <memory>
#include <array>
#include <cmath>
#include <limits>
#include <algorithm>
#include <stdexcept>

// ============================================================================
// 第一部分：基础类型萃取
// ============================================================================

/**
 * is_container - 检测类型是否为容器
 *
 * 检测原理：
 *   容器通常具有以下特征：
 *   1. 有 value_type 类型别名
 *   2. 有 begin() 和 end() 成员函数
 *   3. 有 size() 成员函数（可选）
 *
 * 我们使用 SFINAE 技术来检测这些特征
 */
namespace detail {
    // 检测是否有 value_type
    template<typename T, typename = void>
    struct has_value_type : std::false_type {};

    template<typename T>
    struct has_value_type<T, std::void_t<typename T::value_type>> : std::true_type {};

    // 检测是否有 begin() 成员函数
    template<typename T, typename = void>
    struct has_begin : std::false_type {};

    template<typename T>
    struct has_begin<T, std::void_t<decltype(std::declval<T>().begin())>> : std::true_type {};

    // 检测是否有 end() 成员函数
    template<typename T, typename = void>
    struct has_end : std::false_type {};

    template<typename T>
    struct has_end<T, std::void_t<decltype(std::declval<T>().end())>> : std::true_type {};
}

/**
 * is_container - 综合判断是否为容器
 *
 * 同时满足以下条件才认为是容器：
 *   1. 有 value_type 类型别名
 *   2. 有 begin() 成员函数
 *   3. 有 end() 成员函数
 */
template<typename T>
struct is_container : std::integral_constant<bool,
    detail::has_value_type<T>::value &&
    detail::has_begin<T>::value &&
    detail::has_end<T>::value
> {};

// C++17 变量模板
template<typename T>
inline constexpr bool is_container_v = is_container<T>::value;

/**
 * is_pair - 检测类型是否为 std::pair
 *
 * 使用模板特化实现
 */
template<typename T>
struct is_pair : std::false_type {};

template<typename T1, typename T2>
struct is_pair<std::pair<T1, T2>> : std::true_type {};

template<typename T>
inline constexpr bool is_pair_v = is_pair<T>::value;

/**
 * has_size - 检测类型是否有 size() 成员函数
 *
 * 使用表达式 SFINAE 检测
 */
template<typename T, typename = void>
struct has_size : std::false_type {};

template<typename T>
struct has_size<T, std::void_t<decltype(std::declval<T>().size())>> : std::true_type {};

template<typename T>
inline constexpr bool has_size_v = has_size<T>::value;

// ============================================================================
// 第二部分：检测成员函数
// ============================================================================

/**
 * 检测特定签名的成员函数
 *
 * 使用宏简化检测代码的编写
 */
#define DEFINE_HAS_MEMBER_FUNCTION(func_name)                               \
    template<typename T, typename... Args>                                  \
    struct has_##func_name {                                                \
    private:                                                                \
        template<typename U>                                                \
        static auto test(int) -> decltype(                                  \
            std::declval<U>().func_name(std::declval<Args>()...),           \
            std::true_type{}                                                \
        );                                                                  \
        template<typename U>                                                \
        static std::false_type test(...);                                   \
    public:                                                                 \
        static constexpr bool value = decltype(test<T>(0))::value;          \
    };                                                                      \
    template<typename T, typename... Args>                                  \
    inline constexpr bool has_##func_name##_v = has_##func_name<T, Args...>::value;

// 生成各种成员函数检测器
DEFINE_HAS_MEMBER_FUNCTION(push_back)
DEFINE_HAS_MEMBER_FUNCTION(emplace_back)
DEFINE_HAS_MEMBER_FUNCTION(resize)
DEFINE_HAS_MEMBER_FUNCTION(clear)
DEFINE_HAS_MEMBER_FUNCTION(at)

// ============================================================================
// 第三部分：自定义类型萃取
// ============================================================================

/**
 * is_string - 检测类型是否为字符串类型
 *
 * 包括 std::string, std::wstring, const char* 等
 */
template<typename T>
struct is_string : std::false_type {};

template<>
struct is_string<std::string> : std::true_type {};

template<>
struct is_string<std::wstring> : std::true_type {};

template<>
struct is_string<const char*> : std::true_type {};

template<>
struct is_string<const wchar_t*> : std::true_type {};

template<typename T>
inline constexpr bool is_string_v = is_string<T>::value;

/**
 * is_smart_pointer - 检测类型是否为智能指针
 *
 * 支持 std::unique_ptr, std::shared_ptr, std::weak_ptr
 */
template<typename T>
struct is_smart_pointer : std::false_type {};

template<typename T>
struct is_smart_pointer<std::unique_ptr<T>> : std::true_type {};

template<typename T>
struct is_smart_pointer<std::shared_ptr<T>> : std::true_type {};

template<typename T>
struct is_smart_pointer<std::weak_ptr<T>> : std::true_type {};

template<typename T>
inline constexpr bool is_smart_pointer_v = is_smart_pointer<T>::value;

/**
 * is_iterable - 检测类型是否可迭代
 *
 * 可迭代类型需要满足：
 *   1. 有 begin() 和 end()
 *   2. begin() 和 end() 返回相同的类型
 *   3. 返回的迭代器支持 * 和 ++ 操作
 */
template<typename T, typename = void>
struct is_iterable : std::false_type {};

template<typename T>
struct is_iterable<T, std::void_t<
    decltype(std::begin(std::declval<T&>())),
    decltype(std::end(std::declval<T&>()))
>> : std::true_type {};

template<typename T>
inline constexpr bool is_iterable_v = is_iterable<T>::value;

/**
 * element_type - 获取容器的元素类型
 *
 * 对于容器，返回 value_type
 * 对于数组，返回元素类型
 */
template<typename T, typename = void>
struct element_type {
    using type = void;
};

// 对于有 value_type 的容器
template<typename T>
struct element_type<T, std::void_t<typename T::value_type>> {
    using type = typename T::value_type;
};

// 对于 C 风格数组
template<typename T, size_t N>
struct element_type<T[N], void> {
    using type = T;
};

// 对于 std::array
template<typename T, size_t N>
struct element_type<std::array<T, N>, void> {
    using type = T;
};

template<typename T>
using element_type_t = typename element_type<T>::type;

// ============================================================================
// 第四部分：类型变换
// ============================================================================

/**
 * add_const_ref - 添加 const 引用
 *
 * 如果类型已经是引用，保持不变
 * 否则添加 const 引用
 */
template<typename T>
struct add_const_ref {
    using type = const T&;
};

// 已经是引用的情况
template<typename T>
struct add_const_ref<T&> {
    using type = T&;  // 引用保持不变
};

template<typename T>
using add_const_ref_t = typename add_const_ref<T>::type;

/**
 * promote - 类型提升
 *
 * 用于数值类型的自动提升
 */
template<typename T>
struct promote {
    using type = T;  // 默认不提升
};

template<>
struct promote<char> {
    using type = int;
};

template<>
struct promote<short> {
    using type = int;
};

template<>
struct promote<float> {
    using type = double;
};

template<typename T>
using promote_t = typename promote<T>::type;

// ============================================================================
// 第五部分：constexpr if 与类型萃取
// ============================================================================

/**
 * print_value - 使用 constexpr if 根据类型选择不同的打印方式
 *
 * C++17 的 constexpr if 允许在编译期根据条件选择代码路径
 * 配合类型萃取，可以实现类型安全的分支
 */
template<typename T>
void print_value(const T& value) {
    if constexpr (std::is_integral_v<T>) {
        // 整数类型：直接输出
        std::cout << "整数: " << value << std::endl;
    } else if constexpr (std::is_floating_point_v<T>) {
        // 浮点类型：设置精度
        std::cout << "浮点数: " << std::fixed << value << std::endl;
    } else if constexpr (is_string_v<T>) {
        // 字符串类型：添加引号
        std::cout << "字符串: \"" << value << "\"" << std::endl;
    } else if constexpr (is_container_v<T>) {
        // 容器类型：遍历输出
        std::cout << "容器: [";
        bool first = true;
        for (const auto& elem : value) {
            if (!first) std::cout << ", ";
            std::cout << elem;
            first = false;
        }
        std::cout << "]" << std::endl;
    } else {
        // 其他类型
        std::cout << "其他类型" << std::endl;
    }
}

/**
 * serialize - 使用类型萃取实现简单的序列化
 *
 * 根据类型选择不同的序列化策略
 */
template<typename T>
std::string serialize(const T& value) {
    if constexpr (std::is_arithmetic_v<T>) {
        // 数值类型：直接转换为字符串
        return std::to_string(value);
    } else if constexpr (is_string_v<T>) {
        // 字符串类型：添加引号
        return "\"" + std::string(value) + "\"";
    } else if constexpr (is_pair_v<T>) {
        // pair 类型：递归序列化 first 和 second
        return "{" + serialize(value.first) + ": " + serialize(value.second) + "}";
    } else if constexpr (is_container_v<T>) {
        // 容器类型：递归序列化每个元素
        std::string result = "[";
        bool first = true;
        for (const auto& elem : value) {
            if (!first) result += ", ";
            result += serialize(elem);
            first = false;
        }
        result += "]";
        return result;
    } else {
        return "(unknown)";
    }
}

/**
 * transform_value - 使用类型萃取进行值变换
 *
 * 根据类型进行不同的变换：
 *   - 整数：取绝对值
 *   - 浮点：四舍五入
 *   - 字符串：转大写
 */
template<typename T>
auto transform_value(const T& value) {
    if constexpr (std::is_integral_v<T>) {
        return std::abs(value);
    } else if constexpr (std::is_floating_point_v<T>) {
        return static_cast<T>(std::round(value));
    } else if constexpr (is_string_v<T>) {
        std::string result = value;
        for (auto& c : result) {
            c = std::toupper(c);
        }
        return result;
    } else {
        return value;
    }
}

// ============================================================================
// 第六部分：enable_if 使用示例
// ============================================================================

/**
 * 使用 std::enable_if 限制函数模板的适用类型
 *
 * 只有满足条件的类型才能调用该函数
 */

// 只接受整数类型
template<typename T>
std::enable_if_t<std::is_integral_v<T>, T>
safe_add(T a, T b) {
    // 检查是否溢出
    if (b > 0 && a > std::numeric_limits<T>::max() - b) {
        throw std::overflow_error("加法溢出");
    }
    if (b < 0 && a < std::numeric_limits<T>::min() - b) {
        throw std::underflow_error("加法下溢");
    }
    return a + b;
}

// 只接受浮点类型
template<typename T>
std::enable_if_t<std::is_floating_point_v<T>, T>
safe_add(T a, T b) {
    return a + b;  // 浮点数不需要溢出检查
}

// 只接受容器类型
template<typename T>
std::enable_if_t<is_container_v<T>, void>
print_if_container(const T& container) {
    std::cout << "这是容器，元素数量: " << container.size() << std::endl;
}

// 对于非容器类型，不定义函数（会导致编译错误）

// ============================================================================
// 主函数：演示各种类型萃取技术
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "类型萃取 (Type Traits) 技术演示" << std::endl;
    std::cout << "========================================" << std::endl;

    // ---- 第一部分：基础类型萃取 ----
    std::cout << "\n--- 1. 基础类型萃取 ---" << std::endl;

    std::cout << "is_container_v<vector<int>>: "
              << std::boolalpha << is_container_v<std::vector<int>> << std::endl;
    std::cout << "is_container_v<list<string>>: "
              << is_container_v<std::list<std::string>> << std::endl;
    std::cout << "is_container_v<int>: "
              << is_container_v<int> << std::endl;

    std::cout << "is_pair_v<pair<int,string>>: "
              << is_pair_v<std::pair<int, std::string>> << std::endl;
    std::cout << "is_pair_v<vector<int>>: "
              << is_pair_v<std::vector<int>> << std::endl;

    std::cout << "has_size_v<vector<int>>: "
              << has_size_v<std::vector<int>> << std::endl;
    std::cout << "has_size_v<int>: "
              << has_size_v<int> << std::endl;

    // ---- 第二部分：成员函数检测 ----
    std::cout << "\n--- 2. 成员函数检测 ---" << std::endl;

    std::cout << "vector<int> 有 push_back: "
              << has_push_back_v<std::vector<int>> << std::endl;
    std::cout << "vector<int> 有 clear: "
              << has_clear_v<std::vector<int>> << std::endl;
    std::cout << "int 有 push_back: "
              << has_push_back_v<int> << std::endl;

    // ---- 第三部分：自定义类型萃取 ----
    std::cout << "\n--- 3. 自定义类型萃取 ---" << std::endl;

    std::cout << "is_string_v<string>: "
              << is_string_v<std::string> << std::endl;
    std::cout << "is_string_v<int>: "
              << is_string_v<int> << std::endl;
    std::cout << "is_string_v<const char*>: "
              << is_string_v<const char*> << std::endl;

    std::cout << "is_smart_pointer_v<unique_ptr<int>>: "
              << is_smart_pointer_v<std::unique_ptr<int>> << std::endl;
    std::cout << "is_smart_pointer_v<int*>: "
              << is_smart_pointer_v<int*> << std::endl;

    std::cout << "is_iterable_v<vector<int>>: "
              << is_iterable_v<std::vector<int>> << std::endl;
    std::cout << "is_iterable_v<int>: "
              << is_iterable_v<int> << std::endl;

    // ---- 第四部分：constexpr if 演示 ----
    std::cout << "\n--- 4. constexpr if 演示 ---" << std::endl;

    print_value(42);
    print_value(3.14);
    print_value(std::string("Hello"));
    print_value(std::vector<int>{1, 2, 3, 4, 5});

    // ---- 第五部分：序列化演示 ----
    std::cout << "\n--- 5. 序列化演示 ---" << std::endl;

    std::cout << "serialize(42): " << serialize(42) << std::endl;
    std::cout << "serialize(3.14): " << serialize(3.14) << std::endl;
    std::cout << "serialize(\"hello\"): " << serialize(std::string("hello")) << std::endl;

    std::map<int, std::string> data = {{1, "one"}, {2, "two"}, {3, "three"}};
    std::cout << "serialize(map): " << serialize(data) << std::endl;

    std::vector<std::pair<int, std::string>> vec = {{1, "a"}, {2, "b"}};
    std::cout << "serialize(vec of pairs): " << serialize(vec) << std::endl;

    // ---- 第六部分：值变换演示 ----
    std::cout << "\n--- 6. 值变换演示 ---" << std::endl;

    std::cout << "transform(-5): " << transform_value(-5) << std::endl;
    std::cout << "transform(3.7): " << transform_value(3.7) << std::endl;
    std::cout << "transform(3.2): " << transform_value(3.2) << std::endl;
    std::cout << "transform(\"hello\"): " << transform_value(std::string("hello")) << std::endl;

    // ---- 第七部分：enable_if 演示 ----
    std::cout << "\n--- 7. enable_if 演示 ---" << std::endl;

    try {
        std::cout << "safe_add(100, 200) = " << safe_add(100, 200) << std::endl;
        std::cout << "safe_add(3.14, 2.86) = " << safe_add(3.14, 2.86) << std::endl;

        // 溢出检测
        std::cout << "safe_add(INT_MAX, 1): ";
        std::cout << safe_add(std::numeric_limits<int>::max(), 1) << std::endl;
    } catch (const std::exception& e) {
        std::cout << "异常: " << e.what() << std::endl;
    }

    std::vector<int> my_vec = {1, 2, 3};
    print_if_container(my_vec);

    // 以下代码会导致编译错误，因为 int 不是容器
    // print_if_container(42);

    // ---- 第八部分：标准库类型萃取 ----
    std::cout << "\n--- 8. 标准库类型萃取 ---" << std::endl;

    std::cout << "is_same_v<int, int32_t>: "
              << std::is_same_v<int, int32_t> << std::endl;
    std::cout << "is_convertible_v<int, double>: "
              << std::is_convertible_v<int, double> << std::endl;
    std::cout << "is_base_of_v<exception, runtime_error>: "
              << std::is_base_of_v<std::exception, std::runtime_error> << std::endl;

    // 条件类型选择
    using IntOrDouble = std::conditional_t<true, int, double>;
    std::cout << "conditional<true, int, double> is int: "
              << std::is_same_v<IntOrDouble, int> << std::endl;

    return 0;
}
