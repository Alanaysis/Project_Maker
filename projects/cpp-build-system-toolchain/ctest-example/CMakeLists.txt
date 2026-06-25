cmake_minimum_required(VERSION 3.16)

# ============================================================================
# CTest 集成示例
# 本文件展示如何使用 CMake CTest 进行测试管理
# ============================================================================

project(CtestExample
    VERSION 1.0.0
    DESCRIPTION "CTest 集成示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. 启用测试
# ============================================================================
enable_testing()

# ============================================================================
# 2. 创建测试用的库
# ============================================================================
add_library(math_lib STATIC src/math_lib.cpp)
target_include_directories(math_lib PUBLIC include)

# ============================================================================
# 3. 创建被测试的程序
# ============================================================================
add_executable(math_app src/math_app.cpp)
target_include_directories(math_app PRIVATE include)
target_link_libraries(math_app PRIVATE math_lib)

# ============================================================================
# 4. 添加测试
# ============================================================================

# 基本测试（无参数显示用法，预期失败）
add_test(NAME basic_test COMMAND math_app)
set_tests_properties(basic_test PROPERTIES
    TIMEOUT 10
    LABELS "basic"
    WILL_FAIL TRUE
)

# 测试输入输出
add_test(NAME test_add COMMAND math_app add 2 3)
set_tests_properties(test_add PROPERTIES
    PASS_REGULAR_EXPRESSION "Result: 5"
    LABELS "arithmetic"
)

add_test(NAME test_subtract COMMAND math_app subtract 10 3)
set_tests_properties(test_subtract PROPERTIES
    PASS_REGULAR_EXPRESSION "Result: 7"
    LABELS "arithmetic"
)

add_test(NAME test_multiply COMMAND math_app multiply 4 5)
set_tests_properties(test_multiply PROPERTIES
    PASS_REGULAR_EXPRESSION "Result: 20"
    LABELS "arithmetic"
)

add_test(NAME test_divide COMMAND math_app divide 10 2)
set_tests_properties(test_divide PROPERTIES
    PASS_REGULAR_EXPRESSION "Result: 5"
    LABELS "arithmetic"
)

# 失败测试（测试错误处理）
add_test(NAME test_divide_by_zero COMMAND math_app divide 10 0)
set_tests_properties(test_divide_by_zero PROPERTIES
    WILL_FAIL TRUE
    LABELS "error"
)

# 条件测试
if(UNIX)
    add_test(NAME unix_test COMMAND math_app add 100 200)
    set_tests_properties(unix_test PROPERTIES
        PASS_REGULAR_EXPRESSION "Result: 300"
        LABELS "platform"
    )
endif()

# ============================================================================
# 5. 自定义测试脚本
# ============================================================================
add_test(
    NAME custom_test
    COMMAND ${CMAKE_COMMAND} -E echo "Running custom test"
)

# ============================================================================
# 6. 测试套件
# ============================================================================
# 使用标签组织测试
# ctest -L basic      - 运行基本测试
# ctest -L arithmetic - 运行算术测试
# ctest -L error      - 运行错误测试

# ============================================================================
# 7. 测试配置
# ============================================================================
# 设置测试处理器数量
set(CTEST_PARALLEL_LEVEL 4)

# 设置测试超时
set(CTEST_TEST_TIMEOUT 60)
