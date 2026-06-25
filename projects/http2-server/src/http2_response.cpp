/**
 * @file http2_response.cpp
 * @brief HTTP 响应处理实现
 */

#include "http2_response.h"
#include <algorithm>
#include <sstream>
#include <ctime>

namespace http2 {

HttpResponse::HttpResponse() : status_(HttpStatusCode::OK) {}

void HttpResponse::set_status(int code) {
    status_ = static_cast<HttpStatusCode>(code);
}

std::string HttpResponse::get_status_message() const {
    switch (status_) {
        case HttpStatusCode::CONTINUE: return "Continue";
        case HttpStatusCode::SWITCHING_PROTOCOLS: return "Switching Protocols";
        case HttpStatusCode::OK: return "OK";
        case HttpStatusCode::CREATED: return "Created";
        case HttpStatusCode::ACCEPTED: return "Accepted";
        case HttpStatusCode::NO_CONTENT: return "No Content";
        case HttpStatusCode::PARTIAL_CONTENT: return "Partial Content";
        case HttpStatusCode::MOVED_PERMANENTLY: return "Moved Permanently";
        case HttpStatusCode::FOUND: return "Found";
        case HttpStatusCode::NOT_MODIFIED: return "Not Modified";
        case HttpStatusCode::TEMPORARY_REDIRECT: return "Temporary Redirect";
        case HttpStatusCode::PERMANENT_REDIRECT: return "Permanent Redirect";
        case HttpStatusCode::BAD_REQUEST: return "Bad Request";
        case HttpStatusCode::UNAUTHORIZED: return "Unauthorized";
        case HttpStatusCode::FORBIDDEN: return "Forbidden";
        case HttpStatusCode::NOT_FOUND: return "Not Found";
        case HttpStatusCode::METHOD_NOT_ALLOWED: return "Method Not Allowed";
        case HttpStatusCode::CONFLICT: return "Conflict";
        case HttpStatusCode::PAYLOAD_TOO_LARGE: return "Payload Too Large";
        case HttpStatusCode::URI_TOO_LONG: return "URI Too Long";
        case HttpStatusCode::UNSUPPORTED_MEDIA_TYPE: return "Unsupported Media Type";
        case HttpStatusCode::TOO_MANY_REQUESTS: return "Too Many Requests";
        case HttpStatusCode::INTERNAL_SERVER_ERROR: return "Internal Server Error";
        case HttpStatusCode::NOT_IMPLEMENTED: return "Not Implemented";
        case HttpStatusCode::BAD_GATEWAY: return "Bad Gateway";
        case HttpStatusCode::SERVICE_UNAVAILABLE: return "Service Unavailable";
        case HttpStatusCode::GATEWAY_TIMEOUT: return "Gateway Timeout";
        case HttpStatusCode::HTTP_VERSION_NOT_SUPPORTED: return "HTTP Version Not Supported";
        default: return "Unknown";
    }
}

void HttpResponse::set_header(const std::string& name, const std::string& value) {
    std::string lower_name = name;
    std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
    headers_[lower_name] = value;
}

std::string HttpResponse::get_header(const std::string& name) const {
    std::string lower_name = name;
    std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
    auto it = headers_.find(lower_name);
    if (it != headers_.end()) {
        return it->second;
    }
    return "";
}

bool HttpResponse::has_header(const std::string& name) const {
    std::string lower_name = name;
    std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
    return headers_.find(lower_name) != headers_.end();
}

void HttpResponse::set_body(const std::string& body) {
    body_.assign(body.begin(), body.end());
    set_content_length(body_.size());
}

void HttpResponse::append_body(const std::string& data) {
    body_.insert(body_.end(), data.begin(), data.end());
}

void HttpResponse::append_body(const std::vector<uint8_t>& data) {
    body_.insert(body_.end(), data.begin(), data.end());
}

std::string HttpResponse::get_body_string() const {
    return std::string(body_.begin(), body_.end());
}

void HttpResponse::set_content_length(size_t length) {
    headers_["content-length"] = std::to_string(length);
}

void HttpResponse::set_cors_headers(const std::string& origin) {
    set_header("access-control-allow-origin", origin);
    set_header("access-control-allow-methods", "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH");
    set_header("access-control-allow-headers", "Content-Type, Authorization, X-Requested-With");
    set_header("access-control-max-age", "86400");
}

void HttpResponse::send_chunk(const std::vector<uint8_t>& chunk) {
    if (stream_callback_) {
        stream_callback_(chunk);
    }
}

void HttpResponse::end_stream() {
    if (stream_callback_) {
        stream_callback_({});  // 空块表示结束
    }
}

void HttpResponse::send_sse_event(const std::string& event, const std::string& data) {
    std::string sse_data;
    if (!event.empty()) {
        sse_data += "event: " + event + "\n";
    }

    // 支持多行数据
    std::istringstream stream(data);
    std::string line;
    while (std::getline(stream, line)) {
        sse_data += "data: " + line + "\n";
    }
    sse_data += "\n";

    std::vector<uint8_t> chunk(sse_data.begin(), sse_data.end());
    send_chunk(chunk);
}

} // namespace http2
