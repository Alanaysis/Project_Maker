/**
 * 所有测试的主入口
 */

#include "lexer.hpp"
#include "parser.hpp"
#include "interpreter.hpp"
#include <iostream>
#include <cassert>
#include <string>
#include <sstream>

using namespace compiler;

// ==================== 词法分析器测试 ====================

void testLexerNumbers() {
    std::cout << "Testing lexer numbers..." << std::endl;

    Lexer lexer("42 3.14 100 0.5");
    auto tokens = lexer.tokenize();

    assert(tokens.size() >= 5);
    assert(tokens[0].type == TokenType::INTEGER);
    assert(tokens[1].type == TokenType::FLOAT);
    assert(tokens[2].type == TokenType::INTEGER);
    assert(tokens[3].type == TokenType::FLOAT);

    std::cout << "  Passed!" << std::endl;
}

void testLexerKeywords() {
    std::cout << "Testing lexer keywords..." << std::endl;

    Lexer lexer("let var const if else while for fn return class");
    auto tokens = lexer.tokenize();

    assert(tokens.size() >= 11);
    assert(tokens[0].type == TokenType::LET);
    assert(tokens[1].type == TokenType::VAR);
    assert(tokens[2].type == TokenType::CONST);
    assert(tokens[3].type == TokenType::IF);
    assert(tokens[4].type == TokenType::ELSE);
    assert(tokens[5].type == TokenType::WHILE);
    assert(tokens[6].type == TokenType::FOR);
    assert(tokens[7].type == TokenType::FUNCTION);
    assert(tokens[8].type == TokenType::RETURN);
    assert(tokens[9].type == TokenType::CLASS);

    std::cout << "  Passed!" << std::endl;
}

void testLexerOperators() {
    std::cout << "Testing lexer operators..." << std::endl;

    Lexer lexer("+ - * / = == != < <= > >= && || !");
    auto tokens = lexer.tokenize();

    assert(tokens[0].type == TokenType::PLUS);
    assert(tokens[1].type == TokenType::MINUS);
    assert(tokens[2].type == TokenType::MULTIPLY);
    assert(tokens[3].type == TokenType::DIVIDE);
    assert(tokens[4].type == TokenType::ASSIGN);
    assert(tokens[5].type == TokenType::EQUAL);
    assert(tokens[6].type == TokenType::NOT_EQUAL);
    assert(tokens[7].type == TokenType::LESS);
    assert(tokens[8].type == TokenType::LESS_EQUAL);
    assert(tokens[9].type == TokenType::GREATER);
    assert(tokens[10].type == TokenType::GREATER_EQUAL);
    assert(tokens[11].type == TokenType::AND);
    assert(tokens[12].type == TokenType::OR);
    assert(tokens[13].type == TokenType::NOT);

    std::cout << "  Passed!" << std::endl;
}

// ==================== 语法分析器测试 ====================

void testParserVarDeclaration() {
    std::cout << "Testing parser var declarations..." << std::endl;

    {
        Lexer lexer("let x = 10;");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
        assert(ast->statements[0]->stmtType == StmtType::VAR_DECL);
    }

    {
        Lexer lexer("var y = 42;");
        auto tokens = lexer.tokenize();
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        assert(parser.getErrors().empty());
        assert(ast->statements.size() == 1);
        assert(ast->statements[0]->stmtType == StmtType::VAR_DECL);
    }

    std::cout << "  Passed!" << std::endl;
}

void testParserExpressions() {
    std::cout << "Testing parser expressions..." << std::endl;

    Lexer lexer("1 + 2 * 3;");
    auto tokens = lexer.tokenize();
    Parser parser(std::move(tokens));
    auto ast = parser.parse();

    assert(parser.getErrors().empty());
    assert(ast->statements.size() == 1);
    assert(ast->statements[0]->stmtType == StmtType::EXPR_STMT);

    std::cout << "  Passed!" << std::endl;
}

void testParserFunctions() {
    std::cout << "Testing parser functions..." << std::endl;

    Lexer lexer("fn add(a: int, b: int): int { return a + b; }");
    auto tokens = lexer.tokenize();
    Parser parser(std::move(tokens));
    auto ast = parser.parse();

    assert(parser.getErrors().empty());
    assert(ast->statements.size() == 1);
    assert(ast->statements[0]->stmtType == StmtType::FUNCTION);

    std::cout << "  Passed!" << std::endl;
}

// ==================== 解释器测试 ====================

std::string executeAndCapture(const std::string& source) {
    Lexer lexer(source);
    auto tokens = lexer.tokenize();

    if (!lexer.getErrors().empty()) {
        return "LEXER ERROR";
    }

    Parser parser(std::move(tokens));
    auto ast = parser.parse();

    if (!parser.getErrors().empty()) {
        return "PARSER ERROR";
    }

    std::ostringstream output;
    Interpreter interpreter;
    interpreter.setOutputStream(&output);

    if (!interpreter.interpret(*ast)) {
        return "RUNTIME ERROR";
    }

    return output.str();
}

void testInterpreterArithmetic() {
    std::cout << "Testing interpreter arithmetic..." << std::endl;

    std::string output = executeAndCapture("print(1 + 2);");
    assert(output.find("3") != std::string::npos);

    output = executeAndCapture("print(10 - 3);");
    assert(output.find("7") != std::string::npos);

    output = executeAndCapture("print(4 * 5);");
    assert(output.find("20") != std::string::npos);

    std::cout << "  Passed!" << std::endl;
}

void testInterpreterVariables() {
    std::cout << "Testing interpreter variables..." << std::endl;

    std::string output = executeAndCapture(R"(
        let x = 10;
        print(x);
    )");
    assert(output.find("10") != std::string::npos);

    output = executeAndCapture(R"(
        var x = 10;
        x = 20;
        print(x);
    )");
    assert(output.find("20") != std::string::npos);

    std::cout << "  Passed!" << std::endl;
}

void testInterpreterIfStatement() {
    std::cout << "Testing interpreter if statements..." << std::endl;

    std::string output = executeAndCapture(R"(
        let x = 10;
        if (x > 5) {
            print("greater");
        }
    )");
    assert(output.find("greater") != std::string::npos);

    output = executeAndCapture(R"(
        let x = 3;
        if (x > 5) {
            print("greater");
        } else {
            print("smaller");
        }
    )");
    assert(output.find("smaller") != std::string::npos);

    std::cout << "  Passed!" << std::endl;
}

void testInterpreterWhileLoop() {
    std::cout << "Testing interpreter while loops..." << std::endl;

    std::string output = executeAndCapture(R"(
        let i = 0;
        while (i < 3) {
            print(i);
            i = i + 1;
        }
    )");
    assert(output.find("0") != std::string::npos);
    assert(output.find("2") != std::string::npos);

    std::cout << "  Passed!" << std::endl;
}

void testInterpreterFunctions() {
    std::cout << "Testing interpreter functions..." << std::endl;

    std::string output = executeAndCapture(R"(
        fn add(a: int, b: int): int {
            return a + b;
        }
        print(add(3, 4));
    )");
    assert(output.find("7") != std::string::npos);

    std::cout << "  Passed!" << std::endl;
}

void testInterpreterBuiltinFunctions() {
    std::cout << "Testing interpreter built-in functions..." << std::endl;

    std::string output = executeAndCapture("print(abs(-5));");
    assert(output.find("5") != std::string::npos);

    output = executeAndCapture("print(sqrt(16));");
    assert(output.find("4") != std::string::npos);

    std::cout << "  Passed!" << std::endl;
}

// ==================== 主测试函数 ====================

int main() {
    std::cout << "=== Simple Compiler Tests ===" << std::endl;
    std::cout << std::endl;

    std::cout << "--- Lexer Tests ---" << std::endl;
    testLexerNumbers();
    testLexerKeywords();
    testLexerOperators();
    std::cout << std::endl;

    std::cout << "--- Parser Tests ---" << std::endl;
    testParserVarDeclaration();
    testParserExpressions();
    testParserFunctions();
    std::cout << std::endl;

    std::cout << "--- Interpreter Tests ---" << std::endl;
    testInterpreterArithmetic();
    testInterpreterVariables();
    testInterpreterIfStatement();
    testInterpreterWhileLoop();
    testInterpreterFunctions();
    testInterpreterBuiltinFunctions();
    std::cout << std::endl;

    std::cout << "=== All tests passed! ===" << std::endl;

    return 0;
}
