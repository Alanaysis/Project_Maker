# 开发手册

## 编译说明

### 环境要求

- **操作系统**: Linux, macOS, Windows (WSL)
- **编译器**: GCC 7+, Clang 5+, MSVC 2017+
- **CMake**: 3.16+
- **C++ 标准**: C++17 (最低) / C++20 (推荐)

### 快速编译

```bash
# 进入项目目录
cd projects/cpp-template-metaprogramming

# 创建构建目录
mkdir build && cd build

# 配置项目
cmake ..

# 编译所有示例
make

# 或者使用并行编译
make -j$(nproc)
```

### 编译单个示例

```bash
# 进入源文件目录
cd src/01_template_basics

# 编译单个文件
g++ -std=c++17 -I../../include -o function_templates function_templates.cpp

# 运行
./function_templates
```

### 编译选项

#### 调试模式

```bash
g++ -std=c++17 -g -O0 -Wall -Wextra -I../../include -o demo demo.cpp
```

#### 优化模式

```bash
g++ -std=c++17 -O2 -DNDEBUG -I../../include -o demo demo.cpp
```

#### C++20 模式

```bash
g++ -std=c++20 -I../../include -o demo demo.cpp
```

## 运行方式

### 运行单个示例

```bash
# 编译后运行
./function_templates
./class_templates
./specialization
# ... 其他示例
```

### 运行所有示例

```bash
# 使用脚本运行所有示例
for demo in build/*; do
    echo "=== Running $demo ==="
    ./$demo
    echo ""
done
```

### 测试

```bash
# 进入构建目录
cd build

# 运行所有可执行文件并检查返回值
for demo in *; do
    if [ -f "$demo" ] && [ -x "$demo" ]; then
        echo "Testing $demo..."
        ./$demo > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "  PASS"
        else
            echo "  FAIL"
        fi
    fi
done
```

## 开发指南

### 添加新示例

1. **创建源文件**

```bash
# 在对应的目录下创建新文件
touch src/01_template_basics/new_example.cpp
```

2. **编写代码**

```cpp
// =============================================================================
// new_example.cpp - 示例描述
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o new_example new_example.cpp
// 运行: ./new_example
// =============================================================================

#include <iostream>
#include "header_file.hpp"

int main() {
    std::cout << "=== 示例标题 ===" << std::endl;
    
    // 示例代码
    
    std::cout << "=== 演示完成 ===" << std::endl;
    return 0;
}
```

3. **更新 CMakeLists.txt**

```cmake
# 在 CMakeLists.txt 中添加
add_executable(new_example src/01_template_basics/new_example.cpp)
target_compile_features(new_example PRIVATE cxx_std_20)
```

4. **编译测试**

```bash
cd build
cmake ..
make new_example
./new_example
```

### 添加新头文件

1. **创建头文件**

```bash
touch include/new_module/new_header.hpp
```

2. **编写头文件**

```cpp
#pragma once
// =============================================================================
// new_header.hpp - 简短描述
// =============================================================================

namespace tmp {

// 实现代码

} // namespace tmp
```

3. **编写示例**

```cpp
#include "new_module/new_header.hpp"

// 使用示例
```

### 代码风格

#### 命名规范

- **命名空间**: `tmp`
- **类名**: PascalCase (`TypeList`, `IntegerSequence`)
- **函数名**: snake_case (`is_same_v`, `make_index_sequence`)
- **变量名**: snake_case (`value`, `size`)
- **常量**: kPascalCase 或 SCREAMING_SNAKE_CASE
- **模板参数**: PascalCase (`T`, `Args`, `Pred`)

#### 注释规范

```cpp
// 文件头注释
// =============================================================================
// filename.hpp - 简短描述
// =============================================================================

// 章节注释
// ---------------------------------------------------------------------------
// 1. 章节标题
// ---------------------------------------------------------------------------

// 功能注释
// 简短描述函数或类的功能
```

#### 格式规范

- 使用 4 空格缩进
- 每行不超过 100 字符
- 函数之间空一行
- 类成员之间空一行

## 调试技巧

### 1. 使用 static_assert

```cpp
static_assert(std::is_same_v<result_type, expected_type>,
              "Type mismatch!");
```

### 2. 使用编译器探索器

访问 [Godbolt](https://godbolt.org/) 查看生成的汇编代码。

### 3. 使用类型名称打印

```cpp
template <typename T>
struct type_printer;

type_printer<your_type> tp;  // 编译错误会显示类型名称
```

### 4. 使用 Boost.TypeIndex

```cpp
#include <boost/type_index.hpp>
std::cout << boost::typeindex::type_id_with_cvr<T>().pretty_name();
```

## 常见问题

### Q1: 编译错误信息太长

**A**: 使用 Concepts (C++20) 或添加 static_assert 约束。

### Q2: 编译时间太长

**A**: 减少模板实例化次数，使用 extern template。

### Q3: 链接错误

**A**: 检查模板特化的声明和定义是否一致。

### Q4: 运行时错误

**A**: 检查模板参数是否正确，使用调试模式编译。

## 参考资源

### 编译器文档

- [GCC 文档](https://gcc.gnu.org/onlinedocs/)
- [Clang 文档](https://clang.llvm.org/docs/)
- [MSVC 文档](https://docs.microsoft.com/en-us/cpp/)

### 在线工具

- [Godbolt Compiler Explorer](https://godbolt.org/)
- [Quick C++ Benchmark](https://quick-bench.com/)
- [C++ Insights](https://cppinsights.io/)

### 学习资源

- [cppreference.com](https://en.cppreference.com/)
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/)
- [C++ Annotations](https://www.icce.rug.nl/documents/cplusplus/)
