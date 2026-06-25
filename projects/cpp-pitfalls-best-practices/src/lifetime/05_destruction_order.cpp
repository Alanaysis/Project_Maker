/**
 * @file 05_destruction_order.cpp
 * @brief 析构顺序陷阱示例
 *
 * 析构顺序：对象销毁顺序导致的问题
 * 危害：悬挂引用、资源泄漏、程序崩溃
 */

#include <iostream>
#include <string>
#include <memory>
#include <vector>
#include <functional>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：成员析构顺序
 *
 * 问题：成员按声明顺序的逆序析构
 */
class BadMemberOrder {
public:
    BadMemberOrder() {
        data_ = new int(42);
        ref_ = data_;  // ref_ 指向 data_
    }

    ~BadMemberOrder() {
        // data_ 先于 ref_ 析构（因为 ref_ 声明在后）
        // 但实际析构顺序是声明的逆序
        // 所以 ref_ 先析构，data_ 后析构
    }

private:
    int* data_;
    int* ref_;  // 悬挂引用
};

/**
 * 错误示例 2：全局对象析构顺序
 *
 * 问题：全局对象析构顺序不确定
 */
class BadGlobal {
public:
    BadGlobal() { std::cout << "BadGlobal 构造" << std::endl; }
    ~BadGlobal() { std::cout << "BadGlobal 析构" << std::endl; }
};

// 全局对象，析构顺序不确定
// BadGlobal global1;
// BadGlobal global2;

/**
 * 错误示例 3：静态对象析构顺序
 *
 * 问题：静态对象析构顺序与构造顺序相反
 */
class BadStatic {
public:
    BadStatic(const std::string& name) : name_(name) {
        std::cout << name_ << " 构造" << std::endl;
    }
    ~BadStatic() {
        std::cout << name_ << " 析构" << std::endl;
    }

private:
    std::string name_;
};

// 静态对象
// BadStatic static1("static1");
// BadStatic static2("static2");

/**
 * 错误示例 4：循环引用的析构
 *
 * 问题：循环引用导致内存泄漏
 */
struct BadNode {
    std::shared_ptr<BadNode> next;
    int value;
};

void bad_circular() {
    auto node1 = std::make_shared<BadNode>();
    auto node2 = std::make_shared<BadNode>();
    node1->next = node2;
    node2->next = node1;  // 循环引用
    // 析构时引用计数不为 0，内存泄漏
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：正确的成员声明顺序
 *
 * 解决方案：按依赖关系声明成员
 */
class GoodMemberOrder {
public:
    GoodMemberOrder() {
        data_ = new int(42);
        ref_ = data_;  // ref_ 指向 data_
    }

    ~GoodMemberOrder() {
        // ref_ 先析构（因为它后声明），data_ 后析构
        // 这是安全的
    }

private:
    int* ref_;  // 先声明，后析构
    int* data_;  // 后声明，先析构
};

/**
 * 正确示例 2：使用智能指针管理生命周期
 *
 * 解决方案：使用智能指针明确所有权
 */
class GoodSmartPointer {
public:
    GoodSmartPointer() : data_(std::make_unique<int>(42)) {}

    int* get_data() { return data_.get(); }

private:
    std::unique_ptr<int> data_;
};

void good_smart_pointer() {
    GoodSmartPointer obj;
    std::cout << "值: " << *obj.get_data() << std::endl;
}

/**
 * 正确示例 3：使用 weak_ptr 打破循环引用
 *
 * 解决方案：使用 weak_ptr 打破循环引用
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
 * 正确示例 4：使用 RAII 管理资源
 *
 * 解决方案：RAII 类在析构时释放资源
 */
class GoodResource {
public:
    GoodResource() { std::cout << "获取资源" << std::endl; }
    ~GoodResource() { std::cout << "释放资源" << std::endl; }

    void use() { std::cout << "使用资源" << std::endl; }
};

void good_raii() {
    GoodResource res;
    res.use();
    // 函数返回时自动释放
}

/**
 * 正确示例 5：使用 std::atexit 注册清理函数
 *
 * 解决方案：使用 atexit 注册清理函数
 */
void cleanup() {
    std::cout << "清理函数" << std::endl;
}

void good_atexit() {
    std::atexit(cleanup);
    std::cout << "注册清理函数" << std::endl;
}

/**
 * 正确示例 6：使用单例模式
 *
 * 解决方案：使用单例模式控制全局对象生命周期
 */
class GoodSingleton {
public:
    static GoodSingleton& instance() {
        static GoodSingleton inst;
        return inst;
    }

    void do_something() {
        std::cout << "单例操作" << std::endl;
    }

private:
    GoodSingleton() { std::cout << "单例构造" << std::endl; }
    ~GoodSingleton() { std::cout << "单例析构" << std::endl; }
};

void good_singleton() {
    GoodSingleton::instance().do_something();
}

/**
 * 正确示例 7：使用依赖注入
 *
 * 解决方案：通过依赖注入控制对象生命周期
 */
class GoodDependency {
public:
    void do_work() { std::cout << "依赖工作" << std::endl; }
};

class GoodService {
public:
    GoodService(std::shared_ptr<GoodDependency> dep) : dep_(dep) {}

    void serve() {
        dep_->do_work();
    }

private:
    std::shared_ptr<GoodDependency> dep_;
};

void good_dependency_injection() {
    auto dep = std::make_shared<GoodDependency>();
    GoodService service(dep);
    service.serve();
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 析构顺序陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 成员析构顺序" << std::endl;
    std::cout << "问题：成员按声明顺序的逆序析构" << std::endl;
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 正确的成员声明顺序" << std::endl;
    GoodMemberOrder obj;
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用智能指针" << std::endl;
    good_smart_pointer();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 weak_ptr" << std::endl;
    good_weak_ptr();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 RAII" << std::endl;
    good_raii();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用 atexit" << std::endl;
    good_atexit();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用单例模式" << std::endl;
    good_singleton();
    std::cout << std::endl;

    std::cout << "[正确示例 7] 使用依赖注入" << std::endl;
    good_dependency_injection();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
