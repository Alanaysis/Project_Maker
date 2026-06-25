#pragma once
/**
 * @file http2_request.h
 * @brief HTTP 请求处理
 *
 * HTTP 请求包含：
 * - 方法：GET, POST, PUT, DELETE, HEAD, OPTIONS 等
 * - 路径：请求的资源路径
 * - 头部：请求头信息
 * - 正文：请求体（POST/PUT 等方法）
 */

#include <string>
#include <map>
#include <vector>
#include <memory>

namespace http2 {

// HTTP 方法
enum class HttpMethod {
    GET,
    POST,
    PUT,
    DELETE_,
    HEAD,
    OPTIONS,
    PATCH,
    TRACE,
    CONNECT,
    UNKNOWN
};

// HTTP 请求类
class HttpRequest {
public:
    HttpRequest() = default;

    // 方法
    void set_method(HttpMethod method) { method_ = method; }
    void set_method(const std::string& method);
    HttpMethod get_method() const { return method_; }
    std::string get_method_string() const;

    // 路径
    void set_path(const std::string& path) { path_ = path; }
    const std::string& get_path() const { return path_; }

    // 查询参数
    void set_query(const std::string& query) { query_ = query; }
    const std::string& get_query() const { return query_; }
    std::string get_query_param(const std::string& name) const;

    // 版本
    void set_version(const std::string& version) { version_ = version; }
    const std::string& get_version() const { return version_; }

    // 头部
    void set_header(const std::string& name, const std::string& value);
    std::string get_header(const std::string& name) const;
    bool has_header(const std::string& name) const;
    const std::map<std::string, std::string>& get_headers() const { return headers_; }

    // 正文
    void set_body(const std::vector<uint8_t>& body) { body_ = body; }
    void set_body(const std::string& body);
    const std::vector<uint8_t>& get_body() const { return body_; }
    std::string get_body_string() const;
    size_t get_body_size() const { return body_.size(); }

    // 流 ID
    void set_stream_id(uint32_t stream_id) { stream_id_ = stream_id; }
    uint32_t get_stream_id() const { return stream_id_; }

    // 解析查询参数
    void parse_query_string();

private:
    HttpMethod method_ = HttpMethod::UNKNOWN;
    std::string path_;
    std::string query_;
    std::string version_ = "HTTP/2";
    std::map<std::string, std::string> headers_;
    std::vector<uint8_t> body_;
    uint32_t stream_id_ = 0;
    std::map<std::string, std::string> query_params_;
};

} // namespace http2
