/**
 * raii.cpp - RAII 资源管理
 *
 * 本文件演示 C++ 中 RAII（Resource Acquisition Is Initialization）模式，包括：
 *   1. RAII 基本概念和原理
 *   2. 智能指针 (unique_ptr, shared_ptr, weak_ptr)
 *   3. Scope Guard（作用域守卫）
 *   4. Lock Guard（锁守卫）
 *   5. 自定义 RAII 包装器
 *
 * RAII 核心思想：将资源的生命周期绑定到对象的生命周期，
 * 利用构造函数获取资源，析构函数释放资源，确保资源不会泄漏。
 *
 * 编译命令:
 *   g++ -std=c++17 -pthread -o raii raii.cpp
 */

#include <iostream>
#include <memory>
#include <mutex>
#include <fstream>
#include <string>
#include <functional>
#include <vector>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <thread>
#include <atomic>
#include <sys/stat.h>
#include <unistd.h>

// ============================================================================
// 第一部分: RAII 基本概念
// ============================================================================
// RAII 是 C++ 最重要的编程范式之一
// 资源在构造函数中获取，在析构函数中释放
// 无论函数如何退出（正常返回、异常），析构函数都会被调用

// 示例 1: 文件句柄的 RAII 包装
// 传统 C 风格的文件操作容易忘记 fclose，导致资源泄漏
class FileHandle {
public:
    // 构造函数：获取资源
    explicit FileHandle(const std::string& filename, const std::string& mode = "r")
        : m_file(std::fopen(filename.c_str(), mode.c_str()))
        , m_name(filename) {
        if (!m_file) {
            throw std::runtime_error("无法打开文件: " + filename);
        }
        std::cout << "  [FileHandle] 打开文件: " << filename << std::endl;
    }

    // 析构函数：释放资源
    // 无论怎样离开作用域，都会执行
    ~FileHandle() {
        if (m_file) {
            std::fclose(m_file);
            std::cout << "  [FileHandle] 关闭文件: " << m_name << std::endl;
        }
    }

    // 禁止拷贝（资源所有权不可共享）
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;

    // 允许移动（转移资源所有权）
    FileHandle(FileHandle&& other) noexcept
        : m_file(other.m_file), m_name(std::move(other.m_name)) {
        other.m_file = nullptr;  // 移动后源对象不再拥有资源
    }

    FileHandle& operator=(FileHandle&& other) noexcept {
        if (this != &other) {
            if (m_file) std::fclose(m_file);
            m_file = other.m_file;
            m_name = std::move(other.m_name);
            other.m_file = nullptr;
        }
        return *this;
    }

    // 资源操作接口
    void write(const std::string& data) {
        if (m_file) {
            std::fwrite(data.c_str(), 1, data.size(), m_file);
        }
    }

    std::string read_all() {
        if (!m_file) return "";
        std::fseek(m_file, 0, SEEK_END);
        auto size = std::ftell(m_file);
        std::fseek(m_file, 0, SEEK_SET);
        std::string result(size, '\0');
        std::fread(result.data(), 1, size, m_file);
        return result;
    }

    bool is_open() const { return m_file != nullptr; }

private:
    std::FILE* m_file;
    std::string m_name;
};

// 示例 2: 内存缓冲区的 RAII 包装
class Buffer {
public:
    explicit Buffer(size_t size)
        : m_data(new char[size]), m_size(size) {
        std::memset(m_data, 0, size);
        std::cout << "  [Buffer] 分配 " << size << " 字节" << std::endl;
    }

    ~Buffer() {
        delete[] m_data;
        std::cout << "  [Buffer] 释放 " << m_size << " 字节" << std::endl;
    }

    // 禁止拷贝
    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;

    // 允许移动
    Buffer(Buffer&& other) noexcept
        : m_data(other.m_data), m_size(other.m_size) {
        other.m_data = nullptr;
        other.m_size = 0;
    }

    char* data() { return m_data; }
    const char* data() const { return m_data; }
    size_t size() const { return m_size; }

    void fill(char c) {
        if (m_data) std::memset(m_data, c, m_size);
    }

private:
    char* m_data;
    size_t m_size;
};

void demo_basic_raii() {
    std::cout << "========================================" << std::endl;
    std::cout << "1. RAII 基本概念" << std::endl;
    std::cout << "========================================" << std::endl;

    // 文件操作 - 自动关闭
    std::cout << "\n--- 文件 RAII ---" << std::endl;
    {
        FileHandle file("/tmp/raii_test.txt", "w");
        file.write("Hello, RAII!\n");
        file.write("资源自动管理\n");
        // 离开作用域时自动 fclose
    }
    std::cout << "文件已自动关闭" << std::endl;

    // 内存缓冲区 - 自动释放
    std::cout << "\n--- 缓冲区 RAII ---" << std::endl;
    {
        Buffer buf(1024);
        buf.fill('A');
        std::cout << "  缓冲区首字节: " << buf.data()[0] << std::endl;
        // 离开作用域时自动 delete[]
    }
    std::cout << "缓冲区已自动释放" << std::endl;

    // 异常安全 - 即使抛出异常也能正确释放
    std::cout << "\n--- 异常安全 ---" << std::endl;
    try {
        FileHandle file("/tmp/raii_test.txt", "r");
        auto content = file.read_all();
        std::cout << "  文件内容: " << content;
        // 即使这里抛出异常，file 的析构函数也会被调用
        throw std::runtime_error("模拟异常");
    } catch (const std::exception& e) {
        std::cout << "  捕获异常: " << e.what() << std::endl;
        std::cout << "  但文件已经被正确关闭了!" << std::endl;
    }

    // 移动语义
    std::cout << "\n--- 移动语义 ---" << std::endl;
    {
        FileHandle file1("/tmp/raii_move.txt", "w");
        file1.write("移动测试");

        // 移动所有权到 file2
        FileHandle file2 = std::move(file1);
        std::cout << "  file1 仍然打开: " << (file1.is_open() ? "是" : "否") << std::endl;
        std::cout << "  file2 仍然打开: " << (file2.is_open() ? "是" : "否") << std::endl;
        // file2 离开作用域时关闭文件
    }

    // 清理临时文件
    std::remove("/tmp/raii_test.txt");
    std::remove("/tmp/raii_move.txt");
}

// ============================================================================
// 第二部分: 智能指针
// ============================================================================
// C++11 引入的智能指针是 RAII 的典型应用

void demo_smart_pointers() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "2. 智能指针 (Smart Pointers)" << std::endl;
    std::cout << "========================================" << std::endl;

    // --- unique_ptr: 独占所有权 ---
    std::cout << "\n--- unique_ptr (独占所有权) ---" << std::endl;
    {
        // 创建
        auto ptr = std::make_unique<int>(42);
        std::cout << "  值: " << *ptr << std::endl;

        // 不能拷贝
        // auto ptr2 = ptr;  // 编译错误!

        // 可以移动
        auto ptr2 = std::move(ptr);
        std::cout << "  移动后 ptr 为空: " << (ptr == nullptr) << std::endl;
        std::cout << "  移动后 ptr2: " << *ptr2 << std::endl;

        // 用于动态数组
        auto arr = std::make_unique<int[]>(5);
        for (int i = 0; i < 5; ++i) arr[i] = i * 10;
        std::cout << "  数组: ";
        for (int i = 0; i < 5; ++i) std::cout << arr[i] << " ";
        std::cout << std::endl;
    }
    std::cout << "unique_ptr 已自动释放" << std::endl;

    // --- shared_ptr: 共享所有权（引用计数）---
    std::cout << "\n--- shared_ptr (共享所有权) ---" << std::endl;
    {
        auto sp1 = std::make_shared<std::string>("Hello");
        std::cout << "  sp1 引用计数: " << sp1.use_count() << std::endl;

        {
            auto sp2 = sp1;  // 共享所有权
            auto sp3 = sp1;
            std::cout << "  sp1 引用计数: " << sp1.use_count() << std::endl;
            std::cout << "  *sp2 = " << *sp2 << std::endl;
            // sp2, sp3 在这里销毁
        }

        std::cout << "  sp1 引用计数: " << sp1.use_count() << std::endl;
    }
    std::cout << "shared_ptr 已自动释放" << std::endl;

    // --- weak_ptr: 弱引用（不增加引用计数）---
    std::cout << "\n--- weak_ptr (弱引用) ---" << std::endl;
    {
        std::weak_ptr<std::string> wp;

        {
            auto sp = std::make_shared<std::string>("World");
            wp = sp;

            // 使用前必须检查是否有效
            if (auto locked = wp.lock()) {
                std::cout << "  对象存在: " << *locked << std::endl;
                std::cout << "  引用计数: " << locked.use_count() << std::endl;
            }
        }
        // sp 在这里销毁

        if (wp.expired()) {
            std::cout << "  对象已销毁" << std::endl;
        }
    }

    // --- 智能指针用于多态 ---
    std::cout << "\n--- 智能指针用于多态 ---" << std::endl;
    struct Shape {
        virtual ~Shape() = default;
        virtual std::string name() const = 0;
        virtual double area() const = 0;
    };

    struct Circle : Shape {
        double radius;
        explicit Circle(double r) : radius(r) {}
        std::string name() const override { return "圆形"; }
        double area() const override { return 3.14159 * radius * radius; }
    };

    struct Rectangle : Shape {
        double width, height;
        Rectangle(double w, double h) : width(w), height(h) {}
        std::string name() const override { return "矩形"; }
        double area() const override { return width * height; }
    };

    // 使用基类指针存储派生类对象
    std::vector<std::unique_ptr<Shape>> shapes;
    shapes.push_back(std::make_unique<Circle>(5.0));
    shapes.push_back(std::make_unique<Rectangle>(4.0, 6.0));
    shapes.push_back(std::make_unique<Circle>(3.0));

    for (const auto& shape : shapes) {
        std::cout << "  " << shape->name()
                  << " 面积: " << shape->area() << std::endl;
    }
}

// ============================================================================
// 第三部分: Scope Guard（作用域守卫）
// ============================================================================
// 确保在作用域退出时执行特定操作，即使发生异常

// 基础 Scope Guard
class ScopeGuard {
public:
    explicit ScopeGuard(std::function<void()> on_exit)
        : m_on_exit(std::move(on_exit)), m_active(true) {}

    ~ScopeGuard() {
        if (m_active && m_on_exit) {
            m_on_exit();
        }
    }

    // 移动构造
    ScopeGuard(ScopeGuard&& other) noexcept
        : m_on_exit(std::move(other.m_on_exit)), m_active(other.m_active) {
        other.m_active = false;
    }

    // 取消守卫（不执行清理函数）
    void dismiss() { m_active = false; }

    // 禁止拷贝
    ScopeGuard(const ScopeGuard&) = delete;
    ScopeGuard& operator=(const ScopeGuard&) = delete;

private:
    std::function<void()> m_on_exit;
    bool m_active;
};

// 便捷宏
#define SCOPE_GUARD_NAME_JOIN(x, y) x##y
#define SCOPE_GUARD_NAME(line) SCOPE_GUARD_NAME_JOIN(_scope_guard_, line)
#define ON_SCOPE_EXIT(code) \
    ScopeGuard SCOPE_GUARD_NAME(__LINE__)([&]() { code; })

// Defer 风格（类似 Go 的 defer）
class Defer {
public:
    explicit Defer(std::function<void()> f) : m_func(std::move(f)) {}
    ~Defer() { if (m_func) m_func(); }

    Defer(Defer&&) = default;
    Defer& operator=(Defer&&) = default;
    Defer(const Defer&) = delete;
    Defer& operator=(const Defer&) = delete;

private:
    std::function<void()> m_func;
};

void demo_scope_guard() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "3. Scope Guard (作用域守卫)" << std::endl;
    std::cout << "========================================" << std::endl;

    // 基础用法
    std::cout << "\n--- 基础 Scope Guard ---" << std::endl;
    {
        std::cout << "  进入作用域" << std::endl;
        ScopeGuard guard([]() {
            std::cout << "  [Guard] 离开作用域，执行清理" << std::endl;
        });
        std::cout << "  执行业务逻辑" << std::endl;
    }

    // ON_SCOPE_EXIT 宏
    std::cout << "\n--- ON_SCOPE_EXIT 宏 ---" << std::endl;
    {
        int counter = 0;
        {
            ON_SCOPE_EXIT(counter++);
            ON_SCOPE_EXIT(std::cout << "  第二个 guard 执行" << std::endl);
            ON_SCOPE_EXIT(std::cout << "  第一个 guard 执行" << std::endl);
            // 注意: guard 按逆序执行（LIFO）
            std::cout << "  counter = " << counter << std::endl;
        }
        std::cout << "  counter = " << counter << std::endl;
    }

    // 异常安全的资源管理
    std::cout << "\n--- 异常安全 ---" << std::endl;
    try {
        int* data = new int[100];
        ON_SCOPE_EXIT(delete[] data);  // 确保释放内存

        data[0] = 42;
        std::cout << "  data[0] = " << data[0] << std::endl;

        throw std::runtime_error("模拟异常");
        // 即使抛出异常，data 也会被释放
    } catch (const std::exception& e) {
        std::cout << "  捕获异常: " << e.what() << std::endl;
        std::cout << "  内存已被正确释放" << std::endl;
    }

    // Defer 风格
    std::cout << "\n--- Defer 风格 ---" << std::endl;
    {
        Defer d([]() { std::cout << "  [Defer] 延迟执行" << std::endl; });
        std::cout << "  正常逻辑" << std::endl;
    }

    // 取消守卫
    std::cout << "\n--- 取消守卫 ---" << std::endl;
    {
        bool committed = false;
        ScopeGuard rollback([]() {
            std::cout << "  [Rollback] 回滚操作" << std::endl;
        });

        // 模拟事务
        std::cout << "  执行事务..." << std::endl;
        committed = true;

        if (committed) {
            rollback.dismiss();  // 成功则取消回滚
            std::cout << "  事务已提交，取消回滚" << std::endl;
        }
    }
}

// ============================================================================
// 第四部分: Lock Guard（锁守卫）
// ============================================================================
// RAII 风格的互斥锁管理

class ThreadSafeCounter {
public:
    void increment() {
        std::lock_guard<std::mutex> lock(m_mutex);  // 自动加锁
        ++m_count;
        // 离开作用域自动解锁
    }

    void decrement() {
        std::lock_guard<std::mutex> lock(m_mutex);
        --m_count;
    }

    int get() const {
        std::lock_guard<std::mutex> lock(m_mutex);
        return m_count;
    }

private:
    mutable std::mutex m_mutex;  // mutable 允许在 const 方法中加锁
    int m_count = 0;
};

// 自定义的 RAII 锁包装器
template <typename Mutex>
class UniqueLock {
public:
    explicit UniqueLock(Mutex& mutex) : m_mutex(mutex), m_locked(true) {
        m_mutex.lock();
    }

    ~UniqueLock() {
        if (m_locked) m_mutex.unlock();
    }

    void lock() {
        if (!m_locked) {
            m_mutex.lock();
            m_locked = true;
        }
    }

    void unlock() {
        if (m_locked) {
            m_mutex.unlock();
            m_locked = false;
        }
    }

    // 禁止拷贝
    UniqueLock(const UniqueLock&) = delete;
    UniqueLock& operator=(const UniqueLock&) = delete;

private:
    Mutex& m_mutex;
    bool m_locked;
};

void demo_lock_guard() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "4. Lock Guard (锁守卫)" << std::endl;
    std::cout << "========================================" << std::endl;

    // 线程安全计数器
    std::cout << "\n--- 线程安全计数器 ---" << std::endl;
    {
        ThreadSafeCounter counter;
        constexpr int iterations = 10000;
        constexpr int thread_count = 4;

        std::vector<std::thread> threads;
        for (int i = 0; i < thread_count; ++i) {
            threads.emplace_back([&counter]() {
                for (int j = 0; j < iterations; ++j) {
                    counter.increment();
                }
            });
        }

        for (auto& t : threads) t.join();

        int expected = thread_count * iterations;
        std::cout << "  期望值: " << expected << std::endl;
        std::cout << "  实际值: " << counter.get() << std::endl;
        std::cout << "  结果: " << (counter.get() == expected ? "正确" : "错误") << std::endl;
    }

    // lock_guard 确保异常安全
    std::cout << "\n--- 异常安全的锁管理 ---" << std::endl;
    {
        std::mutex mtx;
        try {
            std::lock_guard<std::mutex> lock(mtx);
            std::cout << "  持有锁，执行操作" << std::endl;
            throw std::runtime_error("模拟异常");
            // 即使抛出异常，lock_guard 析构时也会释放锁
        } catch (const std::exception& e) {
            std::cout << "  异常后锁已释放: " << e.what() << std::endl;
        }
    }
}

// ============================================================================
// 第五部分: 自定义 RAII 包装器
// ============================================================================
// 展示如何为各种资源创建 RAII 包装器

// 通用资源包装器模板
template <typename ResourceType, typename Deleter>
class ResourceGuard {
public:
    ResourceGuard(ResourceType resource, Deleter deleter)
        : m_resource(resource), m_deleter(deleter), m_active(true) {}

    ~ResourceGuard() {
        if (m_active) {
            m_deleter(m_resource);
        }
    }

    // 移动语义
    ResourceGuard(ResourceGuard&& other) noexcept
        : m_resource(other.m_resource)
        , m_deleter(std::move(other.m_deleter))
        , m_active(other.m_active) {
        other.m_active = false;
    }

    ResourceType get() const { return m_resource; }
    ResourceType release() { m_active = false; return m_resource; }
    void dismiss() { m_active = false; }

    // 禁止拷贝
    ResourceGuard(const ResourceGuard&) = delete;
    ResourceGuard& operator=(const ResourceGuard&) = delete;

private:
    ResourceType m_resource;
    Deleter m_deleter;
    bool m_active;
};

// 便捷工厂函数
template <typename ResourceType, typename Deleter>
auto make_resource_guard(ResourceType resource, Deleter deleter) {
    return ResourceGuard<ResourceType, Deleter>(resource, deleter);
}

// 临时目录的 RAII 包装器
class TempDirectory {
public:
    explicit TempDirectory(const std::string& prefix = "/tmp/raii_") {
        // 创建临时目录名（简化实现）
        m_path = prefix + std::to_string(
            reinterpret_cast<uintptr_t>(this));
        if (mkdir(m_path.c_str(), 0755) == 0) {
            std::cout << "  [TempDir] 创建: " << m_path << std::endl;
        }
    }

    ~TempDirectory() {
        // 递归删除目录（简化实现，只删空目录）
        rmdir(m_path.c_str());
        std::cout << "  [TempDir] 删除: " << m_path << std::endl;
    }

    const std::string& path() const { return m_path; }

    // 禁止拷贝
    TempDirectory(const TempDirectory&) = delete;
    TempDirectory& operator=(const TempDirectory&) = delete;

private:
    std::string m_path;
};

// 计时器的 RAII 包装器
class ScopedTimer {
public:
    explicit ScopedTimer(std::string name)
        : m_name(std::move(name))
        , m_start(std::chrono::high_resolution_clock::now()) {
        std::cout << "  [Timer] 开始: " << m_name << std::endl;
    }

    ~ScopedTimer() {
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
            end - m_start);
        std::cout << "  [Timer] 结束: " << m_name
                  << " 耗时 " << duration.count() << " 微秒" << std::endl;
    }

private:
    std::string m_name;
    std::chrono::high_resolution_clock::time_point m_start;
};

void demo_custom_raii() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "5. 自定义 RAII 包装器" << std::endl;
    std::cout << "========================================" << std::endl;

    // 通用资源包装器
    std::cout << "\n--- 通用资源包装器 ---" << std::endl;
    {
        // 包装 C 风格的 FILE*
        auto file_guard = make_resource_guard(
            std::fopen("/tmp/raii_custom.txt", "w"),
            [](std::FILE* f) {
                if (f) {
                    std::fclose(f);
                    std::cout << "  [Guard] 关闭文件" << std::endl;
                }
            }
        );

        if (file_guard.get()) {
            std::fwrite("RAII 包装器测试\n", 1, 16, file_guard.get());
        }
    }
    std::remove("/tmp/raii_custom.txt");

    // 计时器
    std::cout << "\n--- 作用域计时器 ---" << std::endl;
    {
        ScopedTimer timer("数据处理");

        // 模拟一些工作
        volatile int sum = 0;
        for (int i = 0; i < 1000000; ++i) {
            sum += i;
        }
        (void)sum;
    }

    // 临时目录
    std::cout << "\n--- 临时目录 ---" << std::endl;
    {
        TempDirectory tmpdir;
        std::cout << "  临时目录路径: " << tmpdir.path() << std::endl;
        // 离开作用域自动删除
    }

    // 综合示例：事务式操作
    std::cout << "\n--- 事务式操作 ---" << std::endl;
    {
        int account_a = 1000;
        int account_b = 500;
        int transfer_amount = 200;

        std::cout << "  转账前: A=" << account_a << ", B=" << account_b << std::endl;

        // 使用 scope guard 实现事务回滚
        int old_a = account_a;
        int old_b = account_b;
        bool committed = false;

        ScopeGuard rollback([&]() {
            if (!committed) {
                account_a = old_a;
                account_b = old_b;
                std::cout << "  [Rollback] 转账已回滚" << std::endl;
            }
        });

        // 执行转账
        account_a -= transfer_amount;
        account_b += transfer_amount;

        // 验证
        if (account_a >= 0) {
            committed = true;
            std::cout << "  转账成功: A=" << account_a << ", B=" << account_b << std::endl;
        }
    }
}

// ============================================================================
// 主函数
// ============================================================================
int main() {
    std::cout << "╔══════════════════════════════════════╗" << std::endl;
    std::cout << "║    RAII 资源管理模式 (raii)          ║" << std::endl;
    std::cout << "╚══════════════════════════════════════╝" << std::endl;
    std::cout << std::endl;

    demo_basic_raii();
    demo_smart_pointers();
    demo_scope_guard();
    demo_lock_guard();
    demo_custom_raii();

    std::cout << "\nRAII 演示完成。" << std::endl;
    return 0;
}
