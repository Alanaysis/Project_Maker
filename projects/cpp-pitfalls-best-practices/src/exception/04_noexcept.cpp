/**
 * @file 04_noexcept.cpp
 * @brief noexcept 使用陷阱示例
 *
 * noexcept 使用：错误使用 noexcept 导致的问题
 * 危害：程序终止、性能下降、难以调试
 */

#include <iostream>
#include <vector>
#include <string>
#include <stdexcept>
#include <utility>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：noexcept 函数抛出异常
 *
 * 问题：noexcept 函数抛出异常导致程序终止
 */
void bad_noexcept_throw() noexcept {
    throw std::runtime_error("error");  // 程序终止！
}

/**
 * 错误示例 2：移动构造函数不是 noexcept
 *
 * 问题：容器不会使用移动语义
 */
class BadMove {
public:
    BadMove() = default;
    BadMove(BadMove&& other) {  // 不是 noexcept
        data_ = other.data_;
        other.data_ = nullptr;
    }

private:
    int* data_ = nullptr;
};

/**
 * 错误示例 3：析构函数抛出异常
 *
 * 问题：析构函数默认是 noexcept
 */
class BadDestructor {
public:
    ~BadDestructor() noexcept(false) {  // 允许抛出异常
        throw std::runtime_error("error");  // 危险！
    }
};

/**
 * 错误示例 4：条件 noexcept 不当
 *
 * 问题：条件 noexcept 表达式错误
 */
template <typename T>
void bad_conditional_noexcept() noexcept(noexcept(T())) {
    // 如果 T 的默认构造函数抛出异常，这里也会抛出
    T obj;
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：移动构造函数使用 noexcept
 *
 * 解决方案：移动构造函数标记为 noexcept
 */
class GoodMove {
public:
    GoodMove() = default;
    GoodMove(GoodMove&& other) noexcept : data_(other.data_) {
        other.data_ = nullptr;
    }

    GoodMove& operator=(GoodMove&& other) noexcept {
        if (this != &other) {
            data_ = other.data_;
            other.data_ = nullptr;
        }
        return *this;
    }

private:
    int* data_ = nullptr;
};

void good_move_example() {
    std::vector<GoodMove> vec;
    vec.reserve(10);
    for (int i = 0; i < 10; i++) {
        vec.push_back(GoodMove());
    }
    std::cout << "移动语义优化成功" << std::endl;
}

/**
 * 正确示例 2：析构函数使用 noexcept
 *
 * 解决方案：析构函数应该标记为 noexcept
 */
class GoodDestructor {
public:
    ~GoodDestructor() noexcept {
        // 不抛出异常
        cleanup();
    }

private:
    void cleanup() noexcept {
        // 清理操作
    }
};

/**
 * 正确示例 3：swap 函数使用 noexcept
 *
 * 解决方案：swap 函数应该标记为 noexcept
 */
class GoodSwappable {
public:
    GoodSwappable() = default;

    void swap(GoodSwappable& other) noexcept {
        std::swap(data_, other.data_);
    }

private:
    int* data_ = nullptr;
};

void swap(GoodSwappable& a, GoodSwappable& b) noexcept {
    a.swap(b);
}

/**
 * 正确示例 4：条件 noexcept
 *
 * 解决方案：正确使用条件 noexcept
 */
template <typename T>
void good_conditional_noexcept() noexcept(std::is_nothrow_default_constructible_v<T>) {
    T obj;
}

/**
 * 正确示例 5：noexcept 运算符
 *
 * 解决方案：使用 noexcept 运算符检查
 */
void good_noexcept_operator() {
    std::cout << "int 默认构造 noexcept: "
              << std::is_nothrow_default_constructible_v<int> << std::endl;
    std::cout << "string 默认构造 noexcept: "
              << std::is_nothrow_default_constructible_v<std::string> << std::endl;
}

/**
 * 正确示例 6：使用 std::move_if_noexcept
 *
 * 解决方案：根据 noexcept 选择移动或拷贝
 */
class GoodMoveIfNoexcept {
public:
    GoodMoveIfNoexcept() = default;

    // noexcept 移动构造
    GoodMoveIfNoexcept(GoodMoveIfNoexcept&& other) noexcept : data_(other.data_) {
        other.data_ = nullptr;
        std::cout << "移动构造" << std::endl;
    }

    // 拷贝构造
    GoodMoveIfNoexcept(const GoodMoveIfNoexcept& other) : data_(new int(*other.data_)) {
        std::cout << "拷贝构造" << std::endl;
    }

private:
    int* data_ = new int(42);
};

void good_move_if_noexcept() {
    std::vector<GoodMoveIfNoexcept> vec;
    vec.reserve(10);
    for (int i = 0; i < 5; i++) {
        vec.push_back(GoodMoveIfNoexcept());
    }
}

/**
 * 正确示例 7：noexcept 和异常安全
 *
 * 解决方案：noexcept 保证异常安全
 */
class GoodExceptionSafe {
public:
    void add(int value) noexcept {
        try {
            auto temp = std::make_unique<int[]>(size_ + 1);
            for (size_t i = 0; i < size_; i++) {
                temp[i] = data_[i];
            }
            temp[size_] = value;
            data_.swap(temp);
            size_++;
        } catch (...) {
            // 吞掉异常，保持状态不变
            std::cout << "异常被捕获，状态不变" << std::endl;
        }
    }

private:
    std::unique_ptr<int[]> data_;
    size_t size_ = 0;
};

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== noexcept 使用陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] noexcept 函数抛出异常" << std::endl;
    std::cout << "问题：noexcept 函数抛出异常导致程序终止" << std::endl;
    // bad_noexcept_throw();  // 注释掉，避免程序终止
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 移动构造函数使用 noexcept" << std::endl;
    good_move_example();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 析构函数使用 noexcept" << std::endl;
    GoodDestructor destructor;
    std::cout << std::endl;

    std::cout << "[正确示例 3] swap 函数使用 noexcept" << std::endl;
    GoodSwappable a, b;
    swap(a, b);
    std::cout << std::endl;

    std::cout << "[正确示例 4] 条件 noexcept" << std::endl;
    good_conditional_noexcept<int>();
    std::cout << std::endl;

    std::cout << "[正确示例 5] noexcept 运算符" << std::endl;
    good_noexcept_operator();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用 move_if_noexcept" << std::endl;
    good_move_if_noexcept();
    std::cout << std::endl;

    std::cout << "[正确示例 7] noexcept 和异常安全" << std::endl;
    GoodExceptionSafe safe;
    safe.add(1);
    safe.add(2);
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
