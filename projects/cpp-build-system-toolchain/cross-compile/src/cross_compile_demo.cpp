#include <iostream>
#include "mylib.h"

/**
 * @file cross_compile_demo.cpp
 * @brief 交叉编译示例
 *
 * 演示如何使用 CMake 进行交叉编译。
 * 此代码可以在 x86 主机上编译，在 ARM 目标上运行。
 */

int main() {
    std::cout << "=== 交叉编译示例 ===" << std::endl;
    std::cout << std::endl;

    // 显示目标平台信息
    std::cout << "目标平台信息:" << std::endl;
#if defined(__aarch64__)
    std::cout << "  架构: AArch64 (ARM64)" << std::endl;
#elif defined(__arm__)
    std::cout << "  架构: ARM (32-bit)" << std::endl;
#elif defined(__x86_64__)
    std::cout << "  架构: x86_64" << std::endl;
#elif defined(__i386__)
    std::cout << "  架构: x86 (32-bit)" << std::endl;
#else
    std::cout << "  架构: 未知" << std::endl;
#endif

    std::cout << std::endl;

    // 使用库函数
    std::cout << "库函数测试:" << std::endl;
    std::cout << "  add(3, 4) = " << mylib::add(3, 4) << std::endl;
    std::cout << "  multiply(5, 6) = " << mylib::multiply(5, 6) << std::endl;

    std::cout << std::endl;
    std::cout << "交叉编译说明:" << std::endl;
    std::cout << "  1. 使用工具链文件指定交叉编译器" << std::endl;
    std::cout << "  2. 设置 CMAKE_SYSTEM_NAME 为目标系统" << std::endl;
    std::cout << "  3. 配置查找路径以使用目标系统的库" << std::endl;
    std::cout << "  4. 使用 QEMU 等工具在主机上测试" << std::endl;

    return 0;
}
