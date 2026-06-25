/**
 * SFINAE (Substitution Failure Is Not An Error) 技术演示
 *
 * SFINAE 是 C++ 模板编程的核心概念之一。
 * 当模板参数替换失败时，编译器不会报错，而是简单地忽略这个候选函数。
 *
 * 核心思想：
 *   - 替换失败不是错误，而是排除候选
 *   - 利用这个特性来选择正确的函数重载
 *   - 实现编译期的类型分发
 *
 * 主要应用：
 *   1. 函数重载选择
 *   2. 类型检测（Detection Idiom）
 *   3. 接口限制
 *   4. 编译期多态
 *
 * 编译命令：g++ -std=c++17 -O2 -o sfinae sfinae.cpp
 */

#include <iostream>
#include <vector>
#include <list>
#include <map>
#include <string>
#include <type_traits>
#include <iterator>
#include <memory>
#include <cmath>
#include <stdexcept>
#include <algorithm>

// ============================================================================
// 第一部分：基础 SFINAE - 函数重载
// ============================================================================

/**
 * 使用 SFINAE 实现函数重载选择
 *
 * 示例：根据类型选择不同的处理方式
 */

// 方式1：使用返回类型 SFINAE
// 当 T 是整数类型时，enable_if 的第二个参数（返回类型）才有效
template<typename T>
std::enable_if_t<std::is_integral_v<T>, T>
process_value(T value) {
    std::cout << "处理整数: " << value << std::endl;
    return value * 2;
}

// 当 T 是浮点类型时
template<typename T>
std::enable_if_t<std::is_floating_point_v<T>, T>
process_value(T value) {
    std::cout << "处理浮点: " << value << std::endl;
    return value * 1.5;
}

// 方式2：使用额外的模板参数 SFINAE
// 这种方式更灵活，可以有多个 SFINAE 条件
template<typename T,
         typename std::enable_if<std::is_integral_v<T>, int>::type = 0>
T double_value(T value) {
    return value * 2;
}

template<typename T,
         typename std::enable_if<std::is_floating_point_v<T>, int>::type = 0>
T double_value(T value) {
    return value * 2.0;
}

// ============================================================================
// 第二部分：Detection Idiom（检测惯用法）
// ============================================================================

/**
 * Detection Idiom 是 SFINAE 的重要应用
 * 用于在编译期检测类型是否具有特定的成员或支持特定的操作
 *
 * C++17 引入了 std::void_t，使检测更加简洁
 */

// 使用 void_t 检测类型是否有特定成员
namespace detail {
    // 主模板：默认没有成员
    template<typename, typename = std::void_t<>>
    struct has_size_member : std::false_type {};

    // 特化：当 T 有 size() 成员时匹配
    template<typename T>
    struct has_size_member<T, std::void_t<decltype(std::declval<T>().size())>>
        : std::true_type {};

    // 检测是否有 begin() 和 end()
    template<typename, typename = std::void_t<>>
    struct has_begin_end : std::false_type {};

    template<typename T>
    struct has_begin_end<T, std::void_t<
        decltype(std::declval<T>().begin()),
        decltype(std::declval<T>().end())
    >> : std::true_type {};

    // 检测是否有特定的运算符
    template<typename, typename = std::void_t<>>
    struct has_equality_operator : std::false_type {};

    template<typename T>
    struct has_equality_operator<T, std::void_t<
        decltype(std::declval<T>() == std::declval<T>())
    >> : std::true_type {};

    // 检测是否有下标运算符
    template<typename, typename = std::void_t<>>
    struct has_subscript_operator : std::false_type {};

    template<typename T>
    struct has_subscript_operator<T, std::void_t<
        decltype(std::declval<T>()[0])
    >> : std::true_type {};

    // 检测是否可调用（有 operator()）
    template<typename, typename = std::void_t<>>
    struct is_callable : std::false_type {};

    template<typename T>
    struct is_callable<T, std::void_t<
        decltype(&T::operator())
    >> : std::true_type {};

    // 检测是否有 toString() 方法
    template<typename, typename = std::void_t<>>
    struct has_to_string : std::false_type {};

    template<typename T>
    struct has_to_string<T, std::void_t<
        decltype(std::declval<T>().toString())
    >> : std::true_type {};
}

// 便捷变量模板
template<typename T>
inline constexpr bool has_size_member_v = detail::has_size_member<T>::value;

template<typename T>
inline constexpr bool has_begin_end_v = detail::has_begin_end<T>::value;

template<typename T>
inline constexpr bool has_equality_operator_v = detail::has_equality_operator<T>::value;

template<typename T>
inline constexpr bool has_subscript_operator_v = detail::has_subscript_operator<T>::value;

template<typename T>
inline constexpr bool is_callable_v = detail::is_callable<T>::value;

template<typename T>
inline constexpr bool has_to_string_v = detail::has_to_string<T>::value;

// ============================================================================
// 第三部分：通用检测宏
// ============================================================================

/**
 * DEFINE_DETECTOR 宏 - 简化检测器的定义
 *
 * 使用宏可以快速定义新的检测器
 */
#define DEFINE_DETECTOR(name, expr)                         \
    namespace detail {                                       \
        template<typename, typename = std::void_t<>>        \
        struct has_##name : std::false_type {};              \
        template<typename T>                                \
        struct has_##name<T, std::void_t<decltype(expr)>>   \
            : std::true_type {};                            \
    }                                                       \
    template<typename T>                                    \
    inline constexpr bool has_##name##_v = detail::has_##name<T>::value;

// 使用宏定义各种检测器
DEFINE_DETECTOR(size, std::declval<T>().size())
DEFINE_DETECTOR(empty, std::declval<T>().empty())
DEFINE_DETECTOR(clear, std::declval<T>().clear())
DEFINE_DETECTOR(push_back, std::declval<T>().push_back(std::declval<typename T::value_type>()))
DEFINE_DETECTOR(reserve, std::declval<T>().reserve(0))
DEFINE_DETECTOR(data, std::declval<T>().data())

// ============================================================================
// 第四部分：SFINAE 实现编译期分发
// ============================================================================

/**
 * 使用 SFINAE 实现编译期多态
 *
 * 根据类型的能力选择不同的实现
 */

// 检测类型是否是可迭代的
template<typename T>
constexpr bool is_iterable() {
    return has_begin_end_v<T>;
}

// 打印函数：根据类型能力选择实现
// 版本1：可迭代的容器
template<typename T>
std::enable_if_t<has_begin_end_v<T>>
smart_print(const T& container) {
    std::cout << "[";
    bool first = true;
    for (const auto& elem : container) {
        if (!first) std::cout << ", ";
        std::cout << elem;
        first = false;
    }
    std::cout << "]" << std::endl;
}

// 版本2：有 size() 但不是可迭代的
template<typename T>
std::enable_if_t<!has_begin_end_v<T> && has_size_member_v<T>>
smart_print(const T& obj) {
    std::cout << "对象大小: " << obj.size() << std::endl;
}

// 版本3：基础类型
template<typename T>
std::enable_if_t<!has_begin_end_v<T> && !has_size_member_v<T>>
smart_print(const T& value) {
    std::cout << value << std::endl;
}

// ============================================================================
// 第五部分：SFINAE 与迭代器
// ============================================================================

/**
 * 根据迭代器类型选择最优算法
 *
 * 这是 SFINAE 的经典应用场景
 */

// 检测是否为随机访问迭代器
template<typename Iter, typename = void>
struct is_random_access : std::false_type {};

template<typename Iter>
struct is_random_access<Iter, std::enable_if_t<
    std::is_same_v<
        typename std::iterator_traits<Iter>::iterator_category,
        std::random_access_iterator_tag
    >
>> : std::true_type {};

// 检测是否为双向迭代器
template<typename Iter, typename = void>
struct is_bidirectional : std::false_type {};

template<typename Iter>
struct is_bidirectional<Iter, std::enable_if_t<
    std::is_same_v<
        typename std::iterator_traits<Iter>::iterator_category,
        std::bidirectional_iterator_tag
    > ||
    is_random_access<Iter>::value
>> : std::true_type {};

/**
 * distance_impl - 根据迭代器类型选择最优的距离计算算法
 */
// 随机访问迭代器：O(1) 复杂度
template<typename Iter>
std::enable_if_t<is_random_access<Iter>::value,
    typename std::iterator_traits<Iter>::difference_type>
distance_impl(Iter first, Iter last) {
    std::cout << "使用随机访问迭代器距离计算 (O(1))" << std::endl;
    return last - first;
}

// 输入迭代器：O(n) 复杂度
template<typename Iter>
std::enable_if_t<!is_random_access<Iter>::value,
    typename std::iterator_traits<Iter>::difference_type>
distance_impl(Iter first, Iter last) {
    std::cout << "使用输入迭代器距离计算 (O(n))" << std::endl;
    typename std::iterator_traits<Iter>::difference_type count = 0;
    while (first != last) {
        ++first;
        ++count;
    }
    return count;
}

/**
 * advance_impl - 根据迭代器类型选择最优的前进算法
 */
// 随机访问迭代器：直接跳跃
template<typename Iter>
std::enable_if_t<is_random_access<Iter>::value>
advance_impl(Iter& it, typename std::iterator_traits<Iter>::difference_type n) {
    std::cout << "使用随机访问迭代器前进 (O(1))" << std::endl;
    it += n;
}

// 双向迭代器：可以后退
template<typename Iter>
std::enable_if_t<!is_random_access<Iter>::value && is_bidirectional<Iter>::value>
advance_impl(Iter& it, typename std::iterator_traits<Iter>::difference_type n) {
    std::cout << "使用双向迭代器前进 (O(n))" << std::endl;
    if (n >= 0) {
        while (n--) ++it;
    } else {
        while (n++) --it;
    }
}

// 输入迭代器：只能前进
template<typename Iter>
std::enable_if_t<!is_random_access<Iter>::value && !is_bidirectional<Iter>::value>
advance_impl(Iter& it, typename std::iterator_traits<Iter>::difference_type n) {
    std::cout << "使用输入迭代器前进 (O(n))" << std::endl;
    while (n--) ++it;
}

// ============================================================================
// 第六部分：SFINAE 与类模板
// ============================================================================

/**
 * ContainerAdapter - 根据容器能力提供不同的接口
 *
 * 使用 SFINAE 在编译期选择可用的方法
 */
template<typename Container>
class ContainerAdapter {
    Container& container_;

public:
    explicit ContainerAdapter(Container& c) : container_(c) {}

    // 只有容器有 push_back 时才能调用
    template<typename T = Container>
    std::enable_if_t<has_push_back_v<T>, void>
    add(const typename T::value_type& value) {
        container_.push_back(value);
    }

    // 只有容器有 reserve 时才能调用
    template<typename T = Container>
    std::enable_if_t<has_reserve_v<T>, void>
    reserve(size_t capacity) {
        container_.reserve(capacity);
    }

    // 只有容器有 size 时才能调用
    template<typename T = Container>
    std::enable_if_t<has_size_member_v<T>, size_t>
    size() const {
        return container_.size();
    }

    // 只有容器有 empty 时才能调用
    template<typename T = Container>
    std::enable_if_t<has_empty_v<T>, bool>
    empty() const {
        return container_.empty();
    }

    // 只有容器有 clear 时才能调用
    template<typename T = Container>
    std::enable_if_t<has_clear_v<T>, void>
    clear() {
        container_.clear();
    }

    // 只有容器有 data 时才能调用
    template<typename T = Container>
    std::enable_if_t<has_data_v<T>, decltype(std::declval<Container&>().data())>
    data() {
        return container_.data();
    }
};

// ============================================================================
// 第七部分：实际应用示例
// ============================================================================

/**
 * 使用 SFINAE 实现通用的 toString 函数
 *
 * 根据类型选择不同的转换策略
 */

// 版本1：有 toString() 方法的类型
template<typename T>
std::enable_if_t<has_to_string_v<T>, std::string>
to_string(const T& obj) {
    return obj.toString();
}

// 版本2：数值类型
template<typename T>
std::enable_if_t<!has_to_string_v<T> && std::is_arithmetic_v<T>, std::string>
to_string(const T& value) {
    return std::to_string(value);
}

// 版本3：字符串类型
template<typename T>
std::enable_if_t<!has_to_string_v<T> && !std::is_arithmetic_v<T> &&
                  std::is_convertible_v<T, std::string>, std::string>
to_string(const T& value) {
    return std::string(value);
}

// 版本4：可迭代容器
template<typename T>
std::enable_if_t<!has_to_string_v<T> && !std::is_arithmetic_v<T> &&
                  !std::is_convertible_v<T, std::string> &&
                  has_begin_end_v<T>, std::string>
to_string(const T& container) {
    std::string result = "[";
    bool first = true;
    for (const auto& elem : container) {
        if (!first) result += ", ";
        result += to_string(elem);
        first = false;
    }
    result += "]";
    return result;
}

/**
 * MyPoint - 演示自定义类的 SFINAE 检测
 */
struct MyPoint {
    double x, y;

    std::string toString() const {
        return "(" + std::to_string(x) + ", " + std::to_string(y) + ")";
    }
};

/**
 * 使用 SFINAE 限制模板参数
 *
 * 只接受支持特定操作的类型
 */
template<typename Container>
auto safe_access(Container& c, size_t index)
    -> std::enable_if_t<has_subscript_operator_v<Container> &&
                         has_size_member_v<Container>,
                         typename Container::reference>
{
    if (index >= c.size()) {
        throw std::out_of_range("索引越界");
    }
    return c[index];
}

// ============================================================================
// 主函数：演示各种 SFINAE 技术
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "SFINAE 技术演示" << std::endl;
    std::cout << "========================================" << std::endl;

    // ---- 第一部分：基础函数重载 ----
    std::cout << "\n--- 1. SFINAE 函数重载 ---" << std::endl;

    process_value(42);       // 调用整数版本
    process_value(3.14);     // 调用浮点版本

    std::cout << "double_value(5) = " << double_value(5) << std::endl;
    std::cout << "double_value(3.14) = " << double_value(3.14) << std::endl;

    // ---- 第二部分：Detection Idiom ----
    std::cout << "\n--- 2. Detection Idiom ---" << std::endl;

    std::cout << "vector<int> 有 size(): " << std::boolalpha
              << has_size_member_v<std::vector<int>> << std::endl;
    std::cout << "int 有 size(): " << has_size_member_v<int> << std::endl;

    std::cout << "vector<int> 有 begin/end(): "
              << has_begin_end_v<std::vector<int>> << std::endl;
    std::cout << "int 有 begin/end(): " << has_begin_end_v<int> << std::endl;

    std::cout << "vector<int> 有 operator[]: "
              << has_subscript_operator_v<std::vector<int>> << std::endl;

    // ---- 第三部分：宏定义的检测器 ----
    std::cout << "\n--- 3. 宏定义检测器 ---" << std::endl;

    std::cout << "vector<int> 有 push_back: "
              << has_push_back_v<std::vector<int>> << std::endl;
    std::cout << "vector<int> 有 reserve: "
              << has_reserve_v<std::vector<int>> << std::endl;
    std::cout << "vector<int> 有 data: "
              << has_data_v<std::vector<int>> << std::endl;
    std::cout << "list<int> 有 reserve: "
              << has_reserve_v<std::list<int>> << std::endl;

    // ---- 第四部分：编译期分发 ----
    std::cout << "\n--- 4. 编译期分发 ---" << std::endl;

    std::vector<int> vec = {1, 2, 3, 4, 5};
    int arr[] = {10, 20, 30};
    int scalar = 42;

    std::cout << "smart_print(vector): ";
    smart_print(vec);

    std::cout << "smart_print(array): ";
    smart_print(arr);

    std::cout << "smart_print(scalar): ";
    smart_print(scalar);

    // ---- 第五部分：迭代器分发 ----
    std::cout << "\n--- 5. 迭代器分发 ---" << std::endl;

    auto vec_dist = distance_impl(vec.begin(), vec.end());
    std::cout << "vector 距离: " << vec_dist << std::endl;

    std::list<int> lst = {1, 2, 3};
    auto lst_dist = distance_impl(lst.begin(), lst.end());
    std::cout << "list 距离: " << lst_dist << std::endl;

    auto it = vec.begin();
    advance_impl(it, 3);
    std::cout << "前进 3 后: " << *it << std::endl;

    // ---- 第六部分：ContainerAdapter ----
    std::cout << "\n--- 6. ContainerAdapter ---" << std::endl;

    std::vector<int> my_vec;
    ContainerAdapter<std::vector<int>> adapter(my_vec);

    adapter.reserve(10);
    adapter.add(1);
    adapter.add(2);
    adapter.add(3);

    std::cout << "容器大小: " << adapter.size() << std::endl;
    std::cout << "是否为空: " << adapter.empty() << std::endl;
    std::cout << "数据指针: " << adapter.data() << std::endl;

    // ---- 第七部分：通用 toString ----
    std::cout << "\n--- 7. 通用 toString ---" << std::endl;

    std::cout << "to_string(42): " << to_string(42) << std::endl;
    std::cout << "to_string(3.14): " << to_string(3.14) << std::endl;
    std::cout << "to_string(\"hello\"): " << to_string(std::string("hello")) << std::endl;

    MyPoint point{3.0, 4.0};
    std::cout << "to_string(MyPoint): " << to_string(point) << std::endl;

    std::vector<int> nums = {1, 2, 3};
    std::cout << "to_string(vector): " << to_string(nums) << std::endl;

    // ---- 第八部分：安全访问 ----
    std::cout << "\n--- 8. 安全访问 ---" << std::endl;

    try {
        std::cout << "safe_access(vec, 2) = " << safe_access(vec, 2) << std::endl;
        std::cout << "safe_access(vec, 10): ";
        std::cout << safe_access(vec, 10) << std::endl;
    } catch (const std::exception& e) {
        std::cout << "异常: " << e.what() << std::endl;
    }

    return 0;
}
