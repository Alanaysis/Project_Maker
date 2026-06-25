// =============================================================================
// void_t_demo.cpp - void_t 技巧演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o void_t_demo void_t_demo.cpp
// 运行: ./void_t_demo
// =============================================================================

#include <iostream>
#include <vector>
#include <list>
#include <map>
#include <string>
#include "sfinae/void_t.hpp"

// 用于测试的自定义类型
struct HasAll {
    using value_type = int;
    using iterator = int*;
    using size_type = std::size_t;
    std::size_t size() const { return 0; }
    int* begin() { return nullptr; }
    int* end() { return nullptr; }
    void push_back(const int&) {}
};

struct HasNothing {
    int data;
};

struct Printable {};
struct NotPrintable {};

std::ostream& operator<<(std::ostream& os, const Printable&) {
    return os << "Printable";
}

int main() {
    using namespace tmp::sfinae;

    std::cout << "=== void_t 技巧演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. 成员类型检测
    std::cout << "1. 成员类型检测:" << std::endl;
    std::cout << "  vector has value_type: " << has_value_type_v<std::vector<int>> << std::endl;
    std::cout << "  int has value_type: " << has_value_type_v<int> << std::endl;
    std::cout << "  vector has iterator: " << has_iterator_v<std::vector<int>> << std::endl;
    std::cout << "  int has iterator: " << has_iterator_v<int> << std::endl;
    std::cout << std::endl;

    // 2. 成员函数检测
    std::cout << "2. 成员函数检测:" << std::endl;
    std::cout << "  vector has begin: " << has_begin_v<std::vector<int>> << std::endl;
    std::cout << "  vector has end: " << has_end_v<std::vector<int>> << std::endl;
    std::cout << "  vector has push_back: " << has_push_back_v<std::vector<int>> << std::endl;
    std::cout << "  map has push_back: " << has_push_back_v<std::map<int,int>> << std::endl;
    std::cout << std::endl;

    // 3. 操作符检测
    std::cout << "3. 操作符检测:" << std::endl;
    std::cout << "  int has operator==: " << has_equal_v<int> << std::endl;
    std::cout << "  int has operator<: " << has_less_v<int> << std::endl;
    std::cout << "  string has operator<: " << has_less_v<std::string> << std::endl;
    std::cout << std::endl;

    // 4. 可打印性检测
    std::cout << "4. 可打印性检测:" << std::endl;
    std::cout << "  int is printable: " << is_printable_v<int> << std::endl;
    std::cout << "  string is printable: " << is_printable_v<std::string> << std::endl;
    std::cout << "  Printable is printable: " << is_printable_v<Printable> << std::endl;
    std::cout << "  NotPrintable is printable: " << is_printable_v<NotPrintable> << std::endl;
    std::cout << std::endl;

    // 5. 条件打印
    std::cout << "5. 条件打印:" << std::endl;
    print_if_possible(42);
    print_if_possible(std::string("hello"));
    print_if_possible(Printable{});
    print_if_possible(NotPrintable{});
    std::cout << std::endl;

    // 6. 容器检测
    std::cout << "6. 容器检测:" << std::endl;
    std::cout << "  vector<int> is container: " << is_container_v<std::vector<int>> << std::endl;
    std::cout << "  list<int> is container: " << is_container_v<std::list<int>> << std::endl;
    std::cout << "  map<int,int> is container: " << is_container_v<std::map<int,int>> << std::endl;
    std::cout << "  int is container: " << is_container_v<int> << std::endl;
    std::cout << "  HasAll is container: " << is_container_v<HasAll> << std::endl;
    std::cout << "  HasNothing is container: " << is_container_v<HasNothing> << std::endl;
    std::cout << std::endl;

    std::cout << "=== void_t 技巧演示完成 ===" << std::endl;
    return 0;
}
