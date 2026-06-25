/**
 * @file deducing_this.cpp
 * @brief C++23 推断 this (Deducing this) 示例
 *
 * C++23 引入了显式对象参数（推断 this），允许在成员函数中显式捕获 this。
 * 这使得成员函数可以区分左值和右值对象。
 *
 * 主要特点：
 * - 显式捕获 this 指针
 * - 区分左值和右值对象
 * - 支持完美转发
 * - 简化 CRTP 模式
 *
 * 编译命令：
 * g++ -std=c++23 -o deducing_this deducing_this.cpp
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>

// ========== 1. 基本用法 ==========

class Widget {
private:
    std::string name_;

public:
    Widget(std::string name) : name_(std::move(name)) {}

    // 使用推断 this 的成员函数
    auto get_name(this Widget& self) {
        return self.name_;
    }

    // const 版本
    auto get_name(this const Widget& self) {
        return self.name_;
    }

    // 右值版本
    auto get_name(this Widget&& self) {
        return std::move(self.name_);
    }
};

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    Widget w("Hello");
    const Widget cw("World");

    std::cout << "w.get_name() = " << w.get_name() << std::endl;
    std::cout << "cw.get_name() = " << cw.get_name() << std::endl;
    std::cout << "Widget(\"Move\").get_name() = " << Widget("Move").get_name() << std::endl;
}

// ========== 2. 实际应用：链式调用 ==========

class Builder {
private:
    std::string name_;
    int age_;
    std::string email_;

public:
    Builder() = default;

    // 使用推断 this 实现链式调用
    Builder& set_name(this Builder& self, std::string name) {
        self.name_ = std::move(name);
        return self;
    }

    Builder& set_age(this Builder& self, int age) {
        self.age_ = age;
        return self;
    }

    Builder& set_email(this Builder& self, std::string email) {
        self.email_ = std::move(email);
        return self;
    }

    void print(this const Builder& self) {
        std::cout << "Builder{name='" << self.name_
                  << "', age=" << self.age_
                  << "', email='" << self.email_ << "'}" << std::endl;
    }
};

void builder_pattern() {
    std::cout << "\n=== 实际应用：链式调用 ===" << std::endl;

    Builder()
        .set_name("Alice")
        .set_age(25)
        .set_email("alice@example.com")
        .print();
}

// ========== 3. 实际应用：CRTP 简化 ==========

// 传统 CRTP
template<typename Derived>
class CounterTraditional {
protected:
    static int count_;

public:
    void increment() {
        ++count_;
    }

    int get_count() const {
        return count_;
    }
};

template<typename Derived>
int CounterTraditional<Derived>::count_ = 0;

class MyCounterTraditional : public CounterTraditional<MyCounterTraditional> {};

// 使用推断 this 的简化版本
class CounterModern {
private:
    static int count_;

public:
    // 使用推断 this，无需 CRTP
    void increment(this CounterModern& self) {
        ++count_;
    }

    int get_count(this const CounterModern& self) {
        return count_;
    }
};

int CounterModern::count_ = 0;

void crtp_simplification() {
    std::cout << "\n=== 实际应用：CRTP 简化 ===" << std::endl;

    // 传统 CRTP
    MyCounterTraditional counter1;
    counter1.increment();
    counter1.increment();
    std::cout << "Traditional CRTP count: " << counter1.get_count() << std::endl;

    // 现代方式
    CounterModern counter2;
    counter2.increment();
    counter2.increment();
    counter2.increment();
    std::cout << "Modern count: " << counter2.get_count() << std::endl;
}

// ========== 4. 实际应用：智能指针 ==========

template<typename T>
class SmartPtr {
private:
    T* ptr_;

public:
    explicit SmartPtr(T* ptr = nullptr) : ptr_(ptr) {}

    ~SmartPtr() { delete ptr_; }

    // 使用推断 this 的解引用运算符
    T& operator*(this SmartPtr& self) {
        return *self.ptr_;
    }

    const T& operator*(this const SmartPtr& self) {
        return *self.ptr_;
    }

    // 使用推断 this 的箭头运算符
    T* operator->(this SmartPtr& self) {
        return self.ptr_;
    }

    const T* operator->(this const SmartPtr& self) {
        return self.ptr_;
    }
};

void smart_pointer() {
    std::cout << "\n=== 实际应用：智能指针 ===" << std::endl;

    SmartPtr<int> ptr(new int(42));
    std::cout << "*ptr = " << *ptr << std::endl;

    const SmartPtr<int> cptr(new int(100));
    std::cout << "*cptr = " << *cptr << std::endl;
}

// ========== 5. 实际应用：容器适配器 ==========

template<typename Container>
class ContainerAdapter {
private:
    Container container_;

public:
    // 使用推断 this 的大小查询
    size_t size(this const ContainerAdapter& self) {
        return self.container_.size();
    }

    // 使用推断 this 的元素访问
    auto& at(this ContainerAdapter& self, size_t index) {
        return self.container_.at(index);
    }

    const auto& at(this const ContainerAdapter& self, size_t index) {
        return self.container_.at(index);
    }

    // 使用推断 this 的添加元素
    void push_back(this ContainerAdapter& self, const typename Container::value_type& value) {
        self.container_.push_back(value);
    }

    // 使用推断 this 的打印
    void print(this const ContainerAdapter& self) {
        std::cout << "[";
        bool first = true;
        for (const auto& item : self.container_) {
            if (!first) std::cout << ", ";
            std::cout << item;
            first = false;
        }
        std::cout << "]" << std::endl;
    }
};

void container_adapter() {
    std::cout << "\n=== 实际应用：容器适配器 ===" << std::endl;

    ContainerAdapter<std::vector<int>> adapter;
    adapter.push_back(1);
    adapter.push_back(2);
    adapter.push_back(3);

    std::cout << "Size: " << adapter.size() << std::endl;
    std::cout << "Element at 1: " << adapter.at(1) << std::endl;

    std::cout << "Contents: ";
    adapter.print();
}

// ========== 6. 实际应用：表达式模板 ==========

struct Vec {
    std::vector<double> data;

    Vec(std::initializer_list<double> init) : data(init) {}

    // 使用推断 this 的加法运算符
    Vec operator+(this const Vec& self, const Vec& other) {
        Vec result = self;
        for (size_t i = 0; i < result.data.size(); ++i) {
            result.data[i] += other.data[i];
        }
        return result;
    }

    // 使用推断 this 的打印
    void print(this const Vec& self) {
        std::cout << "[";
        bool first = true;
        for (double v : self.data) {
            if (!first) std::cout << ", ";
            std::cout << v;
            first = false;
        }
        std::cout << "]" << std::endl;
    }
};

void expression_templates() {
    std::cout << "\n=== 实际应用：表达式模板 ===" << std::endl;

    Vec a = {1.0, 2.0, 3.0};
    Vec b = {4.0, 5.0, 6.0};

    Vec c = a + b;

    std::cout << "a = ";
    a.print();
    std::cout << "b = ";
    b.print();
    std::cout << "a + b = ";
    c.print();
}

// ========== 7. 实际应用：访问者模式 ==========

struct ElementA {
    std::string data = "ElementA";
};

struct ElementB {
    int value = 42;
};

struct Visitor {
    void visit(this Visitor& self, ElementA& elem) {
        std::cout << "Visiting ElementA: " << elem.data << std::endl;
    }

    void visit(this Visitor& self, ElementB& elem) {
        std::cout << "Visiting ElementB: " << elem.value << std::endl;
    }
};

void visitor_pattern() {
    std::cout << "\n=== 实际应用：访问者模式 ===" << std::endl;

    Visitor visitor;
    ElementA a;
    ElementB b;

    visitor.visit(a);
    visitor.visit(b);
}

// ========== 8. 实际应用：缓存代理 ==========

template<typename T>
class CachedValue {
private:
    T value_;
    mutable bool cached_ = false;
    mutable T cache_;

public:
    CachedValue(T value) : value_(std::move(value)) {}

    // 使用推断 this 的获取值（带缓存）
    const T& get(this const CachedValue& self) {
        if (!self.cached_) {
            self.cache_ = self.value_;  // 模拟计算
            self.cached_ = true;
        }
        return self.cache_;
    }

    // 使用推断 this 的更新值
    void update(this CachedValue& self, T new_value) {
        self.value_ = std::move(new_value);
        self.cached_ = false;
    }
};

void caching_proxy() {
    std::cout << "\n=== 实际应用：缓存代理 ===" << std::endl;

    CachedValue<int> cv(42);
    std::cout << "First get: " << cv.get() << std::endl;
    std::cout << "Second get (cached): " << cv.get() << std::endl;

    cv.update(100);
    std::cout << "After update: " << cv.get() << std::endl;
}

// ========== 9. 实际应用：序列化 ==========

class Serializable {
private:
    int id_;
    std::string name_;

public:
    Serializable(int id, std::string name) : id_(id), name_(std::move(name)) {}

    // 使用推断 this 的序列化
    std::string serialize(this const Serializable& self) {
        return "{\"id\":" + std::to_string(self.id_) +
               ",\"name\":\"" + self.name_ + "\"}";
    }

    // 使用推断 this 的反序列化
    static Serializable deserialize(const std::string& json) {
        // 简化的 JSON 解析
        return Serializable(1, "Parsed");
    }
};

void serialization() {
    std::cout << "\n=== 实际应用：序列化 ===" << std::endl;

    Serializable obj(42, "Test");
    std::cout << "Serialized: " << obj.serialize() << std::endl;
}

// ========== 10. 实际应用：观察者模式 ==========

class Subject {
private:
    std::vector<std::function<void(int)>> observers_;
    int state_ = 0;

public:
    // 使用推断 this 的注册观察者
    void register_observer(this Subject& self, std::function<void(int)> observer) {
        self.observers_.push_back(std::move(observer));
    }

    // 使用推断 this 的设置状态
    void set_state(this Subject& self, int state) {
        self.state_ = state;
        self.notify();
    }

    // 使用推断 this 的通知
    void notify(this const Subject& self) {
        for (const auto& observer : self.observers_) {
            observer(self.state_);
        }
    }
};

void observer_pattern() {
    std::cout << "\n=== 实际应用：观察者模式 ===" << std::endl;

    Subject subject;

    subject.register_observer([](int state) {
        std::cout << "Observer 1: State changed to " << state << std::endl;
    });

    subject.register_observer([](int state) {
        std::cout << "Observer 2: State changed to " << state << std::endl;
    });

    subject.set_state(1);
    subject.set_state(2);
}

int main() {
    std::cout << "C++23 推断 this (Deducing this) 示例\n" << std::endl;

    basic_usage();
    builder_pattern();
    crtp_simplification();
    smart_pointer();
    container_adapter();
    expression_templates();
    visitor_pattern();
    caching_proxy();
    serialization();
    observer_pattern();

    return 0;
}
