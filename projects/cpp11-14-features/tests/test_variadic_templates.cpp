/**
 * 可变参数模板测试
 */

#include <gtest/gtest.h>
#include <string>
#include <vector>
#include <tuple>

// 测试可变参数模板基础
template<typename... Args>
int count_args(Args... args) {
    return sizeof...(args);
}

TEST(VariadicTemplates, Basic) {
    EXPECT_EQ(count_args(), 0);
    EXPECT_EQ(count_args(1), 1);
    EXPECT_EQ(count_args(1, 2, 3), 3);
    EXPECT_EQ(count_args(1, 2, 3, 4, 5), 5);
}

// 测试递归展开
template<typename T>
T sum_recursive(T t) {
    return t;
}

template<typename T, typename... Args>
T sum_recursive(T first, Args... rest) {
    return first + sum_recursive(rest...);
}

TEST(VariadicTemplates, Recursive) {
    EXPECT_EQ(sum_recursive(1, 2, 3), 6);
    EXPECT_EQ(sum_recursive(1, 2, 3, 4, 5), 15);
    EXPECT_DOUBLE_EQ(sum_recursive(1.5, 2.5, 3.5), 7.5);
}

// 测试完美转发
class Widget {
    int value_;

public:
    Widget(int v) : value_(v) {}
    int value() const { return value_; }
};

template<typename T, typename... Args>
std::unique_ptr<T> make_unique_perfect(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

TEST(VariadicTemplates, PerfectForwarding) {
    auto widget = make_unique_perfect<Widget>(42);
    EXPECT_EQ(widget->value(), 42);
}

// 测试元组
template<typename... Args>
auto make_tuple_custom(Args&&... args) {
    return std::make_tuple(std::forward<Args>(args)...);
}

TEST(VariadicTemplates, Tuple) {
    auto t = make_tuple_custom(1, 3.14, std::string("Hello"));
    EXPECT_EQ(std::get<0>(t), 1);
    EXPECT_DOUBLE_EQ(std::get<1>(t), 3.14);
    EXPECT_EQ(std::get<2>(t), "Hello");
}

// 测试参数包展开
template<typename... Args>
void print_to_vector(std::vector<int>& vec, Args... args) {
    int dummy[] = { (vec.push_back(args), 0)... };
    (void)dummy;
}

TEST(VariadicTemplates, PackExpansion) {
    std::vector<int> vec;
    print_to_vector(vec, 1, 2, 3, 4, 5);

    EXPECT_EQ(vec.size(), 5);
    EXPECT_EQ(vec[0], 1);
    EXPECT_EQ(vec[4], 5);
}

// 测试可变参数模板与继承
template<typename... Types>
struct TypeList {};

// 计算类型列表大小的辅助函数
template<typename... Types>
constexpr size_t count_types(TypeList<Types...>) {
    return sizeof...(Types);
}

TEST(VariadicTemplates, Inheritance) {
    using MyTypes = TypeList<int, double, std::string>;
    EXPECT_EQ(count_types(MyTypes{}), 3);
}

// 测试可变参数模板与函数应用
template<typename Func, typename... Args>
void apply(Func func, Args... args) {
    int dummy[] = { (func(args), 0)... };
    (void)dummy;
}

TEST(VariadicTemplates, FunctionApplication) {
    std::vector<int> results;
    auto collect = [&results](int x) { results.push_back(x * 2); };

    apply(collect, 1, 2, 3, 4, 5);

    EXPECT_EQ(results.size(), 5);
    EXPECT_EQ(results[0], 2);
    EXPECT_EQ(results[4], 10);
}

// 测试可变参数模板与事件系统
template<typename... Args>
class Event {
    std::vector<std::function<void(Args...)>> handlers_;

public:
    void add_handler(std::function<void(Args...)> handler) {
        handlers_.push_back(std::move(handler));
    }

    void emit(Args... args) const {
        for (const auto& handler : handlers_) {
            handler(args...);
        }
    }
};

TEST(VariadicTemplates, EventSystem) {
    Event<int, std::string> event;
    std::vector<std::pair<int, std::string>> results;

    event.add_handler([&results](int x, const std::string& s) {
        results.push_back({x, s});
    });

    event.emit(42, "Hello");

    EXPECT_EQ(results.size(), 1);
    EXPECT_EQ(results[0].first, 42);
    EXPECT_EQ(results[0].second, "Hello");
}

// 测试可变参数模板与容器初始化
template<typename T, typename... Args>
class Container {
    std::vector<T> data_;

public:
    Container(Args... args) {
        int dummy[] = { (data_.push_back(args), 0)... };
        (void)dummy;
    }

    size_t size() const { return data_.size(); }
    const T& operator[](size_t i) const { return data_[i]; }
};

TEST(VariadicTemplates, ContainerInit) {
    Container<int, int, int, int> c(1, 2, 3);
    EXPECT_EQ(c.size(), 3);
    EXPECT_EQ(c[0], 1);
    EXPECT_EQ(c[2], 3);
}
