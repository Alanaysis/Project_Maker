cmake_minimum_required(VERSION 3.20)

# ============================================================================
# CMake 高级特性示例
# 本文件展示 CMake 的高级用法，包括：
# - Generator Expressions
# - Custom Commands
# - External Projects
# - FetchContent
# - 工具链文件
# ============================================================================

project(CMakeAdvanced
    VERSION 1.0.0
    DESCRIPTION "CMake 高级特性示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. Generator Expressions 示例
# ============================================================================
add_executable(generator_expr
    src/generator_expr.cpp
)

# 使用 Generator Expressions 设置编译定义
target_compile_definitions(generator_expr PRIVATE
    # 根据构建类型设置不同的宏
    $<$<CONFIG:Debug>:BUILD_TYPE="Debug">
    $<$<CONFIG:Release>:BUILD_TYPE="Release">
    $<$<CONFIG:RelWithDebInfo>:BUILD_TYPE="RelWithDebInfo">

    # 根据平台设置不同的宏
    $<$<PLATFORM_ID:Windows>:PLATFORM="Windows">
    $<$<PLATFORM_ID:Linux>:PLATFORM="Linux">
    $<$<PLATFORM_ID:Darwin>:PLATFORM="macOS">

    # 根据编译器设置不同的宏
    $<$<CXX_COMPILER_ID:GNU>:COMPILER="GCC">
    $<$<CXX_COMPILER_ID:Clang>:COMPILER="Clang">
    $<$<CXX_COMPILER_ID:MSVC>:COMPILER="MSVC">
)

# 使用 Generator Expressions 设置编译选项
target_compile_options(generator_expr PRIVATE
    # GCC/Clang 特定选项
    $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall -Wextra -Wpedantic>
    # MSVC 特定选项
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /WX>
    # Debug 模式启用调试信息
    $<$<CONFIG:Debug>:-g -O0>
    # Release 模式启用优化
    $<$<CONFIG:Release>:-O2>
)

# ============================================================================
# 2. Custom Commands 示例
# ============================================================================

# 生成版本信息头文件
set(VERSION_HEADER "${CMAKE_CURRENT_BINARY_DIR}/version_info.h")

add_custom_command(
    OUTPUT ${VERSION_HEADER}
    COMMAND ${CMAKE_COMMAND} -E echo "// Auto-generated version info" > ${VERSION_HEADER}
    COMMAND ${CMAKE_COMMAND} -E echo "#ifndef VERSION_INFO_H" >> ${VERSION_HEADER}
    COMMAND ${CMAKE_COMMAND} -E echo "#define VERSION_INFO_H" >> ${VERSION_HEADER}
    COMMAND ${CMAKE_COMMAND} -E echo "#define PROJECT_NAME \"${PROJECT_NAME}\"" >> ${VERSION_HEADER}
    COMMAND ${CMAKE_COMMAND} -E echo "#define PROJECT_VERSION \"${PROJECT_VERSION}\"" >> ${VERSION_HEADER}
    COMMAND ${CMAKE_COMMAND} -E echo "#define BUILD_DATE \"__DATE__\"" >> ${VERSION_HEADER}
    COMMAND ${CMAKE_COMMAND} -E echo "#endif" >> ${VERSION_HEADER}
    COMMENT "Generating version_info.h"
    VERBATIM
)

add_custom_target(generate_version DEPENDS ${VERSION_HEADER})

# 创建使用版本信息的可执行文件
add_executable(custom_command_demo
    src/custom_command_demo.cpp
    ${VERSION_HEADER}
)

add_dependencies(custom_command_demo generate_version)
target_include_directories(custom_command_demo PRIVATE ${CMAKE_CURRENT_BINARY_DIR})

# 自定义目标：代码格式化
find_program(CLANG_FORMAT_PROGRAM clang-format)
if(CLANG_FORMAT_PROGRAM)
    file(GLOB_RECURSE ALL_SOURCE_FILES
        ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp
        ${CMAKE_CURRENT_SOURCE_DIR}/src/*.h
    )

    add_custom_target(format
        COMMAND ${CLANG_FORMAT_PROGRAM} -i ${ALL_SOURCE_FILES}
        COMMENT "Formatting source files with clang-format"
    )
endif()

# 自定义目标：代码统计
add_custom_target(loc
    COMMAND ${CMAKE_COMMAND} -E echo "Lines of code:"
    COMMAND find ${CMAKE_CURRENT_SOURCE_DIR}/src -name "*.cpp" -o -name "*.h" | xargs wc -l
    COMMENT "Counting lines of code"
)

# ============================================================================
# 3. FetchContent 示例
# ============================================================================
include(FetchContent)

# 拉取 fmt 库
FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 10.1.1
)

# 拉取 spdlog 库（依赖 fmt）
FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG v1.12.0
)

# 设置 FetchContent 选项
set(FMT_DOC OFF CACHE BOOL "" FORCE)
set(FMT_TEST OFF CACHE BOOL "" FORCE)
set(SPDLOG_BUILD_EXAMPLE OFF CACHE BOOL "" FORCE)
set(SPDLOG_BUILD_TESTS OFF CACHE BOOL "" FORCE)

# 拉取并构建依赖
FetchContent_MakeAvailable(fmt spdlog)

# 使用 FetchContent 获取的库
add_executable(fetchcontent_demo
    src/fetchcontent_demo.cpp
)

target_link_libraries(fetchcontent_demo
    PRIVATE
        fmt::fmt
        spdlog::spdlog
)

# ============================================================================
# 4. External Project 示例（作为对比）
# ============================================================================
include(ExternalProject)

# 注意：ExternalProject 在构建时下载，不推荐在主项目中使用
# 这里仅作为演示，实际项目建议使用 FetchContent

# ExternalProject_Add(
#     external_json
#     GIT_REPOSITORY https://github.com/nlohmann/json.git
#     GIT_TAG v3.11.2
#     CMAKE_ARGS -DCMAKE_INSTALL_PREFIX=${CMAKE_BINARY_DIR}/external
#     -DJSON_BuildTests=OFF
# )

# ============================================================================
# 5. 构建信息输出
# ============================================================================
message(STATUS "")
message(STATUS "=== CMake 高级特性示例 ===")
message(STATUS "项目名称: ${PROJECT_NAME}")
message(STATUS "项目版本: ${PROJECT_VERSION}")
message(STATUS "CMake 版本: ${CMAKE_VERSION}")
message(STATUS "构建类型: ${CMAKE_BUILD_TYPE}")
message(STATUS "编译器: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "Generator: ${CMAKE_GENERATOR}")
message(STATUS "Source Dir: ${CMAKE_CURRENT_SOURCE_DIR}")
message(STATUS "Binary Dir: ${CMAKE_CURRENT_BINARY_DIR}")
message(STATUS "")
