/**
 * @file 02_memory_leak.cpp
 * @brief 内存泄漏陷阱示例
 *
 * 内存泄漏 (Memory Leak)：分配的内存未释放
 * 危害：内存耗尽、程序变慢、系统不稳定
 */

#include <iostream>
#include <memory>
#include <vector>
#include <cstring>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：忘记释放内存
 *
 * 问题：new 分配的内存未 delete
 */
void bad_forget_delete() {
    int* ptr = new int(42);
    // 忘记 delete ptr;
    // 函数返回后 ptr 销毁，内存泄漏
}

/**
 * 错误示例 2：异常导致泄漏
 *
 * 问题：异常发生时，已分配的内存未释放
 */
void bad_exception_leak() {
    int* ptr = new int(42);
    throw std::runtime_error("error");  // 异常，内存泄漏
    delete ptr;  // 不会执行
}

/**
 * 错误示例 3：循环引用
 *
 * 问题：shared_ptr 循环引用导致内存无法释放
 */
struct BadNode {
    std::shared_ptr<BadNode> next;
    int value;
};

void bad_circular_reference() {
    auto node1 = std::make_shared<BadNode>();
    auto node2 = std::make_shared<BadNode>();
    node1->next = node2;
    node2->next = node1;  // 循环引用
    // node1 和 node2 的引用计数永远不为 0
}

/**
 * 错误示例 4：realloc 失败
 *
 * 问题：realloc 失败时返回 NULL，原内存未释放
 */
void bad_realloc_failure() {
    char* str = (char*)malloc(100);
    strcpy(str, "hello");

    // realloc 可能失败
    char* new_str = (char*)realloc(str, 200);
    if (new_str == NULL) {
        // str 未释放，内存泄漏
        return;
    }
    str = new_str;
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用 unique_ptr
 *
 * 解决方案：unique_ptr 自动释放内存
 */
void good_unique_ptr() {
    auto ptr = std::make_unique<int>(42);
    std::cout << "值: " << *ptr << std::endl;
    // 函数返回时自动释放
}

/**
 * 正确示例 2：使用 RAII 管理资源
 *
 * 解决方案：RAII 类在析构时释放资源
 */
class Resource {
public:
    Resource() : data_(new int[100]) {
        std::cout << "资源获取" << std::endl;
    }
    ~Resource() {
        delete[] data_;
        std::cout << "资源释放" << std::endl;
    }

    // 禁止拷贝
    Resource(const Resource&) = delete;
    Resource& operator=(const Resource&) = delete;

    // 允许移动
    Resource(Resource&& other) noexcept : data_(other.data_) {
        other.data_ = nullptr;
    }

private:
    int* data_;
};

void good_raii() {
    Resource res;
    // 函数返回时自动调用析构函数释放资源
}

/**
 * 正确示例 3：使用 weak_ptr 打破循环引用
 *
 * 解决方案：weak_ptr 不增加引用计数
 */
struct GoodNode {
    std::weak_ptr<GoodNode> next;  // 使用 weak_ptr
    int value;
};

void good_weak_ptr() {
    auto node1 = std::make_shared<GoodNode>();
    auto node2 = std::make_shared<GoodNode>();
    node1->next = node2;
    node2->next = node1;  // 不会导致循环引用
}

/**
 * 正确示例 4：使用 vector 代替动态数组
 *
 * 解决方案：vector 自动管理内存
 */
void good_vector() {
    std::vector<int> vec(100, 0);
    vec.push_back(42);
    // 函数返回时自动释放
}

/**
 * 正确示例 5：异常安全的内存管理
 *
 * 解决方案：使用智能指针确保异常安全
 */
void good_exception_safe() {
    auto ptr = std::make_unique<int>(42);
    throw std::runtime_error("error");
    // ptr 自动释放，无内存泄漏
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 内存泄漏陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 忘记释放内存" << std::endl;
    std::cout << "问题：new 分配的内存未 delete" << std::endl;
    std::cout << "结果：内存泄漏" << std::endl;
    // bad_forget_delete();  // 注释掉，避免实际泄漏
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用 unique_ptr" << std::endl;
    good_unique_ptr();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 RAII" << std::endl;
    good_raii();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 weak_ptr 打破循环引用" << std::endl;
    good_weak_ptr();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 vector 代替动态数组" << std::endl;
    good_vector();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 异常安全的内存管理" << std::endl;
    try {
        good_exception_safe();
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
