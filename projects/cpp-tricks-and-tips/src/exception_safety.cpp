/**
 * exception_safety.cpp - 异常安全编程
 *
 * 本文件演示 C++ 中的异常安全保证级别和相关技术，包括：
 *   1. 基本保证 (Basic Guarantee)
 *   2. 强保证 (Strong Guarantee)
 *   3. 不抛出保证 (No-throw Guarantee)
 *   4. Copy-and-Swap 惯用法
 *   5. RAII 实现异常安全
 *
 * 异常安全是 C++ 编程中最重要但最容易被忽视的主题之一。
 * 编写异常安全的代码是区分初级和高级 C++ 程序员的关键标志。
 *
 * 编译命令:
 *   g++ -std=c++17 -o exception_safety exception_safety.cpp
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <algorithm>
#include <stdexcept>
#include <cstring>
#include <functional>

// ============================================================================
// 第一部分: 异常安全的三个保证级别
// ============================================================================
//
// 1. 基本保证 (Basic Guarantee):
//    - 如果操作抛出异常，程序仍然处于有效状态
//    - 没有资源泄漏
//    - 但对象的状态可能是不确定的
//
// 2. 强保证 (Strong Guarantee):
//    - 如果操作抛出异常，程序状态回滚到操作之前
//    - 操作要么完全成功，要么完全不变（事务语义）
//
// 3. 不抛出保证 (No-throw Guarantee):
//    - 操作保证不抛出任何异常
//    - 通常通过 noexcept 标记
//    - 析构函数、移动操作、swap 通常应该提供此保证

// ============================================================================
// 第二部分: 不安全的代码示例
// ============================================================================
// 先看反面教材，理解为什么需要异常安全

namespace unsafe {

    // 不安全的资源管理 - 可能泄漏内存
    class UnsafeBuffer {
    public:
        UnsafeBuffer(size_t size) : m_data(new int[size]), m_size(size) {}

        ~UnsafeBuffer() { delete[] m_data; }

        // 不安全的拷贝赋值 - 如果 new 抛出异常，原资源泄漏
        UnsafeBuffer& operator=(const UnsafeBuffer& other) {
            if (this != &other) {
                delete[] m_data;              // 释放旧资源
                m_data = new int[other.m_size]; // 如果这里抛出异常?
                // m_data 已经指向新内存，但旧数据已删除
                // 对象处于不一致状态！
                std::memcpy(m_data, other.m_data, other.m_size * sizeof(int));
                m_size = other.m_size;
            }
            return *this;
        }

    private:
        int* m_data;
        size_t m_size;
    };

    // 前向声明
    void process_data(int*);

    // 不安全的函数 - 可能泄漏资源
    void unsafe_process() {
        int* data = new int[1000];
        // 如果这里抛出异常，data 永远不会被释放
        data[0] = 42;
        process_data(data);  // 假设这个函数可能抛异常
        delete[] data;
    }

    void process_data(int*) {
        // 模拟可能抛异常的操作
    }

}  // namespace unsafe

// ============================================================================
// 第三部分: 基本保证 (Basic Guarantee)
// ============================================================================

namespace basic_guarantee {

    // 使用 RAII 实现基本保证
    // 资源通过智能指针管理，即使异常也能正确释放

    class ResourceManager {
    public:
        ResourceManager(size_t size)
            : m_data(std::make_unique<int[]>(size))
            , m_size(size) {}

        // 拷贝赋值提供基本保证
        // 如果拷贝过程中抛异常，原对象可能已经部分修改
        // 但不会有资源泄漏
        ResourceManager& operator=(const ResourceManager& other) {
            if (this != &other) {
                // 分配新资源（如果抛异常，原对象不变）
                auto new_data = std::make_unique<int[]>(other.m_size);

                // 拷贝数据（如果抛异常，new_data 自动释放，原对象不变）
                std::memcpy(new_data.get(), other.m_data.get(),
                           other.m_size * sizeof(int));

                // 交换（noexcept 操作）
                m_data = std::move(new_data);
                m_size = other.m_size;
            }
            return *this;
        }

        int* data() { return m_data.get(); }
        size_t size() const { return m_size; }

    private:
        std::unique_ptr<int[]> m_data;
        size_t m_size;
    };

    // 使用 vector 的基本保证
    // std::vector 的 push_back 提供基本保证
    class TaskQueue {
    public:
        void add_task(std::function<void()> task) {
            // vector::push_back 提供基本保证
            // 如果分配失败，queue 状态不变
            m_tasks.push_back(std::move(task));
        }

        void execute_all() {
            for (auto& task : m_tasks) {
                task();  // 任务本身可能抛异常
            }
            m_tasks.clear();
        }

        size_t size() const { return m_tasks.size(); }

    private:
        std::vector<std::function<void()>> m_tasks;
    };

    void demo() {
        std::cout << "========================================" << std::endl;
        std::cout << "1. 基本保证 (Basic Guarantee)" << std::endl;
        std::cout << "========================================" << std::endl;

        // RAII 资源管理
        std::cout << "\n--- RAII 资源管理 ---" << std::endl;
        {
            ResourceManager buf1(100);
            ResourceManager buf2(50);

            buf1.data()[0] = 42;
            buf2.data()[0] = 99;

            // 安全的赋值
            buf2 = buf1;
            std::cout << "  buf2[0] = " << buf2.data()[0] << std::endl;
            std::cout << "  buf2 大小: " << buf2.size() << std::endl;
        }

        // 任务队列
        std::cout << "\n--- 任务队列 ---" << std::endl;
        {
            TaskQueue queue;
            queue.add_task([]() { std::cout << "  任务1 执行" << std::endl; });
            queue.add_task([]() { std::cout << "  任务2 执行" << std::endl; });
            std::cout << "  队列大小: " << queue.size() << std::endl;
            queue.execute_all();
        }
    }

}  // namespace basic_guarantee

// ============================================================================
// 第四部分: 强保证 (Strong Guarantee)
// ============================================================================

namespace strong_guarantee {

    // Copy-and-Swap 惯用法提供强保证
    // 核心思想：先在临时副本上操作，成功后用 noexcept 操作交换

    template <typename T>
    class Vector {
    public:
        Vector() : m_data(nullptr), m_size(0), m_capacity(0) {}

        explicit Vector(size_t count, const T& value = T{})
            : m_data(static_cast<T*>(::operator new(count * sizeof(T))))
            , m_size(0), m_capacity(count) {
            try {
                for (size_t i = 0; i < count; ++i) {
                    new (m_data + m_size) T(value);  // placement new
                    ++m_size;
                }
            } catch (...) {
                // 清理已构造的元素
                destroy_all();
                ::operator delete(m_data);
                throw;  // 重新抛出
            }
        }

        ~Vector() {
            destroy_all();
            ::operator delete(m_data);
        }

        // 拷贝构造函数（需要显式定义，因为有自定义析构函数和移动操作）
        Vector(const Vector& other)
            : m_data(static_cast<T*>(::operator new(other.m_capacity * sizeof(T))))
            , m_size(0), m_capacity(other.m_capacity) {
            try {
                for (size_t i = 0; i < other.m_size; ++i) {
                    new (m_data + m_size) T(other.m_data[i]);
                    ++m_size;
                }
            } catch (...) {
                destroy_all();
                ::operator delete(m_data);
                throw;
            }
        }

        // Copy-and-Swap 赋值运算符
        // 提供强异常保证：
        // 1. 先拷贝参数（可能抛异常，但 this 不受影响）
        // 2. 用 noexcept 的 swap 交换
        Vector& operator=(const Vector& other) {
            Vector temp(other);  // 拷贝构造（可能抛异常）
            swap(temp);          // noexcept 交换
            return *this;
        }

        // 移动赋值（noexcept）
        Vector& operator=(Vector&& other) noexcept {
            swap(other);
            return *this;
        }

        // push_back 提供强保证
        void push_back(const T& value) {
            if (m_size >= m_capacity) {
                // 需要扩容
                size_t new_cap = m_capacity == 0 ? 1 : m_capacity * 2;

                // 分配新内存（如果抛异常，原对象不变）
                T* new_data = static_cast<T*>(
                    ::operator new(new_cap * sizeof(T)));

                // 拷贝已有元素到新内存
                size_t new_size = 0;
                try {
                    for (size_t i = 0; i < m_size; ++i) {
                        new (new_data + new_size) T(m_data[i]);
                        ++new_size;
                    }
                    // 拷贝新元素
                    new (new_data + new_size) T(value);
                    ++new_size;
                } catch (...) {
                    // 清理新内存中已构造的元素
                    for (size_t i = 0; i < new_size; ++i) {
                        (new_data + i)->~T();
                    }
                    ::operator delete(new_data);
                    throw;  // 原对象完全不受影响，提供强保证
                }

                // 释放旧内存（noexcept 操作）
                destroy_all();
                ::operator delete(m_data);

                m_data = new_data;
                m_size = new_size;
                m_capacity = new_cap;
            } else {
                // 不需要扩容，直接构造
                new (m_data + m_size) T(value);
                ++m_size;
            }
        }

        // noexcept swap
        void swap(Vector& other) noexcept {
            std::swap(m_data, other.m_data);
            std::swap(m_size, other.m_size);
            std::swap(m_capacity, other.m_capacity);
        }

        size_t size() const { return m_size; }
        size_t capacity() const { return m_capacity; }

        T& operator[](size_t i) { return m_data[i]; }
        const T& operator[](size_t i) const { return m_data[i]; }

    private:
        void destroy_all() {
            for (size_t i = 0; i < m_size; ++i) {
                (m_data + i)->~T();
            }
        }

        T* m_data;
        size_t m_size;
        size_t m_capacity;
    };

    // 交易系统示例 - 展示强保证的实际应用
    class Account {
    public:
        Account(std::string name, double balance)
            : m_name(std::move(name)), m_balance(balance) {}

        // 转账提供强保证：要么成功，要么两个账户都不变
        static bool transfer(Account& from, Account& to, double amount) {
            if (from.m_balance < amount) {
                return false;  // 余额不足
            }

            // 保存状态（用于回滚）
            double old_from = from.m_balance;
            double old_to = to.m_balance;

            try {
                // 可能抛异常的操作（如日志记录、通知等）
                from.m_balance -= amount;
                // 如果这里抛异常，需要回滚
                log_transaction(from.m_name, to.m_name, amount);
                to.m_balance += amount;

                return true;
            } catch (...) {
                // 回滚到原始状态
                from.m_balance = old_from;
                to.m_balance = old_to;
                throw;  // 重新抛出
            }
        }

        const std::string& name() const { return m_name; }
        double balance() const { return m_balance; }

    private:
        static void log_transaction(const std::string& from,
                                   const std::string& to,
                                   double amount) {
            // 模拟可能失败的日志操作
            std::cout << "  日志: " << from << " -> " << to
                      << " 金额=" << amount << std::endl;
        }

        std::string m_name;
        double m_balance;
    };

    void demo() {
        std::cout << "\n========================================" << std::endl;
        std::cout << "2. 强保证 (Strong Guarantee)" << std::endl;
        std::cout << "========================================" << std::endl;

        // Copy-and-Swap
        std::cout << "\n--- Copy-and-Swap ---" << std::endl;
        {
            Vector<int> v1;
            v1.push_back(1);
            v1.push_back(2);
            v1.push_back(3);

            Vector<int> v2;
            v2.push_back(10);
            v2.push_back(20);

            v2 = v1;  // Copy-and-Swap 赋值

            std::cout << "  v2 大小: " << v2.size() << std::endl;
            std::cout << "  v2 内容: ";
            for (size_t i = 0; i < v2.size(); ++i) {
                std::cout << v2[i] << " ";
            }
            std::cout << std::endl;
        }

        // 转账示例
        std::cout << "\n--- 交易系统 ---" << std::endl;
        {
            Account alice("Alice", 1000.0);
            Account bob("Bob", 500.0);

            std::cout << "  转账前: Alice=" << alice.balance()
                      << ", Bob=" << bob.balance() << std::endl;

            Account::transfer(alice, bob, 200.0);

            std::cout << "  转账后: Alice=" << alice.balance()
                      << ", Bob=" << bob.balance() << std::endl;
        }
    }

}  // namespace strong_guarantee

// ============================================================================
// 第五部分: 不抛出保证 (No-throw Guarantee)
// ============================================================================

namespace nothrow_guarantee {

    // 使用 noexcept 标记不抛出异常的函数
    // 编译器可以基于此进行优化

    // 移动操作应该标记为 noexcept
    class Buffer {
    public:
        Buffer() noexcept : m_data(nullptr), m_size(0) {}

        Buffer(size_t size)
            : m_data(new char[size]), m_size(size) {}

        ~Buffer() {
            delete[] m_data;
        }

        // 移动构造 - noexcept
        Buffer(Buffer&& other) noexcept
            : m_data(other.m_data), m_size(other.m_size) {
            other.m_data = nullptr;
            other.m_size = 0;
        }

        // 移动赋值 - noexcept
        Buffer& operator=(Buffer&& other) noexcept {
            if (this != &other) {
                delete[] m_data;
                m_data = other.m_data;
                m_size = other.m_size;
                other.m_data = nullptr;
                other.m_size = 0;
            }
            return *this;
        }

        // swap - noexcept
        void swap(Buffer& other) noexcept {
            std::swap(m_data, other.m_data);
            std::swap(m_size, other.m_size);
        }

        // 禁止拷贝
        Buffer(const Buffer&) = delete;
        Buffer& operator=(const Buffer&) = delete;

        char* data() noexcept { return m_data; }
        size_t size() const noexcept { return m_size; }

    private:
        char* m_data;
        size_t m_size;
    };

    // 条件性 noexcept
    // 只有当类型 T 的移动操作是 noexcept 时，才使用移动
    template <typename T>
    void move_if_noexcept(T& src, T& dst) noexcept(
        noexcept(T(std::move(src)))) {
        // 如果 T 的移动构造是 noexcept，使用移动
        // 否则使用拷贝（保证异常安全）
        dst = std::move_if_noexcept(src);
    }

    void demo() {
        std::cout << "\n========================================" << std::endl;
        std::cout << "3. 不抛出保证 (No-throw Guarantee)" << std::endl;
        std::cout << "========================================" << std::endl;

        // noexcept 检查
        std::cout << "\n--- noexcept 检查 ---" << std::endl;
        std::cout << "  Buffer 移动构造 noexcept: "
                  << std::is_nothrow_move_constructible_v<Buffer> << std::endl;
        std::cout << "  Buffer 移动赋值 noexcept: "
                  << std::is_nothrow_move_assignable_v<Buffer> << std::endl;
        std::cout << "  Buffer 可交换 noexcept: "
                  << noexcept(std::declval<Buffer>().swap(
                     std::declval<Buffer&>())) << std::endl;

        // 移动 vs 拷贝
        std::cout << "\n--- vector 重分配时的选择 ---" << std::endl;
        // std::vector 在重分配时：
        // 如果元素的移动构造是 noexcept，使用移动（快）
        // 否则使用拷贝（慢但安全）
        std::cout << "  int 移动构造 noexcept: "
                  << std::is_nothrow_move_constructible_v<int> << std::endl;
        std::cout << "  string 移动构造 noexcept: "
                  << std::is_nothrow_move_constructible_v<std::string> << std::endl;

        // Buffer 操作
        std::cout << "\n--- Buffer 操作 ---" << std::endl;
        {
            Buffer buf1(100);
            std::memset(buf1.data(), 'A', 100);

            // 移动（noexcept）
            Buffer buf2 = std::move(buf1);
            std::cout << "  buf1 大小: " << buf1.size() << std::endl;
            std::cout << "  buf2 大小: " << buf2.size() << std::endl;
        }
    }

}  // namespace nothrow_guarantee

// ============================================================================
// 第六部分: RAII 实现异常安全
// ============================================================================
// 综合运用 RAII 和异常安全技术

namespace raii_safety {

    // 事务类 - 支持提交和回滚
    template <typename T>
    class Transaction {
    public:
        explicit Transaction(T& obj)
            : m_obj(obj), m_backup(obj), m_committed(false) {}

        ~Transaction() {
            if (!m_committed) {
                // 析构时自动回滚
                rollback();
            }
        }

        // 获取可修改的引用
        T& get() { return m_obj; }

        // 提交事务
        void commit() noexcept { m_committed = true; }

        // 回滚事务
        void rollback() {
            m_obj = m_backup;
        }

        // 禁止拷贝和移动
        Transaction(const Transaction&) = delete;
        Transaction& operator=(const Transaction&) = delete;

    private:
        T& m_obj;
        T m_backup;
        bool m_committed;
    };

    // 用于演示的简单数据类
    struct Config {
        std::string hostname;
        int port;
        bool ssl_enabled;

        // 拷贝赋值（可能抛异常）
        Config& operator=(const Config& other) {
            if (this != &other) {
                hostname = other.hostname;
                port = other.port;
                ssl_enabled = other.ssl_enabled;
            }
            return *this;
        }
    };

    // 异常安全的配置更新
    bool update_config(Config& config, const Config& new_config) {
        Transaction<Config> txn(config);

        try {
            // 修改配置（可能抛异常）
            txn.get() = new_config;

            // 验证配置
            if (txn.get().port < 0 || txn.get().port > 65535) {
                throw std::invalid_argument("端口号无效");
            }

            // 验证通过，提交事务
            txn.commit();
            return true;
        } catch (const std::exception& e) {
            std::cout << "  配置更新失败: " << e.what() << std::endl;
            // txn 析构时自动回滚
            return false;
        }
    }

    // RAII 风格的批量操作
    class BatchWriter {
    public:
        explicit BatchWriter(std::vector<int>& target)
            : m_target(target), m_committed(false) {}

        ~BatchWriter() {
            if (!m_committed && !m_pending.empty()) {
                // 未提交，丢弃所有待写入数据
                std::cout << "  [Batch] 丢弃 " << m_pending.size()
                          << " 条待写入数据" << std::endl;
            }
        }

        void add(int value) {
            m_pending.push_back(value);
        }

        // 提交所有待写入数据
        void commit() {
            // 先尝试分配足够的空间
            m_target.reserve(m_target.size() + m_pending.size());

            // 逐个添加（提供基本保证）
            for (int val : m_pending) {
                m_target.push_back(val);
            }

            m_committed = true;
            m_pending.clear();
        }

    private:
        std::vector<int>& m_target;
        std::vector<int> m_pending;
        bool m_committed;
    };

    void demo() {
        std::cout << "\n========================================" << std::endl;
        std::cout << "4. RAII 实现异常安全" << std::endl;
        std::cout << "========================================" << std::endl;

        // 事务式配置更新
        std::cout << "\n--- 事务式配置更新 ---" << std::endl;
        {
            Config config{"localhost", 8080, false};

            std::cout << "  原始: " << config.hostname << ":" << config.port
                      << " SSL=" << config.ssl_enabled << std::endl;

            // 成功的更新
            Config new_config{"example.com", 443, true};
            if (update_config(config, new_config)) {
                std::cout << "  更新后: " << config.hostname << ":" << config.port
                          << " SSL=" << config.ssl_enabled << std::endl;
            }

            // 失败的更新（端口无效）
            Config bad_config{"example.com", -1, true};
            update_config(config, bad_config);
            std::cout << "  回滚后: " << config.hostname << ":" << config.port
                      << " SSL=" << config.ssl_enabled << std::endl;
        }

        // 批量写入
        std::cout << "\n--- 批量写入 ---" << std::endl;
        {
            std::vector<int> data = {1, 2, 3};

            {
                BatchWriter writer(data);
                writer.add(4);
                writer.add(5);
                writer.add(6);
                // 未调用 commit，数据将被丢弃
            }

            std::cout << "  未提交: data 大小 = " << data.size() << std::endl;

            {
                BatchWriter writer(data);
                writer.add(4);
                writer.add(5);
                writer.add(6);
                writer.commit();  // 提交
            }

            std::cout << "  已提交: data = [";
            for (size_t i = 0; i < data.size(); ++i) {
                if (i > 0) std::cout << ", ";
                std::cout << data[i];
            }
            std::cout << "]" << std::endl;
        }
    }

}  // namespace raii_safety

// ============================================================================
// 第七部分: 异常安全最佳实践总结
// ============================================================================

void demo_best_practices() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "5. 异常安全最佳实践" << std::endl;
    std::cout << "========================================" << std::endl;

    std::cout << R"(
    异常安全最佳实践:

    1. 析构函数不应抛异常
       - 析构函数标记为 noexcept
       - 如果析构中操作可能失败，用 try-catch 吞掉

    2. 构造函数中使用 RAII
       - 用智能指针管理动态资源
       - 构造函数失败时自动清理已获取的资源

    3. 赋值运算符使用 Copy-and-Swap
       - 先拷贝参数（可能抛异常）
       - 再用 noexcept 的 swap 交换

    4. 移动操作标记为 noexcept
       - 编译器优化依赖此信息
       - std::vector 重分配时会使用移动

    5. 使用 RAII 管理所有资源
       - 文件: std::fstream 或自定义 RAII
       - 内存: std::unique_ptr, std::shared_ptr
       - 锁: std::lock_guard, std::unique_lock

    6. 遵循 "资源获取即初始化" 原则
       - 在构造函数中获取资源
       - 在析构函数中释放资源
       - 确保资源不会泄漏

    7. 区分三种保证级别
       - 基本保证: 最低要求，不泄漏资源
       - 强保证: 事务语义，要么成功要么不变
       - 不抛出: 最强保证，标记 noexcept
    )" << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================
int main() {
    std::cout << "╔══════════════════════════════════════╗" << std::endl;
    std::cout << "║  异常安全编程 (exception_safety)     ║" << std::endl;
    std::cout << "╚══════════════════════════════════════╝" << std::endl;
    std::cout << std::endl;

    basic_guarantee::demo();
    strong_guarantee::demo();
    nothrow_guarantee::demo();
    raii_safety::demo();
    demo_best_practices();

    std::cout << "\n异常安全演示完成。" << std::endl;
    return 0;
}
