/**
 * @file vod_server_example.cpp
 * @brief 点播服务器示例
 *
 * 演示如何使用点播服务器进行视频点播。
 */

#include "streaming/application/vod_server.hpp"
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

    auto logger = LogManager::instance().get_logger("VODExample");

    // 设置信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 配置服务器
    ServerConfig config;
    config.host = "0.0.0.0";
    config.http_port = 8080;
    config.enable_hls = true;
    config.enable_dash = true;
    config.recording_path = "./videos";
    config.hls_path = "./hls";
    config.dash_path = "./dash";

    // 创建点播服务器
    VodServer server;

    // 初始化服务器
    if (!server.initialize(config)) {
        STREAMING_LOG_ERROR(logger, "Failed to initialize server");
        return 1;
    }

    // 启动服务器
    if (!server.start()) {
        STREAMING_LOG_ERROR(logger, "Failed to start server");
        return 1;
    }

    STREAMING_LOG_INFO(logger, "VOD server started.");
    STREAMING_LOG_INFO(logger, "HLS: http://localhost:" + std::to_string(config.http_port));
    STREAMING_LOG_INFO(logger, "DASH: http://localhost:" + std::to_string(config.http_port + 1));

    // 上传视频（示例）
    if (argc >= 2) {
        std::string video_path = argv[1];
        std::string video_id = server.upload_video("Sample Video", video_path);

        if (!video_id.empty()) {
            STREAMING_LOG_INFO(logger, "Video uploaded: " + video_id);
            STREAMING_LOG_INFO(logger, "HLS URL: " + server.get_playback_url(video_id, ProtocolType::HLS));
            STREAMING_LOG_INFO(logger, "DASH URL: " + server.get_playback_url(video_id, ProtocolType::DASH));
        }
    }

    // 主循环
    while (g_running) {
        std::this_thread::sleep_for(std::chrono::seconds(5));

        // 打印统计信息
        STREAMING_LOG_INFO(logger, server.get_stats());
    }

    // 停止服务器
    STREAMING_LOG_INFO(logger, "Stopping server...");
    server.stop();

    STREAMING_LOG_INFO(logger, "Server stopped.");
    return 0;
}
