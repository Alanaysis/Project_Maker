# range-v3 范围库示例
find_package(range-v3 REQUIRED)

# 基础示例
add_executable(range_v3_basic basic_example.cpp)
target_link_libraries(range_v3_basic PRIVATE range-v3::range-v3)