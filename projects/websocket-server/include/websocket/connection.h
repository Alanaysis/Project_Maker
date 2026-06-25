#pragma once
/**
 * @file connection.h
 * @brief WebSocket 连接管理
 *
 * 管理单个 WebSocket 连接的生命周期，包括：
 * - TCP 套接字管理
 * - 握手处理
 * - 帧读写
 * - 心跳检测
 * - 状态管理
 */

#include "common.h"
#include "frame.h"

namespace ws {

// 前向声明
class Server;
class Connection;
using ConnectionPtr = std::shared_ptr<Connection>;

/**
 * @brief 连接事件回调
 */
struct ConnectionCallbacks {
    std::function<void(ConnectionPtr)>                       on_open;
    std::function<void(ConnectionPtr, const Message&)>       on_message;
    std::function<void(ConnectionPtr, CloseCode, const std::string&)> on_close;
    std::function<void(ConnectionPtr, const std::string&)>   on_error;
    std::function<void(ConnectionPtr)>                       on_ping;
    std::function<void(ConnectionPtr)>                       on_pong;
};

/**
 * @brief WebSocket 连接
 *
 * 代表一个 WebSocket 连接实例，管理其完整的生命周期。
 * 每个连接都有一个唯一的 ID，并维护自己的读写缓冲区。
 */
class Connection : public std::enable_shared_from_this<Connection> {
public:
    /**
     * @brief 构造函数
     * @param fd 套接字文件描述符
     * @param server 所属服务器
     */
    Connection(int fd, Server* server);
    ~Connection();

    // 禁止拷贝
    Connection(const Connection&) = delete;
    Connection& operator=(const Connection&) = delete;

    // ========================================================================
    // 连接信息
    // ========================================================================

    /** @brief 获取连接 ID */
    uint64_t id() const { return id_; }

    /** @brief 获取当前状态 */
    ConnectionState state() const { return state_; }

    /** @brief 获取套接字文件描述符 */
    int fd() const { return fd_; }

    /** @brief 获取远程地址 */
    const std::string& remote_address() const { return remote_addr_; }

    /** @brief 获取远程端口 */
    uint16_t remote_port() const { return remote_port_; }

    // ========================================================================
    // 消息发送
    // ========================================================================

    /**
     * @brief 发送文本消息
     * @param text 文本内容
     */
    void send_text(const std::string& text);

    /**
     * @brief 发送二进制消息
     * @param data 二进制数据
     */
    void send_binary(const std::vector<uint8_t>& data);

    /**
     * @brief 发送消息
     * @param msg 消息对象
     */
    void send(const Message& msg);

    /**
     * @brief 发送 Ping
     * @param payload 可选的载荷数据
     */
    void send_ping(const std::vector<uint8_t>& payload = {});

    /**
     * @brief 发送 Pong
     * @param payload 载荷数据
     */
    void send_pong(const std::vector<uint8_t>& payload = {});

    /**
     * @brief 关闭连接
     * @param code 关闭状态码
     * @param reason 关闭原因
     */
    void close(CloseCode code = CloseCode::Normal, const std::string& reason = "");

    // ========================================================================
    // 连接属性
    // ========================================================================

    /**
     * @brief 设置连接标签（用于标识连接用途）
     */
    void set_tag(const std::string& tag) { tag_ = tag; }

    /**
     * @brief 获取连接标签
     */
    const std::string& tag() const { return tag_; }

    /**
     * @brief 设置用户数据
     */
    void set_user_data(const std::string& data) { user_data_ = data; }

    /**
     * @brief 获取用户数据
     */
    const std::string& user_data() const { return user_data_; }

    /**
     * @brief 获取最后活动时间（毫秒时间戳）
     */
    int64_t last_active_time() const { return last_active_time_; }

    /**
     * @brief 获取加入的房间列表
     */
    const std::vector<std::string>& rooms() const { return rooms_; }

    // ========================================================================
    // 内部方法（供 Server 调用）
    // ========================================================================

    /**
     * @brief 处理可读事件
     */
    void handle_read();

    /**
     * @brief 处理可写事件
     */
    void handle_write();

    /**
     * @brief 处理握手
     * @return 握手是否成功
     */
    bool handle_handshake();

    /**
     * @brief 设置回调函数
     */
    void set_callbacks(const ConnectionCallbacks& callbacks) { callbacks_ = callbacks; }

    /**
     * @brief 加入房间
     */
    void join_room(const std::string& room_name);

    /**
     * @brief 离开房间
     */
    void leave_room(const std::string& room_name);

    /**
     * @brief 更新活动时间
     */
    void update_active_time();

private:
    /**
     * @brief 处理接收到的帧
     */
    void process_frame(const Frame& frame);

    /**
     * @brief 处理数据帧（Text/Binary/Continuation）
     */
    void process_data_frame(const Frame& frame);

    /**
     * @brief 处理控制帧（Close/Ping/Pong）
     */
    void process_control_frame(const Frame& frame);

    /**
     * @brief 完成一条完整消息的处理
     */
    void finalize_message();

    /**
     * @brief 将数据加入发送队列
     */
    void enqueue_send(const std::vector<uint8_t>& data);

    /**
     * @brief 尝试刷新发送缓冲区
     */
    void flush_send_buffer();

    /**
     * @brief 获取对端地址信息
     */
    void get_peer_address();

    /**
     * @brief 触发连接关闭
     */
    void trigger_close(CloseCode code, const std::string& reason);

    // 连接标识
    uint64_t id_;
    int fd_;
    Server* server_;

    // 网络地址
    std::string remote_addr_;
    uint16_t remote_port_ = 0;

    // 状态
    ConnectionState state_ = ConnectionState::Connecting;
    int64_t last_active_time_ = 0;

    // 回调
    ConnectionCallbacks callbacks_;

    // 读缓冲区
    std::vector<uint8_t> read_buffer_;
    static constexpr size_t READ_BUFFER_SIZE = 65536;

    // 写缓冲区
    std::vector<uint8_t> write_buffer_;
    std::mutex write_mutex_;

    // 分片消息重组
    Opcode current_message_type_ = Opcode::Text;
    std::vector<uint8_t> current_message_data_;
    bool message_in_progress_ = false;

    // 连接属性
    std::string tag_;
    std::string user_data_;
    std::vector<std::string> rooms_;

    // 手握手相关
    std::string handshake_data_;

    // 静态 ID 生成器
    static std::atomic<uint64_t> next_id_;
};

} // namespace ws
