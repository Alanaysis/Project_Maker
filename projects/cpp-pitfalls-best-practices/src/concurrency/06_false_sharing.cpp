/**
 * @file 06_false_sharing.cpp
 * @brief 伪共享陷阱示例
 *
 * 伪共享 (False Sharing)：不同线程访问同一缓存行的不同变量
 * 危害：性能下降、缓存抖动
 */

#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <atomic>
#include <cstring>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：相邻变量的伪共享
 *
 * 问题：不同线程访问同一缓存行的不同变量
 */
struct BadData {
    int counter1;  // 线程 1 访问
    int counter2;  // 线程 2 访问
    // 两个变量在同一缓存行，导致伪共享
};

BadData bad_data;

void bad_increment1() {
    for (int i = 0; i < 1000000; i++) {
        bad_data.counter1++;
    }
}

void bad_increment2() {
    for (int i = 0; i < 1000000; i++) {
        bad_data.counter2++;
    }
}

void bad_false_sharing() {
    auto start = std::chrono::high_resolution_clock::now();

    std::thread t1(bad_increment1);
    std::thread t2(bad_increment2);
    t1.join();
    t2.join();

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "伪共享耗时: " << duration.count() << " ms" << std::endl;
}

/**
 * 错误示例 2：数组中的伪共享
 *
 * 问题：数组元素在同一缓存行
 */
int bad_array[2];

void bad_array_increment1() {
    for (int i = 0; i < 1000000; i++) {
        bad_array[0]++;
    }
}

void bad_array_increment2() {
    for (int i = 0; i < 1000000; i++) {
        bad_array[1]++;
    }
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用填充避免伪共享
 *
 * 解决方案：使用填充将变量分到不同缓存行
 */
struct GoodDataPadded {
    alignas(64) int counter1;  // 缓存行对齐
    alignas(64) int counter2;  // 不同缓存行
};

GoodDataPadded good_data_padded;

void good_padded_increment1() {
    for (int i = 0; i < 1000000; i++) {
        good_data_padded.counter1++;
    }
}

void good_padded_increment2() {
    for (int i = 0; i < 1000000; i++) {
        good_data_padded.counter2++;
    }
}

void good_padded_example() {
    auto start = std::chrono::high_resolution_clock::now();

    std::thread t1(good_padded_increment1);
    std::thread t2(good_padded_increment2);
    t1.join();
    t2.join();

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "填充后耗时: " << duration.count() << " ms" << std::endl;
}

/**
 * 正确示例 2：使用硬件破坏性干扰大小
 *
 * 解决方案：使用硬件缓存行大小
 */
#ifdef __cpp_lib_hardware_interference_size
constexpr size_t cache_line_size = std::hardware_destructive_interference_size;
#else
constexpr size_t cache_line_size = 64;
#endif

struct GoodDataHardware {
    alignas(cache_line_size) int counter1;
    alignas(cache_line_size) int counter2;
};

GoodDataHardware good_data_hardware;

void good_hardware_increment1() {
    for (int i = 0; i < 1000000; i++) {
        good_data_hardware.counter1++;
    }
}

void good_hardware_increment2() {
    for (int i = 0; i < 1000000; i++) {
        good_data_hardware.counter2++;
    }
}

void good_hardware_example() {
    auto start = std::chrono::high_resolution_clock::now();

    std::thread t1(good_hardware_increment1);
    std::thread t2(good_hardware_increment2);
    t1.join();
    t2.join();

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "硬件对齐耗时: " << duration.count() << " ms" << std::endl;
}

/**
 * 正确示例 3：使用 thread_local
 *
 * 解决方案：使用 thread_local 避免共享
 */
thread_local int good_thread_local_counter = 0;

void good_thread_local_increment() {
    for (int i = 0; i < 1000000; i++) {
        good_thread_local_counter++;
    }
}

void good_thread_local_example() {
    auto start = std::chrono::high_resolution_clock::now();

    std::thread t1(good_thread_local_increment);
    std::thread t2(good_thread_local_increment);
    t1.join();
    t2.join();

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "thread_local 耗时: " << duration.count() << " ms" << std::endl;
}

/**
 * 正确示例 4：使用原子变量
 *
 * 解决方案：使用 atomic 变量，但注意伪共享
 */
std::atomic<int> good_atomic_counter1{0};
std::atomic<int> good_atomic_counter2{0};

void good_atomic_increment1() {
    for (int i = 0; i < 1000000; i++) {
        good_atomic_counter1.fetch_add(1, std::memory_order_relaxed);
    }
}

void good_atomic_increment2() {
    for (int i = 0; i < 1000000; i++) {
        good_atomic_counter2.fetch_add(1, std::memory_order_relaxed);
    }
}

void good_atomic_example() {
    auto start = std::chrono::high_resolution_clock::now();

    std::thread t1(good_atomic_increment1);
    std::thread t2(good_atomic_increment2);
    t1.join();
    t2.join();

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "原子变量耗时: " << duration.count() << " ms" << std::endl;
}

/**
 * 正确示例 5：使用填充的原子变量
 *
 * 解决方案：使用填充避免原子变量的伪共享
 */
struct GoodAtomicPadded {
    alignas(cache_line_size) std::atomic<int> counter1{0};
    alignas(cache_line_size) std::atomic<int> counter2{0};
};

GoodAtomicPadded good_atomic_padded;

void good_atomic_padded_increment1() {
    for (int i = 0; i < 1000000; i++) {
        good_atomic_padded.counter1.fetch_add(1, std::memory_order_relaxed);
    }
}

void good_atomic_padded_increment2() {
    for (int i = 0; i < 1000000; i++) {
        good_atomic_padded.counter2.fetch_add(1, std::memory_order_relaxed);
    }
}

void good_atomic_padded_example() {
    auto start = std::chrono::high_resolution_clock::now();

    std::thread t1(good_atomic_padded_increment1);
    std::thread t2(good_atomic_padded_increment2);
    t1.join();
    t2.join();

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "填充原子变量耗时: " << duration.count() << " ms" << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 伪共享陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 相邻变量的伪共享" << std::endl;
    std::cout << "问题：不同线程访问同一缓存行的不同变量" << std::endl;
    bad_false_sharing();
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用填充避免伪共享" << std::endl;
    good_padded_example();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用硬件破坏性干扰大小" << std::endl;
    good_hardware_example();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 thread_local" << std::endl;
    good_thread_local_example();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用原子变量" << std::endl;
    good_atomic_example();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用填充的原子变量" << std::endl;
    good_atomic_padded_example();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
