cmake_minimum_required(VERSION 3.20)

# ============================================================================
# 现代 CMake 项目模板
# 本文件展示一个完整的现代 CMake 项目结构
#
# 项目结构:
#   project-template/
#   ├── CMakeLists.txt          # 顶层 CMake
#   ├── CMakePresets.json        # 构建预设
#   ├── cmake/                   # CMake 模块
#   │   ├── CompilerWarnings.cmake
#   │   └── Sanitizers.cmake
#   ├── include/                 # 公共头文件
#   │   └── mylib/
#   ├── src/                     # 源代码
#   │   ├── CMakeLists.txt
#   │   └── library source files
#   ├── tests/                   # 测试代码
#   │   ├── CMakeLists.txt
#   │   └── test files
#   └── apps/                    # 应用程序
#       ├── CMakeLists.txt
#       └── app source files
# ============================================================================

# 读取版本号
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/VERSION" PROJECT_VERSION)
string(STRIP "${PROJECT_VERSION}" PROJECT_VERSION)

project(MyProject
    VERSION ${PROJECT_VERSION}
    DESCRIPTION "Modern C++ Project Template"
    LANGUAGES CXX
)

# ============================================================================
# 1. 项目选项
# ============================================================================
option(MYPROJECT_BUILD_TESTS "Build tests" ON)
option(MYPROJECT_BUILD_APPS "Build applications" ON)
option(MYPROJECT_INSTALL "Generate install targets" ON)
option(MYPROJECT_ENABLE_COVERAGE "Enable code coverage" OFF)
option(MYPROJECT_ENABLE_ASAN "Enable AddressSanitizer" OFF)
option(MYPROJECT_ENABLE_UBSAN "Enable UndefinedBehaviorSanitizer" OFF)

# ============================================================================
# 2. 包含 CMake 模块
# ============================================================================
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

include(CompilerWarnings)
include(Sanitizers)

# ============================================================================
# 3. 全局设置
# ============================================================================
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 生成 compile_commands.json
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# ============================================================================
# 4. 添加子目录
# ============================================================================
add_subdirectory(src)

if(MYPROJECT_BUILD_APPS)
    add_subdirectory(apps)
endif()

if(MYPROJECT_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# ============================================================================
# 5. 安装规则
# ============================================================================
if(MYPROJECT_INSTALL)
    include(GNUInstallDirs)
    include(CMakePackageConfigHelpers)

    # 生成配置文件
    configure_package_config_file(
        cmake/MyProjectConfig.cmake.in
        ${CMAKE_CURRENT_BINARY_DIR}/MyProjectConfig.cmake
        INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/MyProject
    )

    write_basic_package_version_file(
        ${CMAKE_CURRENT_BINARY_DIR}/MyProjectConfigVersion.cmake
        VERSION ${PROJECT_VERSION}
        COMPATIBILITY SameMajorVersion
    )

    install(FILES
        ${CMAKE_CURRENT_BINARY_DIR}/MyProjectConfig.cmake
        ${CMAKE_CURRENT_BINARY_DIR}/MyProjectConfigVersion.cmake
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/MyProject
    )
endif()

# ============================================================================
# 6. 打包支持
# ============================================================================
set(CPACK_PACKAGE_VENDOR "MyCompany")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY ${PROJECT_DESCRIPTION})
set(CPACK_PACKAGE_VERSION_MAJOR ${PROJECT_VERSION_MAJOR})
set(CPACK_PACKAGE_VERSION_MINOR ${PROJECT_VERSION_MINOR})
set(CPACK_PACKAGE_VERSION_PATCH ${PROJECT_VERSION_PATCH})
include(CPack)
