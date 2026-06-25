// =============================================================================
// specialization.cpp - 模板特化 (Template Specialization)
// =============================================================================
// 编译: g++ -std=c++17 -o specialization specialization.cpp
// 运行: ./specialization
// =============================================================================

#include <iostream>
#include <string>
#include <vector>
#include <type_traits>
#include <cstring>

// ---------------------------------------------------------------------------
// 1. 函数模板全特化
// ---------------------------------------------------------------------------

// 通用版本
template <typename T>
T max_value(T a, T b) {
    std::cout << "  [generic] ";
    return (a > b) ? a : b;
}

// const char* 全特化：使用 strcmp 比较
template <>
const char* max_value<const char*>(const char* a, const char* b) {
    std::cout << "  [const char* specialization] ";
    return (std::strcmp(a, b) > 0) ? a : b;
}

// ---------------------------------------------------------------------------
// 2. 类模板全特化
// ---------------------------------------------------------------------------

// 通用版本
template <typename T>
class TypeDescriptor {
public:
    static std::string name() { return "unknown"; }
    static constexpr std::size_t size() { return sizeof(T); }
    static constexpr bool is_fundamental() { return false; }
};

// int 全特化
template <>
class TypeDescriptor<int> {
public:
    static std::string name() { return "int"; }
    static constexpr std::size_t size() { return sizeof(int); }
    static constexpr bool is_fundamental() { return true; }
};

// double 全特化
template <>
class TypeDescriptor<double> {
public:
    static std::string name() { return "double"; }
    static constexpr std::size_t size() { return sizeof(double); }
    static constexpr bool is_fundamental() { return true; }
};

// std::string 全特化
template <>
class TypeDescriptor<std::string> {
public:
    static std::string name() { return "std::string"; }
    static constexpr std::size_t size() { return sizeof(std::string); }
    static constexpr bool is_fundamental() { return false; }
};

// ---------------------------------------------------------------------------
// 3. 类模板偏特化
// ---------------------------------------------------------------------------

// 通用版本：存储器
template <typename T>
class Storage {
public:
    Storage() : value_{} { std::cout << "  [generic Storage]" << std::endl; }
    void set(const T& v) { value_ = v; }
    T get() const { return value_; }

protected:
    T value_;
};

// 指针偏特化
template <typename T>
class Storage<T*> {
public:
    Storage() : ptr_(nullptr) { std::cout << "  [pointer Storage]" << std::endl; }
    ~Storage() { delete ptr_; }

    void set(T* p) {
        delete ptr_;
        ptr_ = p;
    }

    T* get() const { return ptr_; }

    // 指针特有的方法
    bool is_null() const { return ptr_ == nullptr; }
    T& dereference() { return *ptr_; }

protected:
    T* ptr_;
};

// 引用偏特化
template <typename T>
class Storage<T&> {
public:
    Storage(T& ref) : ref_(ref) { std::cout << "  [reference Storage]" << std::endl; }
    void set(const T& v) { ref_ = v; }
    T& get() const { return ref_; }

protected:
    T& ref_;
};

// 数组偏特化
template <typename T, std::size_t N>
class Storage<T[N]> {
public:
    Storage() { std::cout << "  [array Storage]" << std::endl; }

    void set(std::size_t index, const T& value) {
        if (index < N) data_[index] = value;
    }

    T get(std::size_t index) const {
        return (index < N) ? data_[index] : T{};
    }

    constexpr std::size_t size() const { return N; }

protected:
    T data_[N]{};
};

// ---------------------------------------------------------------------------
// 4. 多参数偏特化
// ---------------------------------------------------------------------------

// 通用版本
template <typename T, typename U>
class Pair {
public:
    Pair(T first, U second) : first_(std::move(first)), second_(std::move(second)) {}

    void print() const {
        std::cout << "(" << first_ << ", " << second_ << ")" << std::endl;
    }

protected:
    T first_;
    U second_;
};

// 两个类型相同时的偏特化
template <typename T>
class Pair<T, T> {
public:
    Pair(T first, T second) : first_(std::move(first)), second_(std::move(second)) {}

    void print() const {
        std::cout << "Same-type pair: (" << first_ << ", " << second_ << ")" << std::endl;
    }

    // 同类型特有的方法
    T sum() const { return first_ + second_; }

protected:
    T first_;
    T second_;
};

// 第一个参数为指针时的偏特化
template <typename T, typename U>
class Pair<T*, U> {
public:
    Pair(T* first, U second) : first_(first), second_(std::move(second)) {}

    void print() const {
        if (first_) {
            std::cout << "(ptr:" << *first_ << ", " << second_ << ")" << std::endl;
        } else {
            std::cout << "(nullptr, " << second_ << ")" << std::endl;
        }
    }

protected:
    T* first_;
    U second_;
};

// ---------------------------------------------------------------------------
// 5. 模板特化的匹配规则
// ---------------------------------------------------------------------------

// 演示特化优先级
template <typename T>
void process(T) {
    std::cout << "  Generic process" << std::endl;
}

// 全特化
template <>
void process<int>(int) {
    std::cout << "  Specialized process for int" << std::endl;
}

template <>
void process<double>(double) {
    std::cout << "  Specialized process for double" << std::endl;
}

// 非模板重载（优先级最高）
void process(float) {
    std::cout << "  Non-template overload for float" << std::endl;
}

// ---------------------------------------------------------------------------
// 6. 偏特化用于类型萃取
// ---------------------------------------------------------------------------

// 检查是否为容器
template <typename T>
struct is_container : std::false_type {};

template <typename T, typename Alloc>
struct is_container<std::vector<T, Alloc>> : std::true_type {};

template <typename T>
struct is_container<std::vector<T>> : std::true_type {};

// 检查是否为智能指针
template <typename T>
struct is_smart_pointer : std::false_type {};

template <typename T>
struct is_smart_pointer<std::unique_ptr<T>> : std::true_type {};

template <typename T>
struct is_smart_pointer<std::shared_ptr<T>> : std::true_type {};

// ---------------------------------------------------------------------------
// 7. 递归特化
// ---------------------------------------------------------------------------

// 编译期类型列表
template <typename... Ts>
struct TypeList {};

// 获取第一个类型
template <typename List>
struct Front;

template <typename Head, typename... Tail>
struct Front<TypeList<Head, Tail...>> {
    using type = Head;
};

// 递归特化
template <typename List>
struct Size;

template <>
struct Size<TypeList<>> {
    static constexpr std::size_t value = 0;
};

template <typename Head, typename... Tail>
struct Size<TypeList<Head, Tail...>> {
    static constexpr std::size_t value = 1 + Size<TypeList<Tail...>>::value;
};

// ---------------------------------------------------------------------------
// 8. 条件特化
// ---------------------------------------------------------------------------

// 根据类型特征选择不同的实现
template <typename T, bool = std::is_arithmetic_v<T>>
struct OptimizedProcessor;

// 算术类型的优化实现
template <typename T>
struct OptimizedProcessor<T, true> {
    static T process(T value) {
        std::cout << "  [optimized arithmetic] ";
        return value * 2;
    }
};

// 非算术类型的通用实现
template <typename T>
struct OptimizedProcessor<T, false> {
    static T process(T value) {
        std::cout << "  [generic] ";
        return value;
    }
};

// ---------------------------------------------------------------------------
// 主函数
// ---------------------------------------------------------------------------

int main() {
    std::cout << "=== C++ 模板特化 ===" << std::endl;
    std::cout << std::endl;

    // 1. 函数模板全特化
    std::cout << "1. 函数模板全特化:" << std::endl;
    std::cout << "max(3, 5) = " << max_value(3, 5) << std::endl;
    std::cout << "max(\"hello\", \"world\") = " << max_value("hello", "world") << std::endl;
    std::cout << std::endl;

    // 2. 类模板全特化
    std::cout << "2. 类模板全特化:" << std::endl;
    std::cout << "int: " << TypeDescriptor<int>::name()
              << ", size=" << TypeDescriptor<int>::size()
              << ", fundamental=" << TypeDescriptor<int>::is_fundamental() << std::endl;
    std::cout << "double: " << TypeDescriptor<double>::name()
              << ", size=" << TypeDescriptor<double>::size()
              << ", fundamental=" << TypeDescriptor<double>::is_fundamental() << std::endl;
    std::cout << "string: " << TypeDescriptor<std::string>::name()
              << ", size=" << TypeDescriptor<std::string>::size()
              << ", fundamental=" << TypeDescriptor<std::string>::is_fundamental() << std::endl;
    std::cout << "vector<int>: " << TypeDescriptor<std::vector<int>>::name()
              << ", size=" << TypeDescriptor<std::vector<int>>::size() << std::endl;
    std::cout << std::endl;

    // 3. 类模板偏特化
    std::cout << "3. 类模板偏特化:" << std::endl;
    Storage<int> s1;
    s1.set(42);
    std::cout << "  Storage<int> value: " << s1.get() << std::endl;

    Storage<int*> s2;
    s2.set(new int(100));
    std::cout << "  Storage<int*> value: " << *s2.get() << std::endl;
    std::cout << "  Storage<int*> is_null: " << s2.is_null() << std::endl;

    int arr[] = {1, 2, 3, 4, 5};
    Storage<int[5]> s3;
    for (std::size_t i = 0; i < 5; ++i) s3.set(i, arr[i]);
    std::cout << "  Storage<int[5]>: ";
    for (std::size_t i = 0; i < 5; ++i) std::cout << s3.get(i) << " ";
    std::cout << std::endl;
    std::cout << std::endl;

    // 4. 多参数偏特化
    std::cout << "4. 多参数偏特化:" << std::endl;
    Pair<int, double> p1(1, 3.14);
    p1.print();

    Pair<int, int> p2(3, 4);
    p2.print();
    std::cout << "  sum = " << p2.sum() << std::endl;

    int x = 42;
    Pair<int*, std::string> p3(&x, "hello");
    p3.print();
    std::cout << std::endl;

    // 5. 特化匹配规则
    std::cout << "5. 特化匹配规则:" << std::endl;
    process(42);        // 选择全特化 int
    process(3.14);      // 选择全特化 double
    process(3.14f);     // 选择非模板重载
    process("hello");   // 选择通用模板
    std::cout << std::endl;

    // 6. 类型萃取
    std::cout << "6. 偏特化用于类型萃取:" << std::endl;
    std::cout << "vector<int> is container: " << is_container<std::vector<int>>::value << std::endl;
    std::cout << "int is container: " << is_container<int>::value << std::endl;
    std::cout << "unique_ptr<int> is smart pointer: "
              << is_smart_pointer<std::unique_ptr<int>>::value << std::endl;
    std::cout << "int* is smart pointer: " << is_smart_pointer<int*>::value << std::endl;
    std::cout << std::endl;

    // 7. 递归特化
    std::cout << "7. 递归特化:" << std::endl;
    using MyList = TypeList<int, double, std::string>;
    std::cout << "TypeList<int, double, string> size: " << Size<MyList>::value << std::endl;
    using First = Front<MyList>::type;
    std::cout << "First type is int: " << std::is_same_v<First, int> << std::endl;
    std::cout << std::endl;

    // 8. 条件特化
    std::cout << "8. 条件特化:" << std::endl;
    std::cout << "process(42): " << OptimizedProcessor<int>::process(42) << std::endl;
    std::cout << "process(\"hello\"): "
              << OptimizedProcessor<std::string>::process("hello") << std::endl;
    std::cout << std::endl;

    std::cout << "=== 模板特化演示完成 ===" << std::endl;
    return 0;
}
