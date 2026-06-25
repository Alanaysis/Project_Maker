# 工具和测量示例

add_executable(benchmark_framework benchmark_framework.cpp)
target_link_libraries(benchmark_framework Threads::Threads)

add_executable(perf_counters perf_counters.cpp)
target_link_libraries(perf_counters Threads::Threads)

add_executable(micro_benchmark micro_benchmark.cpp)
target_link_libraries(micro_benchmark Threads::Threads)