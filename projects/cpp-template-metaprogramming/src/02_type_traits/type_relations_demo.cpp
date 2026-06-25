// =============================================================================
// type_relations_demo.cpp - 类型关系萃取演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o type_relations_demo type_relations_demo.cpp
// 运行: ./type_relations_demo
// =============================================================================

#include <iostream>
#include <string>
#include <vector>
#include "type_traits/type_relations.hpp"

// 用于测试的类层次
class Base {
public:
    virtual ~Base() = default;
    virtual void speak() const { std::cout << "Base" << std::endl; }
};

class Derived : public Base {
public:
    void speak() const override { std::cout << "Derived" << std::endl; }
};

class GrandChild : public Derived {
public:
    void speak() const override { std::cout << "GrandChild" << std::endl; }
};

class Unrelated {};

// 用于测试 is_invocable
struct Functor {
    int operator()(int x) { return x * 2; }
    double operator()(double x, double y) { return x + y; }
};

int main() {
    std::cout << "=== 类型关系萃取演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. is_same
    std::cout << "1. is_same:" << std::endl;
    static_assert(tmp::is_same_v<int, int>);
    static_assert(!tmp::is_same_v<int, double>);
    static_assert(!tmp::is_same_v<int, const int>);
    static_assert(tmp::is_same_v<int, tmp::remove_const_t<const int>>);
    std::cout << "  int == int: " << tmp::is_same_v<int, int> << std::endl;
    std::cout << "  int == double: " << tmp::is_same_v<int, double> << std::endl;
    std::cout << "  int == const int: " << tmp::is_same_v<int, const int> << std::endl;
    std::cout << std::endl;

    // 2. is_base_of
    std::cout << "2. is_base_of:" << std::endl;
    static_assert(tmp::is_base_of_v<Base, Derived>);
    static_assert(tmp::is_base_of_v<Base, GrandChild>);
    static_assert(tmp::is_base_of_v<Derived, GrandChild>);
    static_assert(!tmp::is_base_of_v<Derived, Base>);
    static_assert(!tmp::is_base_of_v<Base, Unrelated>);
    static_assert(tmp::is_base_of_v<Base, Base>);  // 自身是自身的基类
    std::cout << "  Base is base of Derived: " << tmp::is_base_of_v<Base, Derived> << std::endl;
    std::cout << "  Base is base of GrandChild: " << tmp::is_base_of_v<Base, GrandChild> << std::endl;
    std::cout << "  Derived is base of Base: " << tmp::is_base_of_v<Derived, Base> << std::endl;
    std::cout << std::endl;

    // 3. is_convertible
    std::cout << "3. is_convertible:" << std::endl;
    static_assert(tmp::is_convertible_v<int, double>);
    static_assert(!tmp::is_convertible_v<double, int>);  // 有损转换不隐式允许
    static_assert(tmp::is_convertible_v<Derived*, Base*>);
    static_assert(!tmp::is_convertible_v<Base*, Derived*>);
    static_assert(tmp::is_convertible_v<void, void>);
    std::cout << "  int -> double: " << tmp::is_convertible_v<int, double> << std::endl;
    std::cout << "  double -> int: " << tmp::is_convertible_v<double, int> << std::endl;
    std::cout << "  Derived* -> Base*: " << tmp::is_convertible_v<Derived*, Base*> << std::endl;
    std::cout << "  Base* -> Derived*: " << tmp::is_convertible_v<Base*, Derived*> << std::endl;
    std::cout << std::endl;

    // 4. is_invocable
    std::cout << "4. is_invocable:" << std::endl;
    static_assert(tmp::is_invocable_v<Functor, int>);
    static_assert(tmp::is_invocable_v<Functor, double, double>);
    static_assert(!tmp::is_invocable_v<Functor, std::string>);
    static_assert(tmp::is_invocable_v<decltype([](int x){ return x; }), int>);
    std::cout << "  Functor(int): " << tmp::is_invocable_v<Functor, int> << std::endl;
    std::cout << "  Functor(double, double): " << tmp::is_invocable_v<Functor, double, double> << std::endl;
    std::cout << "  Functor(string): " << tmp::is_invocable_v<Functor, std::string> << std::endl;
    std::cout << std::endl;

    // 5. is_assignable
    std::cout << "5. is_assignable:" << std::endl;
    static_assert(tmp::is_assignable_v<int&, int>);
    static_assert(tmp::is_assignable_v<std::string&, const char*>);
    static_assert(!tmp::is_assignable_v<int, int>);  // 不能赋值给右值
    std::cout << "  int& = int: " << tmp::is_assignable_v<int&, int> << std::endl;
    std::cout << "  string& = const char*: " << tmp::is_assignable_v<std::string&, const char*> << std::endl;
    std::cout << std::endl;

    // 6. is_constructible
    std::cout << "6. is_constructible:" << std::endl;
    static_assert(tmp::is_constructible_v<int, int>);
    static_assert(tmp::is_constructible_v<std::string, const char*>);
    static_assert(tmp::is_constructible_v<std::string, std::size_t, char>);
    static_assert(tmp::is_default_constructible_v<int>);
    static_assert(tmp::is_copy_constructible_v<std::string>);
    static_assert(tmp::is_move_constructible_v<std::unique_ptr<int>>);
    std::cout << "  int from int: " << tmp::is_constructible_v<int, int> << std::endl;
    std::cout << "  string from const char*: " << tmp::is_constructible_v<std::string, const char*> << std::endl;
    std::cout << "  string default constructible: " << tmp::is_default_constructible_v<std::string> << std::endl;
    std::cout << std::endl;

    // 7. 实际应用：条件重载
    std::cout << "7. 实际应用:" << std::endl;

    // 只接受可转换为 Base* 的指针
    auto process_base = [](auto* ptr) -> std::enable_if_t<
        tmp::is_base_of_v<Base, std::remove_pointer_t<decltype(ptr)>>, void> {
        ptr->speak();
    };

    Derived d;
    GrandChild g;
    process_base(&d);
    process_base(&g);
    // process_base(&Unrelated{});  // 编译错误
    std::cout << std::endl;

    // 8. 类型选择
    std::cout << "8. 类型选择:" << std::endl;

    // 选择更大的类型
    using BiggerType = tmp::conditional_t<(sizeof(int) > sizeof(double)), int, double>;
    std::cout << "  Bigger of int/double: "
              << (std::is_same_v<BiggerType, int> ? "int" : "double") << std::endl;

    // 选择指针或值
    template <typename T>
    using StorageType = tmp::conditional_t<
        sizeof(T) > 16,
        T*,  // 大对象用指针
        T    // 小对象直接存储
    >;

    struct Small { int x; };
    struct Large { int data[100]; };

    std::cout << "  StorageType<Small> is Small: "
              << std::is_same_v<StorageType<Small>, Small> << std::endl;
    std::cout << "  StorageType<Large> is Large*: "
              << std::is_same_v<StorageType<Large>, Large*> << std::endl;
    std::cout << std::endl;

    std::cout << "=== 类型关系萃取演示完成 ===" << std::endl;
    return 0;
}
