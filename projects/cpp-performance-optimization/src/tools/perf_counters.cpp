/**
 * @file perf_counters.cpp
 * @brief 性能计数器使用说明
 */

#include <iostream>
#include <iomanip>

void printPerfInfo()
{
    std::cout << "=== Linux perf 使用说明 ===\n\n";
    std::cout << "1. 基本统计: perf stat ./program\n";
    std::cout << "2. 缓存分析: perf stat -e cache-misses,cache-references ./program\n";
    std::cout << "3. 分支预测: perf stat -e branch-misses,branches ./program\n";
    std::cout << "4. 指令计数: perf stat -e instructions,cycles ./program\n";
    std::cout << "5. 记录报告: perf record -g ./program && perf report\n";
    std::cout << "6. 缓存行:   perf c2c record ./program\n";
    std::cout << "7. 火焰图:   perf script | flamegraph.pl > flame.svg\n";
}

void printValgrindInfo()
{
    std::cout << "\n=== Valgrind 使用说明 ===\n\n";
    std::cout << "1. 缓存分析: valgrind --tool=cachegrind ./program\n";
    std::cout << "2. 调用图:   valgrind --tool=callgrind ./program\n";
    std::cout << "3. 内存错误: valgrind --leak-check=full ./program\n";
    std::cout << "4. 线程错误: valgrind --tool=helgrind ./program\n";
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  性能分析工具\n";
    std::cout << "========================================\n\n";
    printPerfInfo();
    printValgrindInfo();
    return 0;
}
