cmake_minimum_required(VERSION 3.10)
project(ha-server VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -pthread")
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")
set(CMAKE_CXX_FLAGS_RELEASE "-O2")

# 源文件
set(SOURCES
    src/backend.cpp
    src/load_balancer.cpp
    src/health_checker.cpp
    src/connection_pool.cpp
    src/http_parser.cpp
    src/server.cpp
)

# 头文件目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# 主库
add_library(ha_server_lib STATIC ${SOURCES})
target_link_libraries(ha_server_lib pthread)

# 主程序
add_executable(ha_server src/main.cpp)
target_link_libraries(ha_server ha_server_lib pthread)

# 示例程序
add_executable(ha_server_example examples/simple_proxy.cpp)
target_link_libraries(ha_server_example ha_server_lib pthread)

# 测试程序
enable_testing()

add_executable(test_load_balancer tests/test_load_balancer.cpp)
target_link_libraries(test_load_balancer ha_server_lib pthread)
add_test(NAME test_load_balancer COMMAND test_load_balancer)

add_executable(test_health_checker tests/test_health_checker.cpp)
target_link_libraries(test_health_checker ha_server_lib pthread)
add_test(NAME test_health_checker COMMAND test_health_checker)

add_executable(test_connection_pool tests/test_connection_pool.cpp)
target_link_libraries(test_connection_pool ha_server_lib pthread)
add_test(NAME test_connection_pool COMMAND test_connection_pool)

add_executable(test_http_parser tests/test_http_parser.cpp)
target_link_libraries(test_http_parser ha_server_lib pthread)
add_test(NAME test_http_parser COMMAND test_http_parser)

# 所有测试
add_custom_target(tests
    DEPENDS test_load_balancer test_health_checker test_connection_pool test_http_parser
)

# 安装
install(TARGETS ha_server_lib
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)

install(DIRECTORY include/
    DESTINATION include/ha_server
    FILES_MATCHING PATTERN "*.h"
)
