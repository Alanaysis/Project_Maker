cmake_minimum_required(VERSION 3.20)
project(GPUShaderLibrary VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 选项
option(BUILD_DEMOS "Build demo applications" ON)
option(BUILD_TESTS "Build tests" OFF)

# 查找依赖
find_package(OpenGL REQUIRED)

# GLFW
find_package(glfw3 3.3 QUIET)
if(NOT glfw3_FOUND)
    message(STATUS "GLFW not found, using FetchContent")
    include(FetchContent)
    FetchContent_Declare(
        glfw
        GIT_REPOSITORY https://github.com/glfw/glfw.git
        GIT_TAG        3.3.8
    )
    FetchContent_MakeAvailable(glfw)
endif()

# GLAD (从源码构建)
set(GLAD_DIR ${CMAKE_SOURCE_DIR}/third_party/glad)
if(NOT EXISTS ${GLAD_DIR}/src/glad.c)
    message(STATUS "GLAD not found, downloading...")
    file(DOWNLOAD
        "https://raw.githubusercontent.com/Dav1dde/glad/v0.1.36/include/glad/glad.h"
        "${GLAD_DIR}/include/glad/glad.h"
    )
    file(DOWNLOAD
        "https://raw.githubusercontent.com/Dav1dde/glad/v0.1.36/include/KHR/khrplatform.h"
        "${GLAD_DIR}/include/KHR/khrplatform.h"
    )
    # 需要手动生成 glad.c，或者使用预生成版本
endif()

add_library(glad STATIC ${GLAD_DIR}/src/glad.c)
target_include_directories(glad PUBLIC ${GLAD_DIR}/include)

# GLM
find_package(glm QUIET)
if(NOT glm_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        glm
        GIT_REPOSITORY https://github.com/g-truc/glm.git
        GIT_TAG        0.9.9.8
    )
    FetchContent_MakeAvailable(glm)
endif()

# 着色器源文件 (复制到构建目录)
file(GLOB_RECURSE SHADER_FILES
    "${CMAKE_SOURCE_DIR}/shaders/glsl/*.glsl"
    "${CMAKE_SOURCE_DIR}/shaders/hlsl/*.hlsl"
)

# 核心库
add_library(gpu_shader_lib STATIC
    src/core/shader_loader.cpp
    src/utils/mesh_generator.cpp
)

target_include_directories(gpu_shader_lib PUBLIC
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src/utils
)

target_link_libraries(gpu_shader_lib PUBLIC
    glad
    glm::glm
    OpenGL::GL
)

# 演示程序
if(BUILD_DEMOS)
    # 基础渲染演示
    add_executable(demo_basic_rendering
        examples/basic_rendering.cpp
    )
    target_link_libraries(demo_basic_rendering PRIVATE
        gpu_shader_lib
        glfw
    )

    # 后处理演示
    add_executable(demo_postprocess
        examples/postprocess.cpp
    )
    target_link_libraries(demo_postprocess PRIVATE
        gpu_shader_lib
        glfw
    )

    # PBR 渲染演示
    add_executable(demo_pbr
        examples/pbr_rendering.cpp
    )
    target_link_libraries(demo_pbr PRIVATE
        gpu_shader_lib
        glfw
    )

    # 粒子系统演示
    add_executable(demo_particles
        examples/particle_system.cpp
    )
    target_link_libraries(demo_particles PRIVATE
        gpu_shader_lib
        glfw
    )

    # 水面渲染演示
    add_executable(demo_water
        examples/water_rendering.cpp
    )
    target_link_libraries(demo_water PRIVATE
        gpu_shader_lib
        glfw
    )
endif()

# 复制着色器到构建目录
add_custom_target(copy_shaders ALL
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_SOURCE_DIR}/shaders
    ${CMAKE_BINARY_DIR}/shaders
    COMMENT "Copying shaders to build directory"
)

# 安装
install(TARGETS gpu_shader_lib
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/ DESTINATION include)
install(DIRECTORY shaders/ DESTINATION shaders)
