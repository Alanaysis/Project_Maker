/**
 * @file 03_double_free.cpp
 * @brief 双重释放陷阱示例
 *
 * 双重释放 (Double Free)：同一内存被释放两次
 * 危害：程序崩溃、内存损坏、安全漏洞
 */

#include <iostream>
#include <memory>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：直接双重释放
 *
 * 问题：同一指针 delete 两次
 */
void bad_double_free() {
    int* ptr = new int(42);
    delete ptr;
    delete ptr;  // 错误：双重释放
}

/**
 * 错误示例 2：别名指针双重释放
 *
 * 问题：两个指针指向同一内存，各自释放
 */
void bad_alias_double_free() {
    int* ptr1 = new int(42);
    int* ptr2 = ptr1;  // 别名
    delete ptr1;
    delete ptr2;  // 错误：双重释放
}

/**
 * 错误示例 3：容器中的双重释放
 *
 * 问题：手动管理的指针放入容器，容器销毁时双重释放
 */
void bad_container_double_free() {
    int* ptr = new int(42);
    std::vector<int*> vec;
    vec.push_back(ptr);
    delete ptr;  // 手动释放
    // vec 销毁时不会再次释放，但如果误以为会释放...
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：释放后置空
 *
 * 解决方案：释放后将指针置为 nullptr
 */
void good_set_null() {
    int* ptr = new int(42);
    delete ptr;
    ptr = nullptr;  // 置空
    delete ptr;  // delete nullptr 是安全的
}

/**
 * 正确示例 2：使用 unique_ptr
 *
 * 解决方案：unique_ptr 自动管理，不会双重释放
 */
void good_unique_ptr() {
    auto ptr = std::make_unique<int>(42);
    // 函数返回时自动释放，无需手动管理
}

/**
 * 正确示例 3：使用 shared_ptr
 *
 * 解决方案：shared_ptr 引用计数，最后一个销毁时释放
 */
void good_shared_ptr() {
    auto ptr1 = std::make_shared<int>(42);
    auto ptr2 = ptr1;  // 共享所有权
    // 引用计数为 2
    // 两个指针销毁时自动释放
}

/**
 * 正确示例 4：明确所有权
 *
 * 解决方案：明确谁负责释放内存
 */
void good_clear_ownership() {
    // 所有权归 unique_ptr
    auto ptr = std::make_unique<int>(42);

    // 如果需要转移所有权
    auto ptr2 = std::move(ptr);
    // ptr 现在为 nullptr
    // ptr2 拥有内存
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 双重释放陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 直接双重释放" << std::endl;
    std::cout << "问题：同一指针 delete 两次" << std::endl;
    std::cout << "结果：程序崩溃" << std::endl;
    // bad_double_free();  // 注释掉，避免崩溃
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 释放后置空" << std::endl;
    good_set_null();
    std::cout << "释放后置空，再次 delete nullptr 安全" << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 unique_ptr" << std::endl;
    good_unique_ptr();
    std::cout << "unique_ptr 自动管理，不会双重释放" << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 shared_ptr" << std::endl;
    good_shared_ptr();
    std::cout << "shared_ptr 引用计数管理" << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 4] 明确所有权" << std::endl;
    good_clear_ownership();
    std::cout << "使用 move 转移所有权" << std::endl;
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
