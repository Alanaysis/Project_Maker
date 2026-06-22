cmake_minimum_required(VERSION 3.14)
project(matching-engine VERSION 1.0.0 LANGUAGES CXX)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# 头文件目录
include_directories(include)

# 源文件
set(SOURCES
    src/order_book.cpp
    src/matching_engine.cpp
    src/order_manager.cpp
)

# 创建静态库
add_library(matching_engine_lib STATIC ${SOURCES})
target_include_directories(matching_engine_lib PUBLIC include)

# 选项：是否构建测试
option(BUILD_TESTS "Build tests" OFF)

if(BUILD_TESTS)
    # 查找 Google Test
    find_package(GTest REQUIRED)
    include_directories(${GTEST_INCLUDE_DIRS})

    # 测试文件
    set(TEST_SOURCES
        tests/test_order_book.cpp
        tests/test_matching_engine.cpp
        tests/test_main.cpp
    )

    # 创建测试可执行文件
    add_executable(matching_engine_tests ${TEST_SOURCES})
    target_link_libraries(matching_engine_tests
        matching_engine_lib
        GTest::GTest
        GTest::Main
        pthread
    )

    # 启用测试
    enable_testing()
    add_test(NAME matching_engine_tests COMMAND matching_engine_tests)
endif()

# 选项：是否构建示例
option(BUILD_EXAMPLES "Build examples" ON)

if(BUILD_EXAMPLES)
    # 基础示例
    add_executable(basic_example examples/basic.cpp)
    target_link_libraries(basic_example matching_engine_lib)

    # 高级示例
    add_executable(advanced_example examples/advanced.cpp)
    target_link_libraries(advanced_example matching_engine_lib)
endif()

# 安装规则
install(TARGETS matching_engine_lib
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)

install(DIRECTORY include/ DESTINATION include)
