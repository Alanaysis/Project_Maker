cmake_minimum_required(VERSION 3.10)
project(cpp11-14-features LANGUAGES CXX)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# 包含目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# 示例可执行文件
set(EXAMPLES
    01_move_semantics
    02_lambda
    03_smart_pointers
    04_threads
    05_variadic_templates
    06_constexpr
    07_auto_decltype
    08_range_for
    09_initializer_list
)

foreach(example ${EXAMPLES})
    add_executable(${example} examples/${example}.cpp)
endforeach()

# 主程序
add_executable(main main.cpp)

# 测试
enable_testing()
add_subdirectory(tests)
