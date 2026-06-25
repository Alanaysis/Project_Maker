/**
 * 缓存行对齐
 *
 * 缓存行对齐的技术：
 * 1. alignas 指定对齐
 * 2. 填充字节
 * 3. 结构体布局优化
 * 4. 性能影响
 *
 * 编译：g++ -std=c++17 -pthread cache_alignment.cpp -o cache_alignment
 */

#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <atomic>
#include <new>

// 示例1：基本对齐
void basic_alignment() {
    std::cout << "=== 基本对齐 ===" << std::endl;

    // 未对齐
    struct Unaligned {
        char a;
        int b;
        char c;
    };

    // 对齐
    struct Aligned {
        char a;
        char c;
        int b;
    };

    // 强制对齐
    struct ForcedAligned {
        alignas(64) char a;
        alignas(64) int b;
        alignas(64) char c;
    };

    std::cout << "Unaligned 大小: " << sizeof(Unaligned) << " bytes" << std::endl;
    std::cout << "Aligned 大小: " << sizeof(Aligned) << " bytes" << std::endl;
    std::cout << "ForcedAligned 大小: " << sizeof(ForcedAligned) << " bytes" << std::endl;

    std::cout << "\n硬件缓存行大小: " << std::hardware_destructive_interference_size << " bytes" << std::endl;
}

// 示例2：缓存行对齐的原子变量
void cache_aligned_atomics() {
    std::cout << "\n=== 缓存行对齐的原子变量 ===" << std::endl;

    // 未对齐（可能伪共享）
    struct UnalignedAtomics {
        std::atomic<int> x;
        std::atomic<int> y;
    };

    // 对齐（避免伪共享）
    struct AlignedAtomics {
        alignas(64) std::atomic<int> x;
        alignas(64) std::atomic<int> y;
    };

    std::cout << "UnalignedAtomics 大小: " << sizeof(UnalignedAtomics) << " bytes" << std::endl;
    std::cout << "AlignedAtomics 大小: " << sizeof(AlignedAtomics) << " bytes" << std::endl;

    const int iterations = 1000000;

    // 性能测试
    {
        UnalignedAtomics data;
        data.x = 0;
        data.y = 0;

        auto start = std::chrono::high_resolution_clock::now();

        std::thread t1([&]() {
            for (int i = 0; i < iterations; ++i) {
                data.x.fetch_add(1, std::memory_order_relaxed);
            }
        });

        std::thread t2([&]() {
            for (int i = 0; i < iterations; ++i) {
                data.y.fetch_add(1, std::memory_order_relaxed);
            }
        });

        t1.join();
        t2.join();

        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "未对齐: " << time.count() << " ms" << std::endl;
    }

    {
        AlignedAtomics data;
        data.x = 0;
        data.y = 0;

        auto start = std::chrono::high_resolution_clock::now();

        std::thread t1([&]() {
            for (int i = 0; i < iterations; ++i) {
                data.x.fetch_add(1, std::memory_order_relaxed);
            }
        });

        std::thread t2([&]() {
            for (int i = 0; i < iterations; ++i) {
                data.y.fetch_add(1, std::memory_order_relaxed);
            }
        });

        t1.join();
        t2.join();

        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "对齐后: " << time.count() << " ms" << std::endl;
    }
}

// 示例3：动态分配的对齐
void dynamic_alignment() {
    std::cout << "\n=== 动态分配的对齐 ===" << std::endl;

    // 使用 aligned_alloc
    void* ptr = std::aligned_alloc(64, 64);
    std::cout << "对齐分配地址: " << ptr << std::endl;
    std::cout << "是否 64 字节对齐: "
              << (reinterpret_cast<uintptr_t>(ptr) % 64 == 0 ? "是" : "否") << std::endl;
    std::free(ptr);

    // 使用 aligned_new (C++17)
    struct alignas(64) AlignedStruct {
        int value;
    };

    AlignedStruct* obj = new AlignedStruct{42};
    std::cout << "aligned_new 地址: " << obj << std::endl;
    std::cout << "是否 64 字节对齐: "
              << (reinterpret_cast<uintptr_t>(obj) % 64 == 0 ? "是" : "否") << std::endl;
    delete obj;
}

int main() {
    std::cout << "C++ 性能优化：缓存行对齐" << std::endl;
    std::cout << "=========================\n" << std::endl;

    basic_alignment();
    cache_aligned_atomics();
    dynamic_alignment();

    return 0;
}
