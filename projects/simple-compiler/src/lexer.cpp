#include "lexer.hpp"
#include <cctype>
#include <stdexcept>

namespace compiler {

Lexer::Lexer(const std::string& source)
    : source_(source), current_(0), line_(1), column_(1) {}

std::vector<Token> Lexer::tokenize() {
    std::vector<Token> tokens;

    while (!isAtEnd()) {
        skipWhitespace();

        if (isAtEnd()) break;

        // 跳过注释
        if (skipComment()) {
            continue;
        }

        size_t start = current_;
        int startLine = line_;
        int startColumn = column_;

        char c = advance();

        // 标识符或关键字
        if (isAlpha(c)) {
            // 回退一个字符，让identifier()处理
            current_--;
            column_--;
            tokens.push_back(identifier());
        }
        // 数字
        else if (isDigit(c)) {
            current_--;
            column_--;
            tokens.push_back(number());
        }
        // 字符串
        else if (c == '"') {
            current_--;
            column_--;
            tokens.push_back(string());
        }
        // 单引号字符串
        else if (c == '\'') {
            current_--;
            column_--;
            tokens.push_back(string());
        }
        // 运算符和分隔符
        else {
            current_--;
            column_--;
            Token token = operatorToken();
            if (token.type != TokenType::NEWLINE) {
                tokens.push_back(token);
            }
        }
    }

    // 添加EOF token
    tokens.emplace_back(TokenType::EOF_TOKEN, "", line_, column_);
    return tokens;
}

Token Lexer::nextToken() {
    skipWhitespace();

    if (isAtEnd()) {
        return Token(TokenType::EOF_TOKEN, "", line_, column_);
    }

    // 跳过注释
    while (skipComment()) {
        skipWhitespace();
    }

    if (isAtEnd()) {
        return Token(TokenType::EOF_TOKEN, "", line_, column_);
    }

    char c = advance();

    // 标识符或关键字
    if (isAlpha(c)) {
        current_--;
        column_--;
        return identifier();
    }
    // 数字
    else if (isDigit(c)) {
        current_--;
        column_--;
        return number();
    }
    // 字符串
    else if (c == '"' || c == '\'') {
        current_--;
        column_--;
        return string();
    }
    // 运算符和分隔符
    else {
        current_--;
        column_--;
        return operatorToken();
    }
}

bool Lexer::hasMore() const {
    return !isAtEnd();
}

char Lexer::peek() const {
    if (isAtEnd()) return '\0';
    return source_[current_];
}

char Lexer::peekNext() const {
    if (current_ + 1 >= source_.size()) return '\0';
    return source_[current_ + 1];
}

char Lexer::advance() {
    char c = source_[current_++];
    if (c == '\n') {
        line_++;
        column_ = 1;
    } else {
        column_++;
    }
    return c;
}

bool Lexer::match(char expected) {
    if (isAtEnd()) return false;
    if (source_[current_] != expected) return false;

    current_++;
    if (expected == '\n') {
        line_++;
        column_ = 1;
    } else {
        column_++;
    }
    return true;
}

void Lexer::skipWhitespace() {
    while (!isAtEnd()) {
        char c = peek();
        if (c == ' ' || c == '\t' || c == '\r') {
            advance();
        } else if (c == '\n') {
            // 可选：将换行作为token
            advance();
        } else {
            break;
        }
    }
}

bool Lexer::skipComment() {
    if (isAtEnd()) return false;

    // 单行注释 //
    if (peek() == '/' && peekNext() == '/') {
        advance(); // 消耗第一个 /
        advance(); // 消耗第二个 /
        while (!isAtEnd() && peek() != '\n') {
            advance();
        }
        return true;
    }

    // 多行注释 /* ... */
    if (peek() == '/' && peekNext() == '*') {
        int startLine = line_;
        advance(); // 消耗 /
        advance(); // 消耗 *
        while (!isAtEnd()) {
            if (peek() == '*' && peekNext() == '/') {
                advance(); // 消耗 *
                advance(); // 消耗 /
                return true;
            }
            advance();
        }
        errors_.push_back("Unterminated comment starting at line " +
                          std::to_string(startLine));
        return true;
    }

    return false;
}

bool Lexer::isAtEnd() const {
    return current_ >= source_.size();
}

Token Lexer::makeToken(TokenType type, const std::string& lexeme) {
    return Token(type, lexeme, line_, column_ - lexeme.length());
}

Token Lexer::makeToken(TokenType type, const std::string& lexeme, TokenValue value) {
    return Token(type, lexeme, value, line_, column_ - lexeme.length());
}

Token Lexer::errorToken(const std::string& message) {
    errors_.push_back(message + " at line " + std::to_string(line_) +
                      ", column " + std::to_string(column_));
    return Token(TokenType::ERROR, message, line_, column_);
}

Token Lexer::identifier() {
    size_t start = current_;
    int startColumn = column_;

    while (!isAtEnd() && isAlphaNumeric(peek())) {
        advance();
    }

    std::string text = source_.substr(start, current_ - start);

    // 检查是否是关键字
    const auto& keywords = getKeywords();
    auto it = keywords.find(text);
    if (it != keywords.end()) {
        return Token(it->second, text, line_, startColumn);
    }

    return Token(TokenType::IDENTIFIER, text, line_, startColumn);
}

Token Lexer::number() {
    size_t start = current_;
    int startColumn = column_;
    bool isFloat = false;

    // 整数部分
    while (!isAtEnd() && isDigit(peek())) {
        advance();
    }

    // 小数部分
    if (!isAtEnd() && peek() == '.' && isDigit(peekNext())) {
        isFloat = true;
        advance(); // 消耗 .
        while (!isAtEnd() && isDigit(peek())) {
            advance();
        }
    }

    // 科学计数法
    if (!isAtEnd() && (peek() == 'e' || peek() == 'E')) {
        isFloat = true;
        advance();
        if (!isAtEnd() && (peek() == '+' || peek() == '-')) {
            advance();
        }
        while (!isAtEnd() && isDigit(peek())) {
            advance();
        }
    }

    std::string text = source_.substr(start, current_ - start);

    if (isFloat) {
        try {
            double value = std::stod(text);
            return Token(TokenType::FLOAT, text, value, line_, startColumn);
        } catch (const std::exception& e) {
            return errorToken("Invalid float literal: " + text);
        }
    } else {
        try {
            int64_t value = std::stoll(text);
            return Token(TokenType::INTEGER, text, value, line_, startColumn);
        } catch (const std::exception& e) {
            return errorToken("Invalid integer literal: " + text);
        }
    }
}

Token Lexer::string() {
    int startLine = line_;
    int startColumn = column_;
    char quote = advance(); // 消耗引号
    std::string value;

    while (!isAtEnd() && peek() != quote) {
        if (peek() == '\\') {
            advance(); // 消耗反斜杠
            if (isAtEnd()) break;

            char escaped = advance();
            switch (escaped) {
                case 'n': value += '\n'; break;
                case 't': value += '\t'; break;
                case 'r': value += '\r'; break;
                case '\\': value += '\\'; break;
                case '\'': value += '\''; break;
                case '"': value += '"'; break;
                case '0': value += '\0'; break;
                default:
                    value += '\\';
                    value += escaped;
                    break;
            }
        } else {
            value += advance();
        }
    }

    if (isAtEnd()) {
        return errorToken("Unterminated string starting at line " +
                          std::to_string(startLine));
    }

    advance(); // 消耗结束引号
    std::string lexeme = source_.substr(startColumn - 1, current_ - startColumn + 1);
    return Token(TokenType::STRING, lexeme, value, startLine, startColumn);
}

Token Lexer::operatorToken() {
    int startLine = line_;
    int startColumn = column_;
    char c = advance();

    switch (c) {
        case '+':
            if (match('+')) return Token(TokenType::INCREMENT, "++", startLine, startColumn);
            if (match('=')) return Token(TokenType::PLUS_ASSIGN, "+=", startLine, startColumn);
            return Token(TokenType::PLUS, "+", startLine, startColumn);

        case '-':
            if (match('-')) return Token(TokenType::DECREMENT, "--", startLine, startColumn);
            if (match('=')) return Token(TokenType::MINUS_ASSIGN, "-=", startLine, startColumn);
            if (match('>')) return Token(TokenType::ARROW, "->", startLine, startColumn);
            return Token(TokenType::MINUS, "-", startLine, startColumn);

        case '*':
            if (match('*')) return Token(TokenType::POWER, "**", startLine, startColumn);
            if (match('=')) return Token(TokenType::MUL_ASSIGN, "*=", startLine, startColumn);
            return Token(TokenType::MULTIPLY, "*", startLine, startColumn);

        case '/':
            if (match('=')) return Token(TokenType::DIV_ASSIGN, "/=", startLine, startColumn);
            return Token(TokenType::DIVIDE, "/", startLine, startColumn);

        case '%':
            return Token(TokenType::MODULO, "%", startLine, startColumn);

        case '=':
            if (match('=')) return Token(TokenType::EQUAL, "==", startLine, startColumn);
            return Token(TokenType::ASSIGN, "=", startLine, startColumn);

        case '!':
            if (match('=')) return Token(TokenType::NOT_EQUAL, "!=", startLine, startColumn);
            return Token(TokenType::NOT, "!", startLine, startColumn);

        case '<':
            if (match('=')) return Token(TokenType::LESS_EQUAL, "<=", startLine, startColumn);
            if (match('<')) return Token(TokenType::SHIFT_LEFT, "<<", startLine, startColumn);
            return Token(TokenType::LESS, "<", startLine, startColumn);

        case '>':
            if (match('=')) return Token(TokenType::GREATER_EQUAL, ">=", startLine, startColumn);
            if (match('>')) return Token(TokenType::SHIFT_RIGHT, ">>", startLine, startColumn);
            return Token(TokenType::GREATER, ">", startLine, startColumn);

        case '&':
            if (match('&')) return Token(TokenType::AND, "&&", startLine, startColumn);
            return Token(TokenType::BIT_AND, "&", startLine, startColumn);

        case '|':
            if (match('|')) return Token(TokenType::OR, "||", startLine, startColumn);
            return Token(TokenType::BIT_OR, "|", startLine, startColumn);

        case '^':
            return Token(TokenType::BIT_XOR, "^", startLine, startColumn);

        case '~':
            return Token(TokenType::BIT_NOT, "~", startLine, startColumn);

        case '(':
            return Token(TokenType::LEFT_PAREN, "(", startLine, startColumn);

        case ')':
            return Token(TokenType::RIGHT_PAREN, ")", startLine, startColumn);

        case '{':
            return Token(TokenType::LEFT_BRACE, "{", startLine, startColumn);

        case '}':
            return Token(TokenType::RIGHT_BRACE, "}", startLine, startColumn);

        case '[':
            return Token(TokenType::LEFT_BRACKET, "[", startLine, startColumn);

        case ']':
            return Token(TokenType::RIGHT_BRACKET, "]", startLine, startColumn);

        case ',':
            return Token(TokenType::COMMA, ",", startLine, startColumn);

        case '.':
            return Token(TokenType::DOT, ".", startLine, startColumn);

        case ';':
            return Token(TokenType::SEMICOLON, ";", startLine, startColumn);

        case ':':
            if (match(':')) return Token(TokenType::DOUBLE_COLON, "::", startLine, startColumn);
            return Token(TokenType::COLON, ":", startLine, startColumn);

        case '\n':
            return Token(TokenType::NEWLINE, "\\n", startLine, startColumn);

        default:
            return errorToken(std::string("Unexpected character: ") + c);
    }
}

bool Lexer::isAlpha(char c) const {
    return std::isalpha(c) || c == '_';
}

bool Lexer::isDigit(char c) const {
    return std::isdigit(c);
}

bool Lexer::isAlphaNumeric(char c) const {
    return isAlpha(c) || isDigit(c);
}

} // namespace compiler
