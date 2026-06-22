cmake_minimum_required(VERSION 3.16)
project(av-codec VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
elseif(MSVC)
    add_compile_options(/W4)
endif()

# 查找FFmpeg
find_package(PkgConfig REQUIRED)

# 尝试使用pkg-config查找FFmpeg
pkg_check_modules(AVCODEC libavcodec)
pkg_check_modules(AVFORMAT libavformat)
pkg_check_modules(AVUTIL libavutil)
pkg_check_modules(SWSCALE libswscale)
pkg_check_modules(SWRESAMPLE libswresample)

# 如果pkg-config失败，尝试手动查找
if(NOT AVCODEC_FOUND)
    message(STATUS "pkg-config not found for FFmpeg, trying manual detection...")

    # 查找头文件
    find_path(AVCODEC_INCLUDE_DIRS libavcodec/avcodec.h
        PATHS /usr/include /usr/local/include /usr/include/aarch64-linux-gnu)
    find_path(AVFORMAT_INCLUDE_DIRS libavformat/avformat.h
        PATHS /usr/include /usr/local/include /usr/include/aarch64-linux-gnu)
    find_path(AVUTIL_INCLUDE_DIRS libavutil/avutil.h
        PATHS /usr/include /usr/local/include /usr/include/aarch64-linux-gnu)
    find_path(SWSCALE_INCLUDE_DIRS libswscale/swscale.h
        PATHS /usr/include /usr/local/include /usr/include/aarch64-linux-gnu)
    find_path(SWRESAMPLE_INCLUDE_DIRS libswresample/swresample.h
        PATHS /usr/include /usr/local/include /usr/include/aarch64-linux-gnu)

    # 查找库文件
    find_library(AVCODEC_LIBRARIES avcodec
        PATHS /usr/lib /usr/local/lib /usr/lib/aarch64-linux-gnu)
    find_library(AVFORMAT_LIBRARIES avformat
        PATHS /usr/lib /usr/local/lib /usr/lib/aarch64-linux-gnu)
    find_library(AVUTIL_LIBRARIES avutil
        PATHS /usr/lib /usr/local/lib /usr/lib/aarch64-linux-gnu)
    find_library(SWSCALE_LIBRARIES swscale
        PATHS /usr/lib /usr/local/lib /usr/lib/aarch64-linux-gnu)
    find_library(SWRESAMPLE_LIBRARIES swresample
        PATHS /usr/lib /usr/local/lib /usr/lib/aarch64-linux-gnu)

    # 检查是否找到
    if(NOT AVCODEC_LIBRARIES OR NOT AVCODEC_INCLUDE_DIRS)
        message(FATAL_ERROR "FFmpeg libraries not found. Please install FFmpeg development packages:
        sudo apt install libavcodec-dev libavformat-dev libavutil-dev libswscale-dev libswresample-dev")
    endif()

    set(AVCODEC_FOUND TRUE)
    set(AVFORMAT_FOUND TRUE)
    set(AVUTIL_FOUND TRUE)
    set(SWSCALE_FOUND TRUE)
    set(SWRESAMPLE_FOUND TRUE)
endif()

# 头文件目录
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${AVCODEC_INCLUDE_DIRS}
    ${AVFORMAT_INCLUDE_DIRS}
    ${AVUTIL_INCLUDE_DIRS}
    ${SWSCALE_INCLUDE_DIRS}
    ${SWRESAMPLE_INCLUDE_DIRS}
)

# 库目录
link_directories(
    ${AVCODEC_LIBRARY_DIRS}
    ${AVFORMAT_LIBRARY_DIRS}
    ${AVUTIL_LIBRARY_DIRS}
    ${SWSCALE_LIBRARY_DIRS}
    ${SWRESAMPLE_LIBRARY_DIRS}
)

# 源文件
set(LIB_SOURCES
    src/video_encoder.cpp
    src/video_decoder.cpp
    src/audio_encoder.cpp
    src/audio_decoder.cpp
    src/muxer.cpp
    src/demuxer.cpp
    src/utils.cpp
)

# 创建静态库
add_library(avcodec_lib STATIC ${LIB_SOURCES})
target_link_libraries(avcodec_lib
    ${AVCODEC_LIBRARIES}
    ${AVFORMAT_LIBRARIES}
    ${AVUTIL_LIBRARIES}
    ${SWSCALE_LIBRARIES}
    ${SWRESAMPLE_LIBRARIES}
)

# 设置输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 示例程序
add_executable(video_encoder_example examples/video_encoder_example.cpp)
target_link_libraries(video_encoder_example avcodec_lib)

add_executable(audio_encoder_example examples/audio_encoder_example.cpp)
target_link_libraries(audio_encoder_example avcodec_lib)

add_executable(muxer_example examples/muxer_example.cpp)
target_link_libraries(muxer_example avcodec_lib)

# 测试
enable_testing()

add_executable(test_video_codec tests/test_video_codec.cpp)
target_link_libraries(test_video_codec avcodec_lib)
add_test(NAME test_video_codec COMMAND test_video_codec)

add_executable(test_audio_codec tests/test_audio_codec.cpp)
target_link_libraries(test_audio_codec avcodec_lib)
add_test(NAME test_audio_codec COMMAND test_audio_codec)

add_executable(test_muxer tests/test_muxer.cpp)
target_link_libraries(test_muxer avcodec_lib)
add_test(NAME test_muxer COMMAND test_muxer)

# 安装
install(TARGETS avcodec_lib
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)
install(DIRECTORY include/ DESTINATION include)
