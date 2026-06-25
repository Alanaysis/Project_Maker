# doctest 测试框架示例
find_package(doctest REQUIRED)

# 基础测试
add_executable(doctest_basic basic_test.cpp)
target_link_libraries(doctest_basic PRIVATE doctest::doctest)