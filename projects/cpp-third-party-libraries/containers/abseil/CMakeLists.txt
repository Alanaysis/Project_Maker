# Abseil 容器库示例
find_package(absl REQUIRED)

# flat_hash_map 示例
add_executable(abseil_flat_hash_map flat_hash_map_example.cpp)
target_link_libraries(abseil_flat_hash_map PRIVATE absl::flat_hash_map)