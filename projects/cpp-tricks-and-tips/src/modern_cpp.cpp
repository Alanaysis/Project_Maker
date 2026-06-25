/**
 * modern_cpp.cpp - 现代 C++ 编程风格
 *
 * 本文件演示 C++17/20 中的现代编程技巧，包括：
 *   1. auto 类型推导
 *   2. 结构化绑定 (Structured Bindings)
 *   3. 带初始化的 range-based for (C++20)
 *   4. std::optional, std::variant
 *   5. std::string_view 使用
 *
 * 编译命令:
 *   g++ -std=c++20 -o modern_cpp modern_cpp.cpp
 *   (C++17 部分功能需要去掉 C++20 特性)
 */

#include <iostream>
#include <string>
#include <string_view>
#include <vector>
#include <map>
#include <tuple>
#include <optional>
#include <variant>
#include <any>
#include <algorithm>
#include <numeric>
#include <array>
#include <set>
#include <functional>
#include <type_traits>
#include <memory>
#include <sstream>
#include <iomanip>

//// ============================================================================
// 第一部分: auto 类型推导
// ============================================================================
// auto 让编译器自动推导类型，减少冗余代码，提高可维护性

void demo_auto() {
    std::cout << "========================================" << std::endl;
    std::cout << "1. auto 类型推导" << std::endl;
    std::cout << "========================================" << std::endl;

    // 基础 auto 推导
    auto x = 42;              // int
    auto pi = 3.14;           // double
    auto name = std::string("hello");  // std::string
    auto flag = true;         // bool

    std::cout << "x = " << x << " (int)" << std::endl;
    std::cout << "pi = " << pi << " (double)" << std::endl;
    std::cout << "name = " << name << " (string)" << std::endl;
    std::cout << "flag = " << flag << " (bool)" << std::endl;

    // auto 推导容器类型
    auto vec = std::vector<int>{1, 2, 3, 4, 5};
    auto m = std::map<std::string, int>{{"a", 1}, {"b", 2}};

    std::cout << "\n容器 auto 推导:" << std::endl;
    std::cout << "vec 大小: " << vec.size() << std::endl;
    std::cout << "map 大小: " << m.size() << std::endl;

    // auto 用于迭代器（避免冗长的类型声明）
    // 旧写法: std::vector<int>::iterator it = vec.begin();
    // 新写法:
    for (auto it = vec.begin(); it != vec.end(); ++it) {
        std::cout << *it << " ";
    }
    std::cout << std::endl;

    // auto 用于 lambda
    auto add = [](auto a, auto b) { return a + b; };
    std::cout << "\nadd(1, 2) = " << add(1, 2) << std::endl;
    std::cout << "add(1.5, 2.5) = " << add(1.5, 2.5) << std::endl;

    // auto 用于函数返回值
    auto make_pair = [](auto a, auto b) {
        return std::make_pair(a, b);
    };
    auto p = make_pair(42, "hello");
    std::cout << "pair: (" << p.first << ", " << p.second << ")" << std::endl;

    // 注意事项: auto 的陷阱
    // 1. auto 会去掉引用和 const
    const int ci = 10;
    auto ai = ci;        // ai 是 int，不是 const int
    ai = 20;             // OK: 可以修改

    // 2. 需要保留引用时使用 auto&
    std::vector<int> numbers = {1, 2, 3};
    for (auto& n : numbers) {  // auto& 保留引用，可以修改
        n *= 2;
    }
    std::cout << "\nauto& 修改后: ";
    for (const auto& n : numbers) {  // const auto& 只读引用
        std::cout << n << " ";
    }
    std::cout << std::endl;

    // 3. decltype(auto) 保留引用和 cv 限定符
    int val = 42;
    int& ref = val;
    auto a1 = ref;           // int（丢失引用）
    decltype(auto) a2 = ref; // int&（保留引用）
    a2 = 100;
    std::cout << "decltype(auto) 保留引用: val = " << val << std::endl;
}

// ============================================================================
// 第二部分: 结构化绑定 (Structured Bindings) - C++17
// ============================================================================
// 允许将 tuple、pair、结构体、数组的成员直接绑定到变量

void demo_structured_bindings() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "2. 结构化绑定 (Structured Bindings)" << std::endl;
    std::cout << "========================================" << std::endl;

    // 绑定 pair
    auto pair = std::make_pair(42, "hello");
    auto [id, msg] = pair;  // C++17 结构化绑定
    std::cout << "pair: id=" << id << ", msg=" << msg << std::endl;

    // 绑定 tuple
    auto tuple = std::make_tuple(1, 3.14, "world", true);
    auto [a, b, c, d] = tuple;
    std::cout << "tuple: a=" << a << ", b=" << b
              << ", c=" << c << ", d=" << d << std::endl;

    // 绑定 map（最常见的用法）
    std::map<std::string, int> scores = {
        {"Alice", 95}, {"Bob", 87}, {"Charlie", 92}
    };

    std::cout << "\n学生成绩:" << std::endl;
    for (const auto& [name, score] : scores) {
        std::cout << "  " << name << ": " << score << std::endl;
    }

    // 绑定结构体
    struct Point {
        double x;
        double y;
        double z;
    };

    Point pt{1.0, 2.0, 3.0};
    auto [px, py, pz] = pt;
    std::cout << "\nPoint: x=" << px << ", y=" << py << ", z=" << pz << std::endl;

    // 绑定数组
    int arr[] = {10, 20, 30};
    auto [first, second, third] = arr;
    std::cout << "Array: " << first << ", " << second << ", " << third << std::endl;

    // 绑定 std::array
    std::array<double, 3> values = {1.1, 2.2, 3.3};
    auto [v1, v2, v3] = values;
    std::cout << "std::array: " << v1 << ", " << v2 << ", " << v3 << std::endl;

    // 实际应用：函数返回多个值
    auto get_min_max = [](const std::vector<int>& v)
        -> std::tuple<int, int, double> {
        auto [min_it, max_it] = std::minmax_element(v.begin(), v.end());
        double avg = std::accumulate(v.begin(), v.end(), 0.0) / v.size();
        return {*min_it, *max_it, avg};
    };

    std::vector<int> data = {5, 2, 8, 1, 9, 3};
    auto [min_val, max_val, avg_val] = get_min_max(data);
    std::cout << "\n数据统计: min=" << min_val
              << ", max=" << max_val
              << ", avg=" << avg_val << std::endl;

    // 结构化绑定 + if 初始化 (C++17)
    std::map<std::string, int> cache = {{"key1", 100}};
    if (auto [it, inserted] = cache.insert({"key1", 200}); !inserted) {
        std::cout << "\nkey1 已存在，值为: " << it->second << std::endl;
    }
    if (auto [it, inserted] = cache.insert({"key2", 200}); inserted) {
        std::cout << "key2 插入成功，值为: " << it->second << std::endl;
    }
}

// ============================================================================
// 第三部分: 带初始化的 if/switch (C++17) 和 range-based for (C++20)
// ============================================================================

void demo_init_statements() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "3. 带初始化的控制语句" << std::endl;
    std::cout << "========================================" << std::endl;

    // if 带初始化 (C++17)
    // 语法: if (init; condition) { ... }
    // init 中声明的变量作用域限于 if/else 块
    std::map<std::string, std::vector<int>> grades = {
        {"Alice", {90, 85, 92}},
        {"Bob", {78, 82, 88}}
    };

    // 传统写法（变量泄漏到外部作用域）
    // auto it = grades.find("Alice");
    // if (it != grades.end()) { ... }

    // 现代写法（变量限于 if 块内）
    if (auto it = grades.find("Alice"); it != grades.end()) {
        std::cout << "找到 Alice 的成绩: ";
        for (int g : it->second) std::cout << g << " ";
        std::cout << std::endl;
    }
    // it 在这里不可访问

    // switch 带初始化 (C++17)
    enum class ErrorCode { OK, NotFound, Timeout, Internal };
    auto get_error = [](int code) -> ErrorCode {
        switch (code) {
            case 0: return ErrorCode::OK;
            case 404: return ErrorCode::NotFound;
            case 504: return ErrorCode::Timeout;
            default: return ErrorCode::Internal;
        }
    };

    if (auto err = get_error(404); err == ErrorCode::NotFound) {
        std::cout << "错误: 资源未找到" << std::endl;
    }

    // range-based for 带初始化 (C++20)
    // 语法: for (init; range_decl) { ... }
    // 特别适合在循环前创建临时容器
#if __cplusplus >= 202002L
    std::cout << "\nC++20 range-based for 带初始化:" << std::endl;

    // 创建临时 vector 并立即遍历
    for (auto vec = std::vector{1, 2, 3, 4, 5}; auto& v : vec) {
        std::cout << v << " ";
    }
    std::cout << std::endl;

    // 配合条件判断使用
    for (auto data = std::vector{3, 1, 4, 1, 5, 9}; auto& val : data) {
        if (val > 2) std::cout << val << " ";
    }
    std::cout << " (过滤 > 2)" << std::endl;
#else
    std::cout << "\n(range-based for 带初始化需要 C++20)" << std::endl;
#endif
}

// ============================================================================
// 第四部分: std::optional
// ============================================================================
// 表示一个可能不存在的值，替代 nullptr/哨兵值/异常

// 用 optional 表示可能失败的操作
std::optional<int> parse_int(std::string_view str) {
    try {
        size_t pos;
        int result = std::stoi(std::string(str), &pos);
        if (pos == str.size()) return result;  // 完全解析
        return std::nullopt;  // 有剩余字符
    } catch (...) {
        return std::nullopt;  // 解析失败
    }
}

// 用 optional 作为函数返回值
std::optional<std::string> find_user(int id) {
    static std::map<int, std::string> users = {
        {1, "Alice"}, {2, "Bob"}, {3, "Charlie"}
    };
    if (auto it = users.find(id); it != users.end()) {
        return it->second;
    }
    return std::nullopt;
}

void demo_optional() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "4. std::optional" << std::endl;
    std::cout << "========================================" << std::endl;

    // 创建 optional
    std::optional<int> opt1 = 42;          // 有值
    std::optional<int> opt2 = std::nullopt; // 无值
    std::optional<int> opt3;               // 无值（默认构造）

    // 检查是否有值
    std::cout << "opt1 有值: " << opt1.has_value() << std::endl;
    std::cout << "opt2 有值: " << opt2.has_value() << std::endl;

    // 获取值
    if (opt1) {  // 可以直接用在布尔上下文中
        std::cout << "opt1 = " << *opt1 << std::endl;  // 用 * 解引用
        std::cout << "opt1 = " << opt1.value() << std::endl;  // 或用 value()
    }

    // value_or: 提供默认值
    std::cout << "opt2 默认值: " << opt2.value_or(-1) << std::endl;

    // 实际应用：解析可能失败
    std::cout << "\n字符串解析:" << std::endl;
    for (auto str : {"42", "abc", "3.14", "100"}) {
        auto result = parse_int(str);
        if (result) {
            std::cout << "  \"" << str << "\" -> " << *result << std::endl;
        } else {
            std::cout << "  \"" << str << "\" -> 解析失败" << std::endl;
        }
    }

    // 实际应用：查找可能不存在
    std::cout << "\n用户查找:" << std::endl;
    for (int id : {1, 2, 99}) {
        if (auto user = find_user(id)) {
            std::cout << "  ID " << id << ": " << *user << std::endl;
        } else {
            std::cout << "  ID " << id << ": 未找到" << std::endl;
        }
    }

    // optional 的链式操作（monadic 操作，C++23）
    // C++17 模拟:
    auto transform = [](std::optional<int> opt, auto func)
        -> std::optional<decltype(func(*opt))> {
        if (opt) return func(*opt);
        return std::nullopt;
    };

    auto result = transform(parse_int("42"), [](int x) { return x * 2; });
    if (result) {
        std::cout << "\n\"42\" * 2 = " << *result << std::endl;
    }

    // optional 用于类成员（延迟初始化）
    struct Config {
        std::optional<std::string> name;
        std::optional<int> timeout;

        void print() const {
            std::cout << "Config{name=" << (name ? *name : "<默认>")
                      << ", timeout=" << (timeout ? std::to_string(*timeout) : "<默认>")
                      << "}" << std::endl;
        }
    };

    Config cfg1{"服务器A", 30};
    Config cfg2;  // 全部使用默认值
    std::cout << "\n";
    cfg1.print();
    cfg2.print();
}

// ============================================================================
// 第五部分: std::variant
// ============================================================================
// 类型安全的联合体，替代传统的 union

// 定义一个变体类型：可以是 int、double 或 string
using Value = std::variant<int, double, std::string, std::vector<int>>;

// 访问 variant 的辅助函数（使用 visitor 模式）
struct ValuePrinter {
    void operator()(int v) const {
        std::cout << "整数: " << v;
    }
    void operator()(double v) const {
        std::cout << "浮点: " << std::fixed << std::setprecision(2) << v;
    }
    void operator()(const std::string& v) const {
        std::cout << "字符串: \"" << v << "\"";
    }
    void operator()(const std::vector<int>& v) const {
        std::cout << "数组: [";
        for (size_t i = 0; i < v.size(); ++i) {
            if (i > 0) std::cout << ", ";
            std::cout << v[i];
        }
        std::cout << "]";
    }
};

// 通用 visitor 辅助（C++17 std::visit 配合重载 lambda）
// 这是 "overloaded" 模式，非常实用
template <typename... Ts>
struct overloaded : Ts... {
    using Ts::operator()...;
};

// C++17 需要这个推导指引
template <typename... Ts>
overloaded(Ts...) -> overloaded<Ts...>;

void demo_variant() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "5. std::variant" << std::endl;
    std::cout << "========================================" << std::endl;

    // 创建 variant
    Value v1 = 42;
    Value v2 = 3.14;
    Value v3 = std::string("hello");
    Value v4 = std::vector<int>{1, 2, 3};

    // 使用 visitor 模式访问
    std::cout << "使用自定义 visitor:" << std::endl;
    ValuePrinter printer;
    std::cout << "  v1: "; std::visit(printer, v1); std::cout << std::endl;
    std::cout << "  v2: "; std::visit(printer, v2); std::cout << std::endl;
    std::cout << "  v3: "; std::visit(printer, v3); std::cout << std::endl;
    std::cout << "  v4: "; std::visit(printer, v4); std::cout << std::endl;

    // 使用 overloaded 模式（更简洁）
    std::cout << "\n使用 overloaded 模式:" << std::endl;
    auto print_value = [](const Value& val) {
        std::visit(overloaded{
            [](int v) { std::cout << "int: " << v; },
            [](double v) { std::cout << "double: " << v; },
            [](const std::string& v) { std::cout << "string: " << v; },
            [](const std::vector<int>& v) {
                std::cout << "vector[" << v.size() << "]";
            }
        }, val);
        std::cout << std::endl;
    };

    print_value(v1);
    print_value(v2);
    print_value(v3);
    print_value(v4);

    // 检查当前持有的类型
    std::cout << "\n类型检查:" << std::endl;
    std::cout << "  v1.index() = " << v1.index() << std::endl;
    std::cout << "  v1 是 int: "
              << (std::holds_alternative<int>(v1) ? "是" : "否") << std::endl;

    // 获取值
    if (std::holds_alternative<int>(v1)) {
        int val = std::get<int>(v1);
        std::cout << "  v1 的值: " << val << std::endl;
    }

    // get_if 安全访问
    if (auto* p = std::get_if<std::string>(&v3)) {
        std::cout << "  v3 是字符串: " << *p << std::endl;
    }

    // 修改 variant 的值
    v1 = 100;  // 改为新的 int
    v1 = 3.14; // 改为 double（类型切换）
    std::cout << "\n修改后 v1.index() = " << v1.index() << std::endl;

    // 实际应用：简单的 JSON 值类型
    std::cout << "\n应用场景 - 简单 JSON 值:" << std::endl;
    std::map<std::string, Value> json_obj;
    json_obj["name"] = std::string("Alice");
    json_obj["age"] = 30;
    json_obj["score"] = 95.5;

    for (const auto& [key, val] : json_obj) {
        std::cout << "  " << key << ": ";
        print_value(val);
    }
}

// ============================================================================
// 第六部分: std::string_view
// ============================================================================
// 非拥有的字符串引用，避免不必要的字符串拷贝

// 使用 string_view 作为函数参数（推荐做法）
// 适用于只需要读取字符串的场景
void print_info(std::string_view name, std::string_view message) {
    std::cout << "[" << name << "] " << message << std::endl;
}

// string_view 用于字符串处理（零拷贝）
std::vector<std::string_view> split(std::string_view str, char delim) {
    std::vector<std::string_view> result;
    size_t start = 0;

    while (start < str.size()) {
        auto end = str.find(delim, start);
        if (end == std::string_view::npos) end = str.size();
        result.push_back(str.substr(start, end - start));
        start = end + 1;
    }

    return result;
}

// string_view 用于查找操作
bool starts_with(std::string_view str, std::string_view prefix) {
    return str.substr(0, prefix.size()) == prefix;
}

bool ends_with(std::string_view str, std::string_view suffix) {
    if (suffix.size() > str.size()) return false;
    return str.substr(str.size() - suffix.size()) == suffix;
}

void demo_string_view() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "6. std::string_view" << std::endl;
    std::cout << "========================================" << std::endl;

    // 从字面量创建（零拷贝）
    std::string_view sv1 = "Hello, World!";
    std::cout << "sv1: " << sv1 << std::endl;
    std::cout << "长度: " << sv1.size() << std::endl;

    // 从 std::string 创建（零拷贝）
    std::string str = "这是C++字符串";
    std::string_view sv2 = str;
    std::cout << "sv2: " << sv2 << std::endl;

    // 子串操作（零拷贝）
    std::string_view sub = sv1.substr(7, 5);
    std::cout << "\nsv1.substr(7, 5): " << sub << std::endl;

    // 作为函数参数（避免拷贝）
    std::cout << "\n作为函数参数:" << std::endl;
    print_info("Main", "程序启动");
    std::string msg = "这是一条消息";
    print_info("Logger", msg);  // 从 string 隐式转换

    // 字符串分割（零拷贝）
    std::cout << "\n字符串分割:" << std::endl;
    std::string csv = "Alice,Bob,Charlie,David";
    auto parts = split(csv, ',');
    for (const auto& part : parts) {
        std::cout << "  [" << part << "]" << std::endl;
    }

    // 前缀/后缀检查
    std::cout << "\n前缀/后缀检查:" << std::endl;
    std::string filename = "document.cpp";
    std::cout << "  " << filename << " 以 .cpp 结尾: "
              << (ends_with(filename, ".cpp") ? "是" : "否") << std::endl;
    std::cout << "  " << filename << " 以 doc 开头: "
              << (starts_with(filename, "doc") ? "是" : "否") << std::endl;

    // string_view 的注意事项
    std::cout << "\n注意事项:" << std::endl;

    // 1. string_view 不拥有数据，原数据生命周期必须覆盖 string_view
    std::string_view dangling;
    {
        std::string temp = "temporary";
        dangling = temp;
        // temp 在这里被销毁
    }
    // dangling 现在是悬垂引用！
    // std::cout << dangling << std::endl;  // 未定义行为！
    std::cout << "  不要让 string_view 超出原数据的生命周期" << std::endl;

    // 2. string_view 不能自动转为 std::string
    std::string_view sv3 = "hello";
    std::string s(sv3);  // 需要显式构造
    std::cout << "  string -> string_view: 隐式转换" << std::endl;
    std::cout << "  string_view -> string: 需要显式构造" << std::endl;

    // 3. string_view 通常以值传递（很小，只有指针+长度）
    std::cout << "  sizeof(string_view) = " << sizeof(std::string_view) << " 字节" << std::endl;
    std::cout << "  sizeof(string) = " << sizeof(std::string) << " 字节" << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================
int main() {
    std::cout << "╔══════════════════════════════════════╗" << std::endl;
    std::cout << "║   现代 C++ 编程风格 (modern_cpp)     ║" << std::endl;
    std::cout << "╚══════════════════════════════════════╝" << std::endl;
    std::cout << std::endl;

    demo_auto();
    demo_structured_bindings();
    demo_init_statements();
    demo_optional();
    demo_variant();
    demo_string_view();

    std::cout << "\n现代 C++ 风格演示完成。" << std::endl;
    return 0;
}
