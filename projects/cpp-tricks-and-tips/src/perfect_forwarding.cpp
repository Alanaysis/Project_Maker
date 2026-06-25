/**
 * perfect_forwarding.cpp - 完美转发 (Perfect Forwarding)
 *
 * 本文件全面演示 C++ 完美转发的原理和应用：
 *   1. 万能引用 (Universal References) / 转发引用 (Forwarding References)
 *   2. std::forward 的使用
 *   3. 工厂函数模式 (Factory Function Pattern)
 *   4. 常见陷阱和最佳实践
 *
 * 编译: g++ -std=c++17 -O2 -o perfect_forwarding perfect_forwarding.cpp
 *
 * 完美转发的核心思想：
 *   在模板函数中，将参数按照其原始的值类别（左值/右值）
 *   原封不动地转发给另一个函数，既不改变值类别，也不引入额外的拷贝。
 *
 * 关键概念：
 *   - T&& 在模板推导中是"万能引用"，可以绑定左值或右值
 *   - std::forward<T>(arg) 根据 T 的推导结果恢复原始值类别
 *   - 没有完美转发，泛型编程中的参数传递会导致不必要的拷贝
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <utility>   // std::move, std::forward
#include <type_traits>
#include <chrono>
#include <iomanip>
#include <functional>
#include <map>

// ============================================================================
// 第一部分：基础概念
// ============================================================================

// 辅助函数：判断值类别
// 利用重载来检测传入的是左值还是右值
void value_category(int&) {
    std::cout << "  左值引用 (lvalue reference)\n";
}

void value_category(const int&) {
    std::cout << "  const 左值引用 (const lvalue reference)\n";
}

void value_category(int&&) {
    std::cout << "  右值引用 (rvalue reference)\n";
}

// 字符串版本
void value_category(std::string&) {
    std::cout << "  左值引用 (lvalue reference)\n";
}

void value_category(const std::string&) {
    std::cout << "  const 左值引用 (const lvalue reference)\n";
}

void value_category(std::string&&) {
    std::cout << "  右值引用 (rvalue reference)\n";
}

// ============================================================================
// 第二部分：万能引用和 std::forward
// ============================================================================

/**
 * bad_forward - 错误的转发示例
 *
 * 即使参数是右值，param 本身是左值（有名字的右值引用是左值）
 * 所以 target 收到的永远是左值引用！
 */
template <typename T>
void bad_forward(T&& param) {
    std::cout << "错误转发: ";
    // param 是左值（有名字的变量都是左值）
    value_category(param);  // 永远是左值！
}

/**
 * good_forward - 正确的完美转发
 *
 * std::forward<T>(param) 会：
 *   - 如果 T 被推导为左值引用类型，返回左值
 *   - 如果 T 被推导为非引用类型（表示右值），返回右值
 *
 * 这样就能保持参数的原始值类别。
 */
template <typename T>
void good_forward(T&& param) {
    std::cout << "完美转发: ";
    // std::forward<T> 根据 T 恢复原始值类别
    value_category(std::forward<T>(param));
}

/**
 * demonstrate_forwarding - 演示转发行为
 */
void demonstrate_forwarding() {
    int x = 42;

    std::cout << "--- 传入左值 ---\n";
    std::cout << "错误转发:\n";
    bad_forward(x);     // T = int&, param = int&
    std::cout << "完美转发:\n";
    good_forward(x);    // T = int&, forward 保持左值

    std::cout << "\n--- 传入右值 ---\n";
    std::cout << "错误转发:\n";
    bad_forward(42);    // T = int, param = int&&，但 param 是左值！
    std::cout << "完美转发:\n";
    good_forward(42);   // T = int, forward 恢复为右值

    std::cout << "\n--- 传入 std::move ---\n";
    std::cout << "错误转发:\n";
    bad_forward(std::move(x));   // T = int, param = int&&，但 param 是左值！
    std::cout << "完美转发:\n";
    good_forward(std::move(x));  // T = int, forward 恢复为右值
}

// ============================================================================
// 第三部分：工厂函数模式
// ============================================================================

/**
 * Widget - 演示用的类，有多种构造函数
 */
class Widget {
public:
    // 默认构造
    Widget() : name_("默认"), value_(0) {
        std::cout << "  Widget 默认构造\n";
    }

    // 带名称的构造
    explicit Widget(std::string name) : name_(std::move(name)), value_(0) {
        std::cout << "  Widget 构造: \"" << name_ << "\"\n";
    }

    // 带名称和值的构造
    Widget(std::string name, int value) : name_(std::move(name)), value_(value) {
        std::cout << "  Widget 构造: \"" << name_ << "\" value=" << value_ << "\n";
    }

    // 拷贝构造
    Widget(const Widget& other) : name_(other.name_), value_(other.value_) {
        std::cout << "  Widget 拷贝构造: \"" << name_ << "\"\n";
    }

    // 移动构造
    Widget(Widget&& other) noexcept
        : name_(std::move(other.name_)), value_(other.value_) {
        std::cout << "  Widget 移动构造: \"" << name_ << "\"\n";
    }

    ~Widget() {
        std::cout << "  Widget 析构: \"" << name_ << "\"\n";
    }

    const std::string& name() const { return name_; }
    int value() const { return value_; }

private:
    std::string name_;
    int value_;
};

/**
 * make_widget - 工厂函数（错误版本）
 *
 * 问题：这里使用了值传递，会导致额外的拷贝/移动。
 * 当参数是左值时，会先拷贝一份到 param，然后再移动到 Widget 构造函数。
 */
template <typename T>
T make_widget_bad(T param) {
    std::cout << "(错误工厂) 参数类型: ";
    if constexpr (std::is_lvalue_reference_v<T>) {
        std::cout << "左值引用\n";
    } else {
        std::cout << "值\n";
    }
    return param;  // 再次移动
}

/**
 * make_widget - 工厂函数（正确版本 - 完美转发）
 *
 * 使用万能引用 + std::forward，参数按照原始值类别传递给 Widget 构造函数。
 * 没有额外的拷贝或移动！
 */
template <typename... Args>
std::unique_ptr<Widget> make_widget(Args&&... args) {
    std::cout << "(完美转发工厂)\n";
    return std::make_unique<Widget>(std::forward<Args>(args)...);
}

/**
 * wrap_widget - 包装函数示例
 *
 * 展示在中间层函数中如何正确转发参数。
 * 这在实际开发中非常常见：装饰器、代理、缓存层等。
 */
template <typename... Args>
std::unique_ptr<Widget> wrap_widget(const std::string& prefix, Args&&... args) {
    auto widget = std::make_unique<Widget>(std::forward<Args>(args)...);
    // 这里可以添加额外逻辑，如日志、缓存等
    std::cout << "  包装前缀: " << prefix << "\n";
    return widget;
}

// ============================================================================
// 第四部分：完美转发的实际应用
// ============================================================================

/**
 * Cache - 带完美转发的缓存
 *
 * 实际应用：缓存层使用完美转发来避免不必要的拷贝。
 * 当缓存未命中时，直接在目标位置构造对象。
 */
template <typename Key, typename Value>
class Cache {
public:
    /**
     * get_or_create - 获取缓存值或创建新值
     *
     * 如果 key 存在，返回缓存的值
     * 如果 key 不存在，使用提供的参数构造新值并缓存
     */
    template <typename... Args>
    Value& get_or_create(const Key& key, Args&&... args) {
        auto it = cache_.find(key);
        if (it != cache_.end()) {
            std::cout << "  缓存命中: " << key << "\n";
            return it->second;
        }

        std::cout << "  缓存未命中，创建: " << key << "\n";
        // 使用完美转发直接在 map 中构造值
        auto [inserted_it, success] = cache_.emplace(
            key,
            Value(std::forward<Args>(args)...)
        );
        return inserted_it->second;
    }

    size_t size() const { return cache_.size(); }

private:
    std::map<Key, Value> cache_;
};

/**
 * EventDispatcher - 事件分发器
 *
 * 完美转发在事件系统中的应用：
 * 将事件参数完美转发给所有监听器。
 */
class EventDispatcher {
public:
    using Callback = std::function<void(const std::string&, int)>;

    void add_listener(Callback cb) {
        listeners_.push_back(std::move(cb));
    }

    /**
     * dispatch - 分发事件
     *
     * 参数被完美转发给所有监听器。
     * 这里使用了通用引用来避免不必要的拷贝。
     */
    template <typename S, typename I>
    void dispatch(S&& event_name, I&& value) {
        for (auto& listener : listeners_) {
            listener(std::forward<S>(event_name), std::forward<I>(value));
        }
    }

private:
    std::vector<Callback> listeners_;
};

// ============================================================================
// 第五部分：常见陷阱
// ============================================================================

/**
 * 陷阱 1: 万能引用不是右值引用！
 *
 * T&& 只有在模板类型推导的上下文中才是万能引用。
 * 在非模板上下文中，T&& 就是普通的右值引用。
 */
namespace pitfalls {

// 这是万能引用（模板 + 类型推导）
template <typename T>
void universal_ref(T&& arg) {
    std::cout << "  T = " << typeid(T).name() << "\n";
}

// 这不是万能引用！（虽然看起来一样，但没有类型推导）
// 这里 T 已经确定是 int，所以 int&& 就是右值引用。
template <>
void universal_ref<int>(int&&) {
    std::cout << "  特化版本: 右值引用\n";
}

/**
 * 陷阱 2: 按值传递时不要用 std::forward
 *
 * 只有万能引用（T&&）才需要 std::forward。
 * 按值传递的参数已经是拷贝，直接使用即可。
 */
template <typename T>
void by_value_bad(T param) {
    // 错误！param 是按值传递的，已经是拷贝
    // 使用 std::forward 可能导致意外行为
    // some_function(std::forward<T>(param));  // 不推荐
}

template <typename T>
void by_value_good(T param) {
    // 正确：按值传递的参数直接使用或 std::move
    // some_function(std::move(param));  // 可以移动，因为 param 是本地拷贝
    (void)param;
}

/**
 * 陷阱 3: 完美转发失败的情况
 *
 * 某些情况下完美转发会失败：
 *   1. 花括号初始化列表
 *   2. 空指针常量 nullptr
 *   3. 声明为 bitfield 的成员
 */
template <typename... Args>
void try_forward(Args&&... args) {
    // 这里可以正常转发
    (void)sizeof...(args);
}

/**
 * 陷阱 4: 万能引用重载问题
 *
 * 万能引用的重载优先级很高，可能"抢走"本应匹配其他重载的调用。
 */
struct OverloadTrap {
    // 万能引用版本 - 匹配几乎任何东西！
    template <typename T>
    void process(T&& arg) {
        std::cout << "  万能引用版本\n";
    }

    // 这个版本可能永远不会被调用！
    void process(int) {
        std::cout << "  int 特化版本\n";
    }
};

/**
 * 解决方案：使用 SFINAE 或 concepts 限制万能引用
 */
template <typename T, typename = std::enable_if_t<!std::is_same_v<std::decay_t<T>, int>>>
void safe_process(T&& arg) {
    std::cout << "  万能引用版本 (SFINAE 保护)\n";
    (void)arg;
}

void safe_process(int arg) {
    std::cout << "  int 特化版本\n";
    (void)arg;
}

}  // namespace pitfalls

// ============================================================================
// 第六部分：性能测试
// ============================================================================

class Timer {
public:
    using Clock = std::chrono::high_resolution_clock;
    void start() { start_ = Clock::now(); }
    double elapsed_ms() const {
        return std::chrono::duration<double, std::milli>(Clock::now() - start_).count();
    }
private:
    Clock::time_point start_;
};

// std::map 已在顶部包含

void print_section(const char* title) {
    std::cout << "\n========================================\n"
              << title << "\n"
              << "========================================\n";
}

int main() {
    std::cout << "===== C++ 完美转发演示 =====\n";

    // ---- 演示 1: 转发行为演示 ----
    print_section("1. 转发行为演示");

    demonstrate_forwarding();

    // ---- 演示 2: 工厂函数 ----
    print_section("2. 工厂函数模式");

    {
        std::cout << "--- 使用完美转发的工厂函数 ---\n";

        // 左值参数
        std::string name = "我的部件";
        auto w1 = make_widget(name);
        std::cout << "  结果: " << w1->name() << "\n\n";

        // 右值参数（临时对象）
        auto w2 = make_widget("临时部件");
        std::cout << "  结果: " << w2->name() << "\n\n";

        // 多参数
        auto w3 = make_widget("带值部件", 42);
        std::cout << "  结果: " << w3->name() << " value=" << w3->value() << "\n\n";

        // 包装函数
        std::cout << "--- 包装函数（中间层转发）---\n";
        auto w4 = wrap_widget("[LOG]", "包装部件", 100);
    }

    // ---- 演示 3: 对比错误和正确的转发 ----
    print_section("3. 错误 vs 正确的转发");

    {
        std::string str = "测试字符串";

        std::cout << "--- 错误的工厂函数（按值传递）---\n";
        std::cout << "传入左值:\n";
        auto w1 = make_widget_bad(str);  // 拷贝一次到 param，再移动
        std::cout << "\n传入右值:\n";
        auto w2 = make_widget_bad(std::string("右值"));  // 移动到 param，再移动

        std::cout << "\n--- 正确的工厂函数（完美转发）---\n";
        std::cout << "传入左值:\n";
        auto w3 = make_widget(str);  // 直接转发，零拷贝
        std::cout << "\n传入右值:\n";
        auto w4 = make_widget(std::string("右值"));  // 直接转发，零拷贝
    }

    // ---- 演示 4: 缓存中的完美转发 ----
    print_section("4. 实际应用: 缓存");

    {
        Cache<std::string, Widget> cache;

        std::cout << "第一次访问（缓存未命中）:\n";
        auto& w1 = cache.get_or_create("key1", "缓存部件", 1);
        std::cout << "  结果: " << w1.name() << "\n\n";

        std::cout << "第二次访问（缓存命中）:\n";
        auto& w2 = cache.get_or_create("key1", "不应该创建", 999);
        std::cout << "  结果: " << w2.name() << " (应该是缓存部件)\n\n";

        std::cout << "缓存大小: " << cache.size() << "\n";
    }

    // ---- 演示 5: 事件分发器 ----
    print_section("5. 实际应用: 事件分发器");

    {
        EventDispatcher dispatcher;

        dispatcher.add_listener([](const std::string& event, int value) {
            std::cout << "  监听器1: " << event << " = " << value << "\n";
        });

        dispatcher.add_listener([](const std::string& event, int value) {
            std::cout << "  监听器2: " << event << " = " << value << "\n";
        });

        // 传入左值
        std::string event = "点击事件";
        std::cout << "分发左值事件:\n";
        dispatcher.dispatch(event, 100);

        // 传入右值
        std::cout << "\n分发右值事件:\n";
        dispatcher.dispatch(std::string("滚动事件"), 200);
    }

    // ---- 演示 6: 常见陷阱 ----
    print_section("6. 常见陷阱");

    {
        std::cout << "--- 陷阱1: 万能引用 vs 右值引用 ---\n";
        int x = 42;
        pitfalls::universal_ref(x);        // T = int&（左值）
        pitfalls::universal_ref(42);       // T = int（右值）

        std::cout << "\n--- 陷阱4: 万能引用重载问题 ---\n";
        pitfalls::OverloadTrap trap;
        trap.process(42);                  // 调用万能引用版本！不是 int 版本
        trap.process("hello");

        std::cout << "\n--- 解决方案: SFINAE 限制 ---\n";
        pitfalls::safe_process(42);        // 正确调用 int 版本
        pitfalls::safe_process("hello");   // 调用万能引用版本
    }

    // ---- 演示 7: 变参模板和完美转发 ----
    print_section("7. 变参模板 + 完美转发");

    {
        // 变参模板 + 完美转发是 C++ 泛型编程的核心模式

        /**
         * make_vector - 工厂函数，创建并初始化 vector
         *
         * 每个参数都被完美转发到 emplace_back，
         * 避免了不必要的拷贝。
         */
        auto make_vec = [](auto&&... args) {
            std::vector<std::string> vec;
            vec.reserve(sizeof...(args));
            // 折叠表达式 + 完美转发（C++17）
            (vec.emplace_back(std::forward<decltype(args)>(args)), ...);
            return vec;
        };

        std::string a = "Hello";
        auto vec = make_vec(a, "World", std::string("!"));

        std::cout << "vector 内容: ";
        for (const auto& s : vec) {
            std::cout << "[" << s << "] ";
        }
        std::cout << "\n";

        // 嵌套转发
        /**
         * emplace_new - 在已有 vector 中原地构造元素
         */
        std::vector<Widget> widgets;
        widgets.reserve(3);

        auto emplace_widget = [&widgets](auto&&... args) {
            widgets.emplace_back(std::forward<decltype(args)>(args)...);
        };

        std::cout << "\n嵌套转发构造 Widget:\n";
        emplace_widget();                    // 默认构造
        emplace_widget("直接构造");           // 单参数
        emplace_widget("带值构造", 42);       // 双参数
    }

    // ---- 演示 8: 性能对比 ----
    print_section("8. 性能对比: 完美转发 vs 拷贝");

    {
        Timer timer;
        const int N = 100000;

        // 模拟：通过中间层函数构造对象

        // 方式 1: 按值传递（导致额外拷贝）
        double value_time;
        {
            timer.start();
            std::vector<Widget> vec;
            vec.reserve(N);
            for (int i = 0; i < N; ++i) {
                // 按值传递：参数先拷贝到形参，再移动到 emplace_back
                auto add_by_value = [&vec](Widget w) {
                    vec.push_back(std::move(w));
                };
                add_by_value(Widget("test"));
                vec.clear();
            }
            value_time = timer.elapsed_ms();
        }

        // 方式 2: 完美转发（零额外拷贝）
        double forward_time;
        {
            timer.start();
            std::vector<Widget> vec;
            vec.reserve(N);
            for (int i = 0; i < N; ++i) {
                // 完美转发：参数直接传递到 emplace_back
                auto add_by_forward = [&vec](auto&&... args) {
                    vec.emplace_back(std::forward<decltype(args)>(args)...);
                };
                add_by_forward("test");
                vec.clear();
            }
            forward_time = timer.elapsed_ms();
        }

        std::cout << std::fixed << std::setprecision(2);
        std::cout << N << " 次构造:\n";
        std::cout << "  按值传递:     " << value_time << " ms\n";
        std::cout << "  完美转发:     " << forward_time << " ms\n";
        if (forward_time > 0) {
            std::cout << "  性能提升:     " << (value_time / forward_time) << "x\n";
        }
    }

    // ---- 总结 ----
    print_section("总结: 完美转发要点");

    std::cout <<
        "核心规则:\n\n"
        "1. T&& 在模板类型推导中是万能引用（转发引用）\n"
        "   - 可以绑定左值和右值\n"
        "   - T 被推导为左值引用类型（如 int&）当参数是左值\n"
        "   - T 被推导为非引用类型（如 int）当参数是右值\n\n"
        "2. 使用 std::forward<T>(param) 恢复原始值类别\n"
        "   - 如果 T 是左值引用，forward 返回左值\n"
        "   - 如果 T 是非引用类型，forward 返回右值\n\n"
        "3. 万能引用只在以下情况下成立:\n"
        "   - 函数模板的参数 T&&\n"
        "   - auto&&\n"
        "   - 不包括类模板的成员函数（除非类模板参数也被推导）\n\n"
        "4. 最佳实践:\n"
        "   - 工厂函数使用 (Args&&... args) + std::forward\n"
        "   - 转发时使用 std::forward，移动时使用 std::move\n"
        "   - 避免万能引用的重载（使用 SFINAE 或 concepts 限制）\n"
        "   - 按值传递的参数不要使用 std::forward\n\n"
        "5. 经典模式:\n"
        "   template <typename... Args>\n"
        "   std::unique_ptr<T> make(Args&&... args) {\n"
        "       return std::make_unique<T>(std::forward<Args>(args)...);\n"
        "   }\n";

    std::cout << "\n===== 演示结束 =====\n";
    return 0;
}
