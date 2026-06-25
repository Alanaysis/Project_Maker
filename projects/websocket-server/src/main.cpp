/**
 * @file main.cpp
 * @brief WebSocket 服务器演示程序
 *
 * 演示 WebSocket 服务器的基本功能，包括：
 * - 服务器启动和配置
 * - 连接管理
 * - 消息路由
 * - 房间系统
 * - 心跳检测
 */

#include "websocket/server.h"
#include <iostream>
#include <signal.h>

// 全局服务器指针（用于信号处理）
static ws::Server* g_server = nullptr;

/**
 * @brief 信号处理函数
 */
void signal_handler(int sig) {
    if (g_server) {
        std::cout << "\nReceived signal " << sig << ", shutting down..." << std::endl;
        g_server->stop();
    }
}

/**
 * @brief 主函数
 */
int main(int argc, char* argv[]) {
    // 配置服务器
    ws::ServerConfig config;
    config.host = "0.0.0.0";
    config.port = 8080;
    config.max_connections = 1024;
    config.heartbeat_interval_ms = 30000;
    config.heartbeat_timeout_ms = 60000;
    config.max_message_size = 1048576;

    // 解析命令行参数
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            config.port = static_cast<uint16_t>(std::stoi(argv[++i]));
        } else if (arg == "--host" && i + 1 < argc) {
            config.host = argv[++i];
        } else if (arg == "--help") {
            std::cout << "WebSocket Server" << std::endl;
            std::cout << "Usage: " << argv[0] << " [options]" << std::endl;
            std::cout << "Options:" << std::endl;
            std::cout << "  --port <port>  Server port (default: 8080)" << std::endl;
            std::cout << "  --host <host>  Server host (default: 0.0.0.0)" << std::endl;
            std::cout << "  --help         Show this help" << std::endl;
            return 0;
        }
    }

    // 创建服务器
    ws::Server server(config);
    g_server = &server;

    // 设置信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 设置房间管理器
    auto& room_mgr = server.room_manager();

    // 设置消息路由器
    auto& router = server.router();

    // 注册默认路由
    router.on("default", "message", [&room_mgr](const ws::RouteContext& ctx) {
        std::string text = ctx.message.text();
        std::cout << "Received message from " << ctx.connection->id()
                  << ": " << text << std::endl;

        // 广播消息到所有连接
        // 这里只是简单回显
        ctx.reply("{\"type\":\"echo\",\"data\":\"" + text + "\"}");
    });

    // 注册聊天路由
    router.on("chat", "join", [&room_mgr](const ws::RouteContext& ctx) {
        auto room = ws::SimpleJson::get(ctx.message.text(), "room");
        if (room) {
            room_mgr.join_room(ctx.connection, *room);
            ctx.reply("{\"type\":\"chat\",\"action\":\"joined\",\"room\":\"" + *room + "\"}");
            room_mgr.broadcast_to_room(*room,
                "{\"type\":\"chat\",\"action\":\"user_joined\",\"user\":\"" +
                std::to_string(ctx.connection->id()) + "\"}");
        }
    });

    router.on("chat", "leave", [&room_mgr](const ws::RouteContext& ctx) {
        auto room = ws::SimpleJson::get(ctx.message.text(), "room");
        if (room) {
            room_mgr.broadcast_to_room(*room,
                "{\"type\":\"chat\",\"action\":\"user_left\",\"user\":\"" +
                std::to_string(ctx.connection->id()) + "\"}");
            room_mgr.leave_room(ctx.connection, *room);
            ctx.reply("{\"type\":\"chat\",\"action\":\"left\",\"room\":\"" + *room + "\"}");
        }
    });

    router.on("chat", "message", [&room_mgr](const ws::RouteContext& ctx) {
        auto room = ws::SimpleJson::get(ctx.message.text(), "room");
        auto message = ws::SimpleJson::get(ctx.message.text(), "message");
        if (room && message) {
            std::string json = "{\"type\":\"chat\",\"action\":\"message\","
                              "\"room\":\"" + *room + "\","
                              "\"user\":\"" + std::to_string(ctx.connection->id()) + "\","
                              "\"message\":\"" + *message + "\"}";
            room_mgr.broadcast_to_room(*room, json);
        }
    });

    // 注册房间路由
    router.on("room", "list", [&room_mgr](const ws::RouteContext& ctx) {
        auto rooms = room_mgr.room_names();
        std::string json = "{\"type\":\"room\",\"action\":\"list\",\"rooms\":[";
        for (size_t i = 0; i < rooms.size(); ++i) {
            if (i > 0) json += ",";
            json += "\"" + rooms[i] + "\"";
        }
        json += "]}";
        ctx.reply(json);
    });

    // 设置连接事件回调
    server.set_on_open([](ws::ConnectionPtr conn) {
        std::cout << "Connection " << conn->id() << " opened from "
                  << conn->remote_address() << ":" << conn->remote_port() << std::endl;

        // 发送欢迎消息
        std::string welcome = "{\"type\":\"welcome\","
                             "\"id\":" + std::to_string(conn->id()) + ","
                             "\"message\":\"Welcome to WebSocket Server!\"}";
        conn->send_text(welcome);
    });

    server.set_on_close([](ws::ConnectionPtr conn, ws::CloseCode code, const std::string& reason) {
        std::cout << "Connection " << conn->id() << " closed with code "
                  << static_cast<int>(code) << ": " << reason << std::endl;
    });

    server.set_on_error([](ws::ConnectionPtr conn, const std::string& error) {
        std::cerr << "Connection " << conn->id() << " error: " << error << std::endl;
    });

    // 启动服务器
    if (!server.start()) {
        std::cerr << "Failed to start server" << std::endl;
        return 1;
    }

    std::cout << "WebSocket server running on ws://" << config.host << ":" << config.port << std::endl;
    std::cout << "Press Ctrl+C to stop" << std::endl;

    // 运行事件循环
    server.run();

    std::cout << "Server stopped" << std::endl;
    return 0;
}
