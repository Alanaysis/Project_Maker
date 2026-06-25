/**
 * @file scoped_lock_example.cpp
 * @brief C++17 std::scoped_lock 示例
 *
 * std::scoped_lock 是一个 RAII 风格的锁管理器。
 * 它可以同时锁定多个互斥锁，并在作用域结束时自动释放。
 *
 * 主要优势：
 * 1. RAII 风格 - 自动管理锁的生命周期
 * 2. 多锁支持 - 可以同时锁定多个互斥锁
 * 3. 避免死锁 - 使用死锁避免算法
 */

#include <iostream>
#include <mutex>
#include <thread>
#include <vector>
#include <string>
#include <chrono>
#include <functional>
#include <map>

// 1. 基本使用
void basic_example() {
    std::cout << "\n[基本使用]" << std::endl;

    std::mutex mtx;
    int shared_data = 0;

    auto increment = [&]() {
        std::scoped_lock lock(mtx);
        ++shared_data;
        std::cout << "Thread " << std::this_thread::get_id()
                  << ": " << shared_data << std::endl;
    };

    // 启动多个线程
    std::vector<std::thread> threads;
    for (int i = 0; i < 5; ++i) {
        threads.emplace_back(increment);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "Final value: " << shared_data << std::endl;
}

// 2. 多锁锁定
void multi_lock_example() {
    std::cout << "\n[多锁锁定]" << std::endl;

    std::mutex mtx1;
    std::mutex mtx2;
    int data1 = 0;
    int data2 = 0;

    // 同时锁定两个互斥锁
    auto transfer = [&]() {
        std::scoped_lock lock(mtx1, mtx2);
        ++data1;
        ++data2;
        std::cout << "data1=" << data1 << ", data2=" << data2 << std::endl;
    };

    // 启动多个线程
    std::vector<std::thread> threads;
    for (int i = 0; i < 5; ++i) {
        threads.emplace_back(transfer);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "Final: data1=" << data1 << ", data2=" << data2 << std::endl;
}

// 3. 避免死锁
void deadlock_avoidance_example() {
    std::cout << "\n[避免死锁]" << std::endl;

    std::mutex mtx1;
    std::mutex mtx2;
    int counter = 0;

    // 使用 std::scoped_lock 避免死锁
    auto safe_increment = [&]() {
        std::scoped_lock lock(mtx1, mtx2);
        ++counter;
    };

    // 启动多个线程
    std::vector<std::thread> threads;
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back(safe_increment);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "Counter: " << counter << std::endl;
}

// 4. 线程安全的银行账户
class BankAccount {
public:
    BankAccount(const std::string& name, double balance)
        : name_(name), balance_(balance) {}

    std::string name() const { return name_; }

    double balance() const {
        std::scoped_lock lock(mutex_);
        return balance_;
    }

    void deposit(double amount) {
        std::scoped_lock lock(mutex_);
        balance_ += amount;
        std::cout << name_ << ": deposited " << amount
                  << ", balance=" << balance_ << std::endl;
    }

    void withdraw(double amount) {
        std::scoped_lock lock(mutex_);
        if (balance_ >= amount) {
            balance_ -= amount;
            std::cout << name_ << ": withdrew " << amount
                      << ", balance=" << balance_ << std::endl;
        } else {
            std::cout << name_ << ": insufficient funds" << std::endl;
        }
    }

    // 转账（需要同时锁定两个账户）
    static void transfer(BankAccount& from, BankAccount& to, double amount) {
        std::scoped_lock lock(from.mutex_, to.mutex_);
        if (from.balance_ >= amount) {
            from.balance_ -= amount;
            to.balance_ += amount;
            std::cout << "Transferred " << amount << " from " << from.name_
                      << " to " << to.name_ << std::endl;
        } else {
            std::cout << "Transfer failed: insufficient funds" << std::endl;
        }
    }

private:
    std::string name_;
    double balance_;
    mutable std::mutex mutex_;
};

void bank_account_example() {
    std::cout << "\n[线程安全的银行账户]" << std::endl;

    BankAccount account1("Alice", 1000.0);
    BankAccount account2("Bob", 500.0);

    // 并发操作
    std::vector<std::thread> threads;

    // 存款
    threads.emplace_back([&]() {
        for (int i = 0; i < 5; ++i) {
            account1.deposit(100.0);
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    });

    // 取款
    threads.emplace_back([&]() {
        for (int i = 0; i < 3; ++i) {
            account1.withdraw(50.0);
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        }
    });

    // 转账
    threads.emplace_back([&]() {
        for (int i = 0; i < 3; ++i) {
            BankAccount::transfer(account1, account2, 100.0);
            std::this_thread::sleep_for(std::chrono::milliseconds(30));
        }
    });

    // 等待完成
    for (auto& t : threads) {
        t.join();
    }

    std::cout << "Final balances:" << std::endl;
    std::cout << "  " << account1.name() << ": " << account1.balance() << std::endl;
    std::cout << "  " << account2.name() << ": " << account2.balance() << std::endl;
}

// 5. 线程安全的队列
template <typename T>
class ThreadSafeQueue {
public:
    void push(const T& value) {
        std::scoped_lock lock(mutex_);
        queue_.push_back(value);
        std::cout << "Pushed: " << value << std::endl;
    }

    bool pop(T& value) {
        std::scoped_lock lock(mutex_);
        if (queue_.empty()) {
            return false;
        }
        value = queue_.front();
        queue_.erase(queue_.begin());
        std::cout << "Popped: " << value << std::endl;
        return true;
    }

    size_t size() const {
        std::scoped_lock lock(mutex_);
        return queue_.size();
    }

    bool empty() const {
        std::scoped_lock lock(mutex_);
        return queue_.empty();
    }

private:
    mutable std::mutex mutex_;
    std::vector<T> queue_;
};

void thread_safe_queue_example() {
    std::cout << "\n[线程安全的队列]" << std::endl;

    ThreadSafeQueue<int> queue;

    // 生产者
    auto producer = [&]() {
        for (int i = 0; i < 10; ++i) {
            queue.push(i);
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    };

    // 消费者
    auto consumer = [&]() {
        for (int i = 0; i < 5; ++i) {
            int value;
            if (queue.pop(value)) {
                std::this_thread::sleep_for(std::chrono::milliseconds(20));
            }
        }
    };

    // 启动线程
    std::vector<std::thread> threads;
    threads.emplace_back(producer);
    threads.emplace_back(consumer);
    threads.emplace_back(consumer);

    // 等待完成
    for (auto& t : threads) {
        t.join();
    }

    std::cout << "Final queue size: " << queue.size() << std::endl;
}

// 6. 资源管理器
class ResourceManager {
public:
    void acquire(const std::string& resource) {
        std::scoped_lock lock(mutex_);
        if (resources_.find(resource) == resources_.end()) {
            resources_[resource] = true;
            std::cout << "Acquired: " << resource << std::endl;
        } else {
            std::cout << "Already acquired: " << resource << std::endl;
        }
    }

    void release(const std::string& resource) {
        std::scoped_lock lock(mutex_);
        auto it = resources_.find(resource);
        if (it != resources_.end()) {
            resources_.erase(it);
            std::cout << "Released: " << resource << std::endl;
        } else {
            std::cout << "Not acquired: " << resource << std::endl;
        }
    }

    bool is_acquired(const std::string& resource) const {
        std::scoped_lock lock(mutex_);
        return resources_.find(resource) != resources_.end();
    }

    std::vector<std::string> list() const {
        std::scoped_lock lock(mutex_);
        std::vector<std::string> result;
        for (const auto& [resource, _] : resources_) {
            result.push_back(resource);
        }
        return result;
    }

private:
    mutable std::mutex mutex_;
    std::map<std::string, bool> resources_;
};

void resource_manager_example() {
    std::cout << "\n[资源管理器]" << std::endl;

    ResourceManager manager;

    // 并发操作
    std::vector<std::thread> threads;

    threads.emplace_back([&]() {
        manager.acquire("database");
        manager.acquire("cache");
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        manager.release("database");
    });

    threads.emplace_back([&]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
        manager.acquire("database");
        manager.acquire("file");
    });

    threads.emplace_back([&]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(30));
        manager.release("cache");
    });

    // 等待完成
    for (auto& t : threads) {
        t.join();
    }

    // 列出资源
    auto resources = manager.list();
    std::cout << "Acquired resources: ";
    for (const auto& r : resources) {
        std::cout << r << " ";
    }
    std::cout << std::endl;
}

// 7. 性能对比
void performance_example() {
    std::cout << "\n[性能对比]" << std::endl;

    const int iterations = 100000;

    // 测试 std::mutex
    std::mutex mtx;
    int counter1 = 0;

    auto start = std::chrono::high_resolution_clock::now();

    std::vector<std::thread> threads1;
    for (int i = 0; i < 4; ++i) {
        threads1.emplace_back([&]() {
            for (int j = 0; j < iterations; ++j) {
                std::lock_guard<std::mutex> lock(mtx);
                ++counter1;
            }
        });
    }
    for (auto& t : threads1) t.join();

    auto end = std::chrono::high_resolution_clock::now();
    auto duration_guard = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // 测试 std::scoped_lock
    std::mutex mtx2;
    int counter2 = 0;

    start = std::chrono::high_resolution_clock::now();

    std::vector<std::thread> threads2;
    for (int i = 0; i < 4; ++i) {
        threads2.emplace_back([&]() {
            for (int j = 0; j < iterations; ++j) {
                std::scoped_lock lock(mtx2);
                ++counter2;
            }
        });
    }
    for (auto& t : threads2) t.join();

    end = std::chrono::high_resolution_clock::now();
    auto duration_scoped = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Iterations: " << iterations << std::endl;
    std::cout << "std::lock_guard: " << duration_guard.count() << " ms" << std::endl;
    std::cout << "std::scoped_lock: " << duration_scoped.count() << " ms" << std::endl;
}

// 8. 最佳实践
void best_practices_example() {
    std::cout << "\n[最佳实践]" << std::endl;

    std::cout << "1. 使用场景:" << std::endl;
    std::cout << "   - 需要锁定多个互斥锁时" << std::endl;
    std::cout << "   - 需要避免死锁时" << std::endl;
    std::cout << "   - 替代 std::lock_guard" << std::endl;

    std::cout << "\n2. 优势:" << std::endl;
    std::cout << "   - RAII 风格，自动释放" << std::endl;
    std::cout << "   - 支持多锁锁定" << std::endl;
    std::cout << "   - 使用死锁避免算法" << std::endl;

    std::cout << "\n3. 注意事项:" << std::endl;
    std::cout << "   - 不要手动解锁" << std::endl;
    std::cout << "   - 注意锁的粒度" << std::endl;
    std::cout << "   - 避免嵌套锁" << std::endl;

    std::cout << "\n4. 与 std::lock_guard 的区别:" << std::endl;
    std::cout << "   - std::lock_guard: 单锁" << std::endl;
    std::cout << "   - std::scoped_lock: 多锁，避免死锁" << std::endl;
}

// 主示例函数
void scoped_lock_example() {
    std::cout << "=== std::scoped_lock ===" << std::endl;

    basic_example();
    multi_lock_example();
    deadlock_avoidance_example();
    bank_account_example();
    thread_safe_queue_example();
    resource_manager_example();
    performance_example();
    best_practices_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    scoped_lock_example();
    return 0;
}
#endif
