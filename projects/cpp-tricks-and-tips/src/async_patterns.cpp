/**
 * async_patterns.cpp - 异步编程模式 (Async Programming Patterns)
 *
 * 本文件演示：
 *   1. std::async 的使用
 *   2. std::future 和 std::promise
 *   3. std::packaged_task
 *   4. 回调模式（Callback Pattern）
 *   5. 异常处理
 *   6. 超时控制
 *
 * 编译命令：
 *   g++ -std=c++17 -O2 -pthread -o async_patterns async_patterns.cpp
 *
 * C++ 异步编程的核心组件：
 *   - std::async         启动异步任务
 *   - std::future         获取异步结果的句柄
 *   - std::promise        设置异步结果的句柄
 *   - std::packaged_task  将可调用对象包装为异步任务
 */

#include <iostream>
#include <future>
#include <thread>
#include <vector>
#include <string>
#include <functional>
#include <chrono>
#include <numeric>
#include <random>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <stdexcept>
#include <cassert>
#include <optional>

// ============================================================================
// 第一部分：std::async 基础
// ============================================================================

/**
 * std::async 是启动异步任务的最简单方式
 *
 * 启动策略：
 *   - std::launch::async    在新线程中立即执行
 *   - std::launch::deferred 延迟到 get() 调用时执行（惰性求值）
 *   - 默认：async | deferred（由实现决定）
 */
void demo_async_basics() {
    std::cout << "=== std::async 基础 ===" << std::endl;

    // --------------------------------------------------
    // 示例 1：基本的异步任务
    // --------------------------------------------------
    std::cout << "\n--- 基本异步任务 ---" << std::endl;

    // 启动一个异步任务，返回 std::future<int>
    auto future = std::async(std::launch::async, []() -> int {
        std::cout << "异步任务在线程 " << std::this_thread::get_id()
                  << " 上执行" << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        return 42;
    });

    std::cout << "主线程继续执行..." << std::endl;

    // get() 会阻塞直到结果可用
    // 注意：get() 只能调用一次！
    int result = future.get();
    std::cout << "异步结果: " << result << std::endl;

    // --------------------------------------------------
    // 示例 2：启动策略对比
    // --------------------------------------------------
    std::cout << "\n--- 启动策略对比 ---" << std::endl;

    // async 策略：立即在新线程执行
    auto async_future = std::async(std::launch::async, []() {
        std::cout << "async 策略：在线程 " << std::this_thread::get_id()
                  << " 上执行" << std::endl;
        return 1;
    });

    // deferred 策略：延迟到 get() 时执行
    auto deferred_future = std::async(std::launch::deferred, []() {
        std::cout << "deferred 策略：在调用者线程上执行" << std::endl;
        return 2;
    });

    std::cout << "async 结果: " << async_future.get() << std::endl;
    std::cout << "deferred 结果: " << deferred_future.get() << std::endl;

    // --------------------------------------------------
    // 示例 3：带参数的异步任务
    // --------------------------------------------------
    std::cout << "\n--- 带参数的异步任务 ---" << std::endl;

    auto add = [](int a, int b) -> int {
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        return a + b;
    };

    // 参数通过值传递给 async
    auto sum_future = std::async(std::launch::async, add, 10, 20);
    std::cout << "10 + 20 = " << sum_future.get() << std::endl;
}

// ============================================================================
// 第二部分：std::future 和 std::promise
// ============================================================================

/**
 * std::promise 和 std::future 是一对配对的通信机制
 *
 * std::promise: 生产者端，用于设置值
 * std::future:  消费者端，用于获取值
 *
 * 这是一种一次性通信：promise 只能设置一次值
 */
void demo_promise_future() {
    std::cout << "\n=== std::promise 和 std::future ===" << std::endl;

    // --------------------------------------------------
    // 示例 1：基本的 promise-future 通信
    // --------------------------------------------------
    std::cout << "\n--- 基本 promise-future ---" << std::endl;

    // 创建 promise-future 对
    std::promise<int> promise;
    std::future<int> future = promise.get_future();

    // 在另一个线程中设置值
    std::thread producer([&promise]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        std::cout << "生产者设置值: 100" << std::endl;
        promise.set_value(100);  // 设置结果
    });

    // 在主线程中等待并获取值
    std::cout << "消费者等待结果..." << std::endl;
    int value = future.get();  // 阻塞直到值被设置
    std::cout << "消费者获取值: " << value << std::endl;

    producer.join();

    // --------------------------------------------------
    // 示例 2：使用 promise 传递异常
    // --------------------------------------------------
    std::cout << "\n--- promise 传递异常 ---" << std::endl;

    std::promise<std::string> error_promise;
    std::future<std::string> error_future = error_promise.get_future();

    std::thread error_producer([&error_promise]() {
        try {
            // 模拟错误
            throw std::runtime_error("发生了严重错误！");
        } catch (...) {
            // 将异常设置到 promise 中
            error_promise.set_exception(std::current_exception());
        }
    });

    try {
        std::string result = error_future.get();
    } catch (const std::exception& e) {
        std::cout << "捕获到异常: " << e.what() << std::endl;
    }

    error_producer.join();

    // --------------------------------------------------
    // 示例 3：多个 promise-future 用于多路通信
    // --------------------------------------------------
    std::cout << "\n--- 多路 promise-future ---" << std::endl;

    constexpr int NUM_WORKERS = 3;
    std::vector<std::promise<int>> promises(NUM_WORKERS);
    std::vector<std::future<int>> futures;

    // 获取所有 future
    for (auto& p : promises) {
        futures.push_back(p.get_future());
    }

    // 启动多个工作线程
    std::vector<std::thread> workers;
    for (int i = 0; i < NUM_WORKERS; ++i) {
        workers.emplace_back([&promises, i]() {
            std::this_thread::sleep_for(std::chrono::milliseconds(50 * (i + 1)));
            int result = (i + 1) * 100;
            std::cout << "工作线程 " << i << " 完成，结果: " << result << std::endl;
            promises[i].set_value(result);
        });
    }

    // 收集所有结果
    int total = 0;
    for (auto& f : futures) {
        total += f.get();
    }
    std::cout << "所有结果之和: " << total << std::endl;

    for (auto& w : workers) {
        w.join();
    }
}

// ============================================================================
// 第三部分：std::packaged_task
// ============================================================================

/**
 * std::packaged_task 将可调用对象包装为可获取 future 的任务
 *
 * 与 std::async 的区别：
 *   - packaged_task 更灵活，可以手动控制何时执行
 *   - 可以将任务存储在队列中，稍后执行
 *   - 可以在任意线程上执行
 */
void demo_packaged_task() {
    std::cout << "\n=== std::packaged_task ===" << std::endl;

    // --------------------------------------------------
    // 示例 1：基本的 packaged_task
    // --------------------------------------------------
    std::cout << "\n--- 基本 packaged_task ---" << std::endl;

    // 创建 packaged_task
    std::packaged_task<int(int, int)> task([](int a, int b) -> int {
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        return a * b;
    });

    // 获取 future
    auto future = task.get_future();

    // 在另一个线程上执行任务
    std::thread t(std::move(task), 6, 7);

    // 获取结果
    std::cout << "6 * 7 = " << future.get() << std::endl;
    t.join();

    // --------------------------------------------------
    // 示例 2：使用 packaged_task 实现简单任务队列
    // --------------------------------------------------
    std::cout << "\n--- 任务队列 ---" << std::endl;

    // 简单的任务队列
    std::queue<std::packaged_task<void()>> task_queue;
    std::mutex queue_mutex;
    std::condition_variable cv;
    bool done = false;

    // 工作线程
    std::thread worker([&]() {
        while (true) {
            std::packaged_task<void()> task;
            {
                std::unique_lock<std::mutex> lock(queue_mutex);
                cv.wait(lock, [&]() { return !task_queue.empty() || done; });

                if (done && task_queue.empty()) return;

                task = std::move(task_queue.front());
                task_queue.pop();
            }
            task();
        }
    });

    // 提交多个任务
    std::vector<std::future<void>> futures;
    for (int i = 0; i < 5; ++i) {
        std::packaged_task<void()> task([i]() {
            std::cout << "执行任务 " << i << " 在线程 "
                      << std::this_thread::get_id() << std::endl;
        });
        futures.push_back(task.get_future());

        {
            std::lock_guard<std::mutex> lock(queue_mutex);
            task_queue.push(std::move(task));
        }
        cv.notify_one();
    }

    // 等待所有任务完成
    for (auto& f : futures) {
        f.get();
    }

    // 关闭工作线程
    {
        std::lock_guard<std::mutex> lock(queue_mutex);
        done = true;
    }
    cv.notify_one();
    worker.join();
}

// ============================================================================
// 第四部分：回调模式（Callback Pattern）
// ============================================================================

/**
 * 回调函数类型
 * 接收结果或错误
 */
template <typename T>
using Callback = std::function<void(std::optional<T>, std::exception_ptr)>;

/**
 * 异步操作类
 *
 * 演示回调模式：
 *   - 注册成功回调
 *   - 注册失败回调
 *   - 异步执行
 */
template <typename T>
class AsyncOperation {
public:
    using SuccessCallback = std::function<void(const T&)>;
    using ErrorCallback = std::function<void(const std::exception&)>;
    using CompleteCallback = std::function<void()>;

    /**
     * 设置成功回调
     */
    AsyncOperation& on_success(SuccessCallback cb) {
        success_cb_ = std::move(cb);
        return *this;
    }

    /**
     * 设置错误回调
     */
    AsyncOperation& on_error(ErrorCallback cb) {
        error_cb_ = std::move(cb);
        return *this;
    }

    /**
     * 设置完成回调（无论成功或失败都会调用）
     */
    AsyncOperation& on_complete(CompleteCallback cb) {
        complete_cb_ = std::move(cb);
        return *this;
    }

    /**
     * 执行异步操作
     */
    void execute(std::function<T()> func) {
        // 在新线程中执行
        std::thread([this, func = std::move(func)]() {
            try {
                T result = func();
                if (success_cb_) {
                    success_cb_(result);
                }
            } catch (const std::exception& e) {
                if (error_cb_) {
                    error_cb_(e);
                }
            } catch (...) {
                if (error_cb_) {
                    try {
                        throw;
                    } catch (const std::exception& e) {
                        error_cb_(e);
                    }
                }
            }
            if (complete_cb_) {
                complete_cb_();
            }
        }).detach();
    }

private:
    SuccessCallback success_cb_;
    ErrorCallback error_cb_;
    CompleteCallback complete_cb_;
};

/**
 * 使用 future 的异步操作（带回调）
 */
template <typename T>
class FutureWithCallback {
public:
    /**
     * 从 future 创建带回调的操作
     */
    static void then(std::future<T> future,
                     std::function<void(T)> on_success,
                     std::function<void(std::exception_ptr)> on_error = nullptr) {
        std::thread([
            fut = std::move(future),
            success = std::move(on_success),
            error = std::move(on_error)
        ]() mutable {
            try {
                T result = fut.get();
                success(result);
            } catch (...) {
                if (error) {
                    error(std::current_exception());
                }
            }
        }).detach();
    }
};

void demo_callback_pattern() {
    std::cout << "\n=== 回调模式（Callback Pattern）===" << std::endl;

    // --------------------------------------------------
    // 示例 1：使用 AsyncOperation 类
    // --------------------------------------------------
    std::cout << "\n--- AsyncOperation 回调 ---" << std::endl;

    std::promise<void> done_promise;
    auto done_future = done_promise.get_future();

    AsyncOperation<int> op;
    op.on_success([&done_promise](const int& result) {
        std::cout << "成功！结果: " << result << std::endl;
        done_promise.set_value();
    })
    .on_error([&done_promise](const std::exception& e) {
        std::cout << "失败: " << e.what() << std::endl;
        done_promise.set_value();
    })
    .on_complete([]() {
        std::cout << "操作完成（无论成功或失败）" << std::endl;
    })
    .execute([]() -> int {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        return 999;
    });

    done_future.get();  // 等待完成

    // --------------------------------------------------
    // 示例 2：使用 FutureWithCallback
    // --------------------------------------------------
    std::cout << "\n--- FutureWithCallback ---" << std::endl;

    auto async_future = std::async(std::launch::async, []() -> std::string {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        return "Hello from async!";
    });

    std::promise<void> callback_done;
    auto callback_future = callback_done.get_future();

    FutureWithCallback<std::string>::then(
        std::move(async_future),
        [&callback_done](std::string result) {
            std::cout << "回调收到: " << result << std::endl;
            callback_done.set_value();
        },
        [&callback_done](std::exception_ptr ep) {
            try {
                std::rethrow_exception(ep);
            } catch (const std::exception& e) {
                std::cout << "错误: " << e.what() << std::endl;
            }
            callback_done.set_value();
        }
    );

    callback_future.get();
}

// ============================================================================
// 第五部分：异常处理
// ============================================================================

void demo_exception_handling() {
    std::cout << "\n=== 异常处理 ===" << std::endl;

    // --------------------------------------------------
    // 示例 1：std::async 中的异常传播
    // --------------------------------------------------
    std::cout << "\n--- async 异常传播 ---" << std::endl;

    auto risky_task = std::async(std::launch::async, []() -> int {
        // 模拟一个可能失败的操作
        if (true) {
            throw std::runtime_error("异步任务失败！");
        }
        return 42;
    });

    try {
        int result = risky_task.get();
    } catch (const std::runtime_error& e) {
        std::cout << "捕获运行时错误: " << e.what() << std::endl;
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }

    // --------------------------------------------------
    // 示例 2：promise 中的异常
    // --------------------------------------------------
    std::cout << "\n--- promise 异常 ---" << std::endl;

    std::promise<int> promise;
    auto future = promise.get_future();

    std::thread([&promise]() {
        try {
            throw std::logic_error("逻辑错误！");
        } catch (...) {
            promise.set_exception(std::current_exception());
        }
    }).detach();

    try {
        future.get();
    } catch (const std::logic_error& e) {
        std::cout << "捕获逻辑错误: " << e.what() << std::endl;
    }

    // --------------------------------------------------
    // 示例 3：多个异步任务的异常处理
    // --------------------------------------------------
    std::cout << "\n--- 多任务异常处理 ---" << std::endl;

    std::vector<std::future<int>> futures;
    std::vector<std::string> errors;

    for (int i = 0; i < 5; ++i) {
        futures.push_back(std::async(std::launch::async, [i]() -> int {
            if (i == 2) {
                throw std::runtime_error("任务 " + std::to_string(i) + " 失败");
            }
            return i * 10;
        }));
    }

    std::vector<int> results;
    for (size_t i = 0; i < futures.size(); ++i) {
        try {
            results.push_back(futures[i].get());
        } catch (const std::exception& e) {
            errors.push_back(e.what());
        }
    }

    std::cout << "成功结果: ";
    for (int r : results) std::cout << r << " ";
    std::cout << std::endl;

    std::cout << "错误: ";
    for (const auto& e : errors) std::cout << "[" << e << "] ";
    std::cout << std::endl;
}

// ============================================================================
// 第六部分：超时控制
// ============================================================================

void demo_timeout() {
    std::cout << "\n=== 超时控制 ===" << std::endl;

    // --------------------------------------------------
    // 示例 1：带超时的 future 等待
    // --------------------------------------------------
    std::cout << "\n--- future 超时 ---" << std::endl;

    auto slow_task = std::async(std::launch::async, []() -> int {
        std::this_thread::sleep_for(std::chrono::seconds(2));
        return 100;
    });

    // 等待最多 500 毫秒
    auto status = slow_task.wait_for(std::chrono::milliseconds(500));

    switch (status) {
        case std::future_status::ready:
            std::cout << "任务完成: " << slow_task.get() << std::endl;
            break;
        case std::future_status::timeout:
            std::cout << "任务超时！" << std::endl;
            break;
        case std::future_status::deferred:
            std::cout << "任务被延迟执行" << std::endl;
            break;
    }

    // --------------------------------------------------
    // 示例 2：使用 async 实现超时包装器
    // --------------------------------------------------
    std::cout << "\n--- 超时包装器 ---" << std::endl;

    /**
     * 带超时的异步执行
     *
     * @param timeout  超时时间
     * @param func     要执行的函数
     * @return optional，超时返回 nullopt
     */
    auto with_timeout = []<typename T>(std::chrono::milliseconds timeout, T func)
        -> std::optional<decltype(func())>
    {
        auto future = std::async(std::launch::async, std::move(func));

        if (future.wait_for(timeout) == std::future_status::ready) {
            return future.get();
        }
        return std::nullopt;
    };

    // 正常完成的任务
    auto result1 = with_timeout(
        std::chrono::milliseconds(500),
        []() -> int {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            return 42;
        }
    );

    if (result1) {
        std::cout << "快速任务结果: " << *result1 << std::endl;
    } else {
        std::cout << "快速任务超时" << std::endl;
    }

    // 超时的任务
    auto result2 = with_timeout(
        std::chrono::milliseconds(100),
        []() -> int {
            std::this_thread::sleep_for(std::chrono::seconds(1));
            return 99;
        }
    );

    if (result2) {
        std::cout << "慢速任务结果: " << *result2 << std::endl;
    } else {
        std::cout << "慢速任务超时" << std::endl;
    }
}

// ============================================================================
// 第七部分：并行算法 - 异步并行 transform
// ============================================================================

/**
 * 并行 map 操作
 *
 * 将函数应用到容器的每个元素上，使用多个异步任务并行执行
 */
template <typename Container, typename Func>
auto parallel_transform(const Container& input, Func func, size_t num_tasks = 4)
    -> std::vector<std::invoke_result_t<Func, typename Container::value_type>>
{
    using ResultType = std::invoke_result_t<Func, typename Container::value_type>;

    size_t chunk_size = input.size() / num_tasks;
    std::vector<std::future<std::vector<ResultType>>> futures;

    // 分发任务
    for (size_t i = 0; i < num_tasks; ++i) {
        size_t start = i * chunk_size;
        size_t end = (i == num_tasks - 1) ? input.size() : start + chunk_size;

        futures.push_back(std::async(std::launch::async,
            [&input, &func, start, end]() -> std::vector<ResultType> {
                std::vector<ResultType> results;
                results.reserve(end - start);
                for (size_t j = start; j < end; ++j) {
                    results.push_back(func(input[j]));
                }
                return results;
            }
        ));
    }

    // 收集结果
    std::vector<ResultType> all_results;
    all_results.reserve(input.size());
    for (auto& future : futures) {
        auto partial = future.get();
        all_results.insert(all_results.end(),
                          std::make_move_iterator(partial.begin()),
                          std::make_move_iterator(partial.end()));
    }

    return all_results;
}

void demo_parallel_transform() {
    std::cout << "\n=== 并行 Transform ===" << std::endl;

    // 创建测试数据
    std::vector<int> data(1000000);
    std::iota(data.begin(), data.end(), 1);  // 1, 2, 3, ...

    auto start = std::chrono::high_resolution_clock::now();

    // 并行计算平方
    auto squares = parallel_transform(data, [](int x) {
        return static_cast<long long>(x) * x;
    }, 8);  // 使用 8 个任务

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "并行计算 " << data.size() << " 个元素的平方" << std::endl;
    std::cout << "耗时: " << duration.count() << " ms" << std::endl;
    std::cout << "前 5 个结果: ";
    for (size_t i = 0; i < 5; ++i) {
        std::cout << squares[i] << " ";
    }
    std::cout << std::endl;
    std::cout << "最后 5 个结果: ";
    for (size_t i = squares.size() - 5; i < squares.size(); ++i) {
        std::cout << squares[i] << " ";
    }
    std::cout << std::endl;
}

// ============================================================================
// 第八部分：when_all 模式
// ============================================================================

/**
 * 等待所有 future 完成
 *
 * 类似 JavaScript 的 Promise.all()
 *
 * @param futures future 的容器
 * @return 包含所有结果的 vector
 */
template <typename T>
std::vector<T> when_all(std::vector<std::future<T>>& futures) {
    std::vector<T> results;
    results.reserve(futures.size());

    for (auto& future : futures) {
        results.push_back(future.get());
    }

    return results;
}

/**
 * 带超时的 when_all
 *
 * @return 如果全部完成返回结果，否则返回 nullopt
 */
template <typename T>
std::optional<std::vector<T>> when_all_with_timeout(
    std::vector<std::future<T>>& futures,
    std::chrono::milliseconds timeout)
{
    auto deadline = std::chrono::steady_clock::now() + timeout;

    std::vector<T> results;
    results.reserve(futures.size());

    for (auto& future : futures) {
        auto remaining = deadline - std::chrono::steady_clock::now();
        if (remaining <= std::chrono::milliseconds(0)) {
            return std::nullopt;  // 超时
        }

        if (future.wait_for(remaining) == std::future_status::timeout) {
            return std::nullopt;
        }

        results.push_back(future.get());
    }

    return results;
}

void demo_when_all() {
    std::cout << "\n=== when_all 模式 ===" << std::endl;

    // 创建多个异步任务
    std::vector<std::future<int>> futures;

    for (int i = 0; i < 5; ++i) {
        futures.push_back(std::async(std::launch::async, [i]() -> int {
            std::this_thread::sleep_for(std::chrono::milliseconds(100 * (i + 1)));
            std::cout << "任务 " << i << " 完成" << std::endl;
            return i * i;
        }));
    }

    // 等待所有完成
    std::cout << "等待所有任务完成..." << std::endl;
    auto results = when_all(futures);

    std::cout << "所有结果: ";
    for (int r : results) std::cout << r << " ";
    std::cout << std::endl;

    // 带超时的版本
    std::cout << "\n--- 带超时的 when_all ---" << std::endl;
    std::vector<std::future<int>> slow_futures;

    for (int i = 0; i < 3; ++i) {
        slow_futures.push_back(std::async(std::launch::async, [i]() -> int {
            std::this_thread::sleep_for(std::chrono::milliseconds(200 * (i + 1)));
            return i;
        }));
    }

    auto timed_results = when_all_with_timeout(slow_futures,
                                               std::chrono::milliseconds(500));

    if (timed_results) {
        std::cout << "所有任务在超时前完成: ";
        for (int r : *timed_results) std::cout << r << " ";
        std::cout << std::endl;
    } else {
        std::cout << "部分任务超时！" << std::endl;
    }
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  异步编程模式 (Async Patterns)" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. async 基础
    demo_async_basics();

    // 2. promise-future
    demo_promise_future();

    // 3. packaged_task
    demo_packaged_task();

    // 4. 回调模式
    demo_callback_pattern();

    // 5. 异常处理
    demo_exception_handling();

    // 6. 超时控制
    demo_timeout();

    // 7. 并行 transform
    demo_parallel_transform();

    // 8. when_all 模式
    demo_when_all();

    std::cout << "\n========================================" << std::endl;
    std::cout << "总结：" << std::endl;
    std::cout << "- std::async 是最简单的异步任务启动方式" << std::endl;
    std::cout << "- std::promise/future 用于一次性异步通信" << std::endl;
    std::cout << "- std::packaged_task 提供更灵活的任务管理" << std::endl;
    std::cout << "- 回调模式适合事件驱动的场景" << std::endl;
    std::cout << "- 异常会通过 future 传播到调用者" << std::endl;
    std::cout << "- 超时控制避免无限等待" << std::endl;
    std::cout << "- when_all 模式适合并行处理多个独立任务" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
