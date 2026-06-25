/**
 * @file bad_class_design.cpp
 * @brief 糟糕类设计规范示例
 *
 * 本文件展示不符合 C++ 类设计规范的糟糕代码示例。
 * 这些代码展示了常见的类设计错误和反模式。
 *
 * 注意：这些代码仅用于教学目的，实际项目中应避免使用。
 */

#include <iostream>
#include <string>
#include <vector>
#include <cstring>

// ============================================================================
// 糟糕的类设计 - 成员顺序和访问控制
// ============================================================================

/**
 * @brief 糟糕的用户类设计
 *
 * 展示糟糕的类设计，包括：
 * - 成员顺序混乱
 * - 访问控制不清晰
 * - 缺少构造函数系列
 * - 返回非 const 引用
 */
class BadUser {
    // 糟糕：没有访问控制说明符
    int id;
    std::string name;
    std::string email;

public:
    // 糟糕：构造函数参数命名不清晰
    BadUser(int i, std::string n, std::string e)
        : id(i), name(n), email(e) {}

    // 糟糕：返回非 const 引用（允许外部修改内部状态）
    std::string& getName() { return name; }
    std::string& getEmail() { return email; }

    // 糟糕：没有 const 修饰
    int getId() { return id; }

    // 糟糕：没有拷贝/移动构造函数和赋值运算符
    // 编译器会生成默认的，但可能不符合预期

    // 糟糕：没有析构函数
    // 如果类管理资源，需要自定义析构函数

    // 糟糕：函数实现放在类定义中（非简单函数）
    void print() {
        std::cout << "User: " << name << " (" << email << ")" << std::endl;
    }

    // 糟糕：使用 C 风格字符串
    char* getRawName() {
        return strdup(name.c_str());
    }
};

// ============================================================================
// 糟糕的类设计 - 资源管理
// ============================================================================

/**
 * @brief 糟糕的资源管理类设计
 *
 * 展示糟糕的资源管理，包括：
 * - 裸指针管理
 * - 缺少 RAII
 * - 缺少拷贝/移动语义
 */
class BadResource {
public:
    // 糟糕：使用裸指针
    BadResource() : data_(new int[100]), size_(100) {}

    // 糟糕：没有拷贝构造函数（浅拷贝）
    // BadResource(const BadResource& other) = default;

    // 糟糕：没有移动构造函数
    // BadResource(BadResource&& other) = default;

    // 糟糕：析构函数可能双重释放
    ~BadResource() {
        delete[] data_;
    }

    // 糟糕：没有赋值运算符
    // BadResource& operator=(const BadResource& other) = default;

    void setValue(int index, int value) {
        if (index >= 0 && index < size_) {
            data_[index] = value;
        }
    }

    int getValue(int index) const {
        if (index >= 0 && index < size_) {
            return data_[index];
        }
        return 0;
    }

private:
    int* data_;    // 糟糕：裸指针
    int size_;     // 糟顿：使用 int 而不是 size_t
};

// ============================================================================
// 糟糕的类设计 - 运算符重载
// ============================================================================

/**
 * @brief 糟糕的运算符重载示例
 *
 * 展示糟糕的运算符重载，包括：
 * - 不一致的运算符
 * - 返回类型不正确
 * - 缺少 const 修饰
 */
class BadVector {
public:
    BadVector() : x_(0), y_(0) {}
    BadVector(double x, double y) : x_(x), y_(y) {}

    // 糟糕：没有 const 修饰
    double getX() { return x_; }
    double getY() { return y_; }

    // 糟糕：返回非 const 引用
    double& getXRef() { return x_; }
    double& getYRef() { return y_; }

    // 糟糕：运算符返回非 const 引用
    BadVector& operator+(const BadVector& other) {
        x_ += other.x_;
        y_ += other.y_;
        return *this;
    }

    // 糟糕：运算符改变了左侧操作数
    BadVector& operator-(const BadVector& other) {
        x_ -= other.x_;
        y_ -= other.y_;
        return *this;
    }

    // 糟糕：没有比较运算符
    // bool operator==(const BadVector& other) const;

    // 糟糕：没有输出运算符
    // friend std::ostream& operator<<(std::ostream& os, const BadVector& v);

private:
    double x_;
    double y_;
};

// ============================================================================
// 糟糕的类设计 - 友元滥用
// ============================================================================

/**
 * @brief 糟糕的友元使用示例
 *
 * 展示糟糕的友元使用，包括：
 * - 友元滥用
 * - 破坏封装
 */
class BadSecret {
public:
    BadSecret(int secret) : secret_(secret) {}

    // 糟糕：过多的友元
    friend class BadFriend1;
    friend class BadFriend2;
    friend class BadFriend3;
    friend void badFunction1(const BadSecret& s);
    friend void badFunction2(const BadSecret& s);
    friend void badFunction3(const BadSecret& s);

private:
    int secret_;
};

class BadFriend1 {
public:
    void access(const BadSecret& s) {
        std::cout << "Secret: " << s.secret_ << std::endl;
    }
};

class BadFriend2 {
public:
    void access(const BadSecret& s) {
        std::cout << "Secret: " << s.secret_ << std::endl;
    }
};

class BadFriend3 {
public:
    void access(const BadSecret& s) {
        std::cout << "Secret: " << s.secret_ << std::endl;
    }
};

void badFunction1(const BadSecret& s) {
    std::cout << "Secret: " << s.secret_ << std::endl;
}

void badFunction2(const BadSecret& s) {
    std::cout << "Secret: " << s.secret_ << std::endl;
}

void badFunction3(const BadSecret& s) {
    std::cout << "Secret: " << s.secret_ << std::endl;
}

// ============================================================================
// 糟糕的类设计 - 基类设计
// ============================================================================

/**
 * @brief 糟糕的基类设计示例
 *
 * 展示糟糕的基类设计，包括：
 * - 没有虚析构函数
 * - 没有使用 override
 * - 缺少纯虚函数
 */
class BadBase {
public:
    // 糟糕：没有虚析构函数
    ~BadBase() {}

    // 糟糕：没有纯虚函数
    void process() {
        std::cout << "Base processing" << std::endl;
    }

    // 糟糕：没有使用 override
    virtual void doSomething() {
        std::cout << "Base doing something" << std::endl;
    }
};

class BadDerived : public BadBase {
public:
    // 糟糕：没有使用 override
    void doSomething() {
        std::cout << "Derived doing something" << std::endl;
    }

    // 糟糕：隐藏基类函数
    void process(int x) {
        std::cout << "Derived processing: " << x << std::endl;
    }
};

// ============================================================================
// 演示函数
// ============================================================================

/**
 * @brief 演示糟糕类设计
 *
 * 注意：这些代码仅用于教学目的，实际项目中应避免使用。
 */
void demonstrateBadClassDesign() {
    std::cout << "=== 糟糕类设计规范示例 ===" << std::endl;
    std::cout << "注意：这些代码仅用于教学目的，实际项目中应避免使用。" << std::endl;

    // 糟糕的用户类
    std::cout << "\n1. 糟糕的用户类:" << std::endl;
    BadUser user(1, "Alice", "alice@example.com");
    user.print();

    // 糟糕的资源管理
    std::cout << "\n2. 糟糕的资源管理:" << std::endl;
    BadResource resource;
    resource.setValue(0, 42);
    std::cout << "   Value: " << resource.getValue(0) << std::endl;

    // 糟糕的运算符重载
    std::cout << "\n3. 糟糕的运算符重载:" << std::endl;
    BadVector v1(1.0, 2.0);
    BadVector v2(3.0, 4.0);
    v1 + v2;  // 糟糕：改变了 v1
    std::cout << "   v1: (" << v1.getX() << ", " << v1.getY() << ")" << std::endl;

    // 糟糕的友元使用
    std::cout << "\n4. 糟糕的友元使用:" << std::endl;
    BadSecret secret(42);
    BadFriend1 friend1;
    friend1.access(secret);

    // 糟糕的基类设计
    std::cout << "\n5. 糟糕的基类设计:" << std::endl;
    BadDerived derived;
    derived.doSomething();
    derived.process(42);
}
