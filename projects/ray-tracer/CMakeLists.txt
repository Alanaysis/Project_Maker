cmake_minimum_required(VERSION 3.10)
project(ray-tracer VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找线程库
find_package(Threads REQUIRED)

# 主程序
add_executable(ray-tracer src/main.cpp)
target_include_directories(ray-tracer PRIVATE include)
target_link_libraries(ray-tracer Threads::Threads)

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
target_link_libraries(test_renderer Threads::Threads)
add_test(NAME test_renderer COMMAND test_renderer)

# 示例程序
add_executable(basic_scene examples/basic_scene.cpp)
target_include_directories(basic_scene PRIVATE include)
target_link_libraries(basic_scene Threads::Threads)

add_executable(01_basic_sphere examples/01_basic_sphere.cpp)
target_include_directories(01_basic_sphere PRIVATE include)
target_link_libraries(01_basic_sphere Threads::Threads)

add_executable(02_complex_scene examples/02_complex_scene.cpp)
target_include_directories(02_complex_scene PRIVATE include)
target_link_libraries(02_complex_scene Threads::Threads)

add_executable(03_primitives examples/03_primitives.cpp)
target_include_directories(03_primitives PRIVATE include)
target_link_libraries(03_primitives Threads::Threads)

add_executable(04_path_tracing examples/04_path_tracing.cpp)
target_include_directories(04_path_tracing PRIVATE include)
target_link_libraries(04_path_tracing Threads::Threads)

add_executable(05_depth_of_field examples/05_depth_of_field.cpp)
target_include_directories(05_depth_of_field PRIVATE include)
target_link_libraries(05_depth_of_field Threads::Threads)

add_executable(06_textures examples/06_textures.cpp)
target_include_directories(06_textures PRIVATE include)
target_link_libraries(06_textures Threads::Threads)

add_executable(07_advanced_materials examples/07_advanced_materials.cpp)
target_include_directories(07_advanced_materials PRIVATE include)
target_link_libraries(07_advanced_materials Threads::Threads)

add_executable(08_motion_blur examples/08_motion_blur.cpp)
target_include_directories(08_motion_blur PRIVATE include)
target_link_libraries(08_motion_blur Threads::Threads)

add_executable(09_acceleration examples/09_acceleration.cpp)
target_include_directories(09_acceleration PRIVATE include)
target_link_libraries(09_acceleration Threads::Threads)

add_executable(10_sampling examples/10_sampling.cpp)
target_include_directories(10_sampling PRIVATE include)
target_link_libraries(10_sampling Threads::Threads)
