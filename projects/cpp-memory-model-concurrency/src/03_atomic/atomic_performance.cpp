/**
 * 原子操作的性能
 *
 * 原子操作的性能考量：
 * 1. 不同内存序的性能差异
 * 2. 无锁 vs 有锁
 * 3. 缓存行弹跳
 * 4. 原子操作的开销
 *
 * 编译：g++ -std=c++17 -pthread atomic_performance.cpp -o atomic_performance
 */

#include <iostream>
#include <atomic>
#include <thread>
#include <vector>
#include <mutex>
#include <chrono>
#include <iomanip>

// 计时器
class Timer {
public:
    Timer() : start_(std::chrono::high_resolution_clock::now()) {}

    double elapsed_us() const {
        auto end = std::chrono::high_resolution_clock::now();
        return std::chrono::duration<double, std::micro>(end - start_).count();
    }

private:
    std::chrono::high_resolution_clock::time_point start_;
};

// 示例1：不同内存序的性能
void memory_order_performance() {
    std::cout << "=== 不同内存序的性能 ===" << std::endl;

    const int iterations = 1000000;
    std::atomic<int> counter{0};

    // relaxed
    Timer timer;
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_relaxed);
    }
    double relaxed_time = timer.elapsed_us();

    // acquire-release
    counter.store(0);
    timer = Timer();
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_acq_rel);
    }
    double acq_rel_time = timer.elapsed_us();

    // seq_cst
    counter.store(0);
    timer = Timer();
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_seq_cst);
    }
    double seq_cst_time = timer.elapsed_us();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "relaxed:  " << relaxed_time << " us" << std::endl;
    std::cout << "acq_rel:  " << acq_rel_time << " us" << std::endl;
    std::cout << "seq_cst:  " << seq_cst_time << " us" << std::endl;
    std::cout << "seq_cst/relaxed: " << seq_cst_time / relaxed_time << "x" << std::endl;
}

// 示例2：原子操作 vs 互斥锁
void atomic_vs_mutex() {
    std::cout << "\n=== 原子操作 vs 互斥锁 ===" << std::endl;

    const int iterations = 1000000;

    // 原子操作
    std::atomic<int> atomic_counter{0};
    Timer timer;
    for (int i = 0; i < iterations; ++i) {
        atomic_counter.fetch_add(1, std::memory_order_relaxed);
    }
    double atomic_time = timer.elapsed_us();

    // 互斥锁
    std::mutex mutex;
    int mutex_counter = 0;
    timer = Timer();
    for (int i = 0; i < iterations; ++i) {
        std::lock_guard<std::mutex> lock(mutex);
        mutex_counter++;
    }
    double mutex_time = timer.elapsed_us();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "原子操作: " << atomic_time << " us" << std::endl;
    std::cout << "互斥锁:  " << mutex_time << " us" << std::endl;
    std::cout << "互斥锁/原子操作: " << mutex_time / atomic_time << "x" << std::endl;
}

// 示例3：多线程竞争
void contention_performance() {
    std::cout << "\n=== 多线程竞争 ===" << std::endl;

    const int iterations = 100000;
    std::atomic<int> atomic_counter{0};
    std::mutex mutex;
    int mutex_counter = 0;

    auto atomic_worker = [&]() {
        for (int i = 0; i < iterations; ++i) {
            atomic_counter.fetch_add(1, std::memory_order_relaxed);
        }
    };

    auto mutex_worker = [&]() {
        for (int i = 0; i < iterations; ++i) {
            std::lock_guard<std::mutex> lock(mutex);
            mutex_counter++;
        }
    };

    // 测试不同线程数
    for (int num_threads : {1, 2, 4, 8}) {
        // 原子操作
        atomic_counter.store(0);
        Timer timer;
        std::vector<std::thread> threads;
        for (int i = 0; i < num_threads; ++i) {
            threads.emplace_back(atomic_worker);
        }
        for (auto& t : threads) {
            t.join();
        }
        double atomic_time = timer.elapsed_us();

        // 互斥锁
        mutex_counter = 0;
        timer = Timer();
        threads.clear();
        for (int i = 0; i < num_threads; ++i) {
            threads.emplace_back(mutex_worker);
        }
        for (auto& t : threads) {
            t.join();
        }
        double mutex_time = timer.elapsed_us();

        std::cout << "线程数 " << num_threads << ": "
                  << "原子=" << atomic_time << " us, "
                  << "互斥=" << mutex_time << " us, "
                  << "比值=" << mutex_time / atomic_time << "x" << std::endl;
    }
}

// 示例4：缓存行弹跳
void cache_line_bouncing() {
    std::cout << "\n=== 缓存行弹跳 ===" << std::endl;

    const int iterations = 100000;

    // 同一缓存行（伪共享）
    struct SharedLine {
        std::atomic<int> x;
        std::atomic<int> y;
    } shared;

    auto worker_x = [&]() {
        for (int i = 0; i < iterations; ++i) {
            shared.x.fetch_add(1, std::memory_order_relaxed);
        }
    };

    auto worker_y = [&]() {
        for (int i = 0; i < iterations; ++i) {
            shared.y.fetch_add(1, std::memory_order_relaxed);
        }
    };

    Timer timer;
    std::thread t1(worker_x);
    std::thread t2(worker_y);
    t1.join();
    t2.join();
    double shared_time = timer.elapsed_us();

    // 不同缓存行（填充）
    struct PaddedLine {
        std::atomic<int> x;
        char padding[64 - sizeof(std::atomic<int>)];
        std::atomic<int> y;
    } padded;

    auto worker_px = [&]() {
        for (int i = 0; i < iterations; ++i) {
            padded.x.fetch_add(1, std::memory_order_relaxed);
        }
    };

    auto worker_py = [&]() {
        for (int i = 0; i < iterations; ++i) {
            padded.y.fetch_add(1, std::memory_order_relaxed);
        }
    };

    timer = Timer();
    std::thread t3(worker_px);
    std::thread t4(worker_py);
    t3.join();
    t4.join();
    double padded_time = timer.elapsed_us();

    std::cout << "伪共享: " << shared_time << " us" << std::endl;
    std::cout << "填充后: " << padded_time << " us" << std::endl;
    std::cout << "性能提升: " << shared_time / padded_time << "x" << std::endl;
}

// 示例5：不同原子操作的性能
void atomic_operation_performance() {
    std::cout << "\n=== 不同原子操作的性能 ===" << std::endl;

    const int iterations = 1000000;
    std::atomic<int> counter{0};

    // load
    Timer timer;
    for (int i = 0; i < iterations; ++i) {
        counter.load(std::memory_order_relaxed);
    }
    double load_time = timer.elapsed_us();

    // store
    timer = Timer();
    for (int i = 0; i < iterations; ++i) {
        counter.store(i, std::memory_order_relaxed);
    }
    double store_time = timer.elapsed_us();

    // fetch_add
    counter.store(0);
    timer = Timer();
    for (int i = 0; i < iterations; ++i) {
        counter.fetch_add(1, std::memory_order_relaxed);
    }
    double fetch_add_time = timer.elapsed_us();

    // exchange
    counter.store(0);
    timer = Timer();
    for (int i = 0; i < iterations; ++i) {
        counter.exchange(i, std::memory_order_relaxed);
    }
    double exchange_time = timer.elapsed_us();

    // CAS
    counter.store(0);
    timer = Timer();
    for (int i = 0; i < iterations; ++i) {
        int expected = i;
        counter.compare_exchange_strong(expected, i + 1, std::memory_order_relaxed);
    }
    double cas_time = timer.elapsed_us();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "load:       " << load_time << " us" << std::endl;
    std::cout << "store:      " << store_time << " us" << std::endl;
    std::cout << "fetch_add:  " << fetch_add_time << " us" << std::endl;
    std::cout << "exchange:   " << exchange_time << " us" << std::endl;
    std::cout << "CAS:        " << cas_time << " us" << std::endl;
}

int main() {
    std::cout << "C++ 原子操作：性能测试" << std::endl;
    std::cout << "========================\n" << std::endl;

    memory_order_performance();
    atomic_vs_mutex();
    contention_performance();
    cache_line_bouncing();
    atomic_operation_performance();

    return 0;
}
