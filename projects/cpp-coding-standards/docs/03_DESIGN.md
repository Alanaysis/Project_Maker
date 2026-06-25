# 技术设计

## 文件组织

### 目录结构设计

```
cpp-coding-standards/
├── examples/                    # 代码示例（按主题分类）
│   ├── 01-naming/              # 命名规范
│   │   ├── CMakeLists.txt
│   │   ├── naming_demo.cpp
│   │   └── README.md
│   ├── 02-formatting/          # 代码格式
│   │   ├── CMakeLists.txt
│   │   ├── formatting_demo.cpp
│   │   └── README.md
│   └── ...
├── docs/                        # 文档
├── include/                     # 公共头文件
│   └── cpp_standards/          # 命名空间
│       ├── naming.h
│       ├── formatting.h
│       └── ...
├── src/                         # 源代码实现
├── tests/                       # 测试文件
├── tools/                       # 工具配置
└── CMakeLists.txt               # 主 CMake 配置
```

### 文件命名规范

**头文件：**
- 使用 `.h` 或 `.hpp` 扩展名
- 文件名使用 snake_case
- 示例：`naming_conventions.h`

**源文件：**
- 使用 `.cpp` 扩展名
- 文件名与头文件一致
- 示例：`naming_conventions.cpp`

**测试文件：**
- 使用 `_test.cpp` 后缀
- 文件名与被测试文件一致
- 示例：`naming_conventions_test.cpp`

## 示例设计

### 示例结构设计

每个示例目录包含：

1. **CMakeLists.txt** - 构建配置
2. **main.cpp** - 主程序入口
3. **good_example.cpp** - 良好代码示例
4. **bad_example.cpp** - 糟糕代码示例
5. **README.md** - 示例说明

### 示例内容设计

**命名规范示例设计：**

```cpp
// good_example.cpp - 良好命名示例

// 1. 变量命名 - 使用描述性名称
int user_age = 25;                    // snake_case
std::string userName = "Alice";       // camelCase
constexpr int MAX_RETRY_COUNT = 3;    // UPPER_CASE

// 2. 函数命名 - 动词开头，描述功能
void calculateTotalPrice();
bool is_valid_email(const std::string& email);
std::string getUserName(int user_id);

// 3. 类命名 - PascalCase
class UserManager;
class DatabaseConnection;
class HttpRequest;
```

```cpp
// bad_example.cpp - 糟糕命名示例

// 1. 变量命名 - 使用模糊名称
int a = 25;                           // 无意义
std::string s = "Alice";              // 无意义
int cnt = 3;                          // 缩写模糊

// 2. 函数命名 - 不清晰
void calc();                          // 无意义
bool check();                         // 检查什么？
void process();                       // 处理什么？

// 3. 类命名 - 不清晰
class Manager;                        // 管理什么？
class Handler;                        // 处理什么？
class Data;                           // 什么数据？
```

### 代码格式示例设计

**K&R 风格：**
```cpp
if (condition) {
    // code
} else {
    // code
}
```

**Allman 风格：**
```cpp
if (condition)
{
    // code
}
else
{
    // code
}
```

**GNU 风格：**
```cpp
if (condition)
  {
    // code
  }
else
  {
    // code
  }
```

### 类设计示例设计

**良好类设计：**
```cpp
class User {
public:
    // 类型别名
    using UserId = int;
    
    // 构造函数
    explicit User(UserId id, std::string name);
    
    // 公共接口
    UserId getId() const;
    const std::string& getName() const;
    void setName(std::string name);
    
private:
    // 数据成员
    UserId id_;
    std::string name_;
    std::string email_;
};
```

**糟糕类设计：**
```cpp
class User {
    int id;
    std::string name;
public:
    User(int i, std::string n) : id(i), name(n) {}
    int getId() { return id; }
    void setId(int i) { id = i; }
    std::string getName() { return name; }
    void setName(std::string n) { name = n; }
};
```

### 内存管理示例设计

**良好内存管理：**
```cpp
class Database {
public:
    Database() : connection_(std::make_unique<Connection>()) {}
    
    void query(const std::string& sql) {
        connection_->execute(sql);
    }
    
private:
    std::unique_ptr<Connection> connection_;
};
```

**糟糕内存管理：**
```cpp
class Database {
public:
    Database() : connection_(new Connection()) {}
    
    ~Database() {
        delete connection_;
    }
    
    void query(const std::string& sql) {
        connection_->execute(sql);
    }
    
private:
    Connection* connection_;
};
```

## 工具配置设计

### Clang-Format 配置设计

```yaml
# .clang-format
BasedOnStyle: Google
IndentWidth: 2
ColumnLimit: 80
AllowShortFunctionsOnASingleLine: Empty
AllowShortIfStatementsOnASingleLine: Never
AllowShortLoopsOnASingleLine: false
BreakBeforeBraces: Attach
PointerAlignment: Left
SpaceAfterCStyleCast: false
SpaceBeforeParens: ControlStatements
```

### Clang-Tidy 配置设计

```yaml
# .clang-tidy
Checks: >
  -*,
  clang-analyzer-*,
  modernize-*,
  readability-*,
  performance-*,
  bugprone-*,
  misc-*,
  cppcoreguidelines-*
```

### EditorConfig 配置设计

```ini
# .editorconfig
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{cpp,h,hpp}]
indent_style = space
indent_size = 2

[CMakeLists.txt]
indent_style = space
indent_size = 2

[*.md]
indent_style = space
indent_size = 2
```

## 测试设计

### 单元测试设计

使用 Google Test 框架：

```cpp
#include <gtest/gtest.h>
#include "cpp_standards/naming.h"

TEST(NamingConventions, VariableNaming) {
    // 测试变量命名规范
    EXPECT_TRUE(is_valid_variable_name("user_age"));
    EXPECT_FALSE(is_valid_variable_name("a"));
}

TEST(NamingConventions, FunctionNaming) {
    // 测试函数命名规范
    EXPECT_TRUE(is_valid_function_name("calculateTotal"));
    EXPECT_FALSE(is_valid_function_name("calc"));
}
```

### 集成测试设计

```cpp
TEST(CodeFormatting, ClangFormat) {
    // 测试代码格式化
    std::string code = "int main(){return 0;}";
    std::string formatted = format_code(code);
    EXPECT_EQ(formatted, "int main() {\n  return 0;\n}\n");
}
```

## 构建设计

### CMake 配置设计

```cmake
cmake_minimum_required(VERSION 3.16)
project(cpp-coding-standards LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 添加子目录
add_subdirectory(examples/01-naming)
add_subdirectory(examples/02-formatting)
# ...

# 添加测试
enable_testing()
add_subdirectory(tests)
```

### 示例 CMake 配置设计

```cmake
# examples/01-naming/CMakeLists.txt
add_executable(naming_demo
    naming_demo.cpp
)

target_link_libraries(naming_demo PRIVATE
    cpp_standards
)

target_include_directories(naming_demo PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)
```
