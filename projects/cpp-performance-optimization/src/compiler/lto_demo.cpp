/**
 * @file lto_demo.cpp
 * @brief 链接时优化 (LTO) 演示
 *
 * 本文件演示 LTO 的概念和效果。
 * LTO 在链接阶段进行跨模块优化。
 * 编译时使用 -flto 选项启用。
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>

class Timer
{
public:
    using Clock = std::chrono::high_resolution_clock;
    Timer() : start_(Clock::now()) {}
    void reset() { start_ = Clock::now(); }
    double elapsedMs() const {
        return std::chrono::duration_cast<std::chrono::nanoseconds>(
            Clock::now() - start_).count() / 1e6;
    }
private:
    Clock::time_point start_;
};

// 模拟跨模块调用
namespace module_a {

inline int compute(int x)
{
    return x * x + 2 * x + 1;
}

int process(const std::vector<int>& data)
{
    int sum = 0;
    for (auto v : data) {
        sum += compute(v);
    }
    return sum;
}

} // namespace module_a

namespace module_b {

int aggregate(const std::vector<int>& data)
{
    int result = 0;
    for (size_t i = 0; i < data.size(); ++i) {
        result += module_a::compute(data[i]);
    }
    return result;
}

} // namespace module_b

/**
 * @brief LTO 的主要优势
 *
 * 1. 跨模块内联: 可以内联其他编译单元的函数
 * 2. 全程序优化: 编译器可以看到整个程序
 * 3. 死代码消除: 移除未使用的代码
 * 4. 常量传播: 跨模块传播常量
 */
void demonstrateLTOConcepts()
{
    std::cout << "=== LTO 概念演示 ===\n\n";

    const size_t N = 10000000;
    std::vector<int> data(N);
    for (size_t i = 0; i < N; ++i) {
        data[i] = static_cast<int>(i);
    }

    constexpr size_t ITERS = 50;

    // 模拟 LTO 优化的场景
    Timer timer;
    volatile int result1 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        result1 = module_a::process(data);
    }
    double time1 = timer.elapsedMs();

    timer.reset();
    volatile int result2 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        result2 = module_b::aggregate(data);
    }
    double time2 = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "module_a::process:   " << time1 << " ms\n";
    std::cout << "module_b::aggregate: " << time2 << " ms\n";
    (void)result1; (void)result2;
}

/**
 * @brief LTO 编译选项说明
 */
void printLTOInfo()
{
    std::cout << "=== LTO 编译选项 ===\n\n";

    std::cout << "GCC LTO:\n";
    std::cout << "  编译: g++ -O3 -flto -c file.cpp\n";
    std::cout << "  链接: g++ -O3 -flto -o binary file.o\n\n";

    std::cout << "Clang LTO:\n";
    std::cout << "  Full LTO: clang++ -O3 -flto -o binary file.cpp\n";
    std::cout << "  Thin LTO: clang++ -O3 -flto=thin -o binary file.cpp\n\n";

    std::cout << "CMake LTO:\n";
    std::cout << "  set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)\n";
    std::cout << "  或: cmake -DENABLE_LTO=ON ..\n\n";

    std::cout << "LTO 优缺点:\n";
    std::cout << "  优点:\n";
    std::cout << "    - 跨模块内联\n";
    std::cout << "    - 全程序优化\n";
    std::cout << "    - 死代码消除\n";
    std::cout << "    - 通常提升 5-15% 性能\n";
    std::cout << "  缺点:\n";
    std::cout << "    - 编译时间增加\n";
    std::cout << "    - 内存使用增加\n";
    std::cout << "    - 调试困难\n";
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  链接时优化 (LTO)\n";
    std::cout << "========================================\n\n";

    std::cout << "说明: LTO (Link-Time Optimization) 在链接阶段\n";
    std::cout << "进行跨模块优化，可以跨编译单元内联函数。\n\n";

    printLTOInfo();
    demonstrateLTOConcepts();

    std::cout << "\n========================================\n";
    std::cout << "  总结\n";
    std::cout << "========================================\n";
    std::cout << "1. LTO 在链接阶段进行优化\n";
    std::cout << "2. 可以跨模块内联\n";
    std::cout << "3. 通常提升 5-15% 性能\n";
    std::cout << "4. 编译时间会增加\n";

    return 0;
}
