# 技术设计

## 设计原则

### 1. 模块化设计
- 每个库独立目录
- 独立的 CMakeLists.txt
- 清晰的依赖关系

### 2. 一致性设计
- 统一的目录结构
- 统一的命名规范
- 统一的注释风格

### 3. 可扩展设计
- 易于添加新库
- 灵活的构建配置
- 清晰的集成方式

## 文件组织

### 目录结构

```
cpp-third-party-libraries/
├── CMakeLists.txt              # 主构建文件
├── cmake/                      # CMake 模块
│   ├── FindXXX.cmake          # 查找模块
│   └── XXXConfig.cmake        # 配置模块
├── containers/                 # 容器库
│   ├── CMakeLists.txt
│   ├── boost_container/
│   │   ├── CMakeLists.txt
│   │   ├── flat_map_example.cpp
│   │   ├── stable_vector_example.cpp
│   │   └── README.md
│   ├── abseil/
│   │   ├── CMakeLists.txt
│   │   ├── flat_hash_map_example.cpp
│   │   └── README.md
│   ├── folly/
│   │   ├── CMakeLists.txt
│   │   ├── f14_hashmap_example.cpp
│   │   └── README.md
│   └── eastl/
│       ├── CMakeLists.txt
│       ├── fixed_vector_example.cpp
│       └── README.md
├── serialization/              # 序列化库
│   ├── CMakeLists.txt
│   ├── protobuf/
│   │   ├── CMakeLists.txt
│   │   ├── proto/
│   │   │   └── message.proto
│   │   ├── basic_example.cpp
│   │   └── README.md
│   ├── flatbuffers/
│   │   ├── CMakeLists.txt
│   │   ├── schemas/
│   │   │   └── message.fbs
│   │   ├── basic_example.cpp
│   │   └── README.md
│   ├── json/
│   │   ├── CMakeLists.txt
│   │   ├── nlohmann_example.cpp
│   │   ├── rapidjson_example.cpp
│   │   └── README.md
│   └── ...
├── networking/                 # 网络库
│   ├── CMakeLists.txt
│   ├── boost_asio/
│   │   ├── CMakeLists.txt
│   │   ├── tcp_server_example.cpp
│   │   ├── tcp_client_example.cpp
│   │   └── README.md
│   ├── cpp_httplib/
│   │   ├── CMakeLists.txt
│   │   ├── server_example.cpp
│   │   ├── client_example.cpp
│   │   └── README.md
│   └── ...
├── concurrency/                # 并发库
│   ├── CMakeLists.txt
│   ├── tbb/
│   │   ├── CMakeLists.txt
│   │   ├── parallel_for_example.cpp
│   │   ├── parallel_reduce_example.cpp
│   │   └── README.md
│   └── ...
├── testing/                    # 测试库
│   ├── CMakeLists.txt
│   ├── gtest/
│   │   ├── CMakeLists.txt
│   │   ├── basic_test.cpp
│   │   ├── fixture_test.cpp
│   │   └── README.md
│   └── ...
├── logging/                    # 日志库
│   ├── CMakeLists.txt
│   ├── spdlog/
│   │   ├── CMakeLists.txt
│   │   ├── basic_example.cpp
│   │   ├── async_example.cpp
│   │   └── README.md
│   └── ...
├── math/                       # 数学库
│   ├── CMakeLists.txt
│   ├── eigen/
│   │   ├── CMakeLists.txt
│   │   ├── matrix_example.cpp
│   │   ├── linear_algebra_example.cpp
│   │   └── README.md
│   └── ...
├── graphics/                   # 图形库
│   ├── CMakeLists.txt
│   ├── imgui/
│   │   ├── CMakeLists.txt
│   │   ├── basic_window.cpp
│   │   └── README.md
│   └── ...
├── utils/                      # 工具库
│   ├── CMakeLists.txt
│   ├── boost/
│   │   ├── CMakeLists.txt
│   │   ├── string_algo_example.cpp
│   │   ├── filesystem_example.cpp
│   │   └── README.md
│   └── ...
└── build/                      # 构建工具
    ├── CMakeLists.txt
    ├── vcpkg/
    │   ├── vcpkg.json
    │   ├── CMakeLists.txt
    │   └── README.md
    ├── conan/
    │   ├── conanfile.txt
    │   ├── CMakeLists.txt
    │   └── README.md
    └── fetch_content/
        ├── CMakeLists.txt
        └── README.md
```

### 文件命名规范

#### 源文件
- 使用小写字母和下划线
- 格式：`<功能>_example.cpp` 或 `<功能>_test.cpp`
- 示例：`flat_map_example.cpp`, `tcp_server_example.cpp`

#### 头文件
- 使用小写字母和下划线
- 格式：`<库名>_<功能>.h`
- 示例：`boost_container_utils.h`

#### CMake 文件
- 主文件：`CMakeLists.txt`
- 模块文件：`Find<库名>.cmake`
- 配置文件：`<库名>Config.cmake`

#### 文档文件
- README.md - 每个目录的说明文档
- 使用中文撰写

## 示例设计

### 示例结构

每个示例文件遵循以下结构：

```cpp
/**
 * @file <文件名>.cpp
 * @brief <简短描述>
 * @details <详细描述>
 * @author <作者>
 * @date <日期>
 */

#include <iostream>
#include <vector>
#include <string>

// 库头文件
#include <库头文件>

/**
 * @brief 基础功能示例
 * @details 展示库的基本使用方法
 */
void basic_example() {
    std::cout << "=== 基础功能示例 ===" << std::endl;
    
    // 示例代码
    // 详细注释说明每一步的作用
    
    std::cout << std::endl;
}

/**
 * @brief 高级功能示例
 * @details 展示库的高级特性
 */
void advanced_example() {
    std::cout << "=== 高级功能示例 ===" << std::endl;
    
    // 示例代码
    
    std::cout << std::endl;
}

/**
 * @brief 实际应用场景示例
 * @details 展示在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;
    
    // 示例代码
    
    std::cout << std::endl;
}

int main() {
    std::cout << "=== <库名> 示例 ===" << std::endl;
    std::cout << std::endl;
    
    basic_example();
    advanced_example();
    real_world_example();
    
    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
```

### 示例类型

#### 1. 基础示例
- 展示库的基本功能
- 简单易懂
- 适合初学者

#### 2. 高级示例
- 展示库的高级特性
- 性能优化
- 最佳实践

#### 3. 实际应用示例
- 解决实际问题
- 完整的工作流程
- 生产环境考虑

### 注释规范

#### 文件头注释
```cpp
/**
 * @file 文件名.cpp
 * @brief 简短描述
 * @details 详细描述
 * @author 作者
 * @date 日期
 */
```

#### 函数注释
```cpp
/**
 * @brief 函数功能简述
 * @details 函数功能详述
 * @param param1 参数1说明
 * @param param2 参数2说明
 * @return 返回值说明
 * @throws 异常说明
 * @note 注意事项
 * @see 相关函数
 */
```

#### 代码注释
```cpp
// 单行注释：说明代码块的功能

/*
 * 多行注释：
 * 说明复杂的逻辑
 * 或算法原理
 */
```

## CMake 设计

### 主 CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.15)
project(CppThirdPartyLibraries VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 选项
option(BUILD_CONTAINERS "Build container examples" ON)
option(BUILD_SERIALIZATION "Build serialization examples" ON)
option(BUILD_NETWORKING "Build networking examples" ON)
option(BUILD_CONCURRENCY "Build concurrency examples" ON)
option(BUILD_TESTING "Build testing examples" ON)
option(BUILD_LOGGING "Build logging examples" ON)
option(BUILD_MATH "Build math examples" ON)
option(BUILD_GRAPHICS "Build graphics examples" OFF)
option(BUILD_UTILS "Build utils examples" ON)
option(BUILD_BUILD_TOOLS "Build tool examples" ON)

# 子目录
if(BUILD_CONTAINERS)
    add_subdirectory(containers)
endif()

if(BUILD_SERIALIZATION)
    add_subdirectory(serialization)
endif()

# ... 其他子目录
```

### 子目录 CMakeLists.txt

```cmake
# containers/CMakeLists.txt

add_subdirectory(boost_container)
add_subdirectory(abseil)
add_subdirectory(folly)
add_subdirectory(eastl)
```

### 示例 CMakeLists.txt

```cmake
# containers/boost_container/CMakeLists.txt

# 查找依赖
find_package(Boost REQUIRED COMPONENTS container)

# 示例目标
add_executable(boost_container_flat_map flat_map_example.cpp)
target_link_libraries(boost_container_flat_map PRIVATE Boost::container)

add_executable(boost_container_stable_vector stable_vector_example.cpp)
target_link_libraries(boost_container_stable_vector PRIVATE Boost::container)
```

## 依赖管理

### 包管理器支持

#### vcpkg
```json
{
  "name": "cpp-third-party-libraries",
  "version": "1.0.0",
  "dependencies": [
    "boost-container",
    "boost-asio",
    "protobuf",
    "nlohmann-json",
    "spdlog",
    "eigen3",
    "gtest"
  ]
}
```

#### Conan
```ini
[requires]
boost/1.83.0
protobuf/3.21.12
nlohmann_json/3.11.2
spdlog/1.13.0
eigen/3.4.0
gtest/1.14.0

[generators]
CMakeDeps
CMakeToolchain
```

### FetchContent

```cmake
include(FetchContent)

FetchContent_Declare(
  nlohmann_json
  GIT_REPOSITORY https://github.com/nlohmann/json.git
  GIT_TAG v3.11.2
)

FetchContent_MakeAvailable(nlohmann_json)
```

## 错误处理

### 编译时检查

```cmake
# 检查 C++ 标准
if(NOT CMAKE_CXX_STANDARD GREATER_EQUAL 17)
    message(FATAL_ERROR "C++17 or higher is required")
endif()

# 检查编译器
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    if(CMAKE_CXX_COMPILER_VERSION LESS 9.0)
        message(FATAL_ERROR "GCC 9.0 or higher is required")
    endif()
endif()
```

### 运行时检查

```cpp
#include <stdexcept>
#include <iostream>

int main() {
    try {
        // 示例代码
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}
```

## 性能考虑

### 编译时优化

```cmake
# 优化级别
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_compile_options(-O2 -DNDEBUG)
endif()

# 预编译头
target_precompile_headers(example PRIVATE
    <iostream>
    <vector>
    <string>
)
```

### 运行时优化

```cpp
// 使用移动语义
std::vector<int> create_vector() {
    std::vector<int> v = {1, 2, 3, 4, 5};
    return std::move(v);  // 或依赖 RVO
}

// 避免不必要的拷贝
void process(const std::vector<int>& v) {
    // 使用 const 引用
}
```

## 测试策略

### 单元测试

```cpp
#include <gtest/gtest.h>

TEST(ExampleTest, BasicFunctionality) {
    // 测试代码
    EXPECT_EQ(1 + 1, 2);
}
```

### 集成测试

```cpp
#include <gtest/gtest.h>

TEST(IntegrationTest, EndToEnd) {
    // 集成测试代码
}
```

## 文档生成

### Doxygen 配置

```
PROJECT_NAME = "C++ Third Party Libraries"
OUTPUT_DIRECTORY = docs
INPUT = .
RECURSIVE = YES
EXTRACT_ALL = YES
GENERATE_HTML = YES
GENERATE_LATEX = NO
```

## 总结

本设计文档定义了项目的：
1. 文件组织结构
2. 命名规范
3. 示例设计模式
4. CMake 配置策略
5. 依赖管理方式
6. 错误处理机制
7. 性能优化策略
8. 测试策略

遵循这些设计原则，可以创建一个高质量、易维护、易扩展的 C++ 三方库介绍项目。