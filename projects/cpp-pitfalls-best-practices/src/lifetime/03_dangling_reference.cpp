/**
 * @file 03_dangling_reference.cpp
 * @brief 引用悬挂陷阱示例
 *
 * 引用悬挂：引用的对象已销毁
 * 危害：未定义行为、程序崩溃、数据损坏
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <functional>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：返回局部变量的引用
 *
 * 问题：局部变量在函数返回后销毁
 */
const int& bad_return_local() {
    int local = 42;
    return local;  // 错误：返回局部变量的引用
}

/**
 * 错误示例 2：引用已销毁的对象
 *
 * 问题：对象销毁后引用失效
 */
void bad_reference_destroyed() {
    std::string* ptr = new std::string("hello");
    std::string& ref = *ptr;
    delete ptr;  // 对象销毁
    // ref 悬空
    // std::cout << ref << std::endl;  // 未定义行为
}

/**
 * 错误示例 3：容器中的悬挂引用
 *
 * 问题：容器修改后引用失效
 */
void bad_container_reference() {
    std::vector<int> vec = {1, 2, 3};
    int& ref = vec[0];
    vec.push_back(4);  // 可能触发扩容
    // ref 可能失效
    // std::cout << ref << std::endl;  // 未定义行为
}

/**
 * 错误示例 4：lambda 中的悬挂引用
 *
 * 问题：lambda 捕获局部变量的引用
 */
std::function<int()> bad_lambda() {
    int local = 42;
    return [&local]() { return local; };  // 错误：捕获局部变量引用
}

/**
 * 错误示例 5：临时对象的引用
 *
 * 问题：临时对象在语句结束后销毁
 */
void bad_temporary_ref() {
    const std::string& ref = std::string("hello") + " world";
    // 临时对象已销毁
    // std::cout << ref << std::endl;  // 未定义行为
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：返回值而非引用
 *
 * 解决方案：直接返回值
 */
std::vector<int> good_return_value() {
    std::vector<int> vec = {1, 2, 3};
    return vec;  // 移动语义
}

/**
 * 正确示例 2：使用智能指针
 *
 * 解决方案：使用智能指针管理生命周期
 */
void good_smart_pointer() {
    auto ptr = std::make_unique<std::string>("hello");
    std::string& ref = *ptr;
    std::cout << ref << std::endl;  // 安全
}

/**
 * 正确示例 3：使用稳定容器
 *
 * 解决方案：使用不会使引用失效的容器
 */
#include <list>

void good_stable_container() {
    std::list<int> list = {1, 2, 3};
    auto it = list.begin();
    list.push_back(4);  // 不会使迭代器失效
    std::cout << *it << std::endl;  // 安全
}

/**
 * 正确示例 4：按值捕获 lambda
 *
 * 解决方案：按值捕获局部变量
 */
std::function<int()> good_lambda() {
    int local = 42;
    return [local]() { return local; };  // 按值捕获
}

/**
 * 正确示例 5：延长临时对象生命周期
 *
 * 解决方案：使用变量存储临时对象
 */
void good_store_temporary() {
    std::string temp = std::string("hello") + " world";
    const std::string& ref = temp;  // 引用有效
    std::cout << ref << std::endl;
}

/**
 * 正确示例 6：使用 weak_ptr
 *
 * 解决方案：使用 weak_ptr 避免悬挂引用
 */
void good_weak_ptr() {
    std::weak_ptr<std::string> weak;
    {
        auto shared = std::make_shared<std::string>("hello");
        weak = shared;
        if (auto locked = weak.lock()) {
            std::cout << *locked << std::endl;
        }
    }
    // shared 已销毁
    if (auto locked = weak.lock()) {
        std::cout << *locked << std::endl;
    } else {
        std::cout << "对象已销毁" << std::endl;
    }
}

/**
 * 正确示例 7：使用 std::reference_wrapper
 *
 * 解决方案：使用 reference_wrapper 明确引用语义
 */
void good_reference_wrapper() {
    int value = 42;
    std::reference_wrapper<int> ref = std::ref(value);
    std::cout << ref << std::endl;

    ref.get() = 100;
    std::cout << value << std::endl;
}

/**
 * 正确示例 8：使用 std::optional
 *
 * 解决方案：使用 optional 表示可能无值的情况
 */
#include <optional>

std::optional<int> good_find(bool found) {
    if (found) {
        return 42;
    }
    return std::nullopt;
}

void good_optional() {
    auto value = good_find(true);
    if (value) {
        std::cout << *value << std::endl;
    }
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 引用悬挂陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 返回局部变量的引用" << std::endl;
    std::cout << "问题：局部变量在函数返回后销毁" << std::endl;
    // const int& bad_ref = bad_return_local();
    // std::cout << bad_ref << std::endl;  // 未定义行为
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 返回值而非引用" << std::endl;
    auto vec = good_return_value();
    std::cout << "返回值大小: " << vec.size() << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用智能指针" << std::endl;
    good_smart_pointer();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用稳定容器" << std::endl;
    good_stable_container();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 按值捕获 lambda" << std::endl;
    auto lambda = good_lambda();
    std::cout << "lambda 结果: " << lambda() << std::endl;
    std::cout << std::endl;

    std::cout << "[正确示例 5] 存储临时对象" << std::endl;
    good_store_temporary();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用 weak_ptr" << std::endl;
    good_weak_ptr();
    std::cout << std::endl;

    std::cout << "[正确示例 7] 使用 reference_wrapper" << std::endl;
    good_reference_wrapper();
    std::cout << std::endl;

    std::cout << "[正确示例 8] 使用 optional" << std::endl;
    good_optional();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
