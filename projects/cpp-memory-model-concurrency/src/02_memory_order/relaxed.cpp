/**
 * memory_order_relaxed
 *
 * 最弱的内存序：
 * 1. 只保证原子性，不保证顺序
 * 2. 不建立同步关系
 * 3. 适合计数器等只需原子性的场景
 * 4. 性能最好，但使用需谨慎
 *
 * 编译：g++ -std=c++17 -pthread relaxed.cpp -o relaxed
 */

#include <iostream>
#include <atomic>
#include <thread>
#include <vector>
#include <cassert>
#include <algorithm>

// 示例1：基本用法 - 计数器
void basic_relaxed() {
    std::cout << "=== 基本用法：计数器 ===" << std::endl;

    std::atomic<int> counter{0};

    auto increment = [&counter](int n) {
        for (int i = 0; i < n; ++i) {
            // relaxed 只保证原子性，不保证顺序
            counter.fetch_add(1, std::memory_order_relaxed);
        }
    };

    std::thread t1(increment, 100000);
    std::thread t2(increment, 100000);

    t1.join();
    t2.join();

    std::cout << "最终计数: " << counter.load(std::memory_order_relaxed) << std::endl;
    std::cout << "期望值: 200000" << std::endl;
}

// 示例2：relaxed 的顺序不确定性
void relaxed_ordering() {
    std::cout << "\n=== relaxed 的顺序不确定性 ===" << std::endl;

    std::atomic<int> x{0};
    std::atomic<int> y{0};

    // 线程 1
    auto writer = [&]() {
        x.store(1, std::memory_order_relaxed);
        y.store(1, std::memory_order_relaxed);
    };

    // 线程 2
    auto reader = [&]() {
        // 可能读到 y=1 但 x=0！
        // 因为 relaxed 不保证顺序
        int y_val = y.load(std::memory_order_relaxed);
        int x_val = x.load(std::memory_order_relaxed);
        std::cout << "y = " << y_val << ", x = " << x_val << std::endl;
    };

    // 多次运行观察不确定性
    for (int i = 0; i < 5; ++i) {
        x.store(0, std::memory_order_relaxed);
        y.store(0, std::memory_order_relaxed);

        std::thread t1(writer);
        std::thread t2(reader);

        t1.join();
        t2.join();
    }
}

// 示例3：relaxed 适合的场景 - ID 生成器
class IDGenerator {
public:
    static uint64_t next_id() {
        // 使用 relaxed 因为只需要原子递增
        return counter_.fetch_add(1, std::memory_order_relaxed);
    }

private:
    static std::atomic<uint64_t> counter_;
};

std::atomic<uint64_t> IDGenerator::counter_{0};

void id_generator() {
    std::cout << "\n=== ID 生成器 ===" << std::endl;

    std::vector<std::thread> threads;
    std::vector<uint64_t> ids[4];

    // 4 个线程并发生成 ID
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&ids, i]() {
            for (int j = 0; j < 5; ++j) {
                ids[i].push_back(IDGenerator::next_id());
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    // 检查 ID 是否唯一
    std::vector<uint64_t> all_ids;
    for (int i = 0; i < 4; ++i) {
        for (auto id : ids[i]) {
            all_ids.push_back(id);
            std::cout << "Thread " << i << ": ID " << id << std::endl;
        }
    }

    // 排序后检查是否有重复
    std::sort(all_ids.begin(), all_ids.end());
    bool unique = std::adjacent_find(all_ids.begin(), all_ids.end()) == all_ids.end();
    std::cout << "所有 ID 唯一: " << (unique ? "是" : "否") << std::endl;
}

// 示例4：relaxed 用于标志位（小心使用）
void relaxed_flag() {
    std::cout << "\n=== relaxed 标志位（小心使用） ===" << std::endl;

    std::atomic<bool> ready{false};
    int data = 0;

    // 生产者
    std::thread producer([&]() {
        data = 42;
        // 危险！relaxed 不保证 data = 42 对消费者可见
        ready.store(true, std::memory_order_relaxed);
    });

    // 消费者
    std::thread consumer([&]() {
        // 自旋等待
        while (!ready.load(std::memory_order_relaxed)) {
            // 可能读到旧的 data 值！
        }
        // data 可能不是 42！
        std::cout << "data = " << data << " (可能不是 42)" << std::endl;
    });

    producer.join();
    consumer.join();
}

// 示例5：relaxed vs 其他内存序的性能对比
void performance_comparison() {
    std::cout << "\n=== 性能对比 ===" << std::endl;

    const int iterations = 1000000;
    std::atomic<int> counter{0};

    // relaxed
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_relaxed);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto relaxed_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    // seq_cst
    counter.store(0);
    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_seq_cst);
    }
    end = std::chrono::high_resolution_clock::now();
    auto seq_cst_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "relaxed: " << relaxed_time.count() << " us" << std::endl;
    std::cout << "seq_cst: " << seq_cst_time.count() << " us" << std::endl;
    std::cout << "relaxed 约快 " << (double)seq_cst_time.count() / relaxed_time.count() << " 倍" << std::endl;
}

int main() {
    std::cout << "C++ 内存序：memory_order_relaxed" << std::endl;
    std::cout << "==================================\n" << std::endl;

    basic_relaxed();
    relaxed_ordering();
    id_generator();
    relaxed_flag();
    performance_comparison();

    return 0;
}
