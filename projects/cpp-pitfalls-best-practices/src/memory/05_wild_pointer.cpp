/**
 * @file 05_wild_pointer.cpp
 * @brief 野指针陷阱示例
 *
 * 野指针 (Wild Pointer)：未初始化的指针
 * 危害：程序崩溃、数据损坏、不可预测行为
 */

#include <iostream>
#include <memory>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：未初始化指针
 *
 * 问题：指针未初始化，指向随机地址
 */
void bad_uninitialized() {
    int* ptr;  // 未初始化，野指针
    // *ptr = 42;  // 未定义行为
}

/**
 * 错误示例 2：部分初始化
 *
 * 问题：结构体中指针成员未初始化
 */
struct BadStruct {
    int value;
    int* ptr;  // 未初始化
};

void bad_partial_init() {
    BadStruct s;
    s.value = 42;
    // s.ptr 未初始化，野指针
}

/**
 * 错误示例 3：条件分支未初始化
 *
 * 问题：某些分支下指针未初始化
 */
void bad_conditional_init(bool condition) {
    int* ptr;
    if (condition) {
        ptr = new int(42);
    }
    // 如果 condition 为 false，ptr 未初始化
    // *ptr = 100;  // 未定义行为
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：初始化为 nullptr
 *
 * 解决方案：声明时初始化为 nullptr
 */
void good_init_nullptr() {
    int* ptr = nullptr;  // 初始化为 nullptr

    if (ptr != nullptr) {
        *ptr = 42;  // 安全检查
    }
}

/**
 * 正确示例 2：使用智能指针
 *
 * 解决方案：智能指针自动初始化为 nullptr
 */
void good_smart_pointer() {
    std::unique_ptr<int> ptr;  // 自动初始化为 nullptr

    if (ptr) {
        std::cout << *ptr << std::endl;
    }
}

/**
 * 正确示例 3：初始化结构体
 *
 * 解决方案：使用默认成员初始化器
 */
struct GoodStruct {
    int value = 0;
    int* ptr = nullptr;  // 默认初始化
};

void good_struct_init() {
    GoodStruct s;
    s.value = 42;
    // s.ptr 已初始化为 nullptr
}

/**
 * 正确示例 4：确保所有分支初始化
 *
 * 解决方案：所有分支都初始化指针
 */
void good_conditional_init(bool condition) {
    int* ptr = nullptr;  // 先初始化为 nullptr

    if (condition) {
        ptr = new int(42);
    }

    if (ptr != nullptr) {
        std::cout << *ptr << std::endl;
        delete ptr;
    }
}

/**
 * 正确示例 5：使用 std::optional
 *
 * 解决方案：用 optional 表示可能无值的情况
 */
#include <optional>

void good_optional(bool condition) {
    std::optional<int> value;

    if (condition) {
        value = 42;
    }

    if (value.has_value()) {
        std::cout << "值: " << value.value() << std::endl;
    }
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 野指针陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 未初始化指针" << std::endl;
    std::cout << "问题：指针未初始化，指向随机地址" << std::endl;
    std::cout << "结果：未定义行为" << std::endl;
    // bad_uninitialized();  // 注释掉
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 初始化为 nullptr" << std::endl;
    good_init_nullptr();
    std::cout << "指针初始化为 nullptr，安全检查" << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用智能指针" << std::endl;
    good_smart_pointer();
    std::cout << "智能指针自动初始化为 nullptr" << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 3] 初始化结构体" << std::endl;
    good_struct_init();
    std::cout << "使用默认成员初始化器" << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 4] 确保所有分支初始化" << std::endl;
    good_conditional_init(true);
    good_conditional_init(false);
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用 std::optional" << std::endl;
    good_optional(true);
    good_optional(false);
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
