#include "parser.h"
#include <cctype>
#include <stack>
#include <stdexcept>

namespace parser {

std::optional<int> parse_int(const std::string& input) {
    if (input.empty()) return std::nullopt;

    size_t start = 0;
    bool negative = false;

    if (input[0] == '-') {
        negative = true;
        start = 1;
    } else if (input[0] == '+') {
        start = 1;
    }

    if (start >= input.size()) return std::nullopt;

    int result = 0;
    for (size_t i = start; i < input.size(); ++i) {
        if (!std::isdigit(input[i])) return std::nullopt;
        result = result * 10 + (input[i] - '0');
    }

    return negative ? -result : result;
}

std::optional<double> parse_expression(const std::string& input) {
    if (input.empty()) return std::nullopt;

    // 简单解析: number op number
    size_t op_pos = std::string::npos;
    for (size_t i = 1; i < input.size(); ++i) {
        if (input[i] == '+' || input[i] == '-' || input[i] == '*' || input[i] == '/') {
            op_pos = i;
            break;
        }
    }

    if (op_pos == std::string::npos) {
        // 没有操作符，尝试解析为数字
        try {
            return std::stod(input);
        } catch (...) {
            return std::nullopt;
        }
    }

    std::string left_str = input.substr(0, op_pos);
    std::string right_str = input.substr(op_pos + 1);

    try {
        double left = std::stod(left_str);
        double right = std::stod(right_str);

        switch (input[op_pos]) {
            case '+': return left + right;
            case '-': return left - right;
            case '*': return left * right;
            case '/':
                if (right == 0) return std::nullopt;
                return left / right;
            default: return std::nullopt;
        }
    } catch (...) {
        return std::nullopt;
    }
}

bool validate_parentheses(const std::string& input) {
    int count = 0;
    for (char c : input) {
        if (c == '(') count++;
        else if (c == ')') count--;
        if (count < 0) return false;
    }
    return count == 0;
}

std::optional<double> parse_paren_expression(const std::string& input) {
    if (!validate_parentheses(input)) return std::nullopt;

    // 移除外层括号
    std::string expr = input;
    while (!expr.empty() && expr.front() == '(' && expr.back() == ')') {
        expr = expr.substr(1, expr.size() - 2);
    }

    return parse_expression(expr);
}

}  // namespace parser
