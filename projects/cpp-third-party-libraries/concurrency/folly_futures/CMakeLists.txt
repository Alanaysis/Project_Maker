# Folly Futures 异步编程示例
find_package(folly REQUIRED)

# 基础示例
add_executable(folly_futures_basic basic_example.cpp)
target_link_libraries(folly_futures_basic PRIVATE Folly::folly)