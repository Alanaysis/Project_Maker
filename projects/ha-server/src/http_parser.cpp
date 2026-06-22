/**
 * @file http_parser.cpp
 * @brief HTTP 协议解析器实现
 *
 * 实现简单的 HTTP/1.1 请求和响应解析。
 *
 * HTTP 请求格式：
 * ```
 * GET /path HTTP/1.1\r\n
 * Host: example.com\r\n
 * Content-Type: text/plain\r\n
 * \r\n
 * [body]
 * ```
 *
 * ⭐ 重点：理解 HTTP 协议格式
 * 💡 思考：如何处理不完整的请求？（粘包/拆包）
 */

#include "../include/http_parser.h"
#include <sstream>
#include <algorithm>

namespace ha_server {

// ============================================================================
// HttpRequest 实现
// ============================================================================

std::string HttpRequest::get_header(const std::string& name) const {
    // HTTP 头部名称不区分大小写
    std::string lower_name = name;
    std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);

    for (const auto& pair : headers) {
        std::string lower_key = pair.first;
        std::transform(lower_key.begin(), lower_key.end(), lower_key.begin(), ::tolower);
        if (lower_key == lower_name) {
            return pair.second;
        }
    }
    return "";
}

std::string HttpRequest::to_string() const {
    std::ostringstream oss;

    // 请求行
    oss << method << " " << path << " " << version << "\r\n";

    // 请求头
    for (const auto& pair : headers) {
        oss << pair.first << ": " << pair.second << "\r\n";
    }

    // 空行
    oss << "\r\n";

    // 请求体
    if (!body.empty()) {
        oss << body;
    }

    return oss.str();
}

// ============================================================================
// HttpResponse 实现
// ============================================================================

void HttpResponse::set_header(const std::string& name, const std::string& value) {
    headers[name] = value;
}

std::string HttpResponse::to_string() const {
    std::ostringstream oss;

    // 状态行
    oss << version << " " << status_code << " " << status_text << "\r\n";

    // 响应头
    for (const auto& pair : headers) {
        oss << pair.first << ": " << pair.second << "\r\n";
    }

    // 空行
    oss << "\r\n";

    // 响应体
    if (!body.empty()) {
        oss << body;
    }

    return oss.str();
}

HttpResponse HttpResponse::error_response(int code, const std::string& message) {
    HttpResponse response;
    response.status_code = code;

    switch (code) {
        case 400: response.status_text = "Bad Request"; break;
        case 404: response.status_text = "Not Found"; break;
        case 500: response.status_text = "Internal Server Error"; break;
        case 502: response.status_text = "Bad Gateway"; break;
        case 503: response.status_text = "Service Unavailable"; break;
        default: response.status_text = "Error"; break;
    }

    response.set_header("Content-Type", "text/plain");
    response.set_header("Connection", "close");
    response.body = message;
    response.set_header("Content-Length", std::to_string(message.size()));

    return response;
}

// ============================================================================
// HttpParser 实现
// ============================================================================

HttpParser::HttpParser()
    : state_(ParseState::RequestLine)
    , content_length_(0) {
}

void HttpParser::reset() {
    state_ = ParseState::RequestLine;
    request_ = HttpRequest();
    buffer_.clear();
    content_length_ = 0;
}

/**
 * 解析 HTTP 数据
 *
 * 支持分块解析，处理不完整的请求。
 * 状态机：RequestLine → Headers → Body → Complete
 *
 * ⭐ 重点：
 * - 状态机设计
 * - 处理不完整的数据
 * - 正确识别请求边界
 */
int HttpParser::parse(const char* data, size_t length) {
    buffer_.append(data, length);
    size_t parsed = 0;

    while (parsed < buffer_.size()) {
        if (state_ == ParseState::RequestLine) {
            // 查找请求行结束符
            auto pos = buffer_.find("\r\n", parsed);
            if (pos == std::string::npos) {
                // 请求行不完整，等待更多数据
                return parsed;
            }

            // 解析请求行
            std::string line = buffer_.substr(parsed, pos - parsed);
            if (!parse_request_line(line)) {
                state_ = ParseState::Error;
                return -1;
            }

            parsed = pos + 2;  // 跳过 \r\n
            state_ = ParseState::Headers;
        }
        else if (state_ == ParseState::Headers) {
            // 查找头部结束符
            auto pos = buffer_.find("\r\n", parsed);
            if (pos == std::string::npos) {
                // 头部不完整，等待更多数据
                return parsed;
            }

            std::string line = buffer_.substr(parsed, pos - parsed);

            if (line.empty()) {
                // 空行表示头部结束
                parsed = pos + 2;

                // 检查是否有请求体
                auto it = request_.headers.find("Content-Length");
                if (it != request_.headers.end()) {
                    content_length_ = std::stoul(it->second);
                    if (content_length_ > 0) {
                        state_ = ParseState::Body;
                    } else {
                        state_ = ParseState::Complete;
                    }
                } else {
                    state_ = ParseState::Complete;
                }
            } else {
                // 解析头部行
                if (!parse_header_line(line)) {
                    state_ = ParseState::Error;
                    return -1;
                }
                parsed = pos + 2;
            }
        }
        else if (state_ == ParseState::Body) {
            // 计算还需要多少字节
            size_t remaining = buffer_.size() - parsed;
            if (remaining >= content_length_) {
                // 请求体完整
                request_.body = buffer_.substr(parsed, content_length_);
                parsed += content_length_;
                state_ = ParseState::Complete;
            } else {
                // 请求体不完整，等待更多数据
                return parsed;
            }
        }
        else if (state_ == ParseState::Complete || state_ == ParseState::Error) {
            break;
        }
    }

    return parsed;
}

bool HttpParser::parse_request_line(const std::string& line) {
    std::istringstream iss(line);
    iss >> request_.method >> request_.path >> request_.version;

    if (request_.method.empty() || request_.path.empty() || request_.version.empty()) {
        return false;
    }

    // 检查是否需要保持连接
    if (request_.version == "HTTP/1.1") {
        request_.keep_alive = true;  // HTTP/1.1 默认保持连接
    } else {
        request_.keep_alive = false;  // HTTP/1.0 默认关闭连接
    }

    return true;
}

bool HttpParser::parse_header_line(const std::string& line) {
    auto colon_pos = line.find(':');
    if (colon_pos == std::string::npos) {
        return false;
    }

    std::string name = line.substr(0, colon_pos);
    std::string value = line.substr(colon_pos + 1);

    // 去除前导空格
    size_t start = value.find_first_not_of(" \t");
    if (start != std::string::npos) {
        value = value.substr(start);
    }

    request_.headers[name] = value;

    // 检查 Connection 头部
    if (name == "Connection") {
        std::string lower_value = value;
        std::transform(lower_value.begin(), lower_value.end(),
                      lower_value.begin(), ::tolower);
        if (lower_value == "close") {
            request_.keep_alive = false;
        } else if (lower_value == "keep-alive") {
            request_.keep_alive = true;
        }
    }

    return true;
}

bool HttpParser::parse_request(const char* data, size_t length, HttpRequest& request) {
    HttpParser parser;
    int parsed = parser.parse(data, length);

    if (parsed < 0 || !parser.is_complete()) {
        return false;
    }

    request = parser.get_request();
    return true;
}

} // namespace ha_server
