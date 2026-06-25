/**
 * @file security.cpp
 * @brief WebSocket 安全管理实现
 *
 * 实现安全相关功能，包括：
 * - 令牌认证
 * - 速率限制
 * - 输入验证
 */

#include "websocket/security.h"

namespace ws {

// ============================================================================
// SimpleTokenAuthenticator 实现
// ============================================================================

void SimpleTokenAuthenticator::add_token(const std::string& token, const std::string& user_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    tokens_[token] = user_id;
}

void SimpleTokenAuthenticator::remove_token(const std::string& token) {
    std::lock_guard<std::mutex> lock(mutex_);
    tokens_.erase(token);
}

AuthResult SimpleTokenAuthenticator::authenticate(ConnectionPtr conn, const std::string& token) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = tokens_.find(token);
    if (it != tokens_.end()) {
        return {
            true,
            it->second,
            "Authentication successful",
            {}
        };
    }

    return {
        false,
        "",
        "Invalid token",
        {}
    };
}

// ============================================================================
// RateLimiter 实现
// ============================================================================

RateLimiter::RateLimiter(int max_requests, int window_ms)
    : max_requests_(max_requests), window_ms_(window_ms) {}

bool RateLimiter::allow(const std::string& client_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    int64_t now = utils::timestamp_ms();
    auto it = clients_.find(client_id);

    if (it == clients_.end()) {
        // 新客户端
        clients_[client_id] = {1, now};
        return true;
    }

    auto& info = it->second;

    // 检查时间窗口
    if (now - info.window_start > window_ms_) {
        // 重置窗口
        info.request_count = 1;
        info.window_start = now;
        return true;
    }

    // 检查请求计数
    if (info.request_count >= max_requests_) {
        return false;
    }

    info.request_count++;
    return true;
}

void RateLimiter::reset(const std::string& client_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    clients_.erase(client_id);
}

int RateLimiter::remaining(const std::string& client_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    int64_t now = utils::timestamp_ms();
    auto it = clients_.find(client_id);

    if (it == clients_.end()) {
        return max_requests_;
    }

    auto& info = it->second;

    // 检查时间窗口
    if (now - info.window_start > window_ms_) {
        return max_requests_;
    }

    return max_requests_ - info.request_count;
}

// ============================================================================
// InputValidator 实现
// ============================================================================

InputValidator::InputValidator(size_t max_message_size, size_t max_string_length)
    : max_message_size_(max_message_size), max_string_length_(max_string_length) {}

bool InputValidator::validate(const Message& msg) const {
    if (msg.type == Opcode::Text) {
        return validate_text(msg.text());
    } else if (msg.type == Opcode::Binary) {
        return validate_binary(msg.data);
    }
    return false;
}

bool InputValidator::validate_text(const std::string& text) const {
    // 检查大小
    if (text.size() > max_string_length_) {
        return false;
    }

    // 检查 UTF-8 有效性
    size_t i = 0;
    while (i < text.size()) {
        uint8_t byte = static_cast<uint8_t>(text[i]);
        size_t char_len = 0;

        if (byte <= 0x7F) {
            char_len = 1;
        } else if ((byte & 0xE0) == 0xC0) {
            char_len = 2;
        } else if ((byte & 0xF0) == 0xE0) {
            char_len = 3;
        } else if ((byte & 0xF8) == 0xF0) {
            char_len = 4;
        } else {
            return false;  // 无效的 UTF-8 起始字节
        }

        // 检查是否有足够的字节
        if (i + char_len > text.size()) {
            return false;
        }

        // 检查后续字节
        for (size_t j = 1; j < char_len; ++j) {
            if ((static_cast<uint8_t>(text[i + j]) & 0xC0) != 0x80) {
                return false;
            }
        }

        i += char_len;
    }

    return true;
}

bool InputValidator::validate_binary(const std::vector<uint8_t>& data) const {
    return data.size() <= max_message_size_;
}

// ============================================================================
// SecurityManager 实现
// ============================================================================

bool SecurityManager::validate_connection(ConnectionPtr conn, const std::string& token) {
    if (!conn) return false;

    // 如果需要认证
    if (auth_required_ && authenticator_) {
        auto result = authenticator_->authenticate(conn, token);
        if (!result.success) {
            return false;
        }
        conn->set_user_data(result.user_id);
    }

    return true;
}

bool SecurityManager::validate_message(ConnectionPtr conn, const Message& msg) {
    if (!conn) return false;

    // 速率限制检查
    if (rate_limit_enabled_ && rate_limiter_ptr_) {
        std::string client_id = conn->remote_address();
        if (!rate_limiter_ptr_->allow(client_id)) {
            return false;
        }
    }

    // 输入验证
    if (input_validator_ptr_ && !input_validator_ptr_->validate(msg)) {
        return false;
    }

    return true;
}

} // namespace ws
