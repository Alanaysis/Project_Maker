# 测试 CMakeLists.txt

# 查找 Google Test
find_package(GTest QUIET)

if(NOT GTest_FOUND)
    # 如果找不到 GTest，使用 FetchContent 下载
    include(FetchContent)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG release-1.12.1
    )
    FetchContent_MakeAvailable(googletest)
endif()

# 测试源文件
set(TEST_SOURCES
    test_vector2d.cpp
    test_aabb.cpp
    test_rigid_body.cpp
    test_collision.cpp
    test_constraint.cpp
    test_world.cpp
    test_integration.cpp
)

# 创建测试可执行文件
add_executable(physics_engine_tests ${TEST_SOURCES})

# 链接库
target_link_libraries(physics_engine_tests
    PRIVATE
        physics_engine
        GTest::gtest
        GTest::gtest_main
)

# 添加测试
add_test(NAME physics_engine_tests COMMAND physics_engine_tests)
