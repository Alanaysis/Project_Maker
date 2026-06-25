/**
 * @file game_server.cpp
 * @brief 在线游戏服务器示例
 *
 * 演示在线游戏服务器的实现，支持：
 * - 游戏房间管理
 * - 玩家匹配
 * - 游戏状态同步
 * - 实时游戏逻辑
 *
 * 使用方式：
 *   编译: g++ -std=c++17 -I../include game_server.cpp ../src/*.cpp -o game_server
 *   运行: ./game_server
 */

#include "websocket/server.h"
#include <iostream>
#include <map>
#include <random>
#include <cmath>
#include <signal.h>

/**
 * @brief 玩家信息
 */
struct Player {
    uint64_t conn_id;
    std::string name;
    int score;
    int x, y;  // 位置
};

/**
 * @brief 游戏房间
 */
struct GameRoom {
    std::string id;
    std::string name;
    std::map<uint64_t, Player> players;
    bool game_started;
    int max_players;
};

/**
 * @brief 游戏服务器
 */
class GameServer {
public:
    GameServer(uint16_t port = 8082) {
        ws::ServerConfig config;
        config.port = port;
        config.max_connections = 2000;
        config.heartbeat_interval_ms = 15000;
        config.heartbeat_timeout_ms = 30000;

        server_ = std::make_unique<ws::Server>(config);
        setup_handlers();
        create_default_rooms();
    }

    void run() {
        if (!server_->start()) {
            std::cerr << "Failed to start game server" << std::endl;
            return;
        }

        std::cout << "Game server running on ws://0.0.0.0:"
                  << server_->config().port << std::endl;
        server_->run();
    }

private:
    void setup_handlers() {
        server_->set_on_open([this](ws::ConnectionPtr conn) {
            std::lock_guard<std::mutex> lock(mutex_);
            players_[conn->id()] = {conn->id(), "Player_" + std::to_string(conn->id()),
                                   0, 0, 0};
            std::cout << "Player connected: " << conn->id() << std::endl;

            // 发送欢迎消息和可用房间列表
            send_room_list(conn);
        });

        server_->set_on_close([this](ws::ConnectionPtr conn, ws::CloseCode code,
                                      const std::string& reason) {
            std::lock_guard<std::mutex> lock(mutex_);
            auto it = players_.find(conn->id());
            if (it != players_.end()) {
                // 从游戏房间移除
                for (auto& [room_id, room] : games_) {
                    room.players.erase(conn->id());
                }
                std::cout << "Player disconnected: " << it->second.name << std::endl;
                players_.erase(it);
            }
        });

        server_->set_on_message([this](ws::ConnectionPtr conn, const ws::Message& msg) {
            if (msg.type != ws::Opcode::Text) return;

            std::string text = msg.text();
            auto action = ws::SimpleJson::get(text, "action");

            if (!action) return;

            if (*action == "set_name") {
                handle_set_name(conn, text);
            } else if (*action == "create_room") {
                handle_create_room(conn, text);
            } else if (*action == "join_room") {
                handle_join_room(conn, text);
            } else if (*action == "leave_room") {
                handle_leave_room(conn);
            } else if (*action == "move") {
                handle_move(conn, text);
            } else if (*action == "attack") {
                handle_attack(conn, text);
            } else if (*action == "list_rooms") {
                send_room_list(conn);
            }
        });
    }

    void handle_set_name(ws::ConnectionPtr conn, const std::string& text) {
        auto name = ws::SimpleJson::get(text, "name");
        if (!name || name->empty()) return;

        std::lock_guard<std::mutex> lock(mutex_);
        auto it = players_.find(conn->id());
        if (it != players_.end()) {
            it->second.name = *name;
            conn->send_text("{\"type\":\"success\",\"action\":\"set_name\","
                          "\"name\":\"" + *name + "\"}");
        }
    }

    void handle_create_room(ws::ConnectionPtr conn, const std::string& text) {
        auto name = ws::SimpleJson::get(text, "name");
        if (!name || name->empty()) return;

        std::lock_guard<std::mutex> lock(mutex_);

        // 生成房间 ID
        std::string room_id = "room_" + std::to_string(next_room_id_++);

        GameRoom room;
        room.id = room_id;
        room.name = *name;
        room.game_started = false;
        room.max_players = 4;

        games_[room_id] = room;

        conn->send_text("{\"type\":\"success\",\"action\":\"create_room\","
                       "\"room_id\":\"" + room_id + "\","
                       "\"name\":\"" + *name + "\"}");

        std::cout << "Room created: " << *name << " (" << room_id << ")" << std::endl;
    }

    void handle_join_room(ws::ConnectionPtr conn, const std::string& text) {
        auto room_id = ws::SimpleJson::get(text, "room_id");
        if (!room_id) return;

        std::lock_guard<std::mutex> lock(mutex_);

        auto room_it = games_.find(*room_id);
        if (room_it == games_.end()) {
            conn->send_text("{\"type\":\"error\",\"message\":\"Room not found\"}");
            return;
        }

        auto& room = room_it->second;
        if (room.players.size() >= static_cast<size_t>(room.max_players)) {
            conn->send_text("{\"type\":\"error\",\"message\":\"Room is full\"}");
            return;
        }

        if (room.game_started) {
            conn->send_text("{\"type\":\"error\",\"message\":\"Game already started\"}");
            return;
        }

        auto player_it = players_.find(conn->id());
        if (player_it == players_.end()) return;

        // 设置随机初始位置
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, 100);
        player_it->second.x = dis(gen);
        player_it->second.y = dis(gen);

        room.players[conn->id()] = player_it->second;

        // 通知房间内所有玩家
        std::string join_msg = "{\"type\":\"player_joined\","
                              "\"player\":\"" + player_it->second.name + "\","
                              "\"x\":" + std::to_string(player_it->second.x) + ","
                              "\"y\":" + std::to_string(player_it->second.y) + "}";

        for (const auto& [pid, player] : room.players) {
            if (pid != conn->id()) {
                auto pconn = server_->get_connection(pid);
                if (pconn) {
                    pconn->send_text(join_msg);
                }
            }
        }

        // 发送当前游戏状态给新玩家
        send_game_state(conn, room);

        conn->send_text("{\"type\":\"success\",\"action\":\"join_room\","
                       "\"room_id\":\"" + *room_id + "\"}");

        std::cout << "Player " << player_it->second.name
                  << " joined room " << room.name << std::endl;
    }

    void handle_leave_room(ws::ConnectionPtr conn) {
        std::lock_guard<std::mutex> lock(mutex_);

        for (auto& [room_id, room] : games_) {
            auto it = room.players.find(conn->id());
            if (it != room.players.end()) {
                std::string player_name = it->second.name;
                room.players.erase(it);

                // 通知其他玩家
                std::string leave_msg = "{\"type\":\"player_left\","
                                       "\"player\":\"" + player_name + "\"}";
                for (const auto& [pid, player] : room.players) {
                    auto pconn = server_->get_connection(pid);
                    if (pconn) {
                        pconn->send_text(leave_msg);
                    }
                }

                conn->send_text("{\"type\":\"success\",\"action\":\"leave_room\"}");
                break;
            }
        }
    }

    void handle_move(ws::ConnectionPtr conn, const std::string& text) {
        auto dx_str = ws::SimpleJson::get(text, "dx");
        auto dy_str = ws::SimpleJson::get(text, "dy");
        if (!dx_str || !dy_str) return;

        int dx = std::stoi(*dx_str);
        int dy = std::stoi(*dy_str);

        std::lock_guard<std::mutex> lock(mutex_);

        for (auto& [room_id, room] : games_) {
            auto it = room.players.find(conn->id());
            if (it != room.players.end()) {
                it->second.x += dx;
                it->second.y += dy;

                // 限制范围
                it->second.x = std::max(0, std::min(100, it->second.x));
                it->second.y = std::max(0, std::min(100, it->second.y));

                // 广播移动
                std::string move_msg = "{\"type\":\"player_moved\","
                                      "\"player\":\"" + it->second.name + "\","
                                      "\"x\":" + std::to_string(it->second.x) + ","
                                      "\"y\":" + std::to_string(it->second.y) + "}";

                for (const auto& [pid, player] : room.players) {
                    if (pid != conn->id()) {
                        auto pconn = server_->get_connection(pid);
                        if (pconn) {
                            pconn->send_text(move_msg);
                        }
                    }
                }
                break;
            }
        }
    }

    void handle_attack(ws::ConnectionPtr conn, const std::string& text) {
        auto target_name = ws::SimpleJson::get(text, "target");
        if (!target_name) return;

        std::lock_guard<std::mutex> lock(mutex_);

        for (auto& [room_id, room] : games_) {
            auto attacker_it = room.players.find(conn->id());
            if (attacker_it == room.players.end()) continue;

            // 查找目标
            for (auto& [tid, target] : room.players) {
                if (target.name == *target_name) {
                    // 计算距离
                    int dx = attacker_it->second.x - target.x;
                    int dy = attacker_it->second.y - target.y;
                    double dist = std::sqrt(dx * dx + dy * dy);

                    if (dist <= 10.0) {
                        // 攻击成功
                        attacker_it->second.score += 10;

                        std::string attack_msg = "{\"type\":\"attack\","
                                                "\"attacker\":\"" + attacker_it->second.name + "\","
                                                "\"target\":\"" + target.name + "\","
                                                "\"score\":" + std::to_string(attacker_it->second.score) + "}";

                        for (const auto& [pid, player] : room.players) {
                            auto pconn = server_->get_connection(pid);
                            if (pconn) {
                                pconn->send_text(attack_msg);
                            }
                        }
                    } else {
                        conn->send_text("{\"type\":\"error\",\"message\":\"Target too far\"}");
                    }
                    break;
                }
            }
            break;
        }
    }

    void send_room_list(ws::ConnectionPtr conn) {
        std::lock_guard<std::mutex> lock(mutex_);
        std::string json = "{\"type\":\"rooms\",\"rooms\":[";

        bool first = true;
        for (const auto& [id, room] : games_) {
            if (!first) json += ",";
            first = false;
            json += "{\"id\":\"" + id + "\","
                   "\"name\":\"" + room.name + "\","
                   "\"players\":" + std::to_string(room.players.size()) + ","
                   "\"max_players\":" + std::to_string(room.max_players) + ","
                   "\"started\":" + (room.game_started ? "true" : "false") + "}";
        }

        json += "]}";
        conn->send_text(json);
    }

    void send_game_state(ws::ConnectionPtr conn, const GameRoom& room) {
        std::string json = "{\"type\":\"game_state\",\"players\":[";

        bool first = true;
        for (const auto& [pid, player] : room.players) {
            if (!first) json += ",";
            first = false;
            json += "{\"name\":\"" + player.name + "\","
                   "\"x\":" + std::to_string(player.x) + ","
                   "\"y\":" + std::to_string(player.y) + ","
                   "\"score\":" + std::to_string(player.score) + "}";
        }

        json += "]}";
        conn->send_text(json);
    }

    void create_default_rooms() {
        GameRoom room1;
        room1.id = "room_lobby";
        room1.name = "Lobby";
        room1.game_started = false;
        room1.max_players = 20;
        games_["room_lobby"] = room1;

        GameRoom room2;
        room2.id = "room_arena";
        room2.name = "Arena";
        room2.game_started = false;
        room2.max_players = 4;
        games_["room_arena"] = room2;

        next_room_id_ = 100;
    }

    std::unique_ptr<ws::Server> server_;
    std::mutex mutex_;
    std::map<uint64_t, Player> players_;
    std::map<std::string, GameRoom> games_;
    int next_room_id_ = 1;
};

int main(int argc, char* argv[]) {
    uint16_t port = 8082;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--port" && i + 1 < argc) {
            port = static_cast<uint16_t>(std::stoi(argv[++i]));
        }
    }

    signal(SIGINT, [](int) { exit(0); });

    GameServer server(port);
    server.run();

    return 0;
}
