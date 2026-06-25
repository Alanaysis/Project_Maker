/**
 * @file 01_object_lifetime.cpp
 * @brief 对象生命周期陷阱示例
 *
 * 对象生命周期陷阱：对象使用时已销毁或未初始化
 * 危害：未定义行为、程序崩溃、数据损坏
 */

#include <iostream>
#include <memory>
#include <vector>
#include <string>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：返回局部对象的引用
 *
 * 问题：局部对象在函数返回后销毁
 */
const int& bad_return_local_ref() {
    int local = 42;
    return local;  // 错误：返回局部对象的引用
}

/**
 * 错误示例 2：使用已销毁的成员
 *
 * 问题：对象销毁后继续使用其成员
 */
class BadOwner {
public:
    BadOwner() : data_(new int(42)) {}
    ~BadOwner() { delete data_; }

    int* get_data() { return data_; }

private:
    int* data_;
};

void bad_use_after_destroy() {
    int* ptr = nullptr;
    {
        BadOwner owner;
        ptr = owner.get_data();
    }  // owner 销毁，data 被释放
    // ptr 悬空
    // std::cout << *ptr << std::endl;  // 未定义行为
}

/**
 * 错误示例 3：容器中的悬空引用
 *
 * 问题：容器扩容后引用失效
 */
void bad_container_reference() {
    std::vector<int> vec = {1, 2, 3};
    int& ref = vec[0];
    vec.push_back(4);  // 可能触发扩容
    // ref 可能失效
    // std::cout << ref << std::endl;  // 未定义行为
}

/**
 * 错误示例 4：临时对象的引用
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
 * 解决方案：直接返回值，利用移动语义
 */
std::vector<int> good_return_value() {
    std::vector<int> vec = {1, 2, 3};
    return vec;  // 移动语义
}

/**
 * 正确示例 2：使用智能指针管理生命周期
 *
 * 解决方案：使用 unique_ptr 明确所有权
 */
class GoodOwner {
public:
    GoodOwner() : data_(std::make_unique<int>(42)) {}

    int* get_data() { return data_.get(); }

private:
    std::unique_ptr<int> data_;
};

void good_smart_pointer() {
    std::unique_ptr<int> ptr;
    {
        GoodOwner owner;
        ptr = std::make_unique<int>(*owner.get_data());
    }
    std::cout << "值: " << *ptr << std::endl;
}

/**
 * 正确示例 3：使用引用计数
 *
 * 解决方案：使用 shared_ptr 共享所有权
 */
void good_shared_ownership() {
    std::shared_ptr<int> ptr;
    {
        auto shared = std::make_shared<int>(42);
        ptr = shared;  // 共享所有权
    }  // shared 销毁，但 ptr 仍持有
    std::cout << "值: " << *ptr << std::endl;
}

/**
 * 正确示例 4：使用稳定容器
 *
 * 解决方案：使用不会使引用失效的容器
 */
#include <list>

void good_stable_container() {
    std::list<int> list = {1, 2, 3};
    auto it = list.begin();
    list.push_back(4);  // 不会使迭代器失效
    std::cout << "第一个元素: " << *it << std::endl;
}

/**
 * 正确示例 5：延长临时对象生命周期
 *
 * 解决方案：使用 const 引用延长临时对象生命周期
 */
void good_extend_temporary() {
    // const 引用延长临时对象生命周期
    const std::string& ref = std::string("hello");
    std::cout << ref << std::endl;  // 安全
}

/**
 * 正确示例 6：使用 RAII 管理资源
 *
 * 解决方案：RAII 类在析构时释放资源
 */
class GoodResource {
public:
    GoodResource() {
        std::cout << "获取资源" << std::endl;
    }
    ~GoodResource() {
        std::cout << "释放资源" << std::endl;
    }

    void use() {
        std::cout << "使用资源" << std::endl;
    }
};

void good_raii() {
    GoodResource res;
    res.use();
    // 函数返回时自动释放
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 对象生命周期陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 返回局部对象的引用" << std::endl;
    std::cout << "问题：局部对象在函数返回后销毁" << std::endl;
    // const int& bad_ref = bad_return_local_ref();
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

    std::cout << "[正确示例 3] 使用引用计数" << std::endl;
    good_shared_ownership();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用稳定容器" << std::endl;
    good_stable_container();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 延长临时对象生命周期" << std::endl;
    good_extend_temporary();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用 RAII" << std::endl;
    good_raii();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
