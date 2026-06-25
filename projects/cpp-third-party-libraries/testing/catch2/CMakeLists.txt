# Catch2 测试框架示例
find_package(Catch2 REQUIRED)

# 基础测试
add_executable(catch2_basic basic_test.cpp)
target_link_libraries(catch2_basic PRIVATE Catch2::Catch2WithMain)