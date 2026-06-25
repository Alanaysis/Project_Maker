/**
 * 08_range_for_init.cpp - C++20 范围 for 循环初始化语句
 *
 * C++20 允许在范围 for 循环中添加初始化语句。
 *
 * 核心要点：
 * 1. for (init; decl : expr) 语法
 * 2. 类似 if/switch 中的初始化语句
 * 3. 限制作用域，减少变量泄漏
 */

#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <algorithm>

// ============================================================
// 1. 基本用法
// ============================================================

void basic_init_for() {
    std::cout << "【1. 基本初始化语句】\n";

    // 传统写法：变量泄漏到外层作用域
    // std::vector<int> vec = {1, 2, 3};
    // auto it = vec.begin();
    // for (; it != vec.end(); ++it) { ... }

    // C++20 写法：迭代器限制在 for 作用域内
    std::vector<int> vec = {10, 20, 30, 40, 50};
    for (auto it = vec.begin(); auto& val : vec) {
        std::cout << "  iter distance=" << std::distance(vec.begin(), it)
                  << ", value=" << val << "\n";
        ++it;
    }
    // it 在这里不可见
    std::cout << "\n";
}

// ============================================================
// 2. 使用临时对象
// ============================================================

void temp_object_for() {
    std::cout << "【2. 使用临时对象】\n";

    // 使用初始化语句创建临时容器
    for (auto vec = std::vector{1, 2, 3, 4, 5}; auto val : vec) {
        std::cout << val << " ";
    }
    std::cout << "\n\n";
}

// ============================================================
// 3. 锁的作用域
// ============================================================

void scoped_lock_for() {
    std::cout << "【3. 初始化语句限制作用域】\n";

    // 模拟：使用初始化语句确保资源在循环内管理
    struct Resource {
        std::string name;
        Resource(const std::string& n) : name(n) {
            std::cout << "  获取资源: " << name << "\n";
        }
        ~Resource() {
            std::cout << "  释放资源: " << name << "\n";
        }
        std::vector<int> get_data() const { return {1, 2, 3}; }
    };

    for (Resource res("数据源"); auto val : res.get_data()) {
        std::cout << "  处理: " << val << "\n";
    }
    std::cout << "  （资源已自动释放）\n\n";
}

// ============================================================
// 4. 配合结构化绑定
// ============================================================

void structured_binding_for() {
    std::cout << "【4. 配合结构化绑定】\n";

    std::map<std::string, int> scores = {
        {"Alice", 95}, {"Bob", 87}, {"Charlie", 92}
    };

    // 初始化语句 + 结构化绑定
    for (auto max_it = scores.begin(); auto& [name, score] : scores) {
        std::cout << "  " << name << ": " << score;
        if (score > max_it->second) {
            std::cout << " (新最高)";
            max_it = scores.find(name);
        }
        std::cout << "\n";
    }
    std::cout << "\n";
}

// ============================================================
// 5. 多重初始化
// ============================================================

void multi_init_for() {
    std::cout << "【5. 多重初始化】\n";

    std::vector data = {3, 1, 4, 1, 5, 9, 2, 6};

    // 初始化多个变量
    for (size_t idx = 0, count = 0; auto val : data) {
        ++count;
        if (val > 3) {
            std::cout << "  #" << idx << " = " << val << " (count=" << count << ")\n";
        }
        ++idx;
    }
    std::cout << "\n";
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 范围 for 循环初始化示例 ===\n\n";

    basic_init_for();
    temp_object_for();
    scoped_lock_for();
    structured_binding_for();
    multi_init_for();

    std::cout << "=== 范围 for 初始化示例完成 ===\n";
    return 0;
}
