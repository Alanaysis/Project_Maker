/**
 * 词法分析器测试
 */

#include "lexer.hpp"
#include <iostream>
#include <cassert>
#include <string>
#include <vector>

using namespace compiler;

/**
 * 测试辅助函数
 */
void assertTokenType(TokenType expected, TokenType actual, const std::string& context) {
    if (expected != actual) {
        std::cerr << "Test failed: " << context << std::endl;
        std::cerr << "  Expected: " << static_cast<int>(expected) << std::endl;
        std::cerr << "  Actual: " << static_cast<int>(actual) << std::endl;
        assert(false);
    }
}

/**
 * 测试数字字面量
 */
void testNumbers() {
    std::cout << "Testing numbers..." << std::endl;

    Lexer lexer("42 3.14 100 0.5");
    auto tokens = lexer.tokenize();

    assert(tokens.size() >= 5); // 4个数字 + EOF
    assertTokenType(TokenType::INTEGER, tokens[0].type, "integer literal");
    assertTokenType(TokenType::FLOAT, tokens[1].type, "float literal");
    assertTokenType(TokenType::INTEGER, tokens[2].type, "integer literal");
    assertTokenType(TokenType::FLOAT, tokens[3].type, "float literal");

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试字符串字面量
 */
void testStrings() {
    std::cout << "Testing strings..." << std::endl;

    Lexer lexer("\"hello\" \"world\" \"\"");
    auto tokens = lexer.tokenize();

    assert(tokens.size() >= 4); // 3个字符串 + EOF
    assertTokenType(TokenType::STRING, tokens[0].type, "string literal");
    assertTokenType(TokenType::STRING, tokens[1].type, "string literal");
    assertTokenType(TokenType::STRING, tokens[2].type, "empty string literal");

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试关键字
 */
void testKeywords() {
    std::cout << "Testing keywords..." << std::endl;

    Lexer lexer("let var const if else while for fn return class");
    auto tokens = lexer.tokenize();

    assert(tokens.size() >= 11); // 10个关键字 + EOF
    assertTokenType(TokenType::LET, tokens[0].type, "let keyword");
    assertTokenType(TokenType::VAR, tokens[1].type, "var keyword");
    assertTokenType(TokenType::CONST, tokens[2].type, "const keyword");
    assertTokenType(TokenType::IF, tokens[3].type, "if keyword");
    assertTokenType(TokenType::ELSE, tokens[4].type, "else keyword");
    assertTokenType(TokenType::WHILE, tokens[5].type, "while keyword");
    assertTokenType(TokenType::FOR, tokens[6].type, "for keyword");
    assertTokenType(TokenType::FUNCTION, tokens[7].type, "fn keyword");
    assertTokenType(TokenType::RETURN, tokens[8].type, "return keyword");
    assertTokenType(TokenType::CLASS, tokens[9].type, "class keyword");

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试标识符
 */
void testIdentifiers() {
    std::cout << "Testing identifiers..." << std::endl;

    Lexer lexer("foo bar_baz _test camelCase");
    auto tokens = lexer.tokenize();

    assert(tokens.size() >= 5); // 4个标识符 + EOF
    assertTokenType(TokenType::IDENTIFIER, tokens[0].type, "identifier foo");
    assertTokenType(TokenType::IDENTIFIER, tokens[1].type, "identifier bar_baz");
    assertTokenType(TokenType::IDENTIFIER, tokens[2].type, "identifier _test");
    assertTokenType(TokenType::IDENTIFIER, tokens[3].type, "identifier camelCase");

    assert(tokens[0].lexeme == "foo");
    assert(tokens[1].lexeme == "bar_baz");
    assert(tokens[2].lexeme == "_test");
    assert(tokens[3].lexeme == "camelCase");

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试运算符
 */
void testOperators() {
    std::cout << "Testing operators..." << std::endl;

    Lexer lexer("+ - * / % = == != < <= > >= && || ! ++ -- += -=");
    auto tokens = lexer.tokenize();

    assert(tokens.size() >= 19); // 18个运算符 + EOF
    assertTokenType(TokenType::PLUS, tokens[0].type, "plus");
    assertTokenType(TokenType::MINUS, tokens[1].type, "minus");
    assertTokenType(TokenType::MULTIPLY, tokens[2].type, "multiply");
    assertTokenType(TokenType::DIVIDE, tokens[3].type, "divide");
    assertTokenType(TokenType::MODULO, tokens[4].type, "modulo");
    assertTokenType(TokenType::ASSIGN, tokens[5].type, "assign");
    assertTokenType(TokenType::EQUAL, tokens[6].type, "equal");
    assertTokenType(TokenType::NOT_EQUAL, tokens[7].type, "not equal");
    assertTokenType(TokenType::LESS, tokens[8].type, "less");
    assertTokenType(TokenType::LESS_EQUAL, tokens[9].type, "less equal");
    assertTokenType(TokenType::GREATER, tokens[10].type, "greater");
    assertTokenType(TokenType::GREATER_EQUAL, tokens[11].type, "greater equal");
    assertTokenType(TokenType::AND, tokens[12].type, "and");
    assertTokenType(TokenType::OR, tokens[13].type, "or");
    assertTokenType(TokenType::NOT, tokens[14].type, "not");
    assertTokenType(TokenType::INCREMENT, tokens[15].type, "increment");
    assertTokenType(TokenType::DECREMENT, tokens[16].type, "decrement");
    assertTokenType(TokenType::PLUS_ASSIGN, tokens[17].type, "plus assign");
    assertTokenType(TokenType::MINUS_ASSIGN, tokens[18].type, "minus assign");

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试注释
 */
void testComments() {
    std::cout << "Testing comments..." << std::endl;

    Lexer lexer("let x = 10; // this is a comment\nlet y = 20;");
    auto tokens = lexer.tokenize();

    // 注释应该被跳过
    assert(tokens.size() >= 9); // let x = 10 ; let y = 20 ; EOF
    assertTokenType(TokenType::LET, tokens[0].type, "let after comment");

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试多行注释
 */
void testMultiLineComments() {
    std::cout << "Testing multi-line comments..." << std::endl;

    Lexer lexer("let x = 10; /* this is\na multi-line\ncomment */ let y = 20;");
    auto tokens = lexer.tokenize();

    // 注释应该被跳过
    assert(tokens.size() >= 9); // let x = 10 ; let y = 20 ; EOF
    assertTokenType(TokenType::LET, tokens[0].type, "let before comment");
    assertTokenType(TokenType::LET, tokens[4].type, "let after comment");

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试行号和列号
 */
void testLineAndColumn() {
    std::cout << "Testing line and column tracking..." << std::endl;

    Lexer lexer("let x = 10;\nlet y = 20;");
    auto tokens = lexer.tokenize();

    // 第一个token应该在第1行
    assert(tokens[0].line == 1);

    // let y应该在第2行
    for (size_t i = 0; i < tokens.size(); ++i) {
        if (tokens[i].type == TokenType::IDENTIFIER && tokens[i].lexeme == "y") {
            assert(tokens[i].line == 2);
            break;
        }
    }

    std::cout << "  Passed!" << std::endl;
}

/**
 * 测试错误处理
 */
void testErrors() {
    std::cout << "Testing error handling..." << std::endl;

    // 未闭合的字符串
    Lexer lexer("\"unterminated string");
    auto tokens = lexer.tokenize();
    assert(!lexer.getErrors().empty());

    // 未闭合的注释
    Lexer lexer2("/* unterminated comment");
    auto tokens2 = lexer2.tokenize();
    assert(!lexer2.getErrors().empty());

    std::cout << "  Passed!" << std::endl;
}

int main() {
    std::cout << "=== Lexer Tests ===" << std::endl;
    std::cout << std::endl;

    testNumbers();
    testStrings();
    testKeywords();
    testIdentifiers();
    testOperators();
    testComments();
    testMultiLineComments();
    testLineAndColumn();
    testErrors();

    std::cout << std::endl;
    std::cout << "All lexer tests passed!" << std::endl;

    return 0;
}
