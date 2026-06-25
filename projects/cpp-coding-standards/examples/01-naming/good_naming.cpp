/**
 * @file good_naming.cpp
 * @brief 良好命名规范示例
 *
 * 本文件展示符合 C++ 命名规范的良好代码示例。
 * 遵循以下命名规则：
 * - 变量：camelCase 或 snake_case
 * - 函数：camelCase
 * - 类：PascalCase
 * - 常量：k + PascalCase
 * - 宏：UPPER_CASE
 * - 命名空间：snake_case
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <algorithm>

// ============================================================================
// 常量命名示例 - 使用 k 前缀 + PascalCase
// ============================================================================

/// 最大重试次数
constexpr int kMaxRetryCount = 3;

/// 默认缓冲区大小
constexpr size_t kDefaultBufferSize = 1024;

/// 无效用户ID
constexpr int kInvalidUserId = -1;

/// 圆周率
constexpr double kPi = 3.14159265358979323846;

// ============================================================================
// 枚举命名示例 - 使用 PascalCase
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

/**
 * @brief 日志级别枚举
 */
enum class LogLevel {
    kDebug,       ///< 调试级别
    kInfo,        ///< 信息级别
    kWarning,     ///< 警告级别
    kError,       ///< 错误级别
    kFatal        ///< 致命级别
};

// ============================================================================
// 类命名示例 - 使用 PascalCase
// ============================================================================

/**
 * @brief 用户类
 *
 * 展示良好的类命名和成员命名
 */
class User {
public:
    /**
     * @brief 构造函数
     * @param user_id 用户ID
     * @param user_name 用户名
     * @param user_email 用户邮箱
     */
    User(int user_id, std::string user_name, std::string user_email)
        : id_(user_id)
        , name_(std::move(user_name))
        , email_(std::move(user_email))
        , status_(UserStatus::kActive) {}

    /**
     * @brief 获取用户ID
     * @return 用户ID
     */
    int getId() const { return id_; }

    /**
     * @brief 获取用户名
     * @return 用户名
     */
    const std::string& getName() const { return name_; }

    /**
     * @brief 获取用户邮箱
     * @return 用户邮箱
     */
    const std::string& getEmail() const { return email_; }

    /**
     * @brief 获取用户状态
     * @return 用户状态
     */
    UserStatus getStatus() const { return status_; }

    /**
     * @brief 设置用户名
     * @param new_name 新用户名
     */
    void setName(std::string new_name) {
        name_ = std::move(new_name);
    }

    /**
     * @brief 设置用户邮箱
     * @param new_email 新邮箱
     */
    void setEmail(std::string new_email) {
        email_ = std::move(new_email);
    }

    /**
     * @brief 设置用户状态
     * @param new_status 新状态
     */
    void setStatus(UserStatus new_status) {
        status_ = new_status;
    }

    /**
     * @brief 检查用户是否活跃
     * @return 是否活跃
     */
    bool isActive() const {
        return status_ == UserStatus::kActive;
    }

private:
    int id_;              ///< 用户ID
    std::string name_;    ///< 用户名
    std::string email_;   ///< 用户邮箱
    UserStatus status_;   ///< 用户状态
};

// ============================================================================
// 函数命名示例 - 使用 camelCase
// ============================================================================

/**
 * @brief 验证邮箱格式
 * @param email 邮箱地址
 * @return 是否有效
 */
bool isValidEmail(const std::string& email) {
    // 简单的邮箱验证逻辑
    size_t at_pos = email.find('@');
    size_t dot_pos = email.rfind('.');

    if (at_pos == std::string::npos || dot_pos == std::string::npos) {
        return false;
    }

    return at_pos < dot_pos && at_pos > 0 && dot_pos < email.length() - 1;
}

/**
 * @brief 计算字符串哈希值
 * @param str 输入字符串
 * @return 哈希值
 */
size_t calculateHash(const std::string& str) {
    size_t hash = 5381;
    for (char c : str) {
        hash = ((hash << 5) + hash) + static_cast<size_t>(c);
    }
    return hash;
}

/**
 * @brief 格式化用户信息
 * @param user 用户对象
 * @return 格式化后的字符串
 */
std::string formatUserInfo(const User& user) {
    return "User[id=" + std::to_string(user.getId()) +
           ", name=" + user.getName() +
           ", email=" + user.getEmail() + "]";
}

/**
 * @brief 查找用户
 * @param users 用户列表
 * @param user_id 用户ID
 * @return 用户指针（如果找到）
 */
User* findUserById(std::vector<User>& users, int user_id) {
    for (auto& user : users) {
        if (user.getId() == user_id) {
            return &user;
        }
    }
    return nullptr;
}

/**
 * @brief 过滤活跃用户
 * @param users 用户列表
 * @return 活跃用户列表
 */
std::vector<User> filterActiveUsers(const std::vector<User>& users) {
    std::vector<User> active_users;
    for (const auto& user : users) {
        if (user.isActive()) {
            active_users.push_back(user);
        }
    }
    return active_users;
}

// ============================================================================
// 命名空间命名示例 - 使用 snake_case
// ============================================================================

namespace user_utils {
    /**
     * @brief 验证用户名
     * @param name 用户名
     * @return 是否有效
     */
    bool validateUserName(const std::string& name) {
        if (name.empty() || name.length() > 50) {
            return false;
        }

        // 检查是否只包含字母、数字和下划线
        for (char c : name) {
            if (!std::isalnum(c) && c != '_') {
                return false;
            }
        }

        return true;
    }

    /**
     * @brief 生成用户ID
     * @return 新的用户ID
     */
    int generateUserId() {
        static int next_id = 1;
        return next_id++;
    }
}  // namespace user_utils

namespace string_utils {
    /**
     * @brief 去除首尾空格
     * @param str 输入字符串
     * @return 处理后的字符串
     */
    std::string trim(const std::string& str) {
        size_t start = str.find_first_not_of(" \t\n\r");
        size_t end = str.find_last_not_of(" \t\n\r");

        if (start == std::string::npos) {
            return "";
        }

        return str.substr(start, end - start + 1);
    }

    /**
     * @brief 转换为小写
     * @param str 输入字符串
     * @return 转换后的字符串
     */
    std::string toLowerCase(const std::string& str) {
        std::string result = str;
        std::transform(result.begin(), result.end(), result.begin(),
                       [](unsigned char c) { return std::tolower(c); });
        return result;
    }
}  // namespace string_utils

// ============================================================================
// 演示函数
// ============================================================================

/**
 * @brief 演示良好命名规范
 */
void demonstrateGoodNaming() {
    std::cout << "=== 良好命名规范示例 ===" << std::endl;

    // 常量命名
    std::cout << "\n1. 常量命名 (k + PascalCase):" << std::endl;
    std::cout << "   kMaxRetryCount = " << kMaxRetryCount << std::endl;
    std::cout << "   kDefaultBufferSize = " << kDefaultBufferSize << std::endl;
    std::cout << "   kPi = " << kPi << std::endl;

    // 变量命名
    std::cout << "\n2. 变量命名 (camelCase):" << std::endl;
    int userAge = 25;
    std::string userName = "Alice";
    double accountBalance = 1000.50;
    std::vector<int> userScores = {95, 87, 92};

    std::cout << "   userAge = " << userAge << std::endl;
    std::cout << "   userName = " << userName << std::endl;
    std::cout << "   accountBalance = " << accountBalance << std::endl;
    std::cout << "   userScores.size() = " << userScores.size() << std::endl;

    // 类命名
    std::cout << "\n3. 类命名 (PascalCase):" << std::endl;
    User user(1, "Bob", "bob@example.com");
    std::cout << "   User: " << formatUserInfo(user) << std::endl;

    // 函数命名
    std::cout << "\n4. 函数命名 (camelCase):" << std::endl;
    std::cout << "   isValidEmail('test@example.com') = "
              << (isValidEmail("test@example.com") ? "true" : "false") << std::endl;
    std::cout << "   calculateHash('hello') = " << calculateHash("hello") << std::endl;

    // 命名空间
    std::cout << "\n5. 命名空间 (snake_case):" << std::endl;
    std::cout << "   user_utils::validateUserName('alice') = "
              << (user_utils::validateUserName("alice") ? "true" : "false") << std::endl;
    std::cout << "   string_utils::trim('  hello  ') = '"
              << string_utils::trim("  hello  ") << "'" << std::endl;

    // 枚举命名
    std::cout << "\n6. 枚举命名 (k + PascalCase):" << std::endl;
    UserStatus status = UserStatus::kActive;
    std::cout << "   UserStatus::kActive" << std::endl;

    LogLevel level = LogLevel::kInfo;
    std::cout << "   LogLevel::kInfo" << std::endl;
}
