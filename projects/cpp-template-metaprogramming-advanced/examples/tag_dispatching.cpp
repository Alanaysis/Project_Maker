/**
 * @file tag_dispatching.cpp
 * @brief 标签分发示例
 *
 * 通过标签选择不同的函数实现，避免运行时分支。
 */

#include <iostream>
#include <vector>
#include <list>
#include <iterator>
#include "../include/advanced_templates/tag_dispatching.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== Tag Dispatching Demo ===" << std::endl;
    std::cout << std::endl;

    // 1. 迭代器标签分发 - advance
    std::cout << "--- 1. Iterator Tag Dispatching (advance) ---" << std::endl;

    std::vector<int> vec = {10, 20, 30, 40, 50};
    auto vec_it = vec.begin();
    std::cout << "Before advance: " << *vec_it << std::endl;
    advance_tagged(vec_it, 2);
    std::cout << "After advance(2): " << *vec_it << std::endl;

    std::list<int> lst = {100, 200, 300, 400};
    auto lst_it = lst.begin();
    std::cout << "Before advance: " << *lst_it << std::endl;
    advance_tagged(lst_it, 2);
    std::cout << "After advance(2): " << *lst_it << std::endl;
    std::cout << std::endl;

    // 2. 迭代器标签分发 - distance
    std::cout << "--- 2. Iterator Tag Dispatching (distance) ---" << std::endl;

    auto dist1 = distance_tagged(vec.begin(), vec.end());
    std::cout << "Vector distance: " << dist1 << std::endl;

    auto dist2 = distance_tagged(lst.begin(), lst.end());
    std::cout << "List distance: " << dist2 << std::endl;
    std::cout << std::endl;

    // 3. 数值类型分发
    std::cout << "--- 3. Numeric Type Tag Dispatching ---" << std::endl;

    int i = 42;
    double d = 3.14;
    std::string s = "hello";

    std::cout << "int is integral: "
              << std::is_same_v<numeric_tag_t<int>, integral_tag> << std::endl;
    std::cout << "double is floating_point: "
              << std::is_same_v<numeric_tag_t<double>, floating_point_tag> << std::endl;
    std::cout << "string is other: "
              << std::is_same_v<numeric_tag_t<std::string>, other_tag> << std::endl;
    std::cout << std::endl;

    // 4. 序列化标签分发
    std::cout << "--- 4. Serialization Tag Dispatching ---" << std::endl;

    int val = 42;
    std::cout << "Serialized int: ";
    for (char c : serialize_tagged(val)) {
        std::cout << std::hex << (int)(unsigned char)c << " ";
    }
    std::cout << std::endl;

    double fval = 3.14;
    std::cout << "Serialized double: " << serialize_tagged(fval) << std::endl;
    std::cout << std::endl;

    // 5. if constexpr 替代标签分发
    std::cout << "--- 5. if constexpr Alternative ---" << std::endl;

    auto d1 = distance_if_constexpr(vec.begin(), vec.end());
    std::cout << "Vector distance (if constexpr): " << d1 << std::endl;

    auto d2 = distance_if_constexpr(lst.begin(), lst.end());
    std::cout << "List distance (if constexpr): " << d2 << std::endl;
    std::cout << std::endl;

    // 6. 编译期条件标签
    std::cout << "--- 6. Compile-time Condition Tags ---" << std::endl;

    using tag1 = condition_tag<true>;
    using tag2 = condition_tag<false>;
    std::cout << "condition_tag<true> is true_type: "
              << std::is_same_v<tag1, std::true_type> << std::endl;
    std::cout << "condition_tag<false> is false_type: "
              << std::is_same_v<tag2, std::false_type> << std::endl;
    std::cout << std::endl;

    std::cout << "Tag dispatching eliminates runtime branches by" << std::endl;
    std::cout << "selecting the optimal implementation at compile time." << std::endl;

    return 0;
}
