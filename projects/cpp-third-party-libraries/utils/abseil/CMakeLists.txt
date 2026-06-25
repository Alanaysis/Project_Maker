# Abseil 工具库示例
find_package(absl REQUIRED)

# 字符串工具示例
add_executable(abseil_string string_example.cpp)
target_link_libraries(abseil_string PRIVATE absl::strings absl::str_format)