cmake_minimum_required(VERSION 3.14)
project(ConstraintSolver VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Main library
add_library(cadsolver
    src/solver.cpp
)

target_include_directories(cadsolver PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Examples
add_executable(basic_example examples/basic_example.cpp)
target_link_libraries(basic_example PRIVATE cadsolver)

add_executable(cad_sketch examples/cad_sketch.cpp)
target_link_libraries(cad_sketch PRIVATE cadsolver)

add_executable(tangent_demo examples/tangent_demo.cpp)
target_link_libraries(tangent_demo PRIVATE cadsolver)

# Tests
enable_testing()
add_executable(constraint_tests tests/test_constraints.cpp)
target_link_libraries(constraint_tests PRIVATE cadsolver)
add_test(NAME constraint_tests COMMAND constraint_tests)

add_executable(solver_tests tests/test_solver.cpp)
target_link_libraries(solver_tests PRIVATE cadsolver)
add_test(NAME solver_tests COMMAND solver_tests)

# Install
install(TARGETS cadsolver
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/ DESTINATION include)
