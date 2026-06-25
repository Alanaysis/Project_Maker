cmake_minimum_required(VERSION 3.16)
project(CppMemoryModelConcurrency VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Threading support
find_package(Threads REQUIRED)

# Common library for shared utilities
add_library(common_utils INTERFACE)
target_include_directories(common_utils INTERFACE ${CMAKE_SOURCE_DIR}/include)

# ==================== 01 Memory Model ====================
add_executable(memory_location src/01_memory_model/memory_location.cpp)
target_link_libraries(memory_location PRIVATE Threads::Threads common_utils)

add_executable(object_model src/01_memory_model/object_model.cpp)
target_link_libraries(object_model PRIVATE Threads::Threads common_utils)

add_executable(value_categories src/01_memory_model/value_categories.cpp)
target_link_libraries(value_categories PRIVATE Threads::Threads common_utils)

add_executable(lifetime src/01_memory_model/lifetime.cpp)
target_link_libraries(lifetime PRIVATE Threads::Threads common_utils)

# ==================== 02 Memory Order ====================
add_executable(relaxed src/02_memory_order/relaxed.cpp)
target_link_libraries(relaxed PRIVATE Threads::Threads common_utils)

add_executable(acquire_release src/02_memory_order/acquire_release.cpp)
target_link_libraries(acquire_release PRIVATE Threads::Threads common_utils)

add_executable(seq_cst src/02_memory_order/seq_cst.cpp)
target_link_libraries(seq_cst PRIVATE Threads::Threads common_utils)

add_executable(memory_fence src/02_memory_order/memory_fence.cpp)
target_link_libraries(memory_fence PRIVATE Threads::Threads common_utils)

# ==================== 03 Atomic ====================
add_executable(atomic_basics src/03_atomic/atomic_basics.cpp)
target_link_libraries(atomic_basics PRIVATE Threads::Threads common_utils)

add_executable(atomic_flag src/03_atomic/atomic_flag.cpp)
target_link_libraries(atomic_flag PRIVATE Threads::Threads common_utils)

add_executable(atomic_smart_ptr src/03_atomic/atomic_smart_ptr.cpp)
target_link_libraries(atomic_smart_ptr PRIVATE Threads::Threads common_utils)

add_executable(atomic_float src/03_atomic/atomic_float.cpp)
target_link_libraries(atomic_float PRIVATE Threads::Threads common_utils)

add_executable(cas_operations src/03_atomic/cas_operations.cpp)
target_link_libraries(cas_operations PRIVATE Threads::Threads common_utils)

add_executable(atomic_performance src/03_atomic/atomic_performance.cpp)
target_link_libraries(atomic_performance PRIVATE Threads::Threads common_utils)

# ==================== 04 Concurrent Data Structures ====================
add_executable(lock_free_stack src/04_concurrent_data_structures/lock_free_stack.cpp)
target_link_libraries(lock_free_stack PRIVATE Threads::Threads common_utils)

add_executable(lock_free_queue src/04_concurrent_data_structures/lock_free_queue.cpp)
target_link_libraries(lock_free_queue PRIVATE Threads::Threads common_utils)

add_executable(lock_free_list src/04_concurrent_data_structures/lock_free_list.cpp)
target_link_libraries(lock_free_list PRIVATE Threads::Threads common_utils)

add_executable(concurrent_hashmap src/04_concurrent_data_structures/concurrent_hashmap.cpp)
target_link_libraries(concurrent_hashmap PRIVATE Threads::Threads common_utils)

add_executable(rwlock src/04_concurrent_data_structures/rwlock.cpp)
target_link_libraries(rwlock PRIVATE Threads::Threads common_utils)

# ==================== 05 Thread Synchronization ====================
add_executable(mutex_types src/05_thread_synchronization/mutex_types.cpp)
target_link_libraries(mutex_types PRIVATE Threads::Threads common_utils)

add_executable(condition_variable src/05_thread_synchronization/condition_variable.cpp)
target_link_libraries(condition_variable PRIVATE Threads::Threads common_utils)

add_executable(latch src/05_thread_synchronization/latch.cpp)
target_link_libraries(latch PRIVATE Threads::Threads common_utils)

add_executable(barrier src/05_thread_synchronization/barrier.cpp)
target_link_libraries(barrier PRIVATE Threads::Threads common_utils)

add_executable(semaphore src/05_thread_synchronization/semaphore.cpp)
target_link_libraries(semaphore PRIVATE Threads::Threads common_utils)

add_executable(stop_token src/05_thread_synchronization/stop_token.cpp)
target_link_libraries(stop_token PRIVATE Threads::Threads common_utils)

# ==================== 06 Concurrent Patterns ====================
add_executable(thread_pool src/06_concurrent_patterns/thread_pool.cpp)
target_link_libraries(thread_pool PRIVATE Threads::Threads common_utils)

add_executable(producer_consumer src/06_concurrent_patterns/producer_consumer.cpp)
target_link_libraries(producer_consumer PRIVATE Threads::Threads common_utils)

add_executable(task_scheduler src/06_concurrent_patterns/task_scheduler.cpp)
target_link_libraries(task_scheduler PRIVATE Threads::Threads common_utils)

add_executable(async_future src/06_concurrent_patterns/async_future.cpp)
target_link_libraries(async_future PRIVATE Threads::Threads common_utils)

# ==================== 07 Performance ====================
add_executable(false_sharing src/07_performance/false_sharing.cpp)
target_link_libraries(false_sharing PRIVATE Threads::Threads common_utils)

add_executable(cache_alignment src/07_performance/cache_alignment.cpp)
target_link_libraries(cache_alignment PRIVATE Threads::Threads common_utils)

add_executable(thread_affinity src/07_performance/thread_affinity.cpp)
target_link_libraries(thread_affinity PRIVATE Threads::Threads common_utils)

add_executable(debug_techniques src/07_performance/debug_techniques.cpp)
target_link_libraries(debug_techniques PRIVATE Threads::Threads common_utils)

# ==================== Benchmarks ====================
option(BUILD_BENCHMARKS "Build performance benchmarks" ON)
if(BUILD_BENCHMARKS)
    add_executable(benchmark_all src/benchmark_all.cpp)
    target_link_libraries(benchmark_all PRIVATE Threads::Threads common_utils)
endif()

# Compiler warnings
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Wno-unused-parameter)
    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        add_compile_options(-O2)
    endif()
endif()
