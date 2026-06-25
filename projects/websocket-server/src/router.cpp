/**
 * @file router.cpp
 * @brief WebSocket 消息路由器实现
 *
 * 实现消息路由功能，支持：
 * - 基于路径的路由
 * - 基于动作的路由
 * - 中间件处理链
 * - 简易 JSON 解析
 */

#include "websocket/router.h"
#include <iostream>

namespace ws {

// ============================================================================
// Router 实现
// ============================================================================

void Router::on(const std::string& path, MessageHandler handler) {
    routes_[path] = std::move(handler);
}

void Router::on(const std::string& path, const std::string& action, MessageHandler handler) {
    action_routes_[path][action] = std::move(handler);
}

void Router::use(Middleware middleware) {
    middlewares_.push_back(std::move(middleware));
}

void Router::route(ConnectionPtr conn, const Message& msg) {
    if (!conn) return;

    // 创建路由上下文
    RouteContext ctx;
    ctx.connection = conn;
    ctx.message = msg;

    // 解析消息获取路径和动作
    std::string path, action;
    if (message_parser_) {
        std::tie(path, action) = message_parser_(msg);
    } else {
        std::tie(path, action) = default_message_parser(msg);
    }

    ctx.path = path;
    ctx.action = action;

    // 执行中间件链
    for (const auto& middleware : middlewares_) {
        if (!middleware(ctx)) {
            return;  // 中间件决定停止处理
        }
    }

    // 尝试匹配带动作的路由
    auto path_it = action_routes_.find(path);
    if (path_it != action_routes_.end()) {
        auto action_it = path_it->second.find(action);
        if (action_it != path_it->second.end()) {
            action_it->second(ctx);
            return;
        }
    }

    // 尝试匹配路径路由
    auto route_it = routes_.find(path);
    if (route_it != routes_.end()) {
        route_it->second(ctx);
        return;
    }

    // 尝试默认路由
    route_it = routes_.find("default");
    if (route_it != routes_.end()) {
        route_it->second(ctx);
        return;
    }

    // 使用默认处理器
    if (default_handler_) {
        default_handler_(ctx);
    } else {
        // 没有匹配的路由
        std::cerr << "No route found for path: " << path
                  << ", action: " << action << std::endl;
    }
}

std::pair<std::string, std::string> Router::default_message_parser(const Message& msg) {
    if (msg.type == Opcode::Text) {
        std::string text = msg.text();

        // 尝试解析 JSON
        auto action = SimpleJson::get(text, "action");
        auto path = SimpleJson::get(text, "path");
        auto type = SimpleJson::get(text, "type");

        return {
            path.value_or(type.value_or("default")),
            action.value_or("message")
        };
    }

    return {"default", "binary"};
}

// ============================================================================
// SimpleJson 实现
// ============================================================================

size_t SimpleJson::skip_whitespace(const std::string& str, size_t pos) {
    while (pos < str.size() && (str[pos] == ' ' || str[pos] == '\t' ||
           str[pos] == '\n' || str[pos] == '\r')) {
        pos++;
    }
    return pos;
}

std::optional<std::pair<std::string, size_t>> SimpleJson::parse_string(
    const std::string& str, size_t pos) {
    if (pos >= str.size() || str[pos] != '"') {
        return std::nullopt;
    }

    pos++;  // 跳过开始的引号
    std::string result;

    while (pos < str.size()) {
        if (str[pos] == '"') {
            return std::make_pair(result, pos + 1);
        }
        if (str[pos] == '\\' && pos + 1 < str.size()) {
            pos++;
            switch (str[pos]) {
                case '"': result += '"'; break;
                case '\\': result += '\\'; break;
                case '/': result += '/'; break;
                case 'n': result += '\n'; break;
                case 'r': result += '\r'; break;
                case 't': result += '\t'; break;
                default: result += str[pos]; break;
            }
        } else {
            result += str[pos];
        }
        pos++;
    }

    return std::nullopt;  // 未关闭的字符串
}

std::optional<std::pair<std::string, size_t>> SimpleJson::parse_value(
    const std::string& str, size_t pos) {
    pos = skip_whitespace(str, pos);
    if (pos >= str.size()) return std::nullopt;

    // 字符串
    if (str[pos] == '"') {
        return parse_string(str, pos);
    }

    // 数字、true、false、null
    size_t start = pos;
    if (str[pos] == '-' || (str[pos] >= '0' && str[pos] <= '9')) {
        while (pos < str.size() && (str[pos] == '-' || str[pos] == '.' ||
               (str[pos] >= '0' && str[pos] <= '9') || str[pos] == 'e' || str[pos] == 'E' ||
               str[pos] == '+')) {
            pos++;
        }
        return std::make_pair(str.substr(start, pos - start), pos);
    }

    if (str.substr(pos, 4) == "true") {
        return std::make_pair("true", pos + 4);
    }
    if (str.substr(pos, 5) == "false") {
        return std::make_pair("false", pos + 5);
    }
    if (str.substr(pos, 4) == "null") {
        return std::make_pair("null", pos + 4);
    }

    return std::nullopt;
}

std::unordered_map<std::string, std::string> SimpleJson::parse(const std::string& json) {
    std::unordered_map<std::string, std::string> result;

    size_t pos = skip_whitespace(json, 0);
    if (pos >= json.size() || json[pos] != '{') {
        return result;
    }
    pos++;  // 跳过 '{'

    while (pos < json.size()) {
        pos = skip_whitespace(json, pos);
        if (pos >= json.size()) break;
        if (json[pos] == '}') break;

        // 解析键
        auto key = parse_string(json, pos);
        if (!key) break;
        pos = skip_whitespace(json, key->second);

        // 检查冒号
        if (pos >= json.size() || json[pos] != ':') break;
        pos = skip_whitespace(json, pos + 1);

        // 解析值
        auto value = parse_value(json, pos);
        if (!value) break;
        pos = value->second;

        result[key->first] = value->first;

        // 检查逗号或结束
        pos = skip_whitespace(json, pos);
        if (pos < json.size() && json[pos] == ',') {
            pos++;
        }
    }

    return result;
}

std::string SimpleJson::stringify(const std::unordered_map<std::string, std::string>& map) {
    std::string json = "{";
    bool first = true;

    for (const auto& [key, value] : map) {
        if (!first) json += ",";
        first = false;

        json += "\"" + key + "\":";

        // 判断值类型
        if (value == "true" || value == "false" || value == "null" ||
            (value.size() > 0 && (value[0] == '-' || (value[0] >= '0' && value[0] <= '9')))) {
            json += value;
        } else {
            json += "\"" + value + "\"";
        }
    }

    json += "}";
    return json;
}

std::optional<std::string> SimpleJson::get(const std::string& json, const std::string& key) {
    auto map = parse(json);
    auto it = map.find(key);
    if (it != map.end()) {
        return it->second;
    }
    return std::nullopt;
}

bool SimpleJson::is_valid(const std::string& json) {
    size_t pos = skip_whitespace(json, 0);
    if (pos >= json.size()) return false;

    // 简单检查是否以 { 开始
    if (json[pos] != '{') return false;

    // 尝试解析
    auto map = parse(json);
    return !map.empty() || json.find('{') != std::string::npos;
}

} // namespace ws
