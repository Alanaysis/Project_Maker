# 并发优化示例

add_executable(thread_pool thread_pool.cpp)
target_link_libraries(thread_pool Threads::Threads)

add_executable(task_scheduler task_scheduler.cpp)
target_link_libraries(task_scheduler Threads::Threads)

add_executable(lock_free_programming lock_free_programming.cpp)
target_link_libraries(lock_free_programming Threads::Threads)

add_executable(atomic_optimization atomic_optimization.cpp)
target_link_libraries(atomic_optimization Threads::Threads)

add_executable(false_sharing false_sharing.cpp)
target_link_libraries(false_sharing Threads::Threads)