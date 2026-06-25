cmake_minimum_required(VERSION 3.20)

# ============================================================================
# CMake FetchContent 示例
# 本文件展示如何使用 FetchContent 拉取第三方依赖
#
# FetchContent 优势:
# - 无需预安装包管理器
# - 与主项目一起编译
# - 版本控制精确
# - 跨平台兼容
# ============================================================================

project(FetchContentExample
    VERSION 1.0.0
    DESCRIPTION "CMake FetchContent 示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)

# ============================================================================
# 1. 拉取 fmt 库
# ============================================================================
FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 10.1.1
)

# 设置 fmt 选项
set(FMT_DOC OFF CACHE BOOL "" FORCE)
set(FMT_TEST OFF CACHE BOOL "" FORCE)

# ============================================================================
# 2. 拉取 spdlog 库
# ============================================================================
FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG v1.12.0
)

# 设置 spdlog 选项
set(SPDLOG_BUILD_EXAMPLE OFF CACHE BOOL "" FORCE)
set(SPDLOG_BUILD_TESTS OFF CACHE BOOL "" FORCE)

# ============================================================================
# 3. 拉取 nlohmann/json 库
# ============================================================================
FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
)

# 设置 json 选项
set(JSON_BuildTests OFF CACHE BOOL "" FORCE)

# ============================================================================
# 4. 拉取 Google Test
# ============================================================================
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)

# ============================================================================
# 5. 执行拉取
# ============================================================================
FetchContent_MakeAvailable(fmt spdlog nlohmann_json googletest)

# ============================================================================
# 6. 创建主程序
# ============================================================================
add_executable(fetchcontent_demo src/fetchcontent_demo.cpp)

target_link_libraries(fetchcontent_demo
    PRIVATE
        fmt::fmt
        spdlog::spdlog
        nlohmann_json::nlohmann_json
)

# ============================================================================
# 7. 创建测试
# ============================================================================
add_executable(fetchcontent_tests tests/test_main.cpp)

target_link_libraries(fetchcontent_tests
    PRIVATE
        GTest::gtest_main
        fmt::fmt
)

enable_testing()
add_test(NAME fetchcontent_tests COMMAND fetchcontent_tests)
