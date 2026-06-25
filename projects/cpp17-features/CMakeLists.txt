cmake_minimum_required(VERSION 3.8)
project(cpp17_features LANGUAGES CXX)

# C++17 标准设置
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
option(ENABLE_PARALLEL "Enable parallel algorithms support (requires TBB)" OFF)
option(ENABLE_ASAN "Enable AddressSanitizer" OFF)
option(ENABLE_UBSAN "Enable UndefinedBehaviorSanitizer" OFF)

# 编译器特定设置
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
elseif(MSVC)
    add_compile_options(/W4)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

# 消毒器设置
if(ENABLE_ASAN)
    add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address)
endif()

if(ENABLE_UBSAN)
    add_compile_options(-fsanitize=undefined)
    add_link_options(-fsanitize=undefined)
endif()

# 查找 TBB（用于并行算法）
if(ENABLE_PARALLEL)
    find_package(TBB QUIET)
    if(TBB_FOUND)
        message(STATUS "TBB found, enabling parallel algorithms")
    else()
        message(WARNING "TBB not found, parallel algorithms may not work")
    endif()
endif()

# 函数：添加示例可执行文件
function(add_example name source)
    add_executable(${name} ${source})

    # 链接文件系统库（GCC 7/8 需要）
    if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" AND CMAKE_CXX_COMPILER_VERSION VERSION_LESS "9.0")
        target_link_libraries(${name} PRIVATE stdc++fs)
    endif()

    # 链接 TBB（如果启用并行）
    if(ENABLE_PARALLEL AND TBB_FOUND)
        target_link_libraries(${name} PRIVATE TBB::tbb)
    endif()
endfunction()

# 示例源文件列表
set(EXAMPLE_SOURCES
    optional_example
    variant_example
    any_example
    string_view_example
    structured_bindings
    if_constexpr_example
    fold_expressions
    inline_variables
    nested_namespaces
    attributes_example
    filesystem_example
    apply_example
    invoke_example
    gcd_lcm_example
    parallel_algorithms
    shared_mutex_example
    scoped_lock_example
    ctad_example
    auto_extensions
)

# 添加独立示例可执行文件
foreach(example ${EXAMPLE_SOURCES})
    add_example(${example} ${example}.cpp)
endforeach()

# 测试支持
enable_testing()

# 添加测试
foreach(example ${EXAMPLE_SOURCES})
    add_test(NAME ${example} COMMAND ${example})
endforeach()

# 安装规则
install(TARGETS ${EXAMPLE_SOURCES} DESTINATION bin)
install(FILES README.md DESTINATION share/doc/cpp17_features)
