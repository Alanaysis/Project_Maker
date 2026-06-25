# Google Mock 模拟框架示例
find_package(GTest REQUIRED)

# 基础测试
add_executable(gmock_basic basic_test.cpp)
target_link_libraries(gmock_basic PRIVATE GTest::gtest GTest::gmock GTest::gtest_main)