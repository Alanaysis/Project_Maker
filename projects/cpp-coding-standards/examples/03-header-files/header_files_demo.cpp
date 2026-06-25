/**
 * @file header_files_demo.cpp
 * @brief 头文件规范演示程序
 *
 * 本程序演示 C++ 头文件规范的最佳实践，包括：
 * - 良好头文件示例
 * - 糟糕头文件示例
 * - 头文件对比
 */

#include <iostream>
#include <string>

#include "good_header.h"

/**
 * @brief 打印分隔线
 */
void printSeparator() {
    std::cout << "\n" << std::string(60, '=') << "\n" << std::endl;
}

/**
 * @brief 打印头文件规范总结
 */
void printHeaderSummary() {
    std::cout << "=== C++ 头文件规范总结 ===" << std::endl;

    std::cout << "\n1. 头文件保护:" << std::endl;
    std::cout << "   - 使用 #ifndef / #define / #endif" << std::endl;
    std::cout << "   - 或使用 #pragma once" << std::endl;
    std::cout << "   - 保护名称唯一" << std::endl;

    std::cout << "\n2. #include 顺序:" << std::endl;
    std::cout << "   - 主头文件（对应的 .h 文件）" << std::endl;
    std::cout << "   - C 系统头文件" << std::endl;
    std::cout << "   - C++ 标准库头文件" << std::endl;
    std::cout << "   - 第三方库头文件" << std::endl;
    std::cout << "   - 项目头文件" << std::endl;

    std::cout << "\n3. 前向声明:" << std::endl;
    std::cout << "   - 优先使用前向声明" << std::endl;
    std::cout << "   - 减少头文件依赖" << std::endl;
    std::cout << "   - 加快编译速度" << std::endl;

    std::cout << "\n4. 命名空间:" << std::endl;
    std::cout << "   - 使用命名空间组织代码" << std::endl;
    std::cout << "   - 避免 using namespace" << std::endl;
    std::cout << "   - 命名空间使用 snake_case" << std::endl;

    std::cout << "\n5. 类声明:" << std::endl;
    std::cout << "   - 访问控制说明符明确" << std::endl;
    std::cout << "   - 成员函数声明清晰" << std::endl;
    std::cout << "   - 使用 Doxygen 注释" << std::endl;

    std::cout << "\n6. 函数声明:" << std::endl;
    std::cout << "   - 参数命名清晰" << std::endl;
    std::cout << "   - 返回类型明确" << std::endl;
    std::cout << "   - 使用 const 修饰" << std::endl;

    std::cout << "\n7. 内联函数:" << std::endl;
    std::cout << "   - 简单函数可以内联" << std::endl;
    std::cout << "   - 复杂函数不要内联" << std::endl;
    std::cout << "   - 使用 inline 关键字" << std::endl;
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "C++ 头文件规范演示程序" << std::endl;
    std::cout << "本程序展示良好和糟糕的头文件规范示例" << std::endl;

    printSeparator();

    // 演示良好头文件
    std::cout << "=== 良好头文件规范示例 ===" << std::endl;

    // 使用良好头文件中定义的类
    cpp_standards::UserManager manager(10);
    auto id = manager.addUser("Alice", "alice@example.com");
    std::cout << "添加用户: " << manager.getUserName(id) << std::endl;
    std::cout << "用户邮箱: " << manager.getUserEmail(id) << std::endl;
    std::cout << "用户数量: " << manager.getUserCount() << std::endl;

    // 使用良好头文件中定义的函数
    std::cout << "\n验证邮箱: "
              << (cpp_standards::isValidEmail("test@example.com") ? "有效" : "无效")
              << std::endl;

    std::cout << "格式化用户: "
              << cpp_standards::formatUserInfo("Bob", "bob@example.com")
              << std::endl;

    // 使用内联函数
    std::cout << "用户ID有效: "
              << (cpp_standards::isValidUserId(id) ? "是" : "否")
              << std::endl;

    printSeparator();

    // 打印头文件规范总结
    printHeaderSummary();

    printSeparator();

    std::cout << "演示完成！" << std::endl;
    std::cout << "请参考良好头文件示例，避免使用糟糕头文件方式。" << std::endl;

    return 0;
}
