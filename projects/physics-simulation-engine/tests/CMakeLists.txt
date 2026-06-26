find_package(GTest QUIET)

if(NOT GTest_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG release-1.12.1
    )
    FetchContent_MakeAvailable(googletest)
endif()

add_executable(test_physics test_physics.cpp)
target_link_libraries(test_physics
    PRIVATE
        physics_simulation
        GTest::gtest
        GTest::gtest_main
)

add_test(NAME test_physics COMMAND test_physics)
