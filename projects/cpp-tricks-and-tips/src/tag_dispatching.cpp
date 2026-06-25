/**
 * 标签分发 (Tag Dispatching) 技术演示
 *
 * 标签分发是 C++ 模板元编程中的一种技术，它使用空的标签类型来在编译期选择正确的函数重载。
 *
 * 核心思想：
 *   - 定义一组标签类型（通常是空结构体）
 *   - 函数根据标签类型选择不同的实现
 *   - 标签通常通过类型萃取获取
 *
 * 典型应用：
 *   1. 迭代器类别分发（STL 的核心机制）
 *   2. 算法优化
 *   3. 策略选择
 *   4. 编译期多态
 *
 * 与 SFINAE 的区别：
 *   - SFINAE：通过排除不匹配的重载来选择
 *   - 标签分发：通过显式的标签来选择
 *   - 标签分发通常更清晰，更容易调试
 *
 * 编译命令：g++ -std=c++17 -O2 -o tag_dispatching tag_dispatching.cpp
 */

#include <iostream>
#include <vector>
#include <list>
#include <deque>
#include <iterator>
#include <type_traits>
#include <algorithm>
#include <chrono>
#include <string>
#include <memory>
#include <cmath>
#include <map>

// ============================================================================
// 第一部分：迭代器标签
// ============================================================================

/**
 * 标准库中的迭代器标签层次结构
 *
 * 输入迭代器 (Input Iterator)
 *   └── 前向迭代器 (Forward Iterator)
 *         └── 双向迭代器 (Bidirectional Iterator)
 *               └── 随机访问迭代器 (Random Access Iterator)
 *                     └── 连续迭代器 (Contiguous Iterator) [C++20]
 *
 * 每个标签都是一个空结构体，继承自前一个标签
 */

// 使用标准库的迭代器标签
using std::input_iterator_tag;
using std::forward_iterator_tag;
using std::bidirectional_iterator_tag;
using std::random_access_iterator_tag;
using std::output_iterator_tag;

// ============================================================================
// 第二部分：自定义标签
// ============================================================================

/**
 * 自定义标签类型
 *
 * 用于演示非迭代器场景的标签分发
 */

// 数值类型标签
struct int_tag {};
struct float_tag {};
struct string_tag {};
struct container_tag {};

/**
 * type_tag - 获取类型的标签
 *
 * 使用模板特化将类型映射到标签
 */
template<typename T>
struct type_tag_of;

template<>
struct type_tag_of<int> {
    using type = int_tag;
};

template<>
struct type_tag_of<float> {
    using type = float_tag;
};

template<>
struct type_tag_of<double> {
    using type = float_tag;
};

template<>
struct type_tag_of<std::string> {
    using type = string_tag;
};

// 容器类型的标签
template<typename T>
struct type_tag_of<std::vector<T>> {
    using type = container_tag;
};

template<typename T>
struct type_tag_of<std::list<T>> {
    using type = container_tag;
};

template<typename T>
using type_tag_of_t = typename type_tag_of<T>::type;

// ============================================================================
// 第三部分：使用标签分发实现 std::advance
// ============================================================================

/**
 * advance_impl - 根据迭代器类别选择最优的前进算法
 *
 * 随机访问迭代器：直接跳跃，O(1)
 * 双向迭代器：逐步前进，O(n)
 * 输入迭代器：逐步前进，O(n)
 */

// 随机访问迭代器版本：直接使用 += 运算符
template<typename Iter>
void advance_impl(Iter& it,
                  typename std::iterator_traits<Iter>::difference_type n,
                  random_access_iterator_tag) {
    std::cout << "  [随机访问迭代器] 直接跳跃 " << n << " 步" << std::endl;
    it += n;
}

// 双向迭代器版本：可以前进也可以后退
template<typename Iter>
void advance_impl(Iter& it,
                  typename std::iterator_traits<Iter>::difference_type n,
                  bidirectional_iterator_tag) {
    std::cout << "  [双向迭代器] 逐步";
    if (n >= 0) {
        std::cout << "前进 " << n << " 步" << std::endl;
        for (; n > 0; --n) {
            ++it;
        }
    } else {
        std::cout << "后退 " << -n << " 步" << std::endl;
        for (; n < 0; ++n) {
            --it;
        }
    }
}

// 输入/前向迭代器版本：只能前进
template<typename Iter>
void advance_impl(Iter& it,
                  typename std::iterator_traits<Iter>::difference_type n,
                  input_iterator_tag) {
    std::cout << "  [输入迭代器] 逐步前进 " << n << " 步" << std::endl;
    for (; n > 0; --n) {
        ++it;
    }
}

/**
 * advance - 用户接口函数
 *
 * 获取迭代器的类别标签，然后调用对应的实现
 */
template<typename Iter>
void advance(Iter& it, typename std::iterator_traits<Iter>::difference_type n) {
    // 获取迭代器类别标签
    using category = typename std::iterator_traits<Iter>::iterator_category;

    // 传递标签对象来分发到正确的实现
    advance_impl(it, n, category{});
}

// ============================================================================
// 第四部分：使用标签分发实现距离计算
// ============================================================================

/**
 * distance_impl - 根据迭代器类别选择最优的距离计算算法
 */

// 随机访问迭代器：直接减法，O(1)
template<typename Iter>
typename std::iterator_traits<Iter>::difference_type
distance_impl(Iter first, Iter last, random_access_iterator_tag) {
    std::cout << "  [随机访问迭代器] 使用减法计算距离" << std::endl;
    return last - first;
}

// 输入迭代器：逐步计数，O(n)
template<typename Iter>
typename std::iterator_traits<Iter>::difference_type
distance_impl(Iter first, Iter last, input_iterator_tag) {
    std::cout << "  [输入迭代器] 逐步计数" << std::endl;
    typename std::iterator_traits<Iter>::difference_type count = 0;
    while (first != last) {
        ++first;
        ++count;
    }
    return count;
}

/**
 * my_distance - 用户接口函数（避免与 std::distance 冲突）
 */
template<typename Iter>
typename std::iterator_traits<Iter>::difference_type
my_distance(Iter first, Iter last) {
    using category = typename std::iterator_traits<Iter>::iterator_category;
    return distance_impl(first, last, category{});
}

// ============================================================================
// 第五部分：使用标签分发实现算法优化
// ============================================================================

/**
 * copy_impl - 根据迭代器类别选择最优的拷贝算法
 */

// 连续内存的迭代器：使用 memmove
template<typename Iter>
Iter copy_impl(Iter first, Iter last, Iter d_first, random_access_iterator_tag) {
    std::cout << "  [随机访问迭代器] 使用优化拷贝" << std::endl;

    // 对于连续内存，可以直接使用 memmove
    // 这里简化处理，实际实现需要检查 is_contiguous
    auto n = last - first;
    for (decltype(n) i = 0; i < n; ++i) {
        d_first[i] = first[i];
    }
    return d_first + n;
}

// 普通迭代器：逐个拷贝
template<typename Iter>
Iter copy_impl(Iter first, Iter last, Iter d_first, input_iterator_tag) {
    std::cout << "  [输入迭代器] 逐个拷贝" << std::endl;

    while (first != last) {
        *d_first = *first;
        ++first;
        ++d_first;
    }
    return d_first;
}

/**
 * copy - 用户接口函数
 */
template<typename InputIt, typename OutputIt>
OutputIt copy(InputIt first, InputIt last, OutputIt d_first) {
    using category = typename std::iterator_traits<InputIt>::iterator_category;
    return copy_impl(first, last, d_first, category{});
}

// ============================================================================
// 第六部分：自定义标签分发 - 数值处理
// ============================================================================

/**
 * 使用自定义标签实现类型特定的处理
 */

// 整数处理
void process_value_impl(int value, int_tag) {
    std::cout << "  [整数] 值: " << value
              << ", 平方: " << (value * value) << std::endl;
}

// 浮点处理
void process_value_impl(double value, float_tag) {
    std::cout << "  [浮点] 值: " << value
              << ", 平方根: " << std::sqrt(value) << std::endl;
}

// 字符串处理
void process_value_impl(const std::string& value, string_tag) {
    std::cout << "  [字符串] 值: \"" << value
              << "\", 长度: " << value.length() << std::endl;
}

/**
 * process_value - 用户接口函数
 *
 * 自动推导类型标签并分发
 */
template<typename T>
void process_value(const T& value) {
    using tag = type_tag_of_t<T>;
    process_value_impl(value, tag{});
}

// ============================================================================
// 第七部分：策略模式标签
// ============================================================================

/**
 * 排序策略标签
 */
struct quick_sort_tag {};
struct merge_sort_tag {};
struct insertion_sort_tag {};

/**
 * sort_impl - 根据策略标签选择排序算法
 */

// 快速排序
template<typename RandomIt>
void sort_impl(RandomIt first, RandomIt last, quick_sort_tag) {
    std::cout << "  [快速排序] ";
    auto n = last - first;
    if (n <= 1) {
        std::cout << "无需排序" << std::endl;
        return;
    }

    // 简化的快速排序实现
    auto pivot = *(first + n / 2);
    auto mid1 = std::partition(first, last,
        [pivot](const auto& x) { return x < pivot; });
    auto mid2 = std::partition(mid1, last,
        [pivot](const auto& x) { return !(pivot < x); });

    sort_impl(first, mid1, quick_sort_tag{});
    sort_impl(mid2, last, quick_sort_tag{});
    std::cout << "完成" << std::endl;
}

// 归并排序
template<typename RandomIt>
void sort_impl(RandomIt first, RandomIt last, merge_sort_tag) {
    std::cout << "  [归并排序] ";
    auto n = last - first;
    if (n <= 1) {
        std::cout << "无需排序" << std::endl;
        return;
    }

    auto mid = first + n / 2;
    sort_impl(first, mid, merge_sort_tag{});
    sort_impl(mid, last, merge_sort_tag{});

    std::vector<typename RandomIt::value_type> temp;
    std::merge(first, mid, mid, last, std::back_inserter(temp));
    std::copy(temp.begin(), temp.end(), first);
    std::cout << "完成" << std::endl;
}

// 插入排序
template<typename RandomIt>
void sort_impl(RandomIt first, RandomIt last, insertion_sort_tag) {
    std::cout << "  [插入排序] ";
    for (auto i = first + 1; i != last; ++i) {
        auto key = *i;
        auto j = i - 1;
        while (j >= first && *j > key) {
            *(j + 1) = *j;
            --j;
        }
        *(j + 1) = key;
    }
    std::cout << "完成" << std::endl;
}

/**
 * sort_with_strategy - 使用指定策略排序
 */
template<typename RandomIt, typename Tag>
void sort_with_strategy(RandomIt first, RandomIt last, Tag tag) {
    sort_impl(first, last, tag);
}

// ============================================================================
// 第八部分：标签分发与 SFINAE 结合
// ============================================================================

/**
 * 有时我们需要根据多个条件来选择实现
 * 这时可以结合标签分发和 SFINAE
 */

// 容器操作标签
struct has_push_back_tag {};
struct has_push_front_tag {};
struct has_insert_tag {};

/**
 * container_add_impl - 根据容器能力选择添加元素的方式
 */

// 有 push_back 的容器
template<typename Container, typename T>
void container_add_impl(Container& c, T&& value, has_push_back_tag) {
    std::cout << "  使用 push_back" << std::endl;
    c.push_back(std::forward<T>(value));
}

// 有 push_front 的容器
template<typename Container, typename T>
void container_add_impl(Container& c, T&& value, has_push_front_tag) {
    std::cout << "  使用 push_front" << std::endl;
    c.push_front(std::forward<T>(value));
}

// 有 insert 的容器
template<typename Container, typename T>
void container_add_impl(Container& c, T&& value, has_insert_tag) {
    std::cout << "  使用 insert" << std::endl;
    c.insert(c.end(), std::forward<T>(value));
}

/**
 * 检测容器支持的操作（使用优先级避免歧义）
 *
 * 由于 list 同时有 push_back 和 push_front，直接检测会导致歧义
 * 使用优先级包装器解决：push_back > push_front > insert
 */

// 优先级标签
template<int N> struct priority_tag : priority_tag<N - 1> {};
template<> struct priority_tag<0> {};

// 最高优先级：有 push_back
template<typename T>
auto container_add_dispatch(priority_tag<2>, T& c, const typename T::value_type& value)
    -> decltype(c.push_back(value), void())
{
    std::cout << "  使用 push_back" << std::endl;
    c.push_back(value);
}

// 中等优先级：有 push_front
template<typename T>
auto container_add_dispatch(priority_tag<1>, T& c, const typename T::value_type& value)
    -> decltype(c.push_front(value), void())
{
    std::cout << "  使用 push_front" << std::endl;
    c.push_front(value);
}

// 最低优先级：使用 insert
template<typename T>
void container_add_dispatch(priority_tag<0>, T& c, const typename T::value_type& value) {
    std::cout << "  使用 insert" << std::endl;
    c.insert(c.end(), value);
}

/**
 * container_add - 用户接口函数
 */
template<typename Container, typename T>
void container_add(Container& c, T&& value) {
    container_add_dispatch(priority_tag<2>{}, c, std::forward<T>(value));
}

// ============================================================================
// 第九部分：标签分发的高级用法 - 多标签分发
// ============================================================================

/**
 * 有时需要根据多个类型来选择实现
 * 这时可以使用多个标签参数
 */

// 两个数的运算标签
struct arithmetic_tag {};
struct string_tag_for_concat {};

/**
 * 二元运算的标签分发
 */
template<typename T1, typename T2>
auto combine_impl(const T1& a, const T2& b, arithmetic_tag, arithmetic_tag) {
    std::cout << "  [算术运算] ";
    return a + b;
}

auto combine_impl(const std::string& a, const std::string& b,
                  string_tag_for_concat, string_tag_for_concat) {
    std::cout << "  [字符串拼接] ";
    return a + b;
}

auto combine_impl(const std::string& a, int b,
                  string_tag_for_concat, arithmetic_tag) {
    std::cout << "  [字符串+数字] ";
    return a + std::to_string(b);
}

/**
 * combine - 用户接口函数
 */
template<typename T1, typename T2>
auto combine(const T1& a, const T2& b) {
    // 简化的标签推导
    using tag1 = std::conditional_t<
        std::is_arithmetic_v<T1>,
        arithmetic_tag,
        string_tag_for_concat
    >;
    using tag2 = std::conditional_t<
        std::is_arithmetic_v<T2>,
        arithmetic_tag,
        string_tag_for_concat
    >;

    return combine_impl(a, b, tag1{}, tag2{});
}

// ============================================================================
// 辅助函数：打印容器
// ============================================================================

template<typename Container>
void print_container(const std::string& name, const Container& c) {
    std::cout << name << ": [";
    bool first = true;
    for (const auto& elem : c) {
        if (!first) std::cout << ", ";
        std::cout << elem;
        first = false;
    }
    std::cout << "]" << std::endl;
}

// ============================================================================
// 主函数：演示各种标签分发技术
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "标签分发 (Tag Dispatching) 技术演示" << std::endl;
    std::cout << "========================================" << std::endl;

    // ---- 第一部分：迭代器 advance 演示 ----
    std::cout << "\n--- 1. 迭器 advance 演示 ---" << std::endl;

    // 随机访问迭代器 (vector)
    std::vector<int> vec = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
    auto vec_it = vec.begin();
    std::cout << "vector 迭代器:" << std::endl;
    advance(vec_it, 5);
    std::cout << "  当前值: " << *vec_it << std::endl;

    // 双向迭代器 (list)
    std::list<int> lst = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
    auto lst_it = lst.begin();
    std::cout << "list 迭代器:" << std::endl;
    advance(lst_it, 5);
    std::cout << "  当前值: " << *lst_it << std::endl;

    // ---- 第二部分：迭代器 distance 演示 ----
    std::cout << "\n--- 2. 迭代器 distance 演示 ---" << std::endl;

    std::cout << "vector 迭代器距离:" << std::endl;
    auto vec_dist = my_distance(vec.begin(), vec.end());
    std::cout << "  距离: " << vec_dist << std::endl;

    std::cout << "list 迭代器距离:" << std::endl;
    auto lst_dist = my_distance(lst.begin(), lst.end());
    std::cout << "  距离: " << lst_dist << std::endl;

    // ---- 第三部分：自定义类型处理 ----
    std::cout << "\n--- 3. 自定义类型处理 ---" << std::endl;

    process_value(42);
    process_value(3.14);
    process_value(std::string("Hello, World!"));

    // ---- 第四部分：排序策略 ----
    std::cout << "\n--- 4. 排序策略 ---" << std::endl;

    std::vector<int> vec1 = {5, 3, 8, 1, 9, 2, 7, 4, 6};
    std::vector<int> vec2 = {5, 3, 8, 1, 9, 2, 7, 4, 6};
    std::vector<int> vec3 = {5, 3, 8, 1, 9, 2, 7, 4, 6};

    std::cout << "原始数据: ";
    print_container("", vec1);

    std::cout << "\n使用不同排序策略:" << std::endl;

    sort_with_strategy(vec1.begin(), vec1.end(), quick_sort_tag{});
    print_container("快排结果", vec1);

    sort_with_strategy(vec2.begin(), vec2.end(), merge_sort_tag{});
    print_container("归并结果", vec2);

    sort_with_strategy(vec3.begin(), vec3.end(), insertion_sort_tag{});
    print_container("插入结果", vec3);

    // ---- 第五部分：容器操作分发 ----
    std::cout << "\n--- 5. 容器操作分发 ---" << std::endl;

    std::vector<int> my_vec;
    std::list<int> my_list;

    std::cout << "向 vector 添加元素:" << std::endl;
    container_add(my_vec, 1);
    container_add(my_vec, 2);
    container_add(my_vec, 3);
    print_container("vector", my_vec);

    std::cout << "向 list 添加元素:" << std::endl;
    container_add(my_list, 10);
    container_add(my_list, 20);
    container_add(my_list, 30);
    print_container("list", my_list);

    // ---- 第六部分：多标签分发 ----
    std::cout << "\n--- 6. 多标签分发 ---" << std::endl;

    auto r1 = combine(10, 20);
    std::cout << "combine(10, 20) = " << r1 << std::endl;

    auto r2 = combine(3.14, 2.86);
    std::cout << "combine(3.14, 2.86) = " << r2 << std::endl;

    auto r3 = combine(std::string("Hello"), std::string(" World"));
    std::cout << "combine(\"Hello\", \" World\") = " << r3 << std::endl;

    auto r4 = combine(std::string("Count: "), 42);
    std::cout << "combine(\"Count: \", 42) = " << r4 << std::endl;

    // ---- 第七部分：性能对比 ----
    std::cout << "\n--- 7. 性能对比 ---" << std::endl;

    const int iterations = 10000000;

    // 随机访问迭代器 vs 输入迭代器
    std::vector<int> perf_vec(iterations, 1);

    auto start = std::chrono::high_resolution_clock::now();
    auto vec_it2 = perf_vec.begin();
    advance(vec_it2, iterations - 1);
    auto end = std::chrono::high_resolution_clock::now();
    auto vec_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::list<int> perf_lst(perf_vec.begin(), perf_vec.end());

    start = std::chrono::high_resolution_clock::now();
    auto lst_it2 = perf_lst.begin();
    advance(lst_it2, iterations - 1);
    end = std::chrono::high_resolution_clock::now();
    auto lst_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "随机访问迭代器 advance: " << vec_time.count() << " 微秒" << std::endl;
    std::cout << "双向迭代器 advance: " << lst_time.count() << " 微秒" << std::endl;
    std::cout << "性能比: " << (double)lst_time.count() / vec_time.count() << "x" << std::endl;

    // ---- 总结 ----
    std::cout << "\n========================================" << std::endl;
    std::cout << "标签分发技术总结：" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "优点：" << std::endl;
    std::cout << "  1. 编译期选择，零运行时开销" << std::endl;
    std::cout << "  2. 代码清晰，易于理解" << std::endl;
    std::cout << "  3. 易于调试（函数名在调用栈中可见）" << std::endl;
    std::cout << "  4. 可以内联优化" << std::endl;
    std::cout << "缺点：" << std::endl;
    std::cout << "  1. 需要定义额外的标签类型" << std::endl;
    std::cout << "  2. 可能导致代码重复" << std::endl;
    std::cout << "应用场景：" << std::endl;
    std::cout << "  1. STL 迭代器和算法" << std::endl;
    std::cout << "  2. 类型特定的优化" << std::endl;
    std::cout << "  3. 策略模式的编译期实现" << std::endl;
    std::cout << "  4. 接口适配" << std::endl;

    return 0;
}
