/**
 * @file attributes_example.cpp
 * @brief C++17 属性示例
 *
 * C++17 引入了多个标准属性，用于向编译器提供额外信息。
 * 主要属性包括：
 * - [[nodiscard]]: 函数返回值不应被忽略
 * - [[maybe_unused]]: 变量可能未使用
 * - [[fallthrough]]: switch 语句中故意贯穿
 *
 * 主要优势：
 * 1. 代码安全性 - 编译器可以帮助发现潜在问题
 * 2. 代码清晰 - 表达开发者的意图
 * 3. 工具支持 - IDE 和静态分析工具可以利用这些信息
 */

#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <memory>
#include <mutex>

// 1. [[nodiscard]] 属性
[[nodiscard]] int compute_value() {
    return 42;
}

[[nodiscard("Error code should be checked")]]
int perform_operation() {
    // 模拟可能失败的操作
    return 0;  // 0 表示成功
}

[[nodiscard]] std::optional<int> find_value(const std::vector<int>& vec, int target) {
    for (size_t i = 0; i < vec.size(); ++i) {
        if (vec[i] == target) {
            return static_cast<int>(i);
        }
    }
    return std::nullopt;
}

void nodiscard_example() {
    std::cout << "\n[[nodiscard]] 属性]" << std::endl;

    // 正确使用：接收返回值
    int value = compute_value();
    std::cout << "compute_value() = " << value << std::endl;

    // 错误使用：忽略返回值（会产生警告）
    // compute_value();  // 警告：忽略了 nodiscard 返回值

    // 正确使用：检查错误码
    int error = perform_operation();
    if (error != 0) {
        std::cout << "Operation failed" << std::endl;
    } else {
        std::cout << "Operation succeeded" << std::endl;
    }

    // 错误使用：忽略错误码（会产生警告）
    // perform_operation();  // 警告：忽略了 nodiscard 返回值

    // 使用 optional 的 nodiscard
    auto result = find_value({1, 2, 3, 4, 5}, 3);
    if (result) {
        std::cout << "Found at index: " << *result << std::endl;
    }
}

// 2. [[maybe_unused]] 属性
void maybe_unused_example() {
    std::cout << "\n[[maybe_unused]] 属性]" << std::endl;

    // 变量可能未使用
    [[maybe_unused]] int unused_var = 42;
    std::cout << "This example demonstrates [[maybe_unused]]" << std::endl;

    // 函数参数可能未使用
    auto callback = []([[maybe_unused]] int event_type,
                       [[maybe_unused]] const std::string& message) {
        // 在某些构建配置中可能不使用这些参数
        std::cout << "Callback called" << std::endl;
    };

    callback(1, "test");

    // 条件编译中的变量
    #ifdef DEBUG
    [[maybe_unused]] int debug_value = 100;
    #endif

    // 模板中的未使用参数（使用 lambda）
    auto process = []([[maybe_unused]] auto value) {
        #if defined(ENABLE_LOGGING)
        std::cout << "Processing: " << value << std::endl;
        #endif
    };

    process(42);
}

// 3. [[fallthrough]] 属性
void fallthrough_example() {
    std::cout << "\n[[fallthrough]] 属性]" << std::endl;

    int value = 2;

    switch (value) {
        case 1:
            std::cout << "Case 1" << std::endl;
            [[fallthrough]];  // 故意贯穿到 case 2
        case 2:
            std::cout << "Case 2" << std::endl;
            [[fallthrough]];  // 故意贯穿到 case 3
        case 3:
            std::cout << "Case 3" << std::endl;
            break;  // 这里不贯穿
        case 4:
            std::cout << "Case 4" << std::endl;
            break;
        default:
            std::cout << "Default" << std::endl;
            break;
    }

    // 实际应用：解析命令
    auto parse_command = [](const std::string& cmd) {
        int result = 0;

        switch (cmd[0]) {
            case 'a':
                result += 1;
                [[fallthrough]];
            case 'b':
                result += 2;
                [[fallthrough]];
            case 'c':
                result += 4;
                break;
            default:
                result = -1;
                break;
        }

        return result;
    };

    std::cout << "parse_command(\"a\"): " << parse_command("a") << std::endl;
    std::cout << "parse_command(\"b\"): " << parse_command("b") << std::endl;
    std::cout << "parse_command(\"c\"): " << parse_command("c") << std::endl;
}

// 4. 组合使用属性
[[nodiscard]] std::unique_ptr<int> create_resource() {
    return std::make_unique<int>(42);
}

void use_resource([[maybe_unused]] std::unique_ptr<int> resource) {
    // 在某些情况下可能不使用资源
    #if defined(USE_RESOURCE)
    std::cout << "Using resource: " << *resource << std::endl;
    #else
    std::cout << "Resource created but not used" << std::endl;
    #endif
}

void combined_example() {
    std::cout << "\n[组合使用属性]" << std::endl;

    // 创建资源（nodiscard 确保不忽略返回值）
    auto resource = create_resource();

    // 使用资源（maybe_unused 允许在某些配置中不使用）
    use_resource(std::move(resource));
}

// 5. 自定义属性（编译器特定）
// 注意：自定义属性是编译器特定的，这里仅作示例

// GCC/Clang 特定属性
#ifdef __GNUC__
#define LIKELY(x)   __builtin_expect(!!(x), 1)
#define UNLIKELY(x) __builtin_expect(!!(x), 0)
#else
#define LIKELY(x)   (x)
#define UNLIKELY(x) (x)
#endif

void compiler_specific_example() {
    std::cout << "\n[编译器特定属性]" << std::endl;

    int value = 42;

    if (LIKELY(value > 0)) {
        std::cout << "Value is positive (likely path)" << std::endl;
    }

    if (UNLIKELY(value < 0)) {
        std::cout << "Value is negative (unlikely path)" << std::endl;
    }
}

// 6. 属性与错误处理
[[nodiscard]] bool validate_input(int value) {
    return value >= 0 && value <= 100;
}

[[nodiscard]] std::string format_output(int value) {
    if (!validate_input(value)) {
        return "Invalid input";
    }
    return "Value: " + std::to_string(value);
}

void error_handling_example() {
    std::cout << "\n[属性与错误处理]" << std::endl;

    // 正确使用：检查验证结果
    int input = 50;
    if (validate_input(input)) {
        std::cout << format_output(input) << std::endl;
    } else {
        std::cout << "Invalid input: " << input << std::endl;
    }

    // 错误使用：忽略验证（会产生警告）
    // validate_input(200);  // 警告：忽略了 nodiscard 返回值
}

// 7. 属性与资源管理
class FileHandle {
public:
    [[nodiscard]] static FileHandle open(const std::string& filename) {
        std::cout << "Opening file: " << filename << std::endl;
        return FileHandle(filename);
    }

    ~FileHandle() {
        if (!filename_.empty()) {
            std::cout << "Closing file: " << filename_ << std::endl;
        }
    }

    // 移动构造函数
    FileHandle(FileHandle&& other) noexcept
        : filename_(std::move(other.filename_)) {
        other.filename_.clear();
    }

    // 移动赋值
    FileHandle& operator=(FileHandle&& other) noexcept {
        if (this != &other) {
            filename_ = std::move(other.filename_);
            other.filename_.clear();
        }
        return *this;
    }

    // 删除拷贝
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;

private:
    explicit FileHandle(const std::string& filename) : filename_(filename) {}

    std::string filename_;
};

void resource_management_example() {
    std::cout << "\n[属性与资源管理]" << std::endl;

    // nodiscard 确保不忽略返回的资源句柄
    auto file = FileHandle::open("test.txt");

    // 文件自动关闭
}

// 8. 属性与线程安全
[[nodiscard("Lock must be held")]]
std::unique_lock<std::mutex> acquire_lock(std::mutex& mtx) {
    return std::unique_lock<std::mutex>(mtx);
}

void thread_safety_example() {
    std::cout << "\n[属性与线程安全]" << std::endl;

    std::mutex mtx;

    // nodiscard 确保不忽略锁
    auto lock = acquire_lock(mtx);
    std::cout << "Lock acquired" << std::endl;

    // 锁在作用域结束时自动释放
}

// 9. 属性与性能优化
[[nodiscard]] int fast_path(int value) {
    // 快速路径
    return value * 2;
}

[[nodiscard]] int slow_path(int value) {
    // 慢速路径
    return value * value;
}

void performance_example() {
    std::cout << "\n[属性与性能优化]" << std::endl;

    int value = 21;

    // 使用 LIKELY/UNLIKELY 优化分支预测
    if (LIKELY(value < 100)) {
        std::cout << "Fast path: " << fast_path(value) << std::endl;
    } else {
        std::cout << "Slow path: " << slow_path(value) << std::endl;
    }
}

// 10. 属性的最佳实践
void best_practices_example() {
    std::cout << "\n[属性的最佳实践]" << std::endl;

    std::cout << "1. [[nodiscard]]:" << std::endl;
    std::cout << "   - 用于错误码、资源句柄、重要返回值" << std::endl;
    std::cout << "   - 提供有意义的警告消息" << std::endl;

    std::cout << "\n2. [[maybe_unused]]:" << std::endl;
    std::cout << "   - 用于条件编译中的变量" << std::endl;
    std::cout << "   - 用于回调函数的未使用参数" << std::endl;

    std::cout << "\n3. [[fallthrough]]:" << std::endl;
    std::cout << "   - 用于 switch 语句中的故意贯穿" << std::endl;
    std::cout << "   - 仅在贯穿到下一个 case 时使用" << std::endl;

    std::cout << "\n4. 最佳实践:" << std::endl;
    std::cout << "   - 不要滥用属性" << std::endl;
    std::cout << "   - 属性应该增强代码安全性" << std::endl;
    std::cout << "   - 属性应该表达开发者的意图" << std::endl;
}

// 主示例函数
void attributes_example() {
    std::cout << "=== 属性 ===" << std::endl;

    nodiscard_example();
    maybe_unused_example();
    fallthrough_example();
    combined_example();
    compiler_specific_example();
    error_handling_example();
    resource_management_example();
    thread_safety_example();
    performance_example();
    best_practices_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    attributes_example();
    return 0;
}
#endif
