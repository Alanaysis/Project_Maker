cmake_minimum_required(VERSION 3.10)
project(ray-tracer VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 主程序
add_executable(ray-tracer src/main.cpp)
target_include_directories(ray-tracer PRIVATE include)

# 测试程序
enable_testing()

add_executable(test_vec3 tests/test_vec3.cpp)
target_include_directories(test_vec3 PRIVATE include)
add_test(NAME test_vec3 COMMAND test_vec3)

add_executable(test_ray tests/test_ray.cpp)
target_include_directories(test_ray PRIVATE include)
add_test(NAME test_ray COMMAND test_ray)

add_executable(test_sphere tests/test_sphere.cpp)
target_include_directories(test_sphere PRIVATE include)
add_test(NAME test_sphere COMMAND test_sphere)

add_executable(test_renderer tests/test_renderer.cpp)
target_include_directories(test_renderer PRIVATE include)
add_test(NAME test_renderer COMMAND test_renderer)

# 示例程序
add_executable(basic_scene examples/basic_scene.cpp)
target_include_directories(basic_scene PRIVATE include)
