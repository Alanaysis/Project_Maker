/**
 * C++11 范围 for 循环示例
 *
 * 学习目标：
 * 1. 掌握范围 for 循环的基本语法
 * 2. 学会使用引用和值遍历
 * 3. 理解自定义类型如何支持范围 for
 * 4. 了解范围 for 的实现原理
 */

#include <iostream>
#include <vector>
#include <list>
#include <map>
#include <set>
#include <string>
#include <algorithm>
#include <numeric>

// ==========================================
// 1. 基本范围 for 循环
// ==========================================

void demonstrate_basic_range_for() {
    std::cout << "\n=== 1. 基本范围 for 循环 ===" << std::endl;

    // 遍历 vector
    std::vector<int> vec = {1, 2, 3, 4, 5};
    std::cout << "--- 遍历 vector ---" << std::endl;
    for (int elem : vec) {
        std::cout << elem << " ";
    }
    std::cout << std::endl;

    // 使用 auto
    std::cout << "\n--- 使用 auto ---" << std::endl;
    for (auto elem : vec) {
        std::cout << elem << " ";
    }
    std::cout << std::endl;

    // 遍历 list
    std::list<std::string> list = {"Hello", "World", "C++"};
    std::cout << "\n--- 遍历 list ---" << std::endl;
    for (const auto& str : list) {
        std::cout << str << " ";
    }
    std::cout << std::endl;

    // 遍历数组
    int arr[] = {10, 20, 30, 40, 50};
    std::cout << "\n--- 遍历数组 ---" << std::endl;
    for (int val : arr) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 遍历初始化列表
    std::cout << "\n--- 遍历初始化列表 ---" << std::endl;
    for (int val : {100, 200, 300}) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

// ==========================================
// 2. 值遍历 vs 引用遍历
// ==========================================

void demonstrate_value_vs_reference() {
    std::cout << "\n=== 2. 值遍历 vs 引用遍历 ===" << std::endl;

    std::vector<int> vec = {1, 2, 3, 4, 5};

    // 值遍历（拷贝）
    std::cout << "--- 值遍历（不会修改原数据）---" << std::endl;
    for (int elem : vec) {
        elem *= 2;  // 修改的是副本
    }
    std::cout << "原数据: ";
    for (int elem : vec) {
        std::cout << elem << " ";
    }
    std::cout << std::endl;

    // 引用遍历（可以修改原数据）
    std::cout << "\n--- 引用遍历（可以修改原数据）---" << std::endl;
    for (int& elem : vec) {
        elem *= 2;  // 修改原数据
    }
    std::cout << "修改后: ";
    for (int elem : vec) {
        std::cout << elem << " ";
    }
    std::cout << std::endl;

    // const 引用遍历（只读，避免拷贝）
    std::cout << "\n--- const 引用遍历（只读）---" << std::endl;
    for (const int& elem : vec) {
        std::cout << elem << " ";
    }
    std::cout << std::endl;
}

// ==========================================
// 3. 遍历关联容器
// ==========================================

void demonstrate_associative_containers() {
    std::cout << "\n=== 3. 遍历关联容器 ===" << std::endl;

    // 遍历 map
    std::map<std::string, int> map = {
        {"Alice", 90}, {"Bob", 85}, {"Charlie", 95}
    };

    std::cout << "--- 遍历 map ---" << std::endl;
    for (const auto& pair : map) {
        std::cout << pair.first << ": " << pair.second << std::endl;
    }

    // 遍历 set
    std::set<int> set = {3, 1, 4, 1, 5, 9, 2, 6};
    std::cout << "\n--- 遍历 set ---" << std::endl;
    for (int val : set) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 遍历 multimap
    std::multimap<std::string, int> multimap = {
        {"Alice", 90}, {"Alice", 95}, {"Bob", 85}
    };
    std::cout << "\n--- 遍历 multimap ---" << std::endl;
    for (const auto& pair : multimap) {
        std::cout << pair.first << ": " << pair.second << std::endl;
    }
}

// ==========================================
// 4. 自定义类型支持范围 for
// ==========================================

// 简单的自定义容器
class MyVector {
    std::vector<int> data_;

public:
    MyVector(std::initializer_list<int> init) : data_(init) {}

    // 必须提供 begin() 和 end() 方法
    auto begin() { return data_.begin(); }
    auto end() { return data_.end(); }

    // const 版本
    auto begin() const { return data_.begin(); }
    auto end() const { return data_.end(); }
};

// 自定义迭代器
class Range {
    int start_;
    int end_;

public:
    class Iterator {
        int current_;

    public:
        Iterator(int current) : current_(current) {}

        int operator*() const { return current_; }
        Iterator& operator++() {
            ++current_;
            return *this;
        }
        bool operator!=(const Iterator& other) const {
            return current_ != other.current_;
        }
    };

    Range(int start, int end) : start_(start), end_(end) {}

    Iterator begin() const { return Iterator(start_); }
    Iterator end() const { return Iterator(end_); }
};

void demonstrate_custom_container() {
    std::cout << "\n=== 4. 自定义类型支持范围 for ===" << std::endl;

    // 使用自定义容器
    MyVector vec = {1, 2, 3, 4, 5};
    std::cout << "--- 自定义容器 ---" << std::endl;
    for (int val : vec) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 使用自定义迭代器
    std::cout << "\n--- 自定义迭代器 ---" << std::endl;
    for (int i : Range(0, 10)) {
        std::cout << i << " ";
    }
    std::cout << std::endl;

    // 范围表达式
    std::cout << "\n--- 范围表达式 ---" << std::endl;
    for (int i : Range(5, 15)) {
        std::cout << i << " ";
    }
    std::cout << std::endl;
}

// ==========================================
// 5. 范围 for 与算法结合
// ==========================================

void demonstrate_range_for_with_algorithms() {
    std::cout << "\n=== 5. 范围 for 与算法结合 ===" << std::endl;

    std::vector<int> vec = {5, 2, 8, 1, 9, 3, 7, 4, 6};

    // 使用范围 for 进行转换
    std::cout << "--- 转换 ---" << std::endl;
    std::vector<int> squared;
    for (int val : vec) {
        squared.push_back(val * val);
    }
    std::cout << "平方: ";
    for (int val : squared) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 使用范围 for 进行过滤
    std::cout << "\n--- 过滤 ---" << std::endl;
    std::vector<int> evens;
    for (int val : vec) {
        if (val % 2 == 0) {
            evens.push_back(val);
        }
    }
    std::cout << "偶数: ";
    for (int val : evens) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 使用范围 for 进行累加
    std::cout << "\n--- 累加 ---" << std::endl;
    int sum = 0;
    for (int val : vec) {
        sum += val;
    }
    std::cout << "总和: " << sum << std::endl;

    // 使用范围 for 进行查找
    std::cout << "\n--- 查找 ---" << std::endl;
    int target = 8;
    bool found = false;
    for (int val : vec) {
        if (val == target) {
            found = true;
            break;
        }
    }
    std::cout << "找到 " << target << ": " << (found ? "是" : "否") << std::endl;
}

// ==========================================
// 6. 范围 for 的性能考虑
// ==========================================

void demonstrate_performance() {
    std::cout << "\n=== 6. 范围 for 的性能考虑 ===" << std::endl;

    std::vector<std::string> strings = {"Hello", "World", "C++", "Modern"};

    // 不好的做法：每次迭代都拷贝
    std::cout << "--- 不好的做法（拷贝）---" << std::endl;
    for (std::string s : strings) {
        std::cout << s << " ";
    }
    std::cout << std::endl;

    // 好的做法：使用 const 引用
    std::cout << "\n--- 好的做法（const 引用）---" << std::endl;
    for (const std::string& s : strings) {
        std::cout << s << " ";
    }
    std::cout << std::endl;

    // 最佳做法：使用 auto&
    std::cout << "\n--- 最佳做法（auto&）---" << std::endl;
    for (const auto& s : strings) {
        std::cout << s << " ";
    }
    std::cout << std::endl;

    // 需要修改时使用 auto&
    std::cout << "\n--- 需要修改时使用 auto& ---" << std::endl;
    for (auto& s : strings) {
        s += "!";
    }
    for (const auto& s : strings) {
        std::cout << s << " ";
    }
    std::cout << std::endl;
}

// ==========================================
// 7. 范围 for 的实现原理
// ==========================================

// 编译器将范围 for 转换为普通 for 循环
// for (auto& elem : container) {
//     // body
// }
//
// 转换为：
// {
//     auto&& __range = container;
//     auto __begin = __range.begin();
//     auto __end = __range.end();
//     for (; __begin != __end; ++__begin) {
//         auto& elem = *__begin;
//         // body
//     }
// }

void demonstrate_implementation() {
    std::cout << "\n=== 7. 范围 for 的实现原理 ===" << std::endl;

    std::vector<int> vec = {1, 2, 3, 4, 5};

    // 范围 for
    std::cout << "--- 范围 for ---" << std::endl;
    for (int val : vec) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 等价的传统 for 循环
    std::cout << "\n--- 等价的传统 for 循环 ---" << std::endl;
    {
        auto&& __range = vec;
        auto __begin = __range.begin();
        auto __end = __range.end();
        for (; __begin != __end; ++__begin) {
            int val = *__begin;
            std::cout << val << " ";
        }
    }
    std::cout << std::endl;
}

// ==========================================
// 8. 范围 for 的实际应用
// ==========================================

// 统计单词频率
std::map<std::string, int> count_words(const std::string& text) {
    std::map<std::string, int> freq;
    std::string word;
    for (char c : text) {
        if (c == ' ' || c == '\n' || c == '\t') {
            if (!word.empty()) {
                freq[word]++;
                word.clear();
            }
        } else {
            word += c;
        }
    }
    if (!word.empty()) {
        freq[word]++;
    }
    return freq;
}

// 打印矩阵
void print_matrix(const std::vector<std::vector<int>>& matrix) {
    for (const auto& row : matrix) {
        for (int val : row) {
            std::cout << val << "\t";
        }
        std::cout << std::endl;
    }
}

void demonstrate_practical() {
    std::cout << "\n=== 8. 范围 for 的实际应用 ===" << std::endl;

    // 统计单词频率
    std::cout << "--- 统计单词频率 ---" << std::endl;
    std::string text = "hello world hello cpp world hello";
    auto freq = count_words(text);
    for (const auto& pair : freq) {
        std::cout << pair.first << ": " << pair.second << std::endl;
    }

    // 打印矩阵
    std::cout << "\n--- 打印矩阵 ---" << std::endl;
    std::vector<std::vector<int>> matrix = {
        {1, 2, 3},
        {4, 5, 6},
        {7, 8, 9}
    };
    print_matrix(matrix);
}

// ==========================================
// 主函数
// ==========================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "C++11 范围 for 循环示例" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. 基本范围 for 循环
    demonstrate_basic_range_for();

    // 2. 值遍历 vs 引用遍历
    demonstrate_value_vs_reference();

    // 3. 遍历关联容器
    demonstrate_associative_containers();

    // 4. 自定义类型支持范围 for
    demonstrate_custom_container();

    // 5. 范围 for 与算法结合
    demonstrate_range_for_with_algorithms();

    // 6. 范围 for 的性能考虑
    demonstrate_performance();

    // 7. 范围 for 的实现原理
    demonstrate_implementation();

    // 8. 范围 for 的实际应用
    demonstrate_practical();

    std::cout << "\n========================================" << std::endl;
    std::cout << "所有示例执行完毕！" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
