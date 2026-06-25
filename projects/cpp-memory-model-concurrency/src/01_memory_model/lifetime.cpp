/**
 * 生命周期 (Lifetime)
 *
 * 对象生命周期的管理：
 * 1. 对象在构造完成时开始生命周期
 * 2. 对象在析构完成时结束生命周期
 * 3. 访问生命周期外的对象是未定义行为
 * 4. 不同存储期的对象有不同的生命周期
 *
 * 编译：g++ -std=c++17 -pthread lifetime.cpp -o lifetime
 */

#include <iostream>
#include <memory>
#include <vector>
#include <string>

// 示例1：基本生命周期
class Resource {
public:
    Resource(const std::string& name) : name_(name) {
        std::cout << "Resource " << name_ << " 创建" << std::endl;
    }

    ~Resource() {
        std::cout << "Resource " << name_ << " 销毁" << std::endl;
    }

    void use() const {
        std::cout << "使用 Resource " << name_ << std::endl;
    }

private:
    std::string name_;
};

void basic_lifetime() {
    std::cout << "=== 基本生命周期 ===" << std::endl;

    // 局部对象的生命周期
    {
        Resource r1("局部对象");
        r1.use();
    } // r1 在此销毁

    std::cout << "局部对象已销毁" << std::endl;

    // 动态对象的生命周期
    Resource* r2 = new Resource("动态对象");
    r2->use();
    delete r2;  // 必须手动销毁
    std::cout << "动态对象已销毁" << std::endl;
}

// 示例2：RAII (Resource Acquisition Is Initialization)
class RAIIExample {
public:
    RAIIExample(int* resource) : resource_(resource) {
        std::cout << "RAII: 获取资源" << std::endl;
    }

    ~RAIIExample() {
        std::cout << "RAII: 释放资源" << std::endl;
        delete resource_;
    }

    int* get() const { return resource_; }

private:
    int* resource_;
};

void raii_lifetime() {
    std::cout << "\n=== RAII 生命周期管理 ===" << std::endl;

    {
        int* raw = new int(42);
        RAIIExample raii(raw);
        std::cout << "值: " << *raii.get() << std::endl;
    } // raii 析构时自动释放资源

    std::cout << "资源已自动释放" << std::endl;
}

// 示例3：智能指针的生命周期
void smart_pointer_lifetime() {
    std::cout << "\n=== 智能指针的生命周期 ===" << std::endl;

    // unique_ptr：独占所有权
    {
        auto ptr = std::make_unique<Resource>("unique_ptr");
        ptr->use();
    } // 自动销毁

    // shared_ptr：共享所有权
    {
        std::shared_ptr<Resource> ptr1;
        {
            auto ptr2 = std::make_shared<Resource>("shared_ptr");
            ptr1 = ptr2;  // 共享所有权
            std::cout << "引用计数: " << ptr1.use_count() << std::endl;
        } // ptr2 销毁，但对象还在
        std::cout << "引用计数: " << ptr1.use_count() << std::endl;
        ptr1->use();
    } // ptr1 销毁，对象销毁

    // weak_ptr：弱引用
    std::weak_ptr<Resource> weak;
    {
        auto shared = std::make_shared<Resource>("weak_ptr");
        weak = shared;
        std::cout << "weak_ptr 是否有效: " << (weak.expired() ? "否" : "是") << std::endl;
    } // shared 销毁
    std::cout << "weak_ptr 是否有效: " << (weak.expired() ? "否" : "是") << std::endl;
}

// 示例4：对象数组的生命周期
void array_lifetime() {
    std::cout << "\n=== 对象数组的生命周期 ===" << std::endl;

    // 栈上数组
    {
        Resource arr[3] = {{"A"}, {"B"}, {"C"}};
        std::cout << "数组创建完成" << std::endl;
    } // 逆序析构：C, B, A

    std::cout << "\n使用 vector:" << std::endl;
    {
        std::vector<Resource> vec;
        vec.reserve(3);
        vec.emplace_back("D");
        vec.emplace_back("E");
        vec.emplace_back("F");
        std::cout << "vector 创建完成" << std::endl;
    } // 逆序析构：F, E, D
}

// 示例5：生命周期延长
void lifetime_extension() {
    std::cout << "\n=== 生命周期延长 ===" << std::endl;

    // const 引用延长临时对象的生命周期
    {
        const Resource& r = Resource("临时对象");
        r.use();
    } // 临时对象在此销毁

    // 右值引用延长临时对象的生命周期
    {
        Resource&& r = Resource("临时对象");
        r.use();
    } // 临时对象在此销毁
}

// 示例6：悬垂引用（危险！）
void dangling_reference_demo() {
    std::cout << "\n=== 悬垂引用示例（仅演示概念） ===" << std::endl;

    // 危险代码：返回局部变量的引用
    // int& get_value() {
    //     int x = 42;
    //     return x;  // 危险！返回局部变量的引用
    // }

    // 安全代码：返回值
    auto get_value = []() -> int {
        int x = 42;
        return x;  // 安全：返回值的拷贝
    };

    int value = get_value();
    std::cout << "安全返回值: " << value << std::endl;
}

// 示例7：对象的构造和析构顺序
class OrderedResource {
public:
    OrderedResource(const std::string& name, int order)
        : name_(name), order_(order) {
        std::cout << "构造 " << name_ << " (顺序 " << order_ << ")" << std::endl;
    }

    ~OrderedResource() {
        std::cout << "析构 " << name_ << " (顺序 " << order_ << ")" << std::endl;
    }

private:
    std::string name_;
    int order_;
};

void construction_destruction_order() {
    std::cout << "\n=== 构造和析构顺序 ===" << std::endl;

    std::cout << "构造顺序（从上到下）:" << std::endl;
    OrderedResource r1("资源1", 1);
    OrderedResource r2("资源2", 2);
    OrderedResource r3("资源3", 3);

    std::cout << "\n析构顺序（从下到上）:" << std::endl;
    // 析构顺序：r3, r2, r1（与构造顺序相反）
}

int main() {
    std::cout << "C++ 内存模型：生命周期 (Lifetime)" << std::endl;
    std::cout << "===================================\n" << std::endl;

    basic_lifetime();
    raii_lifetime();
    smart_pointer_lifetime();
    array_lifetime();
    lifetime_extension();
    dangling_reference_demo();
    construction_destruction_order();

    return 0;
}
