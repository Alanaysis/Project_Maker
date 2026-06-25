# Folly 工具库示例
find_package(folly REQUIRED)

# 字符串格式化示例
add_executable(folly_format format_example.cpp)
target_link_libraries(folly_format PRIVATE Folly::folly)