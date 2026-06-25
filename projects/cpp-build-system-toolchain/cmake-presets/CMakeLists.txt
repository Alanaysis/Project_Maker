cmake_minimum_required(VERSION 3.21)

# ============================================================================
# CMake Presets 示例
# 本文件展示 CMake Presets 的使用，包括：
# - configurePresets: 配置预设
# - buildPresets: 构建预设
# - testPresets: 测试预设
# ============================================================================

project(CMakePresets
    VERSION 1.0.0
    DESCRIPTION "CMake Presets 示例项目"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 创建可执行文件
add_executable(presets_demo src/presets_demo.cpp)

# 根据预设配置设置编译定义
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_definitions(presets_demo PRIVATE DEBUG_MODE)
endif()

if(ENABLE_SANITIZERS)
    target_compile_options(presets_demo PRIVATE -fsanitize=address,undefined)
    target_link_options(presets_demo PRIVATE -fsanitize=address,undefined)
endif()

# 测试
enable_testing()
add_test(NAME presets_demo_test COMMAND presets_demo)
