/**
 * 计算器示例
 *
 * 演示如何使用编译器构建一个简单的计算器
 * 支持：+、-、*、/、%、**、括号、变量
 */

#include "lexer.hpp"
#include "parser.hpp"
#include "interpreter.hpp"

#include <iostream>
#include <string>
#include <sstream>

using namespace compiler;

/**
 * 计算器类
 */
class Calculator {
public:
    Calculator() = default;

    /**
     * 计算表达式
     */
    double evaluate(const std::string& expression) {
        // 包装成完整的语句
        std::string source = "print(" + expression + ");";

        // 词法分析
        Lexer lexer(source);
        auto tokens = lexer.tokenize();

        if (!lexer.getErrors().empty()) {
            throw std::runtime_error("Lexer error: " + lexer.getErrors()[0]);
        }

        // 语法分析
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        if (!parser.getErrors().empty()) {
            throw std::runtime_error("Parser error: " + parser.getErrors()[0]);
        }

        // 解释执行
        Interpreter interpreter;
        if (!interpreter.interpret(*ast)) {
            throw std::runtime_error("Runtime error: " + interpreter.getErrors()[0]);
        }

        // 获取结果
        auto output = interpreter.getOutput();
        if (!output.empty()) {
            try {
                return std::stod(output[0]);
            } catch (...) {
                throw std::runtime_error("Invalid result: " + output[0]);
            }
        }

        return 0.0;
    }

    /**
     * 运行交互式计算器
     */
    void run() {
        std::cout << "Simple Calculator v1.0" << std::endl;
        std::cout << "支持: +, -, *, /, %, **, (), 变量" << std::endl;
        std::cout << "输入 'quit' 或 'exit' 退出" << std::endl;
        std::cout << "示例: 2 + 3 * 4, (1 + 2) ** 3, x = 10, x + 5" << std::endl;
        std::cout << std::endl;

        Interpreter interpreter;

        while (true) {
            std::cout << "calc> ";
            std::string line;

            if (!std::getline(std::cin, line)) {
                break;
            }

            if (line == "quit" || line == "exit") {
                break;
            }

            if (line.empty()) {
                continue;
            }

            // 特殊命令
            if (line == "help") {
                printHelp();
                continue;
            }

            if (line == "clear") {
                // 重置解释器
                interpreter = Interpreter();
                std::cout << "Variables cleared." << std::endl;
                continue;
            }

            try {
                // 检查是否是变量赋值
                bool isAssignment = false;
                for (size_t i = 0; i < line.size(); ++i) {
                    if (line[i] == '=' && (i == 0 || line[i-1] != '=' && line[i-1] != '!' &&
                        line[i-1] != '<' && line[i-1] != '>') &&
                        (i + 1 >= line.size() || line[i+1] != '=')) {
                        isAssignment = true;
                        break;
                    }
                }

                std::string source;
                if (isAssignment) {
                    source = line + ";";
                } else {
                    source = "print(" + line + ");";
                }

                // 词法分析
                Lexer lexer(source);
                auto tokens = lexer.tokenize();

                // 语法分析
                Parser parser(std::move(tokens));
                auto ast = parser.parse();

                // 执行
                if (!interpreter.interpret(*ast)) {
                    for (const auto& error : interpreter.getErrors()) {
                        std::cerr << "Error: " << error << std::endl;
                    }
                }
            } catch (const std::exception& e) {
                std::cerr << "Error: " << e.what() << std::endl;
            }
        }

        std::cout << "Goodbye!" << std::endl;
    }

private:
    void printHelp() {
        std::cout << "Commands:" << std::endl;
        std::cout << "  help   - Show this help" << std::endl;
        std::cout << "  clear  - Clear all variables" << std::endl;
        std::cout << "  quit   - Exit calculator" << std::endl;
        std::cout << std::endl;
        std::cout << "Operators:" << std::endl;
        std::cout << "  +, -, *, /   - Basic arithmetic" << std::endl;
        std::cout << "  %            - Modulo" << std::endl;
        std::cout << "  **           - Power" << std::endl;
        std::cout << "  ()           - Parentheses" << std::endl;
        std::cout << std::endl;
        std::cout << "Examples:" << std::endl;
        std::cout << "  2 + 3        => 5" << std::endl;
        std::cout << "  2 ** 10      => 1024" << std::endl;
        std::cout << "  x = 10       => (stores 10 in x)" << std::endl;
        std::cout << "  x * 2 + 1    => 21" << std::endl;
        std::cout << std::endl;
    }
};

int main(int argc, char* argv[]) {
    Calculator calc;

    if (argc > 1) {
        // 命令行模式：计算参数中的表达式
        std::string expr;
        for (int i = 1; i < argc; ++i) {
            if (i > 1) expr += " ";
            expr += argv[i];
        }

        try {
            double result = calc.evaluate(expr);
            std::cout << result << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "Error: " << e.what() << std::endl;
            return 1;
        }
    } else {
        // 交互式模式
        calc.run();
    }

    return 0;
}
