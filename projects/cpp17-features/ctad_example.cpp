/**
 * @file ctad_example.cpp
 * @brief C++17 类模板参数推导（CTAD）示例
 *
 * CTAD（Class Template Argument Deduction）允许编译器从构造函数参数
 * 自动推导类模板参数，无需显式指定模板参数。
 *
 * 主要优势：
 * 1. 代码简洁 - 无需重复指定模板参数
 * 2. 可读性好 - 更直观的类型表达
 * 3. 减少冗余 - 避免冗长的模板参数列表
 */

#include <iostream>
#include <vector>
#include <map>
#include <string>
#include <tuple>
#include <utility>
#include <optional>
#include <variant>
#include <functional>
#include <algorithm>
#include <numeric>
#include <set>
#include <unordered_map>

// 1. 基本 CTAD
void basic_ctad_example() {
    std::cout << "\n[基本 CTAD]" << std::endl;

    // C++17 之前
    std::vector<int> vec1 = {1, 2, 3, 4, 5};
    std::pair<int, std::string> pair1 = {1, "Hello"};
    std::tuple<int, double, std::string> tuple1 = {1, 3.14, "World"};

    // C++17 CTAD
    std::vector vec2 = {1, 2, 3, 4, 5};  // 推导为 std::vector<int>
    std::pair pair2 = {1, std::string("Hello")};  // 推导为 std::pair<int, std::string>
    std::tuple tuple2 = {1, 3.14, std::string("World")};  // 推导为 std::tuple<int, double, std::string>

    std::cout << "vec2: ";
    for (int v : vec2) std::cout << v << " ";
    std::cout << std::endl;

    std::cout << "pair2: " << pair2.first << ", " << pair2.second << std::endl;

    std::cout << "tuple2: " << std::get<0>(tuple2) << ", "
              << std::get<1>(tuple2) << ", " << std::get<2>(tuple2) << std::endl;
}

// 2. std::pair 和 std::tuple
void pair_tuple_example() {
    std::cout << "\n[std::pair 和 std::tuple]" << std::endl;

    // std::pair
    std::pair p1 = {1, 2.5};
    std::pair p2 = {std::string("Hello"), 42};
    std::pair p3 = {true, std::vector<int>{1, 2, 3}};

    std::cout << "p1: " << p1.first << ", " << p1.second << std::endl;
    std::cout << "p2: " << p2.first << ", " << p2.second << std::endl;

    // std::tuple
    std::tuple t1 = {1, 2.5, std::string("Hello")};
    std::tuple t2 = {std::vector<int>{1, 2, 3}, std::map<std::string, int>{{"a", 1}}};

    std::cout << "t1: " << std::get<0>(t1) << ", "
              << std::get<1>(t1) << ", " << std::get<2>(t1) << std::endl;

    // 使用 std::make_pair 和 std::make_tuple（C++17 之前）
    auto p4 = std::make_pair(1, 2.5);
    auto t3 = std::make_tuple(1, 2.5, std::string("Hello"));

    // C++17 直接使用花括号
    std::pair p5 = {1, 2.5};
    std::tuple t4 = {1, 2.5, std::string("Hello")};
}

// 3. std::vector 和其他容器
void container_example() {
    std::cout << "\n[std::vector 和其他容器]" << std::endl;

    // std::vector
    std::vector vec1 = {1, 2, 3, 4, 5};
    std::vector vec2 = {1.0, 2.0, 3.0};
    std::vector vec3 = {std::string("Hello"), std::string("World")};

    std::cout << "vec1: ";
    for (int v : vec1) std::cout << v << " ";
    std::cout << std::endl;

    // std::map
    std::map map1 = {std::pair{1, "one"}, std::pair{2, "two"}, std::pair{3, "three"}};
    std::map map2 = {std::pair{std::string("a"), 1}, std::pair{std::string("b"), 2}};

    std::cout << "map1: ";
    for (const auto& [key, value] : map1) {
        std::cout << key << "=" << value << " ";
    }
    std::cout << std::endl;

    // 使用初始化列表
    std::vector vec4 = {1, 2, 3};  // std::vector<int>
    std::set set1 = {3, 1, 4, 1, 5};  // std::set<int>
    std::unordered_map umap = {std::pair{1, "one"}, std::pair{2, "two"}};
}

// 4. 自定义类模板
template <typename T>
class Container {
public:
    Container(std::initializer_list<T> init) : data_(init) {}

    void print() const {
        for (const auto& item : data_) {
            std::cout << item << " ";
        }
        std::cout << std::endl;
    }

private:
    std::vector<T> data_;
};

// 用户定义的推导指引（C++17）
template <typename T>
Container(std::initializer_list<T>) -> Container<T>;

void custom_class_example() {
    std::cout << "\n[自定义类模板]" << std::endl;

    // 使用 CTAD
    Container c1 = {1, 2, 3, 4, 5};
    Container c2 = {1.0, 2.0, 3.0};
    Container c3 = {std::string("Hello"), std::string("World")};

    std::cout << "c1: ";
    c1.print();

    std::cout << "c2: ";
    c2.print();

    std::cout << "c3: ";
    c3.print();
}

// 5. 推导指引
template <typename T>
class Wrapper {
public:
    Wrapper(T value) : value_(value) {}

    T get() const { return value_; }

private:
    T value_;
};

// 用户定义的推导指引
template <typename T>
Wrapper(T) -> Wrapper<T>;

void deduction_guide_example() {
    std::cout << "\n[推导指引]" << std::endl;

    // 使用推导指引
    Wrapper w1(42);
    Wrapper w2(3.14);
    Wrapper w3(std::string("Hello"));

    std::cout << "w1: " << w1.get() << std::endl;
    std::cout << "w2: " << w2.get() << std::endl;
    std::cout << "w3: " << w3.get() << std::endl;
}

// 6. std::optional 和 std::variant
void optional_variant_example() {
    std::cout << "\n[std::optional 和 std::variant]" << std::endl;

    // std::optional
    std::optional opt1 = 42;
    std::optional opt2 = std::string("Hello");
    std::optional opt3 = 3.14;

    std::cout << "opt1: " << opt1.value() << std::endl;
    std::cout << "opt2: " << opt2.value() << std::endl;

    // std::variant
    std::variant<int, double, std::string> var1 = 42;
    std::variant<int, double, std::string> var2 = 3.14;
    std::variant<int, double, std::string> var3 = std::string("Hello");

    std::cout << "var1: " << std::get<int>(var1) << std::endl;
    std::cout << "var2: " << std::get<double>(var2) << std::endl;
    std::cout << "var3: " << std::get<std::string>(var3) << std::endl;
}

// 7. 函数对象和 lambda
void function_object_example() {
    std::cout << "\n[函数对象和 lambda]" << std::endl;

    // Lambda 包装器
    auto add = [](int a, int b) { return a + b; };
    std::function func = add;

    std::cout << "func(3, 4) = " << func(3, 4) << std::endl;

    // 使用 CTAD
    std::function func2 = [](int a, int b) { return a * b; };
    std::cout << "func2(3, 4) = " << func2(3, 4) << std::endl;

    // std::function 的 CTAD
    std::function<int(int, int)> func3 = [](int a, int b) { return a - b; };
    std::cout << "func3(10, 5) = " << func3(10, 5) << std::endl;
}

// 8. 算法中的 CTAD
void algorithm_example() {
    std::cout << "\n[算法中的 CTAD]" << std::endl;

    std::vector vec = {5, 3, 1, 4, 2};

    // 使用 CTAD 创建比较器
    std::sort(vec.begin(), vec.end(), std::greater{});

    std::cout << "Sorted (descending): ";
    for (int v : vec) std::cout << v << " ";
    std::cout << std::endl;

    // 使用 CTAD 创建谓词
    auto is_even = [](int x) { return x % 2 == 0; };
    auto count = std::count_if(vec.begin(), vec.end(), is_even);
    std::cout << "Even numbers: " << count << std::endl;
}

// 9. 实际应用：配置系统
class Config {
public:
    Config(const std::string& key, int value) : key_(key), value_(std::to_string(value)) {}
    Config(const std::string& key, double value) : key_(key), value_(std::to_string(value)) {}
    Config(const std::string& key, bool value) : key_(key), value_(value ? "true" : "false") {}
    Config(const std::string& key, const std::string& value)
        : key_(key), value_(value) {}

    std::string key() const { return key_; }
    std::string value() const { return value_; }

private:
    std::string key_;
    std::string value_;
};

void config_example() {
    std::cout << "\n[配置系统]" << std::endl;

    // 使用 CTAD
    Config c1("host", std::string("localhost"));
    Config c2("port", 8080);
    Config c3("debug", true);

    std::cout << c1.key() << " = " << c1.value() << std::endl;
    std::cout << c2.key() << " = " << c2.value() << std::endl;
    std::cout << c3.key() << " = " << c3.value() << std::endl;
}

// 10. 实际应用：观察者模式
template <typename T>
class Observer {
public:
    using Callback = std::function<void(const T&)>;

    Observer(Callback cb) : callback_(cb) {}

    void notify(const T& value) {
        callback_(value);
    }

private:
    Callback callback_;
};

// 推导指引
template <typename T>
Observer(std::function<void(const T&)>) -> Observer<T>;

void observer_example() {
    std::cout << "\n[观察者模式]" << std::endl;

    // 使用 CTAD
    Observer obs1 = Observer<int>([](const int& value) {
        std::cout << "Received: " << value << std::endl;
    });

    Observer obs2 = Observer<std::string>([](const std::string& value) {
        std::cout << "Received: " << value << std::endl;
    });

    obs1.notify(42);
    obs2.notify(std::string("Hello"));
}

// 11. CTAD 的限制
void limitations_example() {
    std::cout << "\n[CTAD 的限制]" << std::endl;

    // 1. 不能用于函数模板
    // template <typename T>
    // void func(T value) {}
    // func(42);  // 这是函数模板参数推导，不是 CTAD

    // 2. 需要推导指引或合适的构造函数
    // template <typename T>
    // class MyClass {
    // public:
    //     MyClass(T value) {}
    // };
    // MyClass obj(42);  // 需要推导指引

    // 3. 某些情况需要显式指定
    // std::vector vec = {1, 2, 3};  // OK
    // std::vector vec2;  // 错误：无法推导

    std::cout << "CTAD 限制：" << std::endl;
    std::cout << "  1. 不能用于函数模板" << std::endl;
    std::cout << "  2. 需要推导指引或合适的构造函数" << std::endl;
    std::cout << "  3. 某些情况需要显式指定" << std::endl;
}

// 12. 最佳实践
void best_practices_example() {
    std::cout << "\n[最佳实践]" << std::endl;

    std::cout << "1. 使用场景:" << std::endl;
    std::cout << "   - 类型显而易见时" << std::endl;
    std::cout << "   - 减少代码冗余" << std::endl;
    std::cout << "   - 提高可读性" << std::endl;

    std::cout << "\n2. 优势:" << std::endl;
    std::cout << "   - 代码简洁" << std::endl;
    std::cout << "   - 类型安全" << std::endl;
    std::cout << "   - 编译期推导" << std::endl;

    std::cout << "\n3. 注意事项:" << std::endl;
    std::cout << "   - 不要过度使用" << std::endl;
    std::cout << "   - 确保类型清晰" << std::endl;
    std::cout << "   - 考虑可读性" << std::endl;
}

// 主示例函数
void ctad_example() {
    std::cout << "=== CTAD（类模板参数推导）===" << std::endl;

    basic_ctad_example();
    pair_tuple_example();
    container_example();
    custom_class_example();
    deduction_guide_example();
    optional_variant_example();
    function_object_example();
    algorithm_example();
    config_example();
    observer_example();
    limitations_example();
    best_practices_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    ctad_example();
    return 0;
}
#endif
