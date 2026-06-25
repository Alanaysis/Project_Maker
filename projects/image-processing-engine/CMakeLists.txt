cmake_minimum_required(VERSION 3.14)
project(image_processing VERSION 1.0.0 LANGUAGES CXX)

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
    src/image_engine.cpp
)

add_library(image_engine ${CORE_SOURCES})
target_include_directories(image_engine PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Tests
enable_testing()
add_executable(test_filters tests/test_filters.cpp)
target_link_libraries(test_filters PRIVATE image_engine)

add_executable(test_color tests/test_color.cpp)
target_link_libraries(test_color PRIVATE image_engine)

add_executable(test_transform tests/test_transform.cpp)
target_link_libraries(test_transform PRIVATE image_engine)

add_test(NAME test_filters COMMAND test_filters)
add_test(NAME test_color COMMAND test_color)
add_test(NAME test_transform COMMAND test_transform)

# Examples
add_executable(basic_filters examples/basic_filters.cpp)
target_link_libraries(basic_filters PRIVATE image_engine)

add_executable(color_transform examples/color_transform.cpp)
target_link_libraries(color_transform PRIVATE image_engine)

add_executable(edge_detection examples/edge_detection.cpp)
target_link_libraries(edge_detection PRIVATE image_engine)

# Install
include(GNUInstallDirs)
install(TARGETS image_engine ARCHIVE DESTINATION lib LIBRARY DESTINATION lib)
install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
