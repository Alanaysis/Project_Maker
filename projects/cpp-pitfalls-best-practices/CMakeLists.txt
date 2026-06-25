cmake_minimum_required(VERSION 3.16)
project(CppPitfallsBestPractices VERSION 1.0.0 LANGUAGES CXX)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# 编译选项
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Wno-unused-parameter)
elseif(MSVC)
    add_compile_options(/W4 /wd4100)
endif()

# Sanitizer 选项
option(ENABLE_SANITIZERS "Enable sanitizers" OFF)
if(ENABLE_SANITIZERS)
    add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address,undefined)
endif()

# 子目录
add_subdirectory(src/memory)
add_subdirectory(src/type)
add_subdirectory(src/template)
add_subdirectory(src/concurrency)
add_subdirectory(src/lifetime)
add_subdirectory(src/exception)
add_subdirectory(src/best_practices)
add_subdirectory(src/quality)

# 测试
enable_testing()
add_test(NAME memory_pitfalls COMMAND memory_pitfalls)
add_test(NAME type_pitfalls COMMAND type_pitfalls)
add_test(NAME template_pitfalls COMMAND template_pitfalls)
add_test(NAME concurrency_pitfalls COMMAND concurrency_pitfalls)
add_test(NAME lifetime_pitfalls COMMAND lifetime_pitfalls)
add_test(NAME exception_safety COMMAND exception_safety)
add_test(NAME best_practices COMMAND best_practices)
add_test(NAME quality COMMAND quality)
