/**
 * @file 01_dangling_pointer.cpp
 * @brief 悬空指针陷阱示例
 *
 * 悬空指针 (Dangling Pointer)：指向已释放内存的指针
 * 危害：程序崩溃、数据损坏、安全漏洞
 */

#include <iostream>
#include <memory>
#include <vector>

// ============================================================================
// 陷阱说明
// ============================================================================

/**
 * 悬空指针产生场景：
 * 1. 函数返回局部变量地址
 * 2. 释放内存后继续使用指针
 * 3. 指向已销毁对象的指针
 * 4. 容器扩容后迭代器失效
 */

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：返回局部变量地址
 *
 * 问题：局部变量在函数返回后被销毁，返回其地址是未定义行为
 */
int* bad_return_local() {
    int local_var = 42;
    return &local_var;  // 错误：返回局部变量地址
}

/**
 * 错误示例 2：释放后继续使用
 *
 * 问题：delete 后指针仍指向原地址，成为悬空指针
 */
void bad_use_after_delete() {
    int* ptr = new int(100);
    delete ptr;
    // ptr 现在是悬空指针
    // std::cout << *ptr << std::endl;  // 未定义行为
}

/**
 * 错误示例 3：指向临时对象
 *
 * 问题：临时对象在语句结束后销毁
 */
void bad_temporary_reference() {
    const int& ref = 42;  // C++11: 绑定到临时对象
    // 临时对象已销毁，ref 悬空
    // std::cout << ref << std::endl;  // 未定义行为
}

/**
 * 错误示例 4：迭代器失效
 *
 * 问题：vector 扩容后，所有迭代器失效
 */
void bad_iterator_invalidation() {
    std::vector<int> vec = {1, 2, 3};
    auto it = vec.begin();
    vec.push_back(4);  // 可能触发扩容
    // it 可能已失效
    // std::cout << *it << std::endl;  // 未定义行为
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用智能指针
 *
 * 解决方案：使用 unique_ptr 自动管理内存生命周期
 */
std::unique_ptr<int> good_smart_pointer() {
    return std::make_unique<int>(42);
}

/**
 * 正确示例 2：返回值而非指针
 *
 * 解决方案：直接返回值，利用移动语义
 */
std::vector<int> good_return_value() {
    std::vector<int> vec = {1, 2, 3};
    return vec;  // 移动语义，高效
}

/**
 * 正确示例 3：使用 std::optional
 *
 * 解决方案：用 optional 表示可能无值的情况
 */
#include <optional>

std::optional<int> good_find_value(bool found) {
    if (found) {
        return 42;
    }
    return std::nullopt;  // 明确表示无值
}

/**
 * 正确示例 4：释放后置空
 *
 * 解决方案：释放内存后立即置空指针
 */
void good_use_after_delete() {
    int* ptr = new int(100);
    delete ptr;
    ptr = nullptr;  // 置空，避免悬空

    if (ptr != nullptr) {
        std::cout << *ptr << std::endl;  // 安全检查
    }
}

/**
 * 正确示例 5：使用引用参数
 *
 * 解决方案：使用引用代替指针，生命周期更明确
 */
void good_use_reference(const int& value) {
    std::cout << "Value: " << value << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 悬空指针陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例（注释掉以避免崩溃）
    std::cout << "[错误示例 1] 返回局部变量地址" << std::endl;
    std::cout << "问题：返回局部变量地址，函数结束后变量被销毁" << std::endl;
    std::cout << "结果：未定义行为，可能崩溃" << std::endl;
    // int* bad_ptr = bad_return_local();
    // std::cout << *bad_ptr << std::endl;  // 未定义行为
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用智能指针" << std::endl;
    auto good_ptr = good_smart_pointer();
    std::cout << "智能指针值: " << *good_ptr << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 2] 返回值而非指针" << std::endl;
    auto vec = good_return_value();
    std::cout << "返回值大小: " << vec.size() << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 std::optional" << std::endl;
    auto val1 = good_find_value(true);
    auto val2 = good_find_value(false);
    std::cout << "找到值: " << val1.value_or(0) << std::endl;
    std::cout << "未找到: " << val2.value_or(0) << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 4] 释放后置空" << std::endl;
    good_use_after_delete();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用引用参数" << std::endl;
    int value = 42;
    good_use_reference(value);
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
