/**
 * @file nested_namespaces.cpp
 * @brief C++17 嵌套命名空间示例
 *
 * C++17 允许使用简洁的语法定义嵌套命名空间，
 * 替代传统的多层嵌套写法。
 *
 * 主要优势：
 * 1. 语法简洁 - 减少缩进层级
 * 2. 可读性好 - 更清晰的命名空间结构
 * 3. 易于维护 - 简化命名空间管理
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <algorithm>

// 1. 传统嵌套命名空间（C++17 之前）
namespace Old {
    namespace Network {
        namespace HTTP {
            class Client {
            public:
                void connect() {
                    std::cout << "Old::Network::HTTP::Client::connect()" << std::endl;
                }
            };
        }
    }
}

// 2. C++17 嵌套命名空间
namespace New::Network::HTTP {
    class Client {
    public:
        void connect() {
            std::cout << "New::Network::HTTP::Client::connect()" << std::endl;
        }
    };
}

void basic_nested_example() {
    std::cout << "\n[基本嵌套命名空间]" << std::endl;

    Old::Network::HTTP::Client old_client;
    old_client.connect();

    New::Network::HTTP::Client new_client;
    new_client.connect();
}

// 3. 多层嵌套命名空间
namespace App::Database::MySQL {
    class Connection {
    public:
        void open() {
            std::cout << "App::Database::MySQL::Connection::open()" << std::endl;
        }
    };
}

namespace App::Database::PostgreSQL {
    class Connection {
    public:
        void open() {
            std::cout << "App::Database::PostgreSQL::Connection::open()" << std::endl;
        }
    };
}

void multi_level_example() {
    std::cout << "\n[多层嵌套命名空间]" << std::endl;

    App::Database::MySQL::Connection mysql_conn;
    mysql_conn.open();

    App::Database::PostgreSQL::Connection pg_conn;
    pg_conn.open();
}

// 4. 命名空间别名
namespace App::Network::HTTP::Response {
    struct Status {
        int code;
        std::string message;
    };
}

// 创建别名简化访问
namespace HTTP = App::Network::HTTP;
namespace Response = App::Network::HTTP::Response;

void alias_example() {
    std::cout << "\n[命名空间别名]" << std::endl;

    Response::Status status{200, "OK"};
    std::cout << "Status: " << status.code << " " << status.message << std::endl;
}

// 5. 嵌套命名空间与内联
namespace App {
    namespace Config {
        inline namespace v1 {
            class Config {
            public:
                std::string get_version() const { return "v1"; }
            };
        }
    }
}

// 版本升级
// inline namespace App::Config {
//     inline namespace v2 {
//         class Config {
//         public:
//             std::string get_version() const { return "v2"; }
//         };
//     }
// }

void inline_namespace_example() {
    std::cout << "\n[内联命名空间]" << std::endl;

    // 可以直接使用，无需指定版本
    App::Config::Config config;
    std::cout << "Config version: " << config.get_version() << std::endl;

    // 也可以显式指定版本
    App::Config::v1::Config v1_config;
    std::cout << "Explicit v1: " << v1_config.get_version() << std::endl;
}

// 6. 嵌套命名空间与模板
namespace App::Math {
    template <typename T>
    class Vector2D {
    public:
        T x, y;

        Vector2D(T x = 0, T y = 0) : x(x), y(y) {}

        Vector2D operator+(const Vector2D& other) const {
            return {x + other.x, y + other.y};
        }

        friend std::ostream& operator<<(std::ostream& os, const Vector2D& v) {
            return os << "(" << v.x << ", " << v.y << ")";
        }
    };

    template <typename T>
    T dot_product(const Vector2D<T>& a, const Vector2D<T>& b) {
        return a.x * b.x + a.y * b.y;
    }
}

void template_example() {
    std::cout << "\n[嵌套命名空间与模板]" << std::endl;

    App::Math::Vector2D<int> v1(1, 2);
    App::Math::Vector2D<int> v2(3, 4);

    auto v3 = v1 + v2;
    std::cout << "v1 + v2 = " << v3 << std::endl;
    std::cout << "dot_product(v1, v2) = " << App::Math::dot_product(v1, v2) << std::endl;
}

// 7. 嵌套命名空间与工厂模式
namespace App::Graphics {
    class Shape {
    public:
        virtual ~Shape() = default;
        virtual void draw() const = 0;
    };

    class Circle : public Shape {
    public:
        void draw() const override {
            std::cout << "Drawing Circle" << std::endl;
        }
    };

    class Rectangle : public Shape {
    public:
        void draw() const override {
            std::cout << "Drawing Rectangle" << std::endl;
        }
    };

    class Factory {
    public:
        static std::unique_ptr<Shape> create(const std::string& type) {
            if (type == "circle") {
                return std::make_unique<Circle>();
            } else if (type == "rectangle") {
                return std::make_unique<Rectangle>();
            }
            return nullptr;
        }
    };
}

void factory_example() {
    std::cout << "\n[嵌套命名空间与工厂模式]" << std::endl;

    auto circle = App::Graphics::Factory::create("circle");
    auto rect = App::Graphics::Factory::create("rectangle");

    if (circle) circle->draw();
    if (rect) rect->draw();
}

// 8. 嵌套命名空间与策略模式
namespace App::Algorithm {
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

    class Sorter {
    public:
        void set_strategy(std::unique_ptr<SortStrategy> strategy) {
            strategy_ = std::move(strategy);
        }

        void sort(std::vector<int>& data) {
            if (strategy_) {
                strategy_->sort(data);
            }
        }

    private:
        std::unique_ptr<SortStrategy> strategy_;
    };
}

void strategy_example() {
    std::cout << "\n[嵌套命名空间与策略模式]" << std::endl;

    App::Algorithm::Sorter sorter;
    std::vector<int> data = {5, 3, 1, 4, 2};

    sorter.set_strategy(std::make_unique<App::Algorithm::BubbleSort>());
    sorter.sort(data);

    std::cout << "Sorted: ";
    for (int v : data) {
        std::cout << v << " ";
    }
    std::cout << std::endl;
}

// 9. 嵌套命名空间与观察者模式
namespace App::Event {
    class Observer {
    public:
        virtual ~Observer() = default;
        virtual void on_event(const std::string& event) = 0;
    };

    class Subject {
    public:
        void attach(Observer* observer) {
            observers_.push_back(observer);
        }

        void notify(const std::string& event) {
            for (auto* observer : observers_) {
                observer->on_event(event);
            }
        }

    private:
        std::vector<Observer*> observers_;
    };
}

class Logger : public App::Event::Observer {
public:
    void on_event(const std::string& event) override {
        std::cout << "[LOG] Event: " << event << std::endl;
    }
};

void observer_example() {
    std::cout << "\n[嵌套命名空间与观察者模式]" << std::endl;

    App::Event::Subject subject;
    Logger logger;

    subject.attach(&logger);
    subject.notify("user_login");
    subject.notify("data_update");
}

// 10. 嵌套命名空间的优势总结
void summary_example() {
    std::cout << "\n[嵌套命名空间的优势]" << std::endl;

    std::cout << "1. 语法简洁:" << std::endl;
    std::cout << "   传统: namespace A { namespace B { namespace C { ... } } }" << std::endl;
    std::cout << "   C++17: namespace A::B::C { ... }" << std::endl;

    std::cout << "\n2. 可读性好:" << std::endl;
    std::cout << "   - 减少缩进层级" << std::endl;
    std::cout << "   - 更清晰的命名空间结构" << std::endl;

    std::cout << "\n3. 易于维护:" << std::endl;
    std::cout << "   - 简化命名空间管理" << std::endl;
    std::cout << "   - 便于重构" << std::endl;

    std::cout << "\n4. 与内联命名空间结合:" << std::endl;
    std::cout << "   - 支持版本控制" << std::endl;
    std::cout << "   - 支持 ABI 兼容性" << std::endl;
}

// 主示例函数
void nested_namespaces_example() {
    std::cout << "=== 嵌套命名空间 ===" << std::endl;

    basic_nested_example();
    multi_level_example();
    alias_example();
    inline_namespace_example();
    template_example();
    factory_example();
    strategy_example();
    observer_example();
    summary_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    nested_namespaces_example();
    return 0;
}
#endif
