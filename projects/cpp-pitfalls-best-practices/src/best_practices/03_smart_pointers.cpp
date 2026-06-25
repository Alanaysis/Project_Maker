/**
 * @file 03_smart_pointers.cpp
 * @brief 智能指针使用示例
 *
 * 智能指针最佳实践：unique_ptr、shared_ptr、weak_ptr
 */

#include <iostream>
#include <memory>
#include <vector>
#include <string>
#include <functional>

// ============================================================================
// unique_ptr 使用
// ============================================================================

/**
 * unique_ptr 示例 1：独占所有权
 *
 * 特点：独占所有权，不能拷贝，只能移动
 */
class Resource {
public:
    Resource(const std::string& name) : name_(name) {
        std::cout << "创建资源: " << name_ << std::endl;
    }

    ~Resource() {
        std::cout << "销毁资源: " << name_ << std::endl;
    }

    void use() {
        std::cout << "使用资源: " << name_ << std::endl;
    }

private:
    std::string name_;
};

void unique_ptr_example() {
    // 创建 unique_ptr
    auto ptr = std::make_unique<Resource>("资源1");
    ptr->use();

    // 移动所有权
    auto ptr2 = std::move(ptr);
    ptr2->use();

    // ptr 现在为空
    if (!ptr) {
        std::cout << "ptr 为空" << std::endl;
    }
}

/**
 * unique_ptr 示例 2：工厂模式
 *
 * 使用 unique_ptr 实现工厂模式
 */
class Animal {
public:
    virtual ~Animal() = default;
    virtual void speak() const = 0;
};

class Dog : public Animal {
public:
    void speak() const override {
        std::cout << "汪汪！" << std::endl;
    }
};

class Cat : public Animal {
public:
    void speak() const override {
        std::cout << "喵喵！" << std::endl;
    }
};

std::unique_ptr<Animal> create_animal(const std::string& type) {
    if (type == "dog") {
        return std::make_unique<Dog>();
    } else if (type == "cat") {
        return std::make_unique<Cat>();
    }
    return nullptr;
}

void factory_example() {
    auto dog = create_animal("dog");
    auto cat = create_animal("cat");

    if (dog) dog->speak();
    if (cat) cat->speak();
}

/**
 * unique_ptr 示例 3：容器中的 unique_ptr
 *
 * 使用 unique_ptr 管理容器中的对象
 */
void container_example() {
    std::vector<std::unique_ptr<Resource>> resources;

    resources.push_back(std::make_unique<Resource>("资源A"));
    resources.push_back(std::make_unique<Resource>("资源B"));
    resources.push_back(std::make_unique<Resource>("资源C"));

    for (auto& res : resources) {
        res->use();
    }
    // 所有资源自动释放
}

// ============================================================================
// shared_ptr 使用
// ============================================================================

/**
 * shared_ptr 示例 1：共享所有权
 *
 * 特点：共享所有权，引用计数
 */
void shared_ptr_example() {
    auto ptr1 = std::make_shared<Resource>("共享资源");
    std::cout << "引用计数: " << ptr1.use_count() << std::endl;

    {
        auto ptr2 = ptr1;  // 共享所有权
        std::cout << "引用计数: " << ptr1.use_count() << std::endl;
        ptr2->use();
    }  // ptr2 销毁，引用计数减 1

    std::cout << "引用计数: " << ptr1.use_count() << std::endl;
    ptr1->use();
}

/**
 * shared_ptr 示例 2：循环引用问题
 *
 * 问题：循环引用导致内存泄漏
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
    // 内存泄漏！
}

/**
 * shared_ptr 示例 3：使用 weak_ptr 打破循环引用
 *
 * 解决方案：使用 weak_ptr 打破循环引用
 */
struct GoodNode {
    std::weak_ptr<GoodNode> next;  // 使用 weak_ptr
    int value;
};

void good_weak_ptr_example() {
    auto node1 = std::make_shared<GoodNode>();
    auto node2 = std::make_shared<GoodNode>();
    node1->next = node2;
    node2->next = node1;  // 不会导致循环引用
}

/**
 * shared_ptr 示例 4：自定义删除器
 *
 * 使用 shared_ptr 管理非内存资源
 */
void custom_deleter_example() {
    // 使用自定义删除器
    auto file = std::shared_ptr<FILE>(
        fopen("test.txt", "w"),
        [](FILE* f) {
            if (f) {
                fclose(f);
                std::cout << "文件关闭" << std::endl;
            }
        }
    );

    if (file) {
        fputs("Hello, shared_ptr!", file.get());
    }
}

// ============================================================================
// weak_ptr 使用
// ============================================================================

/**
 * weak_ptr 示例 1：观察者模式
 *
 * 使用 weak_ptr 观察对象而不拥有它
 */
class Observer {
public:
    void observe(std::shared_ptr<Resource> resource) {
        resource_ = resource;
    }

    void check() {
        if (auto resource = resource_.lock()) {
            std::cout << "资源仍然存在" << std::endl;
            resource->use();
        } else {
            std::cout << "资源已销毁" << std::endl;
        }
    }

private:
    std::weak_ptr<Resource> resource_;
};

void observer_example() {
    Observer observer;

    {
        auto resource = std::make_shared<Resource>("被观察资源");
        observer.observe(resource);
        observer.check();
    }  // resource 销毁

    observer.check();
}

/**
 * weak_ptr 示例 2：缓存
 *
 * 使用 weak_ptr 实现缓存
 */
class Cache {
public:
    std::shared_ptr<Resource> get(const std::string& key) {
        auto it = cache_.find(key);
        if (it != cache_.end()) {
            if (auto resource = it->second.lock()) {
                std::cout << "缓存命中: " << key << std::endl;
                return resource;
            } else {
                cache_.erase(it);
            }
        }

        std::cout << "缓存未命中: " << key << std::endl;
        auto resource = std::make_shared<Resource>(key);
        cache_[key] = resource;
        return resource;
    }

private:
    std::map<std::string, std::weak_ptr<Resource>> cache_;
};

void cache_example() {
    Cache cache;

    auto res1 = cache.get("资源1");
    auto res2 = cache.get("资源1");  // 缓存命中
}

// ============================================================================
// 智能指针最佳实践
// ============================================================================

/**
 * 最佳实践 1：优先使用 unique_ptr
 *
 * 除非需要共享所有权，否则使用 unique_ptr
 */
void best_practice_unique() {
    // 优先使用 unique_ptr
    auto ptr = std::make_unique<int>(42);
    std::cout << "值: " << *ptr << std::endl;
}

/**
 * 最佳实践 2：使用 make_unique 和 make_shared
 *
 * 使用工厂函数创建智能指针
 */
void best_practice_make() {
    // 推荐
    auto ptr1 = std::make_unique<int>(42);
    auto ptr2 = std::make_shared<int>(42);

    // 不推荐
    // std::unique_ptr<int> ptr3(new int(42));
    // std::shared_ptr<int> ptr4(new int(42));
}

/**
 * 最佳实践 3：避免混合使用原始指针和智能指针
 *
 * 不要同时使用原始指针和智能指针管理同一资源
 */
void best_practice_no_mix() {
    auto ptr = std::make_unique<int>(42);

    // 不要这样做
    // int* raw = ptr.get();
    // delete raw;  // 错误！
}

/**
 * 最佳实践 4：使用智能指针作为函数参数
 *
 * 根据所有权语义选择参数类型
 */
void process_unique(std::unique_ptr<Resource> res) {
    res->use();
    // 函数接管所有权
}

void process_shared(std::shared_ptr<Resource> res) {
    res->use();
    // 共享所有权
}

void process_ref(const Resource& res) {
    res.use();
    // 不涉及所有权
}

/**
 * 最佳实践 5：使用智能指针作为返回值
 *
 * 工厂函数返回 unique_ptr
 */
std::unique_ptr<Resource> create_resource(const std::string& name) {
    return std::make_unique<Resource>(name);
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 智能指针使用示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "[1] unique_ptr 独占所有权" << std::endl;
    unique_ptr_example();
    std::cout << std::endl;

    std::cout << "[2] 工厂模式" << std::endl;
    factory_example();
    std::cout << std::endl;

    std::cout << "[3] 容器中的 unique_ptr" << std::endl;
    container_example();
    std::cout << std::endl;

    std::cout << "[4] shared_ptr 共享所有权" << std::endl;
    shared_ptr_example();
    std::cout << std::endl;

    std::cout << "[5] weak_ptr 打破循环引用" << std::endl;
    good_weak_ptr_example();
    std::cout << std::endl;

    std::cout << "[6] 自定义删除器" << std::endl;
    custom_deleter_example();
    std::cout << std::endl;

    std::cout << "[7] 观察者模式" << std::endl;
    observer_example();
    std::cout << std::endl;

    std::cout << "[8] 缓存" << std::endl;
    cache_example();
    std::cout << std::endl;

    std::cout << "[9] 最佳实践" << std::endl;
    best_practice_unique();
    best_practice_make();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
