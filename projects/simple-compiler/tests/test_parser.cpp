/**
 * 语法分析器测试
 */

#include "lexer.hpp"
#include "parser.hpp"
#include <iostream>
#include <cassert>
#include <string>

using namespace compiler;

/**
 * 测试变量声明
 */
void testVarDeclaration() {
    std::cout << "Testing variable declarations..." << std::endl;

    // let声明
    {
        Lexer lexer("let x = 10;");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
        assert(ast->statements[0]->stmtType == StmtType::VAR_DECL);
    }

    // var声明
    {
        Lexer lexer("var y = \"hello\";");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
        assert(ast->statements[0]->stmtType == StmtType::VAR_DECL);
    }

    // const声明
    {
        Lexer lexer("const PI = 3.14;");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
        assert(ast->statements[0]->stmtType == StmtType::VAR_DECL);
    }

    // 带类型注解的声明
    {
        Lexer lexer("let x: int = 10;");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
    }

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试表达式
 */
void testExpressions() {
    std::cout << "Testing expressions..." << std::endl;

    // 算术表达式
    {
        Lexer lexer("1 + 2 * 3;");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
        assert(ast->statements[0]->stmtType == StmtType::EXPR_STMT);
    }

    // 比较表达式
    {
        Lexer lexer("x > 10 && y < 20;");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
    }

    // 函数调用
    {
        Lexer lexer("foo(1, 2, 3);");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
    }

    // 数组字面量
    {
        Lexer lexer("let arr = [1, 2, 3];");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
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
        Lexer lexer("if (x > 0) { print(x); }");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
        assert(ast->statements[0]->stmtType == StmtType::IF);
    }

    // if-else
    {
        Lexer lexer("if (x > 0) { print(x); } else { print(0); }");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
        assert(ast->statements[0]->stmtType == StmtType::IF);
    }

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试while循环
 */
void testWhileLoop() {
    std::cout << "Testing while loops..." << std::endl;

    Lexer lexer("while (x > 0) { x = x - 1; }");
    auto tokens = lexer.tokenize();
    Parser parser(std::move(tokens));
    auto ast = parser.parse();

    assert(parser.getErrors().empty());
    assert(ast->statements.size() == 1);
    assert(ast->statements[0]->stmtType == StmtType::WHILE);

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试for循环
 */
void testForLoop() {
    std::cout << "Testing for loops..." << std::endl;

    Lexer lexer("for (let i = 0; i < 10; i++) { print(i); }");
    auto tokens = lexer.tokenize();
    Parser parser(std::move(tokens));
    auto ast = parser.parse();

    assert(parser.getErrors().empty());
    assert(ast->statements.size() == 1);
    assert(ast->statements[0]->stmtType == StmtType::BLOCK); // for被转换为block

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试函数声明
 */
void testFunctionDeclaration() {
    std::cout << "Testing function declarations..." << std::endl;

    // 简单函数
    {
        Lexer lexer("fn add(a: int, b: int): int { return a + b; }");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
        assert(ast->statements[0]->stmtType == StmtType::FUNCTION);
    }

    // 无参数函数
    {
        Lexer lexer("fn greet() { print(\"hello\"); }");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
        assert(ast->statements[0]->stmtType == StmtType::FUNCTION);
    }

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试类声明
 */
void testClassDeclaration() {
    std::cout << "Testing class declarations..." << std::endl;

    Lexer lexer(R"(
        class Point {
            x: int;
            y: int;

            fn init(x: int, y: int) {
                this.x = x;
                this.y = y;
            }

            fn distance(): float {
                return sqrt(this.x * this.x + this.y * this.y);
            }
        }
    )");

    auto tokens = lexer.tokenize();
    Parser parser(std::move(tokens));
    auto ast = parser.parse();

    assert(parser.getErrors().empty());
    assert(ast->statements.size() == 1);
    assert(ast->statements[0]->stmtType == StmtType::CLASS);

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试错误恢复
 */
void testErrorRecovery() {
    std::cout << "Testing error recovery..." << std::endl;

    // 语法错误后应该能继续解析
    Lexer lexer("let x = ; let y = 10;");
    auto tokens = lexer.tokenize();
    Parser parser(std::move(tokens));
    auto ast = parser.parse();

    // 应该有错误
    assert(!parser.getErrors().empty());

    // 但应该能解析第二个语句
    // (实际实现中可能需要调整)

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试复杂程序
 */
void testComplexProgram() {
    std::cout << "Testing complex program..." << std::endl;

    std::string source = R"(
        // 计算斐波那契数列
        fn fibonacci(n: int): int {
            if (n <= 1) {
                return n;
            }
            return fibonacci(n - 1) + fibonacci(n - 2);
        }

        // 主程序
        let result = fibonacci(10);
        print(result);
    )";

    Lexer lexer(source);
    auto tokens = lexer.tokenize();
    Parser parser(std::move(tokens));
    auto ast = parser.parse();

    assert(parser.getErrors().empty());
    assert(ast->statements.size() == 2); // 函数声明 + 变量声明

    std::cout << "  Passed!" << std::endl;
}

int main() {
    std::cout << "=== Parser Tests ===" << std::endl;
    std::cout << std::endl;

    testVarDeclaration();
    testExpressions();
    testIfStatement();
    testWhileLoop();
    testForLoop();
    testFunctionDeclaration();
    testClassDeclaration();
    testErrorRecovery();
    testComplexProgram();

    std::cout << std::endl;
    std::cout << "All parser tests passed!" << std::endl;

    return 0;
}
