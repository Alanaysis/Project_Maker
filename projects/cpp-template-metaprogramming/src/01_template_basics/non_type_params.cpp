// =============================================================================
// non_type_params.cpp - 非类型模板参数 (Non-Type Template Parameters)
// =============================================================================
// 编译: g++ -std=c++17 -o non_type_params non_type_params.cpp
// 运行: ./non_type_params
// =============================================================================

#include <iostream>
#include <array>
#include <string>
#include <cstring>
#include <type_traits>

// ---------------------------------------------------------------------------
// 1. 整数非类型参数
// ---------------------------------------------------------------------------

// 固定大小的数组
template <typename T, std::size_t N>
class FixedArray {
public:
    constexpr std::size_t size() const { return N; }

    T& operator[](std::size_t i) { return data_[i]; }
    const T& operator[](std::size_t i) const { return data_[i]; }

    T* data() { return data_; }
    const T* data() const { return data_; }

    // 填充
    void fill(const T& value) {
        for (std::size_t i = 0; i < N; ++i) {
            data_[i] = value;
        }
    }

private:
    T data_[N]{};
};

// 编译期计算
template <std::size_t N>
constexpr std::size_t factorial() {
    if constexpr (N <= 1) return 1;
    else return N * factorial<N - 1>();
}

template <std::size_t N>
constexpr std::size_t fibonacci() {
    if constexpr (N <= 1) return N;
    else return fibonacci<N - 1>() + fibonacci<N - 2>();
}

// ---------------------------------------------------------------------------
// 2. 枚举非类型参数
// ---------------------------------------------------------------------------

enum class Color { Red, Green, Blue, Yellow, White, Black };

// 根据颜色返回名称
template <Color C>
constexpr const char* color_name() {
    if constexpr (C == Color::Red)    return "Red";
    if constexpr (C == Color::Green)  return "Green";
    if constexpr (C == Color::Blue)   return "Blue";
    if constexpr (C == Color::Yellow) return "Yellow";
    if constexpr (C == Color::White)  return "White";
    if constexpr (C == Color::Black)  return "Black";
    return "Unknown";
}

// 颜色值
template <Color C>
struct ColorValue {
    static constexpr Color value = C;
    static constexpr const char* name = color_name<C>();
};

// ---------------------------------------------------------------------------
// 3. 指针/引用非类型参数
// ---------------------------------------------------------------------------

// 全局变量用于演示
int global_x = 10;
int global_y = 20;

// 接受指针非类型参数
template <int* Ptr>
class PointerWrapper {
public:
    int& get() { return *Ptr; }
    const int& get() const { return *Ptr; }
};

// 接受函数指针非类型参数
template <typename T, T (*Func)(T, T)>
class BinaryOp {
public:
    static T apply(T a, T b) { return Func(a, b); }
};

// 操作函数
int add(int a, int b) { return a + b; }
int multiply(int a, int b) { return a * b; }

// ---------------------------------------------------------------------------
// 4. 布尔非类型参数
// ---------------------------------------------------------------------------

// 根据布尔值选择实现
template <typename T, bool Debug = false>
class Container {
public:
    void add(const T& value) {
        if constexpr (Debug) {
            std::cout << "  [DEBUG] Adding: " << value << std::endl;
        }
        data_.push_back(value);
    }

    std::size_t size() const {
        if constexpr (Debug) {
            std::cout << "  [DEBUG] Size: " << data_.size() << std::endl;
        }
        return data_.size();
    }

private:
    std::vector<T> data_;
};

// ---------------------------------------------------------------------------
// 5. C++20: 浮点数非类型参数
// ---------------------------------------------------------------------------
// C++20 允许浮点数作为非类型模板参数
// 这里使用 C++17 兼容的方式演示

// 使用整数比例模拟浮点数
template <std::intmax_t Num, std::intmax_t Den = 1>
struct Ratio {
    static constexpr std::intmax_t num = Num;
    static constexpr std::intmax_t den = Den;
    static constexpr double value = static_cast<double>(Num) / Den;
};

// 使用 Ratio 进行计算
template <typename R1, typename R2>
struct RatioAdd {
    using type = Ratio<R1::num * R2::den + R2::num * R1::den,
                       R1::den * R2::den>;
};

// ---------------------------------------------------------------------------
// 6. 字符串非类型参数 (C++17 技巧)
// ---------------------------------------------------------------------------

// 使用字符数组作为模板参数
template <const char* Str>
class StringTemplate {
public:
    static constexpr const char* value = Str;
    static constexpr std::size_t length() {
        std::size_t len = 0;
        while (Str[len] != '\0') ++len;
        return len;
    }
};

// 全局字符串常量
constexpr char hello_str[] = "Hello";
constexpr char world_str[] = "World";

// ---------------------------------------------------------------------------
// 7. 非类型参数的默认值
// ---------------------------------------------------------------------------

// 带默认非类型参数的模板
template <typename T,
          std::size_t Capacity = 16,
          bool ThreadSafe = false,
          bool Debug = false>
class Buffer {
public:
    constexpr std::size_t capacity() const { return Capacity; }

    bool push(const T& value) {
        if (size_ >= Capacity) {
            if constexpr (Debug) {
                std::cout << "  [DEBUG] Buffer full!" << std::endl;
            }
            return false;
        }
        data_[size_++] = value;
        return true;
    }

    std::size_t size() const { return size_; }
    bool empty() const { return size_ == 0; }
    bool full() const { return size_ >= Capacity; }

private:
    T data_[Capacity]{};
    std::size_t size_ = 0;
};

// ---------------------------------------------------------------------------
// 8. 编译期策略选择
// ---------------------------------------------------------------------------

// 排序策略
enum class SortPolicy { BubbleSort, InsertionSort, QuickSort };

template <SortPolicy Policy>
struct SortName;

template <>
struct SortName<SortPolicy::BubbleSort> {
    static constexpr const char* value = "BubbleSort";
};

template <>
struct SortName<SortPolicy::InsertionSort> {
    static constexpr const char* value = "InsertionSort";
};

template <>
struct SortName<SortPolicy::QuickSort> {
    static constexpr const char* value = "QuickSort";
};

// ---------------------------------------------------------------------------
// 9. 复合非类型参数
// ---------------------------------------------------------------------------

// 模板参数包作为非类型参数
template <int... Values>
struct IntegerSequence {
    static constexpr std::size_t size = sizeof...(Values);

    static constexpr int sum() {
        return (Values + ...);
    }

    static constexpr int product() {
        return (Values * ...);
    }
};

// ---------------------------------------------------------------------------
// 10. 非类型参数用于编译期断言
// ---------------------------------------------------------------------------

// 只接受正数
template <int N>
struct Positive {
    static_assert(N > 0, "N must be positive");
    static constexpr int value = N;
};

// 只接受 2 的幂
template <std::size_t N>
struct PowerOfTwo {
    static_assert(N > 0 && (N & (N - 1)) == 0, "N must be a power of 2");
    static constexpr std::size_t value = N;
};

// 范围检查
template <int Value, int Min, int Max>
struct ClampedValue {
    static_assert(Min <= Max, "Min must be <= Max");
    static_assert(Value >= Min && Value <= Max, "Value out of range");
    static constexpr int value = Value;
};

// ---------------------------------------------------------------------------
// 主函数
// ---------------------------------------------------------------------------

int main() {
    std::cout << "=== 非类型模板参数 ===" << std::endl;
    std::cout << std::endl;

    // 1. 整数非类型参数
    std::cout << "1. 整数非类型参数:" << std::endl;
    FixedArray<int, 5> arr;
    arr.fill(42);
    std::cout << "FixedArray<int, 5>: ";
    for (std::size_t i = 0; i < arr.size(); ++i) {
        std::cout << arr[i] << " ";
    }
    std::cout << std::endl;

    std::cout << "factorial<5>() = " << factorial<5>() << std::endl;
    std::cout << "factorial<10>() = " << factorial<10>() << std::endl;
    std::cout << "fibonacci<10>() = " << fibonacci<10>() << std::endl;
    std::cout << "fibonacci<20>() = " << fibonacci<20>() << std::endl;
    std::cout << std::endl;

    // 2. 枚举非类型参数
    std::cout << "2. 枚举非类型参数:" << std::endl;
    using Red = ColorValue<Color::Red>;
    using Blue = ColorValue<Color::Blue>;
    std::cout << "Red: " << Red::name << std::endl;
    std::cout << "Blue: " << Blue::name << std::endl;
    std::cout << std::endl;

    // 3. 指针/引用非类型参数
    std::cout << "3. 指针/引用非类型参数:" << std::endl;
    PointerWrapper<&global_x> pw;
    std::cout << "global_x via PointerWrapper: " << pw.get() << std::endl;
    pw.get() = 42;
    std::cout << "global_x after modification: " << global_x << std::endl;

    using AddOp = BinaryOp<int, add>;
    using MulOp = BinaryOp<int, multiply>;
    std::cout << "AddOp::apply(3, 4) = " << AddOp::apply(3, 4) << std::endl;
    std::cout << "MulOp::apply(3, 4) = " << MulOp::apply(3, 4) << std::endl;
    std::cout << std::endl;

    // 4. 布尔非类型参数
    std::cout << "4. 布尔非类型参数:" << std::endl;
    Container<int, true> debug_container;
    debug_container.add(1);
    debug_container.add(2);
    debug_container.size();

    Container<int, false> release_container;
    release_container.add(1);
    release_container.add(2);
    release_container.size();
    std::cout << std::endl;

    // 5. Ratio 模拟浮点
    std::cout << "5. Ratio (模拟浮点非类型参数):" << std::endl;
    using Half = Ratio<1, 2>;
    using Quarter = Ratio<1, 4>;
    using Sum = RatioAdd<Half, Quarter>::type;
    std::cout << "1/2 + 1/4 = " << Sum::num << "/" << Sum::den
              << " = " << Sum::value << std::endl;
    std::cout << std::endl;

    // 6. 字符串非类型参数
    std::cout << "6. 字符串非类型参数:" << std::endl;
    std::cout << "StringTemplate<hello_str>::value = "
              << StringTemplate<hello_str>::value << std::endl;
    std::cout << "StringTemplate<hello_str>::length() = "
              << StringTemplate<hello_str>::length() << std::endl;
    std::cout << std::endl;

    // 7. 默认非类型参数
    std::cout << "7. 默认非类型参数:" << std::endl;
    Buffer<int, 8, false, true> buf;
    for (int i = 0; i < 10; ++i) {
        if (!buf.push(i)) {
            std::cout << "  Buffer full at i=" << i << std::endl;
        }
    }
    std::cout << "  Buffer size: " << buf.size() << std::endl;
    std::cout << std::endl;

    // 8. 编译期策略
    std::cout << "8. 编译期策略选择:" << std::endl;
    std::cout << "BubbleSort: " << SortName<SortPolicy::BubbleSort>::value << std::endl;
    std::cout << "QuickSort: " << SortName<SortPolicy::QuickSort>::value << std::endl;
    std::cout << std::endl;

    // 9. 整数序列
    std::cout << "9. 整数序列:" << std::endl;
    using Seq = IntegerSequence<1, 2, 3, 4, 5>;
    std::cout << "Sequence size: " << Seq::size << std::endl;
    std::cout << "Sequence sum: " << Seq::sum() << std::endl;
    std::cout << "Sequence product: " << Seq::product() << std::endl;
    std::cout << std::endl;

    // 10. 编译期断言
    std::cout << "10. 编译期断言:" << std::endl;
    std::cout << "Positive<5>::value = " << Positive<5>::value << std::endl;
    std::cout << "PowerOfTwo<16>::value = " << PowerOfTwo<16>::value << std::endl;
    std::cout << "ClampedValue<5, 0, 10>::value = "
              << ClampedValue<5, 0, 10>::value << std::endl;
    // Positive<-1>  // 编译错误
    // PowerOfTwo<15>  // 编译错误
    std::cout << std::endl;

    std::cout << "=== 非类型模板参数演示完成 ===" << std::endl;
    return 0;
}
