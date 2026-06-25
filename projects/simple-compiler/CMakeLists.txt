cmake_minimum_required(VERSION 3.16)

# 项目名称和版本
project(SimpleCompiler
    VERSION 1.0.0
    DESCRIPTION "A simple compiler implementation in C++"
    LANGUAGES CXX
)

# C++标准设置
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror=return-type)
elseif(MSVC)
    add_compile_options(/W4 /WX)
endif()

# 构建类型设置
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")
set(CMAKE_CXX_FLAGS_RELEASE "-O3")

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 头文件目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# 源文件目录
set(SRC_DIR ${CMAKE_SOURCE_DIR}/src)

# ==================== 核心库 ====================

# 词法分析器
set(LEXER_SOURCES
    ${SRC_DIR}/lexer.cpp
)

# 语法分析器
set(PARSER_SOURCES
    ${SRC_DIR}/parser.cpp
)

# 语义分析器
set(SEMANTIC_SOURCES
    ${SRC_DIR}/semantic.cpp
)

# 中间代码生成器
set(IR_SOURCES
    ${SRC_DIR}/ir.cpp
)

# 优化器
set(OPTIMIZER_SOURCES
    ${SRC_DIR}/optimizer.cpp
)

# 代码生成器
set(CODEGEN_SOURCES
    ${SRC_DIR}/codegen.cpp
)

# 解释器
set(INTERPRETER_SOURCES
    ${SRC_DIR}/interpreter.cpp
)

# 所有核心源文件
set(CORE_SOURCES
    ${LEXER_SOURCES}
    ${PARSER_SOURCES}
    ${SEMANTIC_SOURCES}
    ${IR_SOURCES}
    ${OPTIMIZER_SOURCES}
    ${CODEGEN_SOURCES}
    ${INTERPRETER_SOURCES}
)

# 创建核心静态库
add_library(compiler_core STATIC ${CORE_SOURCES})
target_include_directories(compiler_core PUBLIC ${CMAKE_SOURCE_DIR}/include)

# ==================== 可执行文件 ====================

# 主编译器程序
add_executable(simple_compiler
    ${CMAKE_SOURCE_DIR}/examples/main.cpp
)
target_link_libraries(simple_compiler PRIVATE compiler_core)

# 计算器示例
add_executable(calculator
    ${CMAKE_SOURCE_DIR}/examples/calculator.cpp
)
target_link_libraries(calculator PRIVATE compiler_core)

# 脚本解释器示例
add_executable(script_interpreter
    ${CMAKE_SOURCE_DIR}/examples/script_interpreter.cpp
)
target_link_libraries(script_interpreter PRIVATE compiler_core)

# DSL示例
add_executable(dsl_example
    ${CMAKE_SOURCE_DIR}/examples/dsl_example.cpp
)
target_link_libraries(dsl_example PRIVATE compiler_core)

# ==================== 测试 ====================

# 测试源文件
set(TEST_SOURCES
    ${CMAKE_SOURCE_DIR}/tests/test_all.cpp
)

# 创建测试可执行文件
add_executable(compiler_tests ${TEST_SOURCES})
target_link_libraries(compiler_tests PRIVATE compiler_core)

# 启用测试
enable_testing()
add_test(NAME CompilerTests COMMAND compiler_tests)

# ==================== 安装 ====================

# 安装目标
install(TARGETS simple_compiler calculator script_interpreter dsl_example
    RUNTIME DESTINATION bin
)

install(TARGETS compiler_core
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)

# 安装头文件
install(DIRECTORY include/
    DESTINATION include
    FILES_MATCHING PATTERN "*.hpp"
)

# ==================== 文档 ====================

# 查找Doxygen
find_package(Doxygen QUIET)
if(DOXYGEN_FOUND)
    set(DOXYGEN_IN ${CMAKE_SOURCE_DIR}/docs/Doxyfile.in)
    set(DOXYGEN_OUT ${CMAKE_BINARY_DIR}/Doxyfile)

    configure_file(${DOXYGEN_IN} ${DOXYGEN_OUT} @ONLY)

    add_custom_target(doc
        COMMAND ${DOXYGEN_EXECUTABLE} ${DOXYGEN_OUT}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
        COMMENT "Generating API documentation with Doxygen"
        VERBATIM
    )
endif()

# ==================== 打包 ====================

include(CPack)

set(CPACK_PACKAGE_NAME "SimpleCompiler")
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "A simple compiler implementation")
set(CPACK_PACKAGE_VENDOR "Compiler Course")
set(CPACK_RESOURCE_FILE_LICENSE ${CMAKE_SOURCE_DIR}/LICENSE)
set(CPACK_RESOURCE_FILE_README ${CMAKE_SOURCE_DIR}/README.md)

# ==================== 打印配置信息 ====================

message(STATUS "")
message(STATUS "Simple Compiler Configuration:")
message(STATUS "  Build type:      ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ Compiler:    ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "  C++ Standard:    ${CMAKE_CXX_STANDARD}")
message(STATUS "  Install prefix:  ${CMAKE_INSTALL_PREFIX}")
message(STATUS "")
