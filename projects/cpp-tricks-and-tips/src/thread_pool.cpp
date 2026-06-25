/**
 * thread_pool.cpp - 线程池实现 (Thread Pool)
 *
 * 本文件演示：
 *   1. 简单但完整的线程池实现
 *   2. 使用 std::future 获取任务结果
 *   3. 优雅关闭（graceful shutdown）
 *   4. 并行计算的实际应用示例
 *
 * 编译命令：
 *   g++ -std=c++17 -O2 -pthread -o thread_pool thread_pool.cpp
 *
 * 线程池的核心思想：
 *   - 预先创建一组工作线程
 *   - 任务提交到队列中
 *   - 工作线程从队列中取任务执行
 *   - 避免频繁创建/销毁线程的开销
 */

#include <iostream>
#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <future>
#include <functional>
#include <stdexcept>
#include <chrono>
#include <numeric>
#include <random>
#include <cassert>

// ============================================================================
// 第一部分：线程池核心实现
// ============================================================================

/**
 * 简单线程池
 *
 * 特点：
 *   - 固定数量的工作线程
 *   - 任务队列（支持任意可调用对象）
 *   - 返回 std::future 以获取结果
 *   - 支持优雅关闭
 *
 * 设计要点：
 *   - 使用 condition_variable 实现线程间的高效等待/通知
 *   - 使用 std::packaged_task 将普通函数包装为可获取 future 的任务
 *   - 使用 shared_ptr 存储 packaged_task（因为 std::function 需要可拷贝）
 */
class ThreadPool {
public:
    /**
     * 构造函数
     * @param num_threads 工作线程数量，默认为硬件并发数
     */
    explicit ThreadPool(size_t num_threads = std::thread::hardware_concurrency())
        : stop_(false)
        , active_tasks_(0)
    {
        if (num_threads == 0) {
            num_threads = 1;
        }

        std::cout << "创建线程池，工作线程数: " << num_threads << std::endl;

        // 创建工作线程
        workers_.reserve(num_threads);
        for (size_t i = 0; i < num_threads; ++i) {
            workers_.emplace_back([this, i]() {
                worker_thread(i);
            });
        }
    }

    /**
     * 析构函数 - 优雅关闭线程池
     *
     * 两种关闭策略：
     *   1. 等待所有任务完成后再关闭（本实现使用）
     *   2. 立即关闭，丢弃未完成的任务
     */
    ~ThreadPool() {
        {
            // 获取锁，设置停止标志
            std::unique_lock<std::mutex> lock(queue_mutex_);
            stop_ = true;
        }

        // 通知所有等待中的工作线程
        condition_.notify_all();

        // 等待所有工作线程结束
        for (auto& worker : workers_) {
            if (worker.joinable()) {
                worker.join();
            }
        }

        std::cout << "线程池已关闭" << std::endl;
    }

    /**
     * 提交任务到线程池
     *
     * 模板参数 F: 可调用对象类型
     * 模板参数 Args: 参数类型
     * 返回值: std::future<返回类型>
     *
     * 使用完美转发（perfect forwarding）传递参数
     */
    template <typename F, typename... Args>
    auto submit(F&& func, Args&&... args)
        -> std::future<std::invoke_result_t<F, Args...>>
    {
        // 推导返回类型
        using return_type = std::invoke_result_t<F, Args...>;

        // 创建 packaged_task
        // 使用 shared_ptr 因为 std::function 要求可拷贝，而 packaged_task 只能移动
        auto task = std::make_shared<std::packaged_task<return_type()>>(
            std::bind(std::forward<F>(func), std::forward<Args>(args)...)
        );

        // 获取 future（在添加到队列之前）
        std::future<return_type> result = task->get_future();

        {
            std::unique_lock<std::mutex> lock(queue_mutex_);

            // 检查线程池是否已停止
            if (stop_) {
                throw std::runtime_error("线程池已停止，无法提交新任务");
            }

            // 将任务添加到队列
            // 使用 lambda 包装 packaged_task 的调用
            tasks_.emplace([task]() { (*task)(); });
        }

        // 通知一个等待中的工作线程
        condition_.notify_one();

        return result;
    }

    /**
     * 获取当前队列中待处理的任务数
     */
    size_t pending_tasks() const {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        return tasks_.size();
    }

    /**
     * 获取正在执行的任务数
     */
    size_t active_tasks() const {
        return active_tasks_.load();
    }

    /**
     * 等待所有任务完成
     * 注意：这不会阻止新任务的提交
     */
    void wait_all() {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        completion_condition_.wait(lock, [this]() {
            return tasks_.empty() && active_tasks_.load() == 0;
        });
    }

private:
    /**
     * 工作线程的主函数
     *
     * 工作循环：
     *   1. 等待任务（使用 condition_variable）
     *   2. 取出任务
     *   3. 执行任务
     *   4. 重复
     */
    void worker_thread(size_t id) {
        while (true) {
            std::function<void()> task;

            {
                std::unique_lock<std::mutex> lock(queue_mutex_);

                // 等待条件：有任务可执行 或 线程池停止
                condition_.wait(lock, [this]() {
                    return stop_ || !tasks_.empty();
                });

                // 如果线程池已停止且没有剩余任务，退出
                if (stop_ && tasks_.empty()) {
                    return;
                }

                // 取出任务
                task = std::move(tasks_.front());
                tasks_.pop();
            }

            // 执行任务（在锁之外执行，避免阻塞其他线程）
            active_tasks_.fetch_add(1);
            task();
            active_tasks_.fetch_sub(1);

            // 通知 wait_all() 可能的等待者
            completion_condition_.notify_all();
        }
    }

    // 工作线程集合
    std::vector<std::thread> workers_;

    // 任务队列
    std::queue<std::function<void()>> tasks_;

    // 同步原语
    mutable std::mutex queue_mutex_;             // 保护任务队列
    std::condition_variable condition_;           // 通知工作线程有新任务
    std::condition_variable completion_condition_; // 通知所有任务完成

    // 状态标志
    bool stop_;                                  // 停止标志
    std::atomic<size_t> active_tasks_;           // 正在执行的任务数
};

// ============================================================================
// 第二部分：基本使用示例
// ============================================================================

void demo_basic_usage() {
    std::cout << "\n=== 线程池基本使用 ===" << std::endl;

    // 创建包含 4 个工作线程的线程池
    ThreadPool pool(4);

    // 1. 提交无返回值的任务
    std::cout << "\n--- 提交无返回值任务 ---" << std::endl;
    for (int i = 0; i < 8; ++i) {
        pool.submit([i]() {
            std::cout << "任务 " << i << " 在线程 "
                      << std::this_thread::get_id() << " 上执行" << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        });
    }

    // 等待所有任务完成
    pool.wait_all();
    std::cout << "所有无返回值任务完成" << std::endl;

    // 2. 提交有返回值的任务
    std::cout << "\n--- 提交有返回值任务 ---" << std::endl;
    std::vector<std::future<int>> futures;

    for (int i = 0; i < 8; ++i) {
        futures.push_back(pool.submit([i]() -> int {
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
            return i * i;  // 返回平方值
        }));
    }

    // 收集结果
    std::cout << "平方值结果: ";
    for (auto& future : futures) {
        std::cout << future.get() << " ";  // get() 会阻塞直到结果可用
    }
    std::cout << std::endl;
}

// ============================================================================
// 第三部分：并行计算示例 - 并行求和
// ============================================================================

/**
 * 并行计算数组元素之和
 *
 * 策略：将数组分成若干块，每个线程计算一块的和，最后合并
 *
 * @param pool  线程池
 * @param data  数据数组
 * @param num_chunks 分块数量
 * @return 总和
 */
long long parallel_sum(ThreadPool& pool, const std::vector<int>& data, size_t num_chunks) {
    size_t chunk_size = data.size() / num_chunks;
    std::vector<std::future<long long>> futures;

    // 将任务分发到线程池
    for (size_t i = 0; i < num_chunks; ++i) {
        size_t start = i * chunk_size;
        size_t end = (i == num_chunks - 1) ? data.size() : start + chunk_size;

        futures.push_back(pool.submit([&data, start, end]() -> long long {
            long long sum = 0;
            for (size_t j = start; j < end; ++j) {
                sum += data[j];
            }
            return sum;
        }));
    }

    // 收集各块的结果并求和
    long long total = 0;
    for (auto& future : futures) {
        total += future.get();
    }

    return total;
}

void demo_parallel_sum() {
    std::cout << "\n=== 并行求和示例 ===" << std::endl;

    // 创建测试数据
    constexpr size_t DATA_SIZE = 10000000;  // 1000 万个元素
    std::vector<int> data(DATA_SIZE);

    // 填充数据 1, 2, 3, ..., DATA_SIZE
    std::iota(data.begin(), data.end(), 1);

    // 预期结果：n*(n+1)/2
    long long expected = static_cast<long long>(DATA_SIZE) * (DATA_SIZE + 1) / 2;

    ThreadPool pool(4);

    // 单线程求和（基准）
    auto start = std::chrono::high_resolution_clock::now();
    long long single_thread_sum = 0;
    for (const auto& val : data) {
        single_thread_sum += val;
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto single_duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "单线程求和: " << single_thread_sum
              << " (期望: " << expected << ")"
              << " 耗时: " << single_duration.count() << " ms" << std::endl;

    // 并行求和（4 块）
    start = std::chrono::high_resolution_clock::now();
    long long parallel_sum_4 = parallel_sum(pool, data, 4);
    end = std::chrono::high_resolution_clock::now();
    auto parallel_duration_4 = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "并行求和(4块): " << parallel_sum_4
              << " (期望: " << expected << ")"
              << " 耗时: " << parallel_duration_4.count() << " ms" << std::endl;

    // 并行求和（8 块）
    start = std::chrono::high_resolution_clock::now();
    long long parallel_sum_8 = parallel_sum(pool, data, 8);
    end = std::chrono::high_resolution_clock::now();
    auto parallel_duration_8 = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "并行求和(8块): " << parallel_sum_8
              << " (期望: " << expected << ")"
              << " 耗时: " << parallel_duration_8.count() << " ms" << std::endl;

    // 验证正确性
    assert(single_thread_sum == expected);
    assert(parallel_sum_4 == expected);
    assert(parallel_sum_8 == expected);
    std::cout << "所有结果验证正确！" << std::endl;
}

// ============================================================================
// 第四部分：并行排序示例
// ============================================================================

/**
 * 并行快速排序
 *
 * 策略：
 *   - 选择 pivot 进行分区
 *   - 左右两部分分别提交到线程池并行排序
 *   - 使用 future 等待子任务完成
 *
 * 注意：对于非常小的子数组，直接使用串行排序更高效
 * （避免线程调度的开销超过计算本身的开销）
 */
void parallel_quicksort(ThreadPool& pool, std::vector<int>& arr, int left, int right) {
    if (left >= right) return;

    // 小数组直接使用插入排序
    if (right - left < 1000) {
        std::sort(arr.begin() + left, arr.begin() + right + 1);
        return;
    }

    // 分区操作
    int pivot = arr[right];
    int i = left - 1;
    for (int j = left; j < right; ++j) {
        if (arr[j] <= pivot) {
            std::swap(arr[++i], arr[j]);
        }
    }
    std::swap(arr[i + 1], arr[right]);
    int pivot_pos = i + 1;

    // 将右半部分提交到线程池
    auto right_future = pool.submit([&arr, pivot_pos, right, &pool]() {
        parallel_quicksort(pool, arr, pivot_pos + 1, right);
    });

    // 左半部分在当前线程排序
    parallel_quicksort(pool, arr, left, pivot_pos - 1);

    // 等待右半部分完成
    right_future.get();
}

void demo_parallel_sort() {
    std::cout << "\n=== 并行排序示例 ===" << std::endl;

    // 创建测试数据
    constexpr size_t DATA_SIZE = 10000000;  // 1000 万个元素
    std::vector<int> data(DATA_SIZE);

    // 随机填充
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(1, 1000000);
    for (auto& val : data) {
        val = dis(gen);
    }

    // 复制一份用于并行排序
    auto data_copy = data;

    ThreadPool pool(4);

    // 单线程排序
    auto start = std::chrono::high_resolution_clock::now();
    std::sort(data.begin(), data.end());
    auto end = std::chrono::high_resolution_clock::now();
    auto single_duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "单线程排序: 耗时 " << single_duration.count() << " ms" << std::endl;

    // 并行排序
    start = std::chrono::high_resolution_clock::now();
    parallel_quicksort(pool, data_copy, 0, static_cast<int>(data_copy.size()) - 1);
    end = std::chrono::high_resolution_clock::now();
    auto parallel_duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "并行排序:   耗时 " << parallel_duration.count() << " ms" << std::endl;

    // 验证排序正确性
    bool sorted = std::is_sorted(data_copy.begin(), data_copy.end());
    bool equal = (data == data_copy);
    std::cout << "排序正确性: " << (sorted && equal ? "通过" : "失败") << std::endl;
}

// ============================================================================
// 第五部分：异常处理
// ============================================================================

void demo_exception_handling() {
    std::cout << "\n=== 异常处理演示 ===" << std::endl;

    ThreadPool pool(2);

    // 1. 任务抛出异常
    std::cout << "\n--- 任务中的异常 ---" << std::endl;
    auto future = pool.submit([]() -> int {
        throw std::runtime_error("任务中发生错误！");
        return 42;  // 不会执行到这里
    });

    try {
        future.get();  // 异常会在这里被重新抛出
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }

    // 2. 多个任务，部分失败
    std::cout << "\n--- 多任务部分失败 ---" << std::endl;
    std::vector<std::future<int>> futures;

    for (int i = 0; i < 5; ++i) {
        futures.push_back(pool.submit([i]() -> int {
            if (i == 3) {
                throw std::logic_error("任务 3 故意失败");
            }
            return i * 10;
        }));
    }

    for (size_t i = 0; i < futures.size(); ++i) {
        try {
            int result = futures[i].get();
            std::cout << "任务 " << i << " 结果: " << result << std::endl;
        } catch (const std::exception& e) {
            std::cout << "任务 " << i << " 异常: " << e.what() << std::endl;
        }
    }

    // 3. 线程池状态
    std::cout << "\n--- 线程池状态 ---" << std::endl;
    std::cout << "待处理任务数: " << pool.pending_tasks() << std::endl;
    std::cout << "活跃任务数: " << pool.active_tasks() << std::endl;
}

// ============================================================================
// 第六部分：生产者-消费者模式
// ============================================================================

void demo_producer_consumer() {
    std::cout << "\n=== 生产者-消费者模式 ===" << std::endl;

    ThreadPool pool(3);

    // 生产者提交任务，消费者获取结果
    constexpr int NUM_TASKS = 10;
    std::vector<std::future<std::string>> results;

    // 提交任务（生产者）
    for (int i = 0; i < NUM_TASKS; ++i) {
        results.push_back(pool.submit([i]() -> std::string {
            // 模拟不同耗时的任务
            std::this_thread::sleep_for(std::chrono::milliseconds(50 + i * 20));
            return "任务" + std::to_string(i) + "完成";
        }));
    }

    // 获取结果（消费者）
    std::cout << "等待结果..." << std::endl;
    for (auto& future : results) {
        std::cout << future.get() << std::endl;
    }
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  线程池实现 (Thread Pool)" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. 基本使用
    demo_basic_usage();

    // 2. 并行求和
    demo_parallel_sum();

    // 3. 并行排序
    demo_parallel_sort();

    // 4. 异常处理
    demo_exception_handling();

    // 5. 生产者-消费者模式
    demo_producer_consumer();

    std::cout << "\n========================================" << std::endl;
    std::cout << "总结：" << std::endl;
    std::cout << "- 线程池避免了频繁创建/销毁线程的开销" << std::endl;
    std::cout << "- 使用 future 可以方便地获取异步任务的结果" << std::endl;
    std::cout << "- 优雅关闭确保所有任务完成后才终止" << std::endl;
    std::cout << "- 对于计算密集型任务，线程数通常设为 CPU 核心数" << std::endl;
    std::cout << "- 对于 I/O 密集型任务，可以适当增加线程数" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
