/**
 * 内存位置 (Memory Location)
 *
 * 内存位置是 C++ 内存模型的基本概念：
 * 1. 一个标量类型（算术类型、指针类型、枚举类型）的对象占据一个内存位置
 * 2. 相邻的位域成员属于同一个内存位置
 * 3. 不同的内存位置可以并行修改（线程安全）
 * 4. 同一个内存位置的并发修改需要同步
 *
 * 编译：g++ -std=c++17 -pthread memory_location.cpp -o memory_location
 */

#include <iostream>
#include <atomic>
#include <thread>
#include <vector>
#include <cstring>

// 示例1：基本内存位置
void basic_memory_location() {
    std::cout << "=== 基本内存位置 ===" << std::endl;

    int a = 10;
    int b = 20;
    double c = 3.14;

    std::cout << "a 的地址: " << &a << std::endl;
    std::cout << "b 的地址: " << &b << std::endl;
    std::cout << "c 的地址: " << &c << std::endl;

    // 每个变量占据独立的内存位置
    // 可以并行修改 a 和 b（不同的内存位置）
    std::cout << "a 和 b 是不同的内存位置，可以并行修改" << std::endl;
}

// 示例2：位域和内存位置
struct BitFields {
    unsigned int flag1 : 1;  // 位域成员
    unsigned int flag2 : 1;  // 与 flag1 属于同一个内存位置
    unsigned int flag3 : 1;  // 与 flag1, flag2 属于同一个内存位置
    unsigned int : 0;        // 未命名的零宽度位域强制对齐
    unsigned int flag4 : 1;  // 属于新的内存位置
};

void bitfield_memory_location() {
    std::cout << "\n=== 位域和内存位置 ===" << std::endl;

    BitFields bits = {1, 0, 1, 0};
    std::cout << "sizeof(BitFields): " << sizeof(BitFields) << " bytes" << std::endl;
    std::cout << "flag1: " << bits.flag1 << std::endl;
    std::cout << "flag2: " << bits.flag2 << std::endl;
    std::cout << "flag3: " << bits.flag3 << std::endl;
    std::cout << "flag4: " << bits.flag4 << std::endl;

    std::cout << "flag1, flag2, flag3 属于同一个内存位置" << std::endl;
    std::cout << "flag4 属于不同的内存位置（因为零宽度位域）" << std::endl;
    std::cout << "同一个内存位置的位域不能被不同线程并行修改" << std::endl;
}

// 示例3：数组元素的内存位置
void array_memory_location() {
    std::cout << "\n=== 数组元素的内存位置 ===" << std::endl;

    int arr[5] = {1, 2, 3, 4, 5};

    for (int i = 0; i < 5; ++i) {
        std::cout << "arr[" << i << "] 地址: " << &arr[i]
                  << ", 值: " << arr[i] << std::endl;
    }

    std::cout << "\n每个数组元素是独立的内存位置" << std::endl;
    std::cout << "不同线程可以安全地修改不同的数组元素" << std::endl;
}

// 示例4：并发修改不同内存位置
void concurrent_different_locations() {
    std::cout << "\n=== 并发修改不同内存位置 ===" << std::endl;

    int counter1 = 0;
    int counter2 = 0;

    // 两个线程修改不同的变量（不同的内存位置）
    // 这是线程安全的
    std::thread t1([&counter1]() {
        for (int i = 0; i < 100000; ++i) {
            counter1++;
        }
    });

    std::thread t2([&counter2]() {
        for (int i = 0; i < 100000; ++i) {
            counter2++;
        }
    });

    t1.join();
    t2.join();

    std::cout << "counter1: " << counter1 << std::endl;
    std::cout << "counter2: " << counter2 << std::endl;
    std::cout << "两个线程修改不同的内存位置，结果总是正确的" << std::endl;
}

// 示例5：并发修改同一内存位置（数据竞争）
void concurrent_same_location() {
    std::cout << "\n=== 并发修改同一内存位置（数据竞争） ===" << std::endl;

    int counter = 0;

    // 两个线程修改同一个变量（同一个内存位置）
    // 这是数据竞争，结果未定义
    std::thread t1([&counter]() {
        for (int i = 0; i < 100000; ++i) {
            counter++;  // 数据竞争！
        }
    });

    std::thread t2([&counter]() {
        for (int i = 0; i < 100000; ++i) {
            counter++;  // 数据竞争！
        }
    });

    t1.join();
    t2.join();

    std::cout << "counter (有数据竞争): " << counter << std::endl;
    std::cout << "期望值: 200000" << std::endl;
    std::cout << "实际值可能小于期望值，因为存在数据竞争" << std::endl;
}

// 示例6：使用原子操作避免数据竞争
void concurrent_atomic() {
    std::cout << "\n=== 使用原子操作避免数据竞争 ===" << std::endl;

    std::atomic<int> counter{0};

    // 两个线程修改同一个原子变量
    // 原子操作保证线程安全
    std::thread t1([&counter]() {
        for (int i = 0; i < 100000; ++i) {
            counter.fetch_add(1, std::memory_order_relaxed);
        }
    });

    std::thread t2([&counter]() {
        for (int i = 0; i < 100000; ++i) {
            counter.fetch_add(1, std::memory_order_relaxed);
        }
    });

    t1.join();
    t2.join();

    std::cout << "counter (原子操作): " << counter.load() << std::endl;
    std::cout << "期望值: 200000" << std::endl;
    std::cout << "使用原子操作，结果总是正确的" << std::endl;
}

// 示例7：内存位置和对齐
void memory_alignment() {
    std::cout << "\n=== 内存位置和对齐 ===" << std::endl;

    // 基本类型的对齐要求
    std::cout << "char 对齐: " << alignof(char) << " bytes" << std::endl;
    std::cout << "short 对齐: " << alignof(short) << " bytes" << std::endl;
    std::cout << "int 对齐: " << alignof(int) << " bytes" << std::endl;
    std::cout << "long 对齐: " << alignof(long) << " bytes" << std::endl;
    std::cout << "long long 对齐: " << alignof(long long) << " bytes" << std::endl;
    std::cout << "float 对齐: " << alignof(float) << " bytes" << std::endl;
    std::cout << "double 对齐: " << alignof(double) << " bytes" << std::endl;
    std::cout << "void* 对齐: " << alignof(void*) << " bytes" << std::endl;

    // 原子类型的对齐
    std::cout << "\natomic<int> 对齐: " << alignof(std::atomic<int>) << " bytes" << std::endl;
    std::cout << "atomic<long long> 对齐: " << alignof(std::atomic<long long>) << " bytes" << std::endl;

    // 结构体对齐
    struct AlignTest1 {
        char a;     // 1 byte
        int b;      // 4 bytes
        char c;     // 1 byte
    };

    struct AlignTest2 {
        int b;      // 4 bytes
        char a;     // 1 byte
        char c;     // 1 byte
    };

    std::cout << "\nAlignTest1 大小: " << sizeof(AlignTest1) << " bytes" << std::endl;
    std::cout << "AlignTest2 大小: " << sizeof(AlignTest2) << " bytes" << std::endl;
    std::cout << "成员顺序影响结构体大小（内存对齐）" << std::endl;
}

int main() {
    std::cout << "C++ 内存模型：内存位置 (Memory Location)" << std::endl;
    std::cout << "==========================================\n" << std::endl;

    basic_memory_location();
    bitfield_memory_location();
    array_memory_location();
    concurrent_different_locations();
    concurrent_same_location();
    concurrent_atomic();
    memory_alignment();

    return 0;
}
