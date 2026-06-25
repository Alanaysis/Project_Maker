/**
 * 无锁队列 (Lock-free Queue)
 *
 * Michael-Scott Queue 的实现：
 * 1. 使用两个指针：head 和 tail
 * 2. 哨兵节点简化边界处理
 * 3. 支持多生产者多消费者
 * 4. 适合生产者-消费者模式
 *
 * 编译：g++ -std=c++17 -pthread lock_free_queue.cpp -o lock_free_queue
 */

#include <iostream>
#include <atomic>
#include <memory>
#include <thread>
#include <vector>
#include <chrono>

// Michael-Scott 无锁队列
template<typename T>
class LockFreeQueue {
private:
    struct Node {
        std::shared_ptr<T> data;
        std::atomic<Node*> next;
        Node() : data(nullptr), next(nullptr) {}
        Node(const T& d) : data(std::make_shared<T>(d)), next(nullptr) {}
    };

    std::atomic<Node*> head_;
    std::atomic<Node*> tail_;

public:
    LockFreeQueue() {
        Node* dummy = new Node();
        head_.store(dummy, std::memory_order_relaxed);
        tail_.store(dummy, std::memory_order_relaxed);
    }

    ~LockFreeQueue() {
        T dummy;
        while (dequeue(dummy)) {}
        delete head_.load();
    }

    void enqueue(const T& data) {
        Node* new_node = new Node(data);
        Node* old_tail;
        Node* old_next;

        while (true) {
            old_tail = tail_.load(std::memory_order_acquire);
            old_next = old_tail->next.load(std::memory_order_acquire);

            // 检查 tail 是否还是最新的
            if (old_tail == tail_.load(std::memory_order_acquire)) {
                if (old_next == nullptr) {
                    // 尝试链接新节点
                    if (old_tail->next.compare_exchange_weak(old_next, new_node,
                        std::memory_order_release, std::memory_order_relaxed)) {
                        break;
                    }
                } else {
                    // tail 落后了，帮助推进
                    tail_.compare_exchange_weak(old_tail, old_next,
                        std::memory_order_release, std::memory_order_relaxed);
                }
            }
        }

        // 尝试推进 tail
        tail_.compare_exchange_weak(old_tail, new_node,
            std::memory_order_release, std::memory_order_relaxed);
    }

    bool dequeue(T& result) {
        Node* old_head;
        Node* old_tail;
        Node* old_next;

        while (true) {
            old_head = head_.load(std::memory_order_acquire);
            old_tail = tail_.load(std::memory_order_acquire);
            old_next = old_head->next.load(std::memory_order_acquire);

            // 检查 head 是否还是最新的
            if (old_head == head_.load(std::memory_order_acquire)) {
                if (old_head == old_tail) {
                    if (old_next == nullptr) {
                        return false;  // 队列为空
                    }
                    // tail 落后了，帮助推进
                    tail_.compare_exchange_weak(old_tail, old_next,
                        std::memory_order_release, std::memory_order_relaxed);
                } else {
                    // 读取数据
                    if (old_next->data) {
                        result = *old_next->data;
                    }
                    // 尝试推进 head
                    if (head_.compare_exchange_weak(old_head, old_next,
                        std::memory_order_release, std::memory_order_relaxed)) {
                        break;
                    }
                }
            }
        }

        delete old_head;
        return true;
    }

    bool empty() const {
        Node* head = head_.load(std::memory_order_acquire);
        Node* tail = tail_.load(std::memory_order_acquire);
        return head == tail && head->next.load(std::memory_order_acquire) == nullptr;
    }
};

// 基本测试
void basic_test() {
    std::cout << "=== 基本测试 ===" << std::endl;

    LockFreeQueue<int> queue;

    // 入队
    for (int i = 0; i < 10; ++i) {
        queue.enqueue(i);
    }

    // 出队
    int value;
    while (queue.dequeue(value)) {
        std::cout << value << " ";
    }
    std::cout << std::endl;
}

// 并发测试
void concurrent_test() {
    std::cout << "\n=== 并发测试 ===" << std::endl;

    LockFreeQueue<int> queue;
    const int num_producers = 4;
    const int num_consumers = 2;
    const int ops_per_producer = 10000;
    const int total_ops = num_producers * ops_per_producer;

    std::atomic<int> produced{0};
    std::atomic<int> consumed{0};

    // 生产者
    auto producer = [&](int id) {
        for (int i = 0; i < ops_per_producer; ++i) {
            queue.enqueue(id * ops_per_producer + i);
            produced.fetch_add(1, std::memory_order_relaxed);
        }
    };

    // 消费者
    auto consumer = [&]() {
        int value;
        while (consumed.load() < total_ops) {
            if (queue.dequeue(value)) {
                consumed.fetch_add(1, std::memory_order_relaxed);
            }
        }
    };

    auto start = std::chrono::high_resolution_clock::now();

    std::vector<std::thread> threads;
    for (int i = 0; i < num_producers; ++i) {
        threads.emplace_back(producer, i);
    }
    for (int i = 0; i < num_consumers; ++i) {
        threads.emplace_back(consumer);
    }

    for (auto& t : threads) {
        t.join();
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "生产总数: " << produced.load() << std::endl;
    std::cout << "消费总数: " << consumed.load() << std::endl;
    std::cout << "耗时: " << time.count() << " ms" << std::endl;
}

// 性能测试
void performance_test() {
    std::cout << "\n=== 性能测试 ===" << std::endl;

    const int iterations = 100000;

    // 无锁队列
    LockFreeQueue<int> lockfree_queue;
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        lockfree_queue.enqueue(i);
    }
    int dummy;
    while (lockfree_queue.dequeue(dummy)) {}
    auto end = std::chrono::high_resolution_clock::now();
    auto lockfree_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    // 互斥队列
    std::mutex mutex;
    std::vector<int> mutex_queue;
    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        std::lock_guard<std::mutex> lock(mutex);
        mutex_queue.push_back(i);
    }
    while (!mutex_queue.empty()) {
        std::lock_guard<std::mutex> lock(mutex);
        mutex_queue.erase(mutex_queue.begin());
    }
    end = std::chrono::high_resolution_clock::now();
    auto mutex_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "无锁队列: " << lockfree_time.count() << " us" << std::endl;
    std::cout << "互斥队列: " << mutex_time.count() << " us" << std::endl;
    std::cout << "性能比: " << (double)mutex_time.count() / lockfree_time.count() << "x" << std::endl;
}

// 生产者-消费者模式
void producer_consumer_pattern() {
    std::cout << "\n=== 生产者-消费者模式 ===" << std::endl;

    LockFreeQueue<int> queue;
    std::atomic<bool> done{false};

    // 生产者
    auto producer = [&]() {
        for (int i = 0; i < 100; ++i) {
            queue.enqueue(i);
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        done.store(true, std::memory_order_release);
    };

    // 消费者
    auto consumer = [&]() {
        int value;
        while (!done.load(std::memory_order_acquire) || !queue.empty()) {
            if (queue.dequeue(value)) {
                std::cout << "消费: " << value << std::endl;
            }
        }
    };

    std::thread t1(producer);
    std::thread t2(consumer);

    t1.join();
    t2.join();
}

int main() {
    std::cout << "C++ 并发数据结构：无锁队列" << std::endl;
    std::cout << "===========================\n" << std::endl;

    basic_test();
    concurrent_test();
    performance_test();
    producer_consumer_pattern();

    return 0;
}
