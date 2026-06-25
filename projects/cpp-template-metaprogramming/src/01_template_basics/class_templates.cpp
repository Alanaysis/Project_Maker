// =============================================================================
// class_templates.cpp - 类模板基础
// =============================================================================
// 编译: g++ -std=c++17 -o class_templates class_templates.cpp
// 运行: ./class_templates
// =============================================================================

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <stdexcept>

// ---------------------------------------------------------------------------
// 1. 基本类模板
// ---------------------------------------------------------------------------

// 简单的包装器类模板
template <typename T>
class Wrapper {
public:
    explicit Wrapper(T value) : value_(std::move(value)) {}

    const T& get() const { return value_; }
    void set(const T& value) { value_ = value; }
    void set(T&& value) { value_ = std::move(value); }

    // 比较操作符
    bool operator==(const Wrapper& other) const { return value_ == other.value_; }
    bool operator!=(const Wrapper& other) const { return !(*this == other); }
    bool operator<(const Wrapper& other) const { return value_ < other.value_; }

    // 输出操作符
    friend std::ostream& operator<<(std::ostream& os, const Wrapper& w) {
        return os << "Wrapper(" << w.value_ << ")";
    }

private:
    T value_;
};

// ---------------------------------------------------------------------------
// 2. 多模板参数的类模板
// ---------------------------------------------------------------------------

// 键值对
template <typename Key, typename Value>
class KeyValuePair {
public:
    KeyValuePair(Key key, Value value)
        : key_(std::move(key)), value_(std::move(value)) {}

    const Key& key() const { return key_; }
    const Value& value() const { return value_; }

    void set_value(const Value& value) { value_ = value; }

    friend std::ostream& operator<<(std::ostream& os, const KeyValuePair& kvp) {
        return os << "{" << kvp.key_ << ": " << kvp.value_ << "}";
    }

private:
    Key key_;
    Value value_;
};

// ---------------------------------------------------------------------------
// 3. 带默认模板参数
// ---------------------------------------------------------------------------

// 动态数组，带自定义分配器参数（默认使用 std::allocator）
template <typename T, typename Allocator = std::allocator<T>>
class SimpleVector {
public:
    SimpleVector() : data_(nullptr), size_(0), capacity_(0) {}

    ~SimpleVector() {
        for (std::size_t i = 0; i < size_; ++i) {
            data_[i].~T();
        }
        alloc_.deallocate(data_, capacity_);
    }

    void push_back(const T& value) {
        if (size_ >= capacity_) {
            reserve(capacity_ == 0 ? 1 : capacity_ * 2);
        }
        new (&data_[size_]) T(value);
        ++size_;
    }

    void push_back(T&& value) {
        if (size_ >= capacity_) {
            reserve(capacity_ == 0 ? 1 : capacity_ * 2);
        }
        new (&data_[size_]) T(std::move(value));
        ++size_;
    }

    T& operator[](std::size_t index) { return data_[index]; }
    const T& operator[](std::size_t index) const { return data_[index]; }

    std::size_t size() const { return size_; }
    std::size_t capacity() const { return capacity_; }
    bool empty() const { return size_ == 0; }

    T& front() { return data_[0]; }
    T& back() { return data_[size_ - 1]; }

private:
    void reserve(std::size_t new_capacity) {
        T* new_data = alloc_.allocate(new_capacity);
        for (std::size_t i = 0; i < size_; ++i) {
            new (&new_data[i]) T(std::move(data_[i]));
            data_[i].~T();
        }
        alloc_.deallocate(data_, capacity_);
        data_ = new_data;
        capacity_ = new_capacity;
    }

    T* data_;
    std::size_t size_;
    std::size_t capacity_;
    Allocator alloc_;
};

// ---------------------------------------------------------------------------
// 4. 嵌套类模板
// ---------------------------------------------------------------------------

// 带迭代器的容器
template <typename T>
class SimpleList {
private:
    struct Node {
        T data;
        std::unique_ptr<Node> next;

        Node(const T& d) : data(d), next(nullptr) {}
        Node(T&& d) : data(std::move(d)), next(nullptr) {}
    };

public:
    // 嵌套迭代器类
    class Iterator {
    public:
        using iterator_category = std::forward_iterator_tag;
        using value_type = T;
        using difference_type = std::ptrdiff_t;
        using pointer = T*;
        using reference = T&;

        explicit Iterator(Node* node) : node_(node) {}

        T& operator*() { return node_->data; }
        T* operator->() { return &(node_->data); }

        Iterator& operator++() {
            node_ = node_->next.get();
            return *this;
        }

        Iterator operator++(int) {
            Iterator tmp = *this;
            ++(*this);
            return tmp;
        }

        bool operator==(const Iterator& other) const { return node_ == other.node_; }
        bool operator!=(const Iterator& other) const { return !(*this == other); }

    private:
        Node* node_;
    };

    SimpleList() : head_(nullptr), size_(0) {}

    void push_front(const T& value) {
        auto node = std::make_unique<Node>(value);
        node->next = std::move(head_);
        head_ = std::move(node);
        ++size_;
    }

    void push_front(T&& value) {
        auto node = std::make_unique<Node>(std::move(value));
        node->next = std::move(head_);
        head_ = std::move(node);
        ++size_;
    }

    Iterator begin() { return Iterator(head_.get()); }
    Iterator end() { return Iterator(nullptr); }

    std::size_t size() const { return size_; }
    bool empty() const { return size_ == 0; }

private:
    std::unique_ptr<Node> head_;
    std::size_t size_;
};

// ---------------------------------------------------------------------------
// 5. 类模板的成员函数模板
// ---------------------------------------------------------------------------

// 可以接受不同类型参数的容器
template <typename T>
class FlexibleContainer {
public:
    // 成员函数模板：接受任何可转换为 T 的类型
    template <typename U>
    void add(U&& value) {
        data_.push_back(T(std::forward<U>(value)));
    }

    // 成员函数模板：批量添加
    template <typename... Args>
    void add_many(Args&&... args) {
        (data_.push_back(T(std::forward<Args>(args))), ...);
    }

    // 成员函数模板：条件添加
    template <typename U, typename Pred>
    void add_if(U&& value, Pred pred) {
        if (pred(value)) {
            data_.push_back(T(std::forward<U>(value)));
        }
    }

    const std::vector<T>& data() const { return data_; }
    std::size_t size() const { return data_.size(); }

private:
    std::vector<T> data_;
};

// ---------------------------------------------------------------------------
// 6. 静态成员和类模板
// ---------------------------------------------------------------------------

// 带静态计数器的类模板
template <typename T>
class Counter {
public:
    Counter() { ++count_; }
    Counter(const Counter&) { ++count_; }
    ~Counter() { --count_; }

    static std::size_t count() { return count_; }

private:
    static std::size_t count_;
};

// 静态成员初始化
template <typename T>
std::size_t Counter<T>::count_ = 0;

// ---------------------------------------------------------------------------
// 7. CRTP (Curiously Recurring Template Pattern)
// ---------------------------------------------------------------------------

// 基类模板，派生类将自己作为模板参数传入
template <typename Derived>
class Printable {
public:
    void print() const {
        // 调用派生类的实现
        static_cast<const Derived*>(this)->do_print();
    }

    std::string to_string() const {
        return static_cast<const Derived*>(this)->do_to_string();
    }
};

// 使用 CRTP 的派生类
class Point : public Printable<Point> {
public:
    Point(double x, double y) : x_(x), y_(y) {}

    void do_print() const {
        std::cout << "Point(" << x_ << ", " << y_ << ")" << std::endl;
    }

    std::string do_to_string() const {
        return "Point(" + std::to_string(x_) + ", " + std::to_string(y_) + ")";
    }

private:
    double x_, y_;
};

class Circle : public Printable<Circle> {
public:
    Circle(double x, double y, double r) : x_(x), y_(y), r_(r) {}

    void do_print() const {
        std::cout << "Circle(" << x_ << ", " << y_ << ", r=" << r_ << ")" << std::endl;
    }

    std::string do_to_string() const {
        return "Circle(" + std::to_string(x_) + ", " + std::to_string(y_) +
               ", r=" + std::to_string(r_) + ")";
    }

private:
    double x_, y_, r_;
};

// ---------------------------------------------------------------------------
// 8. 类模板参数推导 (C++17 CTAD)
// ---------------------------------------------------------------------------

// 用于演示 CTAD 的包装器
template <typename T>
class ValueHolder {
public:
    ValueHolder(T value) : value_(std::move(value)) {}

    const T& get() const { return value_; }

private:
    T value_;
};

// C++17 推导指引（通常自动生成，这里显式展示）
template <typename T>
ValueHolder(T) -> ValueHolder<T>;

// 双参数包装器
template <typename T, typename U>
class Pair {
public:
    Pair(T first, U second) : first_(std::move(first)), second_(std::move(second)) {}

    const T& first() const { return first_; }
    const U& second() const { return second_; }

private:
    T first_;
    U second_;
};

// ---------------------------------------------------------------------------
// 9. 异常安全的类模板
// ---------------------------------------------------------------------------

template <typename T>
class ScopedGuard {
public:
    explicit ScopedGuard(T resource)
        : resource_(std::move(resource)), active_(true) {}

    ~ScopedGuard() {
        if (active_) {
            resource_.release();
        }
    }

    // 禁止拷贝
    ScopedGuard(const ScopedGuard&) = delete;
    ScopedGuard& operator=(const ScopedGuard&) = delete;

    // 允许移动
    ScopedGuard(ScopedGuard&& other) noexcept
        : resource_(std::move(other.resource_)), active_(other.active_) {
        other.active_ = false;
    }

    void dismiss() { active_ = false; }

private:
    T resource_;
    bool active_;
};

// ---------------------------------------------------------------------------
// 主函数
// ---------------------------------------------------------------------------

int main() {
    std::cout << "=== C++ 类模板基础 ===" << std::endl;
    std::cout << std::endl;

    // 1. 基本类模板
    std::cout << "1. 基本类模板:" << std::endl;
    Wrapper<int> w1(42);
    Wrapper<std::string> w2("hello");
    std::cout << w1 << std::endl;
    std::cout << w2 << std::endl;
    std::cout << std::endl;

    // 2. 多模板参数
    std::cout << "2. 多模板参数:" << std::endl;
    KeyValuePair<std::string, int> kvp("age", 25);
    std::cout << kvp << std::endl;
    KeyValuePair<int, double> kvp2(1, 3.14);
    std::cout << kvp2 << std::endl;
    std::cout << std::endl;

    // 3. 带默认模板参数
    std::cout << "3. 带默认模板参数:" << std::endl;
    SimpleVector<int> sv;
    sv.push_back(1);
    sv.push_back(2);
    sv.push_back(3);
    std::cout << "SimpleVector: ";
    for (std::size_t i = 0; i < sv.size(); ++i) {
        std::cout << sv[i] << " ";
    }
    std::cout << std::endl;
    std::cout << std::endl;

    // 4. 嵌套类模板
    std::cout << "4. 嵌套类模板:" << std::endl;
    SimpleList<int> list;
    list.push_front(3);
    list.push_front(2);
    list.push_front(1);
    std::cout << "List: ";
    for (auto it = list.begin(); it != list.end(); ++it) {
        std::cout << *it << " ";
    }
    std::cout << std::endl;
    std::cout << std::endl;

    // 5. 成员函数模板
    std::cout << "5. 成员函数模板:" << std::endl;
    FlexibleContainer<std::string> fc;
    fc.add("hello");
    fc.add(std::string("world"));
    fc.add_many("foo", "bar", "baz");
    std::cout << "FlexibleContainer: ";
    for (const auto& s : fc.data()) {
        std::cout << s << " ";
    }
    std::cout << std::endl;
    std::cout << std::endl;

    // 6. 静态成员
    std::cout << "6. 静态成员:" << std::endl;
    {
        Counter<int> c1, c2, c3;
        std::cout << "Counter<int> count: " << Counter<int>::count() << std::endl;
        Counter<double> d1, d2;
        std::cout << "Counter<double> count: " << Counter<double>::count() << std::endl;
    }
    std::cout << "Counter<int> count after scope: " << Counter<int>::count() << std::endl;
    std::cout << std::endl;

    // 7. CRTP
    std::cout << "7. CRTP (Curiously Recurring Template Pattern):" << std::endl;
    Point p(1.0, 2.0);
    Circle c(3.0, 4.0, 5.0);
    p.print();
    c.print();
    std::cout << "p.to_string(): " << p.to_string() << std::endl;
    std::cout << "c.to_string(): " << c.to_string() << std::endl;
    std::cout << std::endl;

    // 8. CTAD (C++17)
    std::cout << "8. 类模板参数推导 (CTAD):" << std::endl;
    ValueHolder vh(42);  // 自动推导为 ValueHolder<int>
    ValueHolder vh2(3.14);  // 自动推导为 ValueHolder<double>
    std::cout << "vh.get() = " << vh.get() << std::endl;
    std::cout << "vh2.get() = " << vh2.get() << std::endl;

    Pair p2(42, "hello");  // 自动推导
    std::cout << "Pair: (" << p2.first() << ", " << p2.second() << ")" << std::endl;
    std::cout << std::endl;

    std::cout << "=== 类模板基础演示完成 ===" << std::endl;
    return 0;
}
