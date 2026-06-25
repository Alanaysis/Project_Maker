# I/O 优化示例

add_executable(buffered_io buffered_io.cpp)
target_link_libraries(buffered_io Threads::Threads)

add_executable(async_io async_io.cpp)
target_link_libraries(async_io Threads::Threads)

add_executable(mmap_demo mmap_demo.cpp)
target_link_libraries(mmap_demo Threads::Threads)

add_executable(batch_operations batch_operations.cpp)
target_link_libraries(batch_operations Threads::Threads)