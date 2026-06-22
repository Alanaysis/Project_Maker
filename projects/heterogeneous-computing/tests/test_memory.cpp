/**
 * @file test_memory.cpp
 * @brief 内存管理测试
 */

#include "heterogeneous/memory.h"
#include "heterogeneous/device.h"
#include <iostream>
#include <cassert>
#include <vector>
#include <cstring>

using namespace heterogeneous;

// 测试辅助函数
#define TEST_ASSERT(condition, message) \
    do { \
        if (!(condition)) { \
            std::cerr << "FAIL: " << message << " (" << __FILE__ << ":" << __LINE__ << ")" << std::endl; \
            return false; \
        } \
    } while(0)

#define TEST_PASS(test_name) \
    std::cout << "PASS: " << test_name << std::endl; \
    return true;

// 测试内存分配和释放
bool test_memory_allocation() {
    auto& manager = MemoryManager::instance();
    manager.initialize();

    // 分配主机内存
    void* ptr = manager.allocate(1024, MemoryLocation::Host);
    TEST_ASSERT(ptr != nullptr, "Memory should be allocated");

    // 获取内存块信息
    auto block = manager.get_block(ptr);
    TEST_ASSERT(block != nullptr, "Memory block should exist");
    TEST_ASSERT(block->size == 1024, "Block size should match");
    TEST_ASSERT(block->location == MemoryLocation::Host, "Location should be Host");
    TEST_ASSERT(block->is_allocated, "Block should be allocated");

    // 释放内存
    manager.deallocate(ptr);

    // 验证释放后
    block = manager.get_block(ptr);
    TEST_ASSERT(block == nullptr, "Memory block should not exist after deallocation");

    manager.shutdown();
    TEST_PASS("test_memory_allocation");
}

// 测试内存统计
bool test_memory_statistics() {
    auto& manager = MemoryManager::instance();
    manager.initialize();

    // 分配多个内存块
    void* ptr1 = manager.allocate(1024, MemoryLocation::Host);
    void* ptr2 = manager.allocate(2048, MemoryLocation::Host);
    void* ptr3 = manager.allocate(4096, MemoryLocation::Host);

    // 检查统计
    auto stats = manager.get_usage_stats();
    TEST_ASSERT(stats["total_allocated"] == 1024 + 2048 + 4096, "Total allocated should match");
    TEST_ASSERT(stats["block_count"] == 3, "Block count should match");

    // 释放内存
    manager.deallocate(ptr1);
    manager.deallocate(ptr2);
    manager.deallocate(ptr3);

    // 验证释放后统计
    stats = manager.get_usage_stats();
    TEST_ASSERT(stats["total_allocated"] == 0, "Total allocated should be 0");
    TEST_ASSERT(stats["block_count"] == 0, "Block count should be 0");

    manager.shutdown();
    TEST_PASS("test_memory_statistics");
}

// 测试内存传输
bool test_memory_transfer() {
    auto& manager = MemoryManager::instance();
    manager.initialize();

    // 分配主机内存
    void* src = manager.allocate(1024, MemoryLocation::Host);
    void* dst = manager.allocate(1024, MemoryLocation::Host);

    // 写入源数据
    std::memset(src, 0xAB, 1024);

    // 主机到主机传输
    manager.transfer(src, dst, 1024, MemoryLocation::Host, MemoryLocation::Host);

    // 验证传输结果
    TEST_ASSERT(std::memcmp(src, dst, 1024) == 0, "Data should match after transfer");

    // 释放内存
    manager.deallocate(src);
    manager.deallocate(dst);

    manager.shutdown();
    TEST_PASS("test_memory_transfer");
}

// 测试异步内存传输
bool test_async_memory_transfer() {
    auto& manager = MemoryManager::instance();
    manager.initialize();

    // 分配主机内存
    void* src = manager.allocate(1024, MemoryLocation::Host);
    void* dst = manager.allocate(1024, MemoryLocation::Host);

    // 写入源数据
    std::memset(src, 0xCD, 1024);

    // 异步传输
    auto future = manager.transfer_async(src, dst, 1024,
                                          MemoryLocation::Host, MemoryLocation::Host);

    // 等待完成
    future.wait();

    // 验证传输结果
    TEST_ASSERT(std::memcmp(src, dst, 1024) == 0, "Data should match after async transfer");

    // 释放内存
    manager.deallocate(src);
    manager.deallocate(dst);

    manager.shutdown();
    TEST_PASS("test_async_memory_transfer");
}

// 测试内存池
bool test_memory_pool() {
    auto pool = std::make_unique<MemoryPool>(MemoryLocation::Host, nullptr, 4096);

    // 分配内存
    void* ptr1 = pool->allocate(1024);
    TEST_ASSERT(ptr1 != nullptr, "Memory should be allocated from pool");

    void* ptr2 = pool->allocate(2048);
    TEST_ASSERT(ptr2 != nullptr, "Memory should be allocated from pool");

    // 检查使用率
    double utilization = pool->get_utilization();
    TEST_ASSERT(utilization > 0.0, "Utilization should be positive");

    // 释放内存
    pool->deallocate(ptr1);
    pool->deallocate(ptr2);

    TEST_PASS("test_memory_pool");
}

// 测试托管内存
bool test_managed_memory() {
    auto& manager = MemoryManager::instance();
    manager.initialize();

    // 创建托管内存
    ManagedMemory<float> host_mem(100, MemoryLocation::Host);
    TEST_ASSERT(host_mem.get() != nullptr, "Managed memory should be allocated");
    TEST_ASSERT(host_mem.count() == 100, "Count should match");
    TEST_ASSERT(host_mem.size() == 100 * sizeof(float), "Size should match");

    // 写入数据
    for (size_t i = 0; i < 100; i++) {
        host_mem[i] = static_cast<float>(i);
    }

    // 验证数据
    for (size_t i = 0; i < 100; i++) {
        TEST_ASSERT(host_mem[i] == static_cast<float>(i), "Data should match");
    }

    manager.shutdown();
    TEST_PASS("test_managed_memory");
}

// 测试内存泄漏检测
bool test_memory_leak_detection() {
    auto& manager = MemoryManager::instance();
    manager.initialize();

    // 分配内存但不释放
    void* ptr = manager.allocate(1024, MemoryLocation::Host);

    // 检查泄漏
    size_t leaks = manager.check_leaks();
    TEST_ASSERT(leaks >= 1, "Should detect at least 1 leak");

    // 释放内存
    manager.deallocate(ptr);

    // 再次检查
    leaks = manager.check_leaks();
    TEST_ASSERT(leaks == 0, "Should have no leaks");

    manager.shutdown();
    TEST_PASS("test_memory_leak_detection");
}

// 测试内存对齐
bool test_memory_alignment() {
    auto& manager = MemoryManager::instance();
    manager.initialize();

    // 分配内存
    void* ptr = manager.allocate(1024, MemoryLocation::Host);

    // 检查对齐 (至少 8 字节对齐)
    uintptr_t address = reinterpret_cast<uintptr_t>(ptr);
    TEST_ASSERT(address % 8 == 0, "Memory should be at least 8-byte aligned");

    manager.deallocate(ptr);
    manager.shutdown();
    TEST_PASS("test_memory_alignment");
}

// 测试大量内存分配
bool test_large_allocation() {
    auto& manager = MemoryManager::instance();
    manager.initialize();

    // 分配大量小内存块
    std::vector<void*> ptrs;
    for (int i = 0; i < 1000; i++) {
        void* ptr = manager.allocate(64, MemoryLocation::Host);
        TEST_ASSERT(ptr != nullptr, "Memory should be allocated");
        ptrs.push_back(ptr);
    }

    // 检查统计
    auto stats = manager.get_usage_stats();
    TEST_ASSERT(stats["block_count"] == 1000, "Should have 1000 blocks");

    // 释放所有内存
    for (auto ptr : ptrs) {
        manager.deallocate(ptr);
    }

    // 验证释放后统计
    stats = manager.get_usage_stats();
    TEST_ASSERT(stats["block_count"] == 0, "Should have 0 blocks");

    manager.shutdown();
    TEST_PASS("test_large_allocation");
}

// 测试零大小分配
bool test_zero_size_allocation() {
    auto& manager = MemoryManager::instance();
    manager.initialize();

    // 分配零大小
    void* ptr = manager.allocate(0, MemoryLocation::Host);
    TEST_ASSERT(ptr == nullptr, "Zero size allocation should return nullptr");

    manager.shutdown();
    TEST_PASS("test_zero_size_allocation");
}

// 主函数
int main() {
    std::cout << "=== Memory Manager Tests ===" << std::endl;

    int passed = 0;
    int failed = 0;

    auto run_test = [&](bool (*test)(), const char* name) {
        try {
            if (test()) {
                passed++;
            } else {
                failed++;
            }
        } catch (const std::exception& e) {
            std::cerr << "EXCEPTION in " << name << ": " << e.what() << std::endl;
            failed++;
        }
    };

    run_test(test_memory_allocation, "test_memory_allocation");
    run_test(test_memory_statistics, "test_memory_statistics");
    run_test(test_memory_transfer, "test_memory_transfer");
    run_test(test_async_memory_transfer, "test_async_memory_transfer");
    run_test(test_memory_pool, "test_memory_pool");
    run_test(test_managed_memory, "test_managed_memory");
    run_test(test_memory_leak_detection, "test_memory_leak_detection");
    run_test(test_memory_alignment, "test_memory_alignment");
    run_test(test_large_allocation, "test_large_allocation");
    run_test(test_zero_size_allocation, "test_zero_size_allocation");

    std::cout << "\n=== Results ===" << std::endl;
    std::cout << "Passed: " << passed << std::endl;
    std::cout << "Failed: " << failed << std::endl;
    std::cout << "Total:  " << passed + failed << std::endl;

    return failed > 0 ? 1 : 0;
}
