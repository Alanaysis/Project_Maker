#include "sql/tokenizer.h"
#include <cctype>
#include <stdexcept>
#include <iostream>

namespace minidb {

// 初始化关键字映射表
std::unordered_map<std::string, TokenType> Tokenizer::keywords_;
bool keywords_initialized = false;

void Tokenizer::initKeywords() {
    if (keywords_initialized) return;

    keywords_["SELECT"] = TokenType::SELECT;
    keywords_["FROM"] = TokenType::FROM;
    keywords_["WHERE"] = TokenType::WHERE;
    keywords_["INSERT"] = TokenType::INSERT;
    keywords_["INTO"] = TokenType::INTO;
    keywords_["VALUES"] = TokenType::VALUES;
    keywords_["CREATE"] = TokenType::CREATE;
    keywords_["TABLE"] = TokenType::TABLE;
    keywords_["UPDATE"] = TokenType::UPDATE;
    keywords_["SET"] = TokenType::SET;
    keywords_["DELETE"] = TokenType::DELETE;
    keywords_["DROP"] = TokenType::DROP;
    keywords_["AND"] = TokenType::AND;
    keywords_["OR"] = TokenType::OR;
    keywords_["NOT"] = TokenType::NOT;
    keywords_["NULL"] = TokenType::NULL_TOKEN;
    keywords_["PRIMARY"] = TokenType::PRIMARY;
    keywords_["KEY"] = TokenType::KEY;
    keywords_["INT"] = TokenType::INT_TYPE;
    keywords_["INTEGER"] = TokenType::INT_TYPE;
    keywords_["VARCHAR"] = TokenType::VARCHAR_TYPE;
    keywords_["FLOAT"] = TokenType::FLOAT_TYPE;

    keywords_initialized = true;
}

Tokenizer::Tokenizer(const std::string& sql)
    : sql_(sql), pos_(0), line_(1), column_(1) {
    initKeywords();
}

std::vector<Token> Tokenizer::tokenize() {
    std::vector<Token> tokens;

    while (hasNext()) {
        Token token = nextToken();
        tokens.push_back(token);

        if (token.type == TokenType::INVALID) {
            break;
        }
        if (token.type == TokenType::EOF_TOKEN) {
            break;
        }
    }

    return tokens;
}

Token Tokenizer::nextToken() {
    skipWhitespace();
    skipComment();

    if (isAtEnd()) {
        return makeToken(TokenType::EOF_TOKEN, "");
    }

    char c = current();

    // 数字
    if (std::isdigit(c)) {
        return readNumber();
    }

    // 字符串
    if (c == '\'') {
        return readString();
    }

    // 标识符或关键字
    if (std::isalpha(c) || c == '_') {
        return readIdentifier();
    }

    // 运算符和分隔符
    return readOperator();
}

bool Tokenizer::hasNext() const {
    return pos_ < sql_.size();
}

void Tokenizer::skipWhitespace() {
    while (!isAtEnd()) {
        char c = current();
        if (c == ' ' || c == '\t' || c == '\r') {
            advance();
        } else if (c == '\n') {
            line_++;
            column_ = 1;
            advance();
        } else {
            break;
        }
    }
}

void Tokenizer::skipComment() {
    if (isAtEnd()) return;

    // 单行注释: --
    if (current() == '-' && peek() == '-') {
        while (!isAtEnd() && current() != '\n') {
            advance();
        }
        skipWhitespace();
    }

    // 多行注释: /* ... */
    if (current() == '/' && peek() == '*') {
        advance();  // 跳过 /
        advance();  // 跳过 *
        while (!isAtEnd()) {
            if (current() == '*' && peek() == '/') {
                advance();  // 跳过 *
                advance();  // 跳过 /
                break;
            }
            if (current() == '\n') {
                line_++;
                column_ = 1;
            }
            advance();
        }
        skipWhitespace();
    }
}

Token Tokenizer::readNumber() {
    size_t start = pos_;
    int start_col = column_;
    bool is_float = false;

    while (!isAtEnd() && (std::isdigit(current()) || current() == '.')) {
        if (current() == '.') {
            if (is_float) {
                return errorToken("Invalid number format");
            }
            is_float = true;
        }
        advance();
    }

    std::string value = sql_.substr(start, pos_ - start);

    if (is_float) {
        return Token(TokenType::FLOAT, value, line_, start_col);
    }
    return Token(TokenType::INTEGER, value, line_, start_col);
}

Token Tokenizer::readString() {
    int start_col = column_;
    advance();  // 跳过开始的引号

    size_t start = pos_;
    while (!isAtEnd() && current() != '\'') {
        if (current() == '\\') {
            advance();  // 跳过转义字符
        }
        advance();
    }

    if (isAtEnd()) {
        return errorToken("Unterminated string");
    }

    std::string value = sql_.substr(start, pos_ - start);
    advance();  // 跳过结束的引号

    return Token(TokenType::STRING, value, line_, start_col);
}

Token Tokenizer::readIdentifier() {
    size_t start = pos_;
    int start_col = column_;

    while (!isAtEnd() && (std::isalnum(current()) || current() == '_')) {
        advance();
    }

    std::string value = sql_.substr(start, pos_ - start);

    // 转换为大写进行关键字匹配
    std::string upper_value = value;
    for (auto& c : upper_value) {
        c = std::toupper(c);
    }

    auto it = keywords_.find(upper_value);
    if (it != keywords_.end()) {
        return Token(it->second, value, line_, start_col);
    }

    return Token(TokenType::IDENTIFIER, value, line_, start_col);
}

Token Tokenizer::readOperator() {
    int start_col = column_;
    char c = current();
    advance();

    switch (c) {
        case '+':
            return makeToken(TokenType::PLUS, "+");
        case '-':
            return makeToken(TokenType::MINUS, "-");
        case '*':
            return makeToken(TokenType::STAR, "*");
        case '/':
            return makeToken(TokenType::DIVIDE, "/");
        case '(':
            return makeToken(TokenType::LPAREN, "(");
        case ')':
            return makeToken(TokenType::RPAREN, ")");
        case ',':
            return makeToken(TokenType::COMMA, ",");
        case ';':
            return makeToken(TokenType::SEMICOLON, ";");
        case '.':
            return makeToken(TokenType::DOT, ".");
        case '=':
            return makeToken(TokenType::EQUAL, "=");
        case '<':
            if (!isAtEnd() && current() == '=') {
                advance();
                return makeToken(TokenType::LESS_EQUAL, "<=");
            }
            if (!isAtEnd() && current() == '>') {
                advance();
                return makeToken(TokenType::NOT_EQUAL, "<>");
            }
            return makeToken(TokenType::LESS, "<");
        case '>':
            if (!isAtEnd() && current() == '=') {
                advance();
                return makeToken(TokenType::GREATER_EQUAL, ">=");
            }
            return makeToken(TokenType::GREATER, ">");
        case '!':
            if (!isAtEnd() && current() == '=') {
                advance();
                return makeToken(TokenType::NOT_EQUAL, "!=");
            }
            return errorToken("Expected '=' after '!'");
        default:
            return errorToken("Unexpected character");
    }
}

char Tokenizer::current() const {
    if (isAtEnd()) return '\0';
    return sql_[pos_];
}

char Tokenizer::peek() const {
    if (pos_ + 1 >= sql_.size()) return '\0';
    return sql_[pos_ + 1];
}

void Tokenizer::advance() {
    if (!isAtEnd()) {
        pos_++;
        column_++;
    }
}

bool Tokenizer::isAtEnd() const {
    return pos_ >= sql_.size();
}

Token Tokenizer::makeToken(TokenType type, const std::string& value) {
    return Token(type, value, line_, column_ - value.size());
}

Token Tokenizer::errorToken(const std::string& message) {
    error_ = message + " at line " + std::to_string(line_) +
             ", column " + std::to_string(column_);
    return Token(TokenType::INVALID, message, line_, column_);
}

// Token 方法实现

bool Token::isKeyword() const {
    switch (type) {
        case TokenType::SELECT:
        case TokenType::FROM:
        case TokenType::WHERE:
        case TokenType::INSERT:
        case TokenType::INTO:
        case TokenType::VALUES:
        case TokenType::CREATE:
        case TokenType::TABLE:
        case TokenType::UPDATE:
        case TokenType::SET:
        case TokenType::DELETE:
        case TokenType::DROP:
        case TokenType::AND:
        case TokenType::OR:
        case TokenType::NOT:
        case TokenType::NULL_TOKEN:
        case TokenType::PRIMARY:
        case TokenType::KEY:
        case TokenType::INT_TYPE:
        case TokenType::VARCHAR_TYPE:
        case TokenType::FLOAT_TYPE:
            return true;
        default:
            return false;
    }
}

bool Token::isOperator() const {
    switch (type) {
        case TokenType::PLUS:
        case TokenType::MINUS:
        case TokenType::MULTIPLY:
        case TokenType::DIVIDE:
        case TokenType::EQUAL:
        case TokenType::NOT_EQUAL:
        case TokenType::LESS:
        case TokenType::GREATER:
        case TokenType::LESS_EQUAL:
        case TokenType::GREATER_EQUAL:
        case TokenType::ASSIGN:
            return true;
        default:
            return false;
    }
}

bool Token::isLiteral() const {
    switch (type) {
        case TokenType::INTEGER:
        case TokenType::FLOAT:
        case TokenType::STRING:
            return true;
        default:
            return false;
    }
}

std::string Token::toString() const {
    std::string type_str;
    switch (type) {
        case TokenType::INTEGER: type_str = "INTEGER"; break;
        case TokenType::FLOAT: type_str = "FLOAT"; break;
        case TokenType::STRING: type_str = "STRING"; break;
        case TokenType::IDENTIFIER: type_str = "IDENTIFIER"; break;
        case TokenType::SELECT: type_str = "SELECT"; break;
        case TokenType::FROM: type_str = "FROM"; break;
        case TokenType::WHERE: type_str = "WHERE"; break;
        case TokenType::INSERT: type_str = "INSERT"; break;
        case TokenType::INTO: type_str = "INTO"; break;
        case TokenType::VALUES: type_str = "VALUES"; break;
        case TokenType::CREATE: type_str = "CREATE"; break;
        case TokenType::TABLE: type_str = "TABLE"; break;
        case TokenType::UPDATE: type_str = "UPDATE"; break;
        case TokenType::SET: type_str = "SET"; break;
        case TokenType::DELETE: type_str = "DELETE"; break;
        case TokenType::EOF_TOKEN: type_str = "EOF"; break;
        case TokenType::INVALID: type_str = "INVALID"; break;
        default: type_str = "OTHER"; break;
    }
    return type_str + "('" + value + "')";
}

}  // namespace minidb
