# Google Test 示例
find_package(GTest REQUIRED)

# 基础测试
add_executable(gtest_basic basic_test.cpp)
target_link_libraries(gtest_basic PRIVATE GTest::gtest GTest::gtest_main)

# 测试夹具
add_executable(gtest_fixture fixture_test.cpp)
target_link_libraries(gtest_fixture PRIVATE GTest::gtest GTest::gtest_main)

# 参数化测试
add_executable(gtest_parameterized parameterized_test.cpp)
target_link_libraries(gtest_parameterized PRIVATE GTest::gtest GTest::gtest_main)