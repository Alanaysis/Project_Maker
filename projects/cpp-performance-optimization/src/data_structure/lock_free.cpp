/**
 * @file lock_free.cpp
 * @brief 无锁数据结构示例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <atomic>
#include <thread>
#include <mutex>
#include <stack>

class Timer
{
public:
    using Clock = std::chrono::high_resolution_clock;
    Timer() : start_(Clock::now()) {}
    void reset() { start_ = Clock::now(); }
    double elapsedMs() const {
        return std::chrono::duration_cast<std::chrono::nanoseconds>(
            Clock::now() - start_).count() / 1e6;
    }
private:
    Clock::time_point start_;
};

/**
 * @brief 无锁栈
 */
template<typename T>
class LockFreeStack
{
    struct Node {
        T data;
        Node* next;
        Node(const T& d) : data(d), next(nullptr) {}
    };

    std::atomic<Node*> head_{nullptr};

public:
    void push(const T& data)
    {
        Node* new_node = new Node(data);
        new_node->next = head_.load(std::memory_order_relaxed);
        while (!head_.compare_exchange_weak(new_node->next, new_node,
                                            std::memory_order_release,
                                            std::memory_order_relaxed)) {}
    }

    bool pop(T& result)
    {
        Node* old_head = head_.load(std::memory_order_relaxed);
        while (old_head && !head_.compare_exchange_weak(old_head, old_head->next,
                                                        std::memory_order_acquire,
                                                        std::memory_order_relaxed)) {}
        if (!old_head) return false;
        result = old_head->data;
        delete old_head;
        return true;
    }
};

/**
 * @brief 互斥锁栈
 */
template<typename T>
class MutexStack
{
    std::stack<T> stack_;
    mutable std::mutex mutex_;

public:
    void push(const T& data)
    {
        std::lock_guard<std::mutex> lock(mutex_);
        stack_.push(data);
    }

    bool pop(T& result)
    {
        std::lock_guard<std::mutex> lock(mutex_);
        if (stack_.empty()) return false;
        result = stack_.top();
        stack_.pop();
        return true;
    }
};

void demonstrateLockFreeVsMutex()
{
    std::cout << "=== 无锁 vs 互斥锁 ===\n\n";

    const size_t N = 1000000;
    const size_t num_threads = 4;

    // 互斥锁版本
    {
        MutexStack<int> stack;
        Timer timer;
        std::vector<std::thread> threads;
        for (size_t t = 0; t < num_threads; ++t) {
            threads.emplace_back([&stack, N, t]() {
                for (size_t i = 0; i < N / num_threads; ++i) {
                    stack.push(static_cast<int>(i));
                }
            });
        }
        for (auto& t : threads) t.join();
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "互斥锁栈: " << time << " ms\n";
    }

    // 无锁版本
    {
        LockFreeStack<int> stack;
        Timer timer;
        std::vector<std::thread> threads;
        for (size_t t = 0; t < num_threads; ++t) {
            threads.emplace_back([&stack, N, t]() {
                for (size_t i = 0; i < N / num_threads; ++i) {
                    stack.push(static_cast<int>(i));
                }
            });
        }
        for (auto& t : threads) t.join();
        double time = timer.elapsedMs();
        std::cout << "无锁栈:   " << time << " ms\n";
    }
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  无锁数据结构\n";
    std::cout << "========================================\n\n";
    demonstrateLockFreeVsMutex();
    std::cout << "\n总结: 无锁数据结构在高并发下可以优于互斥锁。\n";
    return 0;
}
