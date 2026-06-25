/**
 * @file good_class_design.cpp
 * @brief 良好类设计规范示例
 *
 * 本文件展示 C++ 类设计规范的最佳实践，包括：
 * - 成员顺序
 * - 访问控制
 * - 构造函数设计
 * - 析构函数设计
 * - 运算符重载
 * - 友元使用
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <algorithm>

// ============================================================================
// 良好类设计示例 - 成员顺序和访问控制
// ============================================================================

/**
 * @brief 用户类
 *
 * 展示良好的类设计，包括：
 * - 合理的成员顺序
 * - 正确的访问控制
 * - 完整的构造函数系列
 * - 清晰的公共接口
 */
class User {
public:
    // =========================================================================
    // 类型别名
    // =========================================================================

    /// 用户ID类型
    using UserId = int64_t;

    // =========================================================================
    // 构造函数和析构函数
    // =========================================================================

    /**
     * @brief 默认构造函数
     */
    User() = default;

    /**
     * @brief 参数化构造函数
     * @param id 用户ID
     * @param name 用户名
     * @param email 邮箱
     */
    User(UserId id, std::string name, std::string email)
        : id_(id)
        , name_(std::move(name))
        , email_(std::move(email))
        , is_active_(true) {}

    /**
     * @brief 拷贝构造函数
     */
    User(const User& other) = default;

    /**
     * @brief 移动构造函数
     */
    User(User&& other) noexcept = default;

    /**
     * @brief 析构函数
     */
    ~User() = default;

    // =========================================================================
    // 赋值运算符
    // =========================================================================

    /**
     * @brief 拷贝赋值运算符
     */
    User& operator=(const User& other) = default;

    /**
     * @brief 移动赋值运算符
     */
    User& operator=(User&& other) noexcept = default;

    // =========================================================================
    // 公共接口
    // =========================================================================

    /**
     * @brief 获取用户ID
     * @return 用户ID
     */
    UserId getId() const { return id_; }

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
     * @brief 检查用户是否活跃
     * @return 是否活跃
     */
    bool isActive() const { return is_active_; }

    /**
     * @brief 设置用户名
     * @param name 新用户名
     */
    void setName(std::string name) { name_ = std::move(name); }

    /**
     * @brief 设置用户邮箱
     * @param email 新邮箱
     */
    void setEmail(std::string email) { email_ = std::move(email); }

    /**
     * @brief 设置用户活跃状态
     * @param is_active 是否活跃
     */
    void setActive(bool is_active) { is_active_ = is_active; }

    // =========================================================================
    // 运算符重载
    // =========================================================================

    /**
     * @brief 相等运算符
     * @param other 另一个用户
     * @return 是否相等
     */
    bool operator==(const User& other) const {
        return id_ == other.id_;
    }

    /**
     * @brief 不等运算符
     * @param other 另一个用户
     * @return 是否不等
     */
    bool operator!=(const User& other) const {
        return !(*this == other);
    }

    /**
     * @brief 小于运算符（用于排序）
     * @param other 另一个用户
     * @return 是否小于
     */
    bool operator<(const User& other) const {
        return id_ < other.id_;
    }

    // =========================================================================
    // 友元函数
    // =========================================================================

    /**
     * @brief 输出运算符
     * @param os 输出流
     * @param user 用户对象
     * @return 输出流
     */
    friend std::ostream& operator<<(std::ostream& os, const User& user);

private:
    // =========================================================================
    // 私有成员
    // =========================================================================

    UserId id_ = 0;              ///< 用户ID
    std::string name_;           ///< 用户名
    std::string email_;          ///< 邮箱
    bool is_active_ = false;     ///< 是否活跃
};

// ============================================================================
// 运算符重载实现
// ============================================================================

std::ostream& operator<<(std::ostream& os, const User& user) {
    os << "User[id=" << user.id_
       << ", name=" << user.name_
       << ", email=" << user.email_
       << ", active=" << (user.is_active_ ? "true" : "false")
       << "]";
    return os;
}

// ============================================================================
// 良好类设计示例 - 管理类
// ============================================================================

/**
 * @brief 用户管理器类
 *
 * 展示良好的管理类设计，包括：
 * - RAII 原则
 * - 异常安全
 * - 清晰的接口
 */
class UserManager {
public:
    // =========================================================================
    // 构造函数和析构函数
    // =========================================================================

    /**
     * @brief 构造函数
     * @param max_users 最大用户数量
     */
    explicit UserManager(size_t max_users)
        : max_users_(max_users) {
        users_.reserve(max_users);
    }

    /**
     * @brief 析构函数
     */
    ~UserManager() = default;

    // =========================================================================
    // 禁用拷贝
    // =========================================================================

    UserManager(const UserManager&) = delete;
    UserManager& operator=(const UserManager&) = delete;

    // =========================================================================
    // 允许移动
    // =========================================================================

    UserManager(UserManager&&) noexcept = default;
    UserManager& operator=(UserManager&&) noexcept = default;

    // =========================================================================
    // 公共接口
    // =========================================================================

    /**
     * @brief 添加用户
     * @param name 用户名
     * @param email 邮箱
     * @return 用户ID
     * @throw std::runtime_error 如果达到最大用户数量
     */
    User::UserId addUser(const std::string& name, const std::string& email) {
        if (users_.size() >= max_users_) {
            throw std::runtime_error("Maximum number of users reached");
        }

        User::UserId id = next_id_++;
        users_.emplace_back(id, name, email);
        return id;
    }

    /**
     * @brief 删除用户
     * @param id 用户ID
     * @return 是否成功
     */
    bool removeUser(User::UserId id) {
        auto it = std::find_if(users_.begin(), users_.end(),
                               [id](const User& u) { return u.getId() == id; });

        if (it == users_.end()) {
            return false;
        }

        users_.erase(it);
        return true;
    }

    /**
     * @brief 查找用户
     * @param id 用户ID
     * @return 用户指针，如果未找到返回 nullptr
     */
    User* findUser(User::UserId id) {
        auto it = std::find_if(users_.begin(), users_.end(),
                               [id](const User& u) { return u.getId() == id; });

        return it != users_.end() ? &(*it) : nullptr;
    }

    /**
     * @brief 获取用户数量
     * @return 用户数量
     */
    size_t getUserCount() const { return users_.size(); }

    /**
     * @brief 获取最大用户数量
     * @return 最大用户数量
     */
    size_t getMaxUsers() const { return max_users_; }

private:
    size_t max_users_;              ///< 最大用户数量
    std::vector<User> users_;       ///< 用户列表
    User::UserId next_id_ = 1;      ///< 下一个用户ID
};

// ============================================================================
// 良好类设计示例 - 值类型类
// ============================================================================

/**
 * @brief 二维点类
 *
 * 展示良好的值类型类设计，包括：
 * - 所有构造函数
 * - 运算符重载
 * - 常量正确性
 */
class Point2D {
public:
    // =========================================================================
    // 构造函数
    // =========================================================================

    Point2D() = default;

    Point2D(double x, double y) : x_(x), y_(y) {}

    Point2D(const Point2D&) = default;
    Point2D(Point2D&&) noexcept = default;

    ~Point2D() = default;

    // =========================================================================
    // 赋值运算符
    // =========================================================================

    Point2D& operator=(const Point2D&) = default;
    Point2D& operator=(Point2D&&) noexcept = default;

    // =========================================================================
    // 访问器
    // =========================================================================

    double getX() const { return x_; }
    double getY() const { return y_; }

    void setX(double x) { x_ = x; }
    void setY(double y) { y_ = y; }

    // =========================================================================
    // 算术运算符
    // =========================================================================

    Point2D operator+(const Point2D& other) const {
        return {x_ + other.x_, y_ + other.y_};
    }

    Point2D operator-(const Point2D& other) const {
        return {x_ - other.x_, y_ - other.y_};
    }

    Point2D operator*(double scalar) const {
        return {x_ * scalar, y_ * scalar};
    }

    Point2D& operator+=(const Point2D& other) {
        x_ += other.x_;
        y_ += other.y_;
        return *this;
    }

    Point2D& operator-=(const Point2D& other) {
        x_ -= other.x_;
        y_ -= other.y_;
        return *this;
    }

    Point2D& operator*=(double scalar) {
        x_ *= scalar;
        y_ *= scalar;
        return *this;
    }

    // =========================================================================
    // 比较运算符
    // =========================================================================

    bool operator==(const Point2D& other) const {
        return x_ == other.x_ && y_ == other.y_;
    }

    bool operator!=(const Point2D& other) const {
        return !(*this == other);
    }

    // =========================================================================
    // 友元函数
    // =========================================================================

    friend std::ostream& operator<<(std::ostream& os, const Point2D& point);

    /**
     * @brief 标量乘法（标量在左）
     */
    friend Point2D operator*(double scalar, const Point2D& point);

private:
    double x_ = 0.0;  ///< X 坐标
    double y_ = 0.0;  ///< Y 坐标
};

std::ostream& operator<<(std::ostream& os, const Point2D& point) {
    os << "Point2D(" << point.x_ << ", " << point.y_ << ")";
    return os;
}

Point2D operator*(double scalar, const Point2D& point) {
    return point * scalar;
}

// ============================================================================
// 演示函数
// ============================================================================

/**
 * @brief 演示良好类设计
 */
void demonstrateGoodClassDesign() {
    std::cout << "=== 良好类设计规范示例 ===" << std::endl;

    // 用户类示例
    std::cout << "\n1. 用户类示例:" << std::endl;
    User user(1, "Alice", "alice@example.com");
    std::cout << "   " << user << std::endl;

    user.setName("Alice Smith");
    std::cout << "   修改后: " << user << std::endl;

    // 用户管理器示例
    std::cout << "\n2. 用户管理器示例:" << std::endl;
    UserManager manager(10);
    auto id1 = manager.addUser("Bob", "bob@example.com");
    auto id2 = manager.addUser("Charlie", "charlie@example.com");
    std::cout << "   用户数量: " << manager.getUserCount() << std::endl;

    User* found = manager.findUser(id1);
    if (found) {
        std::cout << "   找到用户: " << *found << std::endl;
    }

    // 二维点类示例
    std::cout << "\n3. 二维点类示例:" << std::endl;
    Point2D p1(1.0, 2.0);
    Point2D p2(3.0, 4.0);
    Point2D p3 = p1 + p2;
    std::cout << "   " << p1 << " + " << p2 << " = " << p3 << std::endl;

    Point2D p4 = p1 * 2.0;
    std::cout << "   " << p1 << " * 2 = " << p4 << std::endl;

    Point2D p5 = 3.0 * p2;
    std::cout << "   3 * " << p2 << " = " << p5 << std::endl;
}
