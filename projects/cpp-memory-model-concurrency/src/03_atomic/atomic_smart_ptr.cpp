/**
 * 原子智能指针 (C++20)
 *
 * C++20 的原子智能指针：
 * 1. std::atomic<std::shared_ptr<T>>
 * 2. std::atomic<std::weak_ptr<T>>
 * 3. 无锁实现（大部分平台）
 * 4. 替代 std::atomic_shared_ptr（实验性）
 *
 * 编译：g++ -std=c++20 -pthread atomic_smart_ptr.cpp -o atomic_smart_ptr
 */

#include <iostream>
#include <atomic>
#include <memory>
#include <thread>
#include <vector>
#include <string>

// 示例1：基本用法
void basic_atomic_shared_ptr() {
    std::cout << "=== 基本 atomic<shared_ptr> 用法 ===" << std::endl;

    // 创建原子 shared_ptr
    std::atomic<std::shared_ptr<int>> atomic_ptr{
        std::make_shared<int>(42)};

    // load：读取
    auto ptr = atomic_ptr.load();
    std::cout << "load: " << *ptr << std::endl;

    // store：写入
    atomic_ptr.store(std::make_shared<int>(100));
    ptr = atomic_ptr.load();
    std::cout << "store: " << *ptr << std::endl;

    // exchange：交换
    auto old = atomic_ptr.exchange(std::make_shared<int>(200));
    std::cout << "exchange: 旧值=" << *old << ", 新值=" << *atomic_ptr.load() << std::endl;
}

// 示例2：CAS 操作
void cas_shared_ptr() {
    std::cout << "\n=== CAS 操作 ===" << std::endl;

    std::atomic<std::shared_ptr<int>> atomic_ptr{
        std::make_shared<int>(42)};

    // compare_exchange_weak
    auto expected = std::make_shared<int>(42);
    bool success = atomic_ptr.compare_exchange_weak(
        expected, std::make_shared<int>(100));
    std::cout << "weak CAS: 成功=" << success
              << ", 值=" << *atomic_ptr.load() << std::endl;

    // compare_exchange_strong
    expected = atomic_ptr.load();
    success = atomic_ptr.compare_exchange_strong(
        expected, std::make_shared<int>(200));
    std::cout << "strong CAS: 成功=" << success
              << ", 值=" << *atomic_ptr.load() << std::endl;
}

// 示例3：并发访问
void concurrent_shared_ptr() {
    std::cout << "\n=== 并发访问 ===" << std::endl;

    std::atomic<std::shared_ptr<int>> atomic_ptr{
        std::make_shared<int>(0)};

    // 多个线程同时读写
    auto writer = [&](int id) {
        for (int i = 0; i < 100; ++i) {
            auto new_ptr = std::make_shared<int>(id * 1000 + i);
            atomic_ptr.store(new_ptr);
        }
    };

    auto reader = [&](int id) {
        for (int i = 0; i < 100; ++i) {
            auto ptr = atomic_ptr.load();
            if (ptr) {
                // 安全读取
                (void)*ptr;
            }
        }
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < 3; ++i) {
        threads.emplace_back(writer, i);
        threads.emplace_back(reader, i);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "最终值: " << *atomic_ptr.load() << std::endl;
}

// 示例4：无锁检测
void lock_free_detection() {
    std::cout << "\n=== 无锁检测 ===" << std::endl;

    std::atomic<std::shared_ptr<int>> atomic_ptr;

    // 检查是否无锁
    std::cout << "atomic<shared_ptr> 无锁: "
              << atomic_ptr.is_lock_free() << std::endl;

    // 大部分平台上是无锁的
    #if __cpp_lib_atomic_shared_ptr >= 202002L
    std::cout << "C++20 atomic_shared_ptr 支持: 是" << std::endl;
    #else
    std::cout << "C++20 atomic_shared_ptr 支持: 否" << std::endl;
    #endif
}

// 示例5：实际应用 - 共享配置
struct Config {
    std::string server;
    int port;
    int timeout;

    Config(std::string s, int p, int t)
        : server(std::move(s)), port(p), timeout(t) {}
};

class SharedConfig {
public:
    SharedConfig()
        : config_(std::make_shared<Config>("localhost", 8080, 30)) {}

    std::shared_ptr<Config> get() const {
        return config_.load(std::memory_order_acquire);
    }

    void update(std::shared_ptr<Config> new_config) {
        config_.store(std::move(new_config), std::memory_order_release);
    }

private:
    std::atomic<std::shared_ptr<Config>> config_;
};

void shared_config_demo() {
    std::cout << "\n=== 共享配置演示 ===" << std::endl;

    SharedConfig config;

    // 读取配置
    auto cfg = config.get();
    std::cout << "服务器: " << cfg->server << ":" << cfg->port << std::endl;

    // 更新配置
    config.update(std::make_shared<Config>("example.com", 443, 60));
    cfg = config.get();
    std::cout << "更新后: " << cfg->server << ":" << cfg->port << std::endl;

    // 并发读取和更新
    std::atomic<bool> stop{false};

    std::thread updater([&]() {
        for (int i = 0; i < 5 && !stop; ++i) {
            config.update(std::make_shared<Config>(
                "server" + std::to_string(i), 8080 + i, 30 + i));
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    });

    std::thread reader([&]() {
        for (int i = 0; i < 10 && !stop; ++i) {
            auto cfg = config.get();
            std::cout << "读取: " << cfg->server << ":" << cfg->port << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
        }
        stop = true;
    });

    updater.join();
    reader.join();
}

int main() {
    std::cout << "C++ 原子操作：原子智能指针 (C++20)" << std::endl;
    std::cout << "=====================================\n" << std::endl;

    basic_atomic_shared_ptr();
    cas_shared_ptr();
    concurrent_shared_ptr();
    lock_free_detection();
    shared_config_demo();

    return 0;
}
