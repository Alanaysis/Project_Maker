cmake_minimum_required(VERSION 3.14)
project(scene-graph VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# 编译器警告
add_compile_options(-Wall -Wextra -Wpedantic)

# 核心库
add_library(scene_graph_lib STATIC
    src/scene_graph.cpp
)

target_include_directories(scene_graph_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# 测试
option(BUILD_TESTS "Build tests" OFF)

if(BUILD_TESTS)
    # Google Test
    include(FetchContent)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG v1.14.0
    )
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)

    enable_testing()

    add_executable(scene_graph_tests
        tests/test_math_types.cpp
        tests/test_transform.cpp
        tests/test_bounds.cpp
        tests/test_scene_node.cpp
        tests/test_scene_graph.cpp
        tests/test_main.cpp
    )

    target_link_libraries(scene_graph_tests PRIVATE
        scene_graph_lib
        GTest::gtest
        GTest::gtest_main
    )

    include(GoogleTest)
    gtest_discover_tests(scene_graph_tests)
endif()

# 示例
option(BUILD_EXAMPLES "Build examples" ON)

if(BUILD_EXAMPLES)
    add_executable(scene_graph_demo
        examples/demo.cpp
    )

    target_link_libraries(scene_graph_demo PRIVATE
        scene_graph_lib
    )
endif()

# 安装规则
install(TARGETS scene_graph_lib
    ARCHIVE DESTINATION lib
)
install(DIRECTORY include/
    DESTINATION include/scene-graph
)
