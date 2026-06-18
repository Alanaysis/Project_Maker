#pragma once

#include <string>
#include <vector>
#include <unordered_map>

namespace minidb {

// Token 类型
enum class TokenType {
    // 字面量
    INTEGER,
    FLOAT,
    STRING,
    IDENTIFIER,

    // 关键字
    SELECT,
    FROM,
    WHERE,
    INSERT,
    INTO,
    VALUES,
    CREATE,
    TABLE,
    UPDATE,
    SET,
    DELETE,
    DROP,
    AND,
    OR,
    NOT,
    NULL_TOKEN,
    PRIMARY,
    KEY,
    INT_TYPE,
    VARCHAR_TYPE,
    FLOAT_TYPE,

    // 运算符
    PLUS,
    MINUS,
    MULTIPLY,
    DIVIDE,
    EQUAL,
    NOT_EQUAL,
    LESS,
    GREATER,
    LESS_EQUAL,
    GREATER_EQUAL,
    ASSIGN,

    // 分隔符
    COMMA,
    SEMICOLON,
    LPAREN,
    RPAREN,
    DOT,

    // 特殊
    STAR,
    EOF_TOKEN,
    INVALID
};

// Token 结构
struct Token {
    TokenType type;
    std::string value;
    int line;
    int column;

    Token() : type(TokenType::INVALID), line(0), column(0) {}
    Token(TokenType t, const std::string& v, int l, int c)
        : type(t), value(v), line(l), column(c) {}

    bool isKeyword() const;
    bool isOperator() const;
    bool isLiteral() const;
    std::string toString() const;
};

// 词法分析器
class Tokenizer {
public:
    /**
     * @brief 构造函数
     * @param sql SQL 语句
     */
    explicit Tokenizer(const std::string& sql);

    /**
     * @brief 将 SQL 分词
     * @return Token 列表
     */
    std::vector<Token> tokenize();

    /**
     * @brief 获取下一个 Token
     * @return Token
     */
    Token nextToken();

    /**
     * @brief 检查是否还有更多 Token
     * @return 是否有更多
     */
    bool hasNext() const;

    /**
     * @brief 获取当前行号
     * @return 行号
     */
    int getLine() const { return line_; }

    /**
     * @brief 获取当前列号
     * @return 列号
     */
    int getColumn() const { return column_; }

    /**
     * @brief 获取错误信息
     * @return 错误信息
     */
    const std::string& getError() const { return error_; }

private:
    /**
     * @brief 跳过空白字符
     */
    void skipWhitespace();

    /**
     * @brief 跳过注释
     */
    void skipComment();

    /**
     * @brief 读取数字
     * @return Token
     */
    Token readNumber();

    /**
     * @brief 读取字符串
     * @return Token
     */
    Token readString();

    /**
     * @brief 读取标识符或关键字
     * @return Token
     */
    Token readIdentifier();

    /**
     * @brief 读取运算符或分隔符
     * @return Token
     */
    Token readOperator();

    /**
     * @brief 获取当前字符
     * @return 当前字符
     */
    char current() const;

    /**
     * @brief 获取下一个字符
     * @return 下一个字符
     */
    char peek() const;

    /**
     * @brief 前进一个字符
     */
    void advance();

    /**
     * @brief 检查是否到达末尾
     * @return 是否到达末尾
     */
    bool isAtEnd() const;

    /**
     * @brief 创建 Token
     * @param type Token 类型
     * @param value Token 值
     * @return Token
     */
    Token makeToken(TokenType type, const std::string& value);

    /**
     * @brief 创建错误 Token
     * @param message 错误信息
     * @return Token
     */
    Token errorToken(const std::string& message);

    // 关键字映射表
    static std::unordered_map<std::string, TokenType> keywords_;

    // 初始化关键字映射表
    static void initKeywords();

    std::string sql_;           // SQL 语句
    size_t pos_;                // 当前位置
    int line_;                  // 当前行号
    int column_;                // 当前列号
    std::string error_;         // 错误信息
};

}  // namespace minidb
