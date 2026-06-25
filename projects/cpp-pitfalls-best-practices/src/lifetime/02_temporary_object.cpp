/**
 * @file 02_temporary_object.cpp
 * @brief 临时对象陷阱示例
 *
 * 临时对象陷阱：临时对象的创建和销毁导致的问题
 * 危害：性能下降、悬挂引用、意外行为
 */

#include <iostream>
#include <string>
#include <vector>
#include <chrono>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：不必要的临时对象
 *
 * 问题：创建不必要的临时对象，影响性能
 */
void bad_unnecessary_temporary() {
    std::vector<int> vec;
    // 每次循环创建临时 vector
    for (int i = 0; i < 1000; i++) {
        vec = std::vector<int>(100, i);  // 创建临时对象
    }
}

/**
 * 错误示例 2：临时对象的引用
 *
 * 问题：临时对象在语句结束后销毁
 */
void bad_temporary_reference() {
    // const 引用延长生命周期，但仅限当前语句
    const std::string& ref = std::string("hello") + " world";
    // 临时对象已销毁
    // std::cout << ref << std::endl;  // 未定义行为
}

/**
 * 错误示例 3：临时对象的指针
 *
 * 问题：获取临时对象的指针
 */
void bad_temporary_pointer() {
    std::string* ptr = &std::string("hello");  // 错误！
    // 临时对象已销毁
}

/**
 * 错误示例 4：临时对象的迭代器
 *
 * 问题：获取临时容器的迭代器
 */
void bad_temporary_iterator() {
    auto it = std::vector<int>{1, 2, 3}.begin();
    // 临时 vector 已销毁
    // std::cout << *it << std::endl;  // 未定义行为
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：避免不必要的临时对象
 *
 * 解决方案：直接初始化，避免临时对象
 */
void good_no_temporary() {
    std::vector<int> vec(100, 0);
    for (int i = 0; i < 1000; i++) {
        std::fill(vec.begin(), vec.end(), i);  // 直接修改
    }
}

/**
 * 正确示例 2：使用移动语义
 *
 * 解决方案：使用移动语义避免拷贝
 */
void good_move_semantics() {
    std::vector<int> vec;
    for (int i = 0; i < 1000; i++) {
        std::vector<int> temp(100, i);
        vec = std::move(temp);  // 移动而非拷贝
    }
}

/**
 * 正确示例 3：延长临时对象生命周期
 *
 * 解决方案：使用 const 引用延长生命周期
 */
void good_extend_lifetime() {
    // const 引用延长临时对象生命周期
    const std::string& ref = std::string("hello");
    std::cout << ref << std::endl;  // 安全
}

/**
 * 正确示例 4：使用变量存储临时对象
 *
 * 解决方案：将临时对象存储在变量中
 */
void good_store_temporary() {
    std::string temp = std::string("hello") + " world";
    const std::string& ref = temp;  // 引用有效
    std::cout << ref << std::endl;
}

/**
 * 正确示例 5：使用 auto 推导
 *
 * 解决方案：使用 auto 存储临时对象
 */
void good_auto() {
    auto vec = std::vector<int>{1, 2, 3};
    auto it = vec.begin();  // 迭代器有效
    std::cout << *it << std::endl;
}

/**
 * 正确示例 6：使用完美转发
 *
 * 解决方案：使用完美转发避免不必要的拷贝
 */
template <typename T>
void good_perfect_forwarding(T&& arg) {
    // 完美转发，避免临时对象
    std::vector<int> vec = std::forward<T>(arg);
    std::cout << "大小: " << vec.size() << std::endl;
}

void good_perfect_forwarding_example() {
    std::vector<int> original = {1, 2, 3};
    good_perfect_forwarding(original);  // 左值引用
    good_perfect_forwarding(std::vector<int>{4, 5, 6});  // 右值引用
}

/**
 * 正确示例 7：使用 emplace_back
 *
 * 解决方案：使用 emplace_back 原地构造
 */
void good_emplace() {
    std::vector<std::string> vec;

    // push_back 创建临时对象
    vec.push_back(std::string("hello"));

    // emplace_back 原地构造
    vec.emplace_back("world");

    for (const auto& s : vec) {
        std::cout << s << " ";
    }
    std::cout << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 临时对象陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 不必要的临时对象" << std::endl;
    std::cout << "问题：创建不必要的临时对象，影响性能" << std::endl;
    // bad_unnecessary_temporary();  // 性能问题
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 避免不必要的临时对象" << std::endl;
    good_no_temporary();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用移动语义" << std::endl;
    good_move_semantics();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 延长临时对象生命周期" << std::endl;
    good_extend_lifetime();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 存储临时对象" << std::endl;
    good_store_temporary();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用 auto" << std::endl;
    good_auto();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用完美转发" << std::endl;
    good_perfect_forwarding_example();
    std::cout << std::endl;

    std::cout << "[正确示例 7] 使用 emplace_back" << std::endl;
    good_emplace();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
