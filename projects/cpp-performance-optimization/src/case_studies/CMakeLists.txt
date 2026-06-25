# 实际案例

add_executable(vector_operations vector_operations.cpp)
target_link_libraries(vector_operations Threads::Threads)

add_executable(matrix_multiplication matrix_multiplication.cpp)
target_link_libraries(matrix_multiplication Threads::Threads)

add_executable(string_processing string_processing.cpp)
target_link_libraries(string_processing Threads::Threads)

add_executable(hash_table hash_table.cpp)
target_link_libraries(hash_table Threads::Threads)

add_executable(sorting_optimization sorting_optimization.cpp)
target_link_libraries(sorting_optimization Threads::Threads)