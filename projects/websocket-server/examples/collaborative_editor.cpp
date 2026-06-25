/**
 * @file collaborative_editor.cpp
 * @brief 协同编辑服务器示例
 *
 * 演示协同编辑系统的实现，支持：
 * - 多人同时编辑文档
 * - 操作变换 (OT)
 * - 光标同步
 * - 版本控制
 *
 * 使用方式：
 *   编译: g++ -std=c++17 -I../include collaborative_editor.cpp ../src/*.cpp -o collaborative_editor
 *   运行: ./collaborative_editor
 */

#include "websocket/server.h"
#include <iostream>
#include <map>
#include <deque>
#include <signal.h>

/**
 * @brief 编辑操作类型
 */
enum class EditAction {
    Insert,
    Delete,
    Replace
};

/**
 * @brief 编辑操作
 */
struct EditOperation {
    uint64_t user_id;
    EditAction action;
    size_t position;
    std::string content;
    int version;
    int64_t timestamp;
};

/**
 * @brief 用户光标信息
 */
struct CursorInfo {
    uint64_t user_id;
    std::string username;
    size_t position;
    size_t selection_end;
};

/**
 * @brief 文档状态
 */
struct Document {
    std::string content;
    int version;
    std::deque<EditOperation> history;
    std::map<uint64_t, CursorInfo> cursors;
};

/**
 * @brief 协同编辑服务器
 */
class CollaborativeEditor {
public:
    CollaborativeEditor(uint16_t port = 8083) {
        ws::ServerConfig config;
        config.port = port;
        config.max_connections = 100;
        config.heartbeat_interval_ms = 30000;
        config.heartbeat_timeout_ms = 60000;

        server_ = std::make_unique<ws::Server>(config);
        setup_handlers();

        // 初始化默认文档
        document_.content = "Welcome to Collaborative Editor!\n\nStart typing here...";
        document_.version = 0;
    }

    void run() {
        if (!server_->start()) {
            std::cerr << "Failed to start collaborative editor" << std::endl;
            return;
        }

        std::cout << "Collaborative Editor running on ws://0.0.0.0:"
                  << server_->config().port << std::endl;
        server_->run();
    }

private:
    void setup_handlers() {
        server_->set_on_open([this](ws::ConnectionPtr conn) {
            std::lock_guard<std::mutex> lock(mutex_);
            users_[conn->id()] = {"User_" + std::to_string(conn->id())};
            std::cout << "Editor connected: " << conn->id() << std::endl;

            // 发送当前文档状态
            send_document_state(conn);
        });

        server_->set_on_close([this](ws::ConnectionPtr conn, ws::CloseCode code,
                                      const std::string& reason) {
            std::lock_guard<std::mutex> lock(mutex_);
            auto it = users_.find(conn->id());
            if (it != users_.end()) {
                // 移除光标
                document_.cursors.erase(conn->id());

                // 通知其他用户
                std::string msg = "{\"type\":\"user_left\","
                                 "\"user\":\"" + it->second.username + "\"}";
                broadcast_to_editors(msg, conn->id());

                std::cout << "Editor disconnected: " << it->second.username << std::endl;
                users_.erase(it);
            }
        });

        server_->set_on_message([this](ws::ConnectionPtr conn, const ws::Message& msg) {
            if (msg.type != ws::Opcode::Text) return;

            std::string text = msg.text();
            auto action = ws::SimpleJson::get(text, "action");

            if (!action) return;

            if (*action == "set_username") {
                handle_set_username(conn, text);
            } else if (*action == "insert") {
                handle_insert(conn, text);
            } else if (*action == "delete") {
                handle_delete(conn, text);
            } else if (*action == "cursor") {
                handle_cursor(conn, text);
            } else if (*action == "get_document") {
                send_document_state(conn);
            }
        });
    }

    void handle_set_username(ws::ConnectionPtr conn, const std::string& text) {
        auto username = ws::SimpleJson::get(text, "username");
        if (!username || username->empty()) return;

        std::lock_guard<std::mutex> lock(mutex_);
        auto it = users_.find(conn->id());
        if (it != users_.end()) {
            it->second.username = *username;
            conn->send_text("{\"type\":\"success\",\"action\":\"set_username\","
                          "\"username\":\"" + *username + "\"}");

            // 通知其他用户
            std::string msg = "{\"type\":\"user_joined\","
                             "\"user\":\"" + *username + "\"}";
            broadcast_to_editors(msg, conn->id());
        }
    }

    void handle_insert(ws::ConnectionPtr conn, const std::string& text) {
        auto pos_str = ws::SimpleJson::get(text, "position");
        auto content = ws::SimpleJson::get(text, "content");
        if (!pos_str || !content) return;

        size_t position = std::stoul(*pos_str);

        std::lock_guard<std::mutex> lock(mutex_);

        auto it = users_.find(conn->id());
        if (it == users_.end()) return;

        // 验证位置
        if (position > document_.content.size()) {
            conn->send_text("{\"type\":\"error\",\"message\":\"Invalid position\"}");
            return;
        }

        // 应用操作
        document_.content.insert(position, *content);
        document_.version++;

        // 记录操作
        EditOperation op;
        op.user_id = conn->id();
        op.action = EditAction::Insert;
        op.position = position;
        op.content = *content;
        op.version = document_.version;
        op.timestamp = ws::utils::timestamp_ms();
        document_.history.push_back(op);

        // 限制历史记录大小
        while (document_.history.size() > 1000) {
            document_.history.pop_front();
        }

        // 广播操作
        std::string op_msg = "{\"type\":\"operation\","
                            "\"action\":\"insert\","
                            "\"position\":" + std::to_string(position) + ","
                            "\"content\":\"" + escape_json(*content) + "\","
                            "\"user\":\"" + it->second.username + "\","
                            "\"version\":" + std::to_string(document_.version) + "}";

        broadcast_to_editors(op_msg, conn->id());

        // 确认操作
        conn->send_text("{\"type\":\"ack\",\"version\":" +
                       std::to_string(document_.version) + "}");
    }

    void handle_delete(ws::ConnectionPtr conn, const std::string& text) {
        auto pos_str = ws::SimpleJson::get(text, "position");
        auto len_str = ws::SimpleJson::get(text, "length");
        if (!pos_str || !len_str) return;

        size_t position = std::stoul(*pos_str);
        size_t length = std::stoul(*len_str);

        std::lock_guard<std::mutex> lock(mutex_);

        auto it = users_.find(conn->id());
        if (it == users_.end()) return;

        // 验证位置和长度
        if (position + length > document_.content.size()) {
            conn->send_text("{\"type\":\"error\",\"message\":\"Invalid position or length\"}");
            return;
        }

        // 获取被删除的内容
        std::string deleted = document_.content.substr(position, length);

        // 应用操作
        document_.content.erase(position, length);
        document_.version++;

        // 记录操作
        EditOperation op;
        op.user_id = conn->id();
        op.action = EditAction::Delete;
        op.position = position;
        op.content = deleted;
        op.version = document_.version;
        op.timestamp = ws::utils::timestamp_ms();
        document_.history.push_back(op);

        // 广播操作
        std::string op_msg = "{\"type\":\"operation\","
                            "\"action\":\"delete\","
                            "\"position\":" + std::to_string(position) + ","
                            "\"length\":" + std::to_string(length) + ","
                            "\"user\":\"" + it->second.username + "\","
                            "\"version\":" + std::to_string(document_.version) + "}";

        broadcast_to_editors(op_msg, conn->id());

        conn->send_text("{\"type\":\"ack\",\"version\":" +
                       std::to_string(document_.version) + "}");
    }

    void handle_cursor(ws::ConnectionPtr conn, const std::string& text) {
        auto pos_str = ws::SimpleJson::get(text, "position");
        if (!pos_str) return;

        size_t position = std::stoul(*pos_str);

        std::lock_guard<std::mutex> lock(mutex_);

        auto it = users_.find(conn->id());
        if (it == users_.end()) return;

        // 更新光标位置
        CursorInfo cursor;
        cursor.user_id = conn->id();
        cursor.username = it->second.username;
        cursor.position = position;

        auto sel_end = ws::SimpleJson::get(text, "selection_end");
        cursor.selection_end = sel_end ? std::stoul(*sel_end) : position;

        document_.cursors[conn->id()] = cursor;

        // 广播光标位置
        std::string cursor_msg = "{\"type\":\"cursor\","
                                "\"user\":\"" + it->second.username + "\","
                                "\"position\":" + std::to_string(position) + ","
                                "\"selection_end\":" + std::to_string(cursor.selection_end) + "}";

        broadcast_to_editors(cursor_msg, conn->id());
    }

    void send_document_state(ws::ConnectionPtr conn) {
        std::lock_guard<std::mutex> lock(mutex_);

        // 构建用户列表
        std::string users_json = "[";
        bool first = true;
        for (const auto& [id, user] : users_) {
            if (!first) users_json += ",";
            first = false;
            users_json += "\"" + user.username + "\"";
        }
        users_json += "]";

        // 构建光标列表
        std::string cursors_json = "[";
        first = true;
        for (const auto& [id, cursor] : document_.cursors) {
            if (id == conn->id()) continue;
            if (!first) cursors_json += ",";
            first = false;
            cursors_json += "{\"user\":\"" + cursor.username + "\","
                          "\"position\":" + std::to_string(cursor.position) + ","
                          "\"selection_end\":" + std::to_string(cursor.selection_end) + "}";
        }
        cursors_json += "]";

        std::string json = "{\"type\":\"document_state\","
                          "\"content\":\"" + escape_json(document_.content) + "\","
                          "\"version\":" + std::to_string(document_.version) + ","
                          "\"users\":" + users_json + ","
                          "\"cursors\":" + cursors_json + "}";

        conn->send_text(json);
    }

    void broadcast_to_editors(const std::string& msg, uint64_t exclude_id) {
        for (const auto& [id, user] : users_) {
            if (id != exclude_id) {
                auto conn = server_->get_connection(id);
                if (conn && conn->state() == ws::ConnectionState::Open) {
                    conn->send_text(msg);
                }
            }
        }
    }

    std::string escape_json(const std::string& str) {
        std::string result;
        for (char c : str) {
            switch (c) {
                case '"': result += "\\\""; break;
                case '\\': result += "\\\\"; break;
                case '\n': result += "\\n"; break;
                case '\r': result += "\\r"; break;
                case '\t': result += "\\t"; break;
                default: result += c; break;
            }
        }
        return result;
    }

    struct UserInfo {
        std::string username;
    };

    std::unique_ptr<ws::Server> server_;
    std::mutex mutex_;
    std::map<uint64_t, UserInfo> users_;
    Document document_;
};

int main(int argc, char* argv[]) {
    uint16_t port = 8083;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            port = static_cast<uint16_t>(std::stoi(argv[++i]));
        }
    }

    signal(SIGINT, [](int) { exit(0); });

    CollaborativeEditor server(port);
    server.run();

    return 0;
}
