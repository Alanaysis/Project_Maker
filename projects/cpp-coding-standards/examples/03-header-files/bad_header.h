/**
 * @file bad_header.h
 * @brief 糟糕头文件规范示例
 *
 * 本文件展示不符合 C++ 头文件规范的糟糕代码示例。
 * 这些代码展示了常见的头文件错误和反模式。
 *
 * 注意：这些代码仅用于教学目的，实际项目中应避免使用。
 */

// 糟糕：没有头文件保护
// 应该使用 #ifndef / #define / #endif 或 #pragma once

// 糟糕：#include 顺序不正确
#include <algorithm>
#include <iostream>
#include <vector>
#include <string>
#include <cstdint>

// 糟糕：在头文件中使用 using namespace
using namespace std;

// 糟糕：在头文件中定义全局变量
int global_count = 0;
string global_name = "default";

// 糟糕：在头文件中定义静态变量
static int static_count = 0;

// 糟糕：使用宏定义常量（应该使用 constexpr）
#define MAX_SIZE 100
#define DEFAULT_NAME "unknown"

// 糟糕：类声明不完整
class BadUser {
    // 糟糕：没有访问控制说明符
    int id;
    string name;
    string email;

public:
    // 糟糕：构造函数参数命名不清晰
    BadUser(int i, string n, string e) : id(i), name(n), email(e) {}

    // 糟糕：返回非 const 引用
    string& getName() { return name; }
    string& getEmail() { return email; }

    // 糟糕：没有 const 修饰
    int getId() { return id; }

    // 糟糕：函数实现放在头文件中（非内联）
    void print() {
        cout << "User: " << name << " (" << email << ")" << endl;
    }
};

// 糟糕：函数声明不清晰
void process();
void handle();
void doSomething();

// 糟糕：在头文件中定义非内联函数
void nonInlineFunction() {
    // 大量代码
    for (int i = 0; i < 100; i++) {
        cout << i << endl;
    }
}

// 糟糕：没有命名空间
class Manager {
public:
    void manage() {
        cout << "Managing..." << endl;
    }
};

// 糟糕：前向声明不完整
class Logger;  // 前向声明，但没有命名空间

// 糟糕：头文件依赖过多
// 包含了不需要的头文件
#include <map>
#include <set>
#include <list>
#include <deque>
#include <queue>
#include <stack>
#include <array>
#include <tuple>
#include <utility>
#include <functional>
#include <memory>
#include <mutex>
#include <thread>
#include <atomic>
#include <chrono>
#include <random>
#include <regex>
#include <filesystem>
