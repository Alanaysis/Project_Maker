# C++11/14 新特性开发文档

## 1. 开发环境

### 1.1 编译器要求

| 编译器 | 最低版本 | 推荐版本 |
|-------|---------|---------|
| GCC | 5.0 | 9.0+ |
| Clang | 3.4 | 10.0+ |
| MSVC | 19.0 | 19.20+ |

### 1.2 构建工具

- CMake 3.10+
- Make 或 Ninja

### 1.3 依赖库

- Google Test（用于测试）

### 1.4 IDE 推荐

- Visual Studio Code + C/C++ 扩展
- CLion
- Visual Studio 2019+
- Qt Creator

## 2. 项目结构

```
cpp11-14-features/
├── CMakeLists.txt              # 主 CMake 配置
├── README.md                   # 项目说明
├── build.sh                    # 构建脚本
├── run.sh                      # 运行脚本
├── docs/                       # 文档目录
├── examples/                   # 示例代码
├── tests/                      # 测试代码
├── include/                    # 头文件
└── LEARNING_NOTES.md           # 学习笔记
```

## 3. 构建系统

### 3.1 CMake 配置

主 `CMakeLists.txt` 配置：

```cmake
cmake_minimum_required(VERSION 3.10)
project(cpp11-14-features LANGUAGES CXX)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# 包含目录
include_directories(${CMAKE_SOURCE_DIR}/include)
```

### 3.2 构建命令

```bash
# 基本构建
mkdir build && cd build
cmake ..
make

# 指定编译器
cmake .. -DCMAKE_CXX_COMPILER=g++-9

# 指定构建类型
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake .. -DCMAKE_BUILD_TYPE=Debug

# 并行编译
make -j$(nproc)
```

### 3.3 使用构建脚本

```bash
# 编译项目
./build.sh build

# 运行测试
./build.sh test

# 运行示例
./build.sh examples

# 清理构建文件
./build.sh clean

# 完整流程
./build.sh all
```

## 4. 开发流程

### 4.1 添加新示例

1. 在 `examples/` 目录创建新文件：
   ```bash
   touch examples/10_new_feature.cpp
   ```

2. 实现示例代码，参考现有示例的结构

3. 更新 `CMakeLists.txt`：
   ```cmake
   set(EXAMPLES
       # ... 现有示例
       10_new_feature
   )
   ```

4. 添加对应的测试文件

5. 更新文档

### 4.2 添加新测试

1. 在 `tests/` 目录创建新文件：
   ```bash
   touch tests/test_new_feature.cpp
   ```

2. 实现测试代码，使用 Google Test 框架

3. 更新 `tests/CMakeLists.txt`

4. 运行测试验证：
   ```bash
   ./build.sh test
   ```

### 4.3 代码风格

#### 命名规范

- **类名**：PascalCase（如 `MyClass`）
- **函数名**：camelCase（如 `myFunction`）
- **变量名**：snake_case（如 `my_variable`）
- **常量**：UPPER_SNAKE_CASE（如 `MY_CONSTANT`）
- **模板参数**：PascalCase（如 `typename T`）

#### 代码格式

- 缩进：4 个空格
- 行宽：80 字符
- 大括号：单独一行
- 注释：使用 `//` 或 `/* */`

#### 示例代码风格

```cpp
/**
 * 文件说明
 *
 * 学习目标：
 * 1. 目标一
 * 2. 目标二
 */

#include <iostream>

// 常量定义
constexpr int MAX_SIZE = 100;

// 类定义
class MyClass {
    int value_;

public:
    // 构造函数
    MyClass(int value) : value_(value) {}

    // 成员函数
    int getValue() const { return value_; }
};

// 函数定义
void demonstrate_feature() {
    std::cout << "演示特性" << std::endl;
}

// 主函数
int main() {
    demonstrate_feature();
    return 0;
}
```

## 5. 调试技巧

### 5.1 使用 GDB

```bash
# 编译调试版本
cmake .. -DCMAKE_BUILD_TYPE=Debug
make

# 运行 GDB
gdb ./build/01_move_semantics

# GDB 常用命令
(gdb) break main          # 设置断点
(gdb) run                 # 运行程序
(gdb) next                # 单步执行
(gdb) step                # 进入函数
(gdb) print variable      # 打印变量
(gdb) backtrace           # 查看调用栈
(gdb) quit                # 退出
```

### 5.2 使用 Valgrind

```bash
# 检查内存泄漏
valgrind --leak-check=full ./build/01_move_semantics

# 检查线程错误
valgrind --tool=helgrind ./build/04_threads
```

### 5.3 使用 AddressSanitizer

```bash
# 编译时启用
cmake .. -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_FLAGS="-fsanitize=address"
make

# 运行程序
./build/01_move_semantics
```

## 6. 性能分析

### 6.1 使用 gprof

```bash
# 编译时启用
cmake .. -DCMAKE_CXX_FLAGS="-pg"
make

# 运行程序
./build/01_move_semantics

# 分析结果
gprof ./build/01_move_semantics gmon.out > analysis.txt
```

### 6.2 使用 perf

```bash
# 记录性能数据
perf record ./build/01_move_semantics

# 分析结果
perf report
```

## 7. 文档生成

### 7.1 使用 Doxygen

```bash
# 安装 Doxygen
sudo apt-get install doxygen

# 生成文档
doxygen Doxyfile
```

### 7.2 Markdown 文档

项目文档使用 Markdown 格式，包括：
- `README.md`：项目说明
- `docs/`：详细文档
- `LEARNING_NOTES.md`：学习笔记

## 8. 版本控制

### 8.1 Git 工作流

```bash
# 创建特性分支
git checkout -b feature/new-feature

# 提交更改
git add .
git commit -m "feat: 添加新特性"

# 推送分支
git push origin feature/new-feature

# 创建 Pull Request
```

### 8.2 提交规范

使用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- `feat`：新功能
- `fix`：修复
- `docs`：文档
- `style`：格式
- `refactor`：重构
- `test`：测试
- `chore`：构建/工具

## 9. 发布流程

### 9.1 版本号

使用语义化版本号：`MAJOR.MINOR.PATCH`

- `MAJOR`：不兼容的 API 更改
- `MINOR`：向后兼容的功能添加
- `PATCH`：向后兼容的修复

### 9.2 发布检查清单

- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新
- [ ] 构建脚本正常工作

## 10. 故障排除

### 10.1 常见问题

**问题**：编译错误：`'constexpr' function is not valid`
**解决**：检查编译器版本，确保支持 C++14

**问题**：链接错误：`undefined reference to 'pthread_create'`
**解决**：在 CMakeLists.txt 中添加 `pthread` 链接

**问题**：测试失败：`No such file or directory`
**解决**：确保 Google Test 已正确安装

### 10.2 获取帮助

- 查看项目文档
- 搜索 GitHub Issues
- 提交新的 Issue
