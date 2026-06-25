/**
 * @file test_ring_buffer.cpp
 * @brief 环形缓冲区测试
 */

#include <iostream>
#include <cassert>
#include <thread>
#include <vector>

#include "core/ring_buffer.h"

using namespace hft;

/**
 * @brief 测试基本功能
 */
void test_basic() {
    std::cout << "Test basic functionality...\n";

    RingBuffer<int, 16> buffer;

    // 测试空缓冲区
    assert(buffer.empty());
    assert(!buffer.full());
    assert(buffer.size() == 0);

    // 测试写入
    assert(buffer.try_push(1));
    assert(buffer.try_push(2));
    assert(buffer.try_push(3));

    assert(!buffer.empty());
    assert(buffer.size() == 3);

    // 测试读取
    auto val = buffer.try_pop();
    assert(val.has_value());
    assert(val.value() == 1);

    val = buffer.try_pop();
    assert(val.has_value());
    assert(val.value() == 2);

    val = buffer.try_pop();
    assert(val.has_value());
    assert(val.value() == 3);

    assert(buffer.empty());

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试缓冲区满
 */
void test_full() {
    std::cout << "Test buffer full...\n";

    RingBuffer<int, 4> buffer;

    // 写满缓冲区
    assert(buffer.try_push(1));
    assert(buffer.try_push(2));
    assert(buffer.try_push(3));

    // 缓冲区满（实际容量是 Size - 1）
    assert(!buffer.try_push(4));
    assert(buffer.full());

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试多线程
 */
void test_multithread() {
    std::cout << "Test multithreading...\n";

    RingBuffer<int, 1024> buffer;
    const int count = 100000;

    // 生产者线程
    std::thread producer([&]() {
        for (int i = 0; i < count; ++i) {
            while (!buffer.try_push(i)) {
                std::this_thread::yield();
            }
        }
    });

    // 消费者线程
    std::thread consumer([&]() {
        int received = 0;
        while (received < count) {
            auto val = buffer.try_pop();
            if (val.has_value()) {
                assert(val.value() == received);
                received++;
            } else {
                std::this_thread::yield();
            }
        }
    });

    producer.join();
    consumer.join();

    assert(buffer.empty());

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试性能
 */
void test_performance() {
    std::cout << "Test performance...\n";

    RingBuffer<int, 1024> buffer;
    const int count = 1000000;

    auto start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < count; ++i) {
        buffer.try_push(i);
        buffer.try_pop();
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);

    std::cout << "  Operations: " << count << "\n";
    std::cout << "  Time: " << duration.count() / 1000000 << " ms\n";
    std::cout << "  Per operation: " << duration.count() / count << " ns\n";
    std::cout << "  PASSED\n";
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== Ring Buffer Tests ===\n";

    test_basic();
    test_full();
    test_multithread();
    test_performance();

    std::cout << "\nAll tests passed!\n";
    return 0;
}
