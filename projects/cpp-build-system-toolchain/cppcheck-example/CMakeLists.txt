cmake_minimum_required(VERSION 3.16)

# ============================================================================
# Cppcheck 静态分析示例
# 本文件展示如何集成 Cppcheck 进行代码静态分析
# ============================================================================

project(CppcheckExample
    VERSION 1.0.0
    DESCRIPTION "Cppcheck 静态分析示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. 查找 Cppcheck
# ============================================================================
find_program(CPPCHECK cppcheck)

# ============================================================================
# 2. 创建目标
# ============================================================================
add_executable(cppcheck_demo src/cppcheck_demo.cpp)

# ============================================================================
# 3. 集成 Cppcheck
# ============================================================================
if(CPPCHECK)
    # 方法1: 使用 CMAKE_CXX_CPPCHECK (CMake 3.10+)
    set(CMAKE_CXX_CPPCHECK
        ${CPPCHECK};
        --enable=all;
        --suppress=missingIncludeSystem;
        --inline-suppr;
        --std=c++17;
    )

    # 方法2: 自定义目标
    file(GLOB_RECURSE SOURCE_FILES
        ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp
    )

    add_custom_target(run-cppcheck
        COMMAND ${CPPCHECK}
            --enable=all
            --suppress=missingIncludeSystem
            --inline-suppr
            --std=c++17
            --output-file=${CMAKE_BINARY_DIR}/cppcheck_report.txt
            ${SOURCE_FILES}
        COMMENT "Running Cppcheck on all source files"
    )

    # 方法3: 使用 CTest 运行 Cppcheck
    find_program(CPPCHECK cppcheck)
    add_test(
        NAME cppcheck_test
        COMMAND ${CPPCHECK}
            --enable=all
            --suppress=missingIncludeSystem
            --std=c++17
            --error-exitcode=1
            ${SOURCE_FILES}
    )
endif()

# ============================================================================
# 4. 生成 compile_commands.json
# ============================================================================
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
