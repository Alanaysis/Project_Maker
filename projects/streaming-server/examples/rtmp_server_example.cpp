/**
 * @file rtmp_server_example.cpp
 * @brief RTMP 服务器示例
 *
 * 演示如何使用 RTMP 服务器接收推流。
 */

#include "streaming/protocol/rtmp_server.hpp"
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

    auto logger = LogManager::instance().get_logger("RTMPExample");

    // 设置信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 创建 RTMP 服务器
    RtmpServer server;

    // 设置回调
    server.set_connection_callback(
        [logger](uint64_t session_id, bool connected) {
            if (connected) {
                STREAMING_LOG_INFO(logger, "Client connected: " + std::to_string(session_id));
            } else {
                STREAMING_LOG_INFO(logger, "Client disconnected: " + std::to_string(session_id));
            }
        }
    );

    server.set_frame_callback(
        [logger](MediaFramePtr frame) {
            STREAMING_LOG_DEBUG(logger, "Received frame: type=" +
                std::to_string(static_cast<int>(frame->type)) +
                ", size=" + std::to_string(frame->data.size()));
        }
    );

    // 启动服务器
    std::string host = "0.0.0.0";
    uint16_t port = 1935;

    if (argc >= 2) {
        port = static_cast<uint16_t>(std::atoi(argv[1]));
    }

    STREAMING_LOG_INFO(logger, "Starting RTMP server on " + host + ":" + std::to_string(port));

    if (!server.start(host, port)) {
        STREAMING_LOG_ERROR(logger, "Failed to start RTMP server");
        return 1;
    }

    STREAMING_LOG_INFO(logger, "RTMP server started. Press Ctrl+C to stop.");
    STREAMING_LOG_INFO(logger, "Use OBS or FFmpeg to push stream:");
    STREAMING_LOG_INFO(logger, "  ffmpeg -re -i input.mp4 -c copy -f flv rtmp://localhost:" +
                      std::to_string(port) + "/live/stream");

    // 主循环
    while (g_running) {
        std::this_thread::sleep_for(std::chrono::seconds(1));

        // 打印统计信息
        STREAMING_LOG_INFO(logger, "Active sessions: " + std::to_string(server.get_session_count()));
    }

    // 停止服务器
    STREAMING_LOG_INFO(logger, "Stopping RTMP server...");
    server.stop();

    STREAMING_LOG_INFO(logger, "RTMP server stopped.");
    return 0;
}
