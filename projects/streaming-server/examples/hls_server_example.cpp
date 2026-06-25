/**
 * @file hls_server_example.cpp
 * @brief HLS 服务器示例
 *
 * 演示如何使用 HLS 服务器进行流媒体分发。
 */

#include "streaming/protocol/hls_server.hpp"
#include "streaming/monitor/logger.hpp"

#include <iostream>
#include <signal.h>
#include <atomic>

using namespace streaming;

std::atomic<bool> g_running{true};

void signal_handler(int sig) {
    g_running = false;
}

int main(int argc, char* argv[]) {
    // 初始化日志
    LogManager::instance().initialize(LogLevel::Info, "", true);

    auto logger = LogManager::instance().get_logger("HLSExample");

    // 设置信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 创建 HLS 服务器
    HlsServer server;

    // 配置
    server.set_segment_duration(6.0);  // 6秒切片
    server.set_segment_count(5);        // 保留5个切片
    server.set_output_path("./hls_output");

    // 添加流
    MediaParams params;
    params.video.codec = VideoCodec::H264;
    params.video.width = 1280;
    params.video.height = 720;
    params.video.framerate = 30.0;
    params.video.bitrate = 2000000;
    params.audio.codec = AudioCodec::AAC;
    params.audio.sample_rate = 44100;
    params.audio.channels = 2;
    params.audio.bitrate = 128000;

    server.add_stream("live", params);

    // 启动服务器
    std::string host = "0.0.0.0";
    uint16_t port = 8080;

    if (argc >= 2) {
        port = static_cast<uint16_t>(std::atoi(argv[1]));
    }

    STREAMING_LOG_INFO(logger, "Starting HLS server on " + host + ":" + std::to_string(port));

    if (!server.start(host, port)) {
        STREAMING_LOG_ERROR(logger, "Failed to start HLS server");
        return 1;
    }

    STREAMING_LOG_INFO(logger, "HLS server started.");
    STREAMING_LOG_INFO(logger, "Access stream at: http://localhost:" +
                      std::to_string(port) + "/live/playlist.m3u8");

    // 主循环
    while (g_running) {
        std::this_thread::sleep_for(std::chrono::seconds(1));

        // 模拟接收媒体帧
        MediaFrame frame;
        frame.type = FrameType::VideoKeyFrame;
        frame.media_type = MediaType::Video;
        frame.data.resize(1024, 0);  // 模拟数据
        frame.is_keyframe = true;
        frame.pts = std::chrono::steady_clock::now().time_since_epoch().count() / 1000000;

        server.push_frame("live", frame);

        STREAMING_LOG_INFO(logger, "Viewers: " + std::to_string(server.get_viewer_count("live")));
    }

    // 停止服务器
    STREAMING_LOG_INFO(logger, "Stopping HLS server...");
    server.stop();

    STREAMING_LOG_INFO(logger, "HLS server stopped.");
    return 0;
}
