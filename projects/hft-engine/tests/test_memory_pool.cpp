/**
 * @file test_memory_pool.cpp
 * @brief 内存池测试
 */

#include <iostream>
#include <cassert>
#include <vector>
#include <chrono>

#include "core/memory_pool.h"

using namespace hft;

/**
 * @brief 测试基本分配
 */
void test_basic() {
    std::cout << "Test basic allocation...\n";

    MemoryPool<int> pool;

    // 分配和释放
    int* p1 = pool.allocate();
    *p1 = 42;
    assert(*p1 == 42);

    int* p2 = pool.allocate();
    *p2 = 100;
    assert(*p2 == 100);

    pool.deallocate(p1);
    pool.deallocate(p2);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试构造和析构
 */
void test_construct_destroy() {
    std::cout << "Test construct/destroy...\n";

    struct TestObject {
        int value;
        TestObject(int v) : value(v) {}
        ~TestObject() { value = -1; }
    };

    MemoryPool<TestObject> pool;

    // 构造对象
    TestObject* obj = pool.construct(42);
    assert(obj->value == 42);

    // 销毁对象
    pool.destroy(obj);

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试批量分配
 */
void test_batch() {
    std::cout << "Test batch allocation...\n";

    MemoryPool<int, 64> pool;
    std::vector<int*> ptrs;

    // 批量分配
    for (int i = 0; i < 100; ++i) {
        int* p = pool.allocate();
        *p = i;
        ptrs.push_back(p);
    }

    // 验证值
    for (int i = 0; i < 100; ++i) {
        assert(*ptrs[i] == i);
    }

    // 释放
    for (auto p : ptrs) {
        pool.deallocate(p);
    }

    std::cout << "  PASSED\n";
}

/**
 * @brief 测试性能
 */
void test_performance() {
    std::cout << "Test performance...\n";

    MemoryPool<int> pool;
    const int count = 1000000;

    auto start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < count; ++i) {
        int* p = pool.allocate();
        *p = i;
        pool.deallocate(p);
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
    std::cout << "=== Memory Pool Tests ===\n";

    test_basic();
    test_construct_destroy();
    test_batch();
    test_performance();

    std::cout << "\nAll tests passed!\n";
    return 0;
}
