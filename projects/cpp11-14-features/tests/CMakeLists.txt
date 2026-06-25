cmake_minimum_required(VERSION 3.10)

# 使用 FetchContent 下载 Google Test
include(FetchContent)

FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG release-1.12.1
)

# 设置 Google Test 选项
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)

# 下载并构建 Google Test
FetchContent_MakeAvailable(googletest)

# 测试文件列表
set(TEST_SOURCES
    test_move_semantics.cpp
    test_lambda.cpp
    test_smart_pointers.cpp
    test_threads.cpp
    test_variadic_templates.cpp
    test_constexpr.cpp
    test_auto_decltype.cpp
    test_range_for.cpp
    test_initializer_list.cpp
)

# 为每个测试文件创建可执行文件
foreach(test_source ${TEST_SOURCES})
    # 获取测试名称（去掉 .cpp 后缀）
    get_filename_component(test_name ${test_source} NAME_WE)

    # 创建可执行文件
    add_executable(${test_name} ${test_source})

    # 链接 Google Test
    target_link_libraries(${test_name} GTest::gtest_main pthread)

    # 添加测试
    add_test(NAME ${test_name} COMMAND ${test_name})
endforeach()
