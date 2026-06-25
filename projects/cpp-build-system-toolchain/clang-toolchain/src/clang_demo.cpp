#include <iostream>
#include <memory>
#include <string>
#include <vector>
#include <optional>
#include <variant>

/**
 * @file clang_demo.cpp
 * @brief Clang 工具链示例
 *
 * 演示 Clang 编译器的各种特性和选项。
 * Clang 以其快速编译、友好的错误信息和丰富的工具链而闻名。
 */

// 演示 [[nodiscard]] 属性
[[nodiscard]] std::optional<int> parse_int(const std::string& str) {
    try {
        return std::stoi(str);
    } catch (...) {
        return std::nullopt;
    }
}

// 演示 std::variant
using Value = std::variant<int, double, std::string>;

std::string value_to_string(const Value& val) {
    return std::visit([](const auto& v) -> std::string {
        using T = std::decay_t<decltype(v)>;
        if constexpr (std::is_same_v<T, int>) {
            return "int: " + std::to_string(v);
        } else if constexpr (std::is_same_v<T, double>) {
            return "double: " + std::to_string(v);
        } else if constexpr (std::is_same_v<T, std::string>) {
            return "string: " + v;
        }
    }, val);
}

// 演示智能指针
class Resource {
public:
    Resource(const std::string& name) : name_(name) {
        std::cout << "Resource '" << name_ << "' 创建" << std::endl;
    }
    ~Resource() {
        std::cout << "Resource '" << name_ << "' 销毁" << std::endl;
    }
    void use() const {
        std::cout << "使用 Resource '" << name_ << "'" << std::endl;
    }
private:
    std::string name_;
};

// 演示结构化绑定
struct Point {
    double x;
    double y;
};

Point get_origin() {
    return {0.0, 0.0};
}

int main() {
    std::cout << "=== Clang 工具链示例 ===" << std::endl;
    std::cout << std::endl;

    // 编译器信息
    std::cout << "编译器信息:" << std::endl;
#ifdef __clang__
    std::cout << "  Clang 版本: " << __clang_major__ << "." << __clang_minor__ << "." << __clang_patchlevel__ << std::endl;
#endif
    std::cout << "  C++ 标准: " << __cplusplus << std::endl;
    std::cout << std::endl;

    // optional
    std::cout << "--- std::optional ---" << std::endl;
    auto val1 = parse_int("42");
    auto val2 = parse_int("abc");
    std::cout << "parse_int('42'): " << (val1 ? std::to_string(*val1) : "nullopt") << std::endl;
    std::cout << "parse_int('abc'): " << (val2 ? std::to_string(*val2) : "nullopt") << std::endl;

    // variant
    std::cout << std::endl;
    std::cout << "--- std::variant ---" << std::endl;
    std::vector<Value> values = {42, 3.14, std::string("hello")};
    for (const auto& v : values) {
        std::cout << value_to_string(v) << std::endl;
    }

    // 智能指针
    std::cout << std::endl;
    std::cout << "--- 智能指针 ---" << std::endl;
    {
        auto res = std::make_unique<Resource>("MyResource");
        res->use();
    }  // Resource 在这里自动销毁

    // 结构化绑定
    std::cout << std::endl;
    std::cout << "--- 结构化绑定 ---" << std::endl;
    auto [x, y] = get_origin();
    std::cout << "原点: (" << x << ", " << y << ")" << std::endl;

    std::cout << std::endl;
    std::cout << "Clang 工具链优势:" << std::endl;
    std::cout << "  - 编译速度快" << std::endl;
    std::cout << "  - 错误信息友好" << std::endl;
    std::cout << "  - 工具链丰富 (clang-tidy, clang-format, scan-build)" << std::endl;
    std::cout << "  - 支持 LLVM 后端优化" << std::endl;

    return 0;
}
