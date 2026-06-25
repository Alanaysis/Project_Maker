#include <iostream>
#include <string>
#include <memory>
#include <vector>
#include <algorithm>

/**
 * @file msvc_demo.cpp
 * @brief MSVC 工具链示例
 *
 * 演示 MSVC 编译器的特性和跨平台代码编写。
 * MSVC 是 Windows 平台的主要 C++ 编译器。
 */

// 跨平台字符串类型
#ifdef _MSC_VER
    using tchar = wchar_t;
    #define T(x) L##x
#else
    using tchar = char;
    #define T(x) x
#endif

// 演示 [[nodiscard]] 属性
[[nodiscard]] bool is_valid(const std::string& str) {
    return !str.empty();
}

// 演示 constexpr
constexpr double pi = 3.14159265358979323846;

constexpr double circle_area(double radius) {
    return pi * radius * radius;
}

// 演示结构化绑定
struct Config {
    std::string name;
    int width;
    int height;
    bool fullscreen;
};

Config get_default_config() {
    return {"Default", 1920, 1080, false};
}

// 演示移动语义
class Buffer {
public:
    explicit Buffer(size_t size) : data_(std::make_unique<char[]>(size)), size_(size) {
        std::cout << "Buffer 创建 (" << size_ << " 字节)" << std::endl;
    }

    Buffer(Buffer&& other) noexcept : data_(std::move(other.data_)), size_(other.size_) {
        other.size_ = 0;
        std::cout << "Buffer 移动" << std::endl;
    }

    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            data_ = std::move(other.data_);
            size_ = other.size_;
            other.size_ = 0;
        }
        return *this;
    }

    size_t size() const { return size_; }

private:
    std::unique_ptr<char[]> data_;
    size_t size_;
};

int main() {
    std::cout << "=== MSVC 工具链示例 ===" << std::endl;
    std::cout << std::endl;

    // 编译器信息
    std::cout << "编译器信息:" << std::endl;
#ifdef _MSC_VER
    std::cout << "  MSVC 版本: " << _MSC_VER << std::endl;
    std::cout << "  MSVC 完整版本: " << _MSC_FULL_VER << std::endl;
#endif
    std::cout << "  C++ 标准: " << __cplusplus << std::endl;
    std::cout << std::endl;

    // constexpr
    std::cout << "--- constexpr ---" << std::endl;
    std::cout << "pi = " << pi << std::endl;
    std::cout << "圆面积 (r=5) = " << circle_area(5.0) << std::endl;

    // nodiscard
    std::cout << std::endl;
    std::cout << "--- nodiscard ---" << std::endl;
    std::string test = "hello";
    if (is_valid(test)) {
        std::cout << "'" << test << "' 是有效的" << std::endl;
    }

    // 结构化绑定
    std::cout << std::endl;
    std::cout << "--- 结构化绑定 ---" << std::endl;
    auto [name, width, height, fullscreen] = get_default_config();
    std::cout << "配置: " << name << " (" << width << "x" << height << ")" << std::endl;

    // 移动语义
    std::cout << std::endl;
    std::cout << "--- 移动语义 ---" << std::endl;
    Buffer buf1(1024);
    Buffer buf2 = std::move(buf1);
    std::cout << "buf2 大小: " << buf2.size() << std::endl;

    std::cout << std::endl;
    std::cout << "MSVC 编译选项说明:" << std::endl;
    std::cout << "  /W4             : 警告级别 4" << std::endl;
    std::cout << "  /WX             : 将警告视为错误" << std::endl;
    std::cout << "  /permissive-    : 严格标准符合性" << std::endl;
    std::cout << "  /Zc:__cplusplus : 正确报告 C++ 标准版本" << std::endl;
    std::cout << "  /EHsc           : 启用 C++ 异常处理" << std::endl;

    return 0;
}
