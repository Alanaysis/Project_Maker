cmake_minimum_required(VERSION 3.16)
project(http2-server VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准设置
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# 源文件列表
set(SOURCES
    src/http2_frame.cpp
    src/http2_hpack.cpp
    src/http2_stream.cpp
    src/http2_request.cpp
    src/http2_response.cpp
    src/http2_connection.cpp
    src/http2_server.cpp
)

# 头文件目录
include_directories(include)

# 主库
add_library(http2_lib STATIC ${SOURCES})

# 示例程序：基本 HTTP/2 服务器
add_executable(http2_server_example examples/http2_server_example.cpp)
target_link_libraries(http2_server_example http2_lib pthread)

# 示例程序：静态文件服务器
add_executable(static_file_server examples/static_file_server.cpp)
target_link_libraries(static_file_server http2_lib pthread)

# 示例程序：API 服务器
add_executable(api_server examples/api_server.cpp)
target_link_libraries(api_server http2_lib pthread)

# 示例程序：Server-Sent Events
add_executable(sse_server examples/sse_server.cpp)
target_link_libraries(sse_server http2_lib pthread)

# 示例程序：反向代理
add_executable(reverse_proxy examples/reverse_proxy.cpp)
target_link_libraries(reverse_proxy http2_lib pthread)

# 测试
enable_testing()

add_executable(test_frame tests/test_frame.cpp)
target_link_libraries(test_frame http2_lib)
add_test(NAME TestFrame COMMAND test_frame)

add_executable(test_hpack tests/test_hpack.cpp)
target_link_libraries(test_hpack http2_lib)
add_test(NAME TestHPACK COMMAND test_hpack)

add_executable(test_stream tests/test_stream.cpp)
target_link_libraries(test_stream http2_lib)
add_test(NAME TestStream COMMAND test_stream)

add_executable(test_request_response tests/test_request_response.cpp)
target_link_libraries(test_request_response http2_lib)
add_test(NAME TestRequestResponse COMMAND test_request_response)

# 安装
install(TARGETS http2_lib
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)

install(DIRECTORY include/ DESTINATION include)

install(TARGETS http2_server_example static_file_server api_server sse_server reverse_proxy
    RUNTIME DESTINATION bin
)

# 打印配置信息
message(STATUS "HTTP/2 Server Configuration:")
message(STATUS "  C++ Standard: C++${CMAKE_CXX_STANDARD}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Install Prefix: ${CMAKE_INSTALL_PREFIX}")
