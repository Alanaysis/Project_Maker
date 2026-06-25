/**
 * std::condition_variable
 *
 * 条件变量的使用：
 * 1. 等待条件满足
 * 2. 通知等待线程
 * 3. 避免忙等待
 * 4. 生产者-消费者模式
 *
 * 编译：g++ -std=c++17 -pthread condition_variable.cpp -o condition_variable
 */

#include <iostream>
#include <condition_variable>
#include <mutex>
#include <thread>
#include <queue>
#include <vector>
#include <chrono>

// 示例1：基本用法
void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::mutex mutex;
    std::condition_variable cv;
    bool ready = false;
    int data = 0;

    // 等待线程
    std::thread waiter([&]() {
        std::unique_lock lock(mutex);
        cv.wait(lock, [&]() { return ready; });
        std::cout << "收到数据: " << data << std::endl;
    });

    // 通知线程
    std::thread notifier([&]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        {
            std::lock_guard lock(mutex);
            data = 42;
            ready = true;
        }
        cv.notify_one();
    });

    waiter.join();
    notifier.join();
}

// 示例2：生产者-消费者队列
template<typename T>
class BlockingQueue {
public:
    void push(T item) {
        {
            std::lock_guard lock(mutex_);
            queue_.push(std::move(item));
        }
        cv_.notify_one();
    }

    bool pop(T& item, int timeout_ms = -1) {
        std::unique_lock lock(mutex_);

        if (timeout_ms < 0) {
            cv_.wait(lock, [this]() { return !queue_.empty() || stopped_; });
        } else {
            if (!cv_.wait_for(lock, std::chrono::milliseconds(timeout_ms),
                [this]() { return !queue_.empty() || stopped_; })) {
                return false;
            }
        }

        if (stopped_ && queue_.empty()) return false;

        item = std::move(queue_.front());
        queue_.pop();
        return true;
    }

    void stop() {
        {
            std::lock_guard lock(mutex_);
            stopped_ = true;
        }
        cv_.notify_all();
    }

    bool empty() const {
        std::lock_guard lock(mutex_);
        return queue_.empty();
    }

private:
    mutable std::mutex mutex_;
    std::condition_variable cv_;
    std::queue<T> queue_;
    bool stopped_ = false;
};

void producer_consumer() {
    std::cout << "\n=== 生产者-消费者队列 ===" << std::endl;

    BlockingQueue<int> queue;
    const int num_items = 20;

    // 生产者
    std::thread producer([&]() {
        for (int i = 0; i < num_items; ++i) {
            queue.push(i);
            std::cout << "生产: " << i << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
        queue.stop();
    });

    // 消费者
    std::thread consumer([&]() {
        int item;
        while (queue.pop(item)) {
            std::cout << "消费: " << item << std::endl;
        }
    });

    producer.join();
    consumer.join();
}

// 示例3：多消费者
void multiple_consumers() {
    std::cout << "\n=== 多消费者 ===" << std::endl;

    BlockingQueue<int> queue;
    const int num_items = 20;
    std::atomic<int> consumed{0};

    // 生产者
    std::thread producer([&]() {
        for (int i = 0; i < num_items; ++i) {
            queue.push(i);
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        }
        queue.stop();
    });

    // 多个消费者
    std::vector<std::thread> consumers;
    for (int i = 0; i < 3; ++i) {
        consumers.emplace_back([&]() {
            int item;
            while (queue.pop(item)) {
                consumed.fetch_add(1);
                std::cout << "消费: " << item << std::endl;
            }
        });
    }

    producer.join();
    for (auto& t : consumers) {
        t.join();
    }

    std::cout << "消费总数: " << consumed.load() << std::endl;
}

// 示例4：超时等待
void timeout_waiting() {
    std::cout << "\n=== 超时等待 ===" << std::endl;

    std::mutex mutex;
    std::condition_variable cv;
    bool ready = false;

    std::thread waiter([&]() {
        std::unique_lock lock(mutex);
        auto status = cv.wait_for(lock, std::chrono::milliseconds(100),
            [&]() { return ready; });

        if (status) {
            std::cout << "条件满足" << std::endl;
        } else {
            std::cout << "超时" << std::endl;
        }
    });

    // 不通知，让等待超时
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    waiter.join();
}

// 示例5：事件通知
class Event {
public:
    void signal() {
        {
            std::lock_guard lock(mutex_);
            signaled_ = true;
        }
        cv_.notify_all();
    }

    void wait() {
        std::unique_lock lock(mutex_);
        cv_.wait(lock, [this]() { return signaled_; });
    }

    bool wait_for(int timeout_ms) {
        std::unique_lock lock(mutex_);
        return cv_.wait_for(lock, std::chrono::milliseconds(timeout_ms),
            [this]() { return signaled_; });
    }

    void reset() {
        std::lock_guard lock(mutex_);
        signaled_ = false;
    }

private:
    std::mutex mutex_;
    std::condition_variable cv_;
    bool signaled_ = false;
};

void event_demo() {
    std::cout << "\n=== 事件通知 ===" << std::endl;

    Event event;

    std::thread waiter([&]() {
        std::cout << "等待事件..." << std::endl;
        event.wait();
        std::cout << "事件已触发" << std::endl;
    });

    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    event.signal();

    waiter.join();
}

int main() {
    std::cout << "C++ 线程同步：std::condition_variable" << std::endl;
    std::cout << "=======================================\n" << std::endl;

    basic_usage();
    producer_consumer();
    multiple_consumers();
    timeout_waiting();
    event_demo();

    return 0;
}
