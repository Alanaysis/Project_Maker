#ifndef EXAMPLES_GOOD_HEADER_H
#define EXAMPLES_GOOD_HEADER_H

/**
 * @file good_header.h
 * @brief 良好头文件规范示例
 *
 * 本文件展示 C++ 头文件规范的最佳实践，包括：
 * - 头文件保护
 * - #include 顺序
 * - 前向声明
 * - 命名空间
 * - 类声明
 */

// ============================================================================
// 系统头文件
// ============================================================================
#include <cstdint>
#include <string>
#include <vector>

// ============================================================================
// 第三方库头文件
// ============================================================================
// #include <third_party/library.h>

// ============================================================================
// 项目头文件
// ============================================================================
// #include "project/module.h"

// ============================================================================
// 前向声明
// ============================================================================
namespace cpp_standards {
class Logger;
class ConfigManager;
}  // namespace cpp_standards

// ============================================================================
// 命名空间
// ============================================================================
namespace cpp_standards {

// ============================================================================
// 类型别名
// ============================================================================

/// 用户ID类型
using UserId = int64_t;

/// 字符串视图类型
using StringView = std::string_view;

// ============================================================================
// 枚举
// ============================================================================

/**
 * @brief 用户状态枚举
 */
enum class UserStatus {
    kActive,      ///< 活跃状态
    kInactive,    ///< 非活跃状态
    kSuspended,   ///< 挂起状态
    kDeleted      ///< 已删除状态
};

// ============================================================================
// 类声明
// ============================================================================

/**
 * @brief 用户管理器类
 *
 * 负责管理用户信息和操作。该类提供以下功能：
 * - 添加用户
 * - 删除用户
 * - 查询用户
 * - 更新用户信息
 *
 * 使用示例：
 * @code
 *   UserManager manager(100);
 *   UserId id = manager.addUser("Alice", "alice@example.com");
 *   std::string name = manager.getUserName(id);
 * @endcode
 *
 * @note 该类是线程安全的
 * @see User
 */
class UserManager {
public:
    /**
     * @brief 构造函数
     * @param max_users 最大用户数量
     * @throw std::invalid_argument 如果 max_users 为 0
     */
    explicit UserManager(size_t max_users);

    /**
     * @brief 析构函数
     */
    ~UserManager();

    /**
     * @brief 拷贝构造函数（删除）
     */
    UserManager(const UserManager&) = delete;

    /**
     * @brief 拷贝赋值运算符（删除）
     */
    UserManager& operator=(const UserManager&) = delete;

    /**
     * @brief 移动构造函数
     */
    UserManager(UserManager&& other) noexcept;

    /**
     * @brief 移动赋值运算符
     */
    UserManager& operator=(UserManager&& other) noexcept;

    /**
     * @brief 添加用户
     * @param name 用户名
     * @param email 邮箱
     * @return 用户ID
     * @throw std::invalid_argument 如果参数无效
     * @throw std::runtime_error 如果达到最大用户数量
     */
    UserId addUser(const std::string& name, const std::string& email);

    /**
     * @brief 删除用户
     * @param user_id 用户ID
     * @return 是否成功
     * @throw std::invalid_argument 如果用户ID无效
     */
    bool removeUser(UserId user_id);

    /**
     * @brief 获取用户名
     * @param user_id 用户ID
     * @return 用户名
     * @throw std::invalid_argument 如果用户ID无效
     */
    std::string getUserName(UserId user_id) const;

    /**
     * @brief 获取用户邮箱
     * @param user_id 用户ID
     * @return 用户邮箱
     * @throw std::invalid_argument 如果用户ID无效
     */
    std::string getUserEmail(UserId user_id) const;

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

    /**
     * @brief 获取最大用户数量
     * @return 最大用户数量
     */
    size_t getMaxUsers() const;

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

    /**
     * @brief 查找用户
     * @param user_id 用户ID
     * @return 用户索引，-1 表示未找到
     */
    int findUserIndex(UserId user_id) const;
};

// ============================================================================
// 函数声明
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

// ============================================================================
// 内联函数
// ============================================================================

/**
 * @brief 检查用户ID是否有效
 * @param user_id 用户ID
 * @return 是否有效
 */
inline bool isValidUserId(UserId user_id) {
    return user_id > 0;
}

}  // namespace cpp_standards

#endif  // EXAMPLES_GOOD_HEADER_H
