cmake_minimum_required(VERSION 3.16)
project(CppTricksAndTips
    VERSION 1.0.0
    DESCRIPTION "C++ 奇技淫巧集锦 - Advanced C++ Tricks and Tips Collection"
    LANGUAGES CXX
)

# =============================================================================
# 编译器和标准设置
# =============================================================================

# 要求 C++17 最低标准，部分示例需要 C++20
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 检测 C++20 支持
include(CheckCXXCompilerFlag)
check_cxx_compiler_flag("-std=c++20" COMPILER_SUPPORTS_CXX20)

# =============================================================================
# 编译选项
# =============================================================================

# 通用编译选项
add_compile_options(
    -Wall
    -Wextra
    -Wpedantic
    -Wno-unused-parameter
)

# Debug 模式选项 (不使用 -DDEBUG 宏，避免与枚举值冲突)
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")
set(CMAKE_CXX_FLAGS_RELEASE "-O2 -DNDEBUG")

# 默认 Debug 模式
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug)
endif()

# =============================================================================
# 查找线程库 (用于并发技巧)
# =============================================================================

find_package(Threads REQUIRED)

# =============================================================================
# 辅助函数：添加单文件示例
# =============================================================================

function(add_trick name source category)
    add_executable(${name} ${source})
    target_link_libraries(${name} PRIVATE Threads::Threads)
    target_include_directories(${name} PRIVATE ${CMAKE_SOURCE_DIR}/src)

    # 设置分类属性，便于 IDE 组织
    set_target_properties(${name} PROPERTIES
        FOLDER ${category}
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin/${category}"
    )

    # C++20 特殊处理
    set(_use_cxx20 FALSE)
    if(${ARGC} GREATER 3)
        if("${ARGV3}" STREQUAL "CXX20")
            set(_use_cxx20 TRUE)
        endif()
    endif()
    if(_use_cxx20)
        if(COMPILER_SUPPORTS_CXX20)
            set_target_properties(${name} PROPERTIES CXX_STANDARD 20)
            target_compile_options(${name} PRIVATE -std=c++20)
        else()
            message(WARNING "Compiler does not support C++20, skipping ${name}")
            set_target_properties(${name} PROPERTIES EXCLUDE_FROM_ALL TRUE)
        endif()
    endif()
endfunction()

# =============================================================================
# 1. 类型技巧 (Type Tricks)
# =============================================================================

message(STATUS "=== 类型技巧 (Type Tricks) ===")

add_trick(type_erasure      src/type_erasure.cpp      "01_Type_Tricks")
add_trick(type_traits       src/type_traits.cpp       "01_Type_Tricks")
add_trick(sfinae            src/sfinae.cpp            "01_Type_Tricks")
add_trick(crtp              src/crtp.cpp              "01_Type_Tricks")
add_trick(tag_dispatching   src/tag_dispatching.cpp   "01_Type_Tricks")

# =============================================================================
# 2. 模板技巧 (Template Tricks)
# =============================================================================

message(STATUS "=== 模板技巧 (Template Tricks) ===")

add_trick(variadic_templates         src/variadic_templates.cpp         "02_Template_Tricks")
add_trick(fold_expressions           src/fold_expressions.cpp           "02_Template_Tricks")
add_trick(template_metaprogramming   src/template_metaprogramming.cpp   "02_Template_Tricks")
add_trick(if_constexpr               src/if_constexpr.cpp               "02_Template_Tricks")

# C++20 概念需要编译器支持
if(COMPILER_SUPPORTS_CXX20)
    add_trick(concepts               src/concepts.cpp                   "02_Template_Tricks" "CXX20")
else()
    message(WARNING "Skipping 'concepts' - requires C++20 support")
endif()

# =============================================================================
# 3. 内存技巧 (Memory Tricks)
# =============================================================================

message(STATUS "=== 内存技巧 (Memory Tricks) ===")

add_trick(custom_allocator      src/custom_allocator.cpp      "03_Memory_Tricks")
add_trick(memory_pool           src/memory_pool.cpp           "03_Memory_Tricks")
add_trick(small_buffer_opt      src/small_buffer_opt.cpp      "03_Memory_Tricks")
add_trick(move_semantics        src/move_semantics.cpp        "03_Memory_Tricks")
add_trick(perfect_forwarding    src/perfect_forwarding.cpp    "03_Memory_Tricks")

# =============================================================================
# 4. 并发技巧 (Concurrency Tricks)
# =============================================================================

message(STATUS "=== 并发技巧 (Concurrency Tricks) ===")

add_trick(lock_free        src/lock_free.cpp        "04_Concurrency_Tricks")
target_link_libraries(lock_free PRIVATE atomic)
add_trick(atomic_ops       src/atomic_ops.cpp       "04_Concurrency_Tricks")
add_trick(thread_pool      src/thread_pool.cpp      "04_Concurrency_Tricks")
add_trick(async_patterns   src/async_patterns.cpp   "04_Concurrency_Tricks")
set_target_properties(async_patterns PROPERTIES CXX_STANDARD 20)

# C++20 协程需要编译器支持
if(COMPILER_SUPPORTS_CXX20)
    add_trick(coroutines   src/coroutines.cpp       "04_Concurrency_Tricks" "CXX20")
    # 协程可能需要额外的编译选项
    target_compile_options(coroutines PRIVATE -fcoroutines)
else()
    message(WARNING "Skipping 'coroutines' - requires C++20 support")
endif()

# =============================================================================
# 5. 优化技巧 (Optimization Tricks)
# =============================================================================

message(STATUS "=== 优化技巧 (Optimization Tricks) ===")

add_trick(compile_time       src/compile_time.cpp       "05_Optimization_Tricks")
set_target_properties(compile_time PROPERTIES CXX_STANDARD 20)
add_trick(inline_opt         src/inline_opt.cpp         "05_Optimization_Tricks")
add_trick(branch_prediction  src/branch_prediction.cpp  "05_Optimization_Tricks")
set_target_properties(branch_prediction PROPERTIES CXX_STANDARD 20)
add_trick(cache_friendly     src/cache_friendly.cpp     "05_Optimization_Tricks")
add_trick(simd               src/simd.cpp               "05_Optimization_Tricks")

# =============================================================================
# 6. 实用工具 (Utility Tools)
# =============================================================================

message(STATUS "=== 实用工具 (Utility Tools) ===")

add_trick(debug_tips       src/debug_tips.cpp       "06_Utility_Tools")
set_target_properties(debug_tips PROPERTIES CXX_STANDARD 20)
add_trick(logging          src/logging.cpp          "06_Utility_Tools")
add_trick(config_parser    src/config_parser.cpp    "06_Utility_Tools")
add_trick(serialization    src/serialization.cpp    "06_Utility_Tools")
add_trick(reflection       src/reflection.cpp       "06_Utility_Tools")
set_target_properties(reflection PROPERTIES CXX_STANDARD 20)

# =============================================================================
# 7. 代码风格 (Code Style)
# =============================================================================

message(STATUS "=== 代码风格 (Code Style) ===")

add_trick(modern_cpp          src/modern_cpp.cpp          "07_Code_Style")
add_trick(raii                src/raii.cpp                "07_Code_Style")
add_trick(exception_safety    src/exception_safety.cpp    "07_Code_Style")
add_trick(code_organization   src/code_organization.cpp   "07_Code_Style")

# =============================================================================
# 自定义目标：构建所有示例
# =============================================================================

# 收集所有目标
set(ALL_TRICKS
    # 类型技巧
    type_erasure type_traits sfinae crtp tag_dispatching
    # 模板技巧
    variadic_templates fold_expressions template_metaprogramming if_constexpr
    # 内存技巧
    custom_allocator memory_pool small_buffer_opt move_semantics perfect_forwarding
    # 并发技巧
    lock_free atomic_ops thread_pool async_patterns
    # 优化技巧
    compile_time inline_opt branch_prediction cache_friendly simd
    # 实用工具
    debug_tips logging config_parser serialization reflection
    # 代码风格
    modern_cpp raii exception_safety code_organization
)

# 如果支持 C++20，添加 C++20 特有的目标
if(COMPILER_SUPPORTS_CXX20)
    list(APPEND ALL_TRICKS concepts coroutines)
endif()

# 创建一个自定义目标来构建所有示例
add_custom_target(build_all_tricks
    DEPENDS ${ALL_TRICKS}
    COMMENT "Building all C++ tricks..."
)

# 创建一个自定义目标来运行所有示例
add_custom_target(run_all_tricks
    COMMENT "Running all C++ tricks..."
)

foreach(trick ${ALL_TRICKS})
    add_custom_command(
        TARGET run_all_tricks POST_BUILD
        COMMAND echo "========== Running ${trick} =========="
        COMMAND $<TARGET_FILE:${trick}> || true
        COMMENT "Running ${trick}..."
    )
endforeach()

# =============================================================================
# 打印配置信息
# =============================================================================

message(STATUS "")
message(STATUS "========================================")
message(STATUS "  C++ 奇技淫巧集锦 配置信息")
message(STATUS "========================================")
message(STATUS "  编译器:     ${CMAKE_CXX_COMPILER}")
message(STATUS "  C++ 标准:   ${CMAKE_CXX_STANDARD}")
message(STATUS "  C++20 支持: ${COMPILER_SUPPORTS_CXX20}")
message(STATUS "  构建类型:   ${CMAKE_BUILD_TYPE}")
message(STATUS "  输出目录:   ${CMAKE_BINARY_DIR}/bin/")
message(STATUS "========================================")
message(STATUS "")
message(STATUS "可用目标:")
message(STATUS "  make build_all_tricks  - 构建所有示例")
message(STATUS "  make run_all_tricks    - 运行所有示例")
message(STATUS "  make <target_name>     - 构建单个示例")
message(STATUS "")
