# CPR HTTP 请求库示例
find_package(cpr REQUIRED)

# 基础示例
add_executable(cpr_basic basic_example.cpp)
target_link_libraries(cpr_basic PRIVATE cpr::cpr)