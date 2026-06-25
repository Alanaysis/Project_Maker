cmake_minimum_required(VERSION 3.16)
project(streaming-server VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
elseif(MSVC)
    add_compile_options(/W4)
endif()

# 查找依赖
find_package(Threads REQUIRED)

# 尝试查找OpenSSL（可选）
find_package(OpenSSL QUIET)

# 头文件目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# 源文件
set(LIB_SOURCES
    src/protocol/rtmp_server.cpp
    src/protocol/rtsp_server.cpp
    src/protocol/hls_server.cpp
    src/protocol/dash_server.cpp
    src/protocol/webrtc_server.cpp
    src/media/video_transcoder.cpp
    src/media/audio_transcoder.cpp
    src/media/segment_generator.cpp
    src/media/playlist_generator.cpp
    src/media/recorder.cpp
    src/session/session_manager.cpp
    src/session/client_connection.cpp
    src/session/load_balancer.cpp
    src/core/async_io.cpp
    src/core/thread_pool.cpp
    src/core/cache_manager.cpp
    src/core/bandwidth_adaptor.cpp
    src/monitor/stats_collector.cpp
    src/monitor/logger.cpp
    src/application/live_server.cpp
    src/application/vod_server.cpp
    src/application/conference_server.cpp
    src/utils/buffer.cpp
    src/utils/timer.cpp
    src/utils/config.cpp
)

# 创建静态库
add_library(streaming_lib STATIC ${LIB_SOURCES})
target_link_libraries(streaming_lib Threads::Threads)

if(OPENSSL_FOUND)
    target_link_libraries(streaming_lib OpenSSL::SSL OpenSSL::Crypto)
    target_compile_definitions(streaming_lib PRIVATE HAVE_OPENSSL=1)
endif()

# 设置输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 创建目录
file(MAKE_DIRECTORY ${CMAKE_SOURCE_DIR}/src/protocol)
file(MAKE_DIRECTORY ${CMAKE_SOURCE_DIR}/src/media)
file(MAKE_DIRECTORY ${CMAKE_SOURCE_DIR}/src/session)
file(MAKE_DIRECTORY ${CMAKE_SOURCE_DIR}/src/core)
file(MAKE_DIRECTORY ${CMAKE_SOURCE_DIR}/src/monitor)
file(MAKE_DIRECTORY ${CMAKE_SOURCE_DIR}/src/application)
file(MAKE_DIRECTORY ${CMAKE_SOURCE_DIR}/src/utils)

# 示例程序
add_executable(rtmp_server_example examples/rtmp_server_example.cpp)
target_link_libraries(rtmp_server_example streaming_lib)

add_executable(hls_server_example examples/hls_server_example.cpp)
target_link_libraries(hls_server_example streaming_lib)

add_executable(live_server_example examples/live_server_example.cpp)
target_link_libraries(live_server_example streaming_lib)

add_executable(vod_server_example examples/vod_server_example.cpp)
target_link_libraries(vod_server_example streaming_lib)

# 测试
enable_testing()

add_executable(test_protocol tests/test_protocol.cpp)
target_link_libraries(test_protocol streaming_lib)
add_test(NAME test_protocol COMMAND test_protocol)

add_executable(test_session tests/test_session.cpp)
target_link_libraries(test_session streaming_lib)
add_test(NAME test_session COMMAND test_session)

add_executable(test_media tests/test_media.cpp)
target_link_libraries(test_media streaming_lib)
add_test(NAME test_media COMMAND test_media)

# 安装
install(TARGETS streaming_lib
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)
install(DIRECTORY include/ DESTINATION include)
