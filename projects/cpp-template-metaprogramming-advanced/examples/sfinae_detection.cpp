/**
 * @file sfinae_detection.cpp
 * @brief SFINAE 成员检测示例
 */

#include <iostream>
#include <string>
#include <vector>
#include <list>
#include <map>
#include "../include/sfinae/member_detection.hpp"

struct HasToString {
    std::string to_string() const { return "HasToString"; }
};

struct NoToString {};

struct HasSize {
    std::size_t size() const { return 42; }
};

int main() {
    using namespace tmp;

    std::cout << "=== SFINAE Member Detection ===" << std::endl;
    std::cout << std::endl;

    // 1. 成员函数检测
    std::cout << "--- 1. Member Function Detection ---" << std::endl;
    std::cout << "vector has size: " << has_size_v<std::vector<int>> << std::endl;
    std::cout << "int has size: " << has_size_v<int> << std::endl;
    std::cout << "string has size: " << has_size_v<std::string> << std::endl;
    std::cout << std::endl;

    std::cout << "vector has begin/end: " << has_begin_end_v<std::vector<int>> << std::endl;
    std::cout << "int has begin/end: " << has_begin_end_v<int> << std::endl;
    std::cout << std::endl;

    std::cout << "vector has push_back: " << has_push_back_v<std::vector<int>, int> << std::endl;
    std::cout << "map has push_back: " << has_push_back_v<std::map<int,int>, int> << std::endl;
    std::cout << std::endl;

    std::cout << "vector has reserve: " << has_reserve_v<std::vector<int>> << std::endl;
    std::cout << "list has reserve: " << has_reserve_v<std::list<int>> << std::endl;
    std::cout << std::endl;

    // 2. to_string 检测
    std::cout << "--- 2. to_string Detection ---" << std::endl;
    std::cout << "HasToString has to_string: " << has_to_string_v<HasToString> << std::endl;
    std::cout << "NoToString has to_string: " << has_to_string_v<NoToString> << std::endl;
    std::cout << std::endl;

    // 3. 成员类型检测
    std::cout << "--- 3. Member Type Detection ---" << std::endl;
    std::cout << "vector has value_type: " << has_value_type_v<std::vector<int>> << std::endl;
    std::cout << "int has value_type: " << has_value_type_v<int> << std::endl;
    std::cout << std::endl;

    std::cout << "vector has iterator: " << has_iterator_v<std::vector<int>> << std::endl;
    std::cout << "int has iterator: " << has_iterator_v<int> << std::endl;
    std::cout << std::endl;

    // 4. 运算符检测
    std::cout << "--- 4. Operator Detection ---" << std::endl;
    std::cout << "int has operator==: " << has_equal_operator_v<int> << std::endl;
    std::cout << "int has operator<: " << has_less_operator_v<int> << std::endl;
    std::cout << "int has operator<<: " << has_stream_operator_v<int> << std::endl;
    std::cout << "string has operator<<: " << has_stream_operator_v<std::string> << std::endl;
    std::cout << std::endl;

    // 5. 复杂表达式检测
    std::cout << "--- 5. Complex Expression Detection ---" << std::endl;
    std::cout << "vector is iterable: " << is_iterable_v<std::vector<int>> << std::endl;
    std::cout << "int is iterable: " << is_iterable_v<int> << std::endl;
    std::cout << std::endl;

    std::cout << "int is hashable: " << is_hashable_v<int> << std::endl;
    std::cout << "string is hashable: " << is_hashable_v<std::string> << std::endl;
    std::cout << std::endl;

    // 6. 组合特征
    std::cout << "--- 6. Combined Traits ---" << std::endl;
    std::cout << "vector is container_like: " << is_container_like_v<std::vector<int>> << std::endl;
    std::cout << "int is container_like: " << is_container_like_v<int> << std::endl;
    std::cout << "vector is dynamic_container: " << is_dynamic_container_v<std::vector<int>> << std::endl;
    std::cout << std::endl;

    // 7. 编译期条件分发
    std::cout << "--- 7. Compile-time Conditional Dispatch ---" << std::endl;
    auto print_size = [](auto&& container) {
        if constexpr (has_size_v<std::decay_t<decltype(container)>>) {
            std::cout << "Size: " << container.size() << std::endl;
        } else {
            std::cout << "No size() method" << std::endl;
        }
    };

    std::vector<int> v = {1, 2, 3};
    int x = 42;
    print_size(v);
    print_size(x);

    return 0;
}
