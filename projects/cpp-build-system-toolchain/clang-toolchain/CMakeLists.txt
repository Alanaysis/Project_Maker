cmake_minimum_required(VERSION 3.16)

# ============================================================================
# Clang 工具链示例
# 本文件展示 Clang 编译器的选项和特性
# ============================================================================

project(ClangToolchain
    VERSION 1.0.0
    DESCRIPTION "Clang 工具链示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. Clang 特定编译选项
# ============================================================================
add_executable(clang_demo src/clang_demo.cpp)

target_compile_options(clang_demo PRIVATE
    # 基本警告
    -Wall
    -Wextra
    -Wpedantic

    # Clang 特有警告
    -Weverything
    -Wno-c++98-compat
    -Wno-c++98-compat-pedantic
    -Wno-padded
    -Wno-exit-time-destructors
    -Wno-global-constructors
)

# ============================================================================
# 2. Clang 静态分析
# ============================================================================
option(ENABLE_CLANG_STATIC_ANALYSIS "Enable Clang Static Analysis" OFF)

if(ENABLE_CLANG_STATIC_ANALYSIS)
    set(CMAKE_CXX_CLANG_TIDY
        clang-tidy;
        --checks=*,-fuchsia-*,-google-*,-llvm-*,-abseil-*
    )
endif()

# ============================================================================
# 3. Clang 格式化
# ============================================================================
find_program(CLANG_FORMAT clang-format)
if(CLANG_FORMAT)
    file(GLOB_RECURSE ALL_SOURCE_FILES
        ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp
        ${CMAKE_CURRENT_SOURCE_DIR}/src/*.h
    )

    add_custom_target(clang-format
        COMMAND ${CLANG_FORMAT} -i ${ALL_SOURCE_FILES}
        COMMENT "Running clang-format"
    )
endif()

# ============================================================================
# 4. Clang Static Analyzer
# =============================================================================
find_program(CLANG_SCAN_BUILD scan-build)
if(CLANG_SCAN_BUILD)
    add_custom_target(scan-build
        COMMAND ${CLANG_SCAN_BUILD} cmake --build ${CMAKE_BINARY_DIR}
        COMMENT "Running Clang Static Analyzer"
    )
endif()

# ============================================================================
# 5. Link Time Optimization
# ============================================================================
option(ENABLE_LTO "Enable Link Time Optimization" OFF)

if(ENABLE_LTO)
    set_property(TARGET clang_demo PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)
endif()
