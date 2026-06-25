// =============================================================================
// visitor_pattern.cpp - 访问者模式演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o visitor visitor_pattern.cpp
// 运行: ./visitor
// =============================================================================

#include <iostream>
#include <string>
#include <variant>
#include <vector>
#include <memory>
#include "utilities/visitor.hpp"

int main() {
    std::cout << "=== 访问者模式演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. Overloaded 模式
    std::cout << "1. Overloaded 模式 (variant visit):" << std::endl;
    std::variant<int, double, std::string> v1 = 42;
    std::variant<int, double, std::string> v2 = 3.14;
    std::variant<int, double, std::string> v3 = "hello";

    auto visitor = tmp::Overloaded{
        [](int i) { std::cout << "  int: " << i << std::endl; },
        [](double d) { std::cout << "  double: " << d << std::endl; },
        [](const std::string& s) { std::cout << "  string: " << s << std::endl; }
    };

    std::visit(visitor, v1);
    std::visit(visitor, v2);
    std::visit(visitor, v3);
    std::cout << std::endl;

    // 2. make_visitor 辅助函数
    std::cout << "2. make_visitor 辅助函数:" << std::endl;
    auto v = tmp::make_visitor(
        [](int i) { std::cout << "  Got int: " << i * 2 << std::endl; },
        [](double d) { std::cout << "  Got double: " << d * 2 << std::endl; },
        [](const std::string& s) { std::cout << "  Got string: " << s << std::endl; }
    );
    std::visit(v, v1);
    std::visit(v, v2);
    std::visit(v, v3);
    std::cout << std::endl;

    // 3. 递归访问者 - 表达式树
    std::cout << "3. 递归访问者 - 表达式树:" << std::endl;

    // 构建表达式: (2 + 3) * 4
    auto expr = std::make_unique<tmp::Expr>(tmp::Multiplication{
        std::make_unique<tmp::Expr>(tmp::Addition{
            std::make_unique<tmp::Expr>(tmp::Literal{2.0}),
            std::make_unique<tmp::Expr>(tmp::Literal{3.0})
        }),
        std::make_unique<tmp::Expr>(tmp::Literal{4.0})
    });

    // 求值
    tmp::Evaluator eval;
    double result = std::visit(eval, expr->data);
    std::cout << "  (2 + 3) * 4 = " << result << std::endl;

    // 打印
    tmp::Printer printer;
    std::string repr = std::visit(printer, expr->data);
    std::cout << "  Expression: " << repr << std::endl;
    std::cout << std::endl;

    // 4. 复杂表达式
    std::cout << "4. 复杂表达式:" << std::endl;

    // -(2 + 3) * 4
    auto complex_expr = std::make_unique<tmp::Expr>(tmp::Negation{
        std::make_unique<tmp::Expr>(tmp::Multiplication{
            std::make_unique<tmp::Expr>(tmp::Addition{
                std::make_unique<tmp::Expr>(tmp::Literal{2.0}),
                std::make_unique<tmp::Expr>(tmp::Literal{3.0})
            }),
            std::make_unique<tmp::Expr>(tmp::Literal{4.0})
        })
    });

    result = std::visit(eval, complex_expr->data);
    std::cout << "  -(2 + 3) * 4 = " << result << std::endl;

    repr = std::visit(printer, complex_expr->data);
    std::cout << "  Expression: " << repr << std::endl;
    std::cout << std::endl;

    // 5. variant 类型检查
    std::cout << "5. variant 类型检查:" << std::endl;
    using MyVariant = std::variant<int, double, std::string>;
    std::cout << "  variant contains int: "
              << tmp::variant_contains_v<MyVariant, int> << std::endl;
    std::cout << "  variant contains float: "
              << tmp::variant_contains_v<MyVariant, float> << std::endl;
    std::cout << "  variant contains string: "
              << tmp::variant_contains_v<MyVariant, std::string> << std::endl;
    std::cout << std::endl;

    // 6. 实际应用：JSON 值模拟
    std::cout << "6. 实际应用 - JSON 值模拟:" << std::endl;

    struct JsonNull {};
    using JsonValue = std::variant<
        std::nullptr_t,
        bool,
        int,
        double,
        std::string,
        std::vector<int>  // 简化：只支持 int 数组
    >;

    std::vector<JsonValue> json_array;
    json_array.push_back(nullptr);
    json_array.push_back(true);
    json_array.push_back(42);
    json_array.push_back(3.14);
    json_array.push_back(std::string("hello"));
    json_array.push_back(std::vector<int>{1, 2, 3});

    auto json_visitor = tmp::Overloaded{
        [](std::nullptr_t) { std::cout << "  null" << std::endl; },
        [](bool b) { std::cout << "  bool: " << std::boolalpha << b << std::endl; },
        [](int i) { std::cout << "  int: " << i << std::endl; },
        [](double d) { std::cout << "  double: " << d << std::endl; },
        [](const std::string& s) { std::cout << "  string: \"" << s << "\"" << std::endl; },
        [](const std::vector<int>& v) {
            std::cout << "  array: [";
            for (std::size_t i = 0; i < v.size(); ++i) {
                if (i > 0) std::cout << ", ";
                std::cout << v[i];
            }
            std::cout << "]" << std::endl;
        }
    };

    for (const auto& val : json_array) {
        std::visit(json_visitor, val);
    }
    std::cout << std::endl;

    // 7. 编译期分发
    std::cout << "7. 编译期分发:" << std::endl;
    std::variant<int, double, std::string> val = 42;

    tmp::compile_time_visit(val, [](auto&& arg) {
        using T = std::decay_t<decltype(arg)>;
        if constexpr (std::is_same_v<T, int>) {
            std::cout << "  Compile-time dispatch: int = " << arg << std::endl;
        } else if constexpr (std::is_same_v<T, double>) {
            std::cout << "  Compile-time dispatch: double = " << arg << std::endl;
        } else if constexpr (std::is_same_v<T, std::string>) {
            std::cout << "  Compile-time dispatch: string = " << arg << std::endl;
        }
    });
    std::cout << std::endl;

    std::cout << "=== 访问者模式演示完成 ===" << std::endl;
    return 0;
}
