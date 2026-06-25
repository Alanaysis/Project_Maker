/**
 * coroutines.cpp - C++20 协程 (Coroutines)
 *
 * 本文件演示：
 *   1. 简单的生成器（Generator）协程
 *   2. 基于任务（Task）的协程
 *   3. co_yield, co_await, co_return 的使用
 *   4. 协程的实际应用场景
 *
 * 编译命令：
 *   g++ -std=c++20 -O2 -fcoroutines -o coroutines coroutines.cpp
 *   (需要 GCC 10+ 或 Clang 14+，某些编译器需要 -fcoroutines 标志)
 *
 * C++20 协程的核心概念：
 *   - 协程是可以暂停和恢复的函数
 *   - 使用 co_yield, co_await, co_return 关键字
 *   - 编译器将协程转换为状态机
 *   - 无栈协程（stackless），每个协程只保存必要的状态
 */

#include <iostream>
#include <coroutine>
#include <optional>
#include <variant>
#include <exception>
#include <string>
#include <vector>
#include <functional>
#include <utility>
// Note: <generator> is C++23, using custom Generator<T> implementation below
#include <thread>
#include <chrono>

// ============================================================================
// 检查编译器对协程的支持
// ============================================================================

#if !defined(__cpp_impl_coroutine)
    #error "此编译器不支持 C++20 协程，请使用 GCC 10+, Clang 14+, 或 MSVC 19.28+"
#endif

// ============================================================================
// 第一部分：简单生成器（Generator）
// ============================================================================

/**
 * Generator<T> - 一个简单的生成器协程类型
 *
 * 生成器是一种特殊的协程，它可以：
 *   - 暂停执行并返回一个值（使用 co_yield）
 *   - 恢复执行并继续生成下一个值
 *   - 最终完成（使用 co_return 或自然结束）
 *
 * 惰性求值：生成器在被请求时才计算下一个值
 * 适用于处理大量数据或无限序列
 */
template <typename T>
class Generator {
public:
    /**
     * 协程承诺类型（Promise Type）
     *
     * 每个协程类型都必须有一个 promise_type
     * 它定义了协程的行为：
     *   - 如何开始（initial_suspend）
     *   - 如何暂停（yield_value）
     *   - 如何返回（return_value/return_void）
     *   - 如何结束（final_suspend）
     *   - 如何处理异常（unhandled_exception）
     */
    struct promise_type {
        T current_value;                       // 当前生成的值
        std::exception_ptr exception;          // 存储异常

        /**
         * 获取生成器对象
         * 协程首次创建时调用
         */
        Generator get_return_object() {
            return Generator{
                std::coroutine_handle<promise_type>::from_promise(*this)
            };
        }

        /**
         * 初始挂起点
         *
         * suspend_always: 协程创建后立即挂起（惰性启动）
         *   - 优点：避免不必要的计算
         *   - 适用于生成器
         *
         * suspend_never: 协程创建后立即开始执行
         *   - 适用于需要立即开始的任务
         */
        std::suspend_always initial_suspend() noexcept {
            return {};
        }

        /**
         * 处理 co_yield 表达式
         *
         * 当协程执行 co_yield value 时调用
         * 保存值并挂起协程
         */
        std::suspend_always yield_value(T value) noexcept {
            current_value = std::move(value);
            return {};  // 返回 suspend_always，挂起协程
        }

        /**
         * 处理 co_return 语句
         *
         * co_return void: 无返回值
         * co_return value: 有返回值（使用 return_value）
         */
        void return_void() noexcept {}

        /**
         * 处理未捕获的异常
         *
         * 协程中的异常不会直接传播到调用者
         * 需要在 promise 中捕获并存储，稍后在调用者中重新抛出
         */
        void unhandled_exception() {
            exception = std::current_exception();
        }

        /**
         * 最终挂起点
         *
         * 协程执行完毕后挂起的位置
         * 通常返回 suspend_always，这样我们可以检查最终状态
         */
        std::suspend_always final_suspend() noexcept {
            return {};
        }
    };

    /**
     * 构造函数 - 接收协程句柄
     */
    explicit Generator(std::coroutine_handle<promise_type> handle)
        : handle_(handle) {}

    /**
     * 析构函数 - 销毁协程
     */
    ~Generator() {
        if (handle_) {
            handle_.destroy();
        }
    }

    // 禁止拷贝，允许移动
    Generator(const Generator&) = delete;
    Generator& operator=(const Generator&) = delete;

    Generator(Generator&& other) noexcept
        : handle_(std::exchange(other.handle_, nullptr)) {}

    Generator& operator=(Generator&& other) noexcept {
        if (this != &other) {
            if (handle_) handle_.destroy();
            handle_ = std::exchange(other.handle_, nullptr);
        }
        return *this;
    }

    /**
     * 检查是否还有更多值
     */
    bool has_next() {
        if (!handle_) return false;

        // 恢复协程执行
        handle_.resume();

        // 检查是否已完成
        if (handle_.done()) {
            // 如果有异常，重新抛出
            if (handle_.promise().exception) {
                std::rethrow_exception(handle_.promise().exception);
            }
            return false;
        }

        return true;
    }

    /**
     * 获取下一个值
     */
    T next() {
        return std::move(handle_.promise().current_value);
    }

    /**
     * 范围 for 循环支持（begin/end 迭代器）
     */
    class iterator {
    public:
        using iterator_category = std::input_iterator_tag;
        using value_type = T;
        using difference_type = std::ptrdiff_t;
        using pointer = T*;
        using reference = T&;

        iterator() : gen_(nullptr) {}
        explicit iterator(Generator* gen) : gen_(gen) {
            if (gen_ && !gen_->has_next()) {
                gen_ = nullptr;  // 空序列
            }
        }

        T operator*() const {
            return gen_->next();
        }

        iterator& operator++() {
            if (!gen_->has_next()) {
                gen_ = nullptr;
            }
            return *this;
        }

        bool operator==(const iterator& other) const {
            return gen_ == other.gen_;
        }

        bool operator!=(const iterator& other) const {
            return !(*this == other);
        }

    private:
        Generator* gen_;
    };

    iterator begin() { return iterator(this); }
    iterator end() { return iterator(); }

private:
    std::coroutine_handle<promise_type> handle_;
};

// ============================================================================
// 第二部分：使用 Generator 的示例
// ============================================================================

/**
 * 斐波那契数列生成器
 *
 * 使用 co_yield 逐个生成斐波那契数
 * 由于是惰性求值，可以生成无限序列
 */
Generator<long long> fibonacci() {
    long long a = 0, b = 1;

    while (true) {
        co_yield a;  // 暂停并返回当前值
        auto temp = a;
        a = b;
        b = temp + b;
    }
}

/**
 * 范围生成器
 *
 * 类似 Python 的 range()
 */
Generator<int> range(int start, int end, int step = 1) {
    for (int i = start; i < end; i += step) {
        co_yield i;
    }
}

/**
 * 过滤生成器
 *
 * 对另一个生成器的值进行过滤
 */
template <typename T, typename Pred>
Generator<T> filter(Generator<T> source, Pred predicate) {
    while (source.has_next()) {
        T value = source.next();
        if (predicate(value)) {
            co_yield value;
        }
    }
}

/**
 * 映射生成器
 *
 * 对另一个生成器的值进行转换
 */
template <typename T, typename Func>
auto map(Generator<T> source, Func func) -> Generator<decltype(func(std::declval<T>()))> {
    using ResultType = decltype(func(std::declval<T>()));
    while (source.has_next()) {
        co_yield func(source.next());
    }
}

void demo_generator() {
    std::cout << "\n=== 生成器（Generator）演示 ===" << std::endl;

    // 1. 斐波那契数列
    std::cout << "\n--- 斐波那契数列（前 10 个）---" << std::endl;
    auto fib = fibonacci();
    for (int i = 0; i < 10; ++i) {
        if (fib.has_next()) {
            std::cout << fib.next() << " ";
        }
    }
    std::cout << std::endl;

    // 2. 范围生成器
    std::cout << "\n--- range(1, 10, 2) ---" << std::endl;
    for (auto val : range(1, 10, 2)) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 3. 过滤和映射
    std::cout << "\n--- 过滤偶数，乘以 2 ---" << std::endl;
    auto even_doubled = map(
        filter(range(1, 10), [](int x) { return x % 2 == 0; }),
        [](int x) { return x * 2; }
    );
    for (auto val : even_doubled) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

// ============================================================================
// 第三部分：Task 协程（用于异步操作）
// ============================================================================

/**
 * Task<T> - 一个简单的异步任务协程类型
 *
 * 与 Generator 不同，Task 代表一个异步计算的结果
 * 它支持：
 *   - co_await 等待其他异步操作
 *   - co_return 返回结果
 *   - 组合多个异步操作
 */
template <typename T = void>
class Task {
public:
    struct promise_type {
        T result;
        std::exception_ptr exception;

        Task get_return_object() {
            return Task{
                std::coroutine_handle<promise_type>::from_promise(*this)
            };
        }

        /**
         * 初始挂起
         *
         * suspend_never: 立即开始执行
         *   - 适用于 Task，因为我们通常希望任务立即开始
         */
        std::suspend_never initial_suspend() noexcept { return {}; }

        /**
         * 处理 co_return value
         */
        void return_value(T value) {
            result = std::move(value);
        }

        void unhandled_exception() {
            exception = std::current_exception();
        }

        /**
         * 最终挂起
         *
         * suspend_always: 保持协程存活，直到被显式销毁
         *   - 这样调用者可以获取结果
         */
        std::suspend_always final_suspend() noexcept { return {}; }
    };

    explicit Task(std::coroutine_handle<promise_type> handle)
        : handle_(handle) {}

    ~Task() {
        if (handle_) {
            handle_.destroy();
        }
    }

    // 禁止拷贝
    Task(const Task&) = delete;
    Task& operator=(const Task&) = delete;

    // 允许移动
    Task(Task&& other) noexcept
        : handle_(std::exchange(other.handle_, nullptr)) {}

    /**
     * 获取结果
     * 如果协程未完成，会等待
     */
    T get_result() {
        if (!handle_.done()) {
            // 简单的忙等待（实际应用中应使用事件循环）
            while (!handle_.done()) {
                std::this_thread::yield();
            }
        }

        if (handle_.promise().exception) {
            std::rethrow_exception(handle_.promise().exception);
        }

        return handle_.promise().result;
    }

    bool is_done() const {
        return handle_ && handle_.done();
    }

private:
    std::coroutine_handle<promise_type> handle_;
};

/**
 * Task<void> 的特化版本
 */
template <>
class Task<void> {
public:
    struct promise_type {
        std::exception_ptr exception;

        Task get_return_object() {
            return Task{
                std::coroutine_handle<promise_type>::from_promise(*this)
            };
        }

        std::suspend_never initial_suspend() noexcept { return {}; }
        void return_void() {}
        void unhandled_exception() { exception = std::current_exception(); }
        std::suspend_always final_suspend() noexcept { return {}; }
    };

    explicit Task(std::coroutine_handle<promise_type> handle)
        : handle_(handle) {}

    ~Task() {
        if (handle_) handle_.destroy();
    }

    void wait() {
        while (!handle_.done()) {
            std::this_thread::yield();
        }
        if (handle_.promise().exception) {
            std::rethrow_exception(handle_.promise().exception);
        }
    }

    bool is_done() const {
        return handle_ && handle_.done();
    }

private:
    std::coroutine_handle<promise_type> handle_;
};

// ============================================================================
// 第四部分：Awaitable 类型
// ============================================================================

/**
 * SleepAwaitable - 模拟异步等待
 *
 * 一个 Awaitable 类型必须实现三个方法：
 *   1. await_ready()   - 返回 true 表示无需挂起
 *   2. await_suspend() - 定义挂起时的行为
 *   3. await_resume()  - 恢复时返回的值
 */
struct SleepAwaitable {
    std::chrono::milliseconds duration;

    /**
     * 检查是否需要挂起
     * 如果返回 true，协程不会挂起，直接继续执行
     */
    bool await_ready() const noexcept {
        return duration.count() <= 0;
    }

    /**
     * 挂起时的操作
     * 可以返回 void（立即挂起），或 bool，或协程句柄
     */
    void await_suspend(std::coroutine_handle<> handle) const {
        // 在实际应用中，这里应该将 handle 注册到事件循环
        // 简单起见，我们使用 sleep 模拟
        std::this_thread::sleep_for(duration);
    }

    /**
     * 恢复时返回的值
     */
    void await_resume() const noexcept {}
};

/**
 * 辅助函数：创建 sleep awaitable
 */
SleepAwaitable sleep_for(std::chrono::milliseconds duration) {
    return SleepAwaitable{duration};
}

/**
 * 使用 Task 的异步函数示例
 */
Task<int> async_compute(int x) {
    std::cout << "  开始计算 " << x << " 的平方..." << std::endl;

    // co_await 模拟异步等待
    co_await sleep_for(std::chrono::milliseconds(100));

    int result = x * x;
    std::cout << "  计算完成: " << x << "^2 = " << result << std::endl;

    co_return result;
}

/**
 * 组合多个异步任务
 */
Task<int> async_sum_of_squares(int a, int b) {
    std::cout << "计算 " << a << "^2 + " << b << "^2 ..." << std::endl;

    // 依次等待两个异步计算
    // 直接 co_await 返回的 Task 对象
    Task<int> task_a = async_compute(a);
    Task<int> task_b = async_compute(b);

    int result_a = task_a.get_result();
    int result_b = task_b.get_result();

    co_return result_a + result_b;
}

void demo_task() {
    std::cout << "\n=== Task 协程演示 ===" << std::endl;

    // 1. 简单的异步计算
    std::cout << "\n--- 异步计算平方 ---" << std::endl;
    auto task1 = async_compute(5);
    std::cout << "结果: " << task1.get_result() << std::endl;

    // 2. 组合多个任务
    std::cout << "\n--- 组合多个任务 ---" << std::endl;
    auto task2 = async_sum_of_squares(3, 4);
    std::cout << "最终结果: " << task2.get_result() << std::endl;
}

// ============================================================================
// 第五部分：协程的实际应用 - 异步管道
// ============================================================================

/**
 * 异步数据处理管道
 *
 * 演示协程在数据处理流水线中的应用
 * 每个阶段都是一个协程，通过 co_yield 传递数据
 */
template <typename T>
class AsyncPipeline {
public:
    using ProcessFunc = std::function<Generator<T>(Generator<T>)>;

    AsyncPipeline() = default;

    /**
     * 添加处理阶段
     */
    AsyncPipeline& add_stage(ProcessFunc stage) {
        stages_.push_back(std::move(stage));
        return *this;
    }

    /**
     * 执行管道
     */
    Generator<T> execute(Generator<T> source) {
        Generator<T> current = std::move(source);
        for (auto& stage : stages_) {
            current = stage(std::move(current));
        }
        return current;
    }

private:
    std::vector<ProcessFunc> stages_;
};

void demo_pipeline() {
    std::cout << "\n=== 异步处理管道 ===" << std::endl;

    // 创建数据源：1 到 20
    auto source = range(1, 21);

    // 创建处理管道
    AsyncPipeline<int> pipeline;

    // 阶段 1：过滤偶数
    pipeline.add_stage([](Generator<int> input) -> Generator<int> {
        while (input.has_next()) {
            int val = input.next();
            if (val % 2 == 0) {
                co_yield val;
            }
        }
    });

    // 阶段 2：乘以 3
    pipeline.add_stage([](Generator<int> input) -> Generator<int> {
        while (input.has_next()) {
            co_yield input.next() * 3;
        }
    });

    // 阶段 3：只保留大于 10 的值
    pipeline.add_stage([](Generator<int> input) -> Generator<int> {
        while (input.has_next()) {
            int val = input.next();
            if (val > 10) {
                co_yield val;
            }
        }
    });

    // 执行管道
    auto result = pipeline.execute(std::move(source));

    std::cout << "原始数据: 1..20" << std::endl;
    std::cout << "处理步骤: 过滤偶数 -> 乘以3 -> 保留>10" << std::endl;
    std::cout << "结果: ";
    for (auto val : result) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

// ============================================================================
// 第六部分：使用 std::generator（C++23，如果可用）
// ============================================================================

#if __has_include(<generator>) && defined(__cpp_lib_generator)

/**
 * 使用标准库的 std::generator（C++23）
 * 这是最简洁的生成器写法
 */
std::generator<int> fibonacci_std() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;
        auto temp = a;
        a = b;
        b = temp + b;
    }
}

void demo_std_generator() {
    std::cout << "\n=== std::generator（C++23）演示 ===" << std::endl;

    auto fib = fibonacci_std();
    int count = 0;
    for (auto val : fib) {
        std::cout << val << " ";
        if (++count >= 15) break;
    }
    std::cout << std::endl;
}

#endif  // __cpp_lib_generator

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  C++20 协程 (Coroutines)" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. 生成器演示
    demo_generator();

    // 2. Task 协程演示
    demo_task();

    // 3. 异步管道演示
    demo_pipeline();

    // 4. std::generator（如果可用）
    #if __has_include(<generator>) && defined(__cpp_lib_generator)
    demo_std_generator();
    #endif

    std::cout << "\n========================================" << std::endl;
    std::cout << "总结：" << std::endl;
    std::cout << "- co_yield: 暂停协程并返回一个值（生成器）" << std::endl;
    std::cout << "- co_await: 暂停协程等待异步操作完成" << std::endl;
    std::cout << "- co_return: 结束协程并返回最终值" << std::endl;
    std::cout << "- promise_type 定义了协程的行为" << std::endl;
    std::cout << "- 协程是无栈的，状态保存在堆上" << std::endl;
    std::cout << "- 适用于生成器、异步 I/O、状态机等场景" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
