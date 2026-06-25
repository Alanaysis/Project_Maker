cmake_minimum_required(VERSION 3.20)

# ============================================================================
# vcpkg 包管理器示例
# 本文件展示如何使用 vcpkg 管理 C++ 依赖
#
# 使用方法:
#   1. 安装 vcpkg:
#      git clone https://github.com/microsoft/vcpkg.git
#      cd vcpkg && ./bootstrap-vcpkg.sh
#
#   2. 配置项目:
#      cmake -B build -DCMAKE_TOOLCHAIN_FILE=[vcpkg-root]/scripts/buildsystems/vcpkg.cmake
#
#   3. 构建项目:
#      cmake --build build
# ============================================================================

project(VcpkgExample
    VERSION 1.0.0
    DESCRIPTION "vcpkg 包管理器示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找 vcpkg 安装的包
find_package(fmt CONFIG REQUIRED)
find_package(spdlog CONFIG REQUIRED)
find_package(nlohmann_json CONFIG REQUIRED)

# 创建可执行文件
add_executable(vcpkg_demo src/vcpkg_demo.cpp)

target_link_libraries(vcpkg_demo
    PRIVATE
        fmt::fmt
        spdlog::spdlog
        nlohmann_json::nlohmann_json
)
