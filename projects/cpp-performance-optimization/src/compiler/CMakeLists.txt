# 编译器优化示例

add_executable(inlining inlining.cpp)
target_link_libraries(inlining Threads::Threads)

add_executable(loop_unrolling loop_unrolling.cpp)
target_link_libraries(loop_unrolling Threads::Threads)

add_executable(vectorization vectorization.cpp)
target_link_libraries(vectorization Threads::Threads)

add_executable(branch_prediction branch_prediction.cpp)
target_link_libraries(branch_prediction Threads::Threads)

add_executable(lto_demo lto_demo.cpp)
target_link_libraries(lto_demo Threads::Threads)