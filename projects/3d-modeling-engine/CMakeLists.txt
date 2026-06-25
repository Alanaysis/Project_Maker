cmake_minimum_required(VERSION 3.14)
project(3d_modeling VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_compile_options(-Wall -Wextra -Wpedantic)

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_options(-g -O0)
else()
    add_compile_options(-O2)
endif()

set(CORE_SOURCES
    src/3d_engine.cpp
)

add_library(3d_engine ${CORE_SOURCES})
target_include_directories(3d_engine PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

find_package(Threads REQUIRED)
target_link_libraries(3d_engine Threads::Threads)

enable_testing()
add_executable(test_mesh tests/test_mesh.cpp)
target_link_libraries(test_mesh PRIVATE 3d_engine)

add_executable(test_transform tests/test_transform.cpp)
target_link_libraries(test_transform PRIVATE 3d_engine)

add_executable(test_geometry tests/test_geometry.cpp)
target_link_libraries(test_geometry PRIVATE 3d_engine)

add_test(NAME test_mesh COMMAND test_mesh)
add_test(NAME test_transform COMMAND test_transform)
add_test(NAME test_geometry COMMAND test_geometry)

add_executable(demo_mesh examples/demo_mesh.cpp)
target_link_libraries(demo_mesh PRIVATE 3d_engine)

add_executable(demo_transform examples/demo_transform.cpp)
target_link_libraries(demo_transform PRIVATE 3d_engine)

include(GNUInstallDirs)
install(TARGETS 3d_engine ARCHIVE DESTINATION lib LIBRARY DESTINATION lib)
install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
