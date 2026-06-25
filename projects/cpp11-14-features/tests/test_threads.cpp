/**
 * 并发编程测试
 */

#include <gtest/gtest.h>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <future>
#include <vector>
#include <atomic>
#include <chrono>

// 测试线程创建和执行
TEST(Threads, BasicThread) {
    int result = 0;
    std::thread t([&result]() {
        result = 42;
    });
    t.join();
    EXPECT_EQ(result, 42);
}

// 测试多个线程
TEST(Threads, MultipleThreads) {
    std::vector<int> results(5, 0);
    std::vector<std::thread> threads;

    for (int i = 0; i < 5; ++i) {
        threads.emplace_back([&results, i]() {
            results[i] = i * 10;
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    for (int i = 0; i < 5; ++i) {
        EXPECT_EQ(results[i], i * 10);
    }
}

// 测试互斥锁
TEST(Threads, Mutex) {
    std::mutex mtx;
    int counter = 0;
    const int ITERATIONS = 1000;

    std::vector<std::thread> threads;
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back([&]() {
            for (int j = 0; j < ITERATIONS; ++j) {
                std::lock_guard<std::mutex> lock(mtx);
                ++counter;
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    EXPECT_EQ(counter, 10 * ITERATIONS);
}

// 测试条件变量
TEST(Threads, ConditionVariable) {
    std::mutex mtx;
    std::condition_variable cv;
    bool ready = false;
    int result = 0;

    std::thread producer([&]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        {
            std::lock_guard<std::mutex> lock(mtx);
            result = 42;
            ready = true;
        }
        cv.notify_one();
    });

    std::thread consumer([&]() {
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [&]() { return ready; });
        EXPECT_EQ(result, 42);
    });

    producer.join();
    consumer.join();
}

// 测试 future 和 promise
TEST(Threads, FuturePromise) {
    std::promise<int> promise;
    std::future<int> future = promise.get_future();

    std::thread t([&promise]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        promise.set_value(42);
    });

    EXPECT_EQ(future.get(), 42);
    t.join();
}

// 测试 async
TEST(Threads, Async) {
    auto future = std::async(std::launch::async, []() {
        return 42;
    });

    EXPECT_EQ(future.get(), 42);
}

// 测试原子操作
TEST(Threads, Atomic) {
    std::atomic<int> counter(0);
    const int ITERATIONS = 1000;

    std::vector<std::thread> threads;
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back([&]() {
            for (int j = 0; j < ITERATIONS; ++j) {
                counter.fetch_add(1, std::memory_order_relaxed);
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    EXPECT_EQ(counter.load(), 10 * ITERATIONS);
}

// 测试线程安全的队列
TEST(Threads, ThreadSafeQueue) {
    std::mutex mtx;
    std::condition_variable cv;
    std::vector<int> queue;
    bool done = false;

    // 生产者
    std::thread producer([&]() {
        for (int i = 0; i < 10; ++i) {
            {
                std::lock_guard<std::mutex> lock(mtx);
                queue.push_back(i);
            }
            cv.notify_one();
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        {
            std::lock_guard<std::mutex> lock(mtx);
            done = true;
        }
        cv.notify_one();
    });

    // 消费者
    std::vector<int> consumed;
    std::thread consumer([&]() {
        while (true) {
            std::unique_lock<std::mutex> lock(mtx);
            cv.wait(lock, [&]() { return !queue.empty() || done; });

            while (!queue.empty()) {
                consumed.push_back(queue.back());
                queue.pop_back();
            }

            if (done && queue.empty()) {
                break;
            }
        }
    });

    producer.join();
    consumer.join();

    EXPECT_EQ(consumed.size(), 10);
}

// 测试线程局部存储
TEST(Threads, ThreadLocalStorage) {
    thread_local int tls_value = 0;
    std::vector<int> results(3, 0);

    std::vector<std::thread> threads;
    for (int i = 0; i < 3; ++i) {
        threads.emplace_back([&results, i]() {
            tls_value = (i + 1) * 10;
            results[i] = tls_value;
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    EXPECT_EQ(results[0], 10);
    EXPECT_EQ(results[1], 20);
    EXPECT_EQ(results[2], 30);
}

// 测试线程 ID
TEST(Threads, ThreadId) {
    std::thread::id main_id = std::this_thread::get_id();
    std::thread::id child_id;

    std::thread t([&child_id]() {
        child_id = std::this_thread::get_id();
    });

    t.join();

    EXPECT_NE(main_id, child_id);
}

// 测试线程睡眠
TEST(Threads, ThreadSleep) {
    auto start = std::chrono::high_resolution_clock::now();

    std::thread t([]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    });

    t.join();

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    EXPECT_GE(duration.count(), 100);
}

// 测试 try_lock
TEST(Threads, TryLock) {
    std::mutex mtx;
    bool locked = false;

    std::thread t1([&]() {
        std::lock_guard<std::mutex> lock(mtx);
        locked = true;
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    });

    std::this_thread::sleep_for(std::chrono::milliseconds(10));

    std::thread t2([&]() {
        bool success = mtx.try_lock();
        if (success) {
            mtx.unlock();
        } else {
            // 锁被其他线程持有
            EXPECT_TRUE(locked);
        }
    });

    t1.join();
    t2.join();
}
