cmake_minimum_required(VERSION 3.16)

# ============================================================================
# 模糊测试 (Fuzzing) 示例
# 本文件展示如何使用 LibFuzzer 进行模糊测试
#
# 使用方法:
#   cmake -B build -DCMAKE_CXX_COMPILER=clang++
#   cmake --build build
#   ./fuzz_target corpus/
#
# 注意: 需要使用 Clang 编译器
# ============================================================================

project(FuzzingExample
    VERSION 1.0.0
    DESCRIPTION "模糊测试示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. 检查编译器
# ============================================================================
if(NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    message(WARNING "Fuzzing requires Clang compiler")
endif()

# ============================================================================
# 2. 创建被测试的库
# ============================================================================
add_library(parser STATIC
    src/parser.cpp
)
target_include_directories(parser PUBLIC include)

# ============================================================================
# 3. 创建模糊测试目标
# ============================================================================
add_executable(fuzz_target
    fuzz/fuzz_target.cpp
)

target_link_libraries(fuzz_target
    PRIVATE
        parser
)

target_compile_options(fuzz_target PRIVATE
    -fsanitize=fuzzer,address,undefined
    -fno-omit-frame-pointer
)

target_link_options(fuzz_target PRIVATE
    -fsanitize=fuzzer,address,undefined
)

# ============================================================================
# 4. 创建语料库目录
# ============================================================================
file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/corpus)

# 添加初始语料库
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/corpus/sample1.txt "hello world")
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/corpus/sample2.txt "123+456")
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/corpus/sample3.txt "(a+b)*c")

# ============================================================================
# 5. 自定义运行目标
# ============================================================================
add_custom_target(run_fuzzer
    COMMAND ${CMAKE_CURRENT_BINARY_DIR}/fuzz_target
        ${CMAKE_CURRENT_BINARY_DIR}/corpus
        -max_len=1024
        -max_total_time=60
    COMMENT "Running fuzzer for 60 seconds"
)

# ============================================================================
# 6. 普通测试
# ============================================================================
add_executable(parser_tests
    tests/test_parser.cpp
)

target_link_libraries(parser_tests PRIVATE parser)

enable_testing()
add_test(NAME parser_tests COMMAND parser_tests)
