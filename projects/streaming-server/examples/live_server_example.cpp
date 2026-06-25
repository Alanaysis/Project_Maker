/**
 * @file live_server_example.cpp
 * @brief 直播服务器示例
 *
 * 演示如何使用直播服务器进行实时流媒体直播。
 */

#include "streaming/application/live_server.hpp"
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

    auto logger = LogManager::instance().get_logger("LiveExample");

    // 设置信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 配置服务器
    ServerConfig config;
    config.host = "0.0.0.0";
    config.rtmp_port = 1935;
    config.http_port = 8080;
    config.max_connections = 1000;
    config.enable_hls = true;
    config.hls_path = "./hls";

    // 创建直播服务器
    LiveServer server;

    // 设置回调
    server.set_stream_state_callback(
        [logger](const std::string& stream_name, LiveStreamState state) {
            STREAMING_LOG_INFO(logger, "Stream state changed: " + stream_name +
                              " -> " + std::to_string(static_cast<int>(state)));
        }
    );

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

    STREAMING_LOG_INFO(logger, "Live server started.");
    STREAMING_LOG_INFO(logger, "RTMP: rtmp://localhost:" + std::to_string(config.rtmp_port) + "/live/stream");
    STREAMING_LOG_INFO(logger, "HLS: http://localhost:" + std::to_string(config.http_port) + "/live/playlist.m3u8");

    // 创建直播流
    server.get_stream_manager().create_stream("stream1", "stream_key_123");

    // 主循环
    while (g_running) {
        std::this_thread::sleep_for(std::chrono::seconds(5));

        // 打印服务器信息
        STREAMING_LOG_INFO(logger, server.get_server_info());
    }

    // 停止服务器
    STREAMING_LOG_INFO(logger, "Stopping server...");
    server.stop();

    STREAMING_LOG_INFO(logger, "Server stopped.");
    return 0;
}
