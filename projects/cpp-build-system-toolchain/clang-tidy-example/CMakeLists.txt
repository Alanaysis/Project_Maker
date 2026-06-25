cmake_minimum_required(VERSION 3.16)

# ============================================================================
# Clang-Tidy 静态分析示例
# 本文件展示如何集成 Clang-Tidy 进行代码静态分析
# ============================================================================

project(ClangTidyExample
    VERSION 1.0.0
    DESCRIPTION "Clang-Tidy 静态分析示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. 全局启用 Clang-Tidy
# ============================================================================
# 方法1: 在配置时启用
set(CMAKE_CXX_CLANG_TIDY
    clang-tidy;
    --checks=*,-fuchsia-*,-google-readability-todo,-llvm-header-guard;
    --warnings-as-errors=*;
)

# ============================================================================
# 2. 创建目标
# ============================================================================
add_executable(clang_tidy_demo src/clang_tidy_demo.cpp)

# 方法2: 针对特定目标启用
# set_target_properties(clang_tidy_demo PROPERTIES
#     CXX_CLANG_TIDY "clang-tidy;--checks=*"
# )

# ============================================================================
# 3. 自定义目标运行 clang-tidy
# ============================================================================
find_program(CLANG_TIDY clang-tidy)

if(CLANG_TIDY)
    file(GLOB_RECURSE SOURCE_FILES
        ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp
    )

    add_custom_target(run-clang-tidy
        COMMAND ${CLANG_TIDY}
            --checks=*,-fuchsia-*,-google-readability-todo
            -p ${CMAKE_BINARY_DIR}
            ${SOURCE_FILES}
        COMMENT "Running clang-tidy on all source files"
    )
endif()

# ============================================================================
# 4. 生成 compile_commands.json
# ============================================================================
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
