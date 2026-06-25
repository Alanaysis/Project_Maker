add_executable(concurrency_pitfalls
    01_data_race.cpp
    02_deadlock.cpp
    03_livelock.cpp
    04_atomic_traps.cpp
    05_memory_order.cpp
    06_false_sharing.cpp
)

target_link_libraries(concurrency_pitfalls pthread)
