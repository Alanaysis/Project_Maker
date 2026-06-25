# 算法优化示例

add_executable(time_complexity time_complexity.cpp)
target_link_libraries(time_complexity Threads::Threads)

add_executable(space_complexity space_complexity.cpp)
target_link_libraries(space_complexity Threads::Threads)

add_executable(constant_factor constant_factor.cpp)
target_link_libraries(constant_factor Threads::Threads)

add_executable(parallelization parallelization.cpp)
target_link_libraries(parallelization Threads::Threads)

add_executable(simd_optimization simd_optimization.cpp)
target_link_libraries(simd_optimization Threads::Threads)