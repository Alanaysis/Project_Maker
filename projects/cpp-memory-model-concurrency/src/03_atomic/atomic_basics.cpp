/**
 * std::atomic 基础
 *
 * 原子操作的基础：
 * 1. 原子类型保证操作的原子性
 * 2. 支持多种内存序
 * 3. 适合多线程共享数据
 * 4. 性能优于互斥锁
 *
 * 编译：g++ -std=c++17 -pthread atomic_basics.cpp -o atomic_basics
 */

#include <iostream>
#include <atomic>
#include <thread>
#include <vector>
#include <string>

// 示例1：基本原子操作
void basic_atomic() {
    std::cout << "=== 基本原子操作 ===" << std::endl;

    // 原子整数
    std::atomic<int> counter{0};

    // load：读取值
    std::cout << "初始值: " << counter.load() << std::endl;

    // store：写入值
    counter.store(42);
    std::cout << "存储后: " << counter.load() << std::endl;

    // exchange：交换值
    int old = counter.exchange(100);
    std::cout << "交换后: 旧值=" << old << ", 新值=" << counter.load() << std::endl;

    // fetch_add：原子加法
    int prev = counter.fetch_add(10);
    std::cout << "加法后: 旧值=" << prev << ", 新值=" << counter.load() << std::endl;

    // fetch_sub：原子减法
    prev = counter.fetch_sub(5);
    std::cout << "减法后: 旧值=" << prev << ", 新值=" << counter.load() << std::endl;

    // 运算符重载
    counter += 5;
    std::cout << "operator+= 后: " << counter.load() << std::endl;

    counter -= 3;
    std::cout << "operator-= 后: " << counter.load() << std::endl;

    ++counter;
    std::cout << "operator++ 后: " << counter.load() << std::endl;

    --counter;
    std::cout << "operator-- 后: " << counter.load() << std::endl;
}

// 示例2：CAS 操作
void cas_operations() {
    std::cout << "\n=== CAS 操作 ===" << std::endl;

    std::atomic<int> value{0};

    // compare_exchange_weak：弱 CAS
    // 可能失败（即使值相等），适合循环
    int expected = 0;
    bool success = value.compare_exchange_weak(expected, 42);
    std::cout << "weak CAS: 成功=" << success << ", 值=" << value.load() << std::endl;

    // compare_exchange_strong：强 CAS
    // 不会虚假失败
    expected = 42;
    success = value.compare_exchange_strong(expected, 100);
    std::cout << "strong CAS: 成功=" << success << ", 值=" << value.load() << std::endl;

    // CAS 失败时，expected 会被更新为当前值
    expected = 0;
    success = value.compare_exchange_strong(expected, 200);
    std::cout << "CAS 失败: 成功=" << success << ", expected=" << expected << std::endl;
}

// 示例3：原子布尔
void atomic_bool() {
    std::cout << "\n=== 原子布尔 ===" << std::endl;

    std::atomic<bool> flag{false};

    // 测试并设置
    bool old = flag.exchange(true);
    std::cout << "exchange: 旧值=" << old << ", 新值=" << flag.load() << std::endl;

    // CAS
    bool expected = true;
    bool success = flag.compare_exchange_strong(expected, false);
    std::cout << "CAS: 成功=" << success << ", 值=" << flag.load() << std::endl;
}

// 示例4：原子指针
void atomic_pointer() {
    std::cout << "\n=== 原子指针 ===" << std::endl;

    int arr[5] = {1, 2, 3, 4, 5};
    std::atomic<int*> ptr{arr};

    std::cout << "初始指针: " << ptr.load() << std::endl;
    std::cout << "初始值: " << *ptr.load() << std::endl;

    // 指针算术
    int* old = ptr.fetch_add(2);
    std::cout << "fetch_add(2): 旧指针=" << old << ", 新指针=" << ptr.load() << std::endl;
    std::cout << "当前值: " << *ptr.load() << std::endl;
}

// 示例5：并发计数器
class ConcurrentCounter {
public:
    ConcurrentCounter() : count_(0) {}

    void increment() {
        count_.fetch_add(1, std::memory_order_relaxed);
    }

    void decrement() {
        count_.fetch_sub(1, std::memory_order_relaxed);
    }

    int get() const {
        return count_.load(std::memory_order_relaxed);
    }

private:
    std::atomic<int> count_;
};

void concurrent_counter_demo() {
    std::cout << "\n=== 并发计数器 ===" << std::endl;

    ConcurrentCounter counter;

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&counter]() {
            for (int j = 0; j < 10000; ++j) {
                counter.increment();
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "最终计数: " << counter.get() << std::endl;
    std::cout << "期望值: 40000" << std::endl;
}

// 示例6：原子类型支持
void atomic_types() {
    std::cout << "\n=== 原子类型支持 ===" << std::endl;

    // 基本类型
    std::cout << "atomic<bool>: " << sizeof(std::atomic<bool>) << " bytes" << std::endl;
    std::cout << "atomic<int>: " << sizeof(std::atomic<int>) << " bytes" << std::endl;
    std::cout << "atomic<long>: " << sizeof(std::atomic<long>) << " bytes" << std::endl;
    std::cout << "atomic<long long>: " << sizeof(std::atomic<long long>) << " bytes" << std::endl;

    // 指针类型
    std::cout << "atomic<int*>: " << sizeof(std::atomic<int*>) << " bytes" << std::endl;

    // 是否无锁
    std::cout << "\n是否无锁:" << std::endl;
    std::cout << "atomic<int> 无锁: " << std::atomic<int>{}.is_lock_free() << std::endl;
    std::cout << "atomic<long long> 无锁: " << std::atomic<long long>{}.is_lock_free() << std::endl;
}

int main() {
    std::cout << "C++ 原子操作：std::atomic 基础" << std::endl;
    std::cout << "================================\n" << std::endl;

    basic_atomic();
    cas_operations();
    atomic_bool();
    atomic_pointer();
    concurrent_counter_demo();
    atomic_types();

    return 0;
}
