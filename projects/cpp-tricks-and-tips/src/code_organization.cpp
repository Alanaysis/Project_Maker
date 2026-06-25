/**
 * code_organization.cpp - 代码组织与架构模式
 *
 * 本文件演示 C++ 中的代码组织技术，包括：
 *   1. 命名空间 (Namespace) 使用
 *   2. Pimpl 惯用法（编译防火墙）
 *   3. 头文件/源文件分离概念
 *   4. C++20 模块概念
 *
 * 良好的代码组织是大型 C++ 项目成功的关键。
 *
 * 编译命令:
 *   g++ -std=c++20 -o code_organization code_organization.cpp
 */

#include <iostream>
#include <string>
#include <string_view>
#include <memory>
#include <vector>
#include <map>
#include <functional>
#include <sstream>
#include <algorithm>
#include <optional>
#include <cmath>

// ============================================================================
// 第一部分: 命名空间 (Namespace)
// ============================================================================
// 命名空间用于组织代码，避免名称冲突
// 是 C++ 中最基本的代码组织工具

// 基础命名空间
namespace math {

    // 常量
    constexpr double PI = 3.14159265358979323846;
    constexpr double E = 2.71828182845904523536;

    // 基础运算
    namespace basic {
        int add(int a, int b) { return a + b; }
        int subtract(int a, int b) { return a - b; }
        int multiply(int a, int b) { return a * b; }

        // 安全除法（避免除零）
        std::optional<double> divide(double a, double b) {
            if (b == 0.0) return std::nullopt;
            return a / b;
        }
    }  // namespace basic

    // 高级数学函数
    namespace advanced {
        double power(double base, int exp) {
            double result = 1.0;
            bool negative = exp < 0;
            exp = std::abs(exp);
            for (int i = 0; i < exp; ++i) {
                result *= base;
            }
            return negative ? 1.0 / result : result;
        }

        // 阶乘
        long long factorial(int n) {
            if (n <= 1) return 1;
            long long result = 1;
            for (int i = 2; i <= n; ++i) {
                result *= i;
            }
            return result;
        }
    }  // namespace advanced

    // 向量运算
    namespace vector_ops {
        struct Vec2 {
            double x, y;

            Vec2 operator+(const Vec2& other) const {
                return {x + other.x, y + other.y};
            }

            Vec2 operator*(double scalar) const {
                return {x * scalar, y * scalar};
            }

            double dot(const Vec2& other) const {
                return x * other.x + y * other.y;
            }

            double length() const {
                return std::sqrt(x * x + y * y);
            }
        };
    }  // namespace vector_ops

}  // namespace math

// 嵌套命名空间 (C++17 语法)
namespace app::network::http {

    struct Request {
        std::string method;
        std::string url;
        std::map<std::string, std::string> headers;
    };

    struct Response {
        int status_code;
        std::string body;
        std::map<std::string, std::string> headers;
    };

    class Client {
    public:
        Response get(std::string_view url) {
            return {200, "OK: " + std::string(url), {}};
        }

        Response post(std::string_view url, std::string_view body) {
            return {201, "Created: " + std::string(body), {}};
        }
    };

}  // namespace app::network::http

// 命名空间别名
namespace http = app::network::http;

// 内联命名空间 (用于版本控制)
namespace app {
    inline namespace v2 {
        class Logger {
        public:
            void log(std::string_view msg) {
                std::cout << "[v2] " << msg << std::endl;
            }
        };
    }

    namespace v1 {
        class Logger {
        public:
            void log(std::string_view msg) {
                std::cout << "[v1] " << msg << std::endl;
            }
        };
    }
}  // namespace app

// 匿名命名空间（替代 static 的文件内部链接）
namespace {
    int internal_counter = 0;

    void internal_helper() {
        ++internal_counter;
    }
}  // namespace

void demo_namespaces() {
    std::cout << "========================================" << std::endl;
    std::cout << "1. 命名空间 (Namespace)" << std::endl;
    std::cout << "========================================" << std::endl;

    // 使用嵌套命名空间
    std::cout << "\n--- 数学命名空间 ---" << std::endl;
    std::cout << "PI = " << math::PI << std::endl;
    std::cout << "2 + 3 = " << math::basic::add(2, 3) << std::endl;

    auto result = math::basic::divide(10, 3);
    if (result) std::cout << "10 / 3 = " << *result << std::endl;

    std::cout << "5! = " << math::advanced::factorial(5) << std::endl;
    std::cout << "2^10 = " << math::advanced::power(2, 10) << std::endl;

    // 向量运算
    math::vector_ops::Vec2 v1{1.0, 2.0};
    math::vector_ops::Vec2 v2{3.0, 4.0};
    auto v3 = v1 + v2;
    std::cout << "向量加法: (" << v3.x << ", " << v3.y << ")" << std::endl;
    std::cout << "点积: " << v1.dot(v2) << std::endl;

    // C++17 嵌套命名空间
    std::cout << "\n--- HTTP 客户端 ---" << std::endl;
    http::Client client;
    auto resp = client.get("/api/users");
    std::cout << "状态码: " << resp.status_code << std::endl;
    std::cout << "响应: " << resp.body << std::endl;

    // 命名空间别名
    std::cout << "\n--- 命名空间别名 ---" << std::endl;
    std::cout << "http::Client 等价于 app::network::http::Client" << std::endl;

    // 内联命名空间（版本控制）
    std::cout << "\n--- 内联命名空间 ---" << std::endl;
    app::Logger logger;  // 默认使用 v2（内联版本）
    logger.log("默认版本");

    app::v1::Logger old_logger;  // 显式使用 v1
    old_logger.log("旧版本");

    // 匿名命名空间
    std::cout << "\n--- 匿名命名空间 ---" << std::endl;
    internal_helper();
    internal_helper();
    std::cout << "内部计数器: " << internal_counter << std::endl;

    // using 声明
    std::cout << "\n--- using 声明 ---" << std::endl;
    using math::basic::add;
    using math::basic::subtract;
    std::cout << "add(5, 3) = " << add(5, 3) << std::endl;
    std::cout << "subtract(5, 3) = " << subtract(5, 3) << std::endl;

    // using 指令（谨慎使用，可能引起名称冲突）
    // using namespace math::basic;  // 不推荐在全局作用域使用
}

// ============================================================================
// 第二部分: Pimpl 惯用法（编译防火墙）
// ============================================================================
// Pimpl = Pointer to Implementation
// 将实现细节隐藏在 .cpp 文件中，减少编译依赖

// Pimpl 示例：数据库连接类
// 在头文件中只需要声明，不需要暴露实现细节
class DatabaseConnection {
public:
    // 构函数声明（需要在 .cpp 中定义，因为需要知道 Impl 的完整类型）
    DatabaseConnection(const std::string& connection_string);
    ~DatabaseConnection();

    // 移动操作（Pimpl 支持移动）
    DatabaseConnection(DatabaseConnection&&) noexcept;
    DatabaseConnection& operator=(DatabaseConnection&&) noexcept;

    // 禁止拷贝（或实现深拷贝）
    DatabaseConnection(const DatabaseConnection&) = delete;
    DatabaseConnection& operator=(const DatabaseConnection&) = delete;

    // 公共接口
    bool connect();
    void disconnect();
    bool is_connected() const;

    std::vector<std::map<std::string, std::string>>
    query(const std::string& sql);

    std::string get_server_info() const;

private:
    // 前向声明实现类
    struct Impl;

    // 唯一指针指向实现
    std::unique_ptr<Impl> m_impl;
};

// 实现类定义（通常在 .cpp 文件中）
// 这里为了演示放在同一文件
struct DatabaseConnection::Impl {
    std::string connection_string;
    std::string host;
    int port;
    bool connected;
    std::vector<std::map<std::string, std::string>> cached_results;

    Impl(const std::string& cs)
        : connection_string(cs), port(3306), connected(false) {
        // 解析连接字符串
        auto pos = cs.find(':');
        if (pos != std::string::npos) {
            host = cs.substr(0, pos);
            try {
                port = std::stoi(cs.substr(pos + 1));
            } catch (...) {
                port = 3306;
            }
        } else {
            host = cs;
        }
    }

    bool do_connect() {
        // 模拟连接
        std::cout << "  [Impl] 连接到 " << host << ":" << port << std::endl;
        connected = true;
        return true;
    }

    void do_disconnect() {
        std::cout << "  [Impl] 断开连接" << std::endl;
        connected = false;
    }

    std::vector<std::map<std::string, std::string>>
    do_query(const std::string& sql) {
        // 模拟查询
        std::vector<std::map<std::string, std::string>> results;
        results.push_back({{"id", "1"}, {"name", "Alice"}});
        results.push_back({{"id", "2"}, {"name", "Bob"}});
        return results;
    }
};

// 成员函数实现
DatabaseConnection::DatabaseConnection(const std::string& connection_string)
    : m_impl(std::make_unique<Impl>(connection_string)) {}

DatabaseConnection::~DatabaseConnection() = default;

DatabaseConnection::DatabaseConnection(DatabaseConnection&&) noexcept = default;
DatabaseConnection& DatabaseConnection::operator=(DatabaseConnection&&) noexcept = default;

bool DatabaseConnection::connect() {
    return m_impl->do_connect();
}

void DatabaseConnection::disconnect() {
    m_impl->do_disconnect();
}

bool DatabaseConnection::is_connected() const {
    return m_impl->connected;
}

std::vector<std::map<std::string, std::string>>
DatabaseConnection::query(const std::string& sql) {
    return m_impl->do_query(sql);
}

std::string DatabaseConnection::get_server_info() const {
    return m_impl->host + ":" + std::to_string(m_impl->port);
}

// 第二个 Pimpl 示例：图形渲染器
class Renderer {
public:
    Renderer(int width, int height);
    ~Renderer();

    Renderer(Renderer&&) noexcept;
    Renderer& operator=(Renderer&&) noexcept;

    void clear(int r, int g, int b);
    void draw_rect(int x, int y, int w, int h);
    void present();
    std::string get_stats() const;

private:
    struct Impl;
    std::unique_ptr<Impl> m_impl;
};

struct Renderer::Impl {
    int width, height;
    int draw_calls;
    std::string last_operation;

    Impl(int w, int h) : width(w), height(h), draw_calls(0) {}

    void do_clear(int r, int g, int b) {
        last_operation = "clear(" + std::to_string(r) + ","
                       + std::to_string(g) + "," + std::to_string(b) + ")";
        ++draw_calls;
    }

    void do_draw_rect(int x, int y, int w, int h) {
        last_operation = "draw_rect(" + std::to_string(x) + ","
                       + std::to_string(y) + "," + std::to_string(w) + ","
                       + std::to_string(h) + ")";
        ++draw_calls;
    }
};

Renderer::Renderer(int width, int height)
    : m_impl(std::make_unique<Impl>(width, height)) {}
Renderer::~Renderer() = default;
Renderer::Renderer(Renderer&&) noexcept = default;
Renderer& Renderer::operator=(Renderer&&) noexcept = default;

void Renderer::clear(int r, int g, int b) { m_impl->do_clear(r, g, b); }
void Renderer::draw_rect(int x, int y, int w, int h) { m_impl->do_draw_rect(x, y, w, h); }
void Renderer::present() { std::cout << "  [Renderer] 呈现帧" << std::endl; }
std::string Renderer::get_stats() const {
    return "绘制调用: " + std::to_string(m_impl->draw_calls)
         + ", 最后操作: " + m_impl->last_operation;
}

void demo_pimpl() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "2. Pimpl 惯用法（编译防火墙）" << std::endl;
    std::cout << "========================================" << std::endl;

    // 数据库连接
    std::cout << "\n--- 数据库连接 ---" << std::endl;
    {
        DatabaseConnection db("localhost:3306");
        std::cout << "服务器: " << db.get_server_info() << std::endl;

        db.connect();
        std::cout << "已连接: " << (db.is_connected() ? "是" : "否") << std::endl;

        auto results = db.query("SELECT * FROM users");
        std::cout << "查询结果: " << results.size() << " 行" << std::endl;

        db.disconnect();
    }

    // 图形渲染器
    std::cout << "\n--- 图形渲染器 ---" << std::endl;
    {
        Renderer renderer(1920, 1080);
        renderer.clear(0, 0, 0);
        renderer.draw_rect(10, 10, 100, 100);
        renderer.draw_rect(200, 200, 50, 50);
        renderer.present();

        std::cout << "统计: " << renderer.get_stats() << std::endl;
    }

    std::cout << "\nPimpl 的优势:" << std::endl;
    std::cout << "  1. 编译防火墙：修改实现不需要重新编译依赖方" << std::endl;
    std::cout << "  2. 信息隐藏：头文件不暴露实现细节" << std::endl;
    std::cout << "  3. ABI 稳定：二进制兼容性更好" << std::endl;
}

// ============================================================================
// 第三部分: 头文件/源文件分离概念
// ============================================================================
// 虽然本文件是单文件演示，但展示分离的原则和最佳实践

// 模拟头文件声明（通常放在 .h 文件中）

// 接口类（纯虚类）- 定义契约
class IShape {
public:
    virtual ~IShape() = default;
    virtual double area() const = 0;
    virtual double perimeter() const = 0;
    virtual std::string name() const = 0;
    virtual std::string to_string() const = 0;
};

// 工厂函数声明（通常在头文件中声明）
std::unique_ptr<IShape> create_circle(double radius);
std::unique_ptr<IShape> create_rectangle(double width, double height);

// 模拟源文件实现（通常放在 .cpp 文件中）

class CircleImpl : public IShape {
public:
    explicit CircleImpl(double r) : m_radius(r) {}

    double area() const override {
        return math::PI * m_radius * m_radius;
    }

    double perimeter() const override {
        return 2 * math::PI * m_radius;
    }

    std::string name() const override { return "Circle"; }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "Circle(radius=" << m_radius << ")";
        return oss.str();
    }

private:
    double m_radius;
};

class RectangleImpl : public IShape {
public:
    RectangleImpl(double w, double h) : m_width(w), m_height(h) {}

    double area() const override {
        return m_width * m_height;
    }

    double perimeter() const override {
        return 2 * (m_width + m_height);
    }

    std::string name() const override { return "Rectangle"; }

    std::string to_string() const override {
        std::ostringstream oss;
        oss << "Rectangle(" << m_width << "x" << m_height << ")";
        return oss.str();
    }

private:
    double m_width, m_height;
};

// 工厂函数实现
std::unique_ptr<IShape> create_circle(double radius) {
    return std::make_unique<CircleImpl>(radius);
}

std::unique_ptr<IShape> create_rectangle(double width, double height) {
    return std::make_unique<RectangleImpl>(width, height);
}

void demo_separation() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "3. 头文件/源文件分离概念" << std::endl;
    std::cout << "========================================" << std::endl;

    // 使用接口和工厂函数
    std::cout << "\n--- 接口与实现分离 ---" << std::endl;

    std::vector<std::unique_ptr<IShape>> shapes;
    shapes.push_back(create_circle(5.0));
    shapes.push_back(create_rectangle(4.0, 6.0));
    shapes.push_back(create_circle(3.0));

    for (const auto& shape : shapes) {
        std::cout << "  " << shape->to_string()
                  << " 面积=" << shape->area()
                  << " 周长=" << shape->perimeter() << std::endl;
    }

    std::cout << "\n头文件/源文件分离的原则:" << std::endl;
    std::cout << "  1. 头文件 (.h/.hpp):" << std::endl;
    std::cout << "     - 类声明、函数声明" << std::endl;
    std::cout << "     - 模板定义（必须在头文件中）" << std::endl;
    std::cout << "     - 内联函数" << std::endl;
    std::cout << "     - include guard (#pragma once)" << std::endl;

    std::cout << "  2. 源文件 (.cpp):" << std::endl;
    std::cout << "     - 函数实现" << std::endl;
    std::cout << "     - 静态变量定义" << std::endl;
    std::cout << "     - 内部辅助函数" << std::endl;

    std::cout << "  3. 依赖管理:" << std::endl;
    std::cout << "     - 头文件尽量少 include" << std::endl;
    std::cout << "     - 使用前向声明减少依赖" << std::endl;
    std::cout << "     - Pimpl 隐藏实现依赖" << std::endl;
}

// ============================================================================
// 第四部分: C++20 模块概念
// ============================================================================
// C++20 模块是头文件的现代替代方案
// 提供更好的编译性能和封装性

// 注意：实际的模块语法需要 .cppm 文件和模块编译器支持
// 这里展示模块的概念和优势

void demo_modules() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "4. C++20 模块概念" << std::endl;
    std::cout << "========================================" << std::endl;

    std::cout << R"(
    C++20 模块 (Modules) 概述:

    1. 模块声明文件 (.cppm 或 .ixx):

       // math.cppm
       export module math;

       export namespace math {
           constexpr double PI = 3.14159265358979;

           export double add(double a, double b) {
               return a + b;
           }

           export class Calculator {
           public:
               double compute(double a, double b, char op);
           };
       }

    2. 模块实现文件:

       // math_impl.cpp
       module math;

       double math::Calculator::compute(double a, double b, char op) {
           switch (op) {
               case '+': return a + b;
               case '-': return a - b;
               case '*': return a * b;
               case '/': return b != 0 ? a / b : 0;
               default: return 0;
           }
       }

    3. 使用模块:

       // main.cpp
       import math;
       import <iostream>;  // 标准库模块

       int main() {
           std::cout << math::PI << std::endl;
           std::cout << math::add(1, 2) << std::endl;
       }

    模块的优势:

    1. 编译速度提升:
       - 模块只需编译一次，不需要重复解析头文件
       - 消除宏污染和包含顺序问题

    2. 更好的封装:
       - 只有 export 声明对外可见
       - 实现细节完全隐藏
       - 不会意外暴露内部宏或类型

    3. 消除头文件问题:
       - 不需要 include guard
       - 不需要前向声明
       - 不会因为包含顺序导致编译错误

    4. 更好的工具支持:
       - IDE 可以更准确地分析依赖关系
       - 构建系统可以更好地并行编译

    模块的使用场景:

    1. 库的公共接口:
       export module mylib;
       // 只导出用户需要的接口

    2. 大型项目的内部模块:
       module myapp.database;
       module myapp.network;
       // 清晰的模块边界

    3. 替换预编译头:
       import <vector>;
       import <string>;
       // 比预编译头更可靠
    )" << std::endl;
}

// ============================================================================
// 第五部分: 代码组织最佳实践
// ============================================================================

void demo_best_practices() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "5. 代码组织最佳实践" << std::endl;
    std::cout << "========================================" << std::endl;

    std::cout << R"(
    C++ 代码组织最佳实践:

    1. 目录结构:
       project/
       ├── include/          # 公共头文件
       │   └── mylib/
       │       ├── module1.h
       │       └── module2.h
       ├── src/              # 源文件
       │   ├── module1.cpp
       │   └── module2.cpp
       ├── tests/            # 测试文件
       │   ├── test_module1.cpp
       │   └── test_module2.cpp
       └── CMakeLists.txt    # 构建配置

    2. 头文件最佳实践:
       - 使用 #pragma once 或 include guard
       - 尽量少 include，使用前向声明
       - 模板实现放在头文件中
       - 内联函数放在头文件中
       - 避免在头文件中定义全局变量

    3. 命名空间最佳实践:
       - 使用项目级命名空间
       - 避免 using namespace 在头文件中
       - 内部实现放在 detail 或 impl 命名空间
       - 使用嵌套命名空间组织模块

    4. 依赖管理:
       - 依赖接口，不依赖实现
       - 使用依赖注入降低耦合
       - 避免循环依赖
       - 使用 Pimpl 减少编译依赖

    5. 编译策略:
       - 减少头文件依赖
       - 使用预编译头 (PCH)
       - 考虑使用 C++20 模块
       - 合理划分编译单元
    )" << std::endl;

    // 实际示例：使用接口降低耦合
    std::cout << "\n--- 依赖注入示例 ---" << std::endl;

    // 定义接口
    class ILogger {
    public:
        virtual ~ILogger() = default;
        virtual void info(std::string_view msg) = 0;
        virtual void error(std::string_view msg) = 0;
    };

    // 控制台日志实现
    class ConsoleLogger : public ILogger {
    public:
        void info(std::string_view msg) override {
            std::cout << "[INFO] " << msg << std::endl;
        }
        void error(std::string_view msg) override {
            std::cerr << "[ERROR] " << msg << std::endl;
        }
    };

    // 服务类依赖接口，不依赖具体实现
    class UserService {
    public:
        explicit UserService(std::shared_ptr<ILogger> logger)
            : m_logger(std::move(logger)) {}

        void create_user(const std::string& name) {
            m_logger->info("创建用户: " + name);
            // 业务逻辑...
            m_logger->info("用户创建成功");
        }

    private:
        std::shared_ptr<ILogger> m_logger;
    };

    // 使用依赖注入
    auto logger = std::make_shared<ConsoleLogger>();
    UserService service(logger);
    service.create_user("张三");
}

// ============================================================================
// 主函数
// ============================================================================
int main() {
    std::cout << "╔══════════════════════════════════════╗" << std::endl;
    std::cout << "║  代码组织与架构 (code_organization)  ║" << std::endl;
    std::cout << "╚══════════════════════════════════════╝" << std::endl;
    std::cout << std::endl;

    demo_namespaces();
    demo_pimpl();
    demo_separation();
    demo_modules();
    demo_best_practices();

    std::cout << "\n代码组织演示完成。" << std::endl;
    return 0;
}
