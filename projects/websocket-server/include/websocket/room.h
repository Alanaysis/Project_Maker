#pragma once
/**
 * @file room.h
 * @brief WebSocket 房间系统
 *
 * 实现房间管理功能，支持：
 * - 房间创建和销毁
 * - 成员加入和离开
 * - 房间内广播
 * - 房间元数据管理
 */

#include "common.h"
#include "connection.h"

namespace ws {

/**
 * @brief 房间
 *
 * 管理一个房间内的所有连接，支持消息广播。
 */
class Room {
public:
    explicit Room(const std::string& name);
    ~Room() = default;

    /**
     * @brief 获取房间名称
     */
    const std::string& name() const { return name_; }

    /**
     * @brief 添加成员
     * @return 是否成功添加（如果已在房间则返回 false）
     */
    bool add_member(ConnectionPtr conn);

    /**
     * @brief 移除成员
     * @return 是否成功移除
     */
    bool remove_member(ConnectionPtr conn);

    /**
     * @brief 移除成员（通过 ID）
     */
    bool remove_member(uint64_t conn_id);

    /**
     * @brief 检查是否是成员
     */
    bool has_member(ConnectionPtr conn) const;

    /**
     * @brief 检查是否是成员（通过 ID）
     */
    bool has_member(uint64_t conn_id) const;

    /**
     * @brief 获取成员数量
     */
    size_t member_count() const;

    /**
     * @brief 获取所有成员
     */
    std::vector<ConnectionPtr> members() const;

    /**
     * @brief 广播文本消息给房间内所有成员
     */
    void broadcast(const std::string& text);

    /**
     * @brief 广播文本消息给房间内所有成员（排除指定连接）
     */
    void broadcast(const std::string& text, ConnectionPtr exclude);

    /**
     * @brief 广播二进制消息给房间内所有成员
     */
    void broadcast_binary(const std::vector<uint8_t>& data);

    /**
     * @brief 广播二进制消息给房间内所有成员（排除指定连接）
     */
    void broadcast_binary(const std::vector<uint8_t>& data, ConnectionPtr exclude);

    /**
     * @brief 设置房间属性
     */
    void set_property(const std::string& key, const std::string& value);

    /**
     * @brief 获取房间属性
     */
    std::optional<std::string> get_property(const std::string& key) const;

    /**
     * @brief 房间是否为空
     */
    bool empty() const;

private:
    std::string name_;
    mutable std::mutex mutex_;
    std::unordered_map<uint64_t, ConnectionPtr> members_;
    std::unordered_map<std::string, std::string> properties_;
};

/**
 * @brief 房间管理器
 *
 * 管理所有房间的创建、销毁和查找。
 */
class RoomManager {
public:
    RoomManager() = default;
    ~RoomManager() = default;

    /**
     * @brief 创建房间
     * @param name 房间名称
     * @return 房间指针（如果已存在则返回现有房间）
     */
    std::shared_ptr<Room> create_room(const std::string& name);

    /**
     * @brief 销毁房间
     * @param name 房间名称
     * @return 是否成功销毁
     */
    bool destroy_room(const std::string& name);

    /**
     * @brief 获取房间
     * @param name 房间名称
     * @return 房间指针，不存在返回 nullptr
     */
    std::shared_ptr<Room> get_room(const std::string& name);

    /**
     * @brief 检查房间是否存在
     */
    bool has_room(const std::string& name) const;

    /**
     * @brief 获取所有房间名称
     */
    std::vector<std::string> room_names() const;

    /**
     * @brief 获取房间数量
     */
    size_t room_count() const;

    /**
     * @brief 将连接加入房间
     * @param conn 连接
     * @param room_name 房间名称（如果不存在则自动创建）
     */
    void join_room(ConnectionPtr conn, const std::string& room_name);

    /**
     * @brief 将连接从房间移除
     */
    void leave_room(ConnectionPtr conn, const std::string& room_name);

    /**
     * @brief 将连接从所有房间移除
     */
    void leave_all_rooms(ConnectionPtr conn);

    /**
     * @brief 广播消息到指定房间
     */
    void broadcast_to_room(const std::string& room_name, const std::string& text);

private:
    mutable std::mutex mutex_;
    std::unordered_map<std::string, std::shared_ptr<Room>> rooms_;
};

} // namespace ws
