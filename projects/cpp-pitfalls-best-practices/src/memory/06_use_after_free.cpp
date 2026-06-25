/**
 * @file 06_use_after_free.cpp
 * @brief 使用已释放内存陷阱示例
 *
 * 使用已释放内存 (Use After Free)：释放内存后继续使用
 * 危害：程序崩溃、数据损坏、安全漏洞
 */

#include <iostream>
#include <memory>
#include <vector>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：直接使用已释放内存
 *
 * 问题：delete 后继续使用指针
 */
void bad_direct_use_after_free() {
    int* ptr = new int(42);
    delete ptr;
    // ptr 指向已释放内存
    // std::cout << *ptr << std::endl;  // 未定义行为
}

/**
 * 错误示例 2：函数返回后使用
 *
 * 问题：返回指向局部变量的指针
 */
int* bad_return_local() {
    int local = 42;
    return &local;  // 返回局部变量地址
}

/**
 * 错误示例 3：容器元素释放后使用
 *
 * 问题：释放容器元素后继续使用引用
 */
void bad_container_use_after_free() {
    std::vector<int*> vec;
    vec.push_back(new int(42));

    int* ptr = vec[0];
    delete ptr;  // 释放内存
    // vec[0] 仍指向已释放内存
}

/**
 * 错误示例 4：shared_ptr 释放后使用
 *
 * 问题：reset 后继续使用
 */
void bad_shared_ptr_use_after_free() {
    auto ptr = std::make_shared<int>(42);
    int& ref = *ptr;  // 获取引用
    ptr.reset();  // 释放内存
    // ref 悬空
    // std::cout << ref << std::endl;  // 未定义行为
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：释放后置空
 *
 * 解决方案：释放后立即将指针置为 nullptr
 */
void good_set_null_after_free() {
    int* ptr = new int(42);
    delete ptr;
    ptr = nullptr;  // 置空

    if (ptr != nullptr) {
        std::cout << *ptr << std::endl;  // 不会执行
    }
}

/**
 * 正确示例 2：使用 unique_ptr
 *
 * 解决方案：unique_ptr 自动管理，释放后为 nullptr
 */
void good_unique_ptr() {
    auto ptr = std::make_unique<int>(42);
    std::cout << "值: " << *ptr << std::endl;

    ptr.reset();  // 释放内存，ptr 变为 nullptr

    if (ptr) {
        std::cout << *ptr << std::endl;  // 不会执行
    }
}

/**
 * 正确示例 3：使用 shared_ptr 检查引用
 *
 * 解决方案：使用前检查 shared_ptr 是否有效
 */
void good_shared_ptr_check() {
    auto ptr = std::make_shared<int>(42);

    // 使用 weak_ptr 检查
    std::weak_ptr<int> weak = ptr;

    if (auto shared = weak.lock()) {
        std::cout << "值: " << *shared << std::endl;
    } else {
        std::cout << "对象已释放" << std::endl;
    }

    ptr.reset();  // 释放

    if (auto shared = weak.lock()) {
        std::cout << "值: " << *shared << std::endl;
    } else {
        std::cout << "对象已释放" << std::endl;
    }
}

/**
 * 正确示例 4：返回值而非指针
 *
 * 解决方案：直接返回值，利用移动语义
 */
std::vector<int> good_return_value() {
    std::vector<int> vec = {1, 2, 3};
    return vec;  // 移动语义
}

/**
 * 正确示例 5：使用 RAII 管理资源
 *
 * 解决方案：RAII 类在析构时释放资源
 */
class Resource {
public:
    Resource() : data_(new int(42)) {}
    ~Resource() { delete data_; }

    int get() const { return *data_; }

private:
    int* data_;
};

void good_raii() {
    Resource res;
    std::cout << "值: " << res.get() << std::endl;
    // 函数返回时自动释放
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 使用已释放内存陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 直接使用已释放内存" << std::endl;
    std::cout << "问题：delete 后继续使用指针" << std::endl;
    std::cout << "结果：未定义行为" << std::endl;
    // bad_direct_use_after_free();  // 注释掉
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 释放后置空" << std::endl;
    good_set_null_after_free();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 unique_ptr" << std::endl;
    good_unique_ptr();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 shared_ptr 检查引用" << std::endl;
    good_shared_ptr_check();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 返回值而非指针" << std::endl;
    auto vec = good_return_value();
    std::cout << "返回值大小: " << vec.size() << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用 RAII" << std::endl;
    good_raii();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
