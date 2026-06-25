/**
 * @file 02_resource_leak.cpp
 * @brief 资源泄漏陷阱示例
 *
 * 资源泄漏：异常发生时资源未释放
 * 危害：内存泄漏、文件句柄泄漏、锁泄漏
 */

#include <iostream>
#include <memory>
#include <fstream>
#include <mutex>
#include <stdexcept>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：内存泄漏
 *
 * 问题：异常发生时内存未释放
 */
void bad_memory_leak() {
    int* ptr = new int(42);
    throw std::runtime_error("error");
    delete ptr;  // 不会执行
}

/**
 * 错误示例 2：文件泄漏
 *
 * 问题：异常发生时文件未关闭
 */
void bad_file_leak() {
    FILE* file = fopen("test.txt", "w");
    if (!file) return;

    throw std::runtime_error("error");
    fclose(file);  // 不会执行
}

/**
 * 错误示例 3：锁泄漏
 *
 * 问题：异常发生时锁未释放
 */
std::mutex bad_mutex;

void bad_lock_leak() {
    bad_mutex.lock();
    throw std::runtime_error("error");
    bad_mutex.unlock();  // 不会执行
}

/**
 * 错误示例 4：多个资源泄漏
 *
 * 问题：多个资源，部分泄漏
 */
void bad_multiple_resources() {
    int* ptr1 = new int(1);
    int* ptr2 = new int(2);

    throw std::runtime_error("error");

    delete ptr2;  // 不会执行
    delete ptr1;  // 不会执行
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用 unique_ptr
 *
 * 解决方案：使用智能指针自动管理内存
 */
void good_unique_ptr() {
    auto ptr = std::make_unique<int>(42);
    throw std::runtime_error("error");
    // ptr 自动释放
}

/**
 * 正确示例 2：使用 RAII 管理文件
 *
 * 解决方案：使用 RAII 类管理文件
 */
class GoodFile {
public:
    GoodFile(const char* filename, const char* mode)
        : file_(fopen(filename, mode)) {
        if (!file_) {
            throw std::runtime_error("Failed to open file");
        }
    }

    ~GoodFile() {
        if (file_) {
            fclose(file_);
        }
    }

    // 禁止拷贝
    GoodFile(const GoodFile&) = delete;
    GoodFile& operator=(const GoodFile&) = delete;

    FILE* get() { return file_; }

private:
    FILE* file_;
};

void good_raii_file() {
    GoodFile file("test.txt", "w");
    throw std::runtime_error("error");
    // file 自动关闭
}

/**
 * 正确示例 3：使用 lock_guard
 *
 * 解决方案：使用 RAII 管理锁
 */
std::mutex good_mutex;

void good_lock_guard() {
    std::lock_guard<std::mutex> lock(good_mutex);
    throw std::runtime_error("error");
    // 锁自动释放
}

/**
 * 正确示例 4：使用 unique_ptr 管理多个资源
 *
 * 解决方案：每个资源用独立的 unique_ptr
 */
void good_multiple_resources() {
    auto ptr1 = std::make_unique<int>(1);
    auto ptr2 = std::make_unique<int>(2);

    throw std::runtime_error("error");

    // ptr2 和 ptr1 自动释放（逆序）
}

/**
 * 正确示例 5：使用 scope_guard
 *
 * 解决方案：使用 scope_guard 确保清理
 */
template <typename F>
class ScopeGuard {
public:
    explicit ScopeGuard(F f) : f_(std::move(f)), active_(true) {}

    ~ScopeGuard() {
        if (active_) {
            f_();
        }
    }

    // 禁止拷贝
    ScopeGuard(const ScopeGuard&) = delete;
    ScopeGuard& operator=(const ScopeGuard&) = delete;

    // 移动
    ScopeGuard(ScopeGuard&& other) noexcept
        : f_(std::move(other.f_)), active_(other.active_) {
        other.active_ = false;
    }

    void dismiss() { active_ = false; }

private:
    F f_;
    bool active_;
};

template <typename F>
ScopeGuard<F> make_scope_guard(F f) {
    return ScopeGuard<F>(std::move(f));
}

void good_scope_guard() {
    int* ptr = new int(42);
    auto guard = make_scope_guard([ptr]() {
        delete ptr;
        std::cout << "资源释放" << std::endl;
    });

    throw std::runtime_error("error");
    // guard 自动调用清理函数
}

/**
 * 正确示例 6：使用 std::fstream
 *
 * 解决方案：使用标准库的 RAII 类
 */
void good_fstream() {
    std::ofstream file("test.txt");
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file");
    }

    throw std::runtime_error("error");
    // file 自动关闭
}

/**
 * 正确示例 7：使用异常安全的初始化
 *
 * 解决方案：在构造函数中初始化，在析构函数中清理
 */
class GoodResourceManager {
public:
    GoodResourceManager()
        : data_(new int[100]),
          file_(fopen("test.txt", "w")),
          locked_(false) {
        if (!file_) {
            delete[] data_;
            throw std::runtime_error("Failed to open file");
        }
    }

    ~GoodResourceManager() {
        if (locked_) {
            good_mutex.unlock();
        }
        if (file_) {
            fclose(file_);
        }
        delete[] data_;
    }

    void do_work() {
        std::lock_guard<std::mutex> lock(good_mutex);
        locked_ = true;
        // 工作...
    }

private:
    int* data_;
    FILE* file_;
    bool locked_;
};

void good_resource_manager() {
    GoodResourceManager manager;
    manager.do_work();
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 资源泄漏陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 内存泄漏" << std::endl;
    std::cout << "问题：异常发生时内存未释放" << std::endl;
    // bad_memory_leak();  // 注释掉
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用 unique_ptr" << std::endl;
    try {
        good_unique_ptr();
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 RAII 管理文件" << std::endl;
    try {
        good_raii_file();
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 lock_guard" << std::endl;
    try {
        good_lock_guard();
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 unique_ptr 管理多个资源" << std::endl;
    try {
        good_multiple_resources();
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用 scope_guard" << std::endl;
    try {
        good_scope_guard();
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用 fstream" << std::endl;
    try {
        good_fstream();
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
