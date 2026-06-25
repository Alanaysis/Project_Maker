# 内存优化示例

add_executable(cache_friendly cache_friendly.cpp)
target_link_libraries(cache_friendly Threads::Threads)

add_executable(soa_vs_aos soa_vs_aos.cpp)
target_link_libraries(soa_vs_aos Threads::Threads)

add_executable(memory_alignment memory_alignment.cpp)
target_link_libraries(memory_alignment Threads::Threads)

add_executable(prefetching prefetching.cpp)
target_link_libraries(prefetching Threads::Threads)

add_executable(memory_pool memory_pool.cpp)
target_link_libraries(memory_pool Threads::Threads)

add_executable(small_buffer_optimization small_buffer_optimization.cpp)
target_link_libraries(small_buffer_optimization Threads::Threads)