cmake_minimum_required(VERSION 3.16)

# 测试源文件
set(TEST_SOURCES
    test_task.cpp
    test_scheduler.cpp
    test_memory.cpp
    test_integration.cpp
)

# 创建测试可执行文件
add_executable(test_all ${TEST_SOURCES})

# 链接依赖
target_link_libraries(test_all
    PRIVATE
        heterogeneous
        Threads::Threads
)

# 添加测试
add_test(NAME unit_tests COMMAND test_all)

# 设置测试属性
set_tests_properties(unit_tests PROPERTIES
    TIMEOUT 60
    LABELS "unit"
)
