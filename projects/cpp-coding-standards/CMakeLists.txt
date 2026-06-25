cmake_minimum_required(VERSION 3.16)
project(cpp-coding-standards
    VERSION 1.0.0
    DESCRIPTION "C++ 代码规范和风格示例项目"
    LANGUAGES CXX
)

# C++ 标准设置
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
add_compile_options(
    -Wall
    -Wextra
    -Wpedantic
    -Wshadow
    -Wnon-virtual-dtor
    -Wold-style-cast
    -Wcast-align
    -Wunused
    -Woverloaded-virtual
    -Wconversion
    -Wsign-conversion
    -Wnull-dereference
    -Wdouble-promotion
    -Wformat=2
    -Wimplicit-fallthrough
    -Wmisleading-indentation
    -Wduplicated-cond
    -Wduplicated-branches
    -Wlogical-op
    -Wuseless-cast
)

# Debug 模式额外选项
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_options(
        -g
        -O0
        -fno-omit-frame-pointer
        -fsanitize=address
        -fsanitize=undefined
    )
    add_link_options(
        -fsanitize=address
        -fsanitize=undefined
    )
endif()

# Release 模式优化选项
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_compile_options(
        -O2
        -DNDEBUG
    )
endif()

# 包含目录
include_directories(
    ${PROJECT_SOURCE_DIR}/include
)

# 选项
option(BUILD_EXAMPLES "构建示例程序" ON)
option(BUILD_TESTS "构建测试程序" ON)

# 添加子目录
if(BUILD_EXAMPLES)
    add_subdirectory(examples/01-naming)
    add_subdirectory(examples/02-formatting)
    add_subdirectory(examples/03-header-files)
    add_subdirectory(examples/04-class-design)
    add_subdirectory(examples/05-function-design)
    add_subdirectory(examples/06-memory-management)
    add_subdirectory(examples/07-concurrency)
    add_subdirectory(examples/08-error-handling)
    add_subdirectory(examples/09-comments)
endif()

# 测试
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# 安装
install(DIRECTORY include/ DESTINATION include)
install(DIRECTORY tools/ DESTINATION tools)
