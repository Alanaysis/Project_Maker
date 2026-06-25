/**
 * template_metaprogramming.cpp - 模板元编程 (Template Metaprogramming)
 *
 * 编译命令: g++ -std=c++17 -o template_metaprogramming template_metaprogramming.cpp
 *
 * 模板元编程 (TMP) 是利用 C++ 模板系统在编译期执行计算的技术。
 * 它的特点是"图灵完备"——理论上可以在编译期计算任何可计算的东西。
 *
 * 本文件演示:
 *   1. 编译期数学计算 (阶乘、斐波那契)
 *   2. 类型列表 (TypeList) 实现
 *   3. 编译期字符串操作
 *   4. constexpr 与模板元编程的结合
 *
 * 核心思想: 将运行时计算前移到编译期，以"换时间"为代价减少运行时开销。
 */

#include <iostream>
#include <string>
#include <type_traits>
#include <array>
#include <algorithm>
#include <numeric>
#include <cstdint>
#include <tuple>

// ============================================================================
// 第一部分: 编译期数学计算
// ============================================================================

/**
 * 编译期阶乘 - 经典模板递归
 *
 * 这是模板元编程的"Hello World"，展示了递归模板特化的基本模式:
 *   1. 通用模板: 定义递归关系
 *   2. 特化模板: 定义递归终止条件
 *
 * 编译器会在编译时展开所有递归，生成常量值。
 * 这是最早的模板元编程示例，由 Erwin Unruh 在 1994 年首次展示。
 */
template<int N>
struct Factorial {
    // 递归公式: N! = N * (N-1)!
    static constexpr long long value = N * Factorial<N - 1>::value;
};

// 特化: 递归终止条件, 0! = 1
template<>
struct Factorial<0> {
    static constexpr long long value = 1;
};

/**
 * 编译期阶乘 - constexpr 函数版本 (C++11+)
 *
 * constexpr 函数是 C++11 引入的，提供了更简洁的编译期计算语法。
 * 编译器会在编译时求值 constexpr 表达式，结果可作为模板参数或数组大小。
 *
 * 对比模板递归版本，constexpr 版本:
 *   - 语法更接近普通函数
 *   - 编译错误信息更友好
 *   - 可以同时用于编译期和运行时
 */
constexpr long long factorial(long long n) {
    // C++14+ 允许 constexpr 函数包含循环和局部变量
    long long result = 1;
    for (long long i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

/**
 * 编译期斐波那契数列 - 模板递归
 *
 * 递归关系: F(n) = F(n-1) + F(n-2)
 * 终止条件: F(0) = 0, F(1) = 1
 *
 * 模板递归的计算复杂度是 O(2^n)，因为每次递归都分裂为两个子问题。
 * 实际使用时应考虑加记忆化或使用 constexpr 函数。
 */
template<int N>
struct Fibonacci {
    static constexpr long long value = Fibonacci<N - 1>::value + Fibonacci<N - 2>::value;
};

template<>
struct Fibonacci<0> {
    static constexpr long long value = 0;
};

template<>
struct Fibonacci<1> {
    static constexpr long long value = 1;
};

/**
 * 编译期斐波那契 - 高效 constexpr 版本
 *
 * 使用迭代而非递归，复杂度为 O(n)。
 * 这是现代 C++ 推荐的编译期计算方式。
 */
constexpr long long fibonacci(int n) {
    if (n <= 1) return n;

    long long prev = 0, curr = 1;
    for (int i = 2; i <= n; ++i) {
        long long next = prev + curr;
        prev = curr;
        curr = next;
    }
    return curr;
}

/**
 * 编译期最大公约数 (GCD) - 欧几里得算法
 * 使用模板递归实现经典算法
 */
template<int A, int B>
struct GCD {
    // 递归: GCD(A, B) = GCD(B, A % B)
    static constexpr int value = GCD<B, A % B>::value;
};

template<int A>
struct GCD<A, 0> {
    // 终止: GCD(A, 0) = A
    static constexpr int value = A;
};

/**
 * 编译期幂运算
 * 使用模板递归实现快速幂的基础版本
 */
template<int Base, int Exp>
struct Power {
    static constexpr long long value = Base * Power<Base, Exp - 1>::value;
};

template<int Base>
struct Power<Base, 0> {
    static constexpr long long value = 1;
};

// ============================================================================
// 第二部分: 类型列表 (TypeList)
// ============================================================================

/**
 * 类型列表 (TypeList) - 编译期类型容器
 *
 * TypeList 是模板元编程中的核心数据结构，类似于运行时的列表/数组，
 * 但它存储的是类型而非值。通过 TypeList 可以在编译期操作类型集合。
 *
 * TypeList 的基本操作:
 *   - 头部 (Head): 列表的第一个类型
 *   - 尾部 (Tail): 除去第一个类型的剩余列表
 *   - 大小 (Size): 列表中类型的数量
 *   - 包含 (Contains): 检查某个类型是否在列表中
 *   - 追加 (Append): 在列表末尾添加类型
 *   - 索引访问 (At): 获取第 N 个类型
 */

// 基础 TypeList 定义
template<typename... Types>
struct TypeList {
    static constexpr size_t size = sizeof...(Types);
};

/**
 * 获取 TypeList 的头部类型
 * 通过偏特化匹配第一个类型
 */
template<typename List>
struct TypeListHead;

template<typename Head, typename... Tail>
struct TypeListHead<TypeList<Head, Tail...>> {
    using type = Head;
};

/**
 * 获取 TypeList 的尾部类型列表
 * 通过偏特化获取除去头部的剩余类型
 */
template<typename List>
struct TypeListTail;

template<typename Head, typename... Tail>
struct TypeListTail<TypeList<Head, Tail...>> {
    using type = TypeList<Tail...>;
};

/**
 * 向 TypeList 末尾追加类型
 * 使用参数包展开将新类型添加到末尾
 */
template<typename List, typename NewType>
struct TypeListAppend;

template<typename... Types, typename NewType>
struct TypeListAppend<TypeList<Types...>, NewType> {
    using type = TypeList<Types..., NewType>;
};

/**
 * 向 TypeList 头部插入类型
 * 将新类型作为新的头部
 */
template<typename List, typename NewType>
struct TypeListPrepend;

template<typename... Types, typename NewType>
struct TypeListPrepend<TypeList<Types...>, NewType> {
    using type = TypeList<NewType, Types...>;
};

/**
 * 获取 TypeList 中第 N 个类型
 * 使用递归模板实现编译期索引访问
 */
template<typename List, size_t N>
struct TypeListAt {
    // 递归: 去掉头部，N 减 1
    using type = typename TypeListAt<typename TypeListTail<List>::type, N - 1>::type;
};

template<typename List>
struct TypeListAt<List, 0> {
    // 终止: N == 0 时返回头部
    using type = typename TypeListHead<List>::type;
};

/**
 * 检查 TypeList 是否包含某个类型
 * 使用递归遍历实现
 */
template<typename List, typename Target>
struct TypeListContains;

// 空列表不包含任何类型
template<typename Target>
struct TypeListContains<TypeList<>, Target> {
    static constexpr bool value = false;
};

// 检查头部是否匹配，不匹配则递归检查尾部
template<typename Head, typename... Tail, typename Target>
struct TypeListContains<TypeList<Head, Tail...>, Target> {
    static constexpr bool value =
        std::is_same_v<Head, Target> ||
        TypeListContains<TypeList<Tail...>, Target>::value;
};

/**
 * 计算 TypeList 大小
 */
template<typename List>
struct TypeListSize;

template<typename... Types>
struct TypeListSize<TypeList<Types...>> {
    static constexpr size_t value = sizeof...(Types);
};

/**
 * TypeList 转换为 std::tuple
 * 展示 TypeList 如何与标准库结合使用
 */
template<typename List>
struct TypeListToTuple;

template<typename... Types>
struct TypeListToTuple<TypeList<Types...>> {
    using type = std::tuple<Types...>;
};

/**
 * 对 TypeList 中的每个类型应用变换
 * 类似于函数式编程中的 map 操作
 */
template<typename List, template<typename> class Transform>
struct TypeListTransform;

template<typename... Types, template<typename> class Transform>
struct TypeListTransform<TypeList<Types...>, Transform> {
    using type = TypeList<typename Transform<Types>::type...>;
};

/**
 * 筛选 TypeList 中满足条件的类型
 * 类似于函数式编程中的 filter 操作
 */
template<typename List, template<typename> class Predicate>
struct TypeListFilter;

// 基础情况: 空列表
template<template<typename> class Predicate>
struct TypeListFilter<TypeList<>, Predicate> {
    using type = TypeList<>;
};

// 递归情况: 检查头部是否满足条件
template<typename Head, typename... Tail, template<typename> class Predicate>
struct TypeListFilter<TypeList<Head, Tail...>, Predicate> {
    using filtered_tail = typename TypeListFilter<TypeList<Tail...>, Predicate>::type;
    using type = std::conditional_t<
        Predicate<Head>::value,
        typename TypeListPrepend<filtered_tail, Head>::type,
        filtered_tail
    >;
};

// ============================================================================
// 第三部分: 编译期字符串操作
// ============================================================================

/**
 * 编译期固定字符串
 *
 * C++20 之前，模板参数不能是字符串类型。
 * 通过将字符作为非类型模板参数，可以实现编译期字符串。
 *
 * 这个技巧在需要编译期字符串比较、哈希等场景非常有用。
 */
template<char... Chars>
struct CompileString {
    // 将字符包存储为静态数组
    static constexpr char value[] = {Chars..., '\0'};
    static constexpr size_t length = sizeof...(Chars);

    // 输出函数
    static void print() {
        std::cout << value;
    }
};

/**
 * 编译期字符串长度计算
 * 使用 constexpr 函数在编译期计算 C 风格字符串的长度
 */
constexpr size_t cstrlen(const char* str) {
    size_t len = 0;
    while (str[len] != '\0') {
        ++len;
    }
    return len;
}

/**
 * 编译期字符串比较
 * 使用 constexpr 函数在编译期比较两个字符串是否相等
 */
constexpr bool cstrcmp(const char* a, const char* b) {
    while (*a && *b) {
        if (*a != *b) return false;
        ++a;
        ++b;
    }
    return *a == *b;  // 两者都到达末尾才相等
}

/**
 * 编译期字符串哈希 - FNV-1a 算法
 *
 * FNV-1a 是一种简单高效的哈希算法，非常适合编译期使用。
 * 常用于编译期字符串到整数的映射，例如在 switch 语句中匹配字符串。
 *
 * 算法步骤:
 *   hash = offset_basis
 *   for each byte:
 *     hash = hash XOR byte
 *     hash = hash * FNV_prime
 */
constexpr uint32_t fnv1a_hash(const char* str) {
    // FNV-1a 参数 (32位)
    constexpr uint32_t FNV_OFFSET_BASIS = 2166136261u;
    constexpr uint32_t FNV_PRIME = 16777619u;

    uint32_t hash = FNV_OFFSET_BASIS;
    while (*str) {
        hash ^= static_cast<uint32_t>(*str);
        hash *= FNV_PRIME;
        ++str;
    }
    return hash;
}

/**
 * 编译期字符串连接
 * 使用 constexpr 函数在编译期连接两个字符串
 * 注意: 需要静态缓冲区存储结果
 */
template<size_t N1, size_t N2>
struct StringConcat {
    char result[N1 + N2 - 1];  // -1 因为只有一个 '\0'

    constexpr StringConcat(const char (&s1)[N1], const char (&s2)[N2]) : result{} {
        size_t i = 0;
        for (size_t j = 0; j < N1 - 1; ++j) result[i++] = s1[j];
        for (size_t j = 0; j < N2; ++j) result[i++] = s2[j];
    }
};

// 辅助函数推导模板参数
template<size_t N1, size_t N2>
constexpr auto concat_str(const char (&s1)[N1], const char (&s2)[N2]) {
    return StringConcat<N1, N2>(s1, s2);
}

// ============================================================================
// 第四部分: 编译期条件与类型选择
// ============================================================================

/**
 * 编译期条件选择 - 类型级别的 if-else
 *
 * std::conditional 是标准库提供的编译期条件类型选择器:
 *   - 如果条件为 true，选择第一个类型
 *   - 如果条件为 false，选择第二个类型
 *
 * 这是模板元编程中最常用的工具之一。
 */
template<bool Condition, typename TrueType, typename FalseType>
struct Conditional {
    using type = TrueType;
};

template<typename TrueType, typename FalseType>
struct Conditional<false, TrueType, FalseType> {
    using type = FalseType;
};

/**
 * 编译期类型移除
 * 移除类型中的引用、const、volatile 修饰
 */
template<typename T>
struct RemoveCVRef {
    using type = std::remove_cv_t<std::remove_reference_t<T>>;
};

/**
 * 编译期类型映射: 将 C++ 类型映射到描述字符串
 * 展示类型萃取的实际应用
 */
template<typename T>
struct TypeName;

// 基本类型特化
template<> struct TypeName<int>        { static constexpr const char* value = "int"; };
template<> struct TypeName<double>     { static constexpr const char* value = "double"; };
template<> struct TypeName<char>       { static constexpr const char* value = "char"; };
template<> struct TypeName<bool>       { static constexpr const char* value = "bool"; };
template<> struct TypeName<std::string>{ static constexpr const char* value = "std::string"; };

// 通用模板: 使用 typeid 获取运行时类型名
template<typename T>
struct TypeName {
    static constexpr const char* value = typeid(T).name();
};

// ============================================================================
// 第五部分: 编译期算法
// ============================================================================

/**
 * 编译期数组排序 - 选择排序
 *
 * 使用 constexpr 函数在编译期对数组进行排序。
 * C++14+ 的 constexpr 函数支持循环和局部变量，使得这类算法实现更直观。
 */
template<typename T, size_t N>
constexpr std::array<T, N> constexpr_sort(std::array<T, N> arr) {
    // 简单选择排序
    for (size_t i = 0; i < N - 1; ++i) {
        size_t min_idx = i;
        for (size_t j = i + 1; j < N; ++j) {
            if (arr[j] < arr[min_idx]) {
                min_idx = j;
            }
        }
        if (min_idx != i) {
            T temp = arr[i];
            arr[i] = arr[min_idx];
            arr[min_idx] = temp;
        }
    }
    return arr;
}

/**
 * 编译期查找
 * 在编译期数组中查找元素
 */
template<typename T, size_t N>
constexpr bool constexpr_find(const std::array<T, N>& arr, const T& target) {
    for (size_t i = 0; i < N; ++i) {
        if (arr[i] == target) return true;
    }
    return false;
}

/**
 * 编译期统计
 * 统计满足条件的元素数量
 */
template<typename T, size_t N, typename Pred>
constexpr size_t constexpr_count_if(const std::array<T, N>& arr, Pred pred) {
    size_t count = 0;
    for (size_t i = 0; i < N; ++i) {
        if (pred(arr[i])) ++count;
    }
    return count;
}

// ============================================================================
// 第六部分: 策略模式与策略选择
// ============================================================================

/**
 * 编译期策略选择
 * 根据类型特征选择不同的算法实现
 */

// 策略 A: 适用于算术类型，使用快速路径
struct FastStrategy {
    static constexpr const char* name = "快速策略";
    template<typename T>
    static T compute(T a, T b) { return a * b + a + b; }
};

// 策略 B: 适用于其他类型，使用通用路径
struct GeneralStrategy {
    static constexpr const char* name = "通用策略";
    template<typename T>
    static T compute(T a, T b) { return (a + 1) * (b + 1) - 1; }
};

// 根据类型特征选择策略
template<typename T>
using Strategy = std::conditional_t<std::is_arithmetic_v<T>, FastStrategy, GeneralStrategy>;

// ============================================================================
// 主函数: 演示所有功能
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  模板元编程 (Template Metaprogramming)" << std::endl;
    std::cout << "========================================" << std::endl;

    // --- 1. 编译期阶乘 ---
    std::cout << "\n--- 1. 编译期阶乘 ---" << std::endl;
    // 模板递归版本: 编译期求值
    std::cout << "Factorial<10>::value = " << Factorial<10>::value << std::endl;
    std::cout << "Factorial<20>::value = " << Factorial<20>::value << std::endl;

    // constexpr 函数版本
    std::cout << "factorial(10) = " << factorial(10) << std::endl;
    std::cout << "factorial(20) = " << factorial(20) << std::endl;

    // 验证编译期求值: 可用作数组大小
    int arr[Factorial<5>::value];  // 120 个元素的数组
    std::cout << "arr 大小 (Factorial<5>): " << sizeof(arr) / sizeof(arr[0]) << std::endl;

    // --- 2. 编译期斐波那契 ---
    std::cout << "\n--- 2. 编译期斐波那契 ---" << std::endl;
    std::cout << "Fibonacci 数列: ";

    // 注意: 模板参数必须是编译期常量，不能用运行时循环变量
    // 这里使用辅助函数 + index_sequence 在编译期展开
    // 展开 Fibonacci<0> 到 Fibonacci<15>
    [](auto... vals) {
        ((std::cout << vals << " "), ...);
    }(Fibonacci<0>::value, Fibonacci<1>::value, Fibonacci<2>::value,
      Fibonacci<3>::value, Fibonacci<4>::value, Fibonacci<5>::value,
      Fibonacci<6>::value, Fibonacci<7>::value, Fibonacci<8>::value,
      Fibonacci<9>::value, Fibonacci<10>::value, Fibonacci<11>::value,
      Fibonacci<12>::value, Fibonacci<13>::value, Fibonacci<14>::value,
      Fibonacci<15>::value);
    std::cout << std::endl;

    std::cout << "fibonacci(20) = " << fibonacci(20) << std::endl;
    std::cout << "fibonacci(30) = " << fibonacci(30) << std::endl;

    // --- 3. 其他编译期数学 ---
    std::cout << "\n--- 3. 编译期数学运算 ---" << std::endl;
    std::cout << "GCD(12, 8) = " << GCD<12, 8>::value << std::endl;
    std::cout << "GCD(100, 75) = " << GCD<100, 75>::value << std::endl;
    std::cout << "Power<2, 10> = " << Power<2, 10>::value << std::endl;
    std::cout << "Power<3, 5> = " << Power<3, 5>::value << std::endl;

    // --- 4. TypeList 操作 ---
    std::cout << "\n--- 4. 类型列表 (TypeList) ---" << std::endl;

    using MyTypes = TypeList<int, double, char, bool>;
    std::cout << "TypeList 大小: " << TypeListSize<MyTypes>::value << std::endl;

    // 头部和尾部
    std::cout << "头部类型是否为 int: "
              << std::boolalpha
              << std::is_same_v<TypeListHead<MyTypes>::type, int>
              << std::endl;

    // 索引访问
    std::cout << "第 0 个类型是否为 int: "
              << std::is_same_v<TypeListAt<MyTypes, 0>::type, int>
              << std::endl;
    std::cout << "第 2 个类型是否为 char: "
              << std::is_same_v<TypeListAt<MyTypes, 2>::type, char>
              << std::endl;

    // 追加类型
    using Extended = TypeListAppend<MyTypes, std::string>::type;
    std::cout << "追加 string 后大小: " << TypeListSize<Extended>::value << std::endl;

    // 包含检查
    std::cout << "包含 double: " << TypeListContains<MyTypes, double>::value << std::endl;
    std::cout << "包含 float: " << TypeListContains<MyTypes, float>::value << std::endl;

    // 转换为 tuple
    using MyTuple = TypeListToTuple<MyTypes>::type;
    MyTuple tuple_val{42, 3.14, 'A', true};
    std::cout << "tuple[0] (int): " << std::get<0>(tuple_val) << std::endl;

    // 类型变换: 将所有类型转换为 const 版本
    using ConstTypes = TypeListTransform<MyTypes, std::add_const>::type;
    std::cout << "变换后第 0 个类型是否为 const int: "
              << std::is_same_v<TypeListAt<ConstTypes, 0>::type, const int>
              << std::endl;

    // 类型筛选: 只保留算术类型
    using ArithmeticOnly = TypeListFilter<MyTypes, std::is_arithmetic>::type;
    std::cout << "筛选算术类型后大小: " << TypeListSize<ArithmeticOnly>::value << std::endl;

    // --- 5. 编译期字符串操作 ---
    std::cout << "\n--- 5. 编译期字符串操作 ---" << std::endl;

    // 编译期字符串长度
    constexpr size_t len = cstrlen("Hello, Template Metaprogramming!");
    std::cout << "字符串长度: " << len << std::endl;

    // 编译期字符串比较
    constexpr bool equal = cstrcmp("hello", "hello");
    constexpr bool not_equal = cstrcmp("hello", "world");
    std::cout << "\"hello\" == \"hello\": " << std::boolalpha << equal << std::endl;
    std::cout << "\"hello\" == \"world\": " << std::boolalpha << not_equal << std::endl;

    // 编译期哈希
    constexpr uint32_t hash1 = fnv1a_hash("Hello");
    constexpr uint32_t hash2 = fnv1a_hash("World");
    std::cout << "哈希 \"Hello\": " << hash1 << std::endl;
    std::cout << "哈希 \"World\": " << hash2 << std::endl;

    // 编译期字符串连接
    constexpr auto concat = concat_str("Hello, ", "World!");
    std::cout << "连接结果: " << concat.result << std::endl;

    // --- 6. 编译期数组操作 ---
    std::cout << "\n--- 6. 编译期数组算法 ---" << std::endl;

    // 编译期排序
    constexpr std::array<int, 6> unsorted = {5, 2, 8, 1, 9, 3};
    constexpr auto sorted = constexpr_sort(unsorted);
    std::cout << "排序前: ";
    for (const auto& v : unsorted) std::cout << v << " ";
    std::cout << std::endl;
    std::cout << "排序后: ";
    for (const auto& v : sorted) std::cout << v << " ";
    std::cout << std::endl;

    // 编译期查找
    constexpr bool found = constexpr_find(sorted, 8);
    constexpr bool not_found = constexpr_find(sorted, 99);
    std::cout << "查找 8: " << std::boolalpha << found << std::endl;
    std::cout << "查找 99: " << std::boolalpha << not_found << std::endl;

    // 编译期统计
    constexpr auto even_count = constexpr_count_if(sorted, [](int x) {
        return x % 2 == 0;
    });
    std::cout << "偶数个数: " << even_count << std::endl;

    // --- 7. 策略选择 ---
    std::cout << "\n--- 7. 编译期策略选择 ---" << std::endl;
    Strategy<int> int_strategy;
    std::cout << "int 策略: " << int_strategy.name << std::endl;
    std::cout << "compute(3, 4): " << int_strategy.compute(3, 4) << std::endl;

    Strategy<double> double_strategy;
    std::cout << "double 策略: " << double_strategy.name << std::endl;
    std::cout << "compute(3.0, 4.0): " << double_strategy.compute(3.0, 4.0) << std::endl;

    std::cout << "\n========================================" << std::endl;
    std::cout << "  演示结束" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
