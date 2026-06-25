#pragma once
/**
 * @file router.h
 * @brief WebSocket 消息路由器
 *
 * 实现消息路由功能，支持：
 * - 基于类型的路由
 * - 基于路径的路由
 * - 中间件处理链
 * - 消息过滤
 */

#include "common.h"
#include "connection.h"

namespace ws {

/**
 * @brief 路由上下文
 *
 * 包含消息处理所需的所有上下文信息。
 */
struct RouteContext {
    ConnectionPtr connection;     // 发送消息的连接
    Message       message;        // 接收到的消息
    std::string   path;           // 消息路径（用于路由）
    std::string   action;         // 消息动作
    std::unordered_map<std::string, std::string> params;  // 参数

    /**
     * @brief 发送文本回复
     */
    void reply(const std::string& text) const {
        if (connection) {
            connection->send_text(text);
        }
    }

    /**
     * @brief 发送 JSON 回复
     */
    void reply_json(const std::string& json) const {
        reply(json);
    }

    /**
     * @brief 发送错误回复
     */
    void error(const std::string& message, int code = -1) const {
        std::string json = "{\"error\":true,\"code\":" + std::to_string(code) +
                          ",\"message\":\"" + message + "\"}";
        reply(json);
    }
};

/**
 * @brief 消息处理器类型
 */
using MessageHandler = std::function<void(const RouteContext&)>;

/**
 * @brief 中间件类型
 *
 * 中间件可以修改上下文或决定是否继续处理。
 * 返回 true 表示继续处理，返回 false 表示停止。
 */
using Middleware = std::function<bool(RouteContext&)>;

/**
 * @brief 消息路由器
 *
 * 支持基于路径和动作的消息路由。
 */
class Router {
public:
    Router() = default;
    ~Router() = default;

    /**
     * @brief 注册消息处理器
     * @param path 消息路径
     * @param handler 处理函数
     */
    void on(const std::string& path, MessageHandler handler);

    /**
     * @brief 注册带动作的处理器
     * @param path 消息路径
     * @param action 动作名称
     * @param handler 处理函数
     */
    void on(const std::string& path, const std::string& action, MessageHandler handler);

    /**
     * @brief 添加中间件
     * @param middleware 中间件函数
     */
    void use(Middleware middleware);

    /**
     * @brief 路由消息
     * @param conn 发送消息的连接
     * @param msg 接收到的消息
     */
    void route(ConnectionPtr conn, const Message& msg);

    /**
     * @brief 设置默认处理器（未匹配路由时调用）
     */
    void set_default_handler(MessageHandler handler) {
        default_handler_ = std::move(handler);
    }

    /**
     * @brief 设置消息解析器
     *
     * 消息解析器负责从原始消息中提取路径和动作信息。
     * 默认假设消息格式为 JSON: {"action": "xxx", "data": {...}}
     */
    void set_message_parser(std::function<std::pair<std::string, std::string>(const Message&)> parser) {
        message_parser_ = std::move(parser);
    }

    /**
     * @brief 默认消息解析器
     */
    static std::pair<std::string, std::string> default_message_parser(const Message& msg);

private:

    // 路由表: path -> handler
    std::unordered_map<std::string, MessageHandler> routes_;

    // 带动作的路由表: path/action -> handler
    std::unordered_map<std::string, std::unordered_map<std::string, MessageHandler>> action_routes_;

    // 中间件链
    std::vector<Middleware> middlewares_;

    // 默认处理器
    MessageHandler default_handler_;

    // 消息解析器
    std::function<std::pair<std::string, std::string>(const Message&)> message_parser_;
};

/**
 * @brief 简易 JSON 解析器
 *
 * 用于解析简单的 JSON 消息。
 * 注意：这是一个简化的实现，仅支持基本的 JSON 格式。
 */
class SimpleJson {
public:
    /**
     * @brief 解析 JSON 字符串
     * @return 键值对映射
     */
    static std::unordered_map<std::string, std::string> parse(const std::string& json);

    /**
     * @brief 创建 JSON 字符串
     */
    static std::string stringify(const std::unordered_map<std::string, std::string>& map);

    /**
     * @brief 获取 JSON 字段值
     */
    static std::optional<std::string> get(const std::string& json, const std::string& key);

    /**
     * @brief 检查是否是有效的 JSON
     */
    static bool is_valid(const std::string& json);

private:
    /**
     * @brief 跳过空白字符
     */
    static size_t skip_whitespace(const std::string& str, size_t pos);

    /**
     * @brief 解析字符串（带引号）
     */
    static std::optional<std::pair<std::string, size_t>> parse_string(
        const std::string& str, size_t pos);

    /**
     * @brief 解析值
     */
    static std::optional<std::pair<std::string, size_t>> parse_value(
        const std::string& str, size_t pos);
};

} // namespace ws
