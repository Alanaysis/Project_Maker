/**
 * @file 04_value_semantics.cpp
 * @brief 值语义 vs 引用语义示例
 *
 * 值语义：对象被复制，副本独立
 * 引用语义：对象被共享，通过指针或引用访问
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <functional>

// ============================================================================
// 值语义示例
// ============================================================================

/**
 * 值语义示例 1：简单的值类型
 *
 * 特点：拷贝后副本独立
 */
class Point {
public:
    Point(int x, int y) : x_(x), y_(y) {}

    int x() const { return x_; }
    int y() const { return y_; }

    void set_x(int x) { x_ = x; }
    void set_y(int y) { y_ = y; }

private:
    int x_;
    int y_;
};

void value_semantics_example() {
    Point p1(1, 2);
    Point p2 = p1;  // 拷贝

    p2.set_x(10);

    std::cout << "p1: (" << p1.x() << ", " << p1.y() << ")" << std::endl;
    std::cout << "p2: (" << p2.x() << ", " << p2.y() << ")" << std::endl;
    // p1 和 p2 独立
}

/**
 * 值语义示例 2：字符串
 *
 * 标准库字符串是值语义
 */
void string_value_semantics() {
    std::string s1 = "hello";
    std::string s2 = s1;  // 拷贝

    s2 += " world";

    std::cout << "s1: " << s1 << std::endl;
    std::cout << "s2: " << s2 << std::endl;
    // s1 和 s2 独立
}

/**
 * 值语义示例 3：容器
 *
 * 标准库容器是值语义
 */
void vector_value_semantics() {
    std::vector<int> v1 = {1, 2, 3};
    std::vector<int> v2 = v1;  // 拷贝

    v2.push_back(4);

    std::cout << "v1 大小: " << v1.size() << std::endl;
    std::cout << "v2 大小: " << v2.size() << std::endl;
    // v1 和 v2 独立
}

/**
 * 值语义示例 4：移动语义
 *
 * 使用移动语义避免不必要的拷贝
 */
void move_semantics() {
    std::vector<int> v1 = {1, 2, 3};
    std::vector<int> v2 = std::move(v1);  // 移动

    std::cout << "v1 大小: " << v1.size() << std::endl;
    std::cout << "v2 大小: " << v2.size() << std::endl;
    // v1 被移动，v2 拥有数据
}

// ============================================================================
// 引用语义示例
// ============================================================================

/**
 * 引用语义示例 1：使用指针
 *
 * 特点：多个指针可以指向同一对象
 */
class SharedResource {
public:
    SharedResource(const std::string& name) : name_(name) {
        std::cout << "创建: " << name_ << std::endl;
    }

    ~SharedResource() {
        std::cout << "销毁: " << name_ << std::endl;
    }

    void use() {
        std::cout << "使用: " << name_ << std::endl;
    }

private:
    std::string name_;
};

void pointer_semantics() {
    SharedResource* p1 = new SharedResource("资源1");
    SharedResource* p2 = p1;  // 共享

    p1->use();
    p2->use();

    delete p1;  // 只能删除一次
    // p2 悬空！
}

/**
 * 引用语义示例 2：使用 shared_ptr
 *
 * 使用智能指针管理共享对象
 */
void shared_ptr_semantics() {
    auto p1 = std::make_shared<SharedResource>("资源2");
    auto p2 = p1;  // 共享所有权

    p1->use();
    p2->use();

    std::cout << "引用计数: " << p1.use_count() << std::endl;
    // 自动释放
}

/**
 * 引用语义示例 3：使用引用
 *
 * 引用是别名，不是新对象
 */
void reference_semantics() {
    int x = 42;
    int& ref = x;  // 引用

    ref = 100;
    std::cout << "x = " << x << std::endl;
    // x 和 ref 是同一个对象
}

// ============================================================================
// 值语义 vs 引用语义的选择
// ============================================================================

/**
 * 选择指南 1：小对象使用值语义
 *
 * 小对象拷贝成本低，使用值语义更简单
 */
class SmallObject {
public:
    SmallObject(int value) : value_(value) {}
    int value() const { return value_; }

private:
    int value_;
};

void small_object_example() {
    SmallObject obj1(42);
    SmallObject obj2 = obj1;  // 拷贝成本低
    std::cout << "值: " << obj2.value() << std::endl;
}

/**
 * 选择指南 2：大对象使用引用语义
 *
 * 大对象拷贝成本高，使用引用语义更高效
 */
class LargeObject {
public:
    LargeObject(size_t size) : data_(size, 0) {}
    size_t size() const { return data_.size(); }

private:
    std::vector<int> data_;
};

void large_object_example() {
    auto obj1 = std::make_shared<LargeObject>(1000000);
    auto obj2 = obj1;  // 共享，不拷贝
    std::cout << "大小: " << obj2->size() << std::endl;
}

/**
 * 选择指南 3：多态使用引用语义
 *
 * 多态需要指针或引用
 */
class Shape {
public:
    virtual ~Shape() = default;
    virtual void draw() const = 0;
};

class Circle : public Shape {
public:
    void draw() const override {
        std::cout << "绘制圆形" << std::endl;
    }
};

class Rectangle : public Shape {
public:
    void draw() const override {
        std::cout << "绘制矩形" << std::endl;
    }
};

void polymorphism_example() {
    std::vector<std::unique_ptr<Shape>> shapes;
    shapes.push_back(std::make_unique<Circle>());
    shapes.push_back(std::make_unique<Rectangle>());

    for (const auto& shape : shapes) {
        shape->draw();
    }
}

/**
 * 选择指南 4：所有权明确使用 unique_ptr
 *
 * 独占所有权使用 unique_ptr
 */
void ownership_example() {
    auto resource = std::make_unique<SharedResource>("独占资源");
    resource->use();
    // 明确的所有权
}

/**
 * 选择指南 5：共享所有权使用 shared_ptr
 *
 * 多个所有者使用 shared_ptr
 */
void sharing_example() {
    auto resource = std::make_shared<SharedResource>("共享资源");
    auto copy = resource;  // 共享所有权
    resource->use();
    copy->use();
}

// ============================================================================
// 最佳实践
// ============================================================================

/**
 * 最佳实践 1：默认使用值语义
 *
 * 除非有特殊需求，否则使用值语义
 */
void best_practice_default_value() {
    // 默认使用值语义
    std::string s = "hello";
    std::vector<int> v = {1, 2, 3};
    Point p(1, 2);
}

/**
 * 最佳实践 2：使用移动语义
 *
 * 需要转移所有权时使用移动语义
 */
void best_practice_move() {
    std::vector<int> v1 = {1, 2, 3};
    std::vector<int> v2 = std::move(v1);
}

/**
 * 最佳实践 3：明确所有权
 *
 * 使用智能指针明确所有权
 */
void best_practice_ownership() {
    // 独占所有权
    auto unique = std::make_unique<int>(42);

    // 共享所有权
    auto shared = std::make_shared<int>(42);
}

/**
 * 最佳实践 4：避免不必要的堆分配
 *
 * 优先使用栈分配
 */
void best_practice_stack() {
    // 栈分配
    Point p(1, 2);
    std::string s = "hello";
    std::vector<int> v = {1, 2, 3};

    // 堆分配（仅在必要时）
    auto ptr = std::make_unique<LargeObject>(1000000);
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 值语义 vs 引用语义示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "[1] 值语义：Point" << std::endl;
    value_semantics_example();
    std::cout << std::endl;

    std::cout << "[2] 值语义：字符串" << std::endl;
    string_value_semantics();
    std::cout << std::endl;

    std::cout << "[3] 值语义：容器" << std::endl;
    vector_value_semantics();
    std::cout << std::endl;

    std::cout << "[4] 移动语义" << std::endl;
    move_semantics();
    std::cout << std::endl;

    std::cout << "[5] 引用语义：shared_ptr" << std::endl;
    shared_ptr_semantics();
    std::cout << std::endl;

    std::cout << "[6] 引用语义：引用" << std::endl;
    reference_semantics();
    std::cout << std::endl;

    std::cout << "[7] 多态：引用语义" << std::endl;
    polymorphism_example();
    std::cout << std::endl;

    std::cout << "[8] 最佳实践" << std::endl;
    best_practice_default_value();
    best_practice_move();
    best_practice_ownership();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
