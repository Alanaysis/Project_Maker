cmake_minimum_required(VERSION 3.16)
project(physics-simulation-engine VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Main library
add_library(physics_simulation
    src/rigid_body.cpp
)

target_include_directories(physics_simulation PUBLIC
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
)

target_compile_options(physics_simulation PRIVATE
    $<$<CXX_COMPILER_ID:GNU>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:Clang>:-Wall -Wextra -Wpedantic>
)

# Examples
add_subdirectory(examples)

# Tests
enable_testing()
add_subdirectory(tests)
