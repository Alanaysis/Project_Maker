/**
 * atomic_ops.cpp - 原子操作详解 (Atomic Operations)
 *
 * 本文件演示：
 *   1. std::atomic 的基本用法
 *   2. 不同内存序（memory order）的含义和使用场景
 *   3. CAS（Compare-And-Swap）模式
 *   4. 自旋锁（Spinlock）的实现
 *   5. 原子操作的实际应用示例
 *
 * 编译命令：
 *   g++ -std=c++17 -O2 -pthread -o atomic_ops atomic_ops.cpp
 *
 * 核心概念：
 *   原子操作是不可分割的操作，要么完全执行，要么完全不执行
 *   在多线程环境下，原子操作保证不会出现数据竞争（data race）
 */

#include <atomic>
#include <thread>
#include <iostream>
#include <vector>
#include <mutex>
#include <cassert>
#include <functional>
#include <chrono>

// ============================================================================
// 第一部分：std::atomic 基础用法
// ============================================================================

/**
 * 演示 std::atomic 的基本操作
 *
 * std::atomic<T> 支持的操作：
 *   - load()         读取值
 *   - store()        写入值
 *   - exchange()     交换值，返回旧值
 *   - compare_exchange_weak/strong()  CAS 操作
 *   - fetch_add()    原子加法，返回旧值
 *   - fetch_sub()    原子减法，返回旧值
 *   - fetch_and()    原子按位与
 *   - fetch_or()     原子按位或
 *   - fetch_xor()    原子按位异或
 *   - ++, --, +=, -= 等运算符重载
 */
void demo_atomic_basics() {
    std::cout << "=== std::atomic 基础操作 ===" << std::endl;

    // 1. 基本原子变量声明
    std::atomic<int> counter{0};             // 原子计数器
    std::atomic<bool> flag{false};           // 原子标志位
    std::atomic<double> value{3.14};         // 原子浮点数（C++20 起支持）

    // 2. load() 和 store()
    int old_val = counter.load();            // 原子读取
    counter.store(42);                       // 原子写入
    std::cout << "counter = " << counter.load() << std::endl;

    // 3. exchange() - 原子交换
    int prev = counter.exchange(100);        // 原子交换，返回旧值
    std::cout << "exchange: 旧值=" << prev << ", 新值=" << counter.load() << std::endl;

    // 4. fetch_add() 和 fetch_sub() - 原子算术
    counter.store(0);
    int before = counter.fetch_add(5);       // 原子加 5，返回加之前的值
    std::cout << "fetch_add(5): 之前=" << before << ", 之后=" << counter.load() << std::endl;

    before = counter.fetch_sub(3);           // 原子减 3
    std::cout << "fetch_sub(3): 之前=" << before << ", 之后=" << counter.load() << std::endl;

    // 5. 运算符重载
    counter = 10;
    counter++;                               // 原子自增
    ++counter;                               // 前缀自增
    counter += 5;                            // 原子加法赋值
    std::cout << "运算符操作后: " << counter.load() << std::endl;

    // 6. 原子标志位
    flag.store(true);
    bool was_set = flag.exchange(false);
    std::cout << "flag exchange: 之前=" << was_set
              << ", 之后=" << flag.load() << std::endl;
}

// ============================================================================
// 第二部分：内存序（Memory Order）详解
// ============================================================================

/**
 * 内存序决定了原子操作如何与其他内存操作排序
 *
 * C++ 提供 6 种内存序：
 *   1. memory_order_relaxed   - 最宽松，只保证原子性
 *   2. memory_order_consume   - 消费语义（很少使用）
 *   3. memory_order_acquire   - 获取语义，防止后续读写重排到此操作之前
 *   4. memory_order_release   - 释放语义，防止之前的读写重排到此操作之后
 *   5. memory_order_acq_rel   - acquire + release
 *   6. memory_order_seq_cst   - 最严格，顺序一致性（默认）
 */
void demo_memory_orders() {
    std::cout << "\n=== 内存序（Memory Order）演示 ===" << std::endl;

    // --------------------------------------------------
    // 示例 1：memory_order_relaxed - 松散序
    // 适用场景：计数器、统计信息等不需要严格顺序的场景
    // --------------------------------------------------
    std::cout << "\n--- memory_order_relaxed ---" << std::endl;
    {
        std::atomic<int> counter{0};
        constexpr int ITERATIONS = 100000;

        std::vector<std::thread> threads;
        for (int i = 0; i < 4; ++i) {
            threads.emplace_back([&counter]() {
                for (int j = 0; j < ITERATIONS; ++j) {
                    // relaxed 只保证原子性，不保证顺序
                    // 对于纯计数器来说足够了
                    counter.fetch_add(1, std::memory_order_relaxed);
                }
            });
        }

        for (auto& t : threads) t.join();
        std::cout << "relaxed 计数器结果: " << counter.load()
                  << " (期望: " << 4 * ITERATIONS << ")" << std::endl;
    }

    // --------------------------------------------------
    // 示例 2：acquire-release 配对使用
    // 适用场景：生产者-消费者模式，同步数据
    // --------------------------------------------------
    std::cout << "\n--- acquire-release 配对 ---" << std::endl;
    {
        int data = 0;                              // 非原子数据
        std::atomic<bool> ready{false};            // 原子标志

        // 生产者线程
        std::thread producer([&]() {
            data = 42;                             // 写入数据

            // release 确保 data 的写入在 ready.store 之前完成
            // 消费者看到 ready == true 时，一定能看到 data == 42
            ready.store(true, std::memory_order_release);
        });

        // 消费者线程
        std::thread consumer([&]() {
            // acquire 确保在读取到 ready == true 后
            // 能看到 producer 在 release 之前的所有写入
            while (!ready.load(std::memory_order_acquire)) {
                // 自旋等待
            }
            // 这里 data 一定是 42
            std::cout << "消费者读取 data = " << data << " (期望: 42)" << std::endl;
        });

        producer.join();
        consumer.join();
    }

    // --------------------------------------------------
    // 示例 3：seq_cst（顺序一致性）
    // 最严格的内存序，也是默认的内存序
    // 保证所有线程看到相同的操作顺序
    // --------------------------------------------------
    std::cout << "\n--- memory_order_seq_cst ---" << std::endl;
    {
        // 经典的 seq_cst 示例：两个标志位
        // 如果不使用 seq_cst，可能出现 x==0 && y==0 的情况
        std::atomic<bool> x{false}, y{false};
        std::atomic<int> z{0};

        auto write_x = [&]() {
            x.store(true, std::memory_order_seq_cst);
        };

        auto write_y = [&]() {
            y.store(true, std::memory_order_seq_cst);
        };

        auto read_x_then_y = [&]() {
            while (!x.load(std::memory_order_seq_cst));
            if (y.load(std::memory_order_seq_cst)) {
                z.fetch_add(1, std::memory_order_relaxed);
            }
        };

        auto read_y_then_x = [&]() {
            while (!y.load(std::memory_order_seq_cst));
            if (x.load(std::memory_order_seq_cst)) {
                z.fetch_add(1, std::memory_order_relaxed);
            }
        };

        // 使用 seq_cst 时，z 的结果一定是 >= 1
        // 使用 relaxed 时，理论上可能出现 z == 0
        std::thread t1(write_x);
        std::thread t2(write_y);
        std::thread t3(read_x_then_y);
        std::thread t4(read_y_then_x);

        t1.join(); t2.join(); t3.join(); t4.join();

        std::cout << "seq_cst z = " << z.load()
                  << " (使用 seq_cst 保证 z >= 1)" << std::endl;
    }
}

// ============================================================================
// 第三部分：CAS（Compare-And-Swap）模式
// ============================================================================

/**
 * CAS 是无锁编程的核心操作
 *
 * compare_exchange_weak(expected, desired):
 *   - 如果当前值 == expected，则设置为 desired，返回 true
 *   - 如果当前值 != expected，则将 expected 更新为当前值，返回 false
 *   - weak 版本可能伪失败（spurious failure），需要在循环中使用
 *
 * compare_exchange_strong(expected, desired):
 *   - 与 weak 相同，但不会伪失败
 *   - 性能可能略低于 weak
 */
void demo_cas_pattern() {
    std::cout << "\n=== CAS（Compare-And-Swap）模式 ===" << std::endl;

    // --------------------------------------------------
    // 示例 1：使用 CAS 实现无锁原子最大值更新
    // --------------------------------------------------
    std::cout << "\n--- 无锁原子最大值更新 ---" << std::endl;
    {
        std::atomic<int> max_val{0};
        constexpr int NUM_THREADS = 4;
        constexpr int OPS = 100000;

        std::vector<std::thread> threads;
        for (int t = 0; t < NUM_THREADS; ++t) {
            threads.emplace_back([&max_val, t]() {
                for (int i = 0; i < OPS; ++i) {
                    int new_val = t * OPS + i;
                    int current = max_val.load();

                    // CAS 循环：只有当 new_val > current 时才更新
                    while (new_val > current) {
                        // 如果 max_val 仍然是 current，则更新为 new_val
                        if (max_val.compare_exchange_weak(current, new_val)) {
                            break;  // CAS 成功
                        }
                        // CAS 失败时，current 会被更新为 max_val 的最新值
                        // 循环会重新比较
                    }
                }
            });
        }

        for (auto& t : threads) t.join();
        std::cout << "原子最大值: " << max_val.load()
                  << " (期望: " << (NUM_THREADS - 1) * OPS + OPS - 1 << ")" << std::endl;
    }

    // --------------------------------------------------
    // 示例 2：使用 CAS 实现无锁计数器（带限制）
    // --------------------------------------------------
    std::cout << "\n--- 带限制的无锁计数器 ---" << std::endl;
    {
        std::atomic<int> bounded_counter{0};
        constexpr int MAX_VALUE = 1000;

        auto increment_if_less_than_max = [&]() -> bool {
            int current = bounded_counter.load();
            if (current >= MAX_VALUE) {
                return false;  // 已达上限
            }
            // 尝试 CAS 增加
            return bounded_counter.compare_exchange_weak(current, current + 1);
        };

        // 多线程同时增加
        std::atomic<int> success_count{0};
        std::vector<std::thread> threads;

        for (int i = 0; i < 4; ++i) {
            threads.emplace_back([&]() {
                for (int j = 0; j < MAX_VALUE; ++j) {
                    if (increment_if_less_than_max()) {
                        success_count.fetch_add(1, std::memory_order_relaxed);
                    }
                }
            });
        }

        for (auto& t : threads) t.join();
        std::cout << "有界计数器: " << bounded_counter.load()
                  << " (上限: " << MAX_VALUE << ")" << std::endl;
        std::cout << "成功增加次数: " << success_count.load() << std::endl;
    }
}

// ============================================================================
// 第四部分：自旋锁（Spinlock）实现
// ============================================================================

/**
 * 自旋锁是一种简单的锁实现
 *
 * 与互斥锁的区别：
 *   - 互斥锁：线程阻塞，让出 CPU
 *   - 自旋锁：线程忙等待，不让出 CPU
 *
 * 适用场景：
 *   - 临界区非常短（微秒级）
 *   - 不希望发生上下文切换
 *   - 多核处理器
 *
 * 不适用场景：
 *   - 临界区较长
 *   - 单核处理器（自旋会浪费 CPU 时间）
 */
class SpinLock {
private:
    std::atomic_flag flag_ = ATOMIC_FLAG_INIT;  // 原子标志

public:
    /**
     * 获取锁
     *
     * 使用 test_and_set() 原子操作：
     *   - 将标志设置为 true
     *   - 返回设置之前的值
     *   - 如果之前是 false（未锁定），则获取成功
     *   - 如果之前是 true（已锁定），则继续自旋
     */
    void lock() {
        // 自旋等待
        while (flag_.test_and_set(std::memory_order_acquire)) {
            // 使用 std::atomic_flag::test_and_set 进行忙等待
            // memory_order_acquire 确保锁获取后的内存可见性

            // 可选：降低自旋的 CPU 开销
            // 在某些架构上，pause 指令可以提示 CPU 我们在自旋
            #if defined(__x86_64__) || defined(__i386__)
            __builtin_ia32_pause();  // x86 pause 指令
            #endif
        }
    }

    /**
     * 释放锁
     *
     * 使用 clear() 原子操作将标志重置为 false
     * memory_order_release 确保临界区内的操作在释放锁之前完成
     */
    void unlock() {
        flag_.clear(std::memory_order_release);
    }

    /**
     * 尝试获取锁（非阻塞）
     * 如果锁已经被持有，立即返回 false
     */
    bool try_lock() {
        return !flag_.test_and_set(std::memory_order_acquire);
    }
};

/**
 * 自旋锁的 RAII 包装器
 * 确保在异常情况下也能正确释放锁
 */
class SpinLockGuard {
private:
    SpinLock& lock_;

public:
    explicit SpinLockGuard(SpinLock& lock) : lock_(lock) {
        lock_.lock();
    }

    ~SpinLockGuard() {
        lock_.unlock();
    }

    // 禁止拷贝和移动
    SpinLockGuard(const SpinLockGuard&) = delete;
    SpinLockGuard& operator=(const SpinLockGuard&) = delete;
};

/**
 * 演示自旋锁的使用
 */
void demo_spinlock() {
    std::cout << "\n=== 自旋锁（Spinlock）演示 ===" << std::endl;

    SpinLock spinlock;
    int shared_counter = 0;
    constexpr int ITERATIONS = 100000;
    constexpr int NUM_THREADS = 4;

    std::vector<std::thread> threads;

    auto start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < NUM_THREADS; ++i) {
        threads.emplace_back([&]() {
            for (int j = 0; j < ITERATIONS; ++j) {
                // 使用 RAII 方式获取锁
                SpinLockGuard guard(spinlock);
                shared_counter++;
                // 临界区结束时自动释放锁
            }
        });
    }

    for (auto& t : threads) t.join();

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "自旋锁保护的计数器: " << shared_counter
              << " (期望: " << NUM_THREADS * ITERATIONS << ")" << std::endl;
    std::cout << "耗时: " << duration.count() << " ms" << std::endl;

    // 与互斥锁对比
    std::mutex mtx;
    shared_counter = 0;

    start = std::chrono::high_resolution_clock::now();

    threads.clear();
    for (int i = 0; i < NUM_THREADS; ++i) {
        threads.emplace_back([&]() {
            for (int j = 0; j < ITERATIONS; ++j) {
                std::lock_guard<std::mutex> lock(mtx);
                shared_counter++;
            }
        });
    }

    for (auto& t : threads) t.join();

    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "互斥锁保护的计数器: " << shared_counter
              << " (期望: " << NUM_THREADS * ITERATIONS << ")" << std::endl;
    std::cout << "耗时: " << duration.count() << " ms" << std::endl;
}

// ============================================================================
// 第五部分：实际应用 - 原子标志和状态机
// ============================================================================

/**
 * 使用原子操作实现简单的线程安全状态机
 *
 * 状态转换：
 *   IDLE -> RUNNING -> STOPPING -> IDLE
 */
class AtomicStateMachine {
public:
    enum class State {
        IDLE,
        RUNNING,
        STOPPING
    };

private:
    std::atomic<State> state_{State::IDLE};

    // 将状态转换为字符串
    static const char* state_to_string(State s) {
        switch (s) {
            case State::IDLE: return "IDLE";
            case State::RUNNING: return "RUNNING";
            case State::STOPPING: return "STOPPING";
            default: return "UNKNOWN";
        }
    }

public:
    /**
     * 尝试从 IDLE 转换到 RUNNING
     * 使用 CAS 确保原子性
     */
    bool try_start() {
        State expected = State::IDLE;
        if (state_.compare_exchange_strong(expected, State::RUNNING)) {
            std::cout << "状态转换: IDLE -> RUNNING" << std::endl;
            return true;
        }
        std::cout << "启动失败: 当前状态是 " << state_to_string(expected) << std::endl;
        return false;
    }

    /**
     * 尝试从 RUNNING 转换到 STOPPING
     */
    bool try_stop() {
        State expected = State::RUNNING;
        if (state_.compare_exchange_strong(expected, State::STOPPING)) {
            std::cout << "状态转换: RUNNING -> STOPPING" << std::endl;
            return true;
        }
        std::cout << "停止失败: 当前状态是 " << state_to_string(expected) << std::endl;
        return false;
    }

    /**
     * 尝试从 STOPPING 转换到 IDLE
     */
    bool try_reset() {
        State expected = State::STOPPING;
        if (state_.compare_exchange_strong(expected, State::IDLE)) {
            std::cout << "状态转换: STOPPING -> IDLE" << std::endl;
            return true;
        }
        std::cout << "重置失败: 当前状态是 " << state_to_string(expected) << std::endl;
        return false;
    }

    State get_state() const {
        return state_.load(std::memory_order_acquire);
    }
};

/**
 * 演示原子状态机
 */
void demo_state_machine() {
    std::cout << "\n=== 原子状态机演示 ===" << std::endl;

    AtomicStateMachine sm;

    // 正常的状态转换流程
    sm.try_start();
    sm.try_stop();
    sm.try_reset();

    // 无效的状态转换
    sm.try_stop();   // 应该失败，当前是 IDLE
    sm.try_start();
    sm.try_start();  // 应该失败，当前是 RUNNING
    sm.try_reset();  // 应该失败，当前是 RUNNING

    std::cout << "最终状态: "
              << (sm.get_state() == AtomicStateMachine::State::RUNNING ? "RUNNING" : "其他")
              << std::endl;
}

// ============================================================================
// 第六部分：线程安全的懒初始化
// ============================================================================

/**
 * 使用 std::once_flag 和 std::call_once 实现线程安全的懒初始化
 * 这是 double-checked locking 的正确实现
 */
class LazyInitializer {
private:
    std::once_flag init_flag_;
    int value_ = 0;

    void initialize() {
        std::cout << "执行初始化（只会执行一次）" << std::endl;
        // 模拟耗时的初始化操作
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        value_ = 42;
    }

public:
    int get_value() {
        // call_once 保证 initialize 只被执行一次
        // 即使多个线程同时调用 get_value()
        std::call_once(init_flag_, &LazyInitializer::initialize, this);
        return value_;
    }
};

void demo_lazy_initialization() {
    std::cout << "\n=== 线程安全的懒初始化 ===" << std::endl;

    LazyInitializer lazy;
    constexpr int NUM_THREADS = 10;

    std::vector<std::thread> threads;
    for (int i = 0; i < NUM_THREADS; ++i) {
        threads.emplace_back([&lazy]() {
            int val = lazy.get_value();
            std::cout << "线程 " << std::this_thread::get_id()
                      << " 获取值: " << val << std::endl;
        });
    }

    for (auto& t : threads) t.join();
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  原子操作详解 (Atomic Operations)" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. atomic 基础
    demo_atomic_basics();

    // 2. 内存序
    demo_memory_orders();

    // 3. CAS 模式
    demo_cas_pattern();

    // 4. 自旋锁
    demo_spinlock();

    // 5. 状态机
    demo_state_machine();

    // 6. 懒初始化
    demo_lazy_initialization();

    std::cout << "\n========================================" << std::endl;
    std::cout << "总结：" << std::endl;
    std::cout << "- std::atomic 提供了无锁的线程安全操作" << std::endl;
    std::cout << "- 内存序决定了操作的可见性和顺序性" << std::endl;
    std::cout << "- CAS 是无锁编程的基础" << std::endl;
    std::cout << "- 自旋锁适合临界区非常短的场景" << std::endl;
    std::cout << "- 默认的 seq_cst 最安全但可能最慢" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
