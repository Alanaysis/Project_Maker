# C++ 技巧技术设计文档

## 1. 设计概述

本文档描述 C++ 奇技淫巧集锦项目的技术架构、文件组织和实现规范。

## 2. 整体架构

### 2.1 目录结构设计

```
cpp-tricks-and-tips/
├── CMakeLists.txt                    # 主 CMake 配置
├── README.md                         # 项目说明
├── docs/                             # 文档目录
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_PRODUCT.md
│   └── 05_DEVELOPMENT.md
├── include/                          # 公共头文件
│   ├── common.hpp                    # 通用工具
│   ├── type_utils.hpp                # 类型工具
│   ├── memory_utils.hpp              # 内存工具
│   ├── concurrency_utils.hpp         # 并发工具
│   └── benchmark.hpp                 # 性能测试
├── src/                              # 源代码目录
│   ├── type_tricks/                  # 类型技巧
│   │   ├── CMakeLists.txt
│   │   ├── README.md
│   │   ├── 01_type_id.cpp
│   │   ├── 02_type_conversion.cpp
│   │   ├── 03_sfinae.cpp
│   │   ├── 04_type_traits.cpp
│   │   └── 05_if_constexpr.cpp
│   ├── template_tricks/              # 模板技巧
│   │   ├── CMakeLists.txt
│   │   ├── README.md
│   │   └── ...
│   ├── memory_tricks/                # 内存技巧
│   │   ├── CMakeLists.txt
│   │   ├── README.md
│   │   └── ...
│   ├── concurrency_tricks/           # 并发技巧
│   │   ├── CMakeLists.txt
│   │   ├── README.md
│   │   └── ...
│   ├── optimization_tricks/          # 优化技巧
│   │   ├── CMakeLists.txt
│   │   ├── README.md
│   │   └── ...
│   ├── utility_tools/                # 实用工具
│   │   ├── CMakeLists.txt
│   │   ├── README.md
│   │   └── ...
│   └── code_style/                   # 代码风格
│       ├── CMakeLists.txt
│       ├── README.md
│       └── ...
├── tests/                            # 测试目录
│   ├── CMakeLists.txt
│   ├── test_type_tricks.cpp
│   ├── test_template_tricks.cpp
│   └── ...
└── examples/                         # 综合示例
    ├── CMakeLists.txt
    └── real_world_examples.cpp
```

### 2.2 设计原则

1. **单一职责**: 每个 `.cpp` 文件只包含一个技巧
2. **独立编译**: 每个技巧可以独立编译运行
3. **低耦合**: 技巧之间无依赖关系
4. **高内聚**: 相关技巧组织在同一目录下
5. **可扩展**: 易于添加新技巧

## 3. 文件组织规范

### 3.1 文件命名规范

#### 源文件命名
- **格式**: `{序号}_{技巧名称}.cpp`
- **示例**: `01_type_id.cpp`, `02_type_conversion.cpp`
- **规则**:
  - 序号使用两位数字，从 01 开始
  - 技巧名称使用 snake_case
  - 所有字母小写
  - 使用下划线分隔单词

#### 头文件命名
- **格式**: `{功能描述}.hpp`
- **示例**: `common.hpp`, `type_utils.hpp`
- **规则**:
  - 使用 snake_case
  - 使用 `.hpp` 扩展名
  - 名称简洁明确

#### 目录命名
- **格式**: `{分类名称}_tricks` 或 `{分类名称}_tools`
- **示例**: `type_tricks`, `utility_tools`
- **规则**:
  - 使用 snake_case
  - 复数形式
  - 与分类名称对应

### 3.2 文件模板

#### 技巧文件模板

```cpp
/**
 * @file 01_type_id.cpp
 * @brief 类型标识技巧演示
 * @author C++ Tricks Team
 * @date 2024
 *
 * 本文件演示如何使用 typeid 和 type_info 在运行时获取类型信息。
 *
 * 技巧要点:
 * 1. typeid 运算符的基本用法
 * 2. type_info 类的方法
 * 3. 多态类型的运行时识别
 * 4. 类型比较和类型名称获取
 *
 * 应用场景:
 * - 日志系统中的类型记录
 * - 序列化框架的类型识别
 * - 调试工具的类型显示
 *
 * 编译命令:
 * g++ -std=c++17 -o type_id 01_type_id.cpp
 *
 * 运行命令:
 * ./type_id
 */

#include <iostream>
#include <typeinfo>
#include <string>

// ============================================================================
// 示例 1: 基本类型标识
// ============================================================================

/**
 * @brief 演示基本类型的 typeid 使用
 *
 * typeid 可以用于获取任何类型的 type_info 对象，
 * 包括基本类型、自定义类型、指针类型等。
 */
void basic_type_id() {
    std::cout << "=== 基本类型标识 ===" << std::endl;

    // 基本类型
    int i = 42;
    double d = 3.14;
    std::string s = "hello";

    std::cout << "int: " << typeid(i).name() << std::endl;
    std::cout << "double: " << typeid(d).name() << std::endl;
    std::cout << "string: " << typeid(s).name() << std::endl;

    // 类型比较
    std::cout << "i is int: " << (typeid(i) == typeid(int)) << std::endl;
    std::cout << "d is int: " << (typeid(d) == typeid(int)) << std::endl;
}

// ============================================================================
// 示例 2: 多态类型识别
// ============================================================================

/**
 * @brief 基类
 */
class Base {
public:
    virtual ~Base() = default;
    virtual void print() const { std::cout << "Base" << std::endl; }
};

/**
 * @brief 派生类 A
 */
class DerivedA : public Base {
public:
    void print() const override { std::cout << "DerivedA" << std::endl; }
};

/**
 * @brief 派生类 B
 */
class DerivedB : public Base {
public:
    void print() const override { std::cout << "DerivedB" << std::endl; }
};

/**
 * @brief 演示多态类型的运行时识别
 *
 * 对于多态类型，typeid 可以在运行时识别对象的实际类型，
 * 而不是声明类型。这需要基类有虚函数。
 */
void polymorphic_type_id() {
    std::cout << "\n=== 多态类型识别 ===" << std::endl;

    DerivedA a;
    DerivedB b;
    Base* ptr_a = &a;
    Base* ptr_b = &b;

    // 运行时类型识别
    std::cout << "ptr_a actual type: " << typeid(*ptr_a).name() << std::endl;
    std::cout << "ptr_b actual type: " << typeid(*ptr_b).name() << std::endl;

    // 类型比较
    std::cout << "ptr_a is DerivedA: "
              << (typeid(*ptr_a) == typeid(DerivedA)) << std::endl;
    std::cout << "ptr_b is DerivedA: "
              << (typeid(*ptr_b) == typeid(DerivedA)) << std::endl;
}

// ============================================================================
// 示例 3: 类型信息获取
// ============================================================================

/**
 * @brief 演示 type_info 类的方法
 *
 * type_info 类提供了多个有用的方法:
 * - name(): 类型名称 (编译器相关)
 * - hash_code(): 类型哈希值
 * - before(): 类型排序
 */
void type_info_methods() {
    std::cout << "\n=== 类型信息获取 ===" << std::endl;

    const std::type_info& ti_int = typeid(int);
    const std::type_info& ti_double = typeid(double);

    std::cout << "int name: " << ti_int.name() << std::endl;
    std::cout << "int hash: " << ti_int.hash_code() << std::endl;

    std::cout << "double name: " << ti_double.name() << std::endl;
    std::cout << "double hash: " << ti_double.hash_code() << std::endl;

    // 类型排序 (实现定义)
    std::cout << "int before double: " << ti_int.before(ti_double) << std::endl;
}

// ============================================================================
// 示例 4: 模板中的类型标识
// ============================================================================

/**
 * @brief 模板函数中使用 typeid
 *
 * 在模板中，typeid 可以用于显示模板参数类型，
 * 帮助调试和理解模板实例化。
 */
template <typename T>
void show_type(const T& value) {
    std::cout << "Type: " << typeid(T).name()
              << ", Value: " << value << std::endl;
}

/**
 * @brief 演示模板中的类型标识
 */
void template_type_id() {
    std::cout << "\n=== 模板中的类型标识 ===" << std::endl;

    show_type(42);
    show_type(3.14);
    show_type(std::string("hello"));
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "C++ 类型标识技巧演示\n" << std::endl;

    basic_type_id();
    polymorphic_type_id();
    type_info_methods();
    template_type_id();

    return 0;
}

/*
 * 编译和运行:
 *
 * g++ -std=c++17 -o type_id 01_type_id.cpp
 * ./type_id
 *
 * 注意事项:
 * 1. typeid 对于非多态类型在编译时确定，对于多态类型在运行时确定
 * 2. name() 返回的字符串是编译器相关的，不同编译器结果不同
 * 3. 使用 typeid 进行类型比较比 dynamic_cast 更高效
 * 4. 在模板中使用 typeid 有助于调试类型推导问题
 */
```

#### README 文件模板

```markdown
# 类型技巧 (Type Tricks)

## 概述

本目录包含 5 个 C++ 类型操控技巧，帮助开发者理解和利用 C++ 的类型系统。

## 技巧列表

| 编号 | 技巧名称 | 文件名 | 难度 | 描述 |
|------|----------|--------|------|------|
| 01 | 类型标识 | 01_type_id.cpp | ⭐⭐ | 使用 typeid 获取类型信息 |
| 02 | 类型转换 | 02_type_conversion.cpp | ⭐⭐ | 安全的类型转换技术 |
| 03 | SFINAE 基础 | 03_sfinae.cpp | ⭐⭐⭐ | 替换失败不是错误 |
| 04 | 类型萃取 | 04_type_traits.cpp | ⭐⭐ | 编译期类型查询 |
| 05 | if constexpr | 05_if_constexpr.cpp | ⭐⭐ | 编译期条件分支 |

## 学习建议

1. 从基础的类型标识开始
2. 理解类型转换的各种方式
3. 学习 SFINAE 的基本原理
4. 掌握 type_traits 的使用
5. 最后学习 if constexpr 的现代用法

## 编译和运行

```bash
# 编译单个技巧
g++ -std=c++17 -o type_id 01_type_id.cpp

# 运行
./type_id
```

## 参考资源

- [cppreference: type_info](https://en.cppreference.com/w/cpp/types/type_info)
- [cppreference: type_traits](https://en.cppreference.com/w/cpp/header/type_traits)
- Effective Modern C++ Item 1-4
```

## 4. CMake 构建系统设计

### 4.1 主 CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.16)
project(cpp-tricks-and-tips VERSION 1.0.0 LANGUAGES CXX)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 设置输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# 编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# 包含目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# 添加子目录
add_subdirectory(src/type_tricks)
add_subdirectory(src/template_tricks)
add_subdirectory(src/memory_tricks)
add_subdirectory(src/concurrency_tricks)
add_subdirectory(src/optimization_tricks)
add_subdirectory(src/utility_tools)
add_subdirectory(src/code_style)

# 测试 (可选)
option(BUILD_TESTS "Build tests" ON)
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

### 4.2 分类目录 CMakeLists.txt

以 `src/type_tricks/CMakeLists.txt` 为例:

```cmake
# 类型技巧

# 01: 类型标识
add_executable(type_trick_01 01_type_id.cpp)
target_link_libraries(type_trick_01 PRIVATE common_utils)

# 02: 类型转换
add_executable(type_trick_02 02_type_conversion.cpp)
target_link_libraries(type_trick_02 PRIVATE common_utils)

# 03: SFINAE 基础
add_executable(type_trick_03 03_sfinae.cpp)
target_link_libraries(type_trick_03 PRIVATE common_utils)

# 04: 类型萃取
add_executable(type_trick_04 04_type_traits.cpp)
target_link_libraries(type_trick_04 PRIVATE common_utils)

# 05: if constexpr
add_executable(type_trick_05 05_if_constexpr.cpp)
target_link_libraries(type_trick_05 PRIVATE common_utils)

# 添加到测试
add_test(NAME type_trick_01 COMMAND type_trick_01)
add_test(NAME type_trick_02 COMMAND type_trick_02)
add_test(NAME type_trick_03 COMMAND type_trick_03)
add_test(NAME type_trick_04 COMMAND type_trick_04)
add_test(NAME type_trick_05 COMMAND type_trick_05)
```

### 4.3 公共库设计

```cmake
# include/CMakeLists.txt

# 通用工具库 (仅头文件)
add_library(common_utils INTERFACE)
target_include_directories(common_utils INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}
)
target_compile_features(common_utils INTERFACE cxx_std_17)
```

## 5. 头文件设计

### 5.1 common.hpp

```cpp
/**
 * @file common.hpp
 * @brief 通用工具宏和函数
 */

#ifndef CPP_TRICKS_COMMON_HPP
#define CPP_TRICKS_COMMON_HPP

#include <iostream>
#include <string>
#include <chrono>

// ============================================================================
// 调试宏
// ============================================================================

#ifdef DEBUG
    #define DBG_PRINT(msg) std::cout << "[DEBUG] " << msg << std::endl
    #define DBG_VAR(var) std::cout << "[DEBUG] " << #var << " = " << var << std::endl
#else
    #define DBG_PRINT(msg)
    #define DBG_VAR(var)
#endif

// ============================================================================
// 分隔符
// ============================================================================

#define SECTION_BEGIN(title) \
    std::cout << "\n=== " << title << " ===" << std::endl

#define SECTION_END() \
    std::cout << std::endl

// ============================================================================
// 计时工具
// ============================================================================

/**
 * @brief 简单的作用域计时器
 */
class ScopedTimer {
public:
    explicit ScopedTimer(const std::string& name)
        : name_(name)
        , start_(std::chrono::high_resolution_clock::now()) {}

    ~ScopedTimer() {
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start_);
        std::cout << "[TIMER] " << name_ << ": " << duration.count() << " μs" << std::endl;
    }

private:
    std::string name_;
    std::chrono::high_resolution_clock::time_point start_;
};

#define TIMER_SCOPE(name) ScopedTimer timer_##__LINE__(name)

// ============================================================================
// 类型名称工具
// ============================================================================

/**
 * @brief 获取类型的可读名称 (使用 typeid)
 */
template <typename T>
std::string type_name() {
    return typeid(T).name();
}

// ============================================================================
// 断言工具
// ============================================================================

/**
 * @brief 带消息的断言
 */
#define ASSERT_MSG(condition, message) \
    do { \
        if (!(condition)) { \
            std::cerr << "Assertion failed: " << #condition << std::endl; \
            std::cerr << "Message: " << message << std::endl; \
            std::cerr << "File: " << __FILE__ << std::endl; \
            std::cerr << "Line: " << __LINE__ << std::endl; \
            std::abort(); \
        } \
    } while (0)

#endif // CPP_TRICKS_COMMON_HPP
```

### 5.2 type_utils.hpp

```cpp
/**
 * @file type_utils.hpp
 * @brief 类型工具库
 */

#ifndef CPP_TRICKS_TYPE_UTILS_HPP
#define CPP_TRICKS_TYPE_UTILS_HPP

#include <type_traits>
#include <string>

namespace cpp_tricks {

// ============================================================================
// 类型名称打印
// ============================================================================

/**
 * @brief 编译期类型名称打印 (使用 __PRETTY_FUNCTION__)
 *
 * 注意: 此函数返回的字符串包含函数签名，需要手动提取类型名。
 * 不同编译器输出格式不同。
 */
template <typename T>
constexpr auto type_name_raw() {
    return __PRETTY_FUNCTION__;
}

// ============================================================================
// 类型检查工具
// ============================================================================

/**
 * @brief 检查类型是否可打印 (有 operator<<)
 */
template <typename T, typename = void>
struct is_printable : std::false_type {};

template <typename T>
struct is_printable<T, std::void_t<decltype(std::declval<std::ostream&>() << std::declval<T>())>>
    : std::true_type {};

template <typename T>
constexpr bool is_printable_v = is_printable<T>::value;

// ============================================================================
// 类型转换工具
// ============================================================================

/**
 * @brief 安全的向下转换 (使用 dynamic_cast)
 */
template <typename Derived, typename Base>
Derived* safe_downcast(Base* base) {
    return dynamic_cast<Derived*>(base);
}

/**
 * @brief 安全的向下转换 (引用版本，失败抛出异常)
 */
template <typename Derived, typename Base>
Derived& safe_downcast(Base& base) {
    return dynamic_cast<Derived&>(base);
}

} // namespace cpp_tricks

#endif // CPP_TRICKS_TYPE_UTILS_HPP
```

## 6. 设计模式应用

### 6.1 RAII 模式

**应用场景**: 所有资源管理

```cpp
class FileHandle {
public:
    explicit FileHandle(const std::string& filename)
        : file_(fopen(filename.c_str(), "r")) {
        if (!file_) {
            throw std::runtime_error("Failed to open file");
        }
    }

    ~FileHandle() {
        if (file_) {
            fclose(file_);
        }
    }

    // 禁止拷贝
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;

    // 允许移动
    FileHandle(FileHandle&& other) noexcept : file_(other.file_) {
        other.file_ = nullptr;
    }

    FileHandle& operator=(FileHandle&& other) noexcept {
        if (this != &other) {
            if (file_) fclose(file_);
            file_ = other.file_;
            other.file_ = nullptr;
        }
        return *this;
    }

    FILE* get() const { return file_; }

private:
    FILE* file_;
};
```

### 6.2 策略模式 (使用模板)

**应用场景**: 类型特定的行为选择

```cpp
// 排序策略
struct QuickSortPolicy {
    template <typename Iterator>
    static void sort(Iterator begin, Iterator end) {
        std::sort(begin, end);
    }
};

struct MergeSortPolicy {
    template <typename Iterator>
    static void sort(Iterator begin, Iterator end) {
        std::stable_sort(begin, end);
    }
};

// 使用策略的容器
template <typename T, typename SortPolicy = QuickSortPolicy>
class SortedVector {
public:
    void push(const T& value) {
        data_.push_back(value);
        SortPolicy::sort(data_.begin(), data_.end());
    }

    const std::vector<T>& data() const { return data_; }

private:
    std::vector<T> data_;
};
```

### 6.3 CRTP 模式

**应用场景**: 静态多态、编译期接口

```cpp
// CRTP 基类
template <typename Derived>
class Printable {
public:
    void print() const {
        static_cast<const Derived*>(this)->print_impl();
    }
};

// 派生类
class MyClass : public Printable<MyClass> {
public:
    void print_impl() const {
        std::cout << "MyClass instance" << std::endl;
    }
};
```

### 6.4 作用域守卫模式

**应用场景**: 异常安全的资源清理

```cpp
template <typename Callable>
class ScopeGuard {
public:
    explicit ScopeGuard(Callable&& func)
        : func_(std::forward<Callable>(func))
        , active_(true) {}

    ~ScopeGuard() {
        if (active_) {
            func_();
        }
    }

    void dismiss() { active_ = false; }

    // 禁止拷贝和移动
    ScopeGuard(const ScopeGuard&) = delete;
    ScopeGuard& operator=(const ScopeGuard&) = delete;

private:
    Callable func_;
    bool active_;
};

template <typename Callable>
ScopeGuard<Callable> make_scope_guard(Callable&& func) {
    return ScopeGuard<Callable>(std::forward<Callable>(func));
}
```

## 7. 代码风格规范

### 7.1 命名规范

| 元素 | 风格 | 示例 |
|------|------|------|
| 命名空间 | snake_case | `namespace cpp_tricks` |
| 类名 | PascalCase | `class ScopedTimer` |
| 函数名 | snake_case | `void print_info()` |
| 变量名 | snake_case | `int count_` |
| 成员变量 | snake_case + 尾下划线 | `std::string name_` |
| 常量 | UPPER_SNAKE_CASE | `const int MAX_SIZE` |
| 模板参数 | PascalCase | `template <typename T>` |
| 宏 | UPPER_SNAKE_CASE | `#define DBG_PRINT` |

### 7.2 注释规范

```cpp
/**
 * @brief 函数简要描述
 *
 * 详细描述函数的功能、参数、返回值等。
 *
 * @param param1 参数1描述
 * @param param2 参数2描述
 * @return 返回值描述
 * @throw exception_type 异常描述
 *
 * @code
 * // 使用示例
 * int result = function(1, 2);
 * @endcode
 */
int function(int param1, int param2);
```

### 7.3 文件组织规范

1. **头文件保护**: 使用 `#ifndef` 或 `#pragma once`
2. **包含顺序**:
   - 对应头文件
   - C 系统头文件
   - C++ 标准库头文件
   - 第三方库头文件
   - 项目内头文件
3. **命名空间**: 使用项目命名空间
4. **代码分区**: 使用注释分隔符划分代码区域

## 8. 测试设计

### 8.1 测试框架选择

- **推荐**: Google Test (gtest)
- **备选**: Catch2, doctest

### 8.2 测试组织

```cpp
// tests/test_type_tricks.cpp

#include <gtest/gtest.h>
#include "type_utils.hpp"

// 测试类型名称工具
TEST(TypeUtilsTest, TypeName) {
    // 测试基本类型
    EXPECT_EQ(cpp_tricks::type_name<int>(), "int");
    EXPECT_EQ(cpp_tricks::type_name<double>(), "double");
}

// 测试类型检查工具
TEST(TypeUtilsTest, IsPrintable) {
    EXPECT_TRUE(cpp_tricks::is_printable_v<int>);
    EXPECT_TRUE(cpp_tricks::is_printable_v<std::string>);
}

// 测试安全转换
TEST(TypeUtilsTest, SafeDowncast) {
    class Base { public: virtual ~Base() = default; };
    class Derived : public Base {};

    Derived derived;
    Base* base = &derived;

    // 成功转换
    EXPECT_NE(cpp_tricks::safe_downcast<Derived>(base), nullptr);
}
```

### 8.3 测试覆盖要求

- **单元测试**: 每个工具函数都有测试
- **集成测试**: 每个技巧示例都能正确运行
- **边界测试**: 测试边界条件和异常情况
- **性能测试**: 关键技巧有性能基准

## 9. 部署设计

### 9.1 构建产物

```
build/
├── bin/                    # 可执行文件
│   ├── type_trick_01
│   ├── type_trick_02
│   └── ...
├── lib/                    # 库文件 (如果有)
└── test/                   # 测试可执行文件
    ├── test_type_tricks
    └── ...
```

### 9.2 安装配置

```cmake
# 安装目标
install(TARGETS type_trick_01 type_trick_02 ...
        RUNTIME DESTINATION bin)

# 安装头文件
install(DIRECTORY include/
        DESTINATION include/cpp-tricks
        FILES_MATCHING PATTERN "*.hpp")
```

## 10. 扩展设计

### 10.1 添加新技巧

1. 在对应目录创建新文件 `XX_new_trick.cpp`
2. 遵循文件模板格式
3. 更新目录的 `CMakeLists.txt`
4. 更新目录的 `README.md`
5. 更新主 `README.md` 的技巧列表

### 10.2 添加新分类

1. 创建新目录 `src/new_category/`
2. 创建目录的 `CMakeLists.txt`
3. 创建目录的 `README.md`
4. 更新主 `CMakeLists.txt` 添加子目录
5. 更新主 `README.md` 的分类列表

### 10.3 版本管理

- **主版本号**: 架构重大变更
- **次版本号**: 新增技巧或分类
- **修订号**: Bug 修复和文档更新
