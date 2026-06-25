/**
 * DSL (Domain Specific Language) 示例
 *
 * 演示如何使用编译器构建领域特定语言
 * 示例：简单的配置语言
 */

#include "lexer.hpp"
#include "parser.hpp"
#include "interpreter.hpp"

#include <iostream>
#include <string>
#include <sstream>
#include <functional>
#include <unordered_map>

using namespace compiler;

/**
 * 配置DSL解释器
 */
class ConfigDSL {
public:
    ConfigDSL() {
        // 注册内置函数
        registerBuiltins();
    }

    /**
     * 解析配置文件
     */
    bool parse(const std::string& source) {
        // 词法分析
        Lexer lexer(source);
        auto tokens = lexer.tokenize();

        if (!lexer.getErrors().empty()) {
            for (const auto& error : lexer.getErrors()) {
                std::cerr << "Lexer error: " << error << std::endl;
            }
            return false;
        }

        // 语法分析
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        if (!parser.getErrors().empty()) {
            for (const auto& error : parser.getErrors()) {
                std::cerr << "Parser error: " << error << std::endl;
            }
            return false;
        }

        // 解释执行
        Interpreter interpreter;
        if (!interpreter.interpret(*ast)) {
            for (const auto& error : interpreter.getErrors()) {
                std::cerr << "Runtime error: " << error << std::endl;
            }
            return false;
        }

        return true;
    }

    /**
     * 获取配置值
     */
    std::string getString(const std::string& key) const {
        auto it = config_.find(key);
        return it != config_.end() ? it->second : "";
    }

    int getInt(const std::string& key) const {
        auto it = config_.find(key);
        if (it != config_.end()) {
            try {
                return std::stoi(it->second);
            } catch (...) {}
        }
        return 0;
    }

    bool getBool(const std::string& key) const {
        auto it = config_.find(key);
        if (it != config_.end()) {
            return it->second == "true" || it->second == "1";
        }
        return false;
    }

    /**
     * 打印所有配置
     */
    void printConfig() const {
        std::cout << "Configuration:" << std::endl;
        for (const auto& [key, value] : config_) {
            std::cout << "  " << key << " = " << value << std::endl;
        }
    }

private:
    std::unordered_map<std::string, std::string> config_;

    void registerBuiltins() {
        // 这些函数会在解释器中被调用
    }
};

/**
 * 查询DSL解释器
 */
class QueryDSL {
public:
    QueryDSL() = default;

    /**
     * 执行查询
     */
    bool execute(const std::string& query) {
        // 将查询转换为可执行的代码
        std::string source = transformQuery(query);

        // 词法分析
        Lexer lexer(source);
        auto tokens = lexer.tokenize();

        if (!lexer.getErrors().empty()) {
            for (const auto& error : lexer.getErrors()) {
                std::cerr << "Lexer error: " << error << std::endl;
            }
            return false;
        }

        // 语法分析
        Parser parser(std::move(tokens));
        auto ast = parser.parse();

        if (!parser.getErrors().empty()) {
            for (const auto& error : parser.getErrors()) {
                std::cerr << "Parser error: " << error << std::endl;
            }
            return false;
        }

        // 解释执行
        Interpreter interpreter;
        if (!interpreter.interpret(*ast)) {
            for (const auto& error : interpreter.getErrors()) {
                std::cerr << "Runtime error: " << error << std::endl;
            }
            return false;
        }

        return true;
    }

private:
    /**
     * 将查询DSL转换为通用语言
     */
    std::string transformQuery(const std::string& query) {
        // 简单的DSL转换示例
        // SELECT name, age FROM users WHERE age > 18
        // =>
        // let users = [{name: "Alice", age: 25}, ...];
        // for (let i = 0; i < len(users); i++) {
        //     if (users[i].age > 18) {
        //         print(users[i].name, users[i].age);
        //     }
        // }

        // 这里简化处理，直接返回一个示例程序
        return R"QUERY(
            let users = [
                {"name": "Alice", "age": 25},
                {"name": "Bob", "age": 17},
                {"name": "Charlie", "age": 30},
                {"name": "Diana", "age": 15}
            ];

            print("Users older than 18:");
            for (let i = 0; i < len(users); i++) {
                if (users[i].age > 18) {
                    print("  -", users[i].name, "(age:", users[i].age, ")");
                }
            }
        )QUERY";
    }
};

/**
 * 测试配置DSL
 */
void testConfigDSL() {
    std::cout << "=== Configuration DSL ===" << std::endl;
    std::cout << std::endl;

    ConfigDSL config;

    std::string source = R"(
        // 应用配置
        let app_name = "My Application";
        let app_version = "1.0.0";
        let debug_mode = true;
        let max_connections = 100;

        // 数据库配置
        let db_host = "localhost";
        let db_port = 5432;
        let db_name = "mydb";

        print("Application: " + app_name + " v" + app_version);
        print("Debug mode:", debug_mode);
        print("Max connections:", max_connections);
        print("Database:", db_host + ":" + str(db_port) + "/" + db_name);
    )";

    config.parse(source);
    std::cout << std::endl;
}

/**
 * 测试查询DSL
 */
void testQueryDSL() {
    std::cout << "=== Query DSL ===" << std::endl;
    std::cout << std::endl;

    QueryDSL query;

    std::string q = "SELECT name, age FROM users WHERE age > 18";
    std::cout << "Query: " << q << std::endl;
    std::cout << std::endl;

    query.execute(q);
    std::cout << std::endl;
}

/**
 * 测试数学DSL
 */
void testMathDSL() {
    std::cout << "=== Math DSL ===" << std::endl;
    std::cout << std::endl;

    std::string source = R"(
        // 数学函数库
        fn square(x: float): float {
            return x * x;
        }

        fn cube(x: float): float {
            return x * x * x;
        }

        fn factorial(n: int): int {
            if (n <= 1) {
                return 1;
            }
            return n * factorial(n - 1);
        }

        fn is_prime(n: int): bool {
            if (n < 2) {
                return false;
            }
            for (let i = 2; i * i <= n; i++) {
                if (n % i == 0) {
                    return false;
                }
            }
            return true;
        }

        // 使用函数
        print("Math Examples:");
        print("  square(5) =", square(5));
        print("  cube(3) =", cube(3));
        print("  factorial(10) =", factorial(10));

        print("  Prime numbers up to 20:");
        for (let i = 2; i <= 20; i++) {
            if (is_prime(i)) {
                print("   ", i);
            }
        }
    )";

    Lexer lexer(source);
    auto tokens = lexer.tokenize();

    Parser parser(std::move(tokens));
    auto ast = parser.parse();

    Interpreter interpreter;
    interpreter.interpret(*ast);

    std::cout << std::endl;
}

int main() {
    std::cout << "DSL (Domain Specific Language) Examples" << std::endl;
    std::cout << "=======================================" << std::endl;
    std::cout << std::endl;

    testConfigDSL();
    testQueryDSL();
    testMathDSL();

    std::cout << "All DSL examples completed." << std::endl;

    return 0;
}
