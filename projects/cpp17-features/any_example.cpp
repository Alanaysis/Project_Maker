/**
 * @file any_example.cpp
 * @brief C++17 std::any 示例
 *
 * std::any 是一个可以存储任何类型值的容器。
 * 它提供了类型安全的类型擦除机制，是 void* 的现代替代品。
 *
 * 主要优势：
 * 1. 类型安全 - 运行时类型检查
 * 2. 值语义 - 自动管理内存
 * 3. 异常安全 - 提供异常安全保证
 */

#include <iostream>
#include <any>
#include <string>
#include <vector>
#include <map>
#include <functional>
#include <typeinfo>

// 1. 基本 any 使用
void basic_any_example() {
    std::cout << "\n[基本 any 使用]" << std::endl;

    // 创建空 any
    std::any a1;
    std::cout << "a1 has value: " << a1.has_value() << std::endl;

    // 存储不同类型的值
    std::any a2 = 42;
    std::any a3 = 3.14;
    std::any a4 = std::string("Hello");

    std::cout << "a2 type: " << a2.type().name() << std::endl;
    std::cout << "a3 type: " << a3.type().name() << std::endl;
    std::cout << "a4 type: " << a4.type().name() << std::endl;
}

// 2. 访问值
void access_value_example() {
    std::cout << "\n[访问值]" << std::endl;

    std::any a = 42;

    // 使用 std::any_cast（抛出异常如果类型错误）
    try {
        int value = std::any_cast<int>(a);
        std::cout << "int value: " << value << std::endl;

        // 这会抛出 std::bad_any_cast
        double wrong = std::any_cast<double>(a);
        (void)wrong;
    } catch (const std::bad_any_cast& e) {
        std::cout << "Exception: " << e.what() << std::endl;
    }

    // 使用指针版本（不抛出异常）
    if (auto* p = std::any_cast<int>(&a)) {
        std::cout << "int value: " << *p << std::endl;
    } else {
        std::cout << "not an int" << std::endl;
    }

    if (auto* p = std::any_cast<double>(&a)) {
        std::cout << "double value: " << *p << std::endl;
    } else {
        std::cout << "not a double" << std::endl;
    }
}

// 3. any 在容器中的使用
void any_in_container_example() {
    std::cout << "\n[any 在容器中]" << std::endl;

    // 存储不同类型的值
    std::vector<std::any> values;
    values.push_back(42);
    values.push_back(3.14);
    values.push_back(std::string("Hello"));
    values.push_back(true);

    // 遍历并处理
    for (const auto& v : values) {
        if (auto* p = std::any_cast<int>(&v)) {
            std::cout << "int: " << *p << std::endl;
        } else if (auto* p = std::any_cast<double>(&v)) {
            std::cout << "double: " << *p << std::endl;
        } else if (auto* p = std::any_cast<std::string>(&v)) {
            std::cout << "string: " << *p << std::endl;
        } else if (auto* p = std::any_cast<bool>(&v)) {
            std::cout << "bool: " << *p << std::endl;
        }
    }
}

// 4. any 作为配置值
void config_example() {
    std::cout << "\n[配置示例]" << std::endl;

    // 使用 any 存储配置值
    std::map<std::string, std::any> config;
    config["hostname"] = std::string("localhost");
    config["port"] = 8080;
    config["debug"] = true;
    config["timeout"] = 30.5;

    // 获取并使用配置值
    auto hostname_any = config["hostname"];
    auto port_any = config["port"];
    auto debug_any = config["debug"];

    if (auto* hostname = std::any_cast<std::string>(&hostname_any)) {
        std::cout << "hostname: " << *hostname << std::endl;
    }

    if (auto* port = std::any_cast<int>(&port_any)) {
        std::cout << "port: " << *port << std::endl;
    }

    if (auto* debug = std::any_cast<bool>(&debug_any)) {
        std::cout << "debug: " << (*debug ? "true" : "false") << std::endl;
    }
}

// 5. any 与类型擦除
void type_erasure_example() {
    std::cout << "\n[类型擦除]" << std::endl;

    // 使用 any 存储函数
    std::any func_any = std::function<int(int, int)>([](int a, int b) { return a + b; });

    // 获取并调用函数
    auto func = std::any_cast<std::function<int(int, int)>>(func_any);
    std::cout << "func(1, 2) = " << func(1, 2) << std::endl;

    // 存储不同类型的函数
    std::any greet_any = std::function<std::string(const std::string&)>(
        [](const std::string& name) { return "Hello, " + name + "!"; }
    );

    auto greet = std::any_cast<std::function<std::string(const std::string&)>>(greet_any);
    std::cout << "greet(\"World\") = " << greet("World") << std::endl;
}

// 6. any 的修改和重置
void modify_any_example() {
    std::cout << "\n[修改和重置]" << std::endl;

    std::any a = 42;
    std::cout << "initial: " << std::any_cast<int>(a) << std::endl;

    // 赋新值
    a = 3.14;
    std::cout << "after assignment: " << std::any_cast<double>(a) << std::endl;

    // 使用 emplace
    a.emplace<std::string>("Hello");
    std::cout << "after emplace: " << std::any_cast<std::string>(a) << std::endl;

    // 重置为空
    a.reset();
    std::cout << "after reset: " << a.has_value() << std::endl;

    // 使用 swap
    std::any a1 = 1;
    std::any a2 = 2;
    std::cout << "before swap: a1=" << std::any_cast<int>(a1)
              << ", a2=" << std::any_cast<int>(a2) << std::endl;

    a1.swap(a2);
    std::cout << "after swap: a1=" << std::any_cast<int>(a1)
              << ", a2=" << std::any_cast<int>(a2) << std::endl;
}

// 7. any 存储复杂类型
struct Person {
    std::string name;
    int age;

    Person(const std::string& n, int a) : name(n), age(a) {}
};

std::ostream& operator<<(std::ostream& os, const Person& p) {
    return os << "Person{name=" << p.name << ", age=" << p.age << "}";
}

void complex_type_example() {
    std::cout << "\n[复杂类型]" << std::endl;

    // 存储自定义类型
    std::any a = Person("Alice", 30);
    std::cout << "Person: " << std::any_cast<Person>(a) << std::endl;

    // 存储容器
    std::any vec = std::vector<int>{1, 2, 3, 4, 5};
    auto& v = std::any_cast<std::vector<int>&>(vec);
    std::cout << "Vector: ";
    for (int i : v) {
        std::cout << i << " ";
    }
    std::cout << std::endl;

    // 存储函数
    std::any func = std::function<int(int, int)>([](int a, int b) { return a + b; });
    auto f = std::any_cast<std::function<int(int, int)>>(func);
    std::cout << "Function result: " << f(3, 4) << std::endl;
}

// 8. any 的拷贝和移动
void copy_move_example() {
    std::cout << "\n[拷贝和移动]" << std::endl;

    std::any a1 = 42;
    std::cout << "a1: " << std::any_cast<int>(a1) << std::endl;

    // 拷贝
    std::any a2 = a1;
    std::cout << "a2 (copy): " << std::any_cast<int>(a2) << std::endl;

    // 移动
    std::any a3 = std::move(a1);
    std::cout << "a3 (moved): " << std::any_cast<int>(a3) << std::endl;
    std::cout << "a1 after move: " << a1.has_value() << std::endl;

    // 拷贝赋值
    std::any a4;
    a4 = a2;
    std::cout << "a4 (copy assigned): " << std::any_cast<int>(a4) << std::endl;

    // 移动赋值
    std::any a5;
    a5 = std::move(a2);
    std::cout << "a5 (move assigned): " << std::any_cast<int>(a5) << std::endl;
}

// 9. any 与 RTTI
void rtti_example() {
    std::cout << "\n[RTTI 示例]" << std::endl;

    std::any a = 42;

    // 获取类型信息
    std::cout << "type: " << a.type().name() << std::endl;

    // 类型检查
    if (a.type() == typeid(int)) {
        std::cout << "is int" << std::endl;
    } else if (a.type() == typeid(double)) {
        std::cout << "is double" << std::endl;
    } else if (a.type() == typeid(std::string)) {
        std::cout << "is string" << std::endl;
    }
}

// 主示例函数
void any_example() {
    std::cout << "=== std::any ===" << std::endl;

    basic_any_example();
    access_value_example();
    any_in_container_example();
    config_example();
    type_erasure_example();
    modify_any_example();
    complex_type_example();
    copy_move_example();
    rtti_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    any_example();
    return 0;
}
#endif
