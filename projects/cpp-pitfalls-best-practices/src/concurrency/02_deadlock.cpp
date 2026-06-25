/**
 * @file 02_deadlock.cpp
 * @brief 死锁陷阱示例
 *
 * 死锁 (Deadlock)：多个线程互相等待对方持有的资源
 * 危害：程序挂起、无法继续执行
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <chrono>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：锁顺序不一致
 *
 * 问题：不同线程以不同顺序获取锁，导致死锁
 */
std::mutex mutex_a;
std::mutex mutex_b;

void bad_thread1() {
    std::lock_guard<std::mutex> lock_a(mutex_a);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    std::lock_guard<std::mutex> lock_b(mutex_b);  // 等待 mutex_b
    std::cout << "Thread 1 完成" << std::endl;
}

void bad_thread2() {
    std::lock_guard<std::mutex> lock_b(mutex_b);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    std::lock_guard<std::mutex> lock_a(mutex_a);  // 等待 mutex_a
    std::cout << "Thread 2 完成" << std::endl;
}

void bad_deadlock() {
    std::thread t1(bad_thread1);
    std::thread t2(bad_thread2);
    t1.join();
    t2.join();
}

/**
 * 错误示例 2：嵌套锁
 *
 * 问题：在持有锁的情况下再次获取锁
 */
std::mutex nested_mutex;

void bad_nested_lock() {
    std::lock_guard<std::mutex> lock1(nested_mutex);
    // 在持有锁的情况下再次获取锁
    std::lock_guard<std::mutex> lock2(nested_mutex);  // 死锁！
}

/**
 * 错误示例 3：锁和条件变量
 *
 * 问题：条件变量使用不当导致死锁
 */
std::mutex cv_mutex;
std::condition_variable cv;
bool ready = false;

void bad_wait() {
    std::unique_lock<std::mutex> lock(cv_mutex);
    // 忘记使用谓词，可能导致虚假唤醒或死锁
    cv.wait(lock);  // 可能永远等待
    std::cout << "继续执行" << std::endl;
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：统一锁顺序
 *
 * 解决方案：所有线程以相同顺序获取锁
 */
std::mutex good_mutex_a;
std::mutex good_mutex_b;

void good_thread1() {
    // 始终按 A -> B 顺序获取锁
    std::lock_guard<std::mutex> lock_a(good_mutex_a);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    std::lock_guard<std::mutex> lock_b(good_mutex_b);
    std::cout << "Thread 1 完成" << std::endl;
}

void good_thread2() {
    // 也按 A -> B 顺序获取锁
    std::lock_guard<std::mutex> lock_a(good_mutex_a);
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
    std::lock_guard<std::mutex> lock_b(good_mutex_b);
    std::cout << "Thread 2 完成" << std::endl;
}

void good_lock_order() {
    std::thread t1(good_thread1);
    std::thread t2(good_thread2);
    t1.join();
    t2.join();
}

/**
 * 正确示例 2：使用 std::lock
 *
 * 解决方案：使用 std::lock 同时获取多个锁
 */
std::mutex good_lock_mutex_a;
std::mutex good_lock_mutex_b;

void good_lock_both() {
    // std::lock 同时获取多个锁，避免死锁
    std::lock(good_lock_mutex_a, good_lock_mutex_b);
    std::lock_guard<std::mutex> lock_a(good_lock_mutex_a, std::adopt_lock);
    std::lock_guard<std::mutex> lock_b(good_lock_mutex_b, std::adopt_lock);
    std::cout << "同时获取两个锁" << std::endl;
}

void good_std_lock() {
    std::thread t1(good_lock_both);
    std::thread t2(good_lock_both);
    t1.join();
    t2.join();
}

/**
 * 正确示例 3：使用 std::scoped_lock (C++17)
 *
 * 解决方案：scoped_lock 自动处理多个锁
 */
std::mutex good_scoped_mutex_a;
std::mutex good_scoped_mutex_b;

void good_scoped_lock() {
    // scoped_lock 自动以避免死锁的方式获取锁
    std::scoped_lock lock(good_scoped_mutex_a, good_scoped_mutex_b);
    std::cout << "使用 scoped_lock" << std::endl;
}

void good_scoped_lock_example() {
    std::thread t1(good_scoped_lock);
    std::thread t2(good_scoped_lock);
    t1.join();
    t2.join();
}

/**
 * 正确示例 4：使用条件变量的正确方式
 *
 * 解决方案：使用谓词等待，避免虚假唤醒
 */
std::mutex good_cv_mutex;
std::condition_variable good_cv;
bool good_ready = false;

void good_signal() {
    {
        std::lock_guard<std::mutex> lock(good_cv_mutex);
        good_ready = true;
    }
    good_cv.notify_one();
}

void good_wait() {
    std::unique_lock<std::mutex> lock(good_cv_mutex);
    // 使用谓词等待，避免虚假唤醒
    good_cv.wait(lock, [] { return good_ready; });
    std::cout << "继续执行" << std::endl;
}

void good_condition_variable() {
    std::thread t1(good_wait);
    std::thread t2(good_signal);
    t1.join();
    t2.join();
}

/**
 * 正确示例 5：使用超时避免死锁
 *
 * 解决方案：使用 try_lock_for 设置超时
 */
std::mutex good_timeout_mutex;

void good_timeout_lock() {
    std::unique_lock<std::mutex> lock(good_timeout_mutex, std::defer_lock);
    if (lock.try_lock_for(std::chrono::seconds(1))) {
        std::cout << "获取锁成功" << std::endl;
    } else {
        std::cout << "获取锁超时" << std::endl;
    }
}

void good_timeout_example() {
    std::thread t1(good_timeout_lock);
    std::thread t2(good_timeout_lock);
    t1.join();
    t2.join();
}

/**
 * 正确示例 6：使用 RAII 管理锁
 *
 * 解决方案：使用 lock_guard 或 unique_lock 自动管理锁
 */
std::mutex good_raii_mutex;

void good_raii_lock() {
    std::lock_guard<std::mutex> lock(good_raii_mutex);
    std::cout << "使用 RAII 管理锁" << std::endl;
    // 函数返回时自动释放锁
}

void good_raii_example() {
    std::thread t1(good_raii_lock);
    std::thread t2(good_raii_lock);
    t1.join();
    t2.join();
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 死锁陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 锁顺序不一致" << std::endl;
    std::cout << "问题：不同线程以不同顺序获取锁" << std::endl;
    // bad_deadlock();  // 注释掉，避免死锁
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 统一锁顺序" << std::endl;
    good_lock_order();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 std::lock" << std::endl;
    good_std_lock();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 std::scoped_lock" << std::endl;
    good_scoped_lock_example();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用条件变量的正确方式" << std::endl;
    good_condition_variable();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用超时避免死锁" << std::endl;
    good_timeout_example();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用 RAII 管理锁" << std::endl;
    good_raii_example();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
