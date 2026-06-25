/**
 * @file chat_server.cpp
 * @brief 聊天服务器示例
 *
 * 演示一个完整的聊天服务器，支持：
 * - 多房间聊天
 * - 用户昵称
 * - 消息广播
 * - 在线用户列表
 *
 * 使用方式：
 *   编译: g++ -std=c++17 -I../include chat_server.cpp ../src/*.cpp -o chat_server
 *   运行: ./chat_server --port 8080
 *
 * 客户端测试:
 *   打开 examples/chat_client.html 连接 ws://localhost:8080
 */

#include "websocket/server.h"
#include <iostream>
#include <map>
#include <signal.h>

/**
 * @brief 用户信息
 */
struct UserInfo {
    std::string nickname;
    std::string current_room;
};

/**
 * @brief 聊天服务器
 */
class ChatServer {
public:
    ChatServer(uint16_t port = 8080) {
        ws::ServerConfig config;
        config.port = port;
        config.max_connections = 1000;
        config.heartbeat_interval_ms = 30000;
        config.heartbeat_timeout_ms = 60000;

        server_ = std::make_unique<ws::Server>(config);
        setup_handlers();
    }

    void run() {
        if (!server_->start()) {
            std::cerr << "Failed to start chat server" << std::endl;
            return;
        }

        std::cout << "Chat server running on ws://0.0.0.0:"
                  << server_->config().port << std::endl;
        std::cout << "Press Ctrl+C to stop" << std::endl;

        server_->run();
    }

    void stop() {
        server_->stop();
    }

private:
    void setup_handlers() {
        // 连接打开
        server_->set_on_open([this](ws::ConnectionPtr conn) {
            std::lock_guard<std::mutex> lock(users_mutex_);
            users_[conn->id()] = {"User_" + std::to_string(conn->id()), ""};
            std::cout << "User connected: " << conn->id() << std::endl;
        });

        // 连接关闭
        server_->set_on_close([this](ws::ConnectionPtr conn, ws::CloseCode code,
                                      const std::string& reason) {
            std::lock_guard<std::mutex> lock(users_mutex_);
            auto it = users_.find(conn->id());
            if (it != users_.end()) {
                if (!it->second.current_room.empty()) {
                    // 通知房间内其他用户
                    std::string msg = "{\"type\":\"system\",\"action\":\"user_left\","
                                     "\"user\":\"" + it->second.nickname + "\"}";
                    server_->room_manager().broadcast_to_room(it->second.current_room, msg);
                }
                std::cout << "User disconnected: " << it->second.nickname << std::endl;
                users_.erase(it);
            }
        });

        // 消息处理
        server_->set_on_message([this](ws::ConnectionPtr conn, const ws::Message& msg) {
            if (msg.type != ws::Opcode::Text) return;

            std::string text = msg.text();
            auto action = ws::SimpleJson::get(text, "action");

            if (!action) {
                send_error(conn, "Missing action field");
                return;
            }

            if (*action == "set_nickname") {
                handle_set_nickname(conn, text);
            } else if (*action == "join") {
                handle_join(conn, text);
            } else if (*action == "leave") {
                handle_leave(conn, text);
            } else if (*action == "message") {
                handle_message(conn, text);
            } else if (*action == "list_rooms") {
                handle_list_rooms(conn);
            } else if (*action == "list_users") {
                handle_list_users(conn, text);
            } else {
                send_error(conn, "Unknown action: " + *action);
            }
        });
    }

    void handle_set_nickname(ws::ConnectionPtr conn, const std::string& text) {
        auto nickname = ws::SimpleJson::get(text, "nickname");
        if (!nickname || nickname->empty()) {
            send_error(conn, "Invalid nickname");
            return;
        }

        std::lock_guard<std::mutex> lock(users_mutex_);
        auto it = users_.find(conn->id());
        if (it != users_.end()) {
            std::string old_nick = it->second.nickname;
            it->second.nickname = *nickname;

            // 如果在房间中，通知其他用户
            if (!it->second.current_room.empty()) {
                std::string msg = "{\"type\":\"system\",\"action\":\"nickname_changed\","
                                 "\"old\":\"" + old_nick + "\","
                                 "\"new\":\"" + *nickname + "\"}";
                server_->room_manager().broadcast_to_room(it->second.current_room, msg);
            }

            conn->send_text("{\"type\":\"success\",\"action\":\"set_nickname\","
                          "\"nickname\":\"" + *nickname + "\"}");
        }
    }

    void handle_join(ws::ConnectionPtr conn, const std::string& text) {
        auto room = ws::SimpleJson::get(text, "room");
        if (!room || room->empty()) {
            send_error(conn, "Invalid room name");
            return;
        }

        std::lock_guard<std::mutex> lock(users_mutex_);
        auto it = users_.find(conn->id());
        if (it == users_.end()) return;

        // 离开当前房间
        if (!it->second.current_room.empty()) {
            server_->room_manager().leave_room(conn, it->second.current_room);

            std::string leave_msg = "{\"type\":\"system\",\"action\":\"user_left\","
                                   "\"user\":\"" + it->second.nickname + "\"}";
            server_->room_manager().broadcast_to_room(it->second.current_room, leave_msg);
        }

        // 加入新房间
        server_->room_manager().join_room(conn, *room);
        it->second.current_room = *room;

        // 通知房间内其他用户
        std::string join_msg = "{\"type\":\"system\",\"action\":\"user_joined\","
                              "\"user\":\"" + it->second.nickname + "\"}";
        server_->room_manager().broadcast_to_room(*room, join_msg);

        // 发送成功响应
        conn->send_text("{\"type\":\"success\",\"action\":\"join\","
                       "\"room\":\"" + *room + "\"}");

        // 发送在线用户列表
        send_user_list(conn, *room);
    }

    void handle_leave(ws::ConnectionPtr conn, const std::string& text) {
        std::lock_guard<std::mutex> lock(users_mutex_);
        auto it = users_.find(conn->id());
        if (it == users_.end() || it->second.current_room.empty()) {
            send_error(conn, "Not in any room");
            return;
        }

        std::string room = it->second.current_room;
        server_->room_manager().leave_room(conn, room);
        it->second.current_room.clear();

        // 通知房间内其他用户
        std::string msg = "{\"type\":\"system\",\"action\":\"user_left\","
                         "\"user\":\"" + it->second.nickname + "\"}";
        server_->room_manager().broadcast_to_room(room, msg);

        conn->send_text("{\"type\":\"success\",\"action\":\"leave\","
                       "\"room\":\"" + room + "\"}");
    }

    void handle_message(ws::ConnectionPtr conn, const std::string& text) {
        auto message = ws::SimpleJson::get(text, "message");
        if (!message || message->empty()) {
            send_error(conn, "Empty message");
            return;
        }

        std::lock_guard<std::mutex> lock(users_mutex_);
        auto it = users_.find(conn->id());
        if (it == users_.end() || it->second.current_room.empty()) {
            send_error(conn, "Not in any room");
            return;
        }

        // 广播消息到房间
        std::string json = "{\"type\":\"message\","
                          "\"room\":\"" + it->second.current_room + "\","
                          "\"user\":\"" + it->second.nickname + "\","
                          "\"message\":\"" + *message + "\","
                          "\"timestamp\":" + std::to_string(ws::utils::timestamp_ms()) + "}";

        server_->room_manager().broadcast_to_room(it->second.current_room, json);
    }

    void handle_list_rooms(ws::ConnectionPtr conn) {
        auto rooms = server_->room_manager().room_names();
        std::string json = "{\"type\":\"rooms\",\"rooms\":[";
        for (size_t i = 0; i < rooms.size(); ++i) {
            if (i > 0) json += ",";
            json += "\"" + rooms[i] + "\"";
        }
        json += "]}";
        conn->send_text(json);
    }

    void handle_list_users(ws::ConnectionPtr conn, const std::string& text) {
        auto room = ws::SimpleJson::get(text, "room");
        if (room) {
            send_user_list(conn, *room);
        }
    }

    void send_user_list(ws::ConnectionPtr conn, const std::string& room_name) {
        auto room = server_->room_manager().get_room(room_name);
        if (!room) return;

        std::lock_guard<std::mutex> lock(users_mutex_);
        std::string json = "{\"type\":\"users\",\"room\":\"" + room_name + "\",\"users\":[";
        bool first = true;

        for (const auto& member : room->members()) {
            auto it = users_.find(member->id());
            if (it != users_.end()) {
                if (!first) json += ",";
                first = false;
                json += "\"" + it->second.nickname + "\"";
            }
        }

        json += "]}";
        conn->send_text(json);
    }

    void send_error(ws::ConnectionPtr conn, const std::string& message) {
        conn->send_text("{\"type\":\"error\",\"message\":\"" + message + "\"}");
    }

    std::unique_ptr<ws::Server> server_;
    std::mutex users_mutex_;
    std::map<uint64_t, UserInfo> users_;
};

int main(int argc, char* argv[]) {
    uint16_t port = 8080;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            port = static_cast<uint16_t>(std::stoi(argv[++i]));
        } else if (arg == "--help") {
            std::cout << "Chat Server" << std::endl;
            std::cout << "Usage: " << argv[0] << " [--port <port>]" << std::endl;
            return 0;
        }
    }

    signal(SIGINT, [](int) { exit(0); });

    ChatServer server(port);
    server.run();

    return 0;
}
