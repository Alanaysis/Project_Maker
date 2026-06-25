/**
 * @file notification_server.cpp
 * @brief 实时通知服务器示例
 *
 * 演示实时通知系统的实现，支持：
 * - 系统通知
 * - 用户通知
 * - 通知优先级
 * - 通知确认
 *
 * 使用方式：
 *   编译: g++ -std=c++17 -I../include notification_server.cpp ../src/*.cpp -o notification_server
 *   运行: ./notification_server
 */

#include "websocket/server.h"
#include <iostream>
#include <queue>
#include <map>
#include <thread>
#include <signal.h>

/**
 * @brief 通知结构
 */
struct Notification {
    uint64_t id;
    std::string type;        // system, user, alert
    std::string priority;    // low, normal, high, critical
    std::string title;
    std::string message;
    int64_t timestamp;
    bool acknowledged;
};

/**
 * @brief 通知服务器
 */
class NotificationServer {
public:
    NotificationServer(uint16_t port = 8081) {
        ws::ServerConfig config;
        config.port = port;
        config.max_connections = 5000;
        config.heartbeat_interval_ms = 60000;
        config.heartbeat_timeout_ms = 120000;

        server_ = std::make_unique<ws::Server>(config);
        setup_handlers();
        start_notification_generator();
    }

    void run() {
        if (!server_->start()) {
            std::cerr << "Failed to start notification server" << std::endl;
            return;
        }

        std::cout << "Notification server running on ws://0.0.0.0:"
                  << server_->config().port << std::endl;
        server_->run();
    }

private:
    void setup_handlers() {
        server_->set_on_open([this](ws::ConnectionPtr conn) {
            std::lock_guard<std::mutex> lock(mutex_);
            subscribed_users_[conn->id()] = {"all", {}};
            std::cout << "Subscriber connected: " << conn->id() << std::endl;

            // 发送待处理的通知
            send_pending_notifications(conn);
        });

        server_->set_on_close([this](ws::ConnectionPtr conn, ws::CloseCode code,
                                      const std::string& reason) {
            std::lock_guard<std::mutex> lock(mutex_);
            subscribed_users_.erase(conn->id());
            std::cout << "Subscriber disconnected: " << conn->id() << std::endl;
        });

        server_->set_on_message([this](ws::ConnectionPtr conn, const ws::Message& msg) {
            if (msg.type != ws::Opcode::Text) return;

            std::string text = msg.text();
            auto action = ws::SimpleJson::get(text, "action");

            if (!action) return;

            if (*action == "subscribe") {
                handle_subscribe(conn, text);
            } else if (*action == "unsubscribe") {
                handle_unsubscribe(conn, text);
            } else if (*action == "acknowledge") {
                handle_acknowledge(conn, text);
            } else if (*action == "get_history") {
                handle_get_history(conn, text);
            }
        });
    }

    void handle_subscribe(ws::ConnectionPtr conn, const std::string& text) {
        auto channel = ws::SimpleJson::get(text, "channel");
        if (!channel) return;

        std::lock_guard<std::mutex> lock(mutex_);
        auto it = subscribed_users_.find(conn->id());
        if (it != subscribed_users_.end()) {
            it->second.channel = *channel;
            conn->send_text("{\"type\":\"success\",\"action\":\"subscribe\","
                          "\"channel\":\"" + *channel + "\"}");
        }
    }

    void handle_unsubscribe(ws::ConnectionPtr conn, const std::string& text) {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = subscribed_users_.find(conn->id());
        if (it != subscribed_users_.end()) {
            it->second.channel = "none";
            conn->send_text("{\"type\":\"success\",\"action\":\"unsubscribe\"}");
        }
    }

    void handle_acknowledge(ws::ConnectionPtr conn, const std::string& text) {
        auto notif_id = ws::SimpleJson::get(text, "notification_id");
        if (!notif_id) return;

        uint64_t id = std::stoull(*notif_id);

        std::lock_guard<std::mutex> lock(mutex_);
        auto it = notification_store_.find(id);
        if (it != notification_store_.end()) {
            it->second.acknowledged = true;
            conn->send_text("{\"type\":\"success\",\"action\":\"acknowledge\","
                          "\"notification_id\":" + *notif_id + "}");
        }
    }

    void handle_get_history(ws::ConnectionPtr conn, const std::string& text) {
        auto count_str = ws::SimpleJson::get(text, "count");
        size_t count = count_str ? std::stoul(*count_str) : 10;

        std::lock_guard<std::mutex> lock(mutex_);
        std::string json = "{\"type\":\"history\",\"notifications\":[";

        size_t i = 0;
        for (auto it = notification_store_.rbegin();
             it != notification_store_.rend() && i < count; ++it, ++i) {
            if (i > 0) json += ",";
            json += notification_to_json(it->second);
        }

        json += "]}";
        conn->send_text(json);
    }

    void send_pending_notifications(ws::ConnectionPtr conn) {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = subscribed_users_.find(conn->id());
        if (it == subscribed_users_.end()) return;

        std::string channel = it->second.channel;

        for (const auto& [id, notif] : notification_store_) {
            if (!notif.acknowledged &&
                (channel == "all" || channel == notif.type)) {
                conn->send_text("{\"type\":\"notification\"," +
                              notification_to_json(notif) + "}");
            }
        }
    }

    void broadcast_notification(const Notification& notif) {
        std::string json = "{\"type\":\"notification\"," +
                          notification_to_json(notif) + "}";

        std::lock_guard<std::mutex> lock(mutex_);
        for (const auto& [id, info] : subscribed_users_) {
            if (info.channel == "all" || info.channel == notif.type) {
                auto conn = server_->get_connection(id);
                if (conn && conn->state() == ws::ConnectionState::Open) {
                    conn->send_text(json);
                }
            }
        }
    }

    std::string notification_to_json(const Notification& notif) {
        return "\"id\":" + std::to_string(notif.id) +
               ",\"type\":\"" + notif.type + "\"" +
               ",\"priority\":\"" + notif.priority + "\"" +
               ",\"title\":\"" + notif.title + "\"" +
               ",\"message\":\"" + notif.message + "\"" +
               ",\"timestamp\":" + std::to_string(notif.timestamp) +
               ",\"acknowledged\":" + (notif.acknowledged ? "true" : "false");
    }

    void start_notification_generator() {
        // 创建系统通知线程
        notification_thread_ = std::thread([this]() {
            uint64_t notif_id = 1;
            int counter = 0;

            while (true) {
                std::this_thread::sleep_for(std::chrono::seconds(10));
                counter++;

                Notification notif;
                notif.id = notif_id++;
                notif.timestamp = ws::utils::timestamp_ms();
                notif.acknowledged = false;

                // 交替发送不同类型的通知
                switch (counter % 4) {
                    case 0:
                        notif.type = "system";
                        notif.priority = "normal";
                        notif.title = "System Update";
                        notif.message = "System maintenance scheduled for tonight.";
                        break;
                    case 1:
                        notif.type = "alert";
                        notif.priority = "high";
                        notif.title = "High CPU Usage";
                        notif.message = "CPU usage has exceeded 90%.";
                        break;
                    case 2:
                        notif.type = "user";
                        notif.priority = "low";
                        notif.title = "New Feature";
                        notif.message = "Check out our new notification system!";
                        break;
                    case 3:
                        notif.type = "system";
                        notif.priority = "critical";
                        notif.title = "Security Alert";
                        notif.message = "Multiple failed login attempts detected.";
                        break;
                }

                {
                    std::lock_guard<std::mutex> lock(mutex_);
                    notification_store_[notif.id] = notif;
                }

                broadcast_notification(notif);
                std::cout << "Generated notification: " << notif.title << std::endl;
            }
        });
        notification_thread_.detach();
    }

    struct SubscriberInfo {
        std::string channel;
        std::vector<uint64_t> pending;
    };

    std::unique_ptr<ws::Server> server_;
    std::mutex mutex_;
    std::map<uint64_t, SubscriberInfo> subscribed_users_;
    std::map<uint64_t, Notification> notification_store_;
    std::thread notification_thread_;
};

int main(int argc, char* argv[]) {
    uint16_t port = 8081;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            port = static_cast<uint16_t>(std::stoi(argv[++i]));
        }
    }

    signal(SIGINT, [](int) { exit(0); });

    NotificationServer server(port);
    server.run();

    return 0;
}
