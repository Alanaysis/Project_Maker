# Folly 容器库示例
find_package(folly REQUIRED)

# F14HashMap 示例
add_executable(folly_f14_hashmap f14_hashmap_example.cpp)
target_link_libraries(folly_f14_hashmap PRIVATE Folly::folly)