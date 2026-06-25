// =============================================================================
// type_erasure.cpp - 类型擦除演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o type_erasure type_erasure.cpp
// 运行: ./type_erasure
// =============================================================================

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include "utilities/type_erasure.hpp"

// 用于演示 Drawable 的具体类型
class Circle {
public:
    Circle(double r) : radius_(r) {}
    void draw() const {
        std::cout << "  Drawing Circle with radius " << radius_ << std::endl;
    }
private:
    double radius_;
};

class Rectangle {
public:
    Rectangle(double w, double h) : width_(w), height_(h) {}
    void draw() const {
        std::cout << "  Drawing Rectangle " << width_ << "x" << height_ << std::endl;
    }
private:
    double width_, height_;
};

class Triangle {
public:
    Triangle(double a, double b, double c) : a_(a), b_(b), c_(c) {}
    void draw() const {
        std::cout << "  Drawing Triangle with sides " << a_ << ", " << b_ << ", " << c_ << std::endl;
    }
private:
    double a_, b_, c_;
};

// 用于演示 Any 的自定义类型
struct Point {
    double x, y;
    std::string to_string() const {
        return "(" + std::to_string(x) + ", " + std::to_string(y) + ")";
    }
};

// 用于演示类型擦除的多态集合
struct Dog {
    void speak() const { std::cout << "  Woof!" << std::endl; }
};

struct Cat {
    void speak() const { std::cout << "  Meow!" << std::endl; }
};

struct Bird {
    void speak() const { std::cout << "  Tweet!" << std::endl; }
};

struct Speakable {
    template <typename T>
    Speakable(T obj) : pimpl_(std::make_unique<Model<T>>(std::move(obj))) {}

    void speak() const { pimpl_->speak(); }

private:
    struct Concept {
        virtual ~Concept() = default;
        virtual void speak() const = 0;
    };

    template <typename T>
    struct Model : Concept {
        T obj_;
        Model(T o) : obj_(std::move(o)) {}
        void speak() const override { obj_.speak(); }
    };

    std::unique_ptr<Concept> pimpl_;
};

int main() {
    std::cout << "=== 类型擦除演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. Drawable 类型擦除
    std::cout << "1. Drawable 类型擦除:" << std::endl;
    std::vector<tmp::Drawable> shapes;
    shapes.push_back(tmp::Drawable(Circle(5.0)));
    shapes.push_back(tmp::Drawable(Rectangle(3.0, 4.0)));
    shapes.push_back(tmp::Drawable(Triangle(3.0, 4.0, 5.0)));

    for (const auto& shape : shapes) {
        shape.draw();
    }

    // 测试拷贝
    tmp::Drawable copy = shapes[0];
    std::cout << "  Copy: ";
    copy.draw();
    std::cout << std::endl;

    // 2. Any 类型擦除容器
    std::cout << "2. Any 类型擦除容器:" << std::endl;
    tmp::Any a1(42);
    tmp::Any a2(3.14);
    tmp::Any a3(std::string("hello"));

    std::cout << "  a1 (int): " << a1.get<int>() << std::endl;
    std::cout << "  a2 (double): " << a2.get<double>() << std::endl;
    std::cout << "  a3 (string): " << a3.get<std::string>() << std::endl;
    std::cout << "  a1 type: " << a1.type().name() << std::endl;
    std::cout << "  a2 type: " << a2.type().name() << std::endl;

    // 测试拷贝
    tmp::Any a4 = a1;
    std::cout << "  a4 (copy of a1): " << a4.get<int>() << std::endl;

    // 测试异常
    try {
        a1.get<double>();
    } catch (const std::bad_cast& e) {
        std::cout << "  Bad cast caught: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    // 3. Function 类型擦除
    std::cout << "3. Function 类型擦除:" << std::endl;

    // Lambda
    tmp::Function<int(int)> f1 = [](int x) { return x * 2; };
    std::cout << "  f1(5) = " << f1(5) << std::endl;

    // 函数指针
    auto add = [](int a, int b) { return a + b; };
    tmp::Function<int(int, int)> f2 = add;
    std::cout << "  f2(3, 4) = " << f2(3, 4) << std::endl;

    // 带捕获的 Lambda
    int factor = 10;
    tmp::Function<int(int)> f3 = [factor](int x) { return x * factor; };
    std::cout << "  f3(5) = " << f3(5) << std::endl;

    // 空函数调用
    tmp::Function<void()> f4;
    try {
        f4();
    } catch (const std::bad_function_call& e) {
        std::cout << "  Empty function call caught: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    // 4. 类型擦除的多态集合
    std::cout << "4. 类型擦除的多态集合:" << std::endl;

    std::vector<Speakable> animals;
    animals.push_back(Speakable(Dog{}));
    animals.push_back(Speakable(Cat{}));
    animals.push_back(Speakable(Bird{}));

    for (const auto& animal : animals) {
        animal.speak();
    }
    std::cout << std::endl;

    // 5. 类型擦除的优势
    std::cout << "5. 类型擦除的优势:" << std::endl;
    std::cout << "  - 无需继承层次" << std::endl;
    std::cout << "  - 值语义（可拷贝、可移动）" << std::endl;
    std::cout << "  - 类型安全的统一接口" << std::endl;
    std::cout << "  - 避免虚函数继承的耦合" << std::endl;
    std::cout << "  - 典型应用: std::function, std::any, std::shared_ptr" << std::endl;
    std::cout << std::endl;

    std::cout << "=== 类型擦除演示完成 ===" << std::endl;
    return 0;
}
