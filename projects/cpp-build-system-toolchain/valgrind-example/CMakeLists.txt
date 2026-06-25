cmake_minimum_required(VERSION 3.16)

# ============================================================================
# Valgrind 动态分析示例
# 本文件展示如何使用 Valgrind 进行动态分析
#
# Valgrind 工具:
# - memcheck: 内存错误检测
# - cachegrind: 缓存分析
# - callgrind: 函数调用分析
# - helgrind: 线程错误检测
# - drd: 线程错误检测
# ============================================================================

project(ValgrindExample
    VERSION 1.0.0
    DESCRIPTION "Valgrind 动态分析示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. 创建示例程序
# ============================================================================
add_executable(valgrind_demo src/valgrind_demo.cpp)

# Debug 构建以获得更好的 Valgrind 输出
target_compile_options(valgrind_demo PRIVATE
    $<$<CONFIG:Debug>:-g -O0>
)

# ============================================================================
# 2. Valgrind CTest 集成
# ============================================================================
find_program(VALGRIND valgrind)

if(VALGRIND)
    # 使用 Valgrind 运行测试
    set(MEMORYCHECK_COMMAND ${VALGRIND})
    set(MEMORYCHECK_COMMAND_OPTIONS
        "--leak-check=full --show-leak-kinds=all --track-origins=yes --error-exitcode=1"
    )

    # 包含 CTest 的 Valgrind 支持
    include(CTest)

    add_test(NAME valgrind_test COMMAND valgrind_demo)
    set_tests_properties(valgrind_test PROPERTIES
        TIMEOUT 30
    )

    # 自定义 Valgrind 目标
    add_custom_target(valgrind
        COMMAND ${VALGRIND}
            --leak-check=full
            --show-leak-kinds=all
            --track-origins=yes
            --verbose
            $<TARGET_FILE:valgrind_demo>
        COMMENT "Running Valgrind memcheck"
    )

    # 缓存分析
    add_custom_target(cachegrind
        COMMAND ${VALGRIND}
            --tool=cachegrind
            $<TARGET_FILE:valgrind_demo>
        COMMENT "Running Valgrind cachegrind"
    )

    # 函数调用分析
    add_custom_target(callgrind
        COMMAND ${VALGRIND}
            --tool=callgrind
            $<TARGET_FILE:valgrind_demo>
        COMMENT "Running Valgrind callgrind"
    )
endif()
