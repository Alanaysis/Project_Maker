#pragma once

/**
 * @file http_parser.h
 * @brief HTTP 协议解析器
 *
 * 实现简单的 HTTP/1.1 请求和响应解析。
 * 支持 GET、POST 等基本方法。
 *
 * ⭐ 重点：理解 HTTP 协议格式
 * 💡 思考：如何处理不完整的请求？（粘包/拆包）
 */

#include "common.h"
#include <string>
#include <unordered_map>

namespace ha_server {

/**
 * @brief HTTP 请求
 */
struct HttpRequest {
    std::string method;                                    // 请求方法
    std::string path;                                      // 请求路径
    std::string version;                                   // HTTP 版本
    std::unordered_map<std::string, std::string> headers;  // 请求头
    std::string body;                                      // 请求体
    bool keep_alive = true;                                // 是否保持连接

    /**
     * @brief 获取请求头
     * @param name 头部名称
     * @return 头部值，不存在返回空字符串
     */
    std::string get_header(const std::string& name) const;

    /**
     * @brief 序列化为 HTTP 请求字符串
     * @return HTTP 请求字符串
     */
    std::string to_string() const;
};

/**
 * @brief HTTP 响应
 */
struct HttpResponse {
    std::string version = "HTTP/1.1";                      // HTTP 版本
    int status_code = 200;                                 // 状态码
    std::string status_text = "OK";                        // 状态文本
    std::unordered_map<std::string, std::string> headers;  // 响应头
    std::string body;                                      // 响应体

    /**
     * @brief 设置响应头
     * @param name 头部名称
     * @param value 头部值
     */
    void set_header(const std::string& name, const std::string& value);

    /**
     * @brief 序列化为 HTTP 响应字符串
     * @return HTTP 响应字符串
     */
    std::string to_string() const;

    /**
     * @brief 创建错误响应
     * @param code 状态码
     * @param message 错误消息
     * @return 错误响应
     */
    static HttpResponse error_response(int code, const std::string& message);
};

/**
 * @brief HTTP 解析器
 *
 * 解析 HTTP 请求字符串为 HttpRequest 结构。
 * 支持分块解析，处理不完整的请求。
 *
 * ⭐ 重点：
 * - HTTP 请求格式：请求行 + 请求头 + 空行 + 请求体
 * - Content-Length 确定请求体长度
 * - 处理不完整的请求（需要继续读取）
 *
 * 💡 思考：
 * - 如何处理超大的请求头？
 * - 如何防止 Slowloris 攻击？
 */
class HttpParser {
public:
    /**
     * @brief 解析状态
     */
    enum class ParseState {
        RequestLine,   // 解析请求行
        Headers,       // 解析请求头
        Body,          // 解析请求体
        Complete,      // 解析完成
        Error          // 解析错误
    };

    /**
     * @brief 构造函数
     */
    HttpParser();

    /**
     * @brief 重置解析器状态
     */
    void reset();

    /**
     * @brief 解析数据
     * @param data 数据指针
     * @param length 数据长度
     * @return 解析的字节数，-1 表示错误
     *
     * 可以多次调用，处理不完整的请求。
     */
    int parse(const char* data, size_t length);

    /**
     * @brief 解析是否完成
     * @return 完成返回 true
     */
    bool is_complete() const { return state_ == ParseState::Complete; }

    /**
     * @brief 是否有解析错误
     * @return 有错误返回 true
     */
    bool has_error() const { return state_ == ParseState::Error; }

    /**
     * @brief 获取解析后的请求
     * @return HTTP 请求
     */
    const HttpRequest& get_request() const { return request_; }

    /**
     * @brief 获取当前解析状态
     * @return 解析状态
     */
    ParseState get_state() const { return state_; }

    /**
     * @brief 解析单个 HTTP 请求
     * @param data 原始数据
     * @param length 数据长度
     * @param request 输出的请求
     * @return 成功返回 true
     */
    static bool parse_request(const char* data, size_t length, HttpRequest& request);

private:
    /**
     * @brief 解析请求行
     * @param line 请求行
     * @return 成功返回 true
     */
    bool parse_request_line(const std::string& line);

    /**
     * @brief 解析请求头
     * @param line 头部行
     * @return 成功返回 true
     */
    bool parse_header_line(const std::string& line);

    ParseState state_;
    HttpRequest request_;
    std::string buffer_;
    size_t content_length_;
};

} // namespace ha_server
