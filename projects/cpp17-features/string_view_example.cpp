/**
 * @file string_view_example.cpp
 * @brief C++17 std::string_view 示例
 *
 * std::string_view 是一个非拥有型的字符串引用，它只包含指针和长度。
 * 它用于避免不必要的字符串拷贝，提升性能。
 *
 * 主要优势：
 * 1. 零拷贝 - 不分配内存，只引用现有字符串
 * 2. 通用性 - 可以引用 std::string、C 字符串、字符数组
 * 3. 性能 - 显著减少内存分配和拷贝
 *
 * 注意事项：
 * 1. 生命周期 - 必须确保被引用的字符串生命周期足够长
 * 2. 不保证空终止 - 不要传递给需要 C 字符串的函数
 */

#include <iostream>
#include <string>
#include <string_view>
#include <vector>
#include <algorithm>
#include <chrono>
#include <functional>
#include <map>

// 1. 基本 string_view 使用
void basic_string_view_example() {
    std::cout << "\n[基本 string_view 使用]" << std::endl;

    // 从 C 字符串创建
    const char* cstr = "Hello, World!";
    std::string_view sv1(cstr);
    std::cout << "sv1: " << sv1 << std::endl;

    // 从 std::string 创建
    std::string str = "Hello, C++17!";
    std::string_view sv2(str);
    std::cout << "sv2: " << sv2 << std::endl;

    // 从字符数组创建
    char arr[] = "Hello, Array!";
    std::string_view sv3(arr);
    std::cout << "sv3: " << sv3 << std::endl;

    // 使用字面量（需要 using namespace std::string_view_literals）
    using namespace std::string_view_literals;
    std::string_view sv4 = "Hello, Literal!"sv;
    std::cout << "sv4: " << sv4 << std::endl;

    // 获取大小和长度
    std::cout << "sv1 size: " << sv1.size() << std::endl;
    std::cout << "sv1 length: " << sv1.length() << std::endl;
    std::cout << "sv1 empty: " << sv1.empty() << std::endl;
}

// 2. string_view 操作
void string_view_operations_example() {
    std::cout << "\n[string_view 操作]" << std::endl;

    std::string_view sv = "Hello, World!";

    // 访问字符
    std::cout << "first: " << sv.front() << std::endl;
    std::cout << "last: " << sv.back() << std::endl;
    std::cout << "at(7): " << sv[7] << std::endl;

    // 子串
    std::string_view sub = sv.substr(7, 5);
    std::cout << "substr(7, 5): " << sub << std::endl;

    // 查找
    size_t pos = sv.find("World");
    if (pos != std::string_view::npos) {
        std::cout << "find 'World': " << pos << std::endl;
    }

    // 比较
    std::string_view sv2 = "Hello, World!";
    std::cout << "sv == sv2: " << (sv == sv2) << std::endl;

    // 前缀和后缀
    std::cout << "starts with 'Hello': " << (sv.substr(0, 5) == "Hello") << std::endl;
    std::cout << "ends with '!': " << (sv.substr(sv.size() - 1) == "!") << std::endl;
}

// 3. string_view 作为函数参数
void print_string(std::string_view sv) {
    std::cout << "string_view: " << sv << std::endl;
}

void process_string(std::string_view sv) {
    // 可以处理任何字符串类型
    std::cout << "Processing: " << sv << std::endl;
    std::cout << "Length: " << sv.length() << std::endl;
}

void function_parameter_example() {
    std::cout << "\n[函数参数]" << std::endl;

    // 传递不同类型的字符串
    const char* cstr = "C string";
    std::string str = "std::string";
    char arr[] = "char array";

    print_string(cstr);
    print_string(str);
    print_string(arr);
    print_string("literal");
}

// 4. 避免不必要的拷贝
void avoid_copy_example() {
    std::cout << "\n[避免不必要的拷贝]" << std::endl;

    // 不好的方式：产生拷贝
    auto process_bad = [](const std::string& s) {
        // 如果传递的是 const char*，会创建临时 std::string
        std::cout << "Bad: " << s << std::endl;
    };

    // 好的方式：零拷贝
    auto process_good = [](std::string_view sv) {
        std::cout << "Good: " << sv << std::endl;
    };

    const char* cstr = "Hello";

    // 测试性能差异
    const int iterations = 1000000;

    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        process_bad(cstr);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_bad = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        process_good(cstr);
    }
    end = std::chrono::high_resolution_clock::now();
    auto duration_good = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Bad approach: " << duration_bad.count() << " ms" << std::endl;
    std::cout << "Good approach: " << duration_good.count() << " ms" << std::endl;
}

// 5. string_view 与字符串解析
void parsing_example() {
    std::cout << "\n[字符串解析]" << std::endl;

    std::string_view csv = "Alice,30,Engineer";

    // 解析 CSV
    size_t pos1 = csv.find(',');
    std::string_view name = csv.substr(0, pos1);

    size_t pos2 = csv.find(',', pos1 + 1);
    std::string_view age_str = csv.substr(pos1 + 1, pos2 - pos1 - 1);

    std::string_view job = csv.substr(pos2 + 1);

    std::cout << "Name: " << name << std::endl;
    std::cout << "Age: " << age_str << std::endl;
    std::cout << "Job: " << job << std::endl;
}

// 6. string_view 与算法
void algorithm_example() {
    std::cout << "\n[与算法结合]" << std::endl;

    std::string_view sv = "Hello, World!";

    // 使用 std::find
    auto it = std::find(sv.begin(), sv.end(), 'W');
    if (it != sv.end()) {
        std::cout << "Found 'W' at position: " << (it - sv.begin()) << std::endl;
    }

    // 使用 std::count
    int count = std::count(sv.begin(), sv.end(), 'l');
    std::cout << "Count of 'l': " << count << std::endl;

    // 使用 std::all_of
    bool all_alpha = std::all_of(sv.begin(), sv.end(), [](char c) {
        return std::isalpha(c) || c == ' ' || c == ',' || c == '!';
    });
    std::cout << "All alpha or punctuation: " << all_alpha << std::endl;
}

// 7. string_view 的安全性
void safety_example() {
    std::cout << "\n[安全性示例]" << std::endl;

    // 危险：悬挂引用
    // std::string_view create_view() {
    //     std::string str = "Hello";
    //     return str;  // str 已销毁，view 悬挂！
    // }

    // 安全：确保生命周期
    std::string str = "Hello, World!";
    std::string_view sv = str;  // str 必须比 sv 活得久
    std::cout << "Safe view: " << sv << std::endl;

    // 安全：从字面量创建
    std::string_view sv2 = "Literal";  // 字面量生命周期足够长
    std::cout << "Literal view: " << sv2 << std::endl;

    // 注意：不要传递给需要 C 字符串的函数
    // printf("%s", sv.data());  // 可能没有空终止符！
    // 应该使用：
    // std::cout << sv << std::endl;
}

// 8. string_view 与 std::string 转换
void conversion_example() {
    std::cout << "\n[类型转换]" << std::endl;

    std::string_view sv = "Hello, World!";

    // string_view -> string
    std::string str(sv);
    std::cout << "to string: " << str << std::endl;

    // string_view -> string (显式)
    std::string str2(sv.data(), sv.size());
    std::cout << "to string (explicit): " << str2 << std::endl;

    // 需要 C 字符串时
    std::string str3(sv);
    const char* cstr = str3.c_str();
    std::cout << "to C string: " << cstr << std::endl;
}

// 9. string_view 在容器中的使用
void container_example() {
    std::cout << "\n[在容器中使用]" << std::endl;

    // 存储 string_view（注意生命周期）
    std::vector<std::string_view> views;

    std::string s1 = "Hello";
    std::string s2 = "World";
    std::string s3 = "!";

    views.push_back(s1);
    views.push_back(s2);
    views.push_back(s3);

    std::cout << "Views: ";
    for (const auto& v : views) {
        std::cout << v << " ";
    }
    std::cout << std::endl;

    // 使用 string_view 作为 map 的键
    std::map<std::string_view, int> word_count;
    std::string text = "hello world hello";

    size_t start = 0;
    while (start < text.size()) {
        size_t end = text.find(' ', start);
        if (end == std::string::npos) {
            end = text.size();
        }

        std::string_view word(text.data() + start, end - start);
        word_count[word]++;

        start = end + 1;
    }

    std::cout << "Word counts:" << std::endl;
    for (const auto& [word, count] : word_count) {
        std::cout << "  " << word << ": " << count << std::endl;
    }
}

// 10. 性能对比
void performance_comparison_example() {
    std::cout << "\n[性能对比]" << std::endl;

    const int iterations = 1000000;
    std::string source = "Hello, World! This is a test string for performance comparison.";

    // 测试 std::string 参数
    auto test_string = [](const std::string& s) {
        return s.length();
    };

    // 测试 std::string_view 参数
    auto test_string_view = [](std::string_view sv) {
        return sv.length();
    };

    // 测试性能
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        test_string(source);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_string = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        test_string_view(source);
    }
    end = std::chrono::high_resolution_clock::now();
    auto duration_view = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "std::string: " << duration_string.count() << " ms" << std::endl;
    std::cout << "std::string_view: " << duration_view.count() << " ms" << std::endl;
    std::cout << "Speedup: " << static_cast<double>(duration_string.count()) / duration_view.count() << "x" << std::endl;
}

// 主示例函数
void string_view_example() {
    std::cout << "=== std::string_view ===" << std::endl;

    basic_string_view_example();
    string_view_operations_example();
    function_parameter_example();
    avoid_copy_example();
    parsing_example();
    algorithm_example();
    safety_example();
    conversion_example();
    container_example();
    performance_comparison_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    string_view_example();
    return 0;
}
#endif
