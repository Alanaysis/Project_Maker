/**
 * @file room.cpp
 * @brief WebSocket 房间系统实现
 *
 * 实现房间管理功能，支持：
 * - 房间创建和销毁
 * - 成员加入和离开
 * - 房间内消息广播
 * - 房间属性管理
 */

#include "websocket/room.h"

namespace ws {

// ============================================================================
// Room 实现
// ============================================================================

Room::Room(const std::string& name) : name_(name) {}

bool Room::add_member(ConnectionPtr conn) {
    if (!conn) return false;

    std::lock_guard<std::mutex> lock(mutex_);
    auto id = conn->id();
    if (members_.find(id) != members_.end()) {
        return false;  // 已经在房间中
    }

    members_[id] = conn;
    conn->join_room(name_);
    return true;
}

bool Room::remove_member(ConnectionPtr conn) {
    if (!conn) return false;
    return remove_member(conn->id());
}

bool Room::remove_member(uint64_t conn_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = members_.find(conn_id);
    if (it == members_.end()) {
        return false;
    }

    it->second->leave_room(name_);
    members_.erase(it);
    return true;
}

bool Room::has_member(ConnectionPtr conn) const {
    if (!conn) return false;
    return has_member(conn->id());
}

bool Room::has_member(uint64_t conn_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return members_.find(conn_id) != members_.end();
}

size_t Room::member_count() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return members_.size();
}

std::vector<ConnectionPtr> Room::members() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<ConnectionPtr> result;
    result.reserve(members_.size());
    for (const auto& [id, conn] : members_) {
        result.push_back(conn);
    }
    return result;
}

void Room::broadcast(const std::string& text) {
    std::lock_guard<std::mutex> lock(mutex_);
    for (const auto& [id, conn] : members_) {
        if (conn->state() == ConnectionState::Open) {
            conn->send_text(text);
        }
    }
}

void Room::broadcast(const std::string& text, ConnectionPtr exclude) {
    std::lock_guard<std::mutex> lock(mutex_);
    for (const auto& [id, conn] : members_) {
        if (conn->state() == ConnectionState::Open && conn != exclude) {
            conn->send_text(text);
        }
    }
}

void Room::broadcast_binary(const std::vector<uint8_t>& data) {
    std::lock_guard<std::mutex> lock(mutex_);
    for (const auto& [id, conn] : members_) {
        if (conn->state() == ConnectionState::Open) {
            conn->send_binary(data);
        }
    }
}

void Room::broadcast_binary(const std::vector<uint8_t>& data, ConnectionPtr exclude) {
    std::lock_guard<std::mutex> lock(mutex_);
    for (const auto& [id, conn] : members_) {
        if (conn->state() == ConnectionState::Open && conn != exclude) {
            conn->send_binary(data);
        }
    }
}

void Room::set_property(const std::string& key, const std::string& value) {
    std::lock_guard<std::mutex> lock(mutex_);
    properties_[key] = value;
}

std::optional<std::string> Room::get_property(const std::string& key) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = properties_.find(key);
    if (it != properties_.end()) {
        return it->second;
    }
    return std::nullopt;
}

bool Room::empty() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return members_.empty();
}

// ============================================================================
// RoomManager 实现
// ============================================================================

std::shared_ptr<Room> RoomManager::create_room(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = rooms_.find(name);
    if (it != rooms_.end()) {
        return it->second;
    }

    auto room = std::make_shared<Room>(name);
    rooms_[name] = room;
    return room;
}

bool RoomManager::destroy_room(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = rooms_.find(name);
    if (it == rooms_.end()) {
        return false;
    }

    // 通知所有成员离开
    auto room = it->second;
    auto members = room->members();
    for (const auto& member : members) {
        room->remove_member(member);
    }

    rooms_.erase(it);
    return true;
}

std::shared_ptr<Room> RoomManager::get_room(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = rooms_.find(name);
    if (it != rooms_.end()) {
        return it->second;
    }
    return nullptr;
}

bool RoomManager::has_room(const std::string& name) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return rooms_.find(name) != rooms_.end();
}

std::vector<std::string> RoomManager::room_names() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::string> names;
    names.reserve(rooms_.size());
    for (const auto& [name, room] : rooms_) {
        names.push_back(name);
    }
    return names;
}

size_t RoomManager::room_count() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return rooms_.size();
}

void RoomManager::join_room(ConnectionPtr conn, const std::string& room_name) {
    if (!conn) return;

    std::lock_guard<std::mutex> lock(mutex_);
    auto it = rooms_.find(room_name);
    if (it == rooms_.end()) {
        // 自动创建房间
        auto room = std::make_shared<Room>(room_name);
        rooms_[room_name] = room;
        room->add_member(conn);
    } else {
        it->second->add_member(conn);
    }
}

void RoomManager::leave_room(ConnectionPtr conn, const std::string& room_name) {
    if (!conn) return;

    std::lock_guard<std::mutex> lock(mutex_);
    auto it = rooms_.find(room_name);
    if (it != rooms_.end()) {
        it->second->remove_member(conn);

        // 如果房间为空，自动销毁
        if (it->second->empty()) {
            rooms_.erase(it);
        }
    }
}

void RoomManager::leave_all_rooms(ConnectionPtr conn) {
    if (!conn) return;

    // 获取连接所在的房间列表
    auto room_names = conn->rooms();
    for (const auto& name : room_names) {
        leave_room(conn, name);
    }
}

void RoomManager::broadcast_to_room(const std::string& room_name, const std::string& text) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = rooms_.find(room_name);
    if (it != rooms_.end()) {
        it->second->broadcast(text);
    }
}

} // namespace ws
