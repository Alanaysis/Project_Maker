# C++17 新特性实践项目 - 技术设计

## 文件组织

### 目录结构

```
cpp17-features/
├── CMakeLists.txt              # 主构建配置
├── README.md                   # 项目说明
├── 01_RESEARCH.md             # 市场调研
├── 02_REQUIREMENTS.md         # 需求分析
├── 03_DESIGN.md               # 技术设计（本文件）
├── 04_PRODUCT.md              # 产品思考
├── 05_DEVELOPMENT.md          # 开发手册
├── main.cpp                   # 主入口
├── optional_example.cpp       # std::optional
├── variant_example.cpp        # std::variant
├── any_example.cpp            # std::any
├── string_view_example.cpp    # std::string_view
├── structured_bindings.cpp    # 结构化绑定
├── if_constexpr_example.cpp   # if constexpr
├── fold_expressions.cpp       # 折叠表达式
├── inline_variables.cpp       # 内联变量
├── nested_namespaces.cpp      # 嵌套命名空间
├── attributes_example.cpp     # 属性
├── filesystem_example.cpp     # std::filesystem
├── apply_example.cpp          # std::apply
├── invoke_example.cpp         # std::invoke
├── gcd_lcm_example.cpp        # std::gcd/lcm
├── parallel_algorithms.cpp    # 并行算法
├── shared_mutex_example.cpp   # std::shared_mutex
├── scoped_lock_example.cpp    # std::scoped_lock
├── ctad_example.cpp           # CTAD
└── auto_extensions.cpp        # auto 扩展
```

### 命名规范

- 文件名：小写字母 + 下划线（snake_case）
- 类名：大驼峰（PascalCase）
- 函数名：小写字母 + 下划线
- 常量：大写字母 + 下划线
- 命名空间：小写字母

## 示例设计

### 1. 文件结构模板

每个示例文件遵循统一结构：

```cpp
/**
 * @file 特性名_example.cpp
 * @brief C++17 特性说明
 * 
 * 详细描述该特性的用途和优势
 */

#include <必要的头文件>
#include <iostream>

// 命名空间（可选）
namespace cpp17 {

// 辅助类/函数定义

} // namespace cpp17

// 示例函数
void 示例函数名() {
    std::cout << "=== 特性名称 ===" << std::endl;
    
    // 示例代码
    // 详细注释
    
    std::cout << std::endl;
}

// 主函数（独立运行时使用）
#ifndef COMBINED_BUILD
int main() {
    示例函数名();
    return 0;
}
#endif
```

### 2. 注释规范

```cpp
/**
 * @brief 函数简要说明
 * 
 * 详细说明函数的功能、参数、返回值
 * 
 * @param param1 参数1说明
 * @param param2 参数2说明
 * @return 返回值说明
 * 
 * @note 注意事项
 * @warning 警告信息
 * @see 相关函数
 */
```

### 3. 输出格式

每个示例输出统一格式：

```
=== 特性名称 ===
[示例1描述]
输出内容

[示例2描述]
输出内容
```

## 构建系统设计

### CMakeLists.txt 设计

```cmake
cmake_minimum_required(VERSION 3.8)
project(cpp17_features LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 独立示例可执行文件
add_executable(optional_example optional_example.cpp)
add_executable(variant_example variant_example.cpp)
# ... 其他示例

# 组合构建（可选）
option(COMBINED_BUILD "Build combined executable" OFF)
if(COMBINED_BUILD)
    add_definitions(-DCOMBINED_BUILD)
    add_executable(cpp17_features main.cpp 所有源文件)
endif()
```

### 编译选项

```cmake
# 编译器特定选项
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
elseif(MSVC)
    target_compile_options(${target} PRIVATE /W4)
endif()

# 并行算法支持（GCC）
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_link_libraries(${target} PRIVATE tbb)  # 可选
endif()
```

## 特性实现设计

### 1. std::optional 设计

**核心展示点:**
- 创建和初始化
- 值访问（value, operator*）
- 状态检查（has_value）
- 默认值处理（value_or）
- 与函数返回值结合

**示例场景:**
- 查找函数返回可选值
- 配置解析
- 链式操作

### 2. std::variant 设计

**核心展示点:**
- 创建和赋值
- 类型安全访问（get, get_if）
- 访问者模式（visit）
- 类型检查（holds_alternative）

**示例场景:**
- 多态替代
- 状态机
- 配置值类型

### 3. 结构化绑定设计

**核心展示点:**
- 绑定元组
- 绑定结构体
- 绑定数组
- 绑定 pair

**示例场景:**
- 函数返回多值
- 遍历 map
- 解构复杂数据

### 4. if constexpr 设计

**核心展示点:**
- 编译期条件分支
- 模板特化替代
- SFINAE 替代

**示例场景:**
- 类型特征检查
- 编译期算法选择
- 模板代码简化

### 5. 折叠表达式设计

**核心展示点:**
- 一元折叠
- 二元折叠
- 四种折叠形式

**示例场景:**
- 变参求和
- 日志打印
- 条件检查

## 测试策略

### 单元测试

每个示例文件独立测试：

```bash
# 编译单个示例
g++ -std=c++17 -o test_optional optional_example.cpp

# 运行测试
./test_optional
```

### 集成测试

组合构建测试：

```bash
# 组合编译
cmake -DCOMBINED_BUILD=ON ..
make

# 运行所有示例
./cpp17_features
```

### 编译器兼容性测试

```bash
# GCC
g++-7 -std=c++17 -Wall -Wextra -o test file.cpp
g++-8 -std=c++17 -Wall -Wextra -o test file.cpp
g++-9 -std=c++17 -Wall -Wextra -o test file.cpp

# Clang
clang++-5 -std=c++17 -Wall -Wextra -o test file.cpp
clang++-6 -std=c++17 -Wall -Wextra -o test file.cpp
```

## 性能考虑

### 编译时间

- 独立编译减少依赖
- 预编译头（可选）
- 模块化设计

### 运行时性能

- 零开销抽象
- 内联优化
- 移动语义

## 扩展性设计

### 添加新特性

1. 创建新的 `.cpp` 文件
2. 遵循命名规范
3. 更新 CMakeLists.txt
4. 更新 main.cpp（组合构建）
5. 更新 README.md

### 模块化设计

- 每个特性独立
- 无跨文件依赖
- 可单独编译运行
