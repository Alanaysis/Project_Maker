/**
 * @file http2_request.cpp
 * @brief HTTP 请求处理实现
 */

#include "http2_request.h"
#include <algorithm>
#include <sstream>

namespace http2 {

void HttpRequest::set_method(const std::string& method) {
    std::string upper_method = method;
    std::transform(upper_method.begin(), upper_method.end(), upper_method.begin(), ::toupper);

    if (upper_method == "GET") method_ = HttpMethod::GET;
    else if (upper_method == "POST") method_ = HttpMethod::POST;
    else if (upper_method == "PUT") method_ = HttpMethod::PUT;
    else if (upper_method == "DELETE") method_ = HttpMethod::DELETE_;
    else if (upper_method == "HEAD") method_ = HttpMethod::HEAD;
    else if (upper_method == "OPTIONS") method_ = HttpMethod::OPTIONS;
    else if (upper_method == "PATCH") method_ = HttpMethod::PATCH;
    else if (upper_method == "TRACE") method_ = HttpMethod::TRACE;
    else if (upper_method == "CONNECT") method_ = HttpMethod::CONNECT;
    else method_ = HttpMethod::UNKNOWN;
}

std::string HttpRequest::get_method_string() const {
    switch (method_) {
        case HttpMethod::GET: return "GET";
        case HttpMethod::POST: return "POST";
        case HttpMethod::PUT: return "PUT";
        case HttpMethod::DELETE_: return "DELETE";
        case HttpMethod::HEAD: return "HEAD";
        case HttpMethod::OPTIONS: return "OPTIONS";
        case HttpMethod::PATCH: return "PATCH";
        case HttpMethod::TRACE: return "TRACE";
        case HttpMethod::CONNECT: return "CONNECT";
        default: return "UNKNOWN";
    }
}

std::string HttpRequest::get_query_param(const std::string& name) const {
    auto it = query_params_.find(name);
    if (it != query_params_.end()) {
        return it->second;
    }
    return "";
}

void HttpRequest::set_header(const std::string& name, const std::string& value) {
    std::string lower_name = name;
    std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
    headers_[lower_name] = value;
}

std::string HttpRequest::get_header(const std::string& name) const {
    std::string lower_name = name;
    std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
    auto it = headers_.find(lower_name);
    if (it != headers_.end()) {
        return it->second;
    }
    return "";
}

bool HttpRequest::has_header(const std::string& name) const {
    std::string lower_name = name;
    std::transform(lower_name.begin(), lower_name.end(), lower_name.begin(), ::tolower);
    return headers_.find(lower_name) != headers_.end();
}

void HttpRequest::set_body(const std::string& body) {
    body_.assign(body.begin(), body.end());
}

std::string HttpRequest::get_body_string() const {
    return std::string(body_.begin(), body_.end());
}

void HttpRequest::parse_query_string() {
    if (query_.empty()) return;

    size_t pos = 0;
    while (pos < query_.size()) {
        size_t eq_pos = query_.find('=', pos);
        if (eq_pos == std::string::npos) break;

        size_t amp_pos = query_.find('&', eq_pos);
        if (amp_pos == std::string::npos) amp_pos = query_.size();

        std::string key = query_.substr(pos, eq_pos - pos);
        std::string value = query_.substr(eq_pos + 1, amp_pos - eq_pos - 1);

        // URL 解码（简化版本）
        auto url_decode = [](const std::string& str) -> std::string {
            std::string result;
            for (size_t i = 0; i < str.size(); ++i) {
                if (str[i] == '%' && i + 2 < str.size()) {
                    int val = 0;
                    for (int j = 0; j < 2; ++j) {
                        char c = str[i + 1 + j];
                        if (c >= '0' && c <= '9') val = val * 16 + (c - '0');
                        else if (c >= 'a' && c <= 'f') val = val * 16 + (c - 'a' + 10);
                        else if (c >= 'A' && c <= 'F') val = val * 16 + (c - 'A' + 10);
                    }
                    result += static_cast<char>(val);
                    i += 2;
                } else if (str[i] == '+') {
                    result += ' ';
                } else {
                    result += str[i];
                }
            }
            return result;
        };

        query_params_[url_decode(key)] = url_decode(value);
        pos = amp_pos + 1;
    }
}

} // namespace http2
