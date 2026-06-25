# ============================================================================
# 测试
# ============================================================================

include(FetchContent)

FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)

set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

# 测试可执行文件
add_executable(mylib_tests
    test_string_utils.cpp
    test_math_utils.cpp
)

target_link_libraries(mylib_tests
    PRIVATE
        mylib
        GTest::gtest_main
)

set_project_warnings(mylib_tests)

include(GoogleTest)
gtest_discover_tests(mylib_tests)
