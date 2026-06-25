cmake_minimum_required(VERSION 3.16)

# ============================================================================
# CMake 基础示例
# 本文件展示 CMake 的基本用法，包括：
# - 项目声明
# - 目标创建（可执行文件、静态库、动态库）
# - 依赖管理
# - 安装规则
# ============================================================================

project(CMakeBasics
    VERSION 1.0.0
    DESCRIPTION "CMake 基础示例项目"
    LANGUAGES CXX
)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 输出编译信息
message(STATUS "CMake 版本: ${CMAKE_VERSION}")
message(STATUS "编译器: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "构建类型: ${CMAKE_BUILD_TYPE}")
message(STATUS "安装前缀: ${CMAKE_INSTALL_PREFIX}")

# ============================================================================
# 1. 创建静态库
# ============================================================================
add_library(math_utils STATIC
    src/math_utils.cpp
)

# 设置头文件搜索路径
target_include_directories(math_utils
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

# 设置编译选项
target_compile_features(math_utils PUBLIC cxx_std_17)

# ============================================================================
# 2. 创建动态库
# ============================================================================
add_library(string_utils SHARED
    src/string_utils.cpp
)

target_include_directories(string_utils
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_compile_features(string_utils PUBLIC cxx_std_17)

# 设置动态库版本
set_target_properties(string_utils PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION 1
    PUBLIC_HEADER "include/string_utils.h"
)

# ============================================================================
# 3. 创建可执行文件
# ============================================================================
add_executable(hello_world
    src/hello.cpp
)

target_link_libraries(hello_world
    PRIVATE
        math_utils
        string_utils
)

# ============================================================================
# 4. 安装规则
# ============================================================================
include(GNUInstallDirs)

# 安装库文件
install(TARGETS math_utils string_utils
    EXPORT CMakeBasicsTargets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

# 安装头文件
install(DIRECTORY include/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

# 安装可执行文件
install(TARGETS hello_world
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

# 导出目标配置
install(EXPORT CMakeBasicsTargets
    FILE CMakeBasicsTargets.cmake
    NAMESPACE CMakeBasics::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/CMakeBasics
)

# ============================================================================
# 5. 打包支持
# ============================================================================
include(CPack)
