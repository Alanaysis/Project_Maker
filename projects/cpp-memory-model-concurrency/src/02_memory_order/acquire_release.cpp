/**
 * memory_order_acquire / memory_order_release
 *
 * 建立同步关系：
 * 1. release：在存储操作上，保证之前的写操作对 acquire 可见
 * 2. acquire：在加载操作上，保证之后的读操作能看到 release 之前的写
 * 3. 建立 happens-before 关系
 * 4. 适合生产者-消费者模式
 *
 * 编译：g++ -std=c++17 -pthread acquire_release.cpp -o acquire_release
 */

#include <iostream>
#include <atomic>
#include <thread>
#include <string>
#include <vector>

// 示例1：基本同步
void basic_acquire_release() {
    std::cout << "=== 基本 acquire/release 同步 ===" << std::endl;

    std::atomic<bool> ready{false};
    int data = 0;

    // 生产者
    std::thread producer([&]() {
        data = 42;
        // release 保证：data = 42 在 store 之前完成
        ready.store(true, std::memory_order_release);
    });

    // 消费者
    std::thread consumer([&]() {
        // acquire 保证：能看到 producer 在 release 之前的写操作
        while (!ready.load(std::memory_order_acquire)) {
            // 自旋等待
        }
        // 保证看到 data = 42
        std::cout << "data = " << data << std::endl;
    });

    producer.join();
    consumer.join();
}

// 示例2：多数据同步
struct SharedData {
    int value1;
    int value2;
    int value3;
};

void multi_data_sync() {
    std::cout << "\n=== 多数据同步 ===" << std::endl;

    SharedData data = {0, 0, 0};
    std::atomic<bool> ready{false};

    // 生产者：写入多个数据
    std::thread producer([&]() {
        data.value1 = 1;
        data.value2 = 2;
        data.value3 = 3;
        // release 保证：所有写入在 store 之前完成
        ready.store(true, std::memory_order_release);
    });

    // 消费者：读取多个数据
    std::thread consumer([&]() {
        // acquire 保证：能看到 producer 在 release 之前的写操作
        while (!ready.load(std::memory_order_acquire)) {
            // 自旋等待
        }
        std::cout << "value1 = " << data.value1 << std::endl;
        std::cout << "value2 = " << data.value2 << std::endl;
        std::cout << "value3 = " << data.value3 << std::endl;
    });

    producer.join();
    consumer.join();
}

// 示例3：链式同步
void chained_sync() {
    std::cout << "\n=== 链式同步 ===" << std::endl;

    std::atomic<int> step1{0};
    std::atomic<int> step2{0};
    std::atomic<int> step3{0};

    // 线程 1：执行步骤 1
    std::thread t1([&]() {
        std::cout << "步骤 1 完成" << std::endl;
        step1.store(1, std::memory_order_release);
    });

    // 线程 2：等待步骤 1，执行步骤 2
    std::thread t2([&]() {
        while (!step1.load(std::memory_order_acquire)) {}
        std::cout << "步骤 2 完成" << std::endl;
        step2.store(1, std::memory_order_release);
    });

    // 线程 3：等待步骤 2，执行步骤 3
    std::thread t3([&]() {
        while (!step2.load(std::memory_order_acquire)) {}
        std::cout << "步骤 3 完成" << std::endl;
        step3.store(1, std::memory_order_release);
    });

    t1.join();
    t2.join();
    t3.join();

    std::cout << "所有步骤完成" << std::endl;
}

// 示例4：单向屏障
void one_way_barrier() {
    std::cout << "\n=== 单向屏障 ===" << std::endl;

    std::atomic<int> flag{0};
    int data1 = 0;
    int data2 = 0;

    // release 是单向屏障：只保证之前的写操作
    std::thread writer([&]() {
        data1 = 100;
        flag.store(1, std::memory_order_release);
        data2 = 200;  // 不保证在 flag 之前完成
    });

    // acquire 是单向屏障：只保证之后的读操作
    std::thread reader([&]() {
        while (flag.load(std::memory_order_acquire) != 1) {}
        std::cout << "data1 = " << data1 << " (保证可见)" << std::endl;
        std::cout << "data2 = " << data2 << " (不保证可见)" << std::endl;
    });

    writer.join();
    reader.join();
}

// 示例5：acquire-release 不等于 seq_cst
void acquire_release_not_seq_cst() {
    std::cout << "\n=== acquire-release 不等于 seq_cst ===" << std::endl;

    std::atomic<int> x{0};
    std::atomic<int> y{0};

    // 线程 1
    auto writer1 = [&]() {
        x.store(1, std::memory_order_release);
    };

    // 线程 2
    auto writer2 = [&]() {
        y.store(1, std::memory_order_release);
    };

    // 线程 3
    auto reader1 = [&]() {
        while (x.load(std::memory_order_acquire) != 1) {}
        return y.load(std::memory_order_acquire);
    };

    // 线程 4
    auto reader2 = [&]() {
        while (y.load(std::memory_order_acquire) != 1) {}
        return x.load(std::memory_order_acquire);
    };

    // 使用 seq_cst 时，不可能出现 x=0, y=0
    // 使用 acquire-release 时，可能出现！
    std::cout << "使用 acquire-release 时，可能出现两个线程都读到 0" << std::endl;
    std::cout << "这是因为没有全局一致的顺序" << std::endl;
}

// 示例6：实际应用 - 简单的消息队列
class SimpleQueue {
public:
    void push(int value) {
        data_ = value;
        // release：保证 data_ 写入在 flag_ 之前
        flag_.store(true, std::memory_order_release);
    }

    bool try_pop(int& value) {
        // acquire：保证能看到 push 中的 data_ 写入
        if (!flag_.load(std::memory_order_acquire)) {
            return false;
        }
        value = data_;
        flag_.store(false, std::memory_order_release);
        return true;
    }

private:
    int data_{0};
    std::atomic<bool> flag_{false};
};

void simple_queue_demo() {
    std::cout << "\n=== 简单消息队列 ===" << std::endl;

    SimpleQueue queue;

    std::thread producer([&]() {
        for (int i = 0; i < 5; ++i) {
            queue.push(i);
            std::cout << "生产: " << i << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
    });

    std::thread consumer([&]() {
        int value;
        for (int i = 0; i < 5; ++i) {
            while (!queue.try_pop(value)) {
                // 自旋等待
            }
            std::cout << "消费: " << value << std::endl;
        }
    });

    producer.join();
    consumer.join();
}

int main() {
    std::cout << "C++ 内存序：acquire / release" << std::endl;
    std::cout << "==============================\n" << std::endl;

    basic_acquire_release();
    multi_data_sync();
    chained_sync();
    one_way_barrier();
    acquire_release_not_seq_cst();
    simple_queue_demo();

    return 0;
}
