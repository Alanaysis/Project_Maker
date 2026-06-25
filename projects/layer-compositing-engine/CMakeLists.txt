cmake_minimum_required(VERSION 3.14)
project(layer_compositing VERSION 1.0.0 LANGUAGES CXX)

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
    src/layer_compositing.cpp
)

add_library(layer_compositing ${CORE_SOURCES})
target_include_directories(layer_compositing PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

enable_testing()
add_executable(test_blending tests/test_blending.cpp)
target_link_libraries(test_blending PRIVATE layer_compositing)

add_executable(test_masking tests/test_masking.cpp)
target_link_libraries(test_masking PRIVATE layer_compositing)

add_executable(test_composite tests/test_composite.cpp)
target_link_libraries(test_composite PRIVATE layer_compositing)

add_test(NAME test_blending COMMAND test_blending)
add_test(NAME test_masking COMMAND test_masking)
add_test(NAME test_composite COMMAND test_composite)

add_executable(demo_blending examples/demo_blending.cpp)
target_link_libraries(demo_blending PRIVATE layer_compositing)

add_executable(demo_masking examples/demo_masking.cpp)
target_link_libraries(demo_masking PRIVATE layer_compositing)

include(GNUInstallDirs)
install(TARGETS layer_compositing ARCHIVE DESTINATION lib LIBRARY DESTINATION lib)
install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
