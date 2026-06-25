#ifndef CPP_STANDARDS_NAMING_H
#define CPP_STANDARDS_NAMING_H

/**
 * @file naming.h
 * @brief 命名规范示例头文件
 *
 * 本文件展示 C++ 命名规范的最佳实践，包括：
 * - 变量命名
 * - 函数命名
 * - 类命名
 * - 常量命名
 * - 宏命名
 * - 命名空间命名
 */

#include <string>
#include <vector>
#include <cstdint>

namespace cpp_standards {

// ============================================================================
// 常量命名 - 使用 k 前缀 + PascalCase
// ============================================================================

/// 最大重试次数
constexpr int kMaxRetryCount = 3;

/// 默认缓冲区大小
constexpr size_t kDefaultBufferSize = 1024;

/// 无效用户ID
constexpr int kInvalidUserId = -1;

// ============================================================================
// 类型别名 - 使用 PascalCase
// ============================================================================

/// 用户ID类型
using UserId = int64_t;

/// 字符串视图类型
using StringView = std::string_view;

/// 字符串向量类型
using StringVector = std::vector<std::string>;

// ============================================================================
// 枚举 - 使用 PascalCase
// ============================================================================

/**
 * @brief 用户状态枚举
 *
 * 表示用户的当前状态
 */
enum class UserStatus {
    kActive,      ///< 活跃状态
    kInactive,    ///< 非活跃状态
    kSuspended,   ///< 挂起状态
    kDeleted      ///< 已删除状态
};

/**
 * @brief 日志级别枚举
 *
 * 表示日志的严重程度
 */
enum class LogLevel {
    kDebug,       ///< 调试级别
    kInfo,        ///< 信息级别
    kWarning,     ///< 警告级别
    kError,       ///< 错误级别
    kFatal        ///< 致命级别
};

// ============================================================================
// 类命名 - 使用 PascalCase
// ============================================================================

/**
 * @brief 用户管理器类
 *
 * 负责管理用户信息和操作
 */
class UserManager {
public:
    /**
     * @brief 构造函数
     * @param max_users 最大用户数量
     */
    explicit UserManager(size_t max_users);

    /**
     * @brief 析构函数
     */
    ~UserManager() = default;

    /**
     * @brief 添加用户
     * @param name 用户名
     * @param email 邮箱
     * @return 用户ID
     */
    UserId addUser(const std::string& name, const std::string& email);

    /**
     * @brief 获取用户名
     * @param user_id 用户ID
     * @return 用户名
     */
    std::string getUserName(UserId user_id) const;

    /**
     * @brief 检查用户是否存在
     * @param user_id 用户ID
     * @return 是否存在
     */
    bool hasUser(UserId user_id) const;

    /**
     * @brief 获取用户数量
     * @return 用户数量
     */
    size_t getUserCount() const;

private:
    /// 用户信息结构体
    struct UserInfo {
        UserId id;           ///< 用户ID
        std::string name;    ///< 用户名
        std::string email;   ///< 邮箱
        UserStatus status;   ///< 用户状态
    };

    size_t max_users_;                    ///< 最大用户数量
    std::vector<UserInfo> users_;         ///< 用户列表
    UserId next_user_id_;                 ///< 下一个用户ID
};

// ============================================================================
// 函数命名 - 使用 camelCase
// ============================================================================

/**
 * @brief 验证邮箱格式
 * @param email 邮箱地址
 * @return 是否有效
 */
bool isValidEmail(const std::string& email);

/**
 * @brief 计算字符串哈希值
 * @param str 输入字符串
 * @return 哈希值
 */
size_t calculateHash(const std::string& str);

/**
 * @brief 格式化用户信息
 * @param name 用户名
 * @param email 邮箱
 * @return 格式化后的字符串
 */
std::string formatUserInfo(const std::string& name, const std::string& email);

/**
 * @brief 解析配置文件
 * @param file_path 文件路径
 * @return 配置键值对
 */
std::vector<std::pair<std::string, std::string>>
parseConfigFile(const std::string& file_path);

// ============================================================================
// 命名空间命名 - 使用 snake_case
// ============================================================================

namespace user_utils {
    /**
     * @brief 验证用户名
     * @param name 用户名
     * @return 是否有效
     */
    bool validateUserName(const std::string& name);

    /**
     * @brief 生成用户ID
     * @return 新的用户ID
     */
    UserId generateUserId();
}  // namespace user_utils

namespace string_utils {
    /**
     * @brief 去除首尾空格
     * @param str 输入字符串
     * @return 处理后的字符串
     */
    std::string trim(const std::string& str);

    /**
     * @brief 转换为小写
     * @param str 输入字符串
     * @return 转换后的字符串
     */
    std::string toLowerCase(const std::string& str);
}  // namespace string_utils

}  // namespace cpp_standards

#endif  // CPP_STANDARDS_NAMING_H
