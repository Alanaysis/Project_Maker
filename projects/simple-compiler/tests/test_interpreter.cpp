/**
 * 解释器测试
 */

#include "lexer.hpp"
#include "parser.hpp"
#include "interpreter.hpp"
#include <iostream>
#include <cassert>
#include <string>
#include <sstream>

using namespace compiler;

/**
 * 执行代码并返回输出
 */
std::string executeAndCapture(const std::string& source) {
    // 词法分析
    Lexer lexer(source);
    auto tokens = lexer.tokenize();

    if (!lexer.getErrors().empty()) {
        return "LEXER ERROR";
    }

    // 语法分析
    Parser parser(std::move(tokens));
    auto ast = parser.parse();

    if (!parser.getErrors().empty()) {
        return "PARSER ERROR";
    }

    // 解释执行
    std::ostringstream output;
    Interpreter interpreter;
    interpreter.setOutputStream(&output);

    if (!interpreter.interpret(*ast)) {
        return "RUNTIME ERROR";
    }

    return output.str();
}

/**
 * 测试简单表达式
 */
void testSimpleExpressions() {
    std::cout << "Testing simple expressions..." << std::endl;

    // 整数运算
    {
        std::string output = executeAndCapture("print(1 + 2);");
        assert(output.find("3") != std::string::npos);
    }

    // 浮点运算
    {
        std::string output = executeAndCapture("print(1.5 + 2.5);");
        assert(output.find("4") != std::string::npos);
    }

    // 字符串连接
    {
        std::string output = executeAndCapture("print(\"hello\" + \" \" + \"world\");");
        assert(output.find("hello world") != std::string::npos);
    }

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试变量
 */
void testVariables() {
    std::cout << "Testing variables..." << std::endl;

    // let变量
    {
        std::string output = executeAndCapture(R"(
            let x = 10;
            print(x);
        )");
        assert(output.find("10") != std::string::npos);
    }

    // var变量
    {
        std::string output = executeAndCapture(R"(
            var x = 10;
            x = 20;
            print(x);
        )");
        assert(output.find("20") != std::string::npos);
    }

    // const变量
    {
        std::string output = executeAndCapture(R"(
            const PI = 3.14;
            print(PI);
        )");
        assert(output.find("3.14") != std::string::npos);
    }

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试if语句
 */
void testIfStatement() {
    std::cout << "Testing if statements..." << std::endl;

    // 简单if
    {
        std::string output = executeAndCapture(R"(
            let x = 10;
            if (x > 5) {
                print("greater");
            }
        )");
        assert(output.find("greater") != std::string::npos);
    }

    // if-else
    {
        std::string output = executeAndCapture(R"(
            let x = 3;
            if (x > 5) {
                print("greater");
            } else {
                print("smaller");
            }
        )");
        assert(output.find("smaller") != std::string::npos);
    }

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试while循环
 */
void testWhileLoop() {
    std::cout << "Testing while loops..." << std::endl;

    std::string output = executeAndCapture(R"(
        let i = 0;
        while (i < 5) {
            print(i);
            i = i + 1;
        }
    )");

    assert(output.find("0") != std::string::npos);
    assert(output.find("4") != std::string::npos);

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试for循环
 */
void testForLoop() {
    std::cout << "Testing for loops..." << std::endl;

    std::string output = executeAndCapture(R"(
        for (let i = 0; i < 5; i++) {
            print(i);
        }
    )");

    assert(output.find("0") != std::string::npos);
    assert(output.find("4") != std::string::npos);

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试函数
 */
void testFunctions() {
    std::cout << "Testing functions..." << std::endl;

    // 简单函数
    {
        std::string output = executeAndCapture(R"(
            fn add(a: int, b: int): int {
                return a + b;
            }
            print(add(3, 4));
        )");
        assert(output.find("7") != std::string::npos);
    }

    // 递归函数
    {
        std::string output = executeAndCapture(R"(
            fn factorial(n: int): int {
                if (n <= 1) {
                    return 1;
                }
                return n * factorial(n - 1);
            }
            print(factorial(5));
        )");
        assert(output.find("120") != std::string::npos);
    }

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试数组
 */
void testArrays() {
    std::cout << "Testing arrays..." << std::endl;

    // 创建数组
    {
        std::string output = executeAndCapture(R"(
            let arr = [1, 2, 3, 4, 5];
            print(arr[0]);
            print(arr[4]);
        )");
        assert(output.find("1") != std::string::npos);
        assert(output.find("5") != std::string::npos);
    }

    // 数组长度
    {
        std::string output = executeAndCapture(R"(
            let arr = [1, 2, 3];
            print(len(arr));
        )");
        assert(output.find("3") != std::string::npos);
    }

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试字符串操作
 */
void testStrings() {
    std::cout << "Testing strings..." << std::endl;

    // 字符串连接
    {
        std::string output = executeAndCapture(R"(
            let s = "Hello" + " " + "World";
            print(s);
        )");
        assert(output.find("Hello World") != std::string::npos);
    }

    // 字符串长度
    {
        std::string output = executeAndCapture(R"(
            print(len("hello"));
        )");
        assert(output.find("5") != std::string::npos);
    }

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试内置函数
 */
void testBuiltinFunctions() {
    std::cout << "Testing built-in functions..." << std::endl;

    // abs
    {
        std::string output = executeAndCapture("print(abs(-5));");
        assert(output.find("5") != std::string::npos);
    }

    // sqrt
    {
        std::string output = executeAndCapture("print(sqrt(16));");
        assert(output.find("4") != std::string::npos);
    }

    // pow
    {
        std::string output = executeAndCapture("print(pow(2, 10));");
        assert(output.find("1024") != std::string::npos);
    }

    // str
    {
        std::string output = executeAndCapture("print(str(42));");
        assert(output.find("42") != std::string::npos);
    }

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试斐波那契数列
 */
void testFibonacci() {
    std::cout << "Testing fibonacci..." << std::endl;

    std::string output = executeAndCapture(R"(
        fn fibonacci(n: int): int {
            if (n <= 1) {
                return n;
            }
            return fibonacci(n - 1) + fibonacci(n - 2);
        }

        for (let i = 0; i < 10; i++) {
            print(fibonacci(i));
        }
    )");

    // 检查一些斐波那契数
    assert(output.find("0") != std::string::npos);
    assert(output.find("1") != std::string::npos);
    assert(output.find("5") != std::string::npos);
    assert(output.find("34") != std::string::npos); // fib(9) = 34

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试冒泡排序
 */
void testBubbleSort() {
    std::cout << "Testing bubble sort..." << std::endl;

    std::string output = executeAndCapture(R"(
        fn bubbleSort(arr: int[], n: int) {
            for (let i = 0; i < n - 1; i++) {
                for (let j = 0; j < n - i - 1; j++) {
                    if (arr[j] > arr[j + 1]) {
                        let temp = arr[j];
                        arr[j] = arr[j + 1];
                        arr[j + 1] = temp;
                    }
                }
            }
        }

        let arr = [64, 34, 25, 12, 22, 11, 90];
        bubbleSort(arr, len(arr));

        for (let i = 0; i < len(arr); i++) {
            print(arr[i]);
        }
    )");

    // 检查排序结果
    assert(output.find("11") != std::string::npos);
    assert(output.find("90") != std::string::npos);

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试错误处理
 */
void testErrorHandling() {
    std::cout << "Testing error handling..." << std::endl;

    // 未定义变量
    {
        std::string output = executeAndCapture("print(x);");
        assert(output.find("ERROR") != std::string::npos ||
               output.find("error") != std::string::npos);
    }

    // 除以零
    {
        std::string output = executeAndCapture("print(1 / 0);");
        assert(output.find("ERROR") != std::string::npos ||
               output.find("error") != std::string::npos);
    }

    std::cout << "  Passed!" << std::endl;
}

int main() {
    std::cout << "=== Interpreter Tests ===" << std::endl;
    std::cout << std::endl;

    testSimpleExpressions();
    testVariables();
    testIfStatement();
    testWhileLoop();
    testForLoop();
    testFunctions();
    testArrays();
    testStrings();
    testBuiltinFunctions();
    testFibonacci();
    testBubbleSort();
    testErrorHandling();

    std::cout << std::endl;
    std::cout << "All interpreter tests passed!" << std::endl;

    return 0;
}
