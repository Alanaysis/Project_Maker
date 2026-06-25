/**
 * C++11 可变参数模板示例
 *
 * 学习目标：
 * 1. 理解可变参数模板的基本语法
 * 2. 掌握参数包展开技术
 * 3. 学会使用递归展开模式
 * 4. 理解完美转发与可变参数模板的配合
 */

#include <iostream>
#include <string>
#include <vector>
#include <tuple>
#include <memory>
#include <functional>

// ==========================================
// 1. 基本可变参数模板
// ==========================================

// 基本函数模板
template<typename... Args>
void print(Args... args) {
    // C++17 折叠表达式
    // (std::cout << ... << args) << std::endl;

    // C++11/14 方式：使用递归展开
    // 这里我们使用一个更简单的方法
    int dummy[] = { (std::cout << args << " ", 0)... };
    (void)dummy;  // 避免未使用警告
    std::cout << std::endl;
}

void demonstrate_basic_variadic() {
    std::cout << "\n=== 1. 基本可变参数模板 ===" << std::endl;

    // 不同参数数量
    print(1, 2, 3);
    print("Hello", "World");
    print(1, 3.14, "C++", true);

    // 不同类型
    print(42, " is the answer", '!');
}

// ==========================================
// 2. 递归展开模式
// ==========================================

// 递归终止条件
void print_recursive() {
    std::cout << std::endl;
}

// 递归展开
template<typename T, typename... Args>
void print_recursive(T first, Args... rest) {
    std::cout << first;
    if (sizeof...(rest) > 0) {
        std::cout << ", ";
    }
    print_recursive(rest...);
}

void demonstrate_recursive() {
    std::cout << "\n=== 2. 递归展开模式 ===" << std::endl;

    print_recursive(1, 2, 3, 4, 5);
    print_recursive("Hello", "World", "C++");
    print_recursive(1, 3.14, "test", true);
}

// ==========================================
// 3. 参数包大小
// ==========================================

template<typename... Args>
void count_args(Args... args) {
    std::cout << "参数数量: " << sizeof...(args) << std::endl;
    std::cout << "参数类型数量: " << sizeof...(Args) << std::endl;
}

void demonstrate_sizeof() {
    std::cout << "\n=== 3. 参数包大小 ===" << std::endl;

    count_args(1, 2, 3);
    count_args("Hello", "World");
    count_args();
}

// ==========================================
// 4. 完美转发与可变参数模板
// ==========================================

class Widget {
    std::string name_;

public:
    Widget(const std::string& name) : name_(name) {
        std::cout << "  [Widget] 构造: " << name_ << std::endl;
    }

    Widget(std::string&& name) : name_(std::move(name)) {
        std::cout << "  [Widget] 移动构造: " << name_ << std::endl;
    }

    ~Widget() {
        std::cout << "  [Widget] 析构: " << name_ << std::endl;
    }

    const std::string& name() const { return name_; }
};

// 使用完美转发创建对象
template<typename T, typename... Args>
std::unique_ptr<T> make_unique_perfect(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

void demonstrate_perfect_forwarding() {
    std::cout << "\n=== 4. 完美转发与可变参数模板 ===" << std::endl;

    // 使用完美转发创建 Widget
    auto w1 = make_unique_perfect<Widget>("Widget1");
    auto w2 = make_unique_perfect<Widget>(std::string("Widget2"));

    std::cout << "w1: " << w1->name() << std::endl;
    std::cout << "w2: " << w2->name() << std::endl;
}

// ==========================================
// 5. 可变参数模板与元组
// ==========================================

// 创建元组
template<typename... Args>
auto make_tuple_custom(Args&&... args) {
    return std::make_tuple(std::forward<Args>(args)...);
}

// 打印元组
template<typename Tuple, std::size_t... I>
void print_tuple_impl(const Tuple& t, std::index_sequence<I...>) {
    int dummy[] = { (std::cout << std::get<I>(t) << " ", 0)... };
    (void)dummy;
}

template<typename... Args>
void print_tuple(const std::tuple<Args...>& t) {
    print_tuple_impl(t, std::index_sequence_for<Args...>{});
    std::cout << std::endl;
}

void demonstrate_tuple() {
    std::cout << "\n=== 5. 可变参数模板与元组 ===" << std::endl;

    // 创建元组
    auto t = make_tuple_custom(1, 3.14, "Hello", 'A');
    std::cout << "元组: ";
    print_tuple(t);

    // 使用 make_tuple
    auto t2 = std::make_tuple(42, std::string("World"), true);
    std::cout << "元组2: ";
    print_tuple(t2);
}

// ==========================================
// 6. 可变参数模板与继承
// ==========================================

// 使用递归继承展开参数包
template<typename... Types>
struct TypeList {};

// 计算类型列表大小
template<typename... Types>
constexpr size_t type_list_size(TypeList<Types...>) {
    return sizeof...(Types);
}

// 获取第 N 个类型
template<size_t N, typename... Types>
struct Get;

// 基础情况：N=0
template<typename Head, typename... Tail>
struct Get<0, TypeList<Head, Tail...>> {
    using type = Head;
};

// 递归情况
template<size_t N, typename Head, typename... Tail>
struct Get<N, TypeList<Head, Tail...>> {
    using type = typename Get<N - 1, TypeList<Tail...>>::type;
};

void demonstrate_inheritance() {
    std::cout << "\n=== 6. 可变参数模板与继承 ===" << std::endl;

    using MyTypes = TypeList<int, double, std::string>;
    std::cout << "类型数量: " << type_list_size(MyTypes{}) << std::endl;

    // 获取第 0 个类型
    using FirstType = Get<0, MyTypes>::type;
    std::cout << "第 0 个类型是 int: "
              << std::is_same<FirstType, int>::value << std::endl;

    // 获取第 2 个类型
    using ThirdType = Get<2, MyTypes>::type;
    std::cout << "第 2 个类型是 string: "
              << std::is_same<ThirdType, std::string>::value << std::endl;
}

// ==========================================
// 7. 可变参数模板与函数式编程
// ==========================================

// 折叠操作（C++11/14 方式）
template<typename T>
T sum_single(T t) {
    return t;
}

template<typename T, typename... Args>
T sum_single(T first, Args... rest) {
    return first + sum_single(rest...);
}

template<typename... Args>
auto sum(Args... args) {
    return sum_single(args...);
}

// C++11/14 方式
template<typename T>
T sum_recursive(T t) {
    return t;
}

template<typename T, typename... Args>
T sum_recursive(T first, Args... rest) {
    return first + sum_recursive(rest...);
}

// 应用函数到参数
template<typename Func, typename... Args>
void apply(Func func, Args... args) {
    // C++17 折叠表达式
    // (func(args), ...);

    // C++11/14 方式
    int dummy[] = { (func(args), 0)... };
    (void)dummy;
}

void demonstrate_functional() {
    std::cout << "\n=== 7. 可变参数模板与函数式编程 ===" << std::endl;

    // 求和
    std::cout << "sum(1, 2, 3, 4, 5) = " << sum_recursive(1, 2, 3, 4, 5) << std::endl;
    std::cout << "sum(1.5, 2.5, 3.5) = " << sum_recursive(1.5, 2.5, 3.5) << std::endl;

    // 应用函数
    std::cout << "\n应用函数:" << std::endl;
    apply([](int x) { std::cout << "  " << x * 2 << " "; }, 1, 2, 3, 4, 5);
    std::cout << std::endl;

    // 应用到字符串
    apply([](const std::string& s) { std::cout << "  " << s << " "; },
          std::string("Hello"), std::string("World"), std::string("C++"));
    std::cout << std::endl;
}

// ==========================================
// 8. 可变参数模板的实际应用
// ==========================================

// 事件系统
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

// 通用容器
template<typename T>
class Container {
    std::vector<T> data_;

public:
    template<typename... Args>
    Container(Args... args) {
        // 使用初始化列表展开
        int dummy[] = { (data_.push_back(args), 0)... };
        (void)dummy;
    }

    void print() const {
        for (const auto& item : data_) {
            std::cout << item << " ";
        }
        std::cout << std::endl;
    }
};

void demonstrate_practical() {
    std::cout << "\n=== 8. 可变参数模板的实际应用 ===" << std::endl;

    // 事件系统
    std::cout << "--- 事件系统 ---" << std::endl;
    Event<int, std::string> click_event;

    click_event.add_handler([](int x, const std::string& button) {
        std::cout << "  处理点击: x=" << x << ", button=" << button << std::endl;
    });

    click_event.add_handler([](int x, const std::string& button) {
        std::cout << "  记录日志: x=" << x << ", button=" << button << std::endl;
    });

    click_event.emit(100, "left");

    // 通用容器
    std::cout << "\n--- 通用容器 ---" << std::endl;
    Container<int> container(1, 2, 3, 4);
    container.print();
}

// ==========================================
// 主函数
// ==========================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "C++11 可变参数模板示例" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. 基本可变参数模板
    demonstrate_basic_variadic();

    // 2. 递归展开模式
    demonstrate_recursive();

    // 3. 参数包大小
    demonstrate_sizeof();

    // 4. 完美转发
    demonstrate_perfect_forwarding();

    // 5. 元组
    demonstrate_tuple();

    // 6. 继承
    demonstrate_inheritance();

    // 7. 函数式编程
    demonstrate_functional();

    // 8. 实际应用
    demonstrate_practical();

    std::cout << "\n========================================" << std::endl;
    std::cout << "所有示例执行完毕！" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
