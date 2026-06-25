# EASTL 容器库示例
find_package(EASTL REQUIRED)

# fixed_vector 示例
add_executable(eastl_fixed_vector fixed_vector_example.cpp)
target_link_libraries(eastl_fixed_vector PRIVATE EASTL::EASTL)