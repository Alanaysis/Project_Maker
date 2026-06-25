#pragma once
/**
 * @file http2_response.h
 * @brief HTTP 响应处理
 *
 * HTTP 响应包含：
 * - 状态码：200, 404, 500 等
 * - 头部：响应头信息
 * - 正文：响应体
 *
 * 特性：
 * - 支持分块传输
 * - 支持流式响应
 * - 支持 Server-Sent Events
 */

#include <cstdint>
#include <string>
#include <map>
#include <vector>
#include <functional>

namespace http2 {

// HTTP 状态码
enum class HttpStatusCode {
    // 1xx 信息性
    CONTINUE = 100,
    SWITCHING_PROTOCOLS = 101,

    // 2xx 成功
    OK = 200,
    CREATED = 201,
    ACCEPTED = 202,
    NO_CONTENT = 204,
    PARTIAL_CONTENT = 206,

    // 3xx 重定向
    MOVED_PERMANENTLY = 301,
    FOUND = 302,
    NOT_MODIFIED = 304,
    TEMPORARY_REDIRECT = 307,
    PERMANENT_REDIRECT = 308,

    // 4xx 客户端错误
    BAD_REQUEST = 400,
    UNAUTHORIZED = 401,
    FORBIDDEN = 403,
    NOT_FOUND = 404,
    METHOD_NOT_ALLOWED = 405,
    CONFLICT = 409,
    PAYLOAD_TOO_LARGE = 413,
    URI_TOO_LONG = 414,
    UNSUPPORTED_MEDIA_TYPE = 415,
    TOO_MANY_REQUESTS = 429,

    // 5xx 服务器错误
    INTERNAL_SERVER_ERROR = 500,
    NOT_IMPLEMENTED = 501,
    BAD_GATEWAY = 502,
    SERVICE_UNAVAILABLE = 503,
    GATEWAY_TIMEOUT = 504,
    HTTP_VERSION_NOT_SUPPORTED = 505
};

// HTTP 响应类
class HttpResponse {
public:
    HttpResponse();

    // 状态码
    void set_status(HttpStatusCode status) { status_ = status; }
    void set_status(int code);
    HttpStatusCode get_status() const { return status_; }
    int get_status_code() const { return static_cast<int>(status_); }
    std::string get_status_message() const;

    // 头部
    void set_header(const std::string& name, const std::string& value);
    std::string get_header(const std::string& name) const;
    bool has_header(const std::string& name) const;
    const std::map<std::string, std::string>& get_headers() const { return headers_; }

    // 正文
    void set_body(const std::vector<uint8_t>& body) { body_ = body; }
    void set_body(const std::string& body);
    void append_body(const std::string& data);
    void append_body(const std::vector<uint8_t>& data);
    const std::vector<uint8_t>& get_body() const { return body_; }
    std::string get_body_string() const;
    size_t get_body_size() const { return body_.size(); }

    // 内容类型快捷方法
    void set_content_type(const std::string& type) { set_header("content-type", type); }
    void set_content_length(size_t length);
    void set_content_disposition(const std::string& disposition) { set_header("content-disposition", disposition); }

    // 缓存控制
    void set_cache_control(const std::string& directive) { set_header("cache-control", directive); }
    void set_etag(const std::string& etag) { set_header("etag", etag); }
    void set_last_modified(const std::string& date) { set_header("last-modified", date); }
    void set_expires(const std::string& date) { set_header("expires", date); }

    // CORS 支持
    void set_cors_headers(const std::string& origin = "*");

    // 流 ID
    void set_stream_id(uint32_t stream_id) { stream_id_ = stream_id; }
    uint32_t get_stream_id() const { return stream_id_; }

    // 流式响应回调
    using StreamCallback = std::function<void(const std::vector<uint8_t>& chunk)>;
    void set_stream_callback(StreamCallback callback) { stream_callback_ = callback; }
    bool is_streaming() const { return stream_callback_ != nullptr; }
    void send_chunk(const std::vector<uint8_t>& chunk);
    void end_stream();

    // Server-Sent Events
    void send_sse_event(const std::string& event, const std::string& data);

private:
    HttpStatusCode status_;
    std::map<std::string, std::string> headers_;
    std::vector<uint8_t> body_;
    uint32_t stream_id_ = 0;
    StreamCallback stream_callback_;
};

} // namespace http2
