/**
 * 无锁栈 (Lock-free Stack)
 *
 * Treiber Stack 的实现：
 * 1. 使用 CAS 操作实现无锁
 * 2. 简单但有 ABA 问题
 * 3. 适合低竞争场景
 * 4. 性能优于互斥栈
 *
 * 编译：g++ -std=c++17 -pthread lock_free_stack.cpp -o lock_free_stack
 */

#include <iostream>
#include <atomic>
#include <memory>
#include <thread>
#include <vector>
#include <chrono>

// 基本无锁栈
template<typename T>
class LockFreeStack {
private:
    struct Node {
        std::shared_ptr<T> data;
        Node* next;
        Node(const T& d) : data(std::make_shared<T>(d)), next(nullptr) {}
    };

    std::atomic<Node*> head_{nullptr};
    std::atomic<int> size_{0};

public:
    LockFreeStack() = default;

    ~LockFreeStack() {
        T dummy;
        while (pop(dummy)) {}
    }

    void push(const T& data) {
        Node* new_node = new Node(data);
        Node* old_head = head_.load(std::memory_order_relaxed);
        do {
            new_node->next = old_head;
        } while (!head_.compare_exchange_weak(old_head, new_node,
            std::memory_order_release, std::memory_order_relaxed));
        size_.fetch_add(1, std::memory_order_relaxed);
    }

    bool pop(T& result) {
        Node* old_head = head_.load(std::memory_order_acquire);
        while (old_head && !head_.compare_exchange_weak(old_head, old_head->next,
            std::memory_order_acquire)) {
            // 重试
        }
        if (!old_head) return false;
        result = *old_head->data;
        delete old_head;
        size_.fetch_sub(1, std::memory_order_relaxed);
        return true;
    }

    bool empty() const {
        return head_.load(std::memory_order_relaxed) == nullptr;
    }

    int size() const {
        return size_.load(std::memory_order_relaxed);
    }
};

// 使用 hazard pointer 解决 ABA 问题的无锁栈
template<typename T>
class HazardPointerStack {
private:
    struct Node {
        std::shared_ptr<T> data;
        Node* next;
        Node(const T& d) : data(std::make_shared<T>(d)), next(nullptr) {}
    };

    // hazard pointer 表
    static constexpr int MAX_THREADS = 16;
    static std::atomic<Node*> hazard[MAX_THREADS];
    std::atomic<Node*> head_{nullptr};
    std::atomic<int> size_{0};

    // 线程 ID 分配
    static std::atomic<int> thread_count;
    static thread_local int thread_id;

    bool is_safe(Node* node) {
        for (int i = 0; i < MAX_THREADS; ++i) {
            if (hazard[i].load(std::memory_order_relaxed) == node) {
                return false;
            }
        }
        return true;
    }

public:
    HazardPointerStack() = default;

    ~HazardPointerStack() {
        T dummy;
        while (pop(dummy)) {}
    }

    void push(const T& data) {
        Node* new_node = new Node(data);
        Node* old_head = head_.load(std::memory_order_relaxed);
        do {
            new_node->next = old_head;
        } while (!head_.compare_exchange_weak(old_head, new_node,
            std::memory_order_release, std::memory_order_relaxed));
        size_.fetch_add(1, std::memory_order_relaxed);
    }

    bool pop(T& result) {
        if (thread_id < 0) {
            thread_id = thread_count.fetch_add(1) % MAX_THREADS;
        }

        Node* old_head;
        do {
            old_head = head_.load(std::memory_order_acquire);
            if (!old_head) return false;
            // 设置 hazard pointer
            hazard[thread_id].store(old_head, std::memory_order_release);
        } while (old_head != head_.load(std::memory_order_acquire));

        // 尝试 CAS
        if (head_.compare_exchange_strong(old_head, old_head->next)) {
            result = *old_head->data;
            hazard[thread_id].store(nullptr, std::memory_order_release);
            delete old_head;
            size_.fetch_sub(1, std::memory_order_relaxed);
            return true;
        }

        hazard[thread_id].store(nullptr, std::memory_order_release);
        return false;
    }

    bool empty() const {
        return head_.load(std::memory_order_relaxed) == nullptr;
    }

    int size() const {
        return size_.load(std::memory_order_relaxed);
    }
};

template<typename T>
std::atomic<typename HazardPointerStack<T>::Node*> HazardPointerStack<T>::hazard[MAX_THREADS]{};

template<typename T>
std::atomic<int> HazardPointerStack<T>::thread_count{0};

template<typename T>
thread_local int HazardPointerStack<T>::thread_id = -1;

// 基本测试
void basic_test() {
    std::cout << "=== 基本测试 ===" << std::endl;

    LockFreeStack<int> stack;

    // 压入元素
    for (int i = 0; i < 10; ++i) {
        stack.push(i);
    }

    std::cout << "栈大小: " << stack.size() << std::endl;

    // 弹出元素
    int value;
    while (stack.pop(value)) {
        std::cout << value << " ";
    }
    std::cout << std::endl;
}

// 并发测试
void concurrent_test() {
    std::cout << "\n=== 并发测试 ===" << std::endl;

    LockFreeStack<int> stack;
    const int num_threads = 4;
    const int ops_per_thread = 10000;

    // 生产者
    auto producer = [&](int id) {
        for (int i = 0; i < ops_per_thread; ++i) {
            stack.push(id * ops_per_thread + i);
        }
    };

    // 消费者
    std::atomic<int> consumed{0};
    auto consumer = [&]() {
        int value;
        while (consumed.load() < num_threads * ops_per_thread) {
            if (stack.pop(value)) {
                consumed.fetch_add(1);
            }
        }
    };

    auto start = std::chrono::high_resolution_clock::now();

    std::vector<std::thread> threads;
    for (int i = 0; i < num_threads; ++i) {
        threads.emplace_back(producer, i);
    }
    threads.emplace_back(consumer);

    for (auto& t : threads) {
        t.join();
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "消费总数: " << consumed.load() << std::endl;
    std::cout << "耗时: " << time.count() << " ms" << std::endl;
}

// 性能测试
void performance_test() {
    std::cout << "\n=== 性能测试 ===" << std::endl;

    const int iterations = 100000;

    // 无锁栈
    LockFreeStack<int> lockfree_stack;
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        lockfree_stack.push(i);
    }
    int dummy;
    while (lockfree_stack.pop(dummy)) {}
    auto end = std::chrono::high_resolution_clock::now();
    auto lockfree_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    // 互斥栈
    std::mutex mutex;
    std::vector<int> mutex_stack;
    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        std::lock_guard<std::mutex> lock(mutex);
        mutex_stack.push_back(i);
    }
    while (!mutex_stack.empty()) {
        std::lock_guard<std::mutex> lock(mutex);
        mutex_stack.pop_back();
    }
    end = std::chrono::high_resolution_clock::now();
    auto mutex_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "无锁栈: " << lockfree_time.count() << " us" << std::endl;
    std::cout << "互斥栈: " << mutex_time.count() << " us" << std::endl;
    std::cout << "性能比: " << (double)mutex_time.count() / lockfree_time.count() << "x" << std::endl;
}

int main() {
    std::cout << "C++ 并发数据结构：无锁栈" << std::endl;
    std::cout << "=========================\n" << std::endl;

    basic_test();
    concurrent_test();
    performance_test();

    return 0;
}
