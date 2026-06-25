/**
 * C++11 智能指针示例
 *
 * 学习目标：
 * 1. 掌握 unique_ptr 独占所有权
 * 2. 掌握 shared_ptr 共享所有权
 * 3. 掌握 weak_ptr 打破循环引用
 * 4. 学会使用自定义删除器
 * 5. 理解 RAII 原则
 */

#include <iostream>
#include <memory>
#include <vector>
#include <string>
#include <functional>

// ==========================================
// 1. unique_ptr 基础
// ==========================================

class Resource {
    std::string name_;

public:
    Resource(const std::string& name) : name_(name) {
        std::cout << "  [Resource] 构造: " << name_ << std::endl;
    }

    ~Resource() {
        std::cout << "  [Resource] 析构: " << name_ << std::endl;
    }

    void use() const {
        std::cout << "  [Resource] 使用: " << name_ << std::endl;
    }

    const std::string& name() const { return name_; }
};

void demonstrate_unique_ptr() {
    std::cout << "\n=== 1. unique_ptr 基础 ===" << std::endl;

    // 创建 unique_ptr
    std::cout << "--- 创建 ---" << std::endl;
    std::unique_ptr<Resource> ptr1(new Resource("Resource1"));
    ptr1->use();

    // 使用 make_unique（C++14）
    std::cout << "\n--- make_unique ---" << std::endl;
    auto ptr2 = std::make_unique<Resource>("Resource2");
    ptr2->use();

    // unique_ptr 不能拷贝
    // std::unique_ptr<Resource> ptr3 = ptr1;  // 编译错误！

    // unique_ptr 可以移动
    std::cout << "\n--- 移动 ---" << std::endl;
    std::unique_ptr<Resource> ptr3 = std::move(ptr1);
    ptr3->use();
    // ptr1 现在为空
    std::cout << "ptr1 is " << (ptr1 ? "valid" : "null") << std::endl;

    // 重置
    std::cout << "\n--- 重置 ---" << std::endl;
    ptr2.reset();  // 释放资源
    std::cout << "ptr2 is " << (ptr2 ? "valid" : "null") << std::endl;

    // 释放所有权
    std::cout << "\n--- 释放所有权 ---" << std::endl;
    Resource* raw = ptr3.release();  // 放弃所有权
    std::cout << "ptr3 is " << (ptr3 ? "valid" : "null") << std::endl;
    delete raw;  // 需要手动删除
}

// ==========================================
// 2. unique_ptr 与容器
// ==========================================

void demonstrate_unique_ptr_with_containers() {
    std::cout << "\n=== 2. unique_ptr 与容器 ===" << std::endl;

    // 存储在容器中
    std::vector<std::unique_ptr<Resource>> resources;

    resources.push_back(std::make_unique<Resource>("Container1"));
    resources.push_back(std::make_unique<Resource>("Container2"));
    resources.push_back(std::make_unique<Resource>("Container3"));

    std::cout << "--- 遍历容器 ---" << std::endl;
    for (const auto& res : resources) {
        res->use();
    }

    // 移动到容器
    std::cout << "\n--- 移动到容器 ---" << std::endl;
    auto ptr = std::make_unique<Resource>("Movable");
    resources.push_back(std::move(ptr));
    std::cout << "ptr is " << (ptr ? "valid" : "null") << std::endl;

    // 从容器移动
    std::cout << "\n--- 从容器移动 ---" << std::endl;
    auto extracted = std::move(resources[0]);
    extracted->use();
    std::cout << "resources[0] is " << (resources[0] ? "valid" : "null") << std::endl;
}

// ==========================================
// 3. shared_ptr 基础
// ==========================================

void demonstrate_shared_ptr() {
    std::cout << "\n=== 3. shared_ptr 基础 ===" << std::endl;

    // 创建 shared_ptr
    std::cout << "--- 创建 ---" << std::endl;
    std::shared_ptr<Resource> ptr1 = std::make_shared<Resource>("Shared1");
    std::cout << "引用计数: " << ptr1.use_count() << std::endl;

    // 拷贝
    std::cout << "\n--- 拷贝 ---" << std::endl;
    std::shared_ptr<Resource> ptr2 = ptr1;
    std::cout << "ptr1 引用计数: " << ptr1.use_count() << std::endl;
    std::cout << "ptr2 引用计数: " << ptr2.use_count() << std::endl;

    // 移动
    std::cout << "\n--- 移动 ---" << std::endl;
    std::shared_ptr<Resource> ptr3 = std::move(ptr2);
    std::cout << "ptr1 引用计数: " << ptr1.use_count() << std::endl;
    std::cout << "ptr2 is " << (ptr2 ? "valid" : "null") << std::endl;
    std::cout << "ptr3 引用计数: " << ptr3.use_count() << std::endl;

    // 重置
    std::cout << "\n--- 重置 ---" << std::endl;
    ptr3.reset();
    std::cout << "ptr1 引用计数: " << ptr1.use_count() << std::endl;
    std::cout << "ptr3 is " << (ptr3 ? "valid" : "null") << std::endl;
}

// ==========================================
// 4. shared_ptr 共享所有权
// ==========================================

class Node {
public:
    std::string name;
    std::shared_ptr<Node> next;

    Node(const std::string& n) : name(n) {
        std::cout << "  [Node] 构造: " << name << std::endl;
    }

    ~Node() {
        std::cout << "  [Node] 析构: " << name << std::endl;
    }
};

void demonstrate_shared_ownership() {
    std::cout << "\n=== 4. shared_ptr 共享所有权 ===" << std::endl;

    // 创建节点
    auto node1 = std::make_shared<Node>("Node1");
    auto node2 = std::make_shared<Node>("Node2");
    auto node3 = std::make_shared<Node>("Node3");

    // 建立链接
    node1->next = node2;
    node2->next = node3;

    // 多个所有者
    std::vector<std::shared_ptr<Node>> owners;
    owners.push_back(node1);
    owners.push_back(node2);
    owners.push_back(node3);

    std::cout << "\n--- 引用计数 ---" << std::endl;
    std::cout << "node1 引用计数: " << node1.use_count() << std::endl;
    std::cout << "node2 引用计数: " << node2.use_count() << std::endl;
    std::cout << "node3 引用计数: " << node3.use_count() << std::endl;

    // 释放一个所有者
    std::cout << "\n--- 释放一个所有者 ---" << std::endl;
    owners.clear();
    std::cout << "node1 引用计数: " << node1.use_count() << std::endl;
    std::cout << "node2 引用计数: " << node2.use_count() << std::endl;
    std::cout << "node3 引用计数: " << node3.use_count() << std::endl;
}

// ==========================================
// 5. weak_ptr 打破循环引用
// ==========================================

class BadNode {
public:
    std::string name;
    std::shared_ptr<BadNode> next;  // 循环引用！

    BadNode(const std::string& n) : name(n) {
        std::cout << "  [BadNode] 构造: " << name << std::endl;
    }

    ~BadNode() {
        std::cout << "  [BadNode] 析构: " << name << std::endl;
    }
};

class GoodNode {
public:
    std::string name;
    std::weak_ptr<GoodNode> next;  // 使用 weak_ptr 打破循环

    GoodNode(const std::string& n) : name(n) {
        std::cout << "  [GoodNode] 构造: " << name << std::endl;
    }

    ~GoodNode() {
        std::cout << "  [GoodNode] 析构: " << name << std::endl;
    }
};

void demonstrate_weak_ptr() {
    std::cout << "\n=== 5. weak_ptr 打破循环引用 ===" << std::endl;

    // 问题：循环引用导致内存泄漏
    std::cout << "--- 循环引用问题 ---" << std::endl;
    {
        auto node1 = std::make_shared<BadNode>("BadNode1");
        auto node2 = std::make_shared<BadNode>("BadNode2");

        node1->next = node2;
        node2->next = node1;  // 循环引用！

        std::cout << "node1 引用计数: " << node1.use_count() << std::endl;
        std::cout << "node2 引用计数: " << node2.use_count() << std::endl;
    }
    std::cout << "离开作用域，但 BadNode 可能不会析构（内存泄漏）" << std::endl;

    // 解决方案：使用 weak_ptr
    std::cout << "\n--- 使用 weak_ptr ---" << std::endl;
    {
        auto node1 = std::make_shared<GoodNode>("GoodNode1");
        auto node2 = std::make_shared<GoodNode>("GoodNode2");

        node1->next = node2;
        node2->next = node1;  // weak_ptr 不增加引用计数

        std::cout << "node1 引用计数: " << node1.use_count() << std::endl;
        std::cout << "node2 引用计数: " << node2.use_count() << std::endl;

        // 使用 weak_ptr
        if (auto locked = node1->next.lock()) {
            std::cout << "locked->name: " << locked->name << std::endl;
            std::cout << "locked 引用计数: " << locked.use_count() << std::endl;
        }
    }
    std::cout << "离开作用域，GoodNode 正常析构" << std::endl;
}

// ==========================================
// 6. weak_ptr 实际应用：缓存
// ==========================================

class Cache {
    std::weak_ptr<Resource> cached_resource_;

public:
    std::shared_ptr<Resource> get_resource() {
        // 尝试获取缓存的资源
        auto ptr = cached_resource_.lock();
        if (ptr) {
            std::cout << "  [Cache] 命中缓存" << std::endl;
            return ptr;
        }

        // 缓存未命中，创建新资源
        std::cout << "  [Cache] 未命中，创建新资源" << std::endl;
        ptr = std::make_shared<Resource>("CachedResource");
        cached_resource_ = ptr;
        return ptr;
    }
};

void demonstrate_weak_ptr_cache() {
    std::cout << "\n=== 6. weak_ptr 实际应用：缓存 ===" << std::endl;

    Cache cache;

    // 第一次获取
    std::cout << "--- 第一次获取 ---" << std::endl;
    auto res1 = cache.get_resource();
    res1->use();

    // 第二次获取（缓存命中）
    std::cout << "\n--- 第二次获取 ---" << std::endl;
    auto res2 = cache.get_resource();
    res2->use();

    // 释放资源
    std::cout << "\n--- 释放资源 ---" << std::endl;
    res1.reset();
    res2.reset();

    // 再次获取（缓存未命中）
    std::cout << "\n--- 再次获取 ---" << std::endl;
    auto res3 = cache.get_resource();
    res3->use();
}

// ==========================================
// 7. 自定义删除器
// ==========================================

void demonstrate_custom_deleter() {
    std::cout << "\n=== 7. 自定义删除器 ===" << std::endl;

    // unique_ptr 与自定义删除器
    std::cout << "--- unique_ptr 自定义删除器 ---" << std::endl;
    {
        auto deleter = [](Resource* ptr) {
            std::cout << "  自定义删除器调用: " << ptr->name() << std::endl;
            delete ptr;
        };

        std::unique_ptr<Resource, decltype(deleter)> ptr(
            new Resource("CustomDeleter"), deleter);
        ptr->use();
    }

    // shared_ptr 与自定义删除器
    std::cout << "\n--- shared_ptr 自定义删除器 ---" << std::endl;
    {
        auto deleter = [](Resource* ptr) {
            std::cout << "  自定义删除器调用: " << ptr->name() << std::endl;
            delete ptr;
        };

        std::shared_ptr<Resource> ptr(new Resource("SharedCustom"), deleter);
        ptr->use();
    }

    // 文件句柄管理
    std::cout << "\n--- 文件句柄管理 ---" << std::endl;
    {
        auto file_deleter = [](FILE* fp) {
            if (fp) {
                std::cout << "  关闭文件" << std::endl;
                fclose(fp);
            }
        };

        std::unique_ptr<FILE, decltype(file_deleter)> fp(
            fopen("/dev/null", "w"), file_deleter);

        if (fp) {
            std::cout << "  文件打开成功" << std::endl;
        }
    }
}

// ==========================================
// 8. 智能指针最佳实践
// ==========================================

void demonstrate_best_practices() {
    std::cout << "\n=== 8. 智能指针最佳实践 ===" << std::endl;

    // 1. 优先使用 make_unique 和 make_shared
    std::cout << "--- 使用 make_unique/make_shared ---" << std::endl;
    auto ptr1 = std::make_unique<Resource>("BestPractice1");
    auto ptr2 = std::make_shared<Resource>("BestPractice2");

    // 2. 使用 unique_ptr 作为默认选择
    std::cout << "\n--- unique_ptr 作为默认 ---" << std::endl;
    std::unique_ptr<Resource> default_ptr = std::make_unique<Resource>("Default");

    // 3. 只在需要共享所有权时使用 shared_ptr
    std::cout << "\n--- 需要共享时使用 shared_ptr ---" << std::endl;
    std::shared_ptr<Resource> shared = std::make_shared<Resource>("Shared");

    // 4. 使用 weak_ptr 打破循环引用
    std::cout << "\n--- weak_ptr 打破循环 ---" << std::endl;
    std::weak_ptr<Resource> weak = shared;

    // 5. 不要混用裸指针和智能指针
    std::cout << "\n--- 不要混用 ---" << std::endl;
    // 错误示例：
    // Resource* raw = new Resource("Raw");
    // std::shared_ptr<Resource> p1(raw);
    // std::shared_ptr<Resource> p2(raw);  // 双重删除！

    // 正确做法：
    auto p1 = std::make_shared<Resource>("Correct");
    auto p2 = p1;  // 共享所有权
}

// ==========================================
// 主函数
// ==========================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "C++11 智能指针示例" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. unique_ptr 基础
    demonstrate_unique_ptr();

    // 2. unique_ptr 与容器
    demonstrate_unique_ptr_with_containers();

    // 3. shared_ptr 基础
    demonstrate_shared_ptr();

    // 4. shared_ptr 共享所有权
    demonstrate_shared_ownership();

    // 5. weak_ptr 打破循环引用
    demonstrate_weak_ptr();

    // 6. weak_ptr 实际应用：缓存
    demonstrate_weak_ptr_cache();

    // 7. 自定义删除器
    demonstrate_custom_deleter();

    // 8. 智能指针最佳实践
    demonstrate_best_practices();

    std::cout << "\n========================================" << std::endl;
    std::cout << "所有示例执行完毕！" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
