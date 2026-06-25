/**
 * @file move_only_function_example.cpp
 * @brief C++23 std::move_only_function 示例
 *
 * std::move_only_function 是 C++23 引入的可移动但不可复制的函数包装器。
 * 它用于包装那些包含只能移动的资源的可调用对象。
 *
 * 主要特点：
 * - 可移动但不可复制
 * - 可以包装 lambda、函数指针、仿函数等
 * - 支持移动语义的资源管理
 * - 适用于异步编程和任务队列
 *
 * 编译命令：
 * g++ -std=c++23 -o move_only_function_example move_only_function_example.cpp
 */

#include <iostream>
#include <functional>
#include <memory>
#include <vector>
#include <string>
#include <utility>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // 包装普通 lambda
    std::move_only_function<int(int, int)> add = [](int a, int b) {
        return a + b;
    };
    std::cout << "add(3, 4) = " << add(3, 4) << std::endl;

    // 包装函数指针
    auto multiply = [](int a, int b) -> int {
        return a * b;
    };
    std::move_only_function<int(int, int)> func = multiply;
    std::cout << "multiply(3, 4) = " << func(3, 4) << std::endl;

    // 移动函数对象
    std::move_only_function<int(int, int)> func2 = std::move(func);
    std::cout << "After move, func2(3, 4) = " << func2(3, 4) << std::endl;

    // 检查是否为空
    if (func) {
        std::cout << "func is valid" << std::endl;
    } else {
        std::cout << "func is empty (moved from)" << std::endl;
    }
}

// ========== 2. 包装只移动类型 ==========

// 包装包含 unique_ptr 的 lambda
void move_only_capture() {
    std::cout << "\n=== 包装只移动类型 ===" << std::endl;

    auto ptr = std::make_unique<int>(42);

    // 使用 move_only_function 包装包含 unique_ptr 的 lambda
    std::move_only_function<int()> get_value = [p = std::move(ptr)]() {
        return *p;
    };

    std::cout << "Value: " << get_value() << std::endl;

    // 移动函数对象
    std::move_only_function<int()> get_value2 = std::move(get_value);
    std::cout << "After move, value: " << get_value2() << std::endl;
}

// ========== 3. 与 std::function 对比 ==========

void comparison_with_std_function() {
    std::cout << "\n=== 与 std::function 对比 ===" << std::endl;

    auto ptr = std::make_unique<int>(100);

    // std::function 不能包装只移动的捕获
    // std::function<int()> func = [p = std::move(ptr)]() { return *p; };  // 编译错误

    // std::move_only_function 可以
    std::move_only_function<int()> func = [p = std::move(ptr)]() {
        return *p;
    };

    std::cout << "move_only_function works with unique_ptr capture" << std::endl;
    std::cout << "Value: " << func() << std::endl;
}

// ========== 4. 任务队列 ==========

class TaskQueue {
private:
    std::vector<std::move_only_function<void()>> tasks_;

public:
    void push(std::move_only_function<void()> task) {
        tasks_.push_back(std::move(task));
    }

    void execute_all() {
        for (auto& task : tasks_) {
            task();
        }
        tasks_.clear();
    }

    size_t size() const { return tasks_.size(); }
};

void task_queue_example() {
    std::cout << "\n=== 任务队列 ===" << std::endl;

    TaskQueue queue;

    // 添加普通任务
    queue.push([]() {
        std::cout << "Task 1: Simple task" << std::endl;
    });

    // 添加包含只移动资源的任务
    auto data = std::make_unique<std::string>("Hello, World!");
    queue.push([d = std::move(data)]() {
        std::cout << "Task 2: Data = " << *d << std::endl;
    });

    // 添加更多任务
    queue.push([]() {
        std::cout << "Task 3: Another task" << std::endl;
    });

    std::cout << "Queue size: " << queue.size() << std::endl;
    std::cout << "Executing all tasks:" << std::endl;
    queue.execute_all();
}

// ========== 5. 回调系统 ==========

class EventSystem {
private:
    std::vector<std::move_only_function<void(const std::string&)>> handlers_;

public:
    void register_handler(std::move_only_function<void(const std::string&)> handler) {
        handlers_.push_back(std::move(handler));
    }

    void emit(const std::string& event) {
        for (auto& handler : handlers_) {
            handler(event);
        }
    }
};

void callback_example() {
    std::cout << "\n=== 回调系统 ===" << std::endl;

    EventSystem events;

    // 注册普通回调
    events.register_handler([](const std::string& event) {
        std::cout << "Handler 1: " << event << std::endl;
    });

    // 注册包含只移动资源的回调
    auto logger = std::make_unique<std::string>("Logger");
    events.register_handler([l = std::move(logger)](const std::string& event) {
        std::cout << *l << ": " << event << std::endl;
    });

    // 触发事件
    events.emit("Button clicked");
    events.emit("File opened");
}

// ========== 6. 工厂模式 ==========

class Widget {
public:
    virtual ~Widget() = default;
    virtual void draw() const = 0;
};

class Button : public Widget {
    std::string label_;
public:
    Button(std::string label) : label_(std::move(label)) {}
    void draw() const override {
        std::cout << "Button: " << label_ << std::endl;
    }
};

class TextBox : public Widget {
    std::string text_;
public:
    TextBox(std::string text) : text_(std::move(text)) {}
    void draw() const override {
        std::cout << "TextBox: " << text_ << std::endl;
    }
};

// 使用 move_only_function 作为工厂函数
using WidgetFactory = std::move_only_function<std::unique_ptr<Widget>()>;

class WidgetFactoryRegistry {
    std::vector<std::pair<std::string, WidgetFactory>> factories_;

public:
    void register_factory(const std::string& type, WidgetFactory factory) {
        factories_.emplace_back(type, std::move(factory));
    }

    std::unique_ptr<Widget> create(const std::string& type) {
        for (auto& [name, factory] : factories_) {
            if (name == type) {
                return factory();
            }
        }
        return nullptr;
    }
};

void factory_example() {
    std::cout << "\n=== 工厂模式 ===" << std::endl;

    WidgetFactoryRegistry registry;

    // 注册工厂函数
    registry.register_factory("button", []() {
        return std::make_unique<Button>("OK");
    });

    registry.register_factory("textbox", []() {
        return std::make_unique<TextBox>("Hello");
    });

    // 创建部件
    auto button = registry.create("button");
    auto textbox = registry.create("textbox");

    if (button) button->draw();
    if (textbox) textbox->draw();
}

// ========== 7. 线程安全的任务系统 ==========

class Task {
    std::move_only_function<void()> func_;
    std::string name_;

public:
    Task(std::string name, std::move_only_function<void()> func)
        : name_(std::move(name)), func_(std::move(func)) {}

    void execute() {
        std::cout << "Executing task: " << name_ << std::endl;
        func_();
    }

    const std::string& name() const { return name_; }
};

void task_example() {
    std::cout << "\n=== 任务系统 ===" << std::endl;

    std::vector<Task> tasks;

    // 创建任务
    tasks.emplace_back("Initialize", []() {
        std::cout << "  Initializing system..." << std::endl;
    });

    auto config = std::make_unique<std::string>("config.json");
    tasks.emplace_back("Load Config", [c = std::move(config)]() {
        std::cout << "  Loading from: " << *c << std::endl;
    });

    tasks.emplace_back("Cleanup", []() {
        std::cout << "  Cleaning up..." << std::endl;
    });

    // 执行所有任务
    for (auto& task : tasks) {
        task.execute();
    }
}

// ========== 8. 函数组合 ==========

void function_composition() {
    std::cout << "\n=== 函数组合 ===" << std::endl;

    // 创建可组合的函数
    std::move_only_function<int(int)> double_it = [](int x) { return x * 2; };
    std::move_only_function<int(int)> add_one = [](int x) { return x + 1; };

    // 组合函数
    std::move_only_function<int(int)> composed = [f = std::move(double_it),
                                                   g = std::move(add_one)](int x) {
        return f(g(x));
    };

    std::cout << "composed(5) = " << composed(5) << std::endl;  // (5 + 1) * 2 = 12
}

int main() {
    std::cout << "C++23 std::move_only_function 示例\n" << std::endl;

    basic_usage();
    move_only_capture();
    comparison_with_std_function();
    task_queue_example();
    callback_example();
    factory_example();
    task_example();
    function_composition();

    return 0;
}
