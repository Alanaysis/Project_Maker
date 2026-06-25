/**
 * CRTP (Curiously Recurring Template Pattern) 奇异递归模板模式演示
 *
 * CRTP 是 C++ 模板元编程中的一个重要模式，它通过将派生类作为模板参数传递给基类，
 * 实现了编译期多态，避免了虚函数的运行时开销。
 *
 * 基本形式：
 *   template<typename Derived>
 *   class Base { ... };
 *
 *   class MyClass : public Base<MyClass> { ... };
 *
 * 主要应用：
 *   1. 静态多态 (Static Polymorphism)
 *   2. Mixin 类
 *   3. 计数器
 *   4. 运算符重载
 *   5. 单例模式
 *
 * 优点：
 *   - 没有虚函数开销
 *   - 编译期绑定，性能更好
 *   - 可以内联优化
 *
 * 缺点：
 *   - 代码可读性较差
 *   - 编译错误信息复杂
 *   - 不能使用基类指针（除非额外包装）
 *
 * 编译命令：g++ -std=c++17 -O2 -o crtp crtp.cpp
 */

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <chrono>
#include <numeric>
#include <functional>
#include <cmath>

// ============================================================================
// 第一部分：静态多态
// ============================================================================

/**
 * Shape<Derived> - 使用 CRTP 实现静态多态
 *
 * 与虚函数不同，这里的 draw() 调用在编译期就确定了
 * 编译器可以直接内联派生类的实现
 */
template<typename Derived>
class Shape {
public:
    // 调用派生类的 do_draw 实现
    void draw() const {
        // static_cast 将 this 转换为派生类指针
        // 这是安全的，因为 Derived 必须继承自 Shape<Derived>
        static_cast<const Derived*>(this)->do_draw();
    }

    // 获取面积
    double area() const {
        return static_cast<const Derived*>(this)->do_area();
    }

    // 获取周长
    double perimeter() const {
        return static_cast<const Derived*>(this)->do_perimeter();
    }

    // 打印信息
    void print() const {
        std::cout << "形状: " << static_cast<const Derived*>(this)->name()
                  << ", 面积: " << area()
                  << ", 周长: " << perimeter() << std::endl;
    }
};

/**
 * Circle - 圆形，继承自 Shape<Circle>
 */
class Circle : public Shape<Circle> {
    double radius_;

public:
    explicit Circle(double r) : radius_(r) {}

    // 实现 do_draw，供基类调用
    void do_draw() const {
        std::cout << "绘制圆形，半径: " << radius_ << std::endl;
    }

    double do_area() const {
        return 3.14159265358979 * radius_ * radius_;
    }

    double do_perimeter() const {
        return 2 * 3.14159265358979 * radius_;
    }

    std::string name() const { return "圆形"; }
};

/**
 * Rectangle - 矩形，继承自 Shape<Rectangle>
 */
class Rectangle : public Shape<Rectangle> {
    double width_, height_;

public:
    Rectangle(double w, double h) : width_(w), height_(h) {}

    void do_draw() const {
        std::cout << "绘制矩形，宽: " << width_ << ", 高: " << height_ << std::endl;
    }

    double do_area() const {
        return width_ * height_;
    }

    double do_perimeter() const {
        return 2 * (width_ + height_);
    }

    std::string name() const { return "矩形"; }
};

/**
 * Triangle - 三角形，继承自 Shape<Triangle>
 */
class Triangle : public Shape<Triangle> {
    double a_, b_, c_;  // 三条边

public:
    Triangle(double a, double b, double c) : a_(a), b_(b), c_(c) {}

    void do_draw() const {
        std::cout << "绘制三角形，边长: " << a_ << ", " << b_ << ", " << c_ << std::endl;
    }

    double do_area() const {
        // 海伦公式
        double s = (a_ + b_ + c_) / 2;
        return std::sqrt(s * (s - a_) * (s - b_) * (s - c_));
    }

    double do_perimeter() const {
        return a_ + b_ + c_;
    }

    std::string name() const { return "三角形"; }
};

// ============================================================================
// 第二部分：Mixin 类
// ============================================================================

/**
 * Printable<Derived> - 可打印的 Mixin
 *
 * 为派生类添加 print() 功能
 * 派生类需要实现 toString() 方法
 */
template<typename Derived>
class Printable {
public:
    void print() const {
        std::cout << static_cast<const Derived*>(this)->toString() << std::endl;
    }

    void println() const {
        print();
        std::cout << std::endl;
    }
};

/**
 * Comparable<Derived> - 可比较的 Mixin
 *
 * 为派生类添加比较运算符
 * 派生类需要实现 compareTo() 方法
 */
template<typename Derived>
class Comparable {
public:
    bool operator==(const Derived& other) const {
        return static_cast<const Derived*>(this)->compareTo(other) == 0;
    }

    bool operator!=(const Derived& other) const {
        return !(*this == other);
    }

    bool operator<(const Derived& other) const {
        return static_cast<const Derived*>(this)->compareTo(other) < 0;
    }

    bool operator>(const Derived& other) const {
        return other < *static_cast<const Derived*>(this);
    }

    bool operator<=(const Derived& other) const {
        return !(other < *static_cast<const Derived*>(this));
    }

    bool operator>=(const Derived& other) const {
        return !(*this < other);
    }
};

/**
 * Cloneable<Derived> - 可克隆的 Mixin
 *
 * 为派生类添加 clone() 功能
 */
template<typename Derived>
class Cloneable {
public:
    std::unique_ptr<Derived> clone() const {
        return std::make_unique<Derived>(
            *static_cast<const Derived*>(this)
        );
    }
};

/**
 * Counter<Derived> - 计数器 Mixin
 *
 * 统计每个派生类创建了多少个实例
 */
template<typename Derived>
class Counter {
    static inline int count_ = 0;  // C++17 inline 变量

protected:
    // 构造时增加计数
    Counter() { ++count_; }

    // 拷贝构造时增加计数
    Counter(const Counter&) { ++count_; }

    // 移动构造时增加计数
    Counter(Counter&&) noexcept { ++count_; }

    // 析构时减少计数
    ~Counter() { --count_; }

public:
    // 获取当前实例数量
    static int instance_count() {
        return count_;
    }

    // 重置计数器
    static void reset_count() {
        count_ = 0;
    }
};

/**
 * 使用多个 Mixin 组合
 *
 * Person 类同时使用 Printable、Comparable 和 Counter
 */
class Person : public Printable<Person>,
               public Comparable<Person>,
               public Counter<Person> {
    std::string name_;
    int age_;

public:
    Person(const std::string& name, int age)
        : name_(name), age_(age) {}

    // 实现 toString()，供 Printable 调用
    std::string toString() const {
        return "Person{name='" + name_ + "', age=" + std::to_string(age_) + "}";
    }

    // 实现 compareTo()，供 Comparable 调用
    int compareTo(const Person& other) const {
        if (name_ != other.name_) {
            return name_ < other.name_ ? -1 : 1;
        }
        return age_ - other.age_;
    }

    // Getter
    const std::string& name() const { return name_; }
    int age() const { return age_; }
};

// ============================================================================
// 第三部分：运算符重载 Mixin
// ============================================================================

/**
 * Addable<Derived> - 可相加的 Mixin
 *
 * 自动实现 += 和 + 运算符
 */
template<typename Derived>
class Addable {
public:
    Derived& operator+=(const Derived& other) {
        auto& self = static_cast<Derived&>(*this);
        self.add(other);
        return self;
    }

    Derived operator+(const Derived& other) const {
        Derived result = static_cast<const Derived&>(*this);
        result += other;
        return result;
    }
};

/**
 * PrintableNumber - 演示运算符重载 Mixin
 */
class PrintableNumber : public Addable<PrintableNumber>,
                         public Printable<PrintableNumber> {
    int value_;

public:
    explicit PrintableNumber(int v) : value_(v) {}

    // 实现 add()，供 Addable 调用
    void add(const PrintableNumber& other) {
        value_ += other.value_;
    }

    // 实现 toString()，供 Printable 调用
    std::string toString() const {
        return std::to_string(value_);
    }

    int value() const { return value_; }
};

// ============================================================================
// 第四部分：单例模式 (使用 CRTP)
// ============================================================================

/**
 * Singleton<Derived> - 使用 CRTP 实现单例模式
 *
 * 任何继承自 Singleton 的类都自动成为单例
 */
template<typename Derived>
class Singleton {
protected:
    Singleton() = default;
    ~Singleton() = default;

public:
    // 禁止拷贝和移动
    Singleton(const Singleton&) = delete;
    Singleton& operator=(const Singleton&) = delete;
    Singleton(Singleton&&) = delete;
    Singleton& operator=(Singleton&&) = delete;

    // 获取单例实例
    static Derived& instance() {
        static Derived instance;
        return instance;
    }
};

/**
 * Logger - 日志类，使用单例模式
 */
class Logger : public Singleton<Logger> {
    friend class Singleton<Logger>;  // 允许基类访问私有构造函数

    Logger() {
        std::cout << "Logger 初始化" << std::endl;
    }

public:
    void log(const std::string& message) {
        std::cout << "[LOG] " << message << std::endl;
    }
};

/**
 * Config - 配置管理类，使用单例模式
 */
class Config : public Singleton<Config> {
    friend class Singleton<Config>;

    Config() {
        std::cout << "Config 初始化" << std::endl;
    }

    std::map<std::string, std::string> settings_;

public:
    void set(const std::string& key, const std::string& value) {
        settings_[key] = value;
    }

    std::string get(const std::string& key) const {
        auto it = settings_.find(key);
        return it != settings_.end() ? it->second : "";
    }
};

// ============================================================================
// 第五部分：链式调用 (Method Chaining)
// ============================================================================

/**
 * Fluent<Derived> - 支持链式调用的 Mixin
 *
 * 每个方法返回 Derived&，允许连续调用
 */
template<typename Derived>
class Fluent {
public:
    Derived& self() {
        return static_cast<Derived&>(*this);
    }
};

/**
 * QueryBuilder - 查询构建器，演示链式调用
 */
class QueryBuilder : public Fluent<QueryBuilder> {
    std::string table_;
    std::string where_clause_;
    std::string order_clause_;
    int limit_ = -1;

public:
    QueryBuilder& from(const std::string& table) {
        table_ = table;
        return self();
    }

    QueryBuilder& where(const std::string& condition) {
        where_clause_ = condition;
        return self();
    }

    QueryBuilder& order_by(const std::string& field) {
        order_clause_ = field;
        return self();
    }

    QueryBuilder& limit(int n) {
        limit_ = n;
        return self();
    }

    std::string build() const {
        std::string sql = "SELECT * FROM " + table_;
        if (!where_clause_.empty()) {
            sql += " WHERE " + where_clause_;
        }
        if (!order_clause_.empty()) {
            sql += " ORDER BY " + order_clause_;
        }
        if (limit_ > 0) {
            sql += " LIMIT " + std::to_string(limit_);
        }
        return sql;
    }
};

// ============================================================================
// 第六部分：性能对比测试
// ============================================================================

/**
 * 虚函数版本的形状
 */
class VirtualShape {
public:
    virtual ~VirtualShape() = default;
    virtual double area() const = 0;
};

class VirtualCircle : public VirtualShape {
    double radius_;
public:
    explicit VirtualCircle(double r) : radius_(r) {}
    double area() const override {
        return 3.14159265358979 * radius_ * radius_;
    }
};

/**
 * benchmark - 性能测试函数
 *
 * 比较虚函数和 CRTP 的性能差异
 */
template<typename Func>
double benchmark(const std::string& name, Func func, int iterations = 10000000) {
    auto start = std::chrono::high_resolution_clock::now();
    func(iterations);
    auto end = std::chrono::high_resolution_clock::now();

    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    double ms = duration.count() / 1000.0;

    std::cout << name << ": " << ms << " ms" << std::endl;
    return ms;
}

// ============================================================================
// 主函数：演示各种 CRTP 技术
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "CRTP (奇异递归模板模式) 技术演示" << std::endl;
    std::cout << "========================================" << std::endl;

    // ---- 第一部分：静态多态 ----
    std::cout << "\n--- 1. 静态多态 ---" << std::endl;

    Circle circle(5.0);
    Rectangle rect(4.0, 6.0);
    Triangle tri(3.0, 4.0, 5.0);

    circle.draw();
    rect.draw();
    tri.draw();

    circle.print();
    rect.print();
    tri.print();

    // 使用模板函数处理不同形状
    auto print_shape_info = [](const auto& shape) {
        shape.print();
    };

    print_shape_info(circle);
    print_shape_info(rect);
    print_shape_info(tri);

    // ---- 第二部分：Mixin 类 ----
    std::cout << "\n--- 2. Mixin 类 ---" << std::endl;

    Person alice("Alice", 30);
    Person bob("Bob", 25);
    Person alice2("Alice", 30);

    alice.print();
    bob.print();

    std::cout << "alice == alice2: " << (alice == alice2) << std::endl;
    std::cout << "alice == bob: " << (alice == bob) << std::endl;
    std::cout << "alice < bob: " << (alice < bob) << std::endl;

    // ---- 第三部分：计数器 ----
    std::cout << "\n--- 3. 计数器 ---" << std::endl;

    Person::reset_count();

    {
        Person p1("Charlie", 20);
        Person p2("Dave", 25);
        std::cout << "当前 Person 实例数: " << Person::instance_count() << std::endl;

        {
            Person p3("Eve", 30);
            std::cout << "当前 Person 实例数: " << Person::instance_count() << std::endl;
        }

        std::cout << "当前 Person 实例数: " << Person::instance_count() << std::endl;
    }

    std::cout << "当前 Person 实例数: " << Person::instance_count() << std::endl;

    // ---- 第四部分：运算符重载 ----
    std::cout << "\n--- 4. 运算符重载 ---" << std::endl;

    PrintableNumber a(10);
    PrintableNumber b(20);
    PrintableNumber c = a + b;

    std::cout << "a = "; a.print();
    std::cout << "b = "; b.print();
    std::cout << "c = a + b = "; c.print();

    a += b;
    std::cout << "a += b 后, a = "; a.print();

    // ---- 第五部分：单例模式 ----
    std::cout << "\n--- 5. 单例模式 ---" << std::endl;

    Logger::instance().log("第一条消息");
    Logger::instance().log("第二条消息");

    Config::instance().set("host", "localhost");
    Config::instance().set("port", "8080");
    std::cout << "host: " << Config::instance().get("host") << std::endl;
    std::cout << "port: " << Config::instance().get("port") << std::endl;

    // ---- 第六部分：链式调用 ----
    std::cout << "\n--- 6. 链式调用 ---" << std::endl;

    std::string query = QueryBuilder()
        .from("users")
        .where("age > 18")
        .order_by("name")
        .limit(10)
        .build();

    std::cout << "生成的查询: " << query << std::endl;

    // ---- 第七部分：性能对比 ----
    std::cout << "\n--- 7. 性能对比 ---" << std::endl;

    const int iterations = 10000000;

    // CRTP 版本
    double crtp_time = benchmark("CRTP (静态多态)", [&](int n) {
        Circle crtp_circle(5.0);
        volatile double sum = 0;
        for (int i = 0; i < n; ++i) {
            sum += crtp_circle.area();
        }
    }, iterations);

    // 虚函数版本
    double virtual_time = benchmark("虚函数 (动态多态)", [&](int n) {
        VirtualCircle virtual_circle(5.0);
        VirtualShape* shape = &virtual_circle;
        volatile double sum = 0;
        for (int i = 0; i < n; ++i) {
            sum += shape->area();
        }
    }, iterations);

    std::cout << "\n性能比: 虚函数/CRTP = "
              << (virtual_time / crtp_time) << "x" << std::endl;
    std::cout << "CRTP 比虚函数快约 "
              << ((virtual_time - crtp_time) / virtual_time * 100)
              << "%" << std::endl;

    // ---- 总结 ----
    std::cout << "\n========================================" << std::endl;
    std::cout << "CRTP 的使用场景总结：" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "1. 静态多态：需要高性能的多态调用" << std::endl;
    std::cout << "2. Mixin 类：为类添加通用功能" << std::endl;
    std::cout << "3. 计数器：统计类的实例数量" << std::endl;
    std::cout << "4. 运算符重载：自动实现相关运算符" << std::endl;
    std::cout << "5. 单例模式：确保类只有一个实例" << std::endl;
    std::cout << "6. 链式调用：支持流畅的 API 设计" << std::endl;

    return 0;
}
