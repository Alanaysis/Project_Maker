cmake_minimum_required(VERSION 3.16)

# ============================================================================
# Sanitizers 动态分析示例
# 本文件展示如何使用各种 Sanitizer 进行动态分析
#
# Sanitizers:
# - AddressSanitizer (ASan): 内存错误检测
# - ThreadSanitizer (TSan): 数据竞争检测
# - MemorySanitizer (MSan): 未初始化内存读取
# - UndefinedBehaviorSanitizer (UBSan): 未定义行为检测
# ============================================================================

project(SanitizersExample
    VERSION 1.0.0
    DESCRIPTION "Sanitizers 动态分析示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. Sanitizer 选项
# ============================================================================
option(ENABLE_ASAN "Enable AddressSanitizer" OFF)
option(ENABLE_TSAN "Enable ThreadSanitizer" OFF)
option(ENABLE_MSAN "Enable MemorySanitizer" OFF)
option(ENABLE_UBSAN "Enable UndefinedBehaviorSanitizer" OFF)

# ============================================================================
# 2. 辅助函数：添加 Sanitizer 选项
# ============================================================================
function(add_sanitizer_flags target)
    if(ENABLE_ASAN)
        target_compile_options(${target} PRIVATE -fsanitize=address -fno-omit-frame-pointer)
        target_link_options(${target} PRIVATE -fsanitize=address)
        message(STATUS "AddressSanitizer enabled for ${target}")
    endif()

    if(ENABLE_TSAN)
        target_compile_options(${target} PRIVATE -fsanitize=thread)
        target_link_options(${target} PRIVATE -fsanitize=thread)
        message(STATUS "ThreadSanitizer enabled for ${target}")
    endif()

    if(ENABLE_MSAN)
        target_compile_options(${target} PRIVATE -fsanitize=memory -fno-omit-frame-pointer)
        target_link_options(${target} PRIVATE -fsanitize=memory)
        message(STATUS "MemorySanitizer enabled for ${target}")
    endif()

    if(ENABLE_UBSAN)
        target_compile_options(${target} PRIVATE -fsanitize=undefined)
        target_link_options(${target} PRIVATE -fsanitize=undefined)
        message(STATUS "UndefinedBehaviorSanitizer enabled for ${target}")
    endif()
endfunction()

# ============================================================================
# 3. 创建示例程序
# ============================================================================

# AddressSanitizer 示例
add_executable(asan_demo src/asan_demo.cpp)
add_sanitizer_flags(asan_demo)

# ThreadSanitizer 示例
add_executable(tsan_demo src/tsan_demo.cpp)
add_sanitizer_flags(tsan_demo)
target_link_libraries(tsan_demo PRIVATE pthread)

# UndefinedBehaviorSanitizer 示例
add_executable(ubsan_demo src/ubsan_demo.cpp)
add_sanitizer_flags(ubsan_demo)
