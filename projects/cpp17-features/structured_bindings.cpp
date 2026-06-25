/**
 * @file structured_bindings.cpp
 * @brief C++17 结构化绑定示例
 *
 * 结构化绑定允许将元组、结构体、数组等复合类型的成员
 * 绑定到独立的变量上，简化代码并提高可读性。
 *
 * 主要优势：
 * 1. 代码简洁 - 减少临时变量
 * 2. 可读性强 - 直接表达意图
 * 3. 类型安全 - 编译期类型检查
 */

#include <iostream>
#include <tuple>
#include <map>
#include <string>
#include <vector>
#include <array>
#include <utility>
#include <functional>

// 1. 绑定元组
void tuple_binding_example() {
    std::cout << "\n[绑定元组]" << std::endl;

    // 创建元组
    auto get_person = []() -> std::tuple<std::string, int, std::string> {
        return {"Alice", 30, "Engineer"};
    };

    // 传统方式
    auto person = get_person();
    std::string name = std::get<0>(person);
    int age = std::get<1>(person);
    std::string job = std::get<2>(person);
    std::cout << "Traditional: " << name << ", " << age << ", " << job << std::endl;

    // 结构化绑定
    auto [name2, age2, job2] = get_person();
    std::cout << "Structured binding: " << name2 << ", " << age2 << ", " << job2 << std::endl;

    // 绑定 pair
    auto p = std::make_pair(42, "Hello");
    auto [key, value] = p;
    std::cout << "Pair: key=" << key << ", value=" << value << std::endl;
}

// 2. 绑定结构体
struct Point {
    double x;
    double y;
    double z;
};

struct Person {
    std::string name;
    int age;
    std::string city;
};

void struct_binding_example() {
    std::cout << "\n[绑定结构体]" << std::endl;

    // 绑定结构体
    Point p{1.0, 2.0, 3.0};
    auto [x, y, z] = p;
    std::cout << "Point: x=" << x << ", y=" << y << ", z=" << z << std::endl;

    // 绑定 const 结构体
    const Person person{"Bob", 25, "Beijing"};
    const auto& [name, age, city] = person;
    std::cout << "Person: " << name << ", " << age << ", " << city << std::endl;

    // 修改绑定的变量
    Person person2{"Charlie", 35, "Shanghai"};
    auto [name2, age2, city2] = person2;
    name2 = "David";
    age2 = 40;
    std::cout << "Modified: " << name2 << ", " << age2 << ", " << city2 << std::endl;
    std::cout << "Original: " << person2.name << ", " << person2.age << ", " << person2.city << std::endl;
}

// 3. 绑定数组
void array_binding_example() {
    std::cout << "\n[绑定数组]" << std::endl;

    // 绑定 C 数组
    int arr[] = {1, 2, 3, 4, 5};
    auto [a, b, c, d, e] = arr;
    std::cout << "Array: " << a << ", " << b << ", " << c << ", " << d << ", " << e << std::endl;

    // 绑定 std::array
    std::array<int, 3> std_arr = {10, 20, 30};
    auto [x, y, z] = std_arr;
    std::cout << "std::array: " << x << ", " << y << ", " << z << std::endl;
}

// 4. 绑定 map
void map_binding_example() {
    std::cout << "\n[绑定 map]" << std::endl;

    std::map<std::string, int> scores = {
        {"Alice", 95},
        {"Bob", 87},
        {"Charlie", 92}
    };

    // 遍历 map
    std::cout << "Scores:" << std::endl;
    for (const auto& [name, score] : scores) {
        std::cout << "  " << name << ": " << score << std::endl;
    }

    // 使用 insert 返回值
    auto [it, inserted] = scores.insert({"David", 88});
    if (inserted) {
        std::cout << "Inserted: " << it->first << " = " << it->second << std::endl;
    }

    // 使用 emplace 返回值
    auto [it2, inserted2] = scores.emplace("Eve", 90);
    if (inserted2) {
        std::cout << "Emplaced: " << it2->first << " = " << it2->second << std::endl;
    }
}

// 5. 函数返回多值
std::tuple<int, int, int> min_max_avg(const std::vector<int>& vec) {
    if (vec.empty()) {
        return {0, 0, 0};
    }

    int min_val = vec[0];
    int max_val = vec[0];
    int sum = 0;

    for (int v : vec) {
        min_val = std::min(min_val, v);
        max_val = std::max(max_val, v);
        sum += v;
    }

    return {min_val, max_val, sum / static_cast<int>(vec.size())};
}

std::pair<bool, std::string> parse_config(const std::string& config) {
    size_t pos = config.find('=');
    if (pos == std::string::npos) {
        return {false, "Invalid config"};
    }

    std::string key = config.substr(0, pos);
    std::string value = config.substr(pos + 1);

    return {true, key + " = " + value};
}

void function_return_example() {
    std::cout << "\n[函数返回多值]" << std::endl;

    std::vector<int> numbers = {3, 1, 4, 1, 5, 9, 2, 6};

    // 使用结构化绑定接收返回值
    auto [min_val, max_val, avg] = min_max_avg(numbers);
    std::cout << "Min: " << min_val << ", Max: " << max_val << ", Avg: " << avg << std::endl;

    // 解析配置
    auto [success, message] = parse_config("hostname=localhost");
    std::cout << "Parse result: " << (success ? "Success" : "Failed")
              << ", Message: " << message << std::endl;

    auto [success2, message2] = parse_config("invalid_config");
    std::cout << "Parse result: " << (success2 ? "Success" : "Failed")
              << ", Message: " << message2 << std::endl;
}

// 6. 绑定自定义类型
struct Range {
    int begin;
    int end;

    // 需要提供 tuple_size 和 tuple_element 特化
    // 或者使用公有成员
};

// 对于公有成员的结构体，结构化绑定自动工作
struct Config {
    std::string hostname;
    int port;
    bool use_ssl;
};

void custom_type_example() {
    std::cout << "\n[自定义类型]" << std::endl;

    // 绑定公有成员的结构体
    Config config{"localhost", 8080, true};
    auto [hostname, port, use_ssl] = config;
    std::cout << "Config: " << hostname << ":" << port
              << " (SSL: " << (use_ssl ? "yes" : "no") << ")" << std::endl;

    // 绑定 Range
    Range range{1, 10};
    auto [begin, end] = range;
    std::cout << "Range: [" << begin << ", " << end << ")" << std::endl;
}

// 7. 嵌套结构化绑定
void nested_binding_example() {
    std::cout << "\n[嵌套结构化绑定]" << std::endl;

    // 嵌套 pair
    auto nested_pair = std::make_pair(std::make_pair(1, 2), std::make_pair(3, 4));
    auto [p1, p2] = nested_pair;
    auto [a, b] = p1;
    auto [c, d] = p2;
    std::cout << "Nested: (" << a << ", " << b << "), ("
              << c << ", " << d << ")" << std::endl;

    // 复杂嵌套
    std::map<std::string, std::vector<int>> data = {
        {"Alice", {90, 85, 95}},
        {"Bob", {80, 75, 85}}
    };

    for (const auto& [name, scores] : data) {
        std::cout << name << ": ";
        for (int score : scores) {
            std::cout << score << " ";
        }
        std::cout << std::endl;
    }
}

// 8. 结构化绑定与 lambda
void lambda_binding_example() {
    std::cout << "\n[与 lambda 结合]" << std::endl;

    // lambda 返回元组
    auto get_stats = [](const std::vector<int>& vec) {
        int sum = 0;
        int count = 0;
        for (int v : vec) {
            sum += v;
            ++count;
        }
        return std::make_tuple(sum, count, static_cast<double>(sum) / count);
    };

    std::vector<int> numbers = {1, 2, 3, 4, 5};
    auto [sum, count, avg] = get_stats(numbers);
    std::cout << "Sum: " << sum << ", Count: " << count << ", Avg: " << avg << std::endl;

    // lambda 参数使用结构化绑定
    auto process_pair = [](const std::pair<int, std::string>& p) {
        auto [key, value] = p;
        std::cout << "Key: " << key << ", Value: " << value << std::endl;
    };

    process_pair({1, "Hello"});
}

// 9. 结构化绑定与算法
void algorithm_binding_example() {
    std::cout << "\n[与算法结合]" << std::endl;

    std::vector<std::pair<int, std::string>> students = {
        {3, "Charlie"},
        {1, "Alice"},
        {2, "Bob"}
    };

    // 排序
    std::sort(students.begin(), students.end(),
        [](const auto& a, const auto& b) {
            auto [id_a, name_a] = a;
            auto [id_b, name_b] = b;
            return id_a < id_b;
        });

    std::cout << "Sorted students:" << std::endl;
    for (const auto& [id, name] : students) {
        std::cout << "  " << id << ": " << name << std::endl;
    }

    // 查找最大值
    auto [max_id, max_name] = *std::max_element(students.begin(), students.end(),
        [](const auto& a, const auto& b) {
            return a.first < b.first;
        });
    std::cout << "Max: " << max_id << " - " << max_name << std::endl;
}

// 10. 结构化绑定的限制
void limitations_example() {
    std::cout << "\n[限制和注意事项]" << std::endl;

    // 1. 绑定数量必须匹配
    auto [a, b, c] = std::make_tuple(1, 2, 3);
    std::cout << "a=" << a << ", b=" << b << ", c=" << c << std::endl;

    // 2. 不能绑定私有成员
    // class MyClass {
    //     int private_member;
    // public:
    //     MyClass(int val) : private_member(val) {}
    // };
    // auto [x] = MyClass(42);  // 编译错误

    // 3. 绑定的变量是引用还是值取决于声明方式
    std::pair<int, int> p = {1, 2};

    auto [x, y] = p;           // 值拷贝
    auto& [rx, ry] = p;        // 左值引用
    [[maybe_unused]] const auto& [cx, cy] = p;  // const 左值引用
    [[maybe_unused]] auto&& [mx, my] = p;       // 通用引用

    x = 10;  // 修改拷贝
    rx = 20; // 修改原值

    std::cout << "p.first=" << p.first << ", p.second=" << p.second << std::endl;
    std::cout << "x=" << x << ", y=" << y << std::endl;
}

// 主示例函数
void structured_bindings_example() {
    std::cout << "=== 结构化绑定 ===" << std::endl;

    tuple_binding_example();
    struct_binding_example();
    array_binding_example();
    map_binding_example();
    function_return_example();
    custom_type_example();
    nested_binding_example();
    lambda_binding_example();
    algorithm_binding_example();
    limitations_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    structured_bindings_example();
    return 0;
}
#endif
