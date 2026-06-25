# 开发手册

## 编译说明

### 环境要求

**编译器：**
- GCC 10+
- Clang 12+
- MSVC 2019+

**构建工具：**
- CMake 3.16+

**可选工具：**
- Clang-Format 12+
- Clang-Tidy 12+
- Google Test

### 编译步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd cpp-coding-standards

# 2. 创建构建目录
mkdir build && cd build

# 3. 配置项目
cmake .. -DCMAKE_BUILD_TYPE=Release

# 4. 编译项目
cmake --build . -j$(nproc)

# 5. 运行测试
ctest --output-on-failure
```

### 编译选项

**Debug 模式：**
```bash
cmake .. -DCMAKE_BUILD_TYPE=Debug
```

**Release 模式：**
```bash
cmake .. -DCMAKE_BUILD_TYPE=Release
```

**启用测试：**
```bash
cmake .. -DBUILD_TESTS=ON
```

**启用示例：**
```bash
cmake .. -DBUILD_EXAMPLES=ON
```

## 运行方式

### 运行示例

```bash
# 运行命名规范示例
./examples/01-naming/naming_demo

# 运行代码格式示例
./examples/02-formatting/formatting_demo

# 运行所有示例
for demo in examples/*/; do
    ./$demo/*_demo
done
```

### 运行测试

```bash
# 运行所有测试
ctest

# 运行特定测试
ctest -R NamingConventions

# 运行详细输出
ctest --output-on-failure -V
```

## 工具使用

### Clang-Format

**格式化单个文件：**
```bash
clang-format -i -style=file examples/01-naming/naming_demo.cpp
```

**格式化所有文件：**
```bash
find . -name "*.cpp" -o -name "*.h" | xargs clang-format -i -style=file
```

**检查格式：**
```bash
find . -name "*.cpp" -o -name "*.h" | xargs clang-format --dry-run -Werror
```

### Clang-Tidy

**检查单个文件：**
```bash
clang-tidy -p build examples/01-naming/naming_demo.cpp
```

**检查所有文件：**
```bash
find . -name "*.cpp" | xargs clang-tidy -p build
```

**自动修复：**
```bash
clang-tidy -p build --fix examples/01-naming/naming_demo.cpp
```

### EditorConfig

**安装插件：**
- VS Code: EditorConfig for VS Code
- CLion: EditorConfig 支持内置
- Vim: editorconfig-vim

**配置文件位置：**
项目根目录 `.editorconfig`

## 开发流程

### 1. 代码编写

**步骤：**
1. 创建新文件
2. 编写代码
3. 添加注释
4. 格式化代码

**示例：**
```cpp
// naming_demo.cpp
// 命名规范示例程序

#include <iostream>
#include <string>

// 用户类 - 展示类命名规范
class User {
public:
    // 构造函数
    explicit User(int id, std::string name)
        : id_(id), name_(std::move(name)) {}
    
    // 获取用户ID
    int getId() const { return id_; }
    
    // 获取用户名
    const std::string& getName() const { return name_; }
    
private:
    int id_;              // 用户ID
    std::string name_;    // 用户名
};

int main() {
    // 创建用户对象
    User user(1, "Alice");
    
    // 输出用户信息
    std::cout << "User: " << user.getName() 
              << " (ID: " << user.getId() << ")" << std::endl;
    
    return 0;
}
```

### 2. 代码审查

**检查清单：**
- [ ] 命名规范符合要求
- [ ] 代码格式正确
- [ ] 注释完整清晰
- [ ] 逻辑正确无误
- [ ] 异常处理完善
- [ ] 内存管理正确
- [ ] 线程安全考虑

### 3. 测试验证

**测试类型：**
- 单元测试
- 集成测试
- 性能测试

**测试示例：**
```cpp
#include <gtest/gtest.h>
#include "cpp_standards/naming.h"

TEST(NamingConventions, VariableNaming) {
    // 测试变量命名规范
    EXPECT_TRUE(is_valid_variable_name("user_age"));
    EXPECT_FALSE(is_valid_variable_name("a"));
    EXPECT_FALSE(is_valid_variable_name("cnt"));
}
```

### 4. 代码提交

**提交信息格式：**
```
<类型>(<范围>): <描述>

<详细说明>

<相关链接>
```

**类型：**
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

**示例：**
```
feat(naming): 添加命名规范示例

- 添加变量命名示例
- 添加函数命名示例
- 添加类命名示例
- 添加对比示例

Closes #123
```

## 常见问题

### Q1: 编译错误：找不到头文件

**原因：** CMake 配置不正确

**解决：**
```cmake
target_include_directories(your_target PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)
```

### Q2: Clang-Format 不生效

**原因：** 配置文件路径不正确

**解决：**
确保 `.clang-format` 文件在项目根目录

### Q3: Clang-Tidy 报告太多警告

**原因：** 检查规则太严格

**解决：**
编辑 `.clang-tidy` 文件，禁用不需要的检查

### Q4: 测试失败

**原因：** 代码逻辑错误或测试用例不正确

**解决：**
1. 检查测试用例
2. 检查代码逻辑
3. 使用调试器定位问题

## 最佳实践

### 1. 代码组织

**原则：**
- 一个文件一个类
- 头文件和源文件分离
- 目录结构清晰

### 2. 命名规范

**原则：**
- 一致性最重要
- 描述性命名
- 避免缩写

### 3. 注释规范

**原则：**
- 注释解释为什么
- 代码解释怎么做
- 保持注释更新

### 4. 错误处理

**原则：**
- 异常用于不可恢复错误
- 错误码用于可恢复错误
- 断言用于逻辑检查

### 5. 内存管理

**原则：**
- RAII 优先
- 智能指针优先
- 避免裸 new/delete

## 参考资源

### 官方文档
- [CMake Documentation](https://cmake.org/cmake/help/latest/)
- [Clang-Format Documentation](https://clang.llvm.org/docs/ClangFormat.html)
- [Clang-Tidy Documentation](https://clang.llvm.org/extra/clang-tidy/)
- [Google Test Documentation](https://github.com/google/googletest/blob/main/docs)

### 工具下载
- [CMake](https://cmake.org/download/)
- [LLVM](https://releases.llvm.org/)
- [Google Test](https://github.com/google/googletest)
