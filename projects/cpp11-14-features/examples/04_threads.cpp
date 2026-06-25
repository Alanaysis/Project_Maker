/**
 * C++11 并发编程示例
 *
 * 学习目标：
 * 1. 掌握 std::thread 的基本使用
 * 2. 学会使用 std::mutex 保护共享数据
 * 3. 理解 std::condition_variable 条件变量
 * 4. 学会使用 std::future 和 std::promise
 * 5. 实现简单的线程池
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <future>
#include <vector>
#include <queue>
#include <functional>
#include <atomic>
#include <chrono>
#include <string>

// ==========================================
// 1. std::thread 基础
// ==========================================

void thread_function(int id) {
    std::cout << "  [Thread " << id << "] 开始执行" << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    std::cout << "  [Thread " << id << "] 执行完毕" << std::endl;
}

void demonstrate_thread_basics() {
    std::cout << "\n=== 1. std::thread 基础 ===" << std::endl;

    // 创建线程
    std::cout << "--- 创建线程 ---" << std::endl;
    std::thread t1(thread_function, 1);
    std::thread t2(thread_function, 2);

    // 等待线程完成
    t1.join();
    t2.join();

    std::cout << "主线程继续执行" << std::endl;

    // 分离线程
    std::cout << "\n--- 分离线程 ---" << std::endl;
    std::thread t3([]() {
        std::cout << "  分离线程执行" << std::endl;
    });
    t3.detach();

    // 等待分离线程完成
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
}

// ==========================================
// 2. 线程与 Lambda
// ==========================================

void demonstrate_thread_with_lambda() {
    std::cout << "\n=== 2. 线程与 Lambda ===" << std::endl;

    int shared_data = 42;

    // Lambda 线程
    std::thread t([&shared_data]() {
        std::cout << "  Lambda 线程: shared_data = " << shared_data << std::endl;
        shared_data = 100;
    });

    t.join();
    std::cout << "  主线程: shared_data = " << shared_data << std::endl;

    // 多个线程
    std::vector<std::thread> threads;
    for (int i = 0; i < 5; ++i) {
        threads.emplace_back([i]() {
            std::cout << "  线程 " << i << " 执行" << std::endl;
        });
    }

    for (auto& t : threads) {
        t.join();
    }
}

// ==========================================
// 3. 互斥锁
// ==========================================

std::mutex mtx;
int shared_counter = 0;

void increment_counter(int id, int iterations) {
    for (int i = 0; i < iterations; ++i) {
        std::lock_guard<std::mutex> lock(mtx);
        ++shared_counter;
    }
}

void demonstrate_mutex() {
    std::cout << "\n=== 3. 互斥锁 ===" << std::endl;

    shared_counter = 0;
    const int ITERATIONS = 1000;
    const int NUM_THREADS = 5;

    // 使用 mutex 保护共享数据
    std::cout << "--- 使用 mutex ---" << std::endl;
    std::vector<std::thread> threads;
    for (int i = 0; i < NUM_THREADS; ++i) {
        threads.emplace_back(increment_counter, i, ITERATIONS);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "预期值: " << NUM_THREADS * ITERATIONS << std::endl;
    std::cout << "实际值: " << shared_counter << std::endl;

    // 使用 unique_lock
    std::cout << "\n--- 使用 unique_lock ---" << std::endl;
    std::mutex mtx2;
    std::unique_lock<std::mutex> lock(mtx2);
    // 可以手动解锁
    lock.unlock();
    // 可以重新加锁
    lock.lock();
}

// ==========================================
// 4. 死锁示例和解决方案
// ==========================================

std::mutex mutex1;
std::mutex mutex2;

void deadlock_thread1() {
    std::lock_guard<std::mutex> lock1(mutex1);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    std::lock_guard<std::mutex> lock2(mutex2);
    std::cout << "  [Thread1] 获得两个锁" << std::endl;
}

void deadlock_thread2() {
    std::lock_guard<std::mutex> lock2(mutex2);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    std::lock_guard<std::mutex> lock1(mutex1);
    std::cout << "  [Thread2] 获得两个锁" << std::endl;
}

void safe_thread1() {
    // 使用 std::lock 同时锁定多个互斥锁
    std::lock(mutex1, mutex2);
    std::lock_guard<std::mutex> lock1(mutex1, std::adopt_lock);
    std::lock_guard<std::mutex> lock2(mutex2, std::adopt_lock);
    std::cout << "  [Safe Thread1] 获得两个锁" << std::endl;
}

void safe_thread2() {
    std::lock(mutex1, mutex2);
    std::lock_guard<std::mutex> lock2(mutex2, std::adopt_lock);
    std::lock_guard<std::mutex> lock1(mutex1, std::adopt_lock);
    std::cout << "  [Safe Thread2] 获得两个锁" << std::endl;
}

void demonstrate_deadlock() {
    std::cout << "\n=== 4. 死锁示例和解决方案 ===" << std::endl;

    // 死锁示例（注释掉，因为会卡住）
    // std::thread t1(deadlock_thread1);
    // std::thread t2(deadlock_thread2);
    // t1.join();
    // t2.join();

    // 安全的锁定方式
    std::cout << "--- 安全的锁定方式 ---" << std::endl;
    std::thread t3(safe_thread1);
    std::thread t4(safe_thread2);
    t3.join();
    t4.join();
}

// ==========================================
// 5. 条件变量
// ==========================================

std::condition_variable cv;
std::mutex cv_mtx;
bool ready = false;
int data = 0;

void producer() {
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    {
        std::lock_guard<std::mutex> lock(cv_mtx);
        data = 42;
        ready = true;
        std::cout << "  [Producer] 生产数据: " << data << std::endl;
    }
    cv.notify_one();
}

void consumer() {
    std::unique_lock<std::mutex> lock(cv_mtx);
    cv.wait(lock, [] { return ready; });
    std::cout << "  [Consumer] 消费数据: " << data << std::endl;
}

void demonstrate_condition_variable() {
    std::cout << "\n=== 5. 条件变量 ===" << std::endl;

    // 生产者-消费者模式
    std::cout << "--- 生产者-消费者 ---" << std::endl;
    std::thread consumer_thread(consumer);
    std::thread producer_thread(producer);

    consumer_thread.join();
    producer_thread.join();

    // 条件变量与超时
    std::cout << "\n--- 条件变量超时 ---" << std::endl;
    std::mutex timeout_mtx;
    std::condition_variable timeout_cv;
    bool completed = false;

    std::thread timeout_thread([&]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
        std::lock_guard<std::mutex> lock(timeout_mtx);
        completed = true;
        timeout_cv.notify_one();
    });

    std::unique_lock<std::mutex> timeout_lock(timeout_mtx);
    auto status = timeout_cv.wait_for(timeout_lock, std::chrono::milliseconds(100),
        [&] { return completed; });

    if (status) {
        std::cout << "  任务完成" << std::endl;
    } else {
        std::cout << "  等待超时" << std::endl;
    }

    timeout_thread.join();
}

// ==========================================
// 6. std::future 和 std::promise
// ==========================================

void demonstrate_future_promise() {
    std::cout << "\n=== 6. std::future 和 std::promise ===" << std::endl;

    // 基本使用
    std::cout << "--- 基本使用 ---" << std::endl;
    std::promise<int> promise;
    std::future<int> future = promise.get_future();

    std::thread t([&promise]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        promise.set_value(42);
    });

    std::cout << "等待结果..." << std::endl;
    int result = future.get();
    std::cout << "结果: " << result << std::endl;

    t.join();

    // std::async
    std::cout << "\n--- std::async ---" << std::endl;
    auto async_future = std::async(std::launch::async, []() {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        return 100;
    });

    std::cout << "异步计算中..." << std::endl;
    std::cout << "结果: " << async_future.get() << std::endl;

    // 异步任务
    std::cout << "\n--- 异步任务 ---" << std::endl;
    std::vector<std::future<int>> futures;
    for (int i = 0; i < 5; ++i) {
        futures.push_back(std::async(std::launch::async, [i]() {
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
            return i * i;
        }));
    }

    for (auto& f : futures) {
        std::cout << "  结果: " << f.get() << std::endl;
    }
}

// ==========================================
// 7. 线程池实现
// ==========================================

class ThreadPool {
public:
    ThreadPool(size_t threads) : stop_(false) {
        for (size_t i = 0; i < threads; ++i) {
            workers_.emplace_back([this] {
                while (true) {
                    std::function<void()> task;
                    {
                        std::unique_lock<std::mutex> lock(queue_mutex_);
                        condition_.wait(lock, [this] {
                            return stop_ || !tasks_.empty();
                        });
                        if (stop_ && tasks_.empty()) {
                            return;
                        }
                        task = std::move(tasks_.front());
                        tasks_.pop();
                    }
                    task();
                }
            });
        }
    }

    ~ThreadPool() {
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            stop_ = true;
        }
        condition_.notify_all();
        for (std::thread& worker : workers_) {
            worker.join();
        }
    }

    template<class F, class... Args>
    auto enqueue(F&& f, Args&&... args)
        -> std::future<typename std::result_of<F(Args...)>::type>
    {
        using return_type = typename std::result_of<F(Args...)>::type;

        auto task = std::make_shared<std::packaged_task<return_type()>>(
            std::bind(std::forward<F>(f), std::forward<Args>(args)...)
        );

        std::future<return_type> res = task->get_future();
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            if (stop_) {
                throw std::runtime_error("enqueue on stopped ThreadPool");
            }
            tasks_.emplace([task]() { (*task)(); });
        }
        condition_.notify_one();
        return res;
    }

private:
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;
    std::mutex queue_mutex_;
    std::condition_variable condition_;
    bool stop_;
};

void demonstrate_thread_pool() {
    std::cout << "\n=== 7. 线程池实现 ===" << std::endl;

    // 创建线程池
    ThreadPool pool(4);

    // 提交任务
    std::vector<std::future<int>> results;
    for (int i = 0; i < 8; ++i) {
        results.emplace_back(
            pool.enqueue([i]() {
                std::cout << "  [Task " << i << "] 开始执行" << std::endl;
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
                std::cout << "  [Task " << i << "] 执行完毕" << std::endl;
                return i * i;
            })
        );
    }

    // 获取结果
    for (auto& result : results) {
        std::cout << "  结果: " << result.get() << std::endl;
    }
}

// ==========================================
// 8. 原子操作
// ==========================================

std::atomic<int> atomic_counter(0);

void atomic_increment(int iterations) {
    for (int i = 0; i < iterations; ++i) {
        atomic_counter.fetch_add(1, std::memory_order_relaxed);
    }
}

void demonstrate_atomic() {
    std::cout << "\n=== 8. 原子操作 ===" << std::endl;

    atomic_counter = 0;
    const int ITERATIONS = 10000;
    const int NUM_THREADS = 5;

    std::vector<std::thread> threads;
    for (int i = 0; i < NUM_THREADS; ++i) {
        threads.emplace_back(atomic_increment, ITERATIONS);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "预期值: " << NUM_THREADS * ITERATIONS << std::endl;
    std::cout << "实际值: " << atomic_counter << std::endl;
}

// ==========================================
// 主函数
// ==========================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "C++11 并发编程示例" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. thread 基础
    demonstrate_thread_basics();

    // 2. 线程与 Lambda
    demonstrate_thread_with_lambda();

    // 3. 互斥锁
    demonstrate_mutex();

    // 4. 死锁示例和解决方案
    demonstrate_deadlock();

    // 5. 条件变量
    demonstrate_condition_variable();

    // 6. future 和 promise
    demonstrate_future_promise();

    // 7. 线程池
    demonstrate_thread_pool();

    // 8. 原子操作
    demonstrate_atomic();

    std::cout << "\n========================================" << std::endl;
    std::cout << "所有示例执行完毕！" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
