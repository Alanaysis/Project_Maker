cmake_minimum_required(VERSION 3.14)
project(disaster-recovery-storage VERSION 1.0.0 LANGUAGES CXX)

# 设置C++标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# 构建类型
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 头文件目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# 源文件
set(SOURCES
    src/ec/galois_field.cpp
    src/ec/reed_solomon.cpp
    src/core/data_sharder.cpp
    src/core/replica_manager.cpp
    src/network/failure_detector.cpp
    src/node/storage_node.cpp
    src/utils/checksum.cpp
)

# 创建库
add_library(disaster_recovery_lib ${SOURCES})

# 设置库属性
set_target_properties(disaster_recovery_lib PROPERTIES
    OUTPUT_NAME disaster_recovery
    VERSION ${PROJECT_VERSION}
)

# 主程序（示例）
add_executable(basic_usage examples/basic_usage.cpp)
target_link_libraries(basic_usage disaster_recovery_lib)

add_executable(erasure_coding examples/erasure_coding.cpp)
target_link_libraries(erasure_coding disaster_recovery_lib)

add_executable(fault_tolerance examples/fault_tolerance.cpp)
target_link_libraries(fault_tolerance disaster_recovery_lib)

# 测试
option(BUILD_TESTS "Build tests" ON)

if(BUILD_TESTS)
    # Google Test
    include(FetchContent)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG release-1.12.1
    )
    FetchContent_MakeAvailable(googletest)

    # 测试源文件
    set(TEST_SOURCES
        tests/unit/test_galois_field.cpp
        tests/unit/test_reed_solomon.cpp
        tests/unit/test_data_sharder.cpp
        tests/unit/test_replica_manager.cpp
        tests/unit/test_failure_detector.cpp
        tests/unit/test_storage_node.cpp
        tests/unit/test_checksum.cpp
    )

    # 创建测试可执行文件
    add_executable(unit_tests ${TEST_SOURCES})
    target_link_libraries(unit_tests
        disaster_recovery_lib
        GTest::gtest_main
    )

    # 添加测试
    include(GoogleTest)
    gtest_discover_tests(unit_tests)
endif()

# 安装
install(TARGETS disaster_recovery_lib
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/ DESTINATION include)

# 打印配置信息
message(STATUS "========================================")
message(STATUS "  Disaster Recovery Storage System")
message(STATUS "========================================")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build Tests: ${BUILD_TESTS}")
message(STATUS "========================================")
