/**
 * @file class_design_demo.cpp
 * @brief 类设计规范演示程序
 *
 * 本程序演示 C++ 类设计规范的最佳实践，包括：
 * - 良好类设计示例
 * - 糟糕类设计示例
 * - 类设计对比
 */

#include <iostream>
#include <string>

// 声明外部函数
extern void demonstrateGoodClassDesign();
extern void demonstrateBadClassDesign();

/**
 * @brief 打印分隔线
 */
void printSeparator() {
    std::cout << "\n" << std::string(60, '=') << "\n" << std::endl;
}

/**
 * @brief 打印类设计规范总结
 */
void printClassDesignSummary() {
    std::cout << "=== C++ 类设计规范总结 ===" << std::endl;

    std::cout << "\n1. 成员顺序:" << std::endl;
    std::cout << "   - 类型别名" << std::endl;
    std::cout << "   - 构造函数和析构函数" << std::endl;
    std::cout << "   - 赋值运算符" << std::endl;
    std::cout << "   - 公共接口" << std::endl;
    std::cout << "   - 运算符重载" << std::endl;
    std::cout << "   - 友元函数" << std::endl;
    std::cout << "   - 私有成员" << std::endl;

    std::cout << "\n2. 访问控制:" << std::endl;
    std::cout << "   - public: 公共接口" << std::endl;
    std::cout << "   - protected: 受保护成员" << std::endl;
    std::cout << "   - private: 私有成员" << std::endl;
    std::cout << "   - 明确使用访问控制说明符" << std::endl;

    std::cout << "\n3. 构造函数设计:" << std::endl;
    std::cout << "   - 默认构造函数" << std::endl;
    std::cout << "   - 参数化构造函数" << std::endl;
    std::cout << "   - 拷贝构造函数" << std::endl;
    std::cout << "   - 移动构造函数" << std::endl;
    std::cout << "   - 使用 explicit 防止隐式转换" << std::endl;

    std::cout << "\n4. 析构函数设计:" << std::endl;
    std::cout << "   - 虚析构函数（基类）" << std::endl;
    std::cout << "   - 资源释放" << std::endl;
    std::cout << "   - 异常安全" << std::endl;

    std::cout << "\n5. 运算符重载:" << std::endl;
    std::cout << "   - 返回类型正确" << std::endl;
    std::cout << "   - const 修饰正确" << std::endl;
    std::cout << "   - 语义一致" << std::endl;
    std::cout << "   - 友元函数用于对称运算" << std::endl;

    std::cout << "\n6. 友元使用:" << std::endl;
    std::cout << "   - 谨慎使用" << std::endl;
    std::cout << "   - 最小化友元数量" << std::endl;
    std::cout << "   - 用于运算符重载" << std::endl;
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "C++ 类设计规范演示程序" << std::endl;
    std::cout << "本程序展示良好和糟糕的类设计规范示例" << std::endl;

    printSeparator();

    // 演示良好类设计
    demonstrateGoodClassDesign();

    printSeparator();

    // 演示糟糕类设计
    demonstrateBadClassDesign();

    printSeparator();

    // 打印类设计规范总结
    printClassDesignSummary();

    printSeparator();

    std::cout << "演示完成！" << std::endl;
    std::cout << "请参考良好类设计示例，避免使用糟糕类设计方式。" << std::endl;

    return 0;
}
