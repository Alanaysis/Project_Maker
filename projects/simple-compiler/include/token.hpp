#pragma once

#include <string>
#include <variant>
#include <unordered_map>

namespace compiler {

/**
 * Token类型枚举
 * 定义了编译器能识别的所有token类型
 */
enum class TokenType {
    // 字面量
    INTEGER,        // 整数: 42, 100
    FLOAT,          // 浮点数: 3.14, 2.0
    STRING,         // 字符串: "hello"
    TRUE,           // true
    FALSE,          // false

    // 标识符
    IDENTIFIER,     // 变量名、函数名等

    // 关键字
    LET,            // let
    VAR,            // var
    CONST,          // const
    IF,             // if
    ELSE,           // else
    WHILE,          // while
    FOR,            // for
    FUNCTION,       // fn
    RETURN,         // return
    CLASS,          // class
    NEW,            // new
    PRINT,          // print
    BREAK,          // break
    CONTINUE,       // continue
    IMPORT,         // import
    FROM,           // from
    AS,             // as

    // 类型关键字
    INT_TYPE,       // int
    FLOAT_TYPE,     // float
    STRING_TYPE,    // string
    BOOL_TYPE,      // bool
    VOID_TYPE,      // void

    // 运算符
    PLUS,           // +
    MINUS,          // -
    MULTIPLY,       // *
    DIVIDE,         // /
    MODULO,         // %
    POWER,          // **

    // 赋值运算符
    ASSIGN,         // =
    PLUS_ASSIGN,    // +=
    MINUS_ASSIGN,   // -=
    MUL_ASSIGN,     // *=
    DIV_ASSIGN,     // /=

    // 比较运算符
    EQUAL,          // ==
    NOT_EQUAL,      // !=
    LESS,           // <
    LESS_EQUAL,     // <=
    GREATER,        // >
    GREATER_EQUAL,  // >=

    // 逻辑运算符
    AND,            // &&
    OR,             // ||
    NOT,            // !

    // 位运算符
    BIT_AND,        // &
    BIT_OR,         // |
    BIT_XOR,        // ^
    BIT_NOT,        // ~
    SHIFT_LEFT,     // <<
    SHIFT_RIGHT,    // >>

    // 分隔符
    LEFT_PAREN,     // (
    RIGHT_PAREN,    // )
    LEFT_BRACE,     // {
    RIGHT_BRACE,    // }
    LEFT_BRACKET,   // [
    RIGHT_BRACKET,  // ]
    COMMA,          // ,
    DOT,            // .
    SEMICOLON,      // ;
    COLON,          // :
    ARROW,          // ->
    DOUBLE_COLON,   // ::

    // 特殊token
    NEWLINE,        // 换行
    EOF_TOKEN,      // 文件结束
    ERROR,          // 错误token

    // 自增自减
    INCREMENT,      // ++
    DECREMENT,      // --

    // 类型检查
    IS,             // is
    AS_TYPE,        // as (类型转换)
};

/**
 * Token值类型
 * 使用std::variant存储不同类型的字面量值
 */
using TokenValue = std::variant<
    std::monostate,     // 无值
    bool,               // 布尔值
    int64_t,            // 整数值
    double,             // 浮点值
    std::string         // 字符串值
>;

/**
 * Token结构体
 * 表示词法分析器输出的一个token
 */
struct Token {
    TokenType type;         // token类型
    std::string lexeme;     // token的原始文本
    TokenValue value;       // token的值（如果有）
    int line;               // 所在行号
    int column;             // 所在列号

    Token() : type(TokenType::ERROR), line(0), column(0) {}

    Token(TokenType type, const std::string& lexeme, int line, int column)
        : type(type), lexeme(lexeme), line(line), column(column) {}

    Token(TokenType type, const std::string& lexeme, TokenValue value, int line, int column)
        : type(type), lexeme(lexeme), value(value), line(line), column(column) {}

    /**
     * 获取token类型的字符串表示
     */
    std::string typeToString() const {
        static const std::unordered_map<TokenType, std::string> typeNames = {
            {TokenType::INTEGER, "INTEGER"},
            {TokenType::FLOAT, "FLOAT"},
            {TokenType::STRING, "STRING"},
            {TokenType::TRUE, "TRUE"},
            {TokenType::FALSE, "FALSE"},
            {TokenType::IDENTIFIER, "IDENTIFIER"},
            {TokenType::LET, "LET"},
            {TokenType::VAR, "VAR"},
            {TokenType::CONST, "CONST"},
            {TokenType::IF, "IF"},
            {TokenType::ELSE, "ELSE"},
            {TokenType::WHILE, "WHILE"},
            {TokenType::FOR, "FOR"},
            {TokenType::FUNCTION, "FUNCTION"},
            {TokenType::RETURN, "RETURN"},
            {TokenType::CLASS, "CLASS"},
            {TokenType::NEW, "NEW"},
            {TokenType::PRINT, "PRINT"},
            {TokenType::BREAK, "BREAK"},
            {TokenType::CONTINUE, "CONTINUE"},
            {TokenType::IMPORT, "IMPORT"},
            {TokenType::FROM, "FROM"},
            {TokenType::AS, "AS"},
            {TokenType::INT_TYPE, "INT_TYPE"},
            {TokenType::FLOAT_TYPE, "FLOAT_TYPE"},
            {TokenType::STRING_TYPE, "STRING_TYPE"},
            {TokenType::BOOL_TYPE, "BOOL_TYPE"},
            {TokenType::VOID_TYPE, "VOID_TYPE"},
            {TokenType::PLUS, "PLUS"},
            {TokenType::MINUS, "MINUS"},
            {TokenType::MULTIPLY, "MULTIPLY"},
            {TokenType::DIVIDE, "DIVIDE"},
            {TokenType::MODULO, "MODULO"},
            {TokenType::POWER, "POWER"},
            {TokenType::ASSIGN, "ASSIGN"},
            {TokenType::PLUS_ASSIGN, "PLUS_ASSIGN"},
            {TokenType::MINUS_ASSIGN, "MINUS_ASSIGN"},
            {TokenType::MUL_ASSIGN, "MUL_ASSIGN"},
            {TokenType::DIV_ASSIGN, "DIV_ASSIGN"},
            {TokenType::EQUAL, "EQUAL"},
            {TokenType::NOT_EQUAL, "NOT_EQUAL"},
            {TokenType::LESS, "LESS"},
            {TokenType::LESS_EQUAL, "LESS_EQUAL"},
            {TokenType::GREATER, "GREATER"},
            {TokenType::GREATER_EQUAL, "GREATER_EQUAL"},
            {TokenType::AND, "AND"},
            {TokenType::OR, "OR"},
            {TokenType::NOT, "NOT"},
            {TokenType::BIT_AND, "BIT_AND"},
            {TokenType::BIT_OR, "BIT_OR"},
            {TokenType::BIT_XOR, "BIT_XOR"},
            {TokenType::BIT_NOT, "BIT_NOT"},
            {TokenType::SHIFT_LEFT, "SHIFT_LEFT"},
            {TokenType::SHIFT_RIGHT, "SHIFT_RIGHT"},
            {TokenType::LEFT_PAREN, "LEFT_PAREN"},
            {TokenType::RIGHT_PAREN, "RIGHT_PAREN"},
            {TokenType::LEFT_BRACE, "LEFT_BRACE"},
            {TokenType::RIGHT_BRACE, "RIGHT_BRACE"},
            {TokenType::LEFT_BRACKET, "LEFT_BRACKET"},
            {TokenType::RIGHT_BRACKET, "RIGHT_BRACKET"},
            {TokenType::COMMA, "COMMA"},
            {TokenType::DOT, "DOT"},
            {TokenType::SEMICOLON, "SEMICOLON"},
            {TokenType::COLON, "COLON"},
            {TokenType::ARROW, "ARROW"},
            {TokenType::DOUBLE_COLON, "DOUBLE_COLON"},
            {TokenType::NEWLINE, "NEWLINE"},
            {TokenType::EOF_TOKEN, "EOF"},
            {TokenType::ERROR, "ERROR"},
            {TokenType::INCREMENT, "INCREMENT"},
            {TokenType::DECREMENT, "DECREMENT"},
            {TokenType::IS, "IS"},
            {TokenType::AS_TYPE, "AS_TYPE"},
        };

        auto it = typeNames.find(type);
        if (it != typeNames.end()) {
            return it->second;
        }
        return "UNKNOWN";
    }

    /**
     * 获取值的字符串表示
     */
    std::string valueToString() const {
        if (std::holds_alternative<int64_t>(value)) {
            return std::to_string(std::get<int64_t>(value));
        } else if (std::holds_alternative<double>(value)) {
            return std::to_string(std::get<double>(value));
        } else if (std::holds_alternative<std::string>(value)) {
            return std::get<std::string>(value);
        }
        return "";
    }
};

/**
 * 关键字映射表
 * 将关键字字符串映射到对应的TokenType
 */
inline const std::unordered_map<std::string, TokenType>& getKeywords() {
    static const std::unordered_map<std::string, TokenType> keywords = {
        {"let", TokenType::LET},
        {"var", TokenType::VAR},
        {"const", TokenType::CONST},
        {"if", TokenType::IF},
        {"else", TokenType::ELSE},
        {"while", TokenType::WHILE},
        {"for", TokenType::FOR},
        {"fn", TokenType::FUNCTION},
        {"return", TokenType::RETURN},
        {"class", TokenType::CLASS},
        {"new", TokenType::NEW},
        {"print", TokenType::PRINT},
        {"break", TokenType::BREAK},
        {"continue", TokenType::CONTINUE},
        {"import", TokenType::IMPORT},
        {"from", TokenType::FROM},
        {"as", TokenType::AS},
        {"true", TokenType::TRUE},
        {"false", TokenType::FALSE},
        {"int", TokenType::INT_TYPE},
        {"float", TokenType::FLOAT_TYPE},
        {"string", TokenType::STRING_TYPE},
        {"bool", TokenType::BOOL_TYPE},
        {"void", TokenType::VOID_TYPE},
        {"is", TokenType::IS},
    };
    return keywords;
}

} // namespace compiler
