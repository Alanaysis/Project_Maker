/**
 * 简易编译器 - 主程序
 *
 * 功能：
 * 1. 读取源代码文件或从标准输入读取
 * 2. 执行词法分析、语法分析、语义分析
 * 3. 生成中间代码和优化
 * 4. 解释执行或生成汇编代码
 */

#include "lexer.hpp"
#include "parser.hpp"
#include "semantic.hpp"
#include "ir.hpp"
#include "optimizer.hpp"
#include "codegen.hpp"
#include "interpreter.hpp"

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>

using namespace compiler;

/**
 * 打印使用说明
 */
void printUsage(const char* programName) {
    std::cout << "Simple Compiler v1.0" << std::endl;
    std::cout << "Usage: " << programName << " [options] [file]" << std::endl;
    std::cout << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  -h, --help        Show this help message" << std::endl;
    std::cout << "  -l, --lex         Show tokens (lexer output)" << std::endl;
    std::cout << "  -p, --parse       Show AST (parser output)" << std::endl;
    std::cout << "  -s, --semantic    Show semantic analysis" << std::endl;
    std::cout << "  -i, --ir          Show intermediate representation" << std::endl;
    std::cout << "  -o, --optimize    Show optimized IR" << std::endl;
    std::cout << "  -c, --codegen     Show generated assembly" << std::endl;
    std::cout << "  -r, --run         Run the program (default)" << std::endl;
    std::cout << "  -a, --all         Show all stages" << std::endl;
    std::cout << "  -e, --eval EXPR   Evaluate expression" << std::endl;
    std::cout << std::endl;
    std::cout << "If no file is given, reads from standard input." << std::endl;
}

/**
 * 读取文件内容
 */
std::string readFile(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Cannot open file '" << filename << "'" << std::endl;
        return "";
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

/**
 * 从标准输入读取
 */
std::string readStdin() {
    std::stringstream buffer;
    std::string line;

    std::cout << "Enter code (Ctrl+D to finish):" << std::endl;

    while (std::getline(std::cin, line)) {
        buffer << line << "\n";
    }

    return buffer.str();
}

/**
 * 交互式REPL
 */
void repl() {
    std::cout << "Simple Compiler REPL v1.0" << std::endl;
    std::cout << "Type 'exit' or 'quit' to exit." << std::endl;
    std::cout << std::endl;

    Interpreter interpreter;

    while (true) {
        std::cout << ">>> ";
        std::string line;

        if (!std::getline(std::cin, line)) {
            break;
        }

        if (line == "exit" || line == "quit") {
            break;
        }

        if (line.empty()) {
            continue;
        }

        // 词法分析
        Lexer lexer(line);
        auto tokens = lexer.tokenize();

        // 检查词法错误
        if (!lexer.getErrors().empty()) {
            for (const auto& error : lexer.getErrors()) {
                std::cerr << "Lexer error: " << error << std::endl;
            }
            continue;
        }

        // 语法分析
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        // 检查语法错误
        if (!parser.getErrors().empty()) {
            for (const auto& error : parser.getErrors()) {
                std::cerr << "Parse error: " << error << std::endl;
            }
            continue;
        }

        // 解释执行
        if (!interpreter.interpret(*ast)) {
            for (const auto& error : interpreter.getErrors()) {
                std::cerr << "Runtime error: " << error << std::endl;
            }
        }
    }

    std::cout << "Goodbye!" << std::endl;
}

/**
 * 编译和执行源代码
 */
int compileAndRun(const std::string& source, bool showLex, bool showParse,
                  bool showSemantic, bool showIR, bool showOptimize,
                  bool showCodegen, bool run) {
    // 1. 词法分析
    Lexer lexer(source);
    auto tokens = lexer.tokenize();

    if (!lexer.getErrors().empty()) {
        std::cerr << "Lexer errors:" << std::endl;
        for (const auto& error : lexer.getErrors()) {
            std::cerr << "  " << error << std::endl;
        }
        return 1;
    }

    if (showLex) {
        std::cout << "=== Tokens ===" << std::endl;
        for (const auto& token : tokens) {
            std::cout << "  " << token.typeToString()
                      << " '" << token.lexeme << "'"
                      << " at " << token.line << ":" << token.column
                      << std::endl;
        }
        std::cout << std::endl;
    }

    // 2. 语法分析
    Parser parser(std::move(tokens));
    auto ast = parser.parse();

    if (!parser.getErrors().empty()) {
        std::cerr << "Parser errors:" << std::endl;
        for (const auto& error : parser.getErrors()) {
            std::cerr << "  " << error << std::endl;
        }
        return 1;
    }

    if (showParse) {
        std::cout << "=== AST ===" << std::endl;
        ast->print();
        std::cout << std::endl;
    }

    // 3. 语义分析
    SemanticAnalyzer semanticAnalyzer;
    if (!semanticAnalyzer.analyze(*ast)) {
        std::cerr << "Semantic errors:" << std::endl;
        for (const auto& error : semanticAnalyzer.getErrors()) {
            std::cerr << "  " << error << std::endl;
        }
        return 1;
    }

    if (showSemantic) {
        std::cout << "=== Semantic Analysis ===" << std::endl;
        std::cout << "  No errors found." << std::endl;
        if (!semanticAnalyzer.getWarnings().empty()) {
            std::cout << "  Warnings:" << std::endl;
            for (const auto& warning : semanticAnalyzer.getWarnings()) {
                std::cout << "    " << warning << std::endl;
            }
        }
        std::cout << std::endl;
    }

    // 4. 生成中间代码
    IRGenerator irGenerator;
    auto irModule = irGenerator.generate(*ast);

    if (showIR) {
        std::cout << "=== Intermediate Representation ===" << std::endl;
        irModule->print();
        std::cout << std::endl;
    }

    // 5. 优化
    Optimizer optimizer;
    optimizer.addPass(std::make_unique<ConstantFoldingPass>());
    optimizer.addPass(std::make_unique<DeadCodeEliminationPass>());
    optimizer.addPass(std::make_unique<StrengthReductionPass>());

    optimizer.optimize(*irModule);

    if (showOptimize) {
        std::cout << "=== Optimized IR ===" << std::endl;
        irModule->print();
        std::cout << std::endl;

        auto stats = optimizer.getStats();
        std::cout << "Optimization stats:" << std::endl;
        std::cout << "  Total passes: " << stats.totalPasses << std::endl;
        std::cout << "  Total modifications: " << stats.totalModifications << std::endl;
        std::cout << std::endl;
    }

    // 6. 代码生成
    CodeGenerator codeGenerator;
    std::string assembly = codeGenerator.generate(*irModule);

    if (showCodegen) {
        std::cout << "=== Generated Assembly ===" << std::endl;
        std::cout << assembly << std::endl;
    }

    // 7. 解释执行
    if (run) {
        std::cout << "=== Execution Output ===" << std::endl;
        Interpreter interpreter;
        if (!interpreter.interpret(*ast)) {
            std::cerr << "Runtime errors:" << std::endl;
            for (const auto& error : interpreter.getErrors()) {
                std::cerr << "  " << error << std::endl;
            }
            return 1;
        }
    }

    return 0;
}

int main(int argc, char* argv[]) {
    // 解析命令行参数
    bool showLex = false;
    bool showParse = false;
    bool showSemantic = false;
    bool showIR = false;
    bool showOptimize = false;
    bool showCodegen = false;
    bool run = true;
    bool interactive = false;
    std::string evalExpr;
    std::string filename;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg == "-h" || arg == "--help") {
            printUsage(argv[0]);
            return 0;
        } else if (arg == "-l" || arg == "--lex") {
            showLex = true;
            run = false;
        } else if (arg == "-p" || arg == "--parse") {
            showParse = true;
            run = false;
        } else if (arg == "-s" || arg == "--semantic") {
            showSemantic = true;
            run = false;
        } else if (arg == "-i" || arg == "--ir") {
            showIR = true;
            run = false;
        } else if (arg == "-o" || arg == "--optimize") {
            showOptimize = true;
            run = false;
        } else if (arg == "-c" || arg == "--codegen") {
            showCodegen = true;
            run = false;
        } else if (arg == "-r" || arg == "--run") {
            run = true;
        } else if (arg == "-a" || arg == "--all") {
            showLex = true;
            showParse = true;
            showSemantic = true;
            showIR = true;
            showOptimize = true;
            showCodegen = true;
            run = true;
        } else if (arg == "-e" || arg == "--eval") {
            if (i + 1 < argc) {
                evalExpr = argv[++i];
            } else {
                std::cerr << "Error: --eval requires an expression" << std::endl;
                return 1;
            }
        } else if (arg[0] != '-') {
            filename = arg;
        } else {
            std::cerr << "Unknown option: " << arg << std::endl;
            printUsage(argv[0]);
            return 1;
        }
    }

    // 评估表达式
    if (!evalExpr.empty()) {
        return compileAndRun(evalExpr, showLex, showParse, showSemantic,
                            showIR, showOptimize, showCodegen, true);
    }

    // 交互式模式
    if (filename.empty() && !showLex && !showParse && !showSemantic &&
        !showIR && !showOptimize && !showCodegen) {
        repl();
        return 0;
    }

    // 读取源代码
    std::string source;
    if (filename.empty()) {
        source = readStdin();
    } else {
        source = readFile(filename);
        if (source.empty()) {
            return 1;
        }
    }

    // 编译和运行
    return compileAndRun(source, showLex, showParse, showSemantic,
                        showIR, showOptimize, showCodegen, run);
}
