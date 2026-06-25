#pragma once
/**
 * @file security.h
 * @brief WebSocket 安全管理
 *
 * 实现安全相关功能，包括：
 * - 认证授权
 * - 速率限制
 * - 输入验证
 * - 连接安全策略
 */

#include "common.h"
#include "connection.h"

namespace ws {

/**
 * @brief 认证结果
 */
struct AuthResult {
    bool        success;    // 是否认证成功
    std::string user_id;    // 用户 ID
    std::string message;    // 结果消息
    std::unordered_map<std::string, std::string> user_data;  // 用户数据
};

/**
 * @brief 认证器接口
 *
 * 负责验证客户端身份。
 */
class Authenticator {
public:
    virtual ~Authenticator() = default;

    /**
     * @brief 验证连接
     * @param conn 连接
     * @param token 认证令牌
     * @return 认证结果
     */
    virtual AuthResult authenticate(ConnectionPtr conn, const std::string& token) = 0;
};

/**
 * @brief 简单令牌认证器
 *
 * 使用预定义的令牌列表进行认证。
 */
class SimpleTokenAuthenticator : public Authenticator {
public:
    /**
     * @brief 添加有效令牌
     * @param token 令牌
     * @param user_id 关联的用户 ID
     */
    void add_token(const std::string& token, const std::string& user_id);

    /**
     * @brief 移除令牌
     */
    void remove_token(const std::string& token);

    /**
     * @brief 验证连接
     */
    AuthResult authenticate(ConnectionPtr conn, const std::string& token) override;

private:
    std::mutex mutex_;
    std::unordered_map<std::string, std::string> tokens_;  // token -> user_id
};

/**
 * @brief 速率限制器
 *
 * 限制客户端的消息发送频率，防止滥用。
 */
class RateLimiter {
public:
    /**
     * @brief 构造函数
     * @param max_requests 时间窗口内最大请求数
     * @param window_ms 时间窗口（毫秒）
     */
    RateLimiter(int max_requests = 100, int window_ms = 60000);

    /**
     * @brief 检查是否允许请求
     * @param client_id 客户端标识（通常是连接 ID 或 IP 地址）
     * @return 是否允许
     */
    bool allow(const std::string& client_id);

    /**
     * @brief 重置客户端计数
     */
    void reset(const std::string& client_id);

    /**
     * @brief 获取客户端剩余配额
     */
    int remaining(const std::string& client_id);

private:
    struct ClientInfo {
        int request_count = 0;
        int64_t window_start = 0;
    };

    int max_requests_;
    int window_ms_;
    mutable std::mutex mutex_;
    std::unordered_map<std::string, ClientInfo> clients_;
};

/**
 * @brief 输入验证器
 *
 * 验证接收到的消息是否符合安全要求。
 */
class InputValidator {
public:
    /**
     * @brief 构造函数
     * @param max_message_size 最大消息大小
     * @param max_string_length 最大字符串长度
     */
    InputValidator(size_t max_message_size = 1048576,
                   size_t max_string_length = 65536);

    /**
     * @brief 验证消息
     * @param msg 消息
     * @return 验证是否通过
     */
    bool validate(const Message& msg) const;

    /**
     * @brief 验证文本消息
     * @param text 文本内容
     * @return 验证是否通过
     */
    bool validate_text(const std::string& text) const;

    /**
     * @brief 验证二进制消息
     * @param data 二进制数据
     * @return 验证是否通过
     */
    bool validate_binary(const std::vector<uint8_t>& data) const;

private:
    size_t max_message_size_;
    size_t max_string_length_;
};

/**
 * @brief 安全管理器
 *
 * 整合所有安全组件，提供统一的安全管理接口。
 */
class SecurityManager {
public:
    SecurityManager() = default;
    ~SecurityManager() = default;

    /**
     * @brief 设置认证器
     */
    void set_authenticator(std::shared_ptr<Authenticator> auth) {
        authenticator_ = std::move(auth);
    }

    /**
     * @brief 获取认证器
     */
    std::shared_ptr<Authenticator> authenticator() const { return authenticator_; }

    /**
     * @brief 获取速率限制器
     */
    RateLimiter& rate_limiter() {
        if (!rate_limiter_ptr_) {
            rate_limiter_ptr_ = std::make_unique<RateLimiter>();
        }
        return *rate_limiter_ptr_;
    }

    /**
     * @brief 获取输入验证器
     */
    const InputValidator& input_validator() const {
        if (!input_validator_ptr_) {
            input_validator_ptr_ = std::make_unique<InputValidator>();
        }
        return *input_validator_ptr_;
    }

    /**
     * @brief 设置是否启用认证
     */
    void set_auth_required(bool required) { auth_required_ = required; }

    /**
     * @brief 是否需要认证
     */
    bool is_auth_required() const { return auth_required_; }

    /**
     * @brief 设置是否启用速率限制
     */
    void set_rate_limit_enabled(bool enabled) { rate_limit_enabled_ = enabled; }

    /**
     * @brief 是否启用速率限制
     */
    bool is_rate_limit_enabled() const { return rate_limit_enabled_; }

    /**
     * @brief 设置速率限制参数
     */
    void set_rate_limit(int max_requests, int window_ms) {
        rate_limiter_ptr_ = std::make_unique<RateLimiter>(max_requests, window_ms);
    }

    /**
     * @brief 设置最大消息大小
     */
    void set_max_message_size(size_t size) {
        input_validator_ptr_ = std::make_unique<InputValidator>(size, 65536);
    }

    /**
     * @brief 验证连接
     * @return 是否通过安全检查
     */
    bool validate_connection(ConnectionPtr conn, const std::string& token = "");

    /**
     * @brief 验证消息
     * @return 是否通过安全检查
     */
    bool validate_message(ConnectionPtr conn, const Message& msg);

private:
    std::shared_ptr<Authenticator> authenticator_;
    mutable std::unique_ptr<RateLimiter> rate_limiter_ptr_;
    mutable std::unique_ptr<InputValidator> input_validator_ptr_;
    bool auth_required_ = false;
    bool rate_limit_enabled_ = false;
};

} // namespace ws
