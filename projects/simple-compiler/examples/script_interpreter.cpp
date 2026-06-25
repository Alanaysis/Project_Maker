/**
 * 脚本解释器示例
 *
 * 演示如何使用编译器构建一个脚本语言解释器
 * 支持：变量、函数、控制流、数组、类
 */

#include "lexer.hpp"
#include "parser.hpp"
#include "semantic.hpp"
#include "interpreter.hpp"

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>

using namespace compiler;

/**
 * 脚本解释器类
 */
class ScriptInterpreter {
public:
    ScriptInterpreter() = default;

    /**
     * 执行脚本文件
     */
    bool executeFile(const std::string& filename) {
        // 读取文件
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Error: Cannot open file '" << filename << "'" << std::endl;
            return false;
        }

        std::stringstream buffer;
        buffer << file.rdbuf();
        std::string source = buffer.str();

        return execute(source);
    }

    /**
     * 执行源代码
     */
    bool execute(const std::string& source) {
        // 词法分析
        Lexer lexer(source);
        auto tokens = lexer.tokenize();

        if (!lexer.getErrors().empty()) {
            std::cerr << "Lexer errors:" << std::endl;
            for (const auto& error : lexer.getErrors()) {
                std::cerr << "  " << error << std::endl;
            }
            return false;
        }

        // 语法分析
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        if (!parser.getErrors().empty()) {
            std::cerr << "Parser errors:" << std::endl;
            for (const auto& error : parser.getErrors()) {
                std::cerr << "  " << error << std::endl;
            }
            return false;
        }

        // 语义分析
        SemanticAnalyzer semanticAnalyzer;
        if (!semanticAnalyzer.analyze(*ast)) {
            std::cerr << "Semantic errors:" << std::endl;
            for (const auto& error : semanticAnalyzer.getErrors()) {
                std::cerr << "  " << error << std::endl;
            }
            return false;
        }

        // 解释执行
        Interpreter interpreter;
        if (!interpreter.interpret(*ast)) {
            std::cerr << "Runtime errors:" << std::endl;
            for (const auto& error : interpreter.getErrors()) {
                std::cerr << "  " << error << std::endl;
            }
            return false;
        }

        return true;
    }

    /**
     * 运行交互式解释器
     */
    void runREPL() {
        std::cout << "Simple Script Interpreter v1.0" << std::endl;
        std::cout << "Type 'help' for commands, 'exit' to quit." << std::endl;
        std::cout << std::endl;

        Interpreter interpreter;
        std::string buffer;

        while (true) {
            if (buffer.empty()) {
                std::cout << ">>> ";
            } else {
                std::cout << "... ";
            }

            std::string line;
            if (!std::getline(std::cin, line)) {
                break;
            }

            // 处理命令
            if (buffer.empty()) {
                if (line == "exit" || line == "quit") {
                    break;
                }

                if (line == "help") {
                    printHelp();
                    continue;
                }

                if (line == "run") {
                    runExamples();
                    continue;
                }
            }

            // 检查是否是多行输入（以{结尾）
            buffer += line + "\n";

            // 简单的括号匹配检查
            int braces = 0;
            for (char c : buffer) {
                if (c == '{') braces++;
                if (c == '}') braces--;
            }

            // 如果括号不匹配，继续读取
            if (braces > 0) {
                continue;
            }

            // 执行代码
            try {
                // 词法分析
                Lexer lexer(buffer);
                auto tokens = lexer.tokenize();

                // 语法分析
                Parser parser(std::move(tokens));
                auto ast = parser.parse();

                // 解释执行
                if (!interpreter.interpret(*ast)) {
                    for (const auto& error : interpreter.getErrors()) {
                        std::cerr << "Error: " << error << std::endl;
                    }
                }
            } catch (const std::exception& e) {
                std::cerr << "Error: " << e.what() << std::endl;
            }

            buffer.clear();
        }

        std::cout << "Goodbye!" << std::endl;
    }

private:
    void printHelp() {
        std::cout << "Simple Script Language Reference:" << std::endl;
        std::cout << std::endl;

        std::cout << "Variables:" << std::endl;
        std::cout << "  let x = 10;          // immutable variable" << std::endl;
        std::cout << "  var y = 20;          // mutable variable" << std::endl;
        std::cout << "  const PI = 3.14;     // constant" << std::endl;
        std::cout << std::endl;

        std::cout << "Data Types:" << std::endl;
        std::cout << "  42                   // integer" << std::endl;
        std::cout << "  3.14                 // float" << std::endl;
        std::cout << "  \"hello\"             // string" << std::endl;
        std::cout << "  true, false          // boolean" << std::endl;
        std::cout << "  [1, 2, 3]            // array" << std::endl;
        std::cout << std::endl;

        std::cout << "Functions:" << std::endl;
        std::cout << "  fn add(a: int, b: int): int {" << std::endl;
        std::cout << "    return a + b;" << std::endl;
        std::cout << "  }" << std::endl;
        std::cout << std::endl;

        std::cout << "Control Flow:" << std::endl;
        std::cout << "  if (x > 0) { ... } else { ... }" << std::endl;
        std::cout << "  while (x > 0) { x = x - 1; }" << std::endl;
        std::cout << "  for (let i = 0; i < 10; i++) { ... }" << std::endl;
        std::cout << std::endl;

        std::cout << "Built-in Functions:" << std::endl;
        std::cout << "  print(...)           // print values" << std::endl;
        std::cout << "  len(arr)             // array/string length" << std::endl;
        std::cout << "  str(x)               // convert to string" << std::endl;
        std::cout << "  int(x)               // convert to integer" << std::endl;
        std::cout << "  float(x)             // convert to float" << std::endl;
        std::cout << "  abs(x)               // absolute value" << std::endl;
        std::cout << "  sqrt(x)              // square root" << std::endl;
        std::cout << "  pow(x, y)            // power" << std::endl;
        std::cout << std::endl;

        std::cout << "Commands:" << std::endl;
        std::cout << "  help                 // show this help" << std::endl;
        std::cout << "  run                  // run example programs" << std::endl;
        std::cout << "  exit, quit           // exit interpreter" << std::endl;
        std::cout << std::endl;
    }

    void runExamples() {
        std::cout << "Running example programs..." << std::endl;
        std::cout << std::endl;

        // 示例1：Hello World
        std::cout << "=== Example 1: Hello World ===" << std::endl;
        execute("print(\"Hello, World!\");");
        std::cout << std::endl;

        // 示例2：变量和运算
        std::cout << "=== Example 2: Variables and Arithmetic ===" << std::endl;
        execute(R"(
            let x = 10;
            let y = 20;
            print("x =", x);
            print("y =", y);
            print("x + y =", x + y);
            print("x * y =", x * y);
        )");
        std::cout << std::endl;

        // 示例3：函数
        std::cout << "=== Example 3: Functions ===" << std::endl;
        execute(R"(
            fn fibonacci(n: int): int {
                if (n <= 1) {
                    return n;
                }
                return fibonacci(n - 1) + fibonacci(n - 2);
            }

            for (let i = 0; i < 10; i++) {
                print("fibonacci(", i, ") =", fibonacci(i));
            }
        )");
        std::cout << std::endl;

        // 示例4：数组
        std::cout << "=== Example 4: Arrays ===" << std::endl;
        execute(R"(
            let arr = [5, 3, 8, 1, 9, 2, 7, 4, 6];
            print("Array:", arr);
            print("Length:", len(arr));

            // 找最大值
            let max = arr[0];
            for (let i = 1; i < len(arr); i++) {
                if (arr[i] > max) {
                    max = arr[i];
                }
            }
            print("Max:", max);
        )");
        std::cout << std::endl;

        // 示例5：字符串
        std::cout << "=== Example 5: Strings ===" << std::endl;
        execute(R"(
            let name = "World";
            let greeting = "Hello, " + name + "!";
            print(greeting);
            print("Length:", len(greeting));

            // 字符串重复
            fn repeat(s: string, n: int): string {
                let result = "";
                for (let i = 0; i < n; i++) {
                    result = result + s;
                }
                return result;
            }

            print(repeat("*", 20));
        )");
        std::cout << std::endl;

        std::cout << "Examples completed." << std::endl;
    }
};

int main(int argc, char* argv[]) {
    ScriptInterpreter interpreter;

    if (argc > 1) {
        // 执行脚本文件
        return interpreter.executeFile(argv[1]) ? 0 : 1;
    } else {
        // 交互式模式
        interpreter.runREPL();
    }

    return 0;
}
