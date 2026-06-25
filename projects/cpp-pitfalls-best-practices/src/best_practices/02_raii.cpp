/**
 * @file 02_raii.cpp
 * @brief RAII 应用示例
 *
 * RAII (Resource Acquisition Is Initialization)：资源获取即初始化
 * 核心思想：在构造函数中获取资源，在析构函数中释放资源
 */

#include <iostream>
#include <memory>
#include <fstream>
#include <mutex>
#include <vector>
#include <stdexcept>

// ============================================================================
// 传统资源管理
// ============================================================================

/**
 * 传统方式：手动管理资源
 *
 * 问题：容易忘记释放资源，异常时资源泄漏
 */
void traditional_resource() {
    int* ptr = new int(42);
    FILE* file = fopen("test.txt", "w");

    // 如果这里抛出异常...
    throw std::runtime_error("error");

    // 这些不会执行
    fclose(file);
    delete ptr;
}

// ============================================================================
// RAII 示例
// ============================================================================

/**
 * RAII 示例 1：内存管理
 *
 * 使用构造函数获取内存，析构函数释放内存
 */
class MemoryRAII {
public:
    MemoryRAII(size_t size) : data_(new int[size]), size_(size) {
        std::cout << "分配内存: " << size << " 个 int" << std::endl;
    }

    ~MemoryRAII() {
        delete[] data_;
        std::cout << "释放内存" << std::endl;
    }

    // 禁止拷贝
    MemoryRAII(const MemoryRAII&) = delete;
    MemoryRAII& operator=(const MemoryRAII&) = delete;

    // 允许移动
    MemoryRAII(MemoryRAII&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }

    int* get() { return data_; }
    size_t size() const { return size_; }

private:
    int* data_;
    size_t size_;
};

void memory_raii_example() {
    MemoryRAII mem(100);
    mem.get()[0] = 42;
    std::cout << "值: " << mem.get()[0] << std::endl;
    // 函数返回时自动释放
}

/**
 * RAII 示例 2：文件管理
 *
 * 使用 RAII 管理文件句柄
 */
class FileRAII {
public:
    FileRAII(const char* filename, const char* mode)
        : file_(fopen(filename, mode)) {
        if (!file_) {
            throw std::runtime_error("Failed to open file");
        }
        std::cout << "打开文件: " << filename << std::endl;
    }

    ~FileRAII() {
        if (file_) {
            fclose(file_);
            std::cout << "关闭文件" << std::endl;
        }
    }

    // 禁止拷贝
    FileRAII(const FileRAII&) = delete;
    FileRAII& operator=(const FileRAII&) = delete;

    FILE* get() { return file_; }

    void write(const char* data) {
        if (fputs(data, file_) == EOF) {
            throw std::runtime_error("Failed to write");
        }
    }

private:
    FILE* file_;
};

void file_raii_example() {
    try {
        FileRAII file("test.txt", "w");
        file.write("Hello, RAII!");
        // 函数返回时自动关闭
    } catch (const std::exception& e) {
        std::cout << "错误: " << e.what() << std::endl;
    }
}

/**
 * RAII 示例 3：锁管理
 *
 * 使用 RAII 管理互斥锁
 */
class LockRAII {
public:
    explicit LockRAII(std::mutex& mtx) : mtx_(mtx) {
        mtx_.lock();
        std::cout << "获取锁" << std::endl;
    }

    ~LockRAII() {
        mtx_.unlock();
        std::cout << "释放锁" << std::endl;
    }

    // 禁止拷贝
    LockRAII(const LockRAII&) = delete;
    LockRAII& operator=(const LockRAII&) = delete;

private:
    std::mutex& mtx_;
};

std::mutex example_mutex;

void lock_raii_example() {
    LockRAII lock(example_mutex);
    // 临界区
    std::cout << "在临界区内" << std::endl;
    // 函数返回时自动释放锁
}

/**
 * RAII 示例 4：计时器
 *
 * 使用 RAII 测量代码执行时间
 */
#include <chrono>

class TimerRAII {
public:
    TimerRAII(const std::string& name)
        : name_(name), start_(std::chrono::high_resolution_clock::now()) {
        std::cout << "开始计时: " << name_ << std::endl;
    }

    ~TimerRAII() {
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start_);
        std::cout << "结束计时: " << name_ << " 耗时 " << duration.count() << " 微秒"
                  << std::endl;
    }

private:
    std::string name_;
    std::chrono::high_resolution_clock::time_point start_;
};

void timer_raii_example() {
    TimerRAII timer("示例函数");
    // 模拟一些工作
    for (int i = 0; i < 1000000; i++) {
        volatile int x = i;
        (void)x;
    }
}

/**
 * RAII 示例 5：数据库连接
 *
 * 使用 RAII 管理数据库连接
 */
class DatabaseRAII {
public:
    DatabaseRAII(const std::string& connection_string) {
        // 模拟连接数据库
        std::cout << "连接数据库: " << connection_string << std::endl;
        connected_ = true;
    }

    ~DatabaseRAII() {
        if (connected_) {
            std::cout << "断开数据库连接" << std::endl;
            connected_ = false;
        }
    }

    void query(const std::string& sql) {
        if (!connected_) {
            throw std::runtime_error("Not connected");
        }
        std::cout << "执行查询: " << sql << std::endl;
    }

private:
    bool connected_ = false;
};

void database_raii_example() {
    try {
        DatabaseRAII db("localhost:5432");
        db.query("SELECT * FROM users");
        // 函数返回时自动断开连接
    } catch (const std::exception& e) {
        std::cout << "错误: " << e.what() << std::endl;
    }
}

/**
 * RAII 示例 6：范围守卫
 *
 * 使用 RAII 确保代码在作用域结束时执行
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

void scope_guard_example() {
    auto guard = make_scope_guard([]() {
        std::cout << "作用域结束，执行清理" << std::endl;
    });

    std::cout << "在作用域内" << std::endl;
    // guard 自动执行清理
}

/**
 * RAII 示例 7：使用标准库 RAII 类
 *
 * 使用标准库提供的 RAII 类
 */
void standard_raii_example() {
    // unique_ptr
    auto ptr = std::make_unique<int>(42);
    std::cout << "unique_ptr: " << *ptr << std::endl;

    // lock_guard
    std::mutex mtx;
    {
        std::lock_guard<std::mutex> lock(mtx);
        std::cout << "lock_guard 保护的临界区" << std::endl;
    }

    // fstream
    std::ofstream file("test.txt");
    if (file.is_open()) {
        file << "Hello, RAII!" << std::endl;
    }
    // file 自动关闭
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== RAII 应用示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "[1] 内存管理 RAII" << std::endl;
    memory_raii_example();
    std::cout << std::endl;

    std::cout << "[2] 文件管理 RAII" << std::endl;
    file_raii_example();
    std::cout << std::endl;

    std::cout << "[3] 锁管理 RAII" << std::endl;
    lock_raii_example();
    std::cout << std::endl;

    std::cout << "[4] 计时器 RAII" << std::endl;
    timer_raii_example();
    std::cout << std::endl;

    std::cout << "[5] 数据库连接 RAII" << std::endl;
    database_raii_example();
    std::cout << std::endl;

    std::cout << "[6] 范围守卫" << std::endl;
    scope_guard_example();
    std::cout << std::endl;

    std::cout << "[7] 标准库 RAII 类" << std::endl;
    standard_raii_example();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
