/**
 * @file 06_null_dereference.cpp
 * @brief 空指针解引用陷阱示例
 *
 * 空指针解引用：解引用空指针
 * 危害：程序崩溃、未定义行为
 */

#include <iostream>
#include <memory>
#include <optional>
#include <string>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：直接解引用空指针
 *
 * 问题：解引用 nullptr 导致崩溃
 */
void bad_direct_null() {
    int* ptr = nullptr;
    // *ptr = 42;  // 崩溃！
}

/**
 * 错误示例 2：函数返回空指针
 *
 * 问题：函数可能返回空指针，调用者未检查
 */
int* find_value(bool found) {
    if (found) {
        static int value = 42;
        return &value;
    }
    return nullptr;
}

void bad_return_null() {
    int* ptr = find_value(false);
    // std::cout << *ptr << std::endl;  // 崩溃！
}

/**
 * 错误示例 3：容器返回空指针
 *
 * 问题：容器操作可能返回空指针
 */
void bad_container_null() {
    std::unique_ptr<int> ptr;
    // std::cout << *ptr << std::endl;  // 崩溃！
}

/**
 * 错误示例 4：未检查的指针运算
 *
 * 问题：指针可能为空，未检查就使用
 */
void bad_pointer_arithmetic(int* ptr) {
    int value = *ptr;  // 如果 ptr 为空，崩溃
    std::cout << value << std::endl;
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：检查指针是否为空
 *
 * 解决方案：使用前检查指针是否为空
 */
void good_check_null() {
    int* ptr = nullptr;

    if (ptr != nullptr) {
        std::cout << *ptr << std::endl;
    } else {
        std::cout << "指针为空" << std::endl;
    }
}

/**
 * 正确示例 2：使用 std::optional
 *
 * 解决方案：用 optional 表示可能无值的情况
 */
std::optional<int> find_value_optional(bool found) {
    if (found) {
        return 42;
    }
    return std::nullopt;
}

void good_optional() {
    auto value = find_value_optional(false);

    if (value.has_value()) {
        std::cout << "值: " << value.value() << std::endl;
    } else {
        std::cout << "未找到值" << std::endl;
    }
}

/**
 * 正确示例 3：使用智能指针检查
 *
 * 解决方案：智能指针可以隐式转换为 bool
 */
void good_smart_pointer_check() {
    std::unique_ptr<int> ptr;

    if (ptr) {
        std::cout << *ptr << std::endl;
    } else {
        std::cout << "指针为空" << std::endl;
    }
}

/**
 * 正确示例 4：使用引用代替指针
 *
 * 解决方案：引用不能为空，编译时保证
 */
void good_reference(int& value) {
    std::cout << "值: " << value << std::endl;
}

/**
 * 正确示例 5：使用 gsl::not_null
 *
 * 解决方案：使用 not_null 保证指针不为空
 */
#include <cassert>

template <typename T>
class not_null {
public:
    not_null(T* p) : ptr_(p) {
        assert(ptr_ != nullptr);
    }

    T* get() const { return ptr_; }
    T& operator*() const { return *ptr_; }
    T* operator->() const { return ptr_; }

private:
    T* ptr_;
};

void good_not_null(not_null<int> ptr) {
    std::cout << "值: " << *ptr << std::endl;
}

/**
 * 正确示例 6：使用 std::expected (C++23) 或类似模式
 *
 * 解决方案：使用 expected 表示可能失败的操作
 */
#include <variant>

template <typename T, typename E>
class Expected {
public:
    Expected(T value) : data_(std::move(value)) {}
    Expected(E error) : data_(std::move(error)) {}

    bool has_value() const { return std::holds_alternative<T>(data_); }
    const T& value() const { return std::get<T>(data_); }
    const E& error() const { return std::get<E>(data_); }

private:
    std::variant<T, E> data_;
};

Expected<int, std::string> find_value_expected(bool found) {
    if (found) {
        return 42;
    }
    return std::string("未找到值");
}

void good_expected() {
    auto result = find_value_expected(false);

    if (result.has_value()) {
        std::cout << "值: " << result.value() << std::endl;
    } else {
        std::cout << "错误: " << result.error() << std::endl;
    }
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 空指针解引用陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 直接解引用空指针" << std::endl;
    std::cout << "问题：解引用 nullptr 导致崩溃" << std::endl;
    // bad_direct_null();  // 注释掉，避免崩溃
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 检查指针是否为空" << std::endl;
    good_check_null();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 std::optional" << std::endl;
    good_optional();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用智能指针检查" << std::endl;
    good_smart_pointer_check();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用引用代替指针" << std::endl;
    int value = 42;
    good_reference(value);
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用 not_null" << std::endl;
    int val = 42;
    good_not_null(&val);
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用 Expected 模式" << std::endl;
    good_expected();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
