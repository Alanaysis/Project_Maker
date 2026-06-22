cmake_minimum_required(VERSION 3.15)
project(VRApplication VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 构建类型
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# 编译选项
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -DDEBUG")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")

# 选项
option(BUILD_TESTS "Build unit tests" ON)
option(BUILD_EXAMPLES "Build example programs" ON)
option(USE_OPENXR "Enable OpenXR support" OFF)
option(USE_DESKTOP_MODE "Enable desktop simulation mode" ON)

# 查找依赖
find_package(OpenGL REQUIRED)

# 查找 GLFW
find_package(glfw3 3.3 QUIET)
if(NOT glfw3_FOUND)
    # 尝试使用 pkg-config
    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(GLFW3 glfw3)
    endif()
endif()

# 查找 GLEW
find_package(GLEW QUIET)
if(NOT GLEW_FOUND)
    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(GLEW glew)
    endif()
endif()

# 查找 GLM
find_package(glm QUIET)
if(NOT glm_FOUND)
    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(GLM glm)
    endif()
endif()

# OpenXR（可选）
if(USE_OPENXR)
    find_package(OpenXR QUIET)
    if(NOT OpenXR_FOUND)
        message(WARNING "OpenXR not found, disabling OpenXR support")
        set(USE_OPENXR OFF)
    endif()
endif()

# 源文件
set(CORE_SOURCES
    src/core/Engine.cpp
    src/core/Application.cpp
)

set(RENDERING_SOURCES
    src/rendering/Renderer.cpp
    src/rendering/Shader.cpp
)

set(VR_SOURCES
    src/vr/VRSystem.cpp
)

set(INPUT_SOURCES
    src/input/InputManager.cpp
)

set(SCENE_SOURCES
    src/scene/Scene.cpp
)

# 所有源文件
set(ALL_SOURCES
    ${CORE_SOURCES}
    ${RENDERING_SOURCES}
    ${VR_SOURCES}
    ${INPUT_SOURCES}
    ${SCENE_SOURCES}
)

# 头文件目录
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# 主应用程序
add_executable(vr_application
    src/main.cpp
    ${ALL_SOURCES}
)

# 链接库
target_link_libraries(vr_application
    OpenGL::GL
)

if(glfw3_FOUND)
    target_link_libraries(vr_application glfw)
elseif(GLFW3_FOUND)
    target_link_libraries(vr_application ${GLFW3_LIBRARIES})
    target_include_directories(vr_application PRIVATE ${GLFW3_INCLUDE_DIRS})
else()
    message(FATAL_ERROR "GLFW not found")
endif()

if(GLEW_FOUND)
    target_link_libraries(vr_application GLEW::GLEW)
elseif(GLEW_LIBRARIES)
    target_link_libraries(vr_application ${GLEW_LIBRARIES})
    target_include_directories(vr_application PRIVATE ${GLEW_INCLUDE_DIRS})
else()
    message(FATAL_ERROR "GLEW not found")
endif()

if(glm_FOUND)
    target_link_libraries(vr_application glm::glm)
elseif(GLM_INCLUDE_DIRS)
    target_include_directories(vr_application PRIVATE ${GLM_INCLUDE_DIRS})
else()
    # 尝试直接包含
    find_path(GLM_INCLUDE_DIR glm/glm.hpp)
    if(GLM_INCLUDE_DIR)
        target_include_directories(vr_application PRIVATE ${GLM_INCLUDE_DIR})
    else()
        message(FATAL_ERROR "GLM not found")
    endif()
endif()

# OpenXR 支持
if(USE_OPENXR AND OpenXR_FOUND)
    target_link_libraries(vr_application OpenXR::openxr_loader)
    target_compile_definitions(vr_application PRIVATE USE_OPENXR)
    message(STATUS "OpenXR support enabled")
else()
    message(STATUS "OpenXR support disabled")
endif()

# 桌面模式
if(USE_DESKTOP_MODE)
    target_compile_definitions(vr_application PRIVATE USE_DESKTOP_MODE)
endif()

# 设置输出目录
set_target_properties(vr_application PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# 测试
if(BUILD_TESTS)
    enable_testing()

    # 数学测试
    add_executable(math_tests
        tests/math_tests.cpp
    )
    target_link_libraries(math_tests
        OpenGL::GL
    )
    if(glm_FOUND)
        target_link_libraries(math_tests glm::glm)
    elseif(GLM_INCLUDE_DIRS)
        target_include_directories(math_tests PRIVATE ${GLM_INCLUDE_DIRS})
    endif()
    target_include_directories(math_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
    add_test(NAME MathTests COMMAND math_tests)

    # 场景测试
    add_executable(scene_tests
        tests/scene_tests.cpp
        ${ALL_SOURCES}
    )
    target_link_libraries(scene_tests
        OpenGL::GL
    )
    if(glfw3_FOUND)
        target_link_libraries(scene_tests glfw)
    elseif(GLFW3_FOUND)
        target_link_libraries(scene_tests ${GLFW3_LIBRARIES})
        target_include_directories(scene_tests PRIVATE ${GLFW3_INCLUDE_DIRS})
    endif()
    if(GLEW_FOUND)
        target_link_libraries(scene_tests GLEW::GLEW)
    elseif(GLEW_LIBRARIES)
        target_link_libraries(scene_tests ${GLEW_LIBRARIES})
        target_include_directories(scene_tests PRIVATE ${GLEW_INCLUDE_DIRS})
    endif()
    if(glm_FOUND)
        target_link_libraries(scene_tests glm::glm)
    elseif(GLM_INCLUDE_DIRS)
        target_include_directories(scene_tests PRIVATE ${GLM_INCLUDE_DIRS})
    endif()
    if(USE_OPENXR AND OpenXR_FOUND)
        target_link_libraries(scene_tests OpenXR::openxr_loader)
        target_compile_definitions(scene_tests PRIVATE USE_OPENXR)
    endif()
    target_include_directories(scene_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
    add_test(NAME SceneTests COMMAND scene_tests)
endif()

# 示例程序
if(BUILD_EXAMPLES)
    add_executable(basic_scene
        examples/basic_scene.cpp
        ${ALL_SOURCES}
    )
    target_link_libraries(basic_scene
        OpenGL::GL
    )
    if(glfw3_FOUND)
        target_link_libraries(basic_scene glfw)
    elseif(GLFW3_FOUND)
        target_link_libraries(basic_scene ${GLFW3_LIBRARIES})
        target_include_directories(basic_scene PRIVATE ${GLFW3_INCLUDE_DIRS})
    endif()
    if(GLEW_FOUND)
        target_link_libraries(basic_scene GLEW::GLEW)
    elseif(GLEW_LIBRARIES)
        target_link_libraries(basic_scene ${GLEW_LIBRARIES})
        target_include_directories(basic_scene PRIVATE ${GLEW_INCLUDE_DIRS})
    endif()
    if(glm_FOUND)
        target_link_libraries(basic_scene glm::glm)
    elseif(GLM_INCLUDE_DIRS)
        target_include_directories(basic_scene PRIVATE ${GLM_INCLUDE_DIRS})
    endif()
    if(USE_OPENXR AND OpenXR_FOUND)
        target_link_libraries(basic_scene OpenXR::openxr_loader)
        target_compile_definitions(basic_scene PRIVATE USE_OPENXR)
    endif()
    target_include_directories(basic_scene PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
    set_target_properties(basic_scene PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin/examples
    )
endif()

# 安装
install(TARGETS vr_application
    RUNTIME DESTINATION bin
)

install(DIRECTORY include/
    DESTINATION include
    FILES_MATCHING PATTERN "*.h"
)

install(DIRECTORY shaders/
    DESTINATION share/vr_application/shaders
    FILES_MATCHING PATTERN "*.glsl"
)

# 打印配置信息
message(STATUS "=== VR Application Configuration ===")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Build tests: ${BUILD_TESTS}")
message(STATUS "Build examples: ${BUILD_EXAMPLES}")
message(STATUS "OpenXR support: ${USE_OPENXR}")
message(STATUS "Desktop mode: ${USE_DESKTOP_MODE}")
message(STATUS "===================================")