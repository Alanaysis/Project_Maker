/**
 * CAS 操作
 *
 * Compare-And-Swap 的核心概念：
 * 1. 原子比较并交换
 * 2. 乐观并发控制
 * 3. ABA 问题
 * 4. 自旋重试策略
 *
 * 编译：g++ -std=c++17 -pthread cas_operations.cpp -o cas_operations
 */

#include <iostream>
#include <atomic>
#include <thread>
#include <vector>
#include <memory>

// 示例1：基本 CAS 操作
void basic_cas() {
    std::cout << "=== 基本 CAS 操作 ===" << std::endl;

    std::atomic<int> value{0};

    // CAS 循环：原子地设置为最大值
    auto update_max = [&](int new_val) {
        int current = value.load(std::memory_order_relaxed);
        while (current < new_val) {
            // compare_exchange_weak 可能虚假失败
            if (value.compare_exchange_weak(current, new_val,
                std::memory_order_relaxed)) {
                break;
            }
            // current 被更新为最新值
        }
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back(update_max, i * 100);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "最终值: " << value.load() << std::endl;
}

// 示例2：CAS 实现原子加法
void cas_add() {
    std::cout << "\n=== CAS 实现原子加法 ===" << std::endl;

    std::atomic<int> counter{0};

    auto cas_add = [&](int delta) {
        int current = counter.load(std::memory_order_relaxed);
        while (!counter.compare_exchange_weak(current, current + delta,
            std::memory_order_relaxed)) {
            // current 被更新为最新值，重试
        }
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&]() {
            for (int j = 0; j < 10000; ++j) {
                cas_add(1);
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "最终计数: " << counter.load() << std::endl;
}

// 示例3：ABA 问题演示
void aba_problem() {
    std::cout << "\n=== ABA 问题演示 ===" << std::endl;

    struct Node {
        int value;
        Node* next;
    };

    std::atomic<Node*> head{new Node{1, nullptr}};

    // 线程 1：读取 head，准备 CAS
    std::thread t1([&]() {
        Node* old_head = head.load(std::memory_order_acquire);
        std::cout << "线程 1: 读取 head = " << old_head->value << std::endl;

        // 模拟延迟
        std::this_thread::sleep_for(std::chrono::milliseconds(10));

        // 尝试 CAS
        Node* new_node = new Node{3, nullptr};
        if (head.compare_exchange_strong(old_head, new_node)) {
            std::cout << "线程 1: CAS 成功" << std::endl;
        } else {
            std::cout << "线程 1: CAS 失败" << std::endl;
            delete new_node;
        }
    });

    // 线程 2：修改 head（A -> B -> A）
    std::thread t2([&]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(5));

        Node* old_head = head.load(std::memory_order_acquire);
        Node* new_head = new Node{2, old_head};
        head.store(new_head, std::memory_order_release);
        std::cout << "线程 2: head = " << new_head->value << std::endl;

        // 恢复原来的值（ABA）
        head.store(old_head, std::memory_order_release);
        std::cout << "线程 2: head 恢复为 " << old_head->value << std::endl;
    });

    t1.join();
    t2.join();

    // 清理
    Node* current = head.load();
    while (current) {
        Node* next = current->next;
        delete current;
        current = next;
    }
}

// 示例4：版本号解决 ABA
void versioned_cas() {
    std::cout << "\n=== 版本号解决 ABA ===" << std::endl;

    struct VersionedValue {
        int value;
        uint32_t version;
    };

    std::atomic<VersionedValue> data{{0, 0}};

    auto update = [&](int new_val) {
        VersionedValue current = data.load(std::memory_order_relaxed);
        VersionedValue desired{new_val, current.version + 1};
        while (!data.compare_exchange_weak(current, desired,
            std::memory_order_relaxed)) {
            desired.version = current.version + 1;
        }
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back(update, i);
    }

    for (auto& t : threads) {
        t.join();
    }

    VersionedValue final = data.load();
    std::cout << "值: " << final.value << ", 版本: " << final.version << std::endl;
}

// 示例5：无锁栈（使用 CAS）
template<typename T>
class LockFreeStack {
private:
    struct Node {
        T data;
        Node* next;
        Node(const T& d) : data(d), next(nullptr) {}
    };

    std::atomic<Node*> head_{nullptr};

public:
    void push(const T& data) {
        Node* new_node = new Node(data);
        Node* old_head = head_.load(std::memory_order_relaxed);
        do {
            new_node->next = old_head;
        } while (!head_.compare_exchange_weak(old_head, new_node,
            std::memory_order_release, std::memory_order_relaxed));
    }

    bool pop(T& result) {
        Node* old_head = head_.load(std::memory_order_acquire);
        while (old_head && !head_.compare_exchange_weak(old_head, old_head->next,
            std::memory_order_acquire)) {
            // 重试
        }
        if (!old_head) return false;
        result = old_head->data;
        delete old_head;
        return true;
    }

    ~LockFreeStack() {
        T dummy;
        while (pop(dummy)) {}
    }
};

void lockfree_stack_demo() {
    std::cout << "\n=== 无锁栈演示 ===" << std::endl;

    LockFreeStack<int> stack;

    // 生产者
    auto producer = [&](int id) {
        for (int i = 0; i < 100; ++i) {
            stack.push(id * 100 + i);
        }
    };

    // 消费者
    std::atomic<int> consumed{0};
    auto consumer = [&]() {
        int value;
        while (consumed.load() < 400) {
            if (stack.pop(value)) {
                consumed.fetch_add(1);
            }
        }
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back(producer, i);
    }
    threads.emplace_back(consumer);

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "消费总数: " << consumed.load() << std::endl;
}

// 示例6：CAS 性能
void cas_performance() {
    std::cout << "\n=== CAS 性能 ===" << std::endl;

    const int iterations = 1000000;
    std::atomic<int> counter{0};

    // 单线程 CAS
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        int current = counter.load();
        while (!counter.compare_exchange_weak(current, current + 1)) {}
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto cas_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    // fetch_add
    counter.store(0);
    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1);
    }
    end = std::chrono::high_resolution_clock::now();
    auto fetch_add_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "CAS 循环: " << cas_time.count() << " us" << std::endl;
    std::cout << "fetch_add: " << fetch_add_time.count() << " us" << std::endl;
    std::cout << "CAS 约慢 " << (double)cas_time.count() / fetch_add_time.count() << " 倍" << std::endl;
}

int main() {
    std::cout << "C++ 原子操作：CAS 操作" << std::endl;
    std::cout << "========================\n" << std::endl;

    basic_cas();
    cas_add();
    aba_problem();
    versioned_cas();
    lockfree_stack_demo();
    cas_performance();

    return 0;
}
