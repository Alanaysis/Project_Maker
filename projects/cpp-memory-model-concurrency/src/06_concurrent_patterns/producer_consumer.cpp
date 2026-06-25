/**
 * 生产者-消费者模式
 *
 * 经典的并发模式：
 * 1. 生产者产生数据
 * 2. 消费者处理数据
 * 3. 缓冲区解耦
 * 4. 支持多生产者多消费者
 *
 * 编译：g++ -std=c++17 -pthread producer_consumer.cpp -o producer_consumer
 */

#include <iostream>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <vector>
#include <chrono>
#include <atomic>

// 阻塞队列
template<typename T>
class BlockingQueue {
public:
    explicit BlockingQueue(size_t max_size = 0) : max_size_(max_size) {}

    void push(T item) {
        std::unique_lock lock(mutex_);
        if (max_size_ > 0) {
            not_full_.wait(lock, [this]() {
                return queue_.size() < max_size_ || stopped_;
            });
        }
        if (stopped_) return;
        queue_.push(std::move(item));
        not_empty_.notify_one();
    }

    bool pop(T& item, int timeout_ms = -1) {
        std::unique_lock lock(mutex_);

        if (timeout_ms < 0) {
            not_empty_.wait(lock, [this]() {
                return !queue_.empty() || stopped_;
            });
        } else {
            if (!not_empty_.wait_for(lock, std::chrono::milliseconds(timeout_ms),
                [this]() { return !queue_.empty() || stopped_; })) {
                return false;
            }
        }

        if (stopped_ && queue_.empty()) return false;
        item = std::move(queue_.front());
        queue_.pop();
        not_full_.notify_one();
        return true;
    }

    void stop() {
        {
            std::lock_guard lock(mutex_);
            stopped_ = true;
        }
        not_empty_.notify_all();
        not_full_.notify_all();
    }

    bool empty() const {
        std::lock_guard lock(mutex_);
        return queue_.empty();
    }

    size_t size() const {
        std::lock_guard lock(mutex_);
        return queue_.size();
    }

private:
    mutable std::mutex mutex_;
    std::condition_variable not_empty_;
    std::condition_variable not_full_;
    std::queue<T> queue_;
    size_t max_size_;
    bool stopped_ = false;
};

// 示例1：基本生产者-消费者
void basic_producer_consumer() {
    std::cout << "=== 基本生产者-消费者 ===" << std::endl;

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

// 示例2：多生产者多消费者
void multiple_producers_consumers() {
    std::cout << "\n=== 多生产者多消费者 ===" << std::endl;

    BlockingQueue<int> queue(10);  // 有限缓冲区
    const int items_per_producer = 10;
    const int num_producers = 3;
    const int num_consumers = 2;
    std::atomic<int> produced{0};
    std::atomic<int> consumed{0};

    // 生产者
    std::vector<std::thread> producers;
    for (int i = 0; i < num_producers; ++i) {
        producers.emplace_back([&]() {
            for (int j = 0; j < items_per_producer; ++j) {
                queue.push(j);
                produced.fetch_add(1);
            }
        });
    }

    // 消费者
    std::vector<std::thread> consumers;
    for (int i = 0; i < num_consumers; ++i) {
        consumers.emplace_back([&]() {
            int item;
            while (queue.pop(item)) {
                consumed.fetch_add(1);
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
        });
    }

    // 等待生产者完成
    for (auto& t : producers) {
        t.join();
    }

    // 停止队列
    queue.stop();

    // 等待消费者完成
    for (auto& t : consumers) {
        t.join();
    }

    std::cout << "生产总数: " << produced.load() << std::endl;
    std::cout << "消费总数: " << consumed.load() << std::endl;
}

// 示例3：管道模式
void pipeline_pattern() {
    std::cout << "\n=== 管道模式 ===" << std::endl;

    BlockingQueue<int> queue1;
    BlockingQueue<int> queue2;

    // 阶段 1：生产
    std::thread producer([&]() {
        for (int i = 0; i < 10; ++i) {
            queue1.push(i);
            std::cout << "生产: " << i << std::endl;
        }
        queue1.stop();
    });

    // 阶段 2：处理
    std::thread processor([&]() {
        int item;
        while (queue1.pop(item)) {
            int result = item * 2;
            queue2.push(result);
            std::cout << "处理: " << item << " -> " << result << std::endl;
        }
        queue2.stop();
    });

    // 阶段 3：消费
    std::thread consumer([&]() {
        int item;
        while (queue2.pop(item)) {
            std::cout << "消费: " << item << std::endl;
        }
    });

    producer.join();
    processor.join();
    consumer.join();
}

int main() {
    std::cout << "C++ 并发模式：生产者-消费者" << std::endl;
    std::cout << "=============================\n" << std::endl;

    basic_producer_consumer();
    multiple_producers_consumers();
    pipeline_pattern();

    return 0;
}
