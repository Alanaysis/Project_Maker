# 数据结构优化示例

add_executable(compact_structures compact_structures.cpp)
target_link_libraries(compact_structures Threads::Threads)

add_executable(lock_free lock_free.cpp)
target_link_libraries(lock_free Threads::Threads)

add_executable(concurrent_structures concurrent_structures.cpp)
target_link_libraries(concurrent_structures Threads::Threads)

add_executable(cache_friendly_container cache_friendly_container.cpp)
target_link_libraries(cache_friendly_container Threads::Threads)