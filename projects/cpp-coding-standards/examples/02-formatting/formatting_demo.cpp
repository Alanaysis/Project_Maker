/**
 * @file formatting_demo.cpp
 * @brief 代码格式演示程序
 *
 * 本程序演示 C++ 代码格式规范的最佳实践，包括：
 * - 良好格式示例
 * - 糟糕格式示例
 * - 格式对比
 */

#include <iostream>
#include <string>

// 声明外部函数
extern void demonstrateGoodFormatting();
extern void demonstrateBadFormatting();

/**
 * @brief 打印分隔线
 */
void printSeparator() {
    std::cout << "\n" << std::string(60, '=') << "\n" << std::endl;
}

/**
 * @brief 打印格式规范总结
 */
void printFormattingSummary() {
    std::cout << "=== C++ 代码格式规范总结 ===" << std::endl;

    std::cout << "\n1. 缩进风格:" << std::endl;
    std::cout << "   - 使用 2 空格缩进" << std::endl;
    std::cout << "   - 不要使用制表符" << std::endl;
    std::cout << "   - 保持缩进一致" << std::endl;

    std::cout << "\n2. 大括号风格:" << std::endl;
    std::cout << "   - 使用 K&R 风格" << std::endl;
    std::cout << "   - 左大括号不换行" << std::endl;
    std::cout << "   - 右大括号单独一行" << std::endl;

    std::cout << "\n3. 行长度限制:" << std::endl;
    std::cout << "   - 限制 80 列" << std::endl;
    std::cout << "   - 长行需要换行" << std::endl;
    std::cout << "   - 换行时缩进 4 空格" << std::endl;

    std::cout << "\n4. 空格使用:" << std::endl;
    std::cout << "   - 运算符周围使用空格" << std::endl;
    std::cout << "   - 逗号后使用空格" << std::endl;
    std::cout << "   - 括号内不使用空格" << std::endl;

    std::cout << "\n5. 空行使用:" << std::endl;
    std::cout << "   - 函数之间使用空行" << std::endl;
    std::cout << "   - 逻辑块之间使用空行" << std::endl;
    std::cout << "   - 不要使用多余空行" << std::endl;

    std::cout << "\n6. 注释格式:" << std::endl;
    std::cout << "   - 使用 // 注释" << std::endl;
    std::cout << "   - 注释符号后使用空格" << std::endl;
    std::cout << "   - 注释内容清晰" << std::endl;
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "C++ 代码格式演示程序" << std::endl;
    std::cout << "本程序展示良好和糟糕的代码格式示例" << std::endl;

    printSeparator();

    // 演示良好格式
    demonstrateGoodFormatting();

    printSeparator();

    // 演示糟糕格式
    demonstrateBadFormatting();

    printSeparator();

    // 打印格式规范总结
    printFormattingSummary();

    printSeparator();

    std::cout << "演示完成！" << std::endl;
    std::cout << "请参考良好格式示例，避免使用糟糕格式。" << std::endl;
    std::cout << "建议使用 Clang-Format 工具自动格式化代码。" << std::endl;

    return 0;
}
