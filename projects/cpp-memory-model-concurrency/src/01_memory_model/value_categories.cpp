/**
 * 值类别 (Value Categories)
 *
 * C++17 的值类别体系：
 * 1. glvalue (泛左值) - 有身份的表达式
 * 2. rvalue (右值) - 可以移动的表达式
 * 3. lvalue (左值) - 有身份且不可移动
 * 4. xvalue (将亡值) - 有身份且可以移动
 * 5. prvalue (纯右值) - 无身份且可以移动
 *
 * 编译：g++ -std=c++17 -pthread value_categories.cpp -o value_categories
 */

#include <iostream>
#include <string>
#include <utility>
#include <type_traits>

// 示例1：左值和右值
void lvalue_rvalue() {
    std::cout << "=== 左值和右值 ===" << std::endl;

    int x = 42;           // x 是左值，42 是右值
    int& lref = x;        // lref 是左值引用
    int&& rref = 42;      // rref 是右值引用，但 rref 本身是左值

    std::cout << "x = " << x << std::endl;
    std::cout << "lref = " << lref << std::endl;
    std::cout << "rref = " << rref << std::endl;

    // 左值可以取地址
    std::cout << "\n左值可以取地址:" << std::endl;
    std::cout << "&x = " << &x << std::endl;
    std::cout << "&lref = " << &lref << std::endl;
    std::cout << "&rref = " << &rref << " (右值引用本身是左值)" << std::endl;

    // 右值不能取地址
    // std::cout << &42;  // 错误：不能取右值的地址
}

// 示例2：左值引用和右值引用
void references() {
    std::cout << "\n=== 左值引用和右值引用 ===" << std::endl;

    int x = 42;

    // 左值引用只能绑定到左值
    int& lref = x;  // 正确
    // int& lref2 = 42;  // 错误：不能将左值引用绑定到右值

    // 右值引用只能绑定到右值
    int&& rref = 42;  // 正确
    // int&& rref2 = x;  // 错误：不能将右值引用绑定到左值

    // const 左值引用可以绑定到右值
    const int& clref = 42;  // 正确
    std::cout << "const 左值引用可以绑定到右值" << std::endl;

    // 移动语义
    std::string s1 = "Hello";
    std::string s2 = std::move(s1);  // std::move 将左值转换为右值引用
    std::cout << "s1 (移动后): " << s1 << std::endl;
    std::cout << "s2 (移动后): " << s2 << std::endl;
}

// 示例3：值类别判断
template<typename T>
void check_value_category(T&& expr) {
    // 使用类型特征判断值类别
    if constexpr (std::is_lvalue_reference_v<T>) {
        std::cout << "  左值" << std::endl;
    } else if constexpr (std::is_rvalue_reference_v<T>) {
        std::cout << "  右值" << std::endl;
    } else {
        std::cout << "  右值" << std::endl;
    }
}

void value_category_check() {
    std::cout << "\n=== 值类别判断 ===" << std::endl;

    int x = 42;
    std::cout << "x: ";
    check_value_category(x);

    std::cout << "42: ";
    check_value_category(42);

    std::cout << "std::move(x): ";
    check_value_category(std::move(x));

    std::cout << "x + 1: ";
    check_value_category(x + 1);
}

// 示例4：完美转发
template<typename T>
void perfect_forwarding_demo(T&& arg) {
    std::cout << "  接收到的类型: ";

    // 使用 std::forward 保持值类别
    if constexpr (std::is_lvalue_reference_v<T>) {
        std::cout << "左值引用" << std::endl;
    } else {
        std::cout << "右值引用" << std::endl;
    }

    // 转发给其他函数
    // 使用 std::forward 保持原始值类别
    auto&& forwarded = std::forward<T>(arg);
    (void)forwarded;
}

void perfect_forwarding() {
    std::cout << "\n=== 完美转发 ===" << std::endl;

    int x = 42;
    std::cout << "转发左值:" << std::endl;
    perfect_forwarding_demo(x);

    std::cout << "转发右值:" << std::endl;
    perfect_forwarding_demo(42);

    std::cout << "转发 std::move(x):" << std::endl;
    perfect_forwarding_demo(std::move(x));
}

// 示例5：移动语义
class Buffer {
public:
    Buffer(size_t size) : size_(size), data_(new char[size]) {
        std::cout << "  构造: 分配 " << size << " bytes" << std::endl;
    }

    ~Buffer() {
        delete[] data_;
        std::cout << "  析构: 释放内存" << std::endl;
    }

    // 移动构造函数
    Buffer(Buffer&& other) noexcept
        : size_(other.size_), data_(other.data_) {
        other.size_ = 0;
        other.data_ = nullptr;
        std::cout << "  移动构造" << std::endl;
    }

    // 移动赋值运算符
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            size_ = other.size_;
            data_ = other.data_;
            other.size_ = 0;
            other.data_ = nullptr;
            std::cout << "  移动赋值" << std::endl;
        }
        return *this;
    }

    // 禁用拷贝
    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;

    size_t size() const { return size_; }

private:
    size_t size_;
    char* data_;
};

void move_semantics() {
    std::cout << "\n=== 移动语义 ===" << std::endl;

    std::cout << "创建 buf1:" << std::endl;
    Buffer buf1(1024);

    std::cout << "\n移动构造 buf2:" << std::endl;
    Buffer buf2 = std::move(buf1);

    std::cout << "\nbuf1.size() = " << buf1.size() << " (已移动)" << std::endl;
    std::cout << "buf2.size() = " << buf2.size() << std::endl;

    std::cout << "\n创建 buf3:" << std::endl;
    Buffer buf3(512);

    std::cout << "\n移动赋值 buf3:" << std::endl;
    buf3 = std::move(buf2);

    std::cout << "\nbuf2.size() = " << buf2.size() << " (已移动)" << std::endl;
    std::cout << "buf3.size() = " << buf3.size() << std::endl;
}

// 示例6：折叠引用
template<typename T>
void reference_collapsing(T&& arg) {
    std::cout << "  T 的类型: ";

    if constexpr (std::is_lvalue_reference_v<T>) {
        std::cout << "左值引用" << std::endl;
    } else if constexpr (std::is_rvalue_reference_v<T>) {
        std::cout << "右值引用" << std::endl;
    } else {
        std::cout << "非引用" << std::endl;
    }
}

void reference_collapsing_demo() {
    std::cout << "\n=== 引用折叠 ===" << std::endl;

    int x = 42;
    std::cout << "左值 x:" << std::endl;
    reference_collapsing(x);

    std::cout << "右值 42:" << std::endl;
    reference_collapsing(42);

    // 引用折叠规则：
    // T& & -> T&
    // T& && -> T&
    // T&& & -> T&
    // T&& && -> T&&
    std::cout << "\n引用折叠规则:" << std::endl;
    std::cout << "T& & -> T&" << std::endl;
    std::cout << "T& && -> T&" << std::endl;
    std::cout << "T&& & -> T&" << std::endl;
    std::cout << "T&& && -> T&&" << std::endl;
}

int main() {
    std::cout << "C++ 内存模型：值类别 (Value Categories)" << std::endl;
    std::cout << "=========================================\n" << std::endl;

    lvalue_rvalue();
    references();
    value_category_check();
    perfect_forwarding();
    move_semantics();
    reference_collapsing_demo();

    return 0;
}
