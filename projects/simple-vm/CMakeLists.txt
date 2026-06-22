cmake_minimum_required(VERSION 3.10)
project(simple-vm VERSION 1.0.0 LANGUAGES C CXX ASM)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# Debug 模式选项
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_options(-g -O0)
    add_definitions(-DDEBUG)
else()
    add_compile_options(-O2)
endif()

# 包含目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# 源文件
set(SOURCES
    src/vm.cpp
    src/vcpu.cpp
    src/io.cpp
)

# 创建静态库
add_library(simple_vm_lib STATIC ${SOURCES})
target_include_directories(simple_vm_lib PUBLIC ${CMAKE_SOURCE_DIR}/include)

# 创建可执行文件
add_executable(simple-vm src/main.cpp)
target_link_libraries(simple-vm simple_vm_lib)

# 测试
enable_testing()

# 测试源文件
set(TEST_SOURCES
    tests/test_vm.cpp
    tests/test_io.cpp
)

# 创建测试可执行文件
add_executable(simple_vm_tests ${TEST_SOURCES})
target_link_libraries(simple_vm_tests simple_vm_lib)

# 添加测试
add_test(NAME VMTests COMMAND simple_vm_tests)

# 安装目标
install(TARGETS simple-vm DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)

# 示例程序（需要 nasm 汇编器）
find_program(NASM nasm)
if(NASM)
    # 查找示例汇编文件
    file(GLOB EXAMPLE_ASM examples/*.asm)

    foreach(ASM_FILE ${EXAMPLE_ASM})
        # 获取文件名（不含扩展名）
        get_filename_component(EXAMPLE_NAME ${ASM_FILE} NAME_WE)

        # 生成二进制文件
        set(BIN_FILE ${CMAKE_BINARY_DIR}/examples/${EXAMPLE_NAME}.bin)

        # 添加自定义命令
        add_custom_command(
            OUTPUT ${BIN_FILE}
            COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/examples
            COMMAND ${NASM} -f bin ${ASM_FILE} -o ${BIN_FILE}
            DEPENDS ${ASM_FILE}
            COMMENT "Assembling ${ASM_FILE}"
        )

        # 添加自定义目标
        add_custom_target(example_${EXAMPLE_NAME} DEPENDS ${BIN_FILE})

        # 添加到默认目标
        add_dependencies(simple-vm example_${EXAMPLE_NAME})
    endforeach()
else()
    message(WARNING "NASM not found, example programs will not be built")
endif()

# 打印配置信息
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "Install prefix: ${CMAKE_INSTALL_PREFIX}")
