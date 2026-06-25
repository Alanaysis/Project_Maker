/**
 * @file 03_exception_propagation.cpp
 * @brief 异常传播陷阱示例
 *
 * 异常传播：异常在函数间传播时的问题
 * 危害：资源泄漏、状态不一致、难以调试
 */

#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include <memory>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：异常被意外捕获
 *
 * 问题：捕获过于宽泛的异常
 */
void bad_catch_all() {
    try {
        throw std::runtime_error("runtime error");
    } catch (...) {
        // 捕获所有异常，可能隐藏问题
        std::cout << "捕获异常" << std::endl;
    }
}

/**
 * 错误示例 2：异常被忽略
 *
 * 问题：捕获异常后不做处理
 */
void bad_ignore_exception() {
    try {
        throw std::runtime_error("error");
    } catch (const std::exception& e) {
        // 忽略异常
    }
}

/**
 * 错误示例 3：异常转换不当
 *
 * 问题：异常转换丢失信息
 */
void bad_exception_conversion() {
    try {
        throw std::runtime_error("original error");
    } catch (const std::exception& e) {
        // 丢失原始错误信息
        throw std::logic_error("converted error");
    }
}

/**
 * 错误示例 4：析构函数中抛出异常
 *
 * 问题：析构函数抛出异常导致程序终止
 */
class BadDestructor {
public:
    ~BadDestructor() {
        throw std::runtime_error("error in destructor");  // 危险！
    }
};

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：捕获特定异常
 *
 * 解决方案：捕获特定类型的异常
 */
void good_catch_specific() {
    try {
        throw std::runtime_error("runtime error");
    } catch (const std::runtime_error& e) {
        std::cout << "运行时错误: " << e.what() << std::endl;
    } catch (const std::logic_error& e) {
        std::cout << "逻辑错误: " << e.what() << std::endl;
    } catch (const std::exception& e) {
        std::cout << "其他错误: " << e.what() << std::endl;
    }
}

/**
 * 正确示例 2：异常链
 *
 * 解决方案：保留原始异常信息
 */
class ExceptionWithCause : public std::runtime_error {
public:
    ExceptionWithCause(const std::string& msg, std::exception_ptr cause)
        : std::runtime_error(msg), cause_(cause) {}

    std::exception_ptr cause() const { return cause_; }

private:
    std::exception_ptr cause_;
};

void good_exception_chain() {
    try {
        try {
            throw std::runtime_error("original error");
        } catch (const std::exception& e) {
            throw ExceptionWithCause("wrapped error", std::current_exception());
        }
    } catch (const ExceptionWithCause& e) {
        std::cout << "错误: " << e.what() << std::endl;
        try {
            std::rethrow_exception(e.cause());
        } catch (const std::exception& cause) {
            std::cout << "原因: " << cause.what() << std::endl;
        }
    }
}

/**
 * 正确示例 3：使用 std::throw_with_nested
 *
 * 解决方案：使用嵌套异常
 */
void good_nested_exception() {
    try {
        try {
            throw std::runtime_error("original error");
        } catch (const std::exception& e) {
            std::throw_with_nested(std::logic_error("wrapped error"));
        }
    } catch (const std::logic_error& e) {
        std::cout << "错误: " << e.what() << std::endl;
        try {
            std::rethrow_if_nested(e);
        } catch (const std::exception& nested) {
            std::cout << "嵌套错误: " << nested.what() << std::endl;
        }
    }
}

/**
 * 正确示例 4：析构函数中不抛出异常
 *
 * 解决方案：析构函数使用 noexcept
 */
class GoodDestructor {
public:
    ~GoodDestructor() noexcept {
        try {
            // 可能抛出异常的操作
            cleanup();
        } catch (...) {
            // 吞掉异常，不传播
            std::cout << "析构函数中捕获异常" << std::endl;
        }
    }

private:
    void cleanup() {
        // 清理操作
    }
};

/**
 * 正确示例 5：使用 RAII 管理资源
 *
 * 解决方案：使用 RAII 确保资源释放
 */
class GoodResource {
public:
    GoodResource() { std::cout << "获取资源" << std::endl; }
    ~GoodResource() { std::cout << "释放资源" << std::endl; }
};

void good_raii() {
    GoodResource res;
    throw std::runtime_error("error");
    // res 自动释放
}

/**
 * 正确示例 6：异常安全的函数
 *
 * 解决方案：函数保证异常安全
 */
class GoodContainer {
public:
    void add(int value) {
        auto temp = std::make_unique<int[]>(size_ + 1);
        for (size_t i = 0; i < size_; i++) {
            temp[i] = data_[i];
        }
        temp[size_] = value;
        data_.swap(temp);
        size_++;
    }

private:
    std::unique_ptr<int[]> data_;
    size_t size_ = 0;
};

void good_exception_safe_function() {
    GoodContainer container;
    container.add(1);
    container.add(2);
}

/**
 * 正确示例 7：使用异常处理策略
 *
 * 解决方案：定义明确的异常处理策略
 */
enum class ExceptionPolicy {
    Propagate,   // 传播异常
    LogAndRethrow,  // 记录后重新抛出
    Convert,     // 转换异常
    Swallow      // 吞掉异常
};

void good_exception_policy(ExceptionPolicy policy) {
    try {
        throw std::runtime_error("error");
    } catch (const std::exception& e) {
        switch (policy) {
            case ExceptionPolicy::Propagate:
                throw;
            case ExceptionPolicy::LogAndRethrow:
                std::cout << "记录错误: " << e.what() << std::endl;
                throw;
            case ExceptionPolicy::Convert:
                throw std::logic_error(e.what());
            case ExceptionPolicy::Swallow:
                std::cout << "吞掉异常: " << e.what() << std::endl;
                break;
        }
    }
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 异常传播陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 捕获所有异常" << std::endl;
    std::cout << "问题：捕获过于宽泛的异常" << std::endl;
    // bad_catch_all();  // 注释掉
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 捕获特定异常" << std::endl;
    good_catch_specific();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 异常链" << std::endl;
    good_exception_chain();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用嵌套异常" << std::endl;
    good_nested_exception();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 析构函数不抛出异常" << std::endl;
    GoodDestructor destructor;
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用 RAII" << std::endl;
    try {
        good_raii();
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    std::cout << "[正确示例 6] 异常安全的函数" << std::endl;
    good_exception_safe_function();
    std::cout << std::endl;

    std::cout << "[正确示例 7] 异常处理策略" << std::endl;
    try {
        good_exception_policy(ExceptionPolicy::LogAndRethrow);
    } catch (const std::exception& e) {
        std::cout << "最终捕获: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
