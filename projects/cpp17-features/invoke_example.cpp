/**
 * @file invoke_example.cpp
 * @brief C++17 std::invoke 示例
 *
 * std::invoke 是一个通用的可调用对象调用接口。
 * 它可以调用任何可调用对象：函数、lambda、成员函数、函数对象等。
 *
 * 主要优势：
 * 1. 统一接口 - 一种方式调用所有可调用对象
 * 2. 成员函数支持 - 可以调用成员函数
 * 3. 通用性 - 适用于模板编程
 */

#include <iostream>
#include <functional>
#include <string>
#include <vector>
#include <algorithm>
#include <memory>
#include <tuple>
#include <map>

// 1. 基本 std::invoke 使用
void basic_invoke_example() {
    std::cout << "\n[基本 std::invoke 使用]" << std::endl;

    // 普通函数
    auto add = [](int a, int b) { return a + b; };
    int result1 = std::invoke(add, 3, 4);
    std::cout << "add(3, 4) = " << result1 << std::endl;

    // 函数对象
    struct Multiplier {
        int factor;
        int operator()(int x) const { return x * factor; }
    };

    Multiplier mult{5};
    int result2 = std::invoke(mult, 10);
    std::cout << "mult(10) = " << result2 << std::endl;

    // 函数指针
    auto func_ptr = +[](double x) { return x * x; };
    double result3 = std::invoke(func_ptr, 3.0);
    std::cout << "func_ptr(3.0) = " << result3 << std::endl;
}

// 2. 调用成员函数
void member_function_example() {
    std::cout << "\n[调用成员函数]" << std::endl;

    class Calculator {
    public:
        int add(int a, int b) const { return a + b; }
        int subtract(int a, int b) const { return a - b; }
        int multiply(int a, int b) const { return a * b; }
    };

    Calculator calc;

    // 调用成员函数
    int result1 = std::invoke(&Calculator::add, calc, 10, 5);
    std::cout << "calc.add(10, 5) = " << result1 << std::endl;

    int result2 = std::invoke(&Calculator::subtract, calc, 10, 5);
    std::cout << "calc.subtract(10, 5) = " << result2 << std::endl;

    // 使用指针调用成员函数
    auto calc_ptr = std::make_unique<Calculator>();
    int result3 = std::invoke(&Calculator::multiply, calc_ptr.get(), 10, 5);
    std::cout << "calc_ptr->multiply(10, 5) = " << result3 << std::endl;

    // 使用引用调用成员函数
    Calculator& calc_ref = calc;
    int result4 = std::invoke(&Calculator::add, calc_ref, 20, 30);
    std::cout << "calc_ref.add(20, 30) = " << result4 << std::endl;
}

// 3. 调用成员变量
void member_variable_example() {
    std::cout << "\n[调用成员变量]" << std::endl;

    struct Person {
        std::string name;
        int age;
        std::string city;

        Person(const std::string& n, int a, const std::string& c)
            : name(n), age(a), city(c) {}
    };

    Person person{"Alice", 30, "Beijing"};

    // 访问成员变量
    auto name = std::invoke(&Person::name, person);
    auto age = std::invoke(&Person::age, person);
    auto city = std::invoke(&Person::city, person);

    std::cout << "Name: " << name << std::endl;
    std::cout << "Age: " << age << std::endl;
    std::cout << "City: " << city << std::endl;

    // 使用指针访问
    auto person_ptr = std::make_unique<Person>("Bob", 25, "Shanghai");
    auto name_ptr = std::invoke(&Person::name, person_ptr.get());
    std::cout << "Name (ptr): " << name_ptr << std::endl;
}

// 4. 与 std::function 结合
void function_wrapper_example() {
    std::cout << "\n[与 std::function 结合]" << std::endl;

    // 存储不同类型的可调用对象
    std::function<int(int, int)> func;

    // Lambda
    func = [](int a, int b) { return a + b; };
    std::cout << "Lambda: " << std::invoke(func, 3, 4) << std::endl;

    // 函数对象
    struct Subtract {
        int operator()(int a, int b) const { return a - b; }
    };
    func = Subtract{};
    std::cout << "Function object: " << std::invoke(func, 10, 5) << std::endl;

    // 使用 std::bind
    auto multiply = [](int a, int b) { return a * b; };
    auto bound = std::bind(multiply, std::placeholders::_1, 2);
    std::cout << "Bound function: " << std::invoke(bound, 5) << std::endl;
}

// 5. 与算法结合
void algorithm_example() {
    std::cout << "\n[与算法结合]" << std::endl;

    struct Product {
        std::string name;
        double price;
        int quantity;
    };

    std::vector<Product> products = {
        {"Apple", 1.5, 10},
        {"Banana", 0.8, 20},
        {"Cherry", 3.0, 5}
    };

    // 使用 std::invoke 访问成员变量
    auto get_total = [](const Product& p) {
        return std::invoke(&Product::price, p) * std::invoke(&Product::quantity, p);
    };

    // 计算总价值
    double total = 0.0;
    for (const auto& product : products) {
        total += get_total(product);
    }
    std::cout << "Total value: $" << total << std::endl;

    // 使用 std::transform
    std::vector<double> totals(products.size());
    std::transform(products.begin(), products.end(), totals.begin(), get_total);

    std::cout << "Individual totals: ";
    for (double t : totals) {
        std::cout << "$" << t << " ";
    }
    std::cout << std::endl;
}

// 6. 与模板结合
template <typename Func, typename... Args>
auto invoke_and_log(Func&& func, Args&&... args) {
    std::cout << "Invoking function..." << std::endl;
    auto result = std::invoke(std::forward<Func>(func), std::forward<Args>(args)...);
    std::cout << "Result: " << result << std::endl;
    return result;
}

void template_example() {
    std::cout << "\n[与模板结合]" << std::endl;

    auto square = [](int x) { return x * x; };
    invoke_and_log(square, 5);

    auto add = [](int a, int b) { return a + b; };
    invoke_and_log(add, 3, 4);
}

// 7. 与回调结合
class Button {
public:
    using ClickHandler = std::function<void(const std::string&)>;

    Button(const std::string& name) : name_(name) {}

    void set_click_handler(ClickHandler handler) {
        click_handler_ = handler;
    }

    void click() {
        if (click_handler_) {
            std::invoke(click_handler_, name_);
        }
    }

private:
    std::string name_;
    ClickHandler click_handler_;
};

void callback_example() {
    std::cout << "\n[与回调结合]" << std::endl;

    Button button("Submit");

    button.set_click_handler([](const std::string& name) {
        std::cout << "Button '" << name << "' clicked!" << std::endl;
    });

    button.click();
}

// 8. 与事件系统结合
class EventEmitter {
public:
    using Handler = std::function<void()>;

    void on(const std::string& event, Handler handler) {
        handlers_[event].push_back(handler);
    }

    void emit(const std::string& event) {
        auto it = handlers_.find(event);
        if (it != handlers_.end()) {
            for (auto& handler : it->second) {
                std::invoke(handler);
            }
        }
    }

private:
    std::map<std::string, std::vector<Handler>> handlers_;
};

void event_system_example() {
    std::cout << "\n[与事件系统结合]" << std::endl;

    EventEmitter emitter;

    emitter.on("start", []() {
        std::cout << "Event started" << std::endl;
    });

    emitter.on("start", []() {
        std::cout << "Logging start event" << std::endl;
    });

    emitter.on("stop", []() {
        std::cout << "Event stopped" << std::endl;
    });

    std::cout << "Emitting 'start':" << std::endl;
    emitter.emit("start");

    std::cout << "Emitting 'stop':" << std::endl;
    emitter.emit("stop");
}

// 9. 与策略模式结合
class SortStrategy {
public:
    virtual ~SortStrategy() = default;
    virtual void sort(std::vector<int>& data) = 0;
};

class BubbleSort : public SortStrategy {
public:
    void sort(std::vector<int>& data) override {
        std::cout << "Using BubbleSort" << std::endl;
        // 简化的冒泡排序
        for (size_t i = 0; i < data.size(); ++i) {
            for (size_t j = 0; j < data.size() - i - 1; ++j) {
                if (data[j] > data[j + 1]) {
                    std::swap(data[j], data[j + 1]);
                }
            }
        }
    }
};

class QuickSort : public SortStrategy {
public:
    void sort(std::vector<int>& data) override {
        std::cout << "Using QuickSort" << std::endl;
        std::sort(data.begin(), data.end());
    }
};

void strategy_pattern_example() {
    std::cout << "\n[与策略模式结合]" << std::endl;

    auto bubble = std::make_unique<BubbleSort>();
    auto quick = std::make_unique<QuickSort>();

    std::vector<int> data1 = {5, 3, 1, 4, 2};
    std::vector<int> data2 = {5, 3, 1, 4, 2};

    std::invoke(&SortStrategy::sort, bubble.get(), data1);
    std::invoke(&SortStrategy::sort, quick.get(), data2);

    std::cout << "BubbleSort result: ";
    for (int v : data1) std::cout << v << " ";
    std::cout << std::endl;

    std::cout << "QuickSort result: ";
    for (int v : data2) std::cout << v << " ";
    std::cout << std::endl;
}

// 10. 性能考虑
void performance_example() {
    std::cout << "\n[性能考虑]" << std::endl;

    std::cout << "std::invoke 是编译期分发，没有运行时开销" << std::endl;
    std::cout << "等价于直接调用 func(args...)" << std::endl;

    auto func = [](int x) { return x * 2; };

    // 这两种方式在编译后是等价的
    int result1 = std::invoke(func, 42);
    int result2 = func(42);

    std::cout << "std::invoke: " << result1 << std::endl;
    std::cout << "Direct call: " << result2 << std::endl;
}

// 11. 与 std::apply 结合
void apply_invoke_example() {
    std::cout << "\n[与 std::apply 结合]" << std::endl;

    struct Processor {
        int process(int a, int b, int c) const {
            return a + b + c;
        }
    };

    Processor proc;
    auto args = std::make_tuple(1, 2, 3);

    // 使用 std::apply 和 std::invoke 结合
    int result = std::apply(
        [&proc](auto&&... args) {
            return std::invoke(&Processor::process, proc, std::forward<decltype(args)>(args)...);
        },
        args
    );

    std::cout << "Result: " << result << std::endl;
}

// 12. 最佳实践
void best_practices_example() {
    std::cout << "\n[最佳实践]" << std::endl;

    std::cout << "1. 使用场景:" << std::endl;
    std::cout << "   - 需要统一调用接口时" << std::endl;
    std::cout << "   - 调用成员函数时" << std::endl;
    std::cout << "   - 模板编程中" << std::endl;

    std::cout << "\n2. 优势:" << std::endl;
    std::cout << "   - 统一接口" << std::endl;
    std::cout << "   - 类型安全" << std::endl;
    std::cout << "   - 零开销抽象" << std::endl;

    std::cout << "\n3. 注意事项:" << std::endl;
    std::cout << "   - 不要过度使用" << std::endl;
    std::cout << "   - 直接调用更简洁时，优先使用直接调用" << std::endl;
    std::cout << "   - 主要用于泛型编程" << std::endl;
}

// 主示例函数
void invoke_example() {
    std::cout << "=== std::invoke ===" << std::endl;

    basic_invoke_example();
    member_function_example();
    member_variable_example();
    function_wrapper_example();
    algorithm_example();
    template_example();
    callback_example();
    event_system_example();
    strategy_pattern_example();
    performance_example();
    apply_invoke_example();
    best_practices_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    invoke_example();
    return 0;
}
#endif
