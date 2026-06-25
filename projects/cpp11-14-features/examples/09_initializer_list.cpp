/**
 * C++11 初始化列表示例
 *
 * 学习目标：
 * 1. 掌握统一初始化语法
 * 2. 理解 std::initializer_list
 * 3. 学会使用聚合初始化
 * 4. 了解初始化列表的最佳实践
 */

#include <iostream>
#include <vector>
#include <map>
#include <set>
#include <string>
#include <initializer_list>
#include <algorithm>

// ==========================================
// 1. 统一初始化语法
// ==========================================

void demonstrate_uniform_initialization() {
    std::cout << "\n=== 1. 统一初始化语法 ===" << std::endl;

    // 基本类型
    int a = 42;
    int b(42);
    int c{42};      // C++11 统一初始化
    int d = {42};   // 等价形式

    std::cout << "a = " << a << std::endl;
    std::cout << "b = " << b << std::endl;
    std::cout << "c = " << c << std::endl;
    std::cout << "d = " << d << std::endl;

    // 数组
    int arr1[] = {1, 2, 3, 4, 5};
    int arr2[]{1, 2, 3, 4, 5};  // C++11

    std::cout << "\n数组: ";
    for (int val : arr1) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 防止窄化转换
    // int x{3.14};  // 编译错误：窄化转换
    int y = 3.14;    // 允许，但可能丢失精度
    std::cout << "\ny = " << y << std::endl;
}

// ==========================================
// 2. 容器初始化
// ==========================================

void demonstrate_container_initialization() {
    std::cout << "\n=== 2. 容器初始化 ===" << std::endl;

    // vector
    std::vector<int> vec1 = {1, 2, 3, 4, 5};
    std::vector<int> vec2{10, 20, 30, 40, 50};

    std::cout << "vec1: ";
    for (int val : vec1) std::cout << val << " ";
    std::cout << std::endl;

    std::cout << "vec2: ";
    for (int val : vec2) std::cout << val << " ";
    std::cout << std::endl;

    // map
    std::map<std::string, int> map1 = {
        {"Alice", 90},
        {"Bob", 85},
        {"Charlie", 95}
    };

    std::cout << "\nmap1:" << std::endl;
    for (const auto& pair : map1) {
        std::cout << "  " << pair.first << ": " << pair.second << std::endl;
    }

    // set
    std::set<int> set1 = {3, 1, 4, 1, 5, 9, 2, 6};

    std::cout << "\nset1: ";
    for (int val : set1) std::cout << val << " ";
    std::cout << std::endl;

    // 嵌套容器
    std::vector<std::vector<int>> matrix = {
        {1, 2, 3},
        {4, 5, 6},
        {7, 8, 9}
    };

    std::cout << "\n矩阵:" << std::endl;
    for (const auto& row : matrix) {
        for (int val : row) {
            std::cout << val << "\t";
        }
        std::cout << std::endl;
    }
}

// ==========================================
// 3. std::initializer_list
// ==========================================

class MyVector {
    std::vector<int> data_;

public:
    // 使用 initializer_list 构造
    MyVector(std::initializer_list<int> init) : data_(init) {
        std::cout << "  [MyVector] 使用 initializer_list 构造，大小: "
                  << data_.size() << std::endl;
    }

    // 添加元素
    void push_back(int val) {
        data_.push_back(val);
    }

    // 打印
    void print() const {
        std::cout << "[";
        for (size_t i = 0; i < data_.size(); ++i) {
            if (i > 0) std::cout << ", ";
            std::cout << data_[i];
        }
        std::cout << "]" << std::endl;
    }

    size_t size() const { return data_.size(); }
};

// 使用 initializer_list 的函数
void print_list(std::initializer_list<int> list) {
    std::cout << "(";
    for (auto it = list.begin(); it != list.end(); ++it) {
        if (it != list.begin()) std::cout << ", ";
        std::cout << *it;
    }
    std::cout << ")" << std::endl;
}

void demonstrate_initializer_list() {
    std::cout << "\n=== 3. std::initializer_list ===" << std::endl;

    // 使用 initializer_list 构造
    MyVector vec1 = {1, 2, 3, 4, 5};
    vec1.print();

    MyVector vec2{10, 20, 30};
    vec2.print();

    // 作为函数参数
    std::cout << "\n--- 作为函数参数 ---" << std::endl;
    print_list({1, 2, 3, 4, 5});
    print_list({10, 20, 30});

    // initializer_list 的特性
    std::cout << "\n--- initializer_list 特性 ---" << std::endl;
    std::initializer_list<int> list = {1, 2, 3, 4, 5};
    std::cout << "大小: " << list.size() << std::endl;
    std::cout << "首元素: " << *list.begin() << std::endl;
}

// ==========================================
// 4. 聚合初始化
// ==========================================

struct Point {
    int x;
    int y;
    int z;
};

struct Line {
    Point start;
    Point end;
};

class Aggregate {
public:
    int a;
    double b;
    std::string c;
};

void demonstrate_aggregate_initialization() {
    std::cout << "\n=== 4. 聚合初始化 ===" << std::endl;

    // 基本聚合初始化
    Point p1 = {1, 2, 3};
    Point p2{4, 5, 6};

    std::cout << "p1: (" << p1.x << ", " << p1.y << ", " << p1.z << ")" << std::endl;
    std::cout << "p2: (" << p2.x << ", " << p2.y << ", " << p2.z << ")" << std::endl;

    // 嵌套聚合初始化
    Line line = {
        {0, 0, 0},
        {1, 1, 1}
    };

    std::cout << "\nline.start: (" << line.start.x << ", " << line.start.y
              << ", " << line.start.z << ")" << std::endl;
    std::cout << "line.end: (" << line.end.x << ", " << line.end.y
              << ", " << line.end.z << ")" << std::endl;

    // 类聚合初始化
    Aggregate agg = {42, 3.14, "Hello"};
    std::cout << "\nagg: {" << agg.a << ", " << agg.b << ", " << agg.c << "}" << std::endl;

    // 部分初始化
    Point p3 = {1, 2};  // z 默认初始化为 0
    std::cout << "\np3: (" << p3.x << ", " << p3.y << ", " << p3.z << ")" << std::endl;
}

// ==========================================
// 5. 初始化列表与构造函数
// ==========================================

class Widget {
    int id_;
    std::string name_;
    std::vector<int> values_;

public:
    // 普通构造函数
    Widget(int id, const std::string& name)
        : id_(id), name_(name) {
        std::cout << "  [Widget] 普通构造: id=" << id_ << ", name=" << name_ << std::endl;
    }

    // 带 initializer_list 的构造函数
    Widget(int id, const std::string& name, std::initializer_list<int> values)
        : id_(id), name_(name), values_(values) {
        std::cout << "  [Widget] initializer_list 构造: id=" << id_
                  << ", name=" << name_ << ", values.size=" << values_.size() << std::endl;
    }

    void print() const {
        std::cout << "Widget{id=" << id_ << ", name=" << name_ << ", values=[";
        for (size_t i = 0; i < values_.size(); ++i) {
            if (i > 0) std::cout << ", ";
            std::cout << values_[i];
        }
        std::cout << "]}" << std::endl;
    }
};

void demonstrate_constructor_initialization() {
    std::cout << "\n=== 5. 初始化列表与构造函数 ===" << std::endl;

    // 普通构造
    Widget w1(1, "Widget1");
    w1.print();

    // initializer_list 构造
    Widget w2(2, "Widget2", {10, 20, 30});
    w2.print();

    // 使用花括号初始化
    Widget w3{3, "Widget3", {100, 200, 300, 400}};
    w3.print();
}

// ==========================================
// 6. 初始化列表的注意事项
// ==========================================

void demonstrate_caveats() {
    std::cout << "\n=== 6. 初始化列表的注意事项 ===" << std::endl;

    // 1. 空花括号调用默认构造函数
    std::cout << "--- 空花括号 ---" << std::endl;
    std::vector<int> vec1;      // 默认构造
    std::vector<int> vec2{};    // 也是默认构造
    std::vector<int> vec3 = {}; // 也是默认构造
    std::cout << "vec1.size() = " << vec1.size() << std::endl;
    std::cout << "vec2.size() = " << vec2.size() << std::endl;
    std::cout << "vec3.size() = " << vec3.size() << std::endl;

    // 2. initializer_list 优先级
    std::cout << "\n--- initializer_list 优先级 ---" << std::endl;
    std::vector<int> vec4(5, 10);    // 5 个 10
    std::vector<int> vec5{5, 10};    // 2 个元素：5 和 10
    std::cout << "vec4(5, 10): ";
    for (int val : vec4) std::cout << val << " ";
    std::cout << std::endl;
    std::cout << "vec5{5, 10}: ";
    for (int val : vec5) std::cout << val << " ";
    std::cout << std::endl;

    // 3. 窄化转换
    std::cout << "\n--- 窄化转换 ---" << std::endl;
    // int x{3.14};  // 编译错误：窄化转换
    int y = 3.14;    // 允许，但可能丢失精度
    std::cout << "y = " << y << std::endl;

    // 4. auto 与初始化列表
    std::cout << "\n--- auto 与初始化列表 ---" << std::endl;
    auto a = {1, 2, 3};  // std::initializer_list<int>
    auto b{42};           // int (C++14)
    // auto c = {1, 2.0}; // 编译错误：类型不一致
    std::cout << "a 的类型: " << typeid(a).name() << std::endl;
    std::cout << "b 的类型: " << typeid(b).name() << std::endl;
}

// ==========================================
// 7. 初始化列表的实际应用
// ==========================================

// 配置类
class Config {
    std::map<std::string, std::string> settings_;

public:
    Config(std::initializer_list<std::pair<const std::string, std::string>> init)
        : settings_(init) {}

    std::string get(const std::string& key) const {
        auto it = settings_.find(key);
        return it != settings_.end() ? it->second : "";
    }

    void print() const {
        for (const auto& pair : settings_) {
            std::cout << "  " << pair.first << " = " << pair.second << std::endl;
        }
    }
};

// 矩阵类
class Matrix {
    std::vector<std::vector<double>> data_;

public:
    Matrix(std::initializer_list<std::initializer_list<double>> init) {
        for (const auto& row : init) {
            data_.push_back(std::vector<double>(row));
        }
    }

    void print() const {
        for (const auto& row : data_) {
            for (double val : row) {
                std::cout << val << "\t";
            }
            std::cout << std::endl;
        }
    }
};

void demonstrate_practical() {
    std::cout << "\n=== 7. 初始化列表的实际应用 ===" << std::endl;

    // 配置类
    std::cout << "--- 配置类 ---" << std::endl;
    Config config = {
        {"host", "localhost"},
        {"port", "8080"},
        {"debug", "true"}
    };
    config.print();
    std::cout << "host = " << config.get("host") << std::endl;

    // 矩阵类
    std::cout << "\n--- 矩阵类 ---" << std::endl;
    Matrix matrix = {
        {1.0, 2.0, 3.0},
        {4.0, 5.0, 6.0},
        {7.0, 8.0, 9.0}
    };
    matrix.print();
}

// ==========================================
// 8. 初始化列表与算法
// ==========================================

void demonstrate_initializer_list_with_algorithms() {
    std::cout << "\n=== 8. 初始化列表与算法 ===" << std::endl;

    // 使用初始化列表创建临时容器
    std::cout << "--- 使用初始化列表 ---" << std::endl;
    std::vector<int> vec = {5, 2, 8, 1, 9, 3, 7, 4, 6};

    // 排序
    std::sort(vec.begin(), vec.end());
    std::cout << "排序后: ";
    for (int val : vec) std::cout << val << " ";
    std::cout << std::endl;

    // 查找
    auto it = std::find(vec.begin(), vec.end(), 5);
    if (it != vec.end()) {
        std::cout << "找到 5 在索引 " << std::distance(vec.begin(), it) << std::endl;
    }

    // 使用初始化列表作为参数
    std::cout << "\n--- 使用初始化列表作为参数 ---" << std::endl;
    auto minmax = std::minmax({3, 1, 4, 1, 5, 9, 2, 6});
    std::cout << "最小值: " << minmax.first << std::endl;
    std::cout << "最大值: " << minmax.second << std::endl;
}

// ==========================================
// 主函数
// ==========================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "C++11 初始化列表示例" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. 统一初始化语法
    demonstrate_uniform_initialization();

    // 2. 容器初始化
    demonstrate_container_initialization();

    // 3. std::initializer_list
    demonstrate_initializer_list();

    // 4. 聚合初始化
    demonstrate_aggregate_initialization();

    // 5. 初始化列表与构造函数
    demonstrate_constructor_initialization();

    // 6. 初始化列表的注意事项
    demonstrate_caveats();

    // 7. 初始化列表的实际应用
    demonstrate_practical();

    // 8. 初始化列表与算法
    demonstrate_initializer_list_with_algorithms();

    std::cout << "\n========================================" << std::endl;
    std::cout << "所有示例执行完毕！" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
