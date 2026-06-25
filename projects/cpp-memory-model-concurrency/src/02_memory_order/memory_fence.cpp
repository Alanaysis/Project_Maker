/**
 * 内存屏障 (Memory Fence)
 *
 * 内存屏障的作用：
 * 1. 限制内存操作的重排序
 * 2. 保证内存操作的可见性
 * 3. 建立同步关系
 * 4. 与原子操作配合使用
 *
 * 编译：g++ -std=c++17 -pthread memory_fence.cpp -o memory_fence
 */

#include <iostream>
#include <atomic>
#include <thread>
#include <cassert>

// 示例1：基本内存屏障
void basic_fence() {
    std::cout << "=== 基本内存屏障 ===" << std::endl;

    std::atomic<bool> ready{false};
    int data = 0;

    std::thread producer([&]() {
        data = 42;
        // 内存屏障：保证 data = 42 在 store 之前完成
        std::atomic_thread_fence(std::memory_order_release);
        ready.store(true, std::memory_order_relaxed);
    });

    std::thread consumer([&]() {
        while (!ready.load(std::memory_order_relaxed)) {}
        // 内存屏障：保证能看到 producer 中的写操作
        std::atomic_thread_fence(std::memory_order_acquire);
        assert(data == 42);
        std::cout << "data = " << data << std::endl;
    });

    producer.join();
    consumer.join();
}

// 示例2：顺序一致性屏障
void seq_cst_fence() {
    std::cout << "\n=== 顺序一致性屏障 ===" << std::endl;

    std::atomic<int> x{0};
    std::atomic<int> y{0};
    std::atomic<int> r1{0};
    std::atomic<int> r2{0};

    std::thread t1([&]() {
        x.store(1, std::memory_order_relaxed);
        // seq_cst 屏障：保证全局顺序
        std::atomic_thread_fence(std::memory_order_seq_cst);
        r1.store(y.load(std::memory_order_relaxed), std::memory_order_relaxed);
    });

    std::thread t2([&]() {
        y.store(1, std::memory_order_relaxed);
        // seq_cst 屏障：保证全局顺序
        std::atomic_thread_fence(std::memory_order_seq_cst);
        r2.store(x.load(std::memory_order_relaxed), std::memory_order_relaxed);
    });

    t1.join();
    t2.join();

    std::cout << "r1 = " << r1.load() << ", r2 = " << r2.load() << std::endl;
    std::cout << "使用 seq_cst 屏障，至少一个线程能看到对方的写入" << std::endl;
}

// 示例3：释放屏障和获取屏障
void release_acquire_fence() {
    std::cout << "\n=== 释放屏障和获取屏障 ===" << std::endl;

    std::atomic<int> data[2];
    std::atomic<int> sync;

    std::thread writer([&]() {
        data[0].store(1, std::memory_order_relaxed);
        data[1].store(2, std::memory_order_relaxed);
        // 释放屏障：保证之前的写操作对获取屏障可见
        std::atomic_thread_fence(std::memory_order_release);
        sync.store(1, std::memory_order_relaxed);
    });

    std::thread reader([&]() {
        while (sync.load(std::memory_order_relaxed) != 1) {}
        // 获取屏障：保证能看到释放屏障之前的写操作
        std::atomic_thread_fence(std::memory_order_acquire);
        std::cout << "data[0] = " << data[0].load(std::memory_order_relaxed) << std::endl;
        std::cout << "data[1] = " << data[1].load(std::memory_order_relaxed) << std::endl;
    });

    writer.join();
    reader.join();
}

// 示例4：信号屏障
void signal_fence() {
    std::cout << "\n=== 信号屏障 ===" << std::endl;

    volatile int flag = 0;
    int data = 0;

    // 信号屏障只限制编译器重排序，不限制 CPU 重排序
    // 适用于信号处理函数

    std::cout << "信号屏障用于信号处理函数" << std::endl;
    std::cout << "只限制编译器重排序，不限制 CPU 重排序" << std::endl;

    // 模拟信号处理
    auto signal_handler = [&]() {
        data = 42;
        std::atomic_signal_fence(std::memory_order_release);
        flag = 1;
    };

    auto main_thread = [&]() {
        while (flag == 0) {}
        std::atomic_signal_fence(std::memory_order_acquire);
        std::cout << "data = " << data << std::endl;
    };

    std::thread t1(signal_handler);
    std::thread t2(main_thread);

    t1.join();
    t2.join();
}

// 示例5：屏障的性能影响
void fence_performance() {
    std::cout << "\n=== 屏障的性能影响 ===" << std::endl;

    const int iterations = 1000000;
    std::atomic<int> counter{0};

    // 无屏障
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_relaxed);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto no_fence = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    // 有屏障
    counter.store(0);
    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        std::atomic_thread_fence(std::memory_order_seq_cst);
        counter.fetch_add(1, std::memory_order_relaxed);
    }
    end = std::chrono::high_resolution_clock::now();
    auto with_fence = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "无屏障: " << no_fence.count() << " us" << std::endl;
    std::cout << "有屏障: " << with_fence.count() << " us" << std::endl;
    std::cout << "屏障开销: " << (double)with_fence.count() / no_fence.count() << " 倍" << std::endl;
}

// 示例6：实际应用 - 生产者消费者
void producer_consumer_fence() {
    std::cout << "\n=== 生产者消费者（使用屏障） ===" << std::endl;

    const int buffer_size = 10;
    int buffer[buffer_size];
    std::atomic<int> write_pos{0};
    std::atomic<int> read_pos{0};

    // 生产者
    std::thread producer([&]() {
        for (int i = 0; i < 20; ++i) {
            // 等待缓冲区有空间
            while (write_pos.load(std::memory_order_relaxed) -
                   read_pos.load(std::memory_order_relaxed) >= buffer_size) {}

            buffer[write_pos.load(std::memory_order_relaxed) % buffer_size] = i;
            std::atomic_thread_fence(std::memory_order_release);
            write_pos.fetch_add(1, std::memory_order_relaxed);
            std::cout << "生产: " << i << std::endl;
        }
    });

    // 消费者
    std::thread consumer([&]() {
        for (int i = 0; i < 20; ++i) {
            // 等待有数据
            while (read_pos.load(std::memory_order_relaxed) >=
                   write_pos.load(std::memory_order_relaxed)) {}

            std::atomic_thread_fence(std::memory_order_acquire);
            int value = buffer[read_pos.load(std::memory_order_relaxed) % buffer_size];
            read_pos.fetch_add(1, std::memory_order_relaxed);
            std::cout << "消费: " << value << std::endl;
        }
    });

    producer.join();
    consumer.join();
}

int main() {
    std::cout << "C++ 内存屏障 (Memory Fence)" << std::endl;
    std::cout << "============================\n" << std::endl;

    basic_fence();
    seq_cst_fence();
    release_acquire_fence();
    signal_fence();
    fence_performance();
    producer_consumer_fence();

    return 0;
}
