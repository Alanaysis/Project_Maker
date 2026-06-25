/**
 * 03_coroutines.cpp - C++20 协程 (Coroutines)
 *
 * C++20 协程是一种无栈协程，支持挂起和恢复。
 *
 * 核心要点：
 * 1. co_await - 挂起协程等待结果
 * 2. co_yield - 产出值（生成器）
 * 3. co_return - 协程返回
 * 4. Promise 类型 - 控制协程行为
 * 5. Awaitable/Awaiter - 控制等待行为
 *
 * 注意：C++20 协程基础设施较底层，标准库未提供高级封装。
 * 这里实现最小化的 Generator 和 Task 类型来演示。
 */

#include <iostream>
#include <coroutine>
#include <optional>
#include <exception>
#include <string>
#include <vector>
#include <thread>
#include <chrono>

// ============================================================
// 1. Generator - 生成器协程
// ============================================================

template <typename T>
class Generator {
public:
    struct promise_type {
        T current_value;
        std::exception_ptr exception;

        Generator get_return_object() {
            return Generator{
                std::coroutine_handle<promise_type>::from_promise(*this)
            };
        }

        std::suspend_always initial_suspend() noexcept { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }

        // co_yield 支持
        std::suspend_always yield_value(T value) {
            current_value = std::move(value);
            return {};
        }

        // co_return 支持
        void return_void() {}

        void unhandled_exception() {
            exception = std::current_exception();
        }
    };

    // 迭代器
    class iterator {
        std::coroutine_handle<promise_type> handle_;
    public:
        using iterator_category = std::input_iterator_tag;
        using value_type = T;
        using difference_type = std::ptrdiff_t;

        explicit iterator(std::coroutine_handle<promise_type> h) : handle_(h) {}

        iterator& operator++() {
            handle_.resume();
            if (handle_.done()) handle_ = nullptr;
            return *this;
        }

        const T& operator*() const { return handle_.promise().current_value; }
        bool operator==(const iterator& other) const { return handle_ == other.handle_; }
        bool operator!=(const iterator& other) const { return !(*this == other); }
    };

    iterator begin() {
        if (handle_) handle_.resume();
        if (handle_ && handle_.done()) return iterator{nullptr};
        return iterator{handle_};
    }

    iterator end() { return iterator{nullptr}; }

    Generator(const Generator&) = delete;
    Generator& operator=(const Generator&) = delete;
    Generator(Generator&& other) noexcept : handle_(other.handle_) { other.handle_ = nullptr; }
    ~Generator() { if (handle_) handle_.destroy(); }

private:
    explicit Generator(std::coroutine_handle<promise_type> h) : handle_(h) {}
    std::coroutine_handle<promise_type> handle_;
};

// ============================================================
// 2. 简单 Task 类型 - 用于异步操作
// ============================================================

template <typename T>
class Task {
public:
    struct promise_type {
        T result;
        std::exception_ptr exception;

        Task get_return_object() {
            return Task{std::coroutine_handle<promise_type>::from_promise(*this)};
        }

        std::suspend_never initial_suspend() noexcept { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }

        void return_value(T value) { result = std::move(value); }
        void unhandled_exception() { exception = std::current_exception(); }
    };

    T get_result() {
        if (handle_.promise().exception)
            std::rethrow_exception(handle_.promise().exception);
        return handle_.promise().result;
    }

    Task(const Task&) = delete;
    Task(Task&& other) noexcept : handle_(other.handle_) { other.handle_ = nullptr; }
    ~Task() { if (handle_) handle_.destroy(); }

private:
    explicit Task(std::coroutine_handle<promise_type> h) : handle_(h) {}
    std::coroutine_handle<promise_type> handle_;
};

// ============================================================
// 3. Generator 示例函数
// ============================================================

// 斐波那契生成器
Generator<int> fibonacci() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;
        int temp = a + b;
        a = b;
        b = temp;
    }
}

// 范围生成器
Generator<int> range(int start, int end, int step = 1) {
    for (int i = start; i < end; i += step) {
        co_yield i;
    }
}

// 无限计数器
Generator<int> counter(int start = 0) {
    int n = start;
    while (true) {
        co_yield n++;
    }
}

// ============================================================
// 4. Awaitable 类型
// ============================================================

// 简单的 Sleep Awaitable
struct SleepAwaitable {
    std::chrono::milliseconds duration;

    bool await_ready() const noexcept { return duration.count() <= 0; }
    void await_suspend(std::coroutine_handle<>) const {
        std::this_thread::sleep_for(duration);
    }
    void await_resume() const noexcept {}
};

// ============================================================
// 5. 带异常处理的 Generator
// ============================================================

Generator<int> safe_range(int start, int end) {
    if (start >= end) {
        throw std::invalid_argument("start must be less than end");
    }
    for (int i = start; i < end; ++i) {
        co_yield i;
    }
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 协程 (Coroutines) 示例 ===\n\n";

    // 1. 斐波那契生成器
    std::cout << "【1. 斐波那契生成器】\n";
    std::cout << "前10个: ";
    int count = 0;
    for (auto val : fibonacci()) {
        if (count++ >= 10) break;
        std::cout << val << " ";
    }
    std::cout << "\n\n";

    // 2. 范围生成器
    std::cout << "【2. 范围生成器】\n";
    std::cout << "range(0, 10, 2): ";
    for (auto v : range(0, 10, 2)) {
        std::cout << v << " ";
    }
    std::cout << "\n\n";

    // 3. 计数器生成器
    std::cout << "【3. 计数器生成器 - 取前5个】\n";
    std::cout << "counter(): ";
    for (auto v : counter(100)) {
        if (v >= 105) break;
        std::cout << v << " ";
    }
    std::cout << "\n\n";

    // 4. 生成器用于数据处理
    std::cout << "【4. 生成器用于数据处理】\n";
    std::cout << "偶数平方 (0-9): ";
    for (auto v : range(0, 10)) {
        if (v % 2 == 0) {
            std::cout << v * v << " ";
        }
    }
    std::cout << "\n\n";

    // 5. 协程暂停和恢复
    std::cout << "【5. 协程暂停和恢复机制】\n";
    auto gen = range(1, 6);
    auto it = gen.begin();
    std::cout << "逐步获取: ";
    while (it != gen.end()) {
        std::cout << *it << " ";
        ++it;
    }
    std::cout << "\n\n";

    // 6. 异常处理
    std::cout << "【6. 异常处理】\n";
    try {
        auto bad_gen = safe_range(5, 3);
        for (auto v : bad_gen) {
            std::cout << v << " ";
        }
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << "\n";
    }

    try {
        auto good_gen = safe_range(1, 5);
        std::cout << "safe_range(1, 5): ";
        for (auto v : good_gen) {
            std::cout << v << " ";
        }
        std::cout << "\n";
    } catch (const std::exception& e) {
        std::cout << "异常: " << e.what() << "\n";
    }

    // 7. co_await 基础演示
    std::cout << "\n【7. co_await 机制说明】\n";
    std::cout << "co_await 是协程的核心操作符:\n";
    std::cout << "  - 检查 await_ready()：如果就绪，直接继续\n";
    std::cout << "  - 否则调用 await_suspend()：挂起协程\n";
    std::cout << "  - 恢复后调用 await_resume()：获取结果\n";
    std::cout << "  - 支持同步等待、异步等待、条件等待等模式\n\n";

    std::cout << "协程三剑客:\n";
    std::cout << "  co_yield value  - 产出值（用于生成器）\n";
    std::cout << "  co_await expr   - 等待异步操作完成\n";
    std::cout << "  co_return value - 返回最终值并结束协程\n";

    std::cout << "\n=== 协程示例完成 ===\n";
    return 0;
}
