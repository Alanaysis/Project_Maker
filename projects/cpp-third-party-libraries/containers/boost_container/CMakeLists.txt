# Boost.Container 示例
find_package(Boost REQUIRED COMPONENTS container)

# flat_map 示例
add_executable(boost_container_flat_map flat_map_example.cpp)
target_link_libraries(boost_container_flat_map PRIVATE Boost::container)

# stable_vector 示例
add_executable(boost_container_stable_vector stable_vector_example.cpp)
target_link_libraries(boost_container_stable_vector PRIVATE Boost::container)

# small_vector 示例
add_executable(boost_container_small_vector small_vector_example.cpp)
target_link_libraries(boost_container_small_vector PRIVATE Boost::container)