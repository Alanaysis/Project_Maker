# Intel TBB 并发库示例
find_package(TBB REQUIRED)

# parallel_for 示例
add_executable(tbb_parallel_for parallel_for_example.cpp)
target_link_libraries(tbb_parallel_for PRIVATE TBB::tbb)

# parallel_reduce 示例
add_executable(tbb_parallel_reduce parallel_reduce_example.cpp)
target_link_libraries(tbb_parallel_reduce PRIVATE TBB::tbb)