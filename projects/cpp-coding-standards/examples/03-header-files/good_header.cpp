/**
 * @file good_header.cpp
 * @brief 良好头文件规范示例实现
 *
 * 本文件展示 C++ 头文件规范的最佳实践实现。
 */

#include "good_header.h"

#include <algorithm>
#include <stdexcept>

namespace cpp_standards {

// ============================================================================
// UserManager 实现
// ============================================================================

UserManager::UserManager(size_t max_users)
    : max_users_(max_users)
    , next_user_id_(1) {
    if (max_users == 0) {
        throw std::invalid_argument("max_users must be greater than 0");
    }
    users_.reserve(max_users);
}

UserManager::~UserManager() = default;

UserManager::UserManager(UserManager&& other) noexcept
    : max_users_(other.max_users_)
    , users_(std::move(other.users_))
    , next_user_id_(other.next_user_id_) {
    other.max_users_ = 0;
    other.next_user_id_ = 1;
}

UserManager& UserManager::operator=(UserManager&& other) noexcept {
    if (this != &other) {
        max_users_ = other.max_users_;
        users_ = std::move(other.users_);
        next_user_id_ = other.next_user_id_;
        other.max_users_ = 0;
        other.next_user_id_ = 1;
    }
    return *this;
}

UserId UserManager::addUser(const std::string& name, const std::string& email) {
    if (name.empty()) {
        throw std::invalid_argument("name cannot be empty");
    }

    if (email.empty() || !isValidEmail(email)) {
        throw std::invalid_argument("invalid email");
    }

    if (users_.size() >= max_users_) {
        throw std::runtime_error("maximum number of users reached");
    }

    UserId id = next_user_id_++;
    users_.push_back({id, name, email, UserStatus::kActive});
    return id;
}

bool UserManager::removeUser(UserId user_id) {
    int index = findUserIndex(user_id);
    if (index < 0) {
        return false;
    }

    users_.erase(users_.begin() + index);
    return true;
}

std::string UserManager::getUserName(UserId user_id) const {
    int index = findUserIndex(user_id);
    if (index < 0) {
        throw std::invalid_argument("invalid user id");
    }

    return users_[index].name;
}

std::string UserManager::getUserEmail(UserId user_id) const {
    int index = findUserIndex(user_id);
    if (index < 0) {
        throw std::invalid_argument("invalid user id");
    }

    return users_[index].email;
}

bool UserManager::hasUser(UserId user_id) const {
    return findUserIndex(user_id) >= 0;
}

size_t UserManager::getUserCount() const {
    return users_.size();
}

size_t UserManager::getMaxUsers() const {
    return max_users_;
}

int UserManager::findUserIndex(UserId user_id) const {
    for (size_t i = 0; i < users_.size(); ++i) {
        if (users_[i].id == user_id) {
            return static_cast<int>(i);
        }
    }
    return -1;
}

// ============================================================================
// 函数实现
// ============================================================================

bool isValidEmail(const std::string& email) {
    size_t at_pos = email.find('@');
    size_t dot_pos = email.rfind('.');

    if (at_pos == std::string::npos || dot_pos == std::string::npos) {
        return false;
    }

    return at_pos < dot_pos && at_pos > 0 && dot_pos < email.length() - 1;
}

size_t calculateHash(const std::string& str) {
    size_t hash = 5381;
    for (char c : str) {
        hash = ((hash << 5) + hash) + static_cast<size_t>(c);
    }
    return hash;
}

std::string formatUserInfo(const std::string& name, const std::string& email) {
    return "User[name=" + name + ", email=" + email + "]";
}

}  // namespace cpp_standards
