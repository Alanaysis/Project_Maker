/**
 * @file 03_livelock.cpp
 * @brief 活锁陷阱示例
 *
 * 活锁 (Livelock)：线程不断重试但无法取得进展
 * 危害：CPU 空转、程序无响应
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <chrono>
#include <random>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：礼貌的哲学家问题
 *
 * 问题：两个线程互相谦让，都无法获取资源
 */
std::mutex fork1;
std::mutex fork2;

void bad_polite_philosopher1() {
    while (true) {
        std::unique_lock<std::mutex> lock1(fork1, std::try_to_lock);
        if (lock1.owns_lock()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            std::unique_lock<std::mutex> lock2(fork2, std::try_to_lock);
            if (lock2.owns_lock()) {
                std::cout << "哲学家 1 用餐" << std::endl;
                return;
            }
        }
        // 获取失败，释放锁并重试
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

void bad_polite_philosopher2() {
    while (true) {
        std::unique_lock<std::mutex> lock2(fork2, std::try_to_lock);
        if (lock2.owns_lock()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
            std::unique_lock<std::mutex> lock1(fork1, std::try_to_lock);
            if (lock1.owns_lock()) {
                std::cout << "哲学家 2 用餐" << std::endl;
                return;
            }
        }
        // 获取失败，释放锁并重试
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

/**
 * 错误示例 2：随机重试但同步
 *
 * 问题：两个线程使用相同的随机策略，导致同步失败
 */
std::mutex resource_mutex;
bool resource_available = true;

void bad_random_retry1() {
    std::mt19937 rng(42);  // 相同的种子
    std::uniform_int_distribution<int> dist(1, 100);

    while (true) {
        std::unique_lock<std::mutex> lock(resource_mutex, std::try_to_lock);
        if (lock.owns_lock() && resource_available) {
            resource_available = false;
            std::cout << "线程 1 获取资源" << std::endl;
            return;
        }
        int delay = dist(rng);
        std::this_thread::sleep_for(std::chrono::milliseconds(delay));
    }
}

void bad_random_retry2() {
    std::mt19937 rng(42);  // 相同的种子
    std::uniform_int_distribution<int> dist(1, 100);

    while (true) {
        std::unique_lock<std::mutex> lock(resource_mutex, std::try_to_lock);
        if (lock.owns_lock() && resource_available) {
            resource_available = false;
            std::cout << "线程 2 获取资源" << std::endl;
            return;
        }
        int delay = dist(rng);
        std::this_thread::sleep_for(std::chrono::milliseconds(delay));
    }
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用指数退避
 *
 * 解决方案：使用指数退避策略，避免同步重试
 */
std::mutex good_resource_mutex;
bool good_resource_available = true;

void good_exponential_backoff() {
    int backoff = 1;
    const int max_backoff = 1000;
    std::mt19937 rng(std::hash<std::thread::id>{}(std::this_thread::get_id()));

    while (true) {
        std::unique_lock<std::mutex> lock(good_resource_mutex, std::try_to_lock);
        if (lock.owns_lock() && good_resource_available) {
            good_resource_available = false;
            std::cout << "获取资源成功" << std::endl;
            return;
        }

        // 指数退避
        std::uniform_int_distribution<int> dist(0, backoff);
        int delay = dist(rng);
        std::this_thread::sleep_for(std::chrono::milliseconds(delay));
        backoff = std::min(backoff * 2, max_backoff);
    }
}

void good_exponential_backoff_example() {
    std::thread t1(good_exponential_backoff);
    std::thread t2(good_exponential_backoff);
    t1.join();
    t2.join();
}

/**
 * 正确示例 2：使用条件变量
 *
 * 解决方案：使用条件变量等待资源可用
 */
std::mutex good_cv_mutex;
std::condition_variable good_cv;
bool good_cv_resource_available = true;

void good_condition_variable() {
    std::unique_lock<std::mutex> lock(good_cv_mutex);
    good_cv.wait(lock, [] { return good_cv_resource_available; });
    good_cv_resource_available = false;
    std::cout << "获取资源成功" << std::endl;
}

void good_signal() {
    {
        std::lock_guard<std::mutex> lock(good_cv_mutex);
        good_cv_resource_available = true;
    }
    good_cv.notify_all();
}

void good_condition_variable_example() {
    std::thread t1(good_condition_variable);
    std::thread t2(good_condition_variable);

    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    good_signal();

    t1.join();
    t2.join();
}

/**
 * 正确示例 3：使用超时和回退
 *
 * 解决方案：设置超时，避免无限重试
 */
std::mutex good_timeout_mutex;
bool good_timeout_resource = true;

void good_timeout_strategy() {
    auto start = std::chrono::steady_clock::now();
    auto timeout = std::chrono::seconds(5);

    while (true) {
        std::unique_lock<std::mutex> lock(good_timeout_mutex, std::try_to_lock);
        if (lock.owns_lock() && good_timeout_resource) {
            good_timeout_resource = false;
            std::cout << "获取资源成功" << std::endl;
            return;
        }

        // 检查超时
        auto now = std::chrono::steady_clock::now();
        if (now - start > timeout) {
            std::cout << "获取资源超时" << std::endl;
            return;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

void good_timeout_example() {
    std::thread t1(good_timeout_strategy);
    std::thread t2(good_timeout_strategy);
    t1.join();
    t2.join();
}

/**
 * 正确示例 4：使用随机化策略
 *
 * 解决方案：使用真正的随机延迟
 */
std::mutex good_random_mutex;
bool good_random_resource = true;

void good_random_strategy() {
    // 使用线程 ID 作为种子，确保不同线程有不同的随机序列
    std::mt19937 rng(std::hash<std::thread::id>{}(std::this_thread::get_id()));
    std::uniform_int_distribution<int> dist(1, 100);

    while (true) {
        std::unique_lock<std::mutex> lock(good_random_mutex, std::try_to_lock);
        if (lock.owns_lock() && good_random_resource) {
            good_random_resource = false;
            std::cout << "获取资源成功" << std::endl;
            return;
        }

        int delay = dist(rng);
        std::this_thread::sleep_for(std::chrono::milliseconds(delay));
    }
}

void good_random_example() {
    std::thread t1(good_random_strategy);
    std::thread t2(good_random_strategy);
    t1.join();
    t2.join();
}

/**
 * 正确示例 5：使用优先级
 *
 * 解决方案：使用优先级避免平等竞争
 */
std::mutex good_priority_mutex;
bool good_priority_resource = true;
int next_priority = 0;

void good_priority_strategy(int my_priority) {
    while (true) {
        std::unique_lock<std::mutex> lock(good_priority_mutex, std::try_to_lock);
        if (lock.owns_lock() && good_priority_resource && next_priority == my_priority) {
            good_priority_resource = false;
            std::cout << "线程 " << my_priority << " 获取资源" << std::endl;
            return;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

void good_priority_example() {
    std::thread t1(good_priority_strategy, 0);
    std::thread t2(good_priority_strategy, 1);
    t1.join();
    t2.join();
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 活锁陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 礼貌的哲学家问题" << std::endl;
    std::cout << "问题：两个线程互相谦让，都无法获取资源" << std::endl;
    // bad_polite_philosopher1();  // 注释掉，避免活锁
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用指数退避" << std::endl;
    good_exponential_backoff_example();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用条件变量" << std::endl;
    good_condition_variable_example();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用超时策略" << std::endl;
    good_timeout_example();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用随机化策略" << std::endl;
    good_random_example();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用优先级" << std::endl;
    good_priority_example();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
