/**
 * @file 06_naming_conventions.cpp
 * @brief 命名规范示例
 *
 * 命名规范：提高代码可读性和可维护性
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>

// ============================================================================
// 常见命名规范
// ============================================================================

/**
 * 命名规范 1：类名使用 PascalCase
 *
 * 例如：MyClass, HttpClient, DatabaseConnection
 */
class MyClass {
public:
    void doSomething() {}
};

class HttpClient {
public:
    void sendRequest() {}
};

/**
 * 命名规范 2：函数名使用 camelCase
 *
 * 例如：getValue, setName, processData
 */
class Calculator {
public:
    int add(int a, int b) { return a + b; }
    int subtract(int a, int b) { return a - b; }
    double calculateAverage(const std::vector<int>& values) {
        if (values.empty()) return 0.0;
        int sum = 0;
        for (int val : values) {
            sum += val;
        }
        return static_cast<double>(sum) / values.size();
    }
};

/**
 * 命名规范 3：变量名使用 camelCase 或 snake_case
 *
 * 例如：userName, user_name, totalCount
 */
void variable_naming() {
    // camelCase
    int totalCount = 0;
    std::string userName = "John";

    // snake_case
    int total_count = 0;
    std::string user_name = "John";

    std::cout << "totalCount: " << totalCount << std::endl;
    std::cout << "user_name: " << user_name << std::endl;
}

/**
 * 命名规范 4：常量使用 UPPER_SNAKE_CASE 或 kCamelCase
 *
 * 例如：MAX_SIZE, kMaxSize, PI
 */
const int MAX_SIZE = 100;
const int kMaxSize = 100;
const double PI = 3.14159265358979323846;

void constant_naming() {
    std::cout << "MAX_SIZE: " << MAX_SIZE << std::endl;
    std::cout << "kMaxSize: " << kMaxSize << std::endl;
    std::cout << "PI: " << PI << std::endl;
}

/**
 * 命名规范 5：成员变量使用 m_ 前缀或下划线后缀
 *
 * 例如：m_name, name_, m_count, count_
 */
class Person {
public:
    Person(const std::string& name, int age)
        : m_name(name), m_age(age) {}

    const std::string& getName() const { return m_name; }
    int getAge() const { return m_age; }

private:
    std::string m_name;
    int m_age;
};

/**
 * 命名规范 6：枚举使用 PascalCase 或 UPPER_SNAKE_CASE
 *
 * 例如：Color, ColorType, COLOR_RED
 */
enum class Color {
    Red,
    Green,
    Blue
};

enum ColorType {
    COLOR_RED,
    COLOR_GREEN,
    COLOR_BLUE
};

/**
 * 命名规范 7：命名空间使用 lowercase
 *
 * 例如：my_namespace, utils, core
 */
namespace my_namespace {
    void doSomething() {
        std::cout << "my_namespace::doSomething" << std::endl;
    }
}

namespace utils {
    void printMessage(const std::string& msg) {
        std::cout << msg << std::endl;
    }
}

/**
 * 命名规范 8：模板参数使用 PascalCase
 *
 * 例如：T, Container, Iterator
 */
template <typename T>
class Container {
public:
    void add(const T& item) {
        items_.push_back(item);
    }

    const std::vector<T>& getItems() const { return items_; }

private:
    std::vector<T> items_;
};

/**
 * 命名规范 9：布尔变量使用 is, has, can 前缀
 *
 * 例如：isValid, hasValue, canExecute
 */
class Status {
public:
    bool isValid() const { return valid_; }
    bool hasError() const { return !error_.empty(); }
    bool canProcess() const { return valid_ && error_.empty(); }

private:
    bool valid_ = true;
    std::string error_;
};

/**
 * 命名规范 10：函数命名清晰表达意图
 *
 * 例如：calculateTotal, getUserById, validateInput
 */
class UserService {
public:
    std::string getUserById(int id) {
        return "User" + std::to_string(id);
    }

    bool validateInput(const std::string& input) {
        return !input.empty();
    }

    double calculateTotal(const std::vector<double>& prices) {
        double total = 0.0;
        for (double price : prices) {
            total += price;
        }
        return total;
    }
};

// ============================================================================
// 命名最佳实践
// ============================================================================

/**
 * 最佳实践 1：有意义的命名
 *
 * 避免使用无意义的变量名
 */
void meaningful_naming() {
    // 不好
    int x = 42;
    std::string s = "hello";

    // 好
    int userAge = 42;
    std::string userName = "hello";

    std::cout << "userAge: " << userAge << std::endl;
    std::cout << "userName: " << userName << std::endl;
}

/**
 * 最佳实践 2：避免缩写
 *
 * 使用完整的单词
 */
void avoid_abbreviations() {
    // 不好
    int cnt = 0;
    std::string nm = "John";

    // 好
    int count = 0;
    std::string name = "John";

    std::cout << "count: " << count << std::endl;
    std::cout << "name: " << name << std::endl;
}

/**
 * 最佳实践 3：保持一致性
 *
 * 在整个项目中保持一致的命名风格
 */
void consistent_naming() {
    // 选择一种风格并坚持使用
    // 例如：camelCase
    int totalCount = 0;
    std::string userName = "John";
    double averageScore = 95.5;

    std::cout << "totalCount: " << totalCount << std::endl;
    std::cout << "userName: " << userName << std::endl;
    std::cout << "averageScore: " << averageScore << std::endl;
}

/**
 * 最佳实践 4：使用描述性名称
 *
 * 名称应该描述变量的用途
 */
void descriptive_naming() {
    // 不好
    int d = 10;  // 什么的 10？

    // 好
    int maxRetryCount = 10;
    int daysUntilExpiration = 10;

    std::cout << "maxRetryCount: " << maxRetryCount << std::endl;
    std::cout << "daysUntilExpiration: " << daysUntilExpiration << std::endl;
}

/**
 * 最佳实践 5：避免使用单字母变量名
 *
 * 除了循环计数器和 lambda 参数
 */
void avoid_single_letter() {
    // 不好
    int a = 1;
    int b = 2;
    int c = a + b;

    // 好
    int firstNumber = 1;
    int secondNumber = 2;
    int sum = firstNumber + secondNumber;

    // 可以接受的单字母变量
    for (int i = 0; i < 10; i++) {
        // i 是常见的循环计数器
    }

    auto lambda = [](int x) { return x * 2; };  // x 在简短 lambda 中可以接受
}

// ============================================================================
// Google C++ Style Guide 示例
// ============================================================================

/**
 * Google 风格示例
 *
 * 类名：PascalCase
 * 函数名：PascalCase
 * 变量名：snake_case
 * 常量：kConstantName
 * 成员变量：snake_name_
 */
class GoogleStyleExample {
public:
    static const int kMaxSize = 100;

    GoogleStyleExample(int value) : value_(value) {}

    int GetValue() const { return value_; }
    void SetValue(int value) { value_ = value; }

    static void DoSomething() {
        std::cout << "Doing something" << std::endl;
    }

private:
    int value_;
};

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 命名规范示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "[1] 类名：PascalCase" << std::endl;
    MyClass obj;
    obj.doSomething();
    std::cout << std::endl;

    std::cout << "[2] 函数名：camelCase" << std::endl;
    Calculator calc;
    std::cout << "add: " << calc.add(1, 2) << std::endl;
    std::cout << std::endl;

    std::cout << "[3] 变量名" << std::endl;
    variable_naming();
    std::cout << std::endl;

    std::cout << "[4] 常量名" << std::endl;
    constant_naming();
    std::cout << std::endl;

    std::cout << "[5] 成员变量" << std::endl;
    Person person("John", 30);
    std::cout << "name: " << person.getName() << std::endl;
    std::cout << "age: " << person.getAge() << std::endl;
    std::cout << std::endl;

    std::cout << "[6] 枚举" << std::endl;
    Color color = Color::Red;
    std::cout << "color: " << static_cast<int>(color) << std::endl;
    std::cout << std::endl;

    std::cout << "[7] 命名空间" << std::endl;
    my_namespace::doSomething();
    utils::printMessage("Hello");
    std::cout << std::endl;

    std::cout << "[8] 模板参数" << std::endl;
    Container<int> container;
    container.add(1);
    container.add(2);
    std::cout << "size: " << container.getItems().size() << std::endl;
    std::cout << std::endl;

    std::cout << "[9] 布尔变量" << std::endl;
    Status status;
    std::cout << "isValid: " << status.isValid() << std::endl;
    std::cout << "hasError: " << status.hasError() << std::endl;
    std::cout << std::endl;

    std::cout << "[10] 最佳实践" << std::endl;
    meaningful_naming();
    avoid_abbreviations();
    consistent_naming();
    std::cout << std::endl;

    std::cout << "[11] Google 风格" << std::endl;
    GoogleStyleExample example(42);
    std::cout << "value: " << example.GetValue() << std::endl;
    GoogleStyleExample::DoSomething();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
