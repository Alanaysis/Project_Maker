cmake_minimum_required(VERSION 3.16)

# 示例程序
add_executable(01_basic_task 01_basic_task.cpp)
target_link_libraries(01_basic_task PRIVATE heterogeneous Threads::Threads)

add_executable(02_matrix_multiply 02_matrix_multiply.cpp)
target_link_libraries(02_matrix_multiply PRIVATE heterogeneous Threads::Threads)

add_executable(03_vector_add 03_vector_add.cpp)
target_link_libraries(03_vector_add PRIVATE heterogeneous Threads::Threads)

add_executable(04_performance_benchmark 04_performance_benchmark.cpp)
target_link_libraries(04_performance_benchmark PRIVATE heterogeneous Threads::Threads)
