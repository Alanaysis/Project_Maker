/**
 * @file naming_demo.cpp
 * @brief 命名规范演示程序
 *
 * 本程序演示 C++ 命名规范的最佳实践，包括：
 * - 良好命名示例
 * - 糟糕命名示例
 * - 命名对比
 */

#include <iostream>
#include <string>

// 声明外部函数
extern void demonstrateGoodNaming();
extern void demonstrateBadNaming();

/**
 * @brief 打印分隔线
 */
void printSeparator() {
    std::cout << "\n" << std::string(60, '=') << "\n" << std::endl;
}

/**
 * @brief 打印命名规范总结
 */
void printNamingSummary() {
    std::cout << "=== C++ 命名规范总结 ===" << std::endl;

    std::cout << "\n1. 变量命名:" << std::endl;
    std::cout << "   - 使用 camelCase: userName, accountBalance" << std::endl;
    std::cout << "   - 或使用 snake_case: user_name, account_balance" << std::endl;
    std::cout << "   - 避免: a, b, c, temp, data, val" << std::endl;

    std::cout << "\n2. 函数命名:" << std::endl;
    std::cout << "   - 使用 camelCase: calculateTotal, isValidEmail" << std::endl;
    std::cout << "   - 避免: process, handle, doSomething, calc" << std::endl;

    std::cout << "\n3. 类命名:" << std::endl;
    std::cout << "   - 使用 PascalCase: UserManager, DatabaseConnection" << std::endl;
    std::cout << "   - 避免: Manager, Handler, Processor, Data" << std::endl;

    std::cout << "\n4. 常量命名:" << std::endl;
    std::cout << "   - 使用 k + PascalCase: kMaxRetryCount, kDefaultBufferSize" << std::endl;
    std::cout << "   - 避免: MAX, N, PI, cnt" << std::endl;

    std::cout << "\n5. 枚举命名:" << std::endl;
    std::cout << "   - 使用 k + PascalCase: kActive, kInactive" << std::endl;
    std::cout << "   - 避免: ACTIVE, INACTIVE" << std::endl;

    std::cout << "\n6. 命名空间命名:" << std::endl;
    std::cout << "   - 使用 snake_case: user_utils, string_utils" << std::endl;
    std::cout << "   - 避免: UserUtils, stringutils, _internal" << std::endl;

    std::cout << "\n7. 宏命名:" << std::endl;
    std::cout << "   - 使用 UPPER_CASE: MAX_BUFFER_SIZE, DEBUG_MODE" << std::endl;
    std::cout << "   - 避免: 使用宏，优先使用 constexpr" << std::endl;
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "C++ 命名规范演示程序" << std::endl;
    std::cout << "本程序展示良好和糟糕的命名规范示例" << std::endl;

    printSeparator();

    // 演示良好命名
    demonstrateGoodNaming();

    printSeparator();

    // 演示糟糕命名
    demonstrateBadNaming();

    printSeparator();

    // 打印命名规范总结
    printNamingSummary();

    printSeparator();

    std::cout << "演示完成！" << std::endl;
    std::cout << "请参考良好命名示例，避免使用糟糕命名方式。" << std::endl;

    return 0;
}
