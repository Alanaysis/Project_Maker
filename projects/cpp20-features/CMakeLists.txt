cmake_minimum_required(VERSION 3.16)
project(cpp20-features LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler-specific flags
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
elseif(MSVC)
    add_compile_options(/W4)
endif()

# Helper macro to add example targets
macro(add_example name)
    add_executable(${name} src/${name}.cpp)
    target_compile_features(${name} PRIVATE cxx_std_20)
endmacro()

# ============================================================
# 四大特性 (Big Four Features)
# ============================================================
add_example(01_concepts)
add_example(02_ranges)
add_example(03_coroutines)
# 04_modules 示例需要特殊处理（见 src/04_modules/ 目录）

# ============================================================
# 语言特性 (Language Features)
# ============================================================
add_example(05_spaceship_operator)
add_example(06_consteval_constinit)
add_example(07_aggregate_init)
add_example(08_range_for_init)
add_example(09_lambda_improvements)
add_example(10_no_unique_address)
add_example(11_using_enum)

# ============================================================
# 标准库特性 (Standard Library Features)
# ============================================================
add_example(12_std_format)
add_example(13_std_span)
add_example(14_std_jthread)
add_example(15_synchronization)
add_example(16_std_source_location)
add_example(17_std_stop_token)

# ============================================================
# 综合示例 (Comprehensive Examples)
# ============================================================
add_example(18_comprehensive)

# ============================================================
# CTest
# ============================================================
enable_testing()

# 添加运行测试 - 每个示例应该能正常运行且返回 0
foreach(target
    01_concepts 02_ranges 03_coroutines
    05_spaceship_operator 06_consteval_constinit
    07_aggregate_init 08_range_for_init
    09_lambda_improvements 10_no_unique_address 11_using_enum
    12_std_format 13_std_span 14_std_jthread
    15_synchronization 16_std_source_location 17_std_stop_token
    18_comprehensive)
    add_test(NAME ${target} COMMAND ${target})
endforeach()
