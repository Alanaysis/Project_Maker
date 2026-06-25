# 03 技术设计

## 设计目标

1. **模块化**：每个陷阱独立成文件，便于学习和维护
2. **可运行**：所有代码可直接编译运行
3. **对比性**：错误代码和正确代码对比展示
4. **可扩展**：易于添加新的陷阱示例

## 文件组织

### 目录结构

```
cpp-pitfalls-best-practices/
├── CMakeLists.txt              # 顶层构建配置
├── README.md                   # 项目说明
├── docs/                       # 文档目录
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_PRODUCT.md
│   └── 05_DEVELOPMENT.md
└── src/                        # 源代码目录
    ├── memory/                 # 内存陷阱
    │   ├── CMakeLists.txt
    │   ├── 01_dangling_pointer.cpp
    │   ├── 02_memory_leak.cpp
    │   ├── 03_double_free.cpp
    │   ├── 04_buffer_overflow.cpp
    │   ├── 05_wild_pointer.cpp
    │   └── 06_use_after_free.cpp
    ├── type/                   # 类型陷阱
    │   ├── CMakeLists.txt
    │   ├── 01_implicit_conversion.cpp
    │   ├── 02_integer_overflow.cpp
    │   ├── 03_floating_point.cpp
    │   ├── 04_signed_unsigned.cpp
    │   ├── 05_type_truncation.cpp
    │   └── 06_null_dereference.cpp
    ├── template/               # 模板陷阱
    │   ├── CMakeLists.txt
    │   ├── 01_instantiation.cpp
    │   ├── 02_specialization.cpp
    │   ├── 03_sfinae.cpp
    │   ├── 04_compile_errors.cpp
    │   └── 05_dependent_type.cpp
    ├── concurrency/            # 并发陷阱
    │   ├── CMakeLists.txt
    │   ├── 01_data_race.cpp
    │   ├── 02_deadlock.cpp
    │   ├── 03_livelock.cpp
    │   ├── 04_atomic_traps.cpp
    │   ├── 05_memory_order.cpp
    │   └── 06_false_sharing.cpp
    ├── lifetime/               # 生命周期陷阱
    │   ├── CMakeLists.txt
    │   ├── 01_object_lifetime.cpp
    │   ├── 02_temporary_object.cpp
    │   ├── 03_dangling_reference.cpp
    │   ├── 04_use_after_move.cpp
    │   └── 05_destruction_order.cpp
    ├── exception/              # 异常安全陷阱
    │   ├── CMakeLists.txt
    │   ├── 01_safety_levels.cpp
    │   ├── 02_resource_leak.cpp
    │   ├── 03_exception_propagation.cpp
    │   └── 04_noexcept.cpp
    ├── best_practices/         # 最佳实践
    │   ├── CMakeLists.txt
    │   ├── 01_modern_cpp.cpp
    │   ├── 02_raii.cpp
    │   ├── 03_smart_pointers.cpp
    │   ├── 04_value_semantics.cpp
    │   ├── 05_const_correctness.cpp
    │   └── 06_naming_conventions.cpp
    └── quality/                # 代码质量
        ├── CMakeLists.txt
        ├── 01_code_review.cpp
        ├── 02_static_analysis.cpp
        ├── 03_dynamic_analysis.cpp
        ├── 04_testing.cpp
        └── 05_documentation.cpp
```

## 示例设计

### 1. 代码文件结构

每个陷阱示例文件遵循以下结构：

```cpp
/**
 * @file 01_dangling_pointer.cpp
 * @brief 悬空指针陷阱示例
 * 
 * 本文件展示悬空指针的产生原因、危害和修复方法。
 */

#include <iostream>
#include <memory>

// ============================================================================
// 陷阱说明
// ============================================================================

/**
 * 悬空指针 (Dangling Pointer)
 * 
 * 定义：指向已释放内存的指针
 * 危害：可能导致程序崩溃、数据损坏、安全漏洞
 * 原因：内存释放后指针未置空
 */

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：函数返回局部变量指针
 * 
 * 问题：返回局部变量的地址，函数结束后局部变量被销毁
 */
int* bad_return_local() {
    int local_var = 42;
    return &local_var;  // 错误：返回局部变量地址
}

/**
 * 错误示例 2：释放后继续使用
 * 
 * 问题：内存释放后指针仍指向原地址
 */
void bad_use_after_free() {
    int* ptr = new int(100);
    delete ptr;
    // ptr 现在是悬空指针
    std::cout << *ptr << std::endl;  // 错误：使用已释放内存
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用智能指针
 * 
 * 解决方案：使用 std::unique_ptr 自动管理内存
 */
std::unique_ptr<int> good_smart_pointer() {
    return std::make_unique<int>(42);
}

/**
 * 正确示例 2：释放后置空
 * 
 * 解决方案：释放内存后将指针置为 nullptr
 */
void good_use_after_free() {
    int* ptr = new int(100);
    delete ptr;
    ptr = nullptr;  // 正确：释放后置空
    
    if (ptr != nullptr) {
        std::cout << *ptr << std::endl;  // 不会执行
    }
}

/**
 * 正确示例 3：使用引用代替指针
 * 
 * 解决方案：在可能的情况下使用引用
 */
void good_use_reference(int& ref) {
    std::cout << ref << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 悬空指针陷阱示例 ===" << std::endl;
    
    // 错误示例（注释掉以避免崩溃）
    // int* bad_ptr = bad_return_local();
    // std::cout << *bad_ptr << std::endl;
    
    // 正确示例
    auto good_ptr = good_smart_pointer();
    std::cout << "智能指针值: " << *good_ptr << std::endl;
    
    int value = 42;
    good_use_reference(value);
    
    return 0;
}
```

### 2. 代码组织原则

#### 2.1 文件头部
- 文件说明和作者信息
- 陷阱定义和危害说明

#### 2.2 错误示例部分
- 清晰的错误代码
- 详细的注释说明问题
- 标注错误原因

#### 2.3 正确示例部分
- 修复后的代码
- 解释修复原理
- 提供多种解决方案

#### 2.4 主函数
- 演示错误示例（注释掉危险代码）
- 演示正确示例
- 输出对比结果

### 3. 注释规范

```cpp
/**
 * @brief 简短描述
 * 
 * 详细描述
 * 
 * @param 参数说明
 * @return 返回值说明
 * @note 注意事项
 * @warning 警告信息
 * @see 参考信息
 */
```

## 构建系统设计

### CMake 配置

#### 顶层 CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.16)
project(CppPitfallsBestPractices VERSION 1.0.0 LANGUAGES CXX)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# 子目录
add_subdirectory(src/memory)
add_subdirectory(src/type)
add_subdirectory(src/template)
add_subdirectory(src/concurrency)
add_subdirectory(src/lifetime)
add_subdirectory(src/exception)
add_subdirectory(src/best_practices)
add_subdirectory(src/quality)
```

#### 子目录 CMakeLists.txt

```cmake
# src/memory/CMakeLists.txt

# 内存陷阱示例
add_executable(memory_pitfalls
    01_dangling_pointer.cpp
    02_memory_leak.cpp
    03_double_free.cpp
    04_buffer_overflow.cpp
    05_wild_pointer.cpp
    06_use_after_free.cpp
)

# 设置输出目录
set_target_properties(memory_pitfalls PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)
```

## 错误示例设计

### 1. 错误代码原则

- **清晰性**：错误代码要明显易识别
- **典型性**：选择最常见的错误形式
- **危害性**：展示错误的实际危害

### 2. 错误代码标注

```cpp
// 错误：这里会导致悬空指针
int* ptr = &local_var;
```

```cpp
// 危险：使用已释放内存
*ptr = 100;  // 未定义行为
```

### 3. 错误代码注释

```cpp
/**
 * 错误原因：
 * 1. 释放内存后未置空指针
 * 2. 继续使用已释放的指针
 * 
 * 危害：
 * 1. 程序崩溃
 * 2. 数据损坏
 * 3. 安全漏洞
 */
```

## 正确示例设计

### 1. 正确代码原则

- **安全性**：避免陷阱的正确做法
- **现代性**：使用现代 C++ 特性
- **可读性**：代码清晰易懂

### 2. 修复方案标注

```cpp
// 正确：使用智能指针自动管理内存
auto ptr = std::make_unique<int>(42);
```

```cpp
// 正确：释放后置空指针
delete ptr;
ptr = nullptr;
```

### 3. 最佳实践说明

```cpp
/**
 * 最佳实践：
 * 1. 优先使用智能指针
 * 2. 遵循 RAII 原则
 * 3. 释放后置空指针
 */
```

## 输出设计

### 1. 控制台输出

```
=== 悬空指针陷阱示例 ===

[错误示例 1] 函数返回局部变量指针
问题：返回局部变量地址，函数结束后变量被销毁
结果：未定义行为，可能崩溃

[正确示例 1] 使用智能指针
解决方案：使用 std::unique_ptr 自动管理内存
结果：安全，自动释放

=== 示例结束 ===
```

### 2. 输出格式

- 使用分隔线区分不同示例
- 标注错误和正确示例
- 说明问题和解决方案
- 展示运行结果

## 扩展设计

### 1. 添加新陷阱

1. 在对应目录创建新的 .cpp 文件
2. 更新目录的 CMakeLists.txt
3. 遵循代码结构规范
4. 添加详细注释

### 2. 添加新类别

1. 创建新的目录
2. 添加 CMakeLists.txt
3. 更新顶层 CMakeLists.txt
4. 更新 README.md

## 测试设计

### 1. 编译测试

- 所有示例必须可编译
- 无编译警告
- 支持主流编译器

### 2. 运行测试

- 错误示例注释掉危险代码
- 正确示例可正常运行
- 输出符合预期

### 3. 静态分析

- 通过 Clang-Tidy 检查
- 通过 Cppcheck 检查
- 无严重警告

## 文档设计

### 1. 代码内文档

- 文件头注释
- 函数注释
- 关键代码注释

### 2. 外部文档

- README.md：项目说明
- 学习路径文档
- 参考资源文档

## 工具集成

### 1. 静态分析

```cmake
# Clang-Tidy 集成
set(CMAKE_CXX_CLANG_TIDY "clang-tidy")
```

### 2. 动态分析

```bash
# AddressSanitizer
g++ -fsanitize=address -g program.cpp

# ThreadSanitizer
g++ -fsanitize=thread -g program.cpp
```

### 3. 代码格式化

```bash
# clang-format
clang-format -i *.cpp
```
