/**
 * @file 05_const_correctness.cpp
 * @brief 常量正确性示例
 *
 * 常量正确性：正确使用 const 关键字
 * 优点：提高代码安全性、可读性、可维护性
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>

// ============================================================================
// const 基础
// ============================================================================

/**
 * const 示例 1：常量变量
 *
 * 使用 const 保护变量不被修改
 */
void const_variable() {
    const int x = 42;
    // x = 100;  // 错误！不能修改 const 变量
    std::cout << "x = " << x << std::endl;
}

/**
 * const 示例 2：常量指针
 *
 * 区分 const 指针和指向 const 的指针
 */
void const_pointer() {
    int x = 42;
    int y = 100;

    // 指向 const 的指针：不能通过指针修改值
    const int* ptr1 = &x;
    // *ptr1 = 100;  // 错误！
    ptr1 = &y;  // 可以修改指针本身

    // const 指针：不能修改指针本身
    int* const ptr2 = &x;
    *ptr2 = 100;  // 可以修改值
    // ptr2 = &y;  // 错误！

    // const 指针指向 const：都不能修改
    const int* const ptr3 = &x;
    // *ptr3 = 100;  // 错误！
    // ptr3 = &y;    // 错误！
}

/**
 * const 示例 3：常量引用
 *
 * 使用 const 引用避免拷贝
 */
void const_reference(const std::string& str) {
    // str = "new";  // 错误！不能修改 const 引用
    std::cout << str << std::endl;
}

/**
 * const 示例 4：常量成员函数
 *
 * 标记不修改对象状态的成员函数
 */
class Point {
public:
    Point(int x, int y) : x_(x), y_(y) {}

    // const 成员函数：不修改对象状态
    int x() const { return x_; }
    int y() const { return y_; }

    // 非 const 成员函数：可以修改对象状态
    void set_x(int x) { x_ = x; }
    void set_y(int y) { y_ = y; }

private:
    int x_;
    int y_;
};

void const_member_function() {
    const Point p(1, 2);
    std::cout << "x = " << p.x() << std::endl;
    std::cout << "y = " << p.y() << std::endl;
    // p.set_x(10);  // 错误！不能在 const 对象上调用非 const 成员函数
}

// ============================================================================
// const 高级用法
// ============================================================================

/**
 * const 示例 5：const_iterator
 *
 * 使用 const_iterator 遍历容器时不修改元素
 */
void const_iterator() {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    // const_iterator：不能修改元素
    for (std::vector<int>::const_iterator it = vec.cbegin(); it != vec.cend(); ++it) {
        std::cout << *it << " ";
        // *it = 100;  // 错误！
    }
    std::cout << std::endl;

    // 使用 auto
    for (auto it = vec.cbegin(); it != vec.cend(); ++it) {
        std::cout << *it << " ";
    }
    std::cout << std::endl;
}

/**
 * const 示例 6：const 和 mutable
 *
 * 使用 mutable 允许在 const 成员函数中修改某些成员
 */
class Cache {
public:
    Cache(int value) : value_(value), cached_(false), cache_(0) {}

    int get_value() const {
        if (!cached_) {
            cache_ = compute_expensive_value();
            cached_ = true;
        }
        return cache_;
    }

private:
    int compute_expensive_value() const {
        return value_ * 2;
    }

    int value_;
    mutable bool cached_;  // mutable 允许在 const 函数中修改
    mutable int cache_;
};

void const_mutable() {
    const Cache cache(42);
    std::cout << "值: " << cache.get_value() << std::endl;
}

/**
 * const 示例 7：const 和智能指针
 *
 * 区分 const 智能指针和指向 const 的智能指针
 */
void const_smart_pointer() {
    auto ptr = std::make_unique<int>(42);

    // 指向 const 的 unique_ptr
    const auto& const_ref = ptr;
    // *const_ref = 100;  // 错误！

    // const unique_ptr
    const std::unique_ptr<int> const_ptr = std::make_unique<int>(42);
    *const_ptr = 100;  // 可以修改指向的值
    // const_ptr = std::make_unique<int>(100);  // 错误！不能修改指针本身
}

/**
 * const 示例 8：const 和函数返回值
 *
 * 返回 const 引用避免拷贝
 */
class StringWrapper {
public:
    StringWrapper(const std::string& str) : str_(str) {}

    // 返回 const 引用
    const std::string& get_string() const { return str_; }

    // 返回非 const 引用（允许修改）
    std::string& get_string() { return str_; }

private:
    std::string str_;
};

void const_return() {
    StringWrapper wrapper("hello");

    // const 版本
    const StringWrapper& const_wrapper = wrapper;
    const std::string& str1 = const_wrapper.get_string();
    std::cout << str1 << std::endl;

    // 非 const 版本
    std::string& str2 = wrapper.get_string();
    str2 += " world";
    std::cout << wrapper.get_string() << std::endl;
}

// ============================================================================
// const 最佳实践
// ============================================================================

/**
 * 最佳实践 1：尽可能使用 const
 *
 * 默认使用 const，除非需要修改
 */
void best_practice_const() {
    // const 变量
    const int max_size = 100;

    // const 引用参数
    auto print = [](const std::string& msg) {
        std::cout << msg << std::endl;
    };

    // const 成员函数
    class ConstClass {
    public:
        int get() const { return value_; }
    private:
        int value_ = 0;
    };
}

/**
 * 最佳实践 2：const 和值传递
 *
 * 值传递不需要 const
 */
void value_pass(std::string str) {  // 值传递，不需要 const
    std::cout << str << std::endl;
}

/**
 * 最佳实践 3：const 和引用传递
 *
 * 不修改的参数使用 const 引用
 */
void const_ref_pass(const std::string& str) {  // const 引用
    std::cout << str << std::endl;
}

/**
 * 最佳实践 4：const 和指针传递
 *
 * 不修改的指针参数使用 const
 */
void const_ptr_pass(const int* ptr) {  // 指向 const 的指针
    std::cout << *ptr << std::endl;
}

/**
 * 最佳实践 5：const 和迭代器
 *
 * 不修改元素时使用 const_iterator
 */
void const_iterator_best_practice() {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    // 使用 cbegin/cend
    for (auto it = vec.cbegin(); it != vec.cend(); ++it) {
        std::cout << *it << " ";
    }
    std::cout << std::endl;

    // 使用范围 for
    for (const auto& val : vec) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

/**
 * 最佳实践 6：const 和 lambda
 *
 * lambda 默认是 const
 */
void const_lambda() {
    int x = 42;

    // const lambda
    auto lambda = [x]() {
        // x = 100;  // 错误！lambda 默认是 const
        std::cout << x << std::endl;
    };

    lambda();

    // mutable lambda
    auto mutable_lambda = [x]() mutable {
        x = 100;  // 可以修改捕获的变量
        std::cout << x << std::endl;
    };

    mutable_lambda();
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 常量正确性示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "[1] const 变量" << std::endl;
    const_variable();
    std::cout << std::endl;

    std::cout << "[2] const 指针" << std::endl;
    const_pointer();
    std::cout << std::endl;

    std::cout << "[3] const 引用" << std::endl;
    const_reference("hello");
    std::cout << std::endl;

    std::cout << "[4] const 成员函数" << std::endl;
    const_member_function();
    std::cout << std::endl;

    std::cout << "[5] const_iterator" << std::endl;
    const_iterator();
    std::cout << std::endl;

    std::cout << "[6] const 和 mutable" << std::endl;
    const_mutable();
    std::cout << std::endl;

    std::cout << "[7] const 和智能指针" << std::endl;
    const_smart_pointer();
    std::cout << std::endl;

    std::cout << "[8] const 和函数返回值" << std::endl;
    const_return();
    std::cout << std::endl;

    std::cout << "[9] const lambda" << std::endl;
    const_lambda();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
