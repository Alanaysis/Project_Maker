# 03_DESIGN.md - 技术设计

## 文件组织

### 项目结构

```
cpp20-features/
├── CMakeLists.txt              # 构建配置
├── README.md                   # 项目文档
├── 01_RESEARCH.md              # 市场调研
├── 02_REQUIREMENTS.md          # 需求分析
├── 03_DESIGN.md                # 技术设计（本文件）
├── 04_PRODUCT.md               # 产品思考
├── 05_DEVELOPMENT.md           # 开发手册
└── src/
    ├── 01_concepts.cpp         # 四大特性：概念
    ├── 02_ranges.cpp           # 四大特性：范围
    ├── 03_coroutines.cpp       # 四大特性：协程
    ├── 05_spaceship_operator.cpp   # 语言特性：三向比较
    ├── 06_consteval_constinit.cpp  # 语言特性：编译期计算
    ├── 07_aggregate_init.cpp       # 语言特性：聚合初始化
    ├── 08_range_for_init.cpp       # 语言特性：范围for初始化
    ├── 09_lambda_improvements.cpp  # 语言特性：Lambda改进
    ├── 10_no_unique_address.cpp    # 语言特性：空成员优化
    ├── 11_using_enum.cpp           # 语言特性：using enum
    ├── 12_std_format.cpp           # 标准库：格式化
    ├── 13_std_span.cpp             # 标准库：span
    ├── 14_std_jthread.cpp          # 标准库：jthread
    ├── 15_synchronization.cpp      # 标准库：同步原语
    ├── 16_std_source_location.cpp  # 标准库：source_location
    ├── 17_std_stop_token.cpp       # 标准库：stop_token
    └── 18_comprehensive.cpp        # 综合示例
```

### 编号规则

- 01-04: 四大核心特性
- 05-11: 语言特性
- 12-17: 标准库特性
- 18: 综合示例
- 04 (Modules) 跳过：编译器支持不一致，需要特殊构建配置

---

## 示例设计

### 每个示例的结构

```cpp
/**
 * 文件名.cpp - 特性名称
 *
 * 简要描述
 *
 * 核心要点：
 * 1. 要点一
 * 2. 要点二
 * 3. 要点三
 */

#include <必要的头文件>

// ============================================================
// 1. 基础用法
// ============================================================

void basic_usage() {
    // 代码 + 注释
}

// ============================================================
// 2. 进阶用法
// ============================================================

void advanced_usage() {
    // 代码 + 注释
}

// ============================================================
// 3. 实际应用
// ============================================================

void practical_example() {
    // 代码 + 注释
}

int main() {
    std::cout << "=== 特性名称示例 ===\n\n";
    
    basic_usage();
    advanced_usage();
    practical_example();
    
    std::cout << "\n=== 示例完成 ===\n";
    return 0;
}
```

### 设计原则

1. **独立性**：每个文件可独立编译运行，不依赖其他示例
2. **渐进性**：从基础到进阶，逐步深入
3. **实用性**：包含实际应用场景，不只是语法演示
4. **可读性**：详细注释，中文说明，代码清晰

---

## CMake 设计

### 目标配置

```cmake
# 每个示例一个可执行目标
macro(add_example name)
    add_executable(${name} src/${name}.cpp)
    target_compile_features(${name} PRIVATE cxx_std_20)
endmacro()

# CTest 测试覆盖
enable_testing()
foreach(target ...)
    add_test(NAME ${target} COMMAND ${target})
endforeach()
```

### 编译选项

- `-Wall -Wextra -Wpedantic`：严格警告
- `CMAKE_CXX_STANDARD 20`：C++20 标准
- `CMAKE_CXX_EXTENSIONS OFF`：禁用编译器扩展

---

## 数据流设计

### 综合示例架构

```
数据输入 (vector/span)
    ↓
概念约束过滤 (Concepts + filter)
    ↓
范围管道处理 (Ranges + transform)
    ↓
格式化输出 (std::format)
    ↓
日志记录 (source_location)
```

### 并发示例架构

```
主线程
    ├── jthread + stop_token (可取消任务)
    ├── latch (一次性同步)
    ├── barrier (可重复同步)
    └── semaphore (资源控制)
```
