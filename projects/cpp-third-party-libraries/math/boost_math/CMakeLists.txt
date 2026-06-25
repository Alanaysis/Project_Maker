# Boost.Math 数学库示例
find_package(Boost REQUIRED COMPONENTS math)

# 基础示例
add_executable(boost_math_basic basic_example.cpp)
target_link_libraries(boost_math_basic PRIVATE Boost::math)