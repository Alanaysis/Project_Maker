#include <iostream>
#include <vector>
#include <memory>
#include <algorithm>
#include <string>

/**
 * @file clang_tidy_demo.cpp
 * @brief Clang-Tidy 静态分析示例
 *
 * 演示 Clang-Tidy 能够检测的各种代码问题。
 * Clang-Tidy 是一个基于 Clang 的 C++ linter 和静态分析工具。
 *
 * 常用检查类别:
 * - bugprone-*: 可能的 bug
 * - cert-*: CERT 编码标准
 * - modernize-*: 现代 C++ 特性
 * - performance-*: 性能问题
 * - readability-*: 可读性问题
 * - cppcoreguidelines-*: C++ Core Guidelines
 */

// ============================================================================
// 1. modernize 检查示例
// ============================================================================

// 使用 auto 代替显式类型 (modernize-use-auto)
void modernize_auto() {
    // 不推荐:
    std::vector<int> v = {1, 2, 3};
    std::vector<int>::iterator it = v.begin();

    // 推荐:
    auto v2 = std::vector{1, 2, 3};
    auto it2 = v2.begin();

    (void)it;
    (void)it2;
}

// 使用 nullptr 代替 NULL (modernize-use-nullptr)
void modernize_nullptr() {
    // 不推荐:
    int* p1 = NULL;

    // 推荐:
    int* p2 = nullptr;

    (void)p1;
    (void)p2;
}

// 使用 range-based for (modernize-loop-convert)
void modernize_loop() {
    std::vector<int> v = {1, 2, 3, 4, 5};

    // 不推荐:
    for (size_t i = 0; i < v.size(); ++i) {
        (void)v[i];
    }

    // 推荐:
    for (const auto& item : v) {
        (void)item;
    }
}

// 使用 emplace 代替 insert (modernize-use-emplace)
void modernize_emplace() {
    std::vector<std::string> v;

    // 不推荐:
    v.push_back(std::string("hello"));

    // 推荐:
    v.emplace_back("hello");
}

// ============================================================================
// 2. bugprone 检查示例
// ============================================================================

// 避免整数除法 (bugprone-integer-division)
double bugprone_integer_division() {
    int a = 5;
    int b = 2;

    // 不推荐: 整数除法会丢失精度
    // double result = a / b;

    // 推荐: 显式转换
    double result = static_cast<double>(a) / b;
    return result;
}

// 避免悬空指针 (bugprone-dangling-handle)
void bugprone_dangling() {
    std::string str = "hello";
    // 不推荐: 引用可能悬空
    // const auto& ref = str;

    // 推荐: 使用值或确保生命周期
    auto copy = str;
    (void)copy;
}

// ============================================================================
// 3. performance 检查示例
// ============================================================================

// 避免不必要的拷贝 (performance-unnecessary-copy-initialization)
void performance_copy() {
    std::vector<int> v = {1, 2, 3};

    // 不推荐:
    // auto copy = v;  // 不必要的拷贝

    // 推荐: 使用 const 引用
    const auto& ref = v;
    (void)ref;
}

// 使用 reserve (performance-unnecessary-vector-reserve)
void performance_reserve() {
    std::vector<int> v;
    v.reserve(100);  // 预分配内存
    for (int i = 0; i < 100; ++i) {
        v.push_back(i);
    }
}

// ============================================================================
// 4. readability 检查示例
// ============================================================================

// 使用有意义的变量名 (readability-identifier-naming)
void readability_naming() {
    // 不推荐:
    int x = 42;

    // 推荐:
    int answer_to_everything = 42;

    (void)x;
    (void)answer_to_everything;
}

// 使用 braces (readability-braces-around-statements)
void readability_braces(int value) {
    // 不推荐:
    // if (value > 0) return;

    // 推荐:
    if (value > 0) {
        return;
    }
}

// ============================================================================
// 5. cppcoreguidelines 检查示例
// ============================================================================

// 使用 RAII (cppcoreguidelines-special-member-functions)
class Resource {
public:
    Resource() : data_(new int[100]) {}
    ~Resource() { delete[] data_; }

    // Rule of Five
    Resource(const Resource&) = delete;
    Resource& operator=(const Resource&) = delete;
    Resource(Resource&&) noexcept = default;
    Resource& operator=(Resource&&) noexcept = default;

private:
    int* data_;
};

int main() {
    std::cout << "=== Clang-Tidy 静态分析示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "Clang-Tidy 检查类别:" << std::endl;
    std::cout << "  - bugprone-*: 检测可能的 bug" << std::endl;
    std::cout << "  - cert-*: CERT 编码标准检查" << std::endl;
    std::cout << "  - modernize-*: 建议使用现代 C++ 特性" << std::endl;
    std::cout << "  - performance-*: 检测性能问题" << std::endl;
    std::cout << "  - readability-*: 检查代码可读性" << std::endl;
    std::cout << "  - cppcoreguidelines-*: C++ Core Guidelines" << std::endl;
    std::cout << std::endl;

    // 运行示例函数
    modernize_auto();
    modernize_nullptr();
    modernize_loop();
    modernize_emplace();
    bugprone_integer_division();
    performance_copy();
    performance_reserve();
    readability_naming();
    readability_braces(42);

    std::cout << "所有示例函数已执行。" << std::endl;
    std::cout << std::endl;

    std::cout << "Clang-Tidy 使用方法:" << std::endl;
    std::cout << "  1. 在 CMakeLists.txt 中设置 CMAKE_CXX_CLANG_TIDY" << std::endl;
    std::cout << "  2. 创建 .clang-tidy 配置文件" << std::endl;
    std::cout << "  3. 运行 cmake --build . 时自动检查" << std::endl;
    std::cout << "  4. 或手动运行: clang-tidy src/*.cpp" << std::endl;

    return 0;
}
