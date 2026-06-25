# 05_DEVELOPMENT.md - 开发手册

## 编译说明

### 环境要求

| 工具 | 最低版本 | 推荐版本 |
|------|---------|---------|
| GCC | 10.0 | 13.0+ |
| Clang | 12.0 | 16.0+ |
| MSVC | 2019 16.0 | 2022 17.0+ |
| CMake | 3.16 | 3.25+ |

### 编译步骤

```bash
# 1. 克隆项目
cd projects/cpp-template-metaprogramming-advanced

# 2. 创建构建目录
mkdir build && cd build

# 3. 配置 (Debug)
cmake -DCMAKE_BUILD_TYPE=Debug ..

# 或配置 (Release)
cmake -DCMAKE_BUILD_TYPE=Release ..

# 4. 编译所有示例
cmake --build . --parallel

# 5. 编译特定目标
cmake --build . --target example_crtp
cmake --build . --target test_type_list
```

### 编译选项

```bash
# 启用所有警告
cmake -DCMAKE_CXX_FLAGS="-Wall -Wextra -Wpedantic" ..

# 启用地址消毒
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address" ..

# 启用未定义行为消毒
cmake -DCMAKE_CXX_FLAGS="-fsanitize=undefined" ..
```

## 运行方式

### 运行示例

```bash
# 运行表达式模板示例
./examples/example_expression_templates

# 运行 CRTP 示例
./examples/example_crtp

# 运行编译期排序示例
./examples/example_compile_time_sort

# 运行所有示例
for exe in ./examples/example_*; do
    echo "=== Running $exe ==="
    $exe
    echo
done
```

### 运行测试

```bash
# 运行类型列表测试
./tests/test_type_list

# 运行编译期算法测试
./tests/test_compile_time_algorithms

# 运行 SFINAE 测试
./tests/test_sfinae

# 运行应用测试
./tests/test_applications

# 运行所有测试
for test in ./tests/test_*; do
    echo "=== Running $test ==="
    $test
    echo
done
```

## 调试技巧

### 1. 查看模板实例化

```bash
# 使用 -ftemplate-backtrace-limit=0 查看完整模板错误
g++ -ftemplate-backtrace-limit=0 -std=c++20 your_file.cpp
```

### 2. 使用 static_assert

```cpp
// 编译期验证
static_assert(std::is_same_v<result, expected>, "Type mismatch");
static_assert(value == 42, "Value mismatch");
```

### 3. 使用 Concepts 约束

```cpp
// 提供更好的错误信息
template <typename T>
concept Container = requires(T t) {
    { t.size() } -> std::convertible_to<std::size_t>;
};

template <Container C>
void process(const C& container) { ... }
```

### 4. 使用编译器特定工具

```bash
# GCC: 查看模板实例化
g++ -std=c++20 -ftime-report your_file.cpp

# Clang: 查看模板深度
clang++ -std=c++20 -ftemplate-depth=100 your_file.cpp
```

## 常见问题

### Q1: 编译时间过长
**原因**: 过深的模板递归或大量模板实例化

**解决方案**:
1. 限制递归深度
2. 使用尾递归优化
3. 减少不必要的模板实例化

### Q2: 错误信息难以理解
**原因**: 模板错误信息通常很长

**解决方案**:
1. 使用 Concepts (C++20)
2. 添加 static_assert
3. 分步骤实现

### Q3: 链接错误
**原因**: 模板定义不在头文件中

**解决方案**:
1. 将模板定义放在头文件中
2. 使用显式实例化

### Q4: 运行时错误
**原因**: 编译期代码无法调试

**解决方案**:
1. 使用 constexpr 函数
2. 添加编译期断言
3. 分步验证

## 代码规范

### 命名规范
- 类型名: `PascalCase` (如 `TypeList`, `BubbleSort`)
- 函数名: `snake_case` (如 `push_back`, `is_sorted`)
- 常量名: `kPascalCase` 或 `UPPER_SNAKE_CASE`
- 模板参数: `PascalCase` (如 `T`, `Derived`, `Policy`)

### 注释规范
- 文件头: 描述文件内容和功能
- 函数: 描述功能、参数、返回值
- 复杂逻辑: 解释实现原理
- 示例: 提供使用示例

### 代码风格
- 缩进: 4 个空格
- 行宽: 80 字符
- 大括号: 放在新行
- 空行: 函数之间空一行

## 贡献指南

### 添加新示例
1. 在 `examples/` 目录创建 `.cpp` 文件
2. 在 `CMakeLists.txt` 添加 `add_example()`
3. 更新 `README.md` 的项目结构

### 添加新测试
1. 在 `tests/` 目录创建 `.cpp` 文件
2. 在 `CMakeLists.txt` 添加 `add_test_exec()`
3. 使用 `static_assert` 进行编译期验证

### 添加新模块
1. 在 `include/` 对应目录创建 `.hpp` 文件
2. 添加详细注释
3. 创建对应的示例和测试
4. 更新文档
