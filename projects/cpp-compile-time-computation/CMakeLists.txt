cmake_minimum_required(VERSION 3.16)
project(cpp-compile-time-computation
    VERSION 1.0.0
    LANGUAGES CXX
    DESCRIPTION "C++ Compile-Time Computation Project"
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Compiler warnings
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror=return-type)
elseif(MSVC)
    add_compile_options(/W4 /WX)
endif()

# Header-only library
add_library(compile_time INTERFACE)
target_include_directories(compile_time INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
target_compile_features(compile_time INTERFACE cxx_std_20)

# ─── Examples ────────────────────────────────────────────────────────────────
file(GLOB EXAMPLE_SOURCES examples/*.cpp)
foreach(example_src ${EXAMPLE_SOURCES})
    get_filename_component(example_name ${example_src} NAME_WE)
    add_executable(example_${example_name} ${example_src})
    target_link_libraries(example_${example_name} PRIVATE compile_time)
endforeach()

# ─── Tests ───────────────────────────────────────────────────────────────────
enable_testing()
file(GLOB TEST_SOURCES tests/*.cpp)
foreach(test_src ${TEST_SOURCES})
    get_filename_component(test_name ${test_src} NAME_WE)
    add_executable(test_${test_name} ${test_src})
    target_link_libraries(test_${test_name} PRIVATE compile_time)
    add_test(NAME ${test_name} COMMAND test_${test_name})
endforeach()

# ─── Benchmarks ──────────────────────────────────────────────────────────────
file(GLOB BENCH_SOURCES benchmarks/*.cpp)
foreach(bench_src ${BENCH_SOURCES})
    get_filename_component(bench_name ${bench_src} NAME_WE)
    add_executable(bench_${bench_name} ${bench_src})
    target_link_libraries(bench_${bench_name} PRIVATE compile_time)
endforeach()
