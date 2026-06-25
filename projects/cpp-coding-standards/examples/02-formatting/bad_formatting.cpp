/**
 * @file bad_formatting.cpp
 * @brief 糟糕代码格式示例
 *
 * 本文件展示不符合 C++ 代码格式规范的糟糕代码示例。
 * 这些代码展示了常见的格式错误和反模式。
 *
 * 注意：这些代码仅用于教学目的，实际项目中应避免使用。
 */

#include <iostream>
#include <string>
#include <vector>
#include <algorithm>

// ============================================================================
// 糟糕的缩进风格 - 使用不一致的缩进
// ============================================================================

/**
 * @brief 糟糕的缩进风格示例
 *
 * 使用混合的缩进风格（空格和制表符混合）
 */
class BadIndentation {
public:
    BadIndentation() {
        // 糟糕：混合使用空格和制表符
        int x = 1;
        	int y = 2;  // 使用制表符
          int z = 3;  // 使用不同数量的空格

        // 糟糕：缩进不一致
        if (x > 0) {
        std::cout << "x is positive" << std::endl;
            std::cout << "x is positive" << std::endl;
        }

        // 糟糕：case 语句缩进不正确
        switch (x) {
        case 1:
        std::cout << "one" << std::endl;
        break;
            case 2:
            std::cout << "two" << std::endl;
            break;
        default:
            std::cout << "other" << std::endl;
        }
    }
};

// ============================================================================
// 糟糕的大括号风格 - 使用不一致的大括号风格
// ============================================================================

/**
 * @brief 糟糕的大括号风格示例
 *
 * 使用混合的大括号风格
 */
class BadBraces {
public:
    BadBraces()
    {  // Allman 风格
        int x = 1;
        if (x > 0)
        {  // Allman 风格
            std::cout << "positive" << std::endl;
        }
    }

    void method1() {  // K&R 风格
        int x = 1;
        if (x > 0) {  // K&R 风格
            std::cout << "positive" << std::endl;
        }
    }

    void method2()
    {  // Allman 风格
        int x = 1;
        if (x > 0)
        {  // Allman 风格
            std::cout << "positive" << std::endl;
        }
    }
};

// ============================================================================
// 糟糕的行长度 - 超过 80 列限制
// ============================================================================

/**
 * @brief 糟糕的行长度示例
 *
 * 使用超过 80 列的行长度
 */
class BadLineLength {
public:
    void longLine() {
        // 糟糕：行长度超过 80 列
        std::cout << "This is a very long line that exceeds the 80 column limit and should be split into multiple lines for better readability" << std::endl;

        // 糟糕：函数调用过长
        int result = calculateSomethingVeryLongWithMultipleParameters(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

        // 糟糕：条件表达式过长
        if (condition1 && condition2 && condition3 && condition4 && condition5 && condition6) {
            std::cout << "condition met" << std::endl;
        }
    }

private:
    int calculateSomethingVeryLongWithMultipleParameters(int a, int b, int c, int d, int e, int f, int g, int h, int i, int j) {
        return a + b + c + d + e + f + g + h + i + j;
    }

    bool condition1 = true;
    bool condition2 = true;
    bool condition3 = true;
    bool condition4 = true;
    bool condition5 = true;
    bool condition6 = true;
};

// ============================================================================
// 糟糕的空格使用 - 缺少或多余的空格
// ============================================================================

/**
 * @brief 糟糕的空格使用示例
 *
 * 使用不正确的空格
 */
class BadSpacing {
public:
    void badSpacing() {
        // 糟糕：运算符周围缺少空格
        int a=1+2*3;
        int b=4/2-1;

        // 糟顿：逗号后缺少空格
        std::vector<int> v={1,2,3,4,5};

        // 糟糕：括号内有多余空格
        int c = ( a + b );

        // 糟糕：类型转换后缺少空格
        int d = (int)3.14;

        // 糟糕：指针声明不一致
        int* p1;
        int *p2;
        int*p3;

        // 糟糕：引用声明不一致
        int& r1 = a;
        int &r2 = a;
        int&r3 = a;
    }
};

// ============================================================================
// 糟糕的空行使用 - 缺少或多余的空行
// ============================================================================

/**
 * @brief 糟糕的空行使用示例
 *
 * 使用不合理的空行
 */
class BadEmptyLines {
public:
    void method1() {
        int x = 1;



        // 糟糕：多余的空行
        int y = 2;




        int z = 3;
    }

    void method2() {
        // 糟糕：函数之间没有空行
        int a = 1;
        int b = 2;
        int c = 3;
        int d = 4;
        int e = 5;
        int f = 6;
        int g = 7;
        int h = 8;
        int i = 9;
        int j = 10;
    }
};

// ============================================================================
// 糟糕的注释格式 - 不一致的注释风格
// ============================================================================

/**
 * @brief 糟糕的注释格式示例
 *
 * 使用不一致的注释风格
 */
class BadComments {
public:
    //糟糕：注释符号后缺少空格
    void method1() {
        int x = 1; //糟糕：行尾注释格式不正确
        int y = 2;
    }

    /* 糟糕：使用 C 风格注释 */
    void method2() {
        int x = 1;
        /* 多行
           C 风格
           注释 */
        int y = 2;
    }

    // 糟糕：注释内容不清晰
    void method3() {
        int x = 1; // x
        int y = 2; // y
        int z = 3; // z
    }
};

// ============================================================================
// 演示函数
// ============================================================================

/**
 * @brief 演示糟糕代码格式
 *
 * 注意：这些代码仅用于教学目的，实际项目中应避免使用。
 */
void demonstrateBadFormatting() {
    std::cout << "=== 糟糕代码格式示例 ===" << std::endl;
    std::cout << "注意：这些代码仅用于教学目的，实际项目中应避免使用。" << std::endl;

    // 糟糕的缩进
    std::cout << "\n1. 糟糕的缩进风格:" << std::endl;
    BadIndentation bad_indent;

    // 糟糕的大括号
    std::cout << "\n2. 糟糕的大括号风格:" << std::endl;
    BadBraces bad_braces;

    // 糟糕的空格
    std::cout << "\n3. 糟糕的空格使用:" << std::endl;
    BadSpacing bad_spacing;
    bad_spacing.badSpacing();

    // 糟糕的空行
    std::cout << "\n4. 糟糕的空行使用:" << std::endl;
    BadEmptyLines bad_lines;
    bad_lines.method1();
    bad_lines.method2();

    // 糟糕的注释
    std::cout << "\n5. 糟糕的注释格式:" << std::endl;
    BadComments bad_comments;
    bad_comments.method1();
    bad_comments.method2();
    bad_comments.method3();
}
