cmake_minimum_required(VERSION 3.16)
project(av-codec VERSION 1.0.0 LANGUAGES CXX)

# C++17/20 标准
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 查找依赖
find_package(Threads REQUIRED)

# 编译选项
option(BUILD_EXAMPLES "Build examples" ON)
option(BUILD_TESTS "Build tests" ON)

# 编译器选项
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
elseif(MSVC)
    add_compile_options(/W4)
endif()

# 头文件目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# 视频编解码源文件
set(VIDEO_SOURCES
    src/video/h264_encoder.cpp
    src/video/h264_decoder.cpp
    src/video/h265_encoder.cpp
    src/video/h265_decoder.cpp
    src/video/vp9_encoder.cpp
    src/video/vp9_decoder.cpp
    src/video/av1_encoder.cpp
    src/video/av1_decoder.cpp
    src/video/intra_prediction.cpp
    src/video/motion_estimation.cpp
    src/video/transform_coding.cpp
    src/video/quantization.cpp
    src/video/entropy_coding.cpp
)

# 音频编解码源文件
set(AUDIO_SOURCES
    src/audio/aac_encoder.cpp
    src/audio/aac_decoder.cpp
    src/audio/mp3_encoder.cpp
    src/audio/mp3_decoder.cpp
    src/audio/opus_encoder.cpp
    src/audio/opus_decoder.cpp
    src/audio/vorbis_encoder.cpp
    src/audio/vorbis_decoder.cpp
    src/audio/frequency_coding.cpp
    src/audio/temporal_coding.cpp
    src/audio/psychoacoustic_model.cpp
)

# 容器格式源文件
set(CONTAINER_SOURCES
    src/container/mp4_muxer.cpp
    src/container/mp4_demuxer.cpp
    src/container/mkv_muxer.cpp
    src/container/mkv_demuxer.cpp
    src/container/flv_muxer.cpp
    src/container/flv_demuxer.cpp
)

# 流媒体协议源文件
set(PROTOCOL_SOURCES
    src/protocol/rtmp_client.cpp
    src/protocol/hls_server.cpp
    src/protocol/dash_server.cpp
    src/protocol/webrtc_peer.cpp
)

# 性能优化源文件
set(OPTIMIZATION_SOURCES
    src/optimization/simd_utils.cpp
    src/optimization/multi_thread_encoder.cpp
    src/optimization/gpu_accelerator.cpp
    src/optimization/hw_codec.cpp
)

# 应用源文件
set(APPLICATION_SOURCES
    src/application/video_player.cpp
    src/application/video_transcoder.cpp
    src/application/live_streamer.cpp
    src/application/video_conference.cpp
)

# 主库
add_library(av-codec-core STATIC
    ${VIDEO_SOURCES}
    ${AUDIO_SOURCES}
    ${CONTAINER_SOURCES}
    ${PROTOCOL_SOURCES}
    ${OPTIMIZATION_SOURCES}
    ${APPLICATION_SOURCES}
)
target_link_libraries(av-codec-core PRIVATE Threads::Threads)

# 示例程序
if(BUILD_EXAMPLES)
    add_executable(video_encoder_example examples/video_encoder_example.cpp)
    target_link_libraries(video_encoder_example av-codec-core)

    add_executable(audio_encoder_example examples/audio_encoder_example.cpp)
    target_link_libraries(audio_encoder_example av-codec-core)

    add_executable(container_example examples/container_example.cpp)
    target_link_libraries(container_example av-codec-core)

    add_executable(streaming_example examples/streaming_example.cpp)
    target_link_libraries(streaming_example av-codec-core)

    add_executable(transcoder_example examples/transcoder_example.cpp)
    target_link_libraries(transcoder_example av-codec-core)

    add_executable(player_example examples/player_example.cpp)
    target_link_libraries(player_example av-codec-core)

    add_executable(conference_example examples/conference_example.cpp)
    target_link_libraries(conference_example av-codec-core)
endif()

# 测试
if(BUILD_TESTS)
    enable_testing()

    add_executable(test_video_codec tests/test_video_codec.cpp)
    target_link_libraries(test_video_codec av-codec-core)
    add_test(NAME VideoCodecTest COMMAND test_video_codec)

    add_executable(test_audio_codec tests/test_audio_codec.cpp)
    target_link_libraries(test_audio_codec av-codec-core)
    add_test(NAME AudioCodecTest COMMAND test_audio_codec)
endif()

# 安装
install(TARGETS av-codec-core
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)
install(DIRECTORY include/ DESTINATION include)
