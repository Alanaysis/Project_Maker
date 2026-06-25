#pragma once

#include "token.hpp"
#include <string>
#include <vector>
#include <memory>

namespace compiler {

/**
 * 词法分析器 (Lexer)
 *
 * 职责：
 * 1. 将源代码字符串转换为token流
 * 2. 处理空白字符和注释
 * 3. 识别关键字、标识符、字面量、运算符
 * 4. 报告词法错误
 *
 * 设计原则：
 * - 一次扫描，逐字符处理
 * - 支持单行注释 (//) 和多行注释 (/* ... *​/)
 * - 支持字符串转义序列
 */
class Lexer {
public:
    /**
     * 构造函数
     * @param source 源代码字符串
     */
    explicit Lexer(const std::string& source);

    /**
     * 词法分析
     * @return token列表
     */
    std::vector<Token> tokenize();

    /**
     * 获取下一个token
     * @return 下一个token
     */
    Token nextToken();

    /**
     * 检查是否有更多token
     */
    bool hasMore() const;

    /**
     * 获取错误信息
     */
    const std::vector<std::string>& getErrors() const { return errors_; }

private:
    // 源代码相关
    std::string source_;
    size_t current_;        // 当前字符位置
    int line_;              // 当前行号
    int column_;            // 当前列号

    // 错误信息
    std::vector<std::string> errors_;

    // 辅助方法

    /**
     * 查看当前字符（不消耗）
     */
    char peek() const;

    /**
     * 查看下一个字符（不消耗）
     */
    char peekNext() const;

    /**
     * 消耗并返回当前字符
     */
    char advance();

    /**
     * 检查当前字符是否匹配预期，匹配则消耗
     */
    bool match(char expected);

    /**
     * 跳过空白字符
     */
    void skipWhitespace();

    /**
     * 跳过注释
     * @return 是否成功跳过注释
     */
    bool skipComment();

    /**
     * 检查是否是行结束
     */
    bool isAtEnd() const;

    /**
     * 创建token
     */
    Token makeToken(TokenType type, const std::string& lexeme);

    /**
     * 创建带值的token
     */
    Token makeToken(TokenType type, const std::string& lexeme, TokenValue value);

    /**
     * 创建错误token
     */
    Token errorToken(const std::string& message);

    /**
     * 识别标识符或关键字
     */
    Token identifier();

    /**
     * 识别数字
     */
    Token number();

    /**
     * 识别字符串
     */
    Token string();

    /**
     * 识别运算符
     */
    Token operatorToken();

    /**
     * 检查字符是否是字母
     */
    bool isAlpha(char c) const;

    /**
     * 检查字符是否是数字
     */
    bool isDigit(char c) const;

    /**
     * 检查字符是否是字母或数字
     */
    bool isAlphaNumeric(char c) const;
};

} // namespace compiler
