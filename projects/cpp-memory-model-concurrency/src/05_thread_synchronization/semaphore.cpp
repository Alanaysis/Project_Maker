/**
 * std::counting_semaphore (C++20)
 *
 * 信号量的特点：
 * 1. 计数信号量
 * 2. 控制并发访问数量
 * 3. 可用于资源池
 * 4. 比互斥量更灵活
 *
 * 编译：g++ -std=c++20 -pthread semaphore.cpp -o semaphore
 */

#include <iostream>
#include <semaphore>
#include <thread>
#include <vector>
#include <chrono>

// 示例1：基本用法
void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // 最多 3 个并发
    std::counting_semaphore<3> semaphore(3);

    std::vector<std::thread> threads;
    for (int i = 0; i < 6; ++i) {
        threads.emplace_back([&semaphore, i]() {
            std::cout << "任务 " << i << " 等待获取资源" << std::endl;
            semaphore.acquire();
            std::cout << "任务 " << i << " 获取资源" << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
            std::cout << "任务 " << i << " 释放资源" << std::endl;
            semaphore.release();
        });
    }

    for (auto& t : threads) {
        t.join();
    }
}

// 示例2：二元信号量（类似互斥量）
void binary_semaphore() {
    std::cout << "\n=== 二元信号量 ===" << std::endl;

    std::binary_semaphore semaphore(1);
    int counter = 0;

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back([&]() {
            for (int j = 0; j < 1000; ++j) {
                semaphore.acquire();
                ++counter;
                semaphore.release();
            }
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "最终计数: " << counter << std::endl;
}

// 示例3：资源池
class ResourcePool {
public:
    ResourcePool(int size) : semaphore_(size) {
        for (int i = 0; i < size; ++i) {
            resources_.push_back(i);
        }
    }

    int acquire() {
        semaphore_.acquire();
        std::lock_guard lock(mutex_);
        int resource = resources_.back();
        resources_.pop_back();
        return resource;
    }

    void release(int resource) {
        {
            std::lock_guard lock(mutex_);
            resources_.push_back(resource);
        }
        semaphore_.release();
    }

private:
    std::counting_semaphore<10> semaphore_;
    std::mutex mutex_;
    std::vector<int> resources_;
};

void resource_pool_demo() {
    std::cout << "\n=== 资源池 ===" << std::endl;

    ResourcePool pool(3);

    std::vector<std::thread> threads;
    for (int i = 0; i < 6; ++i) {
        threads.emplace_back([&pool, i]() {
            std::cout << "任务 " << i << " 等待资源" << std::endl;
            int resource = pool.acquire();
            std::cout << "任务 " << i << " 获取资源 " << resource << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
            std::cout << "任务 " << i << " 释放资源 " << resource << std::endl;
            pool.release(resource);
        });
    }

    for (auto& t : threads) {
        t.join();
    }
}

// 示例4：try_acquire
void try_acquire_demo() {
    std::cout << "\n=== try_acquire ===" << std::endl;

    std::counting_semaphore<2> semaphore(2);

    std::thread t1([&semaphore]() {
        if (semaphore.try_acquire()) {
            std::cout << "线程 1 获取成功" << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
            semaphore.release();
        } else {
            std::cout << "线程 1 获取失败" << std::endl;
        }
    });

    std::thread t2([&semaphore]() {
        if (semaphore.try_acquire()) {
            std::cout << "线程 2 获取成功" << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(200));
            semaphore.release();
        } else {
            std::cout << "线程 2 获取失败" << std::endl;
        }
    });

    std::thread t3([&semaphore]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        if (semaphore.try_acquire()) {
            std::cout << "线程 3 获取成功" << std::endl;
            semaphore.release();
        } else {
            std::cout << "线程 3 获取失败（信号量已满）" << std::endl;
        }
    });

    t1.join();
    t2.join();
    t3.join();
}

int main() {
    std::cout << "C++ 线程同步：std::counting_semaphore (C++20)" << std::endl;
    std::cout << "==============================================\n" << std::endl;

    basic_usage();
    binary_semaphore();
    resource_pool_demo();
    try_acquire_demo();

    return 0;
}
