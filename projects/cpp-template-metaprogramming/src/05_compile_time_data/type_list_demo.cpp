// =============================================================================
// type_list_demo.cpp - 编译期类型列表演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o type_list_demo type_list_demo.cpp
// 运行: ./type_list_demo
// =============================================================================

#include <iostream>
#include <string>
#include <type_traits>
#include "compile_time/type_list.hpp"

int main() {
    std::cout << "=== 编译期类型列表演示 ===" << std::endl;
    std::cout << std::endl;

    // 定义类型列表
    using MyList = tmp::TypeList<int, double, std::string, char>;

    // 1. 基本操作
    std::cout << "1. 基本操作:" << std::endl;
    std::cout << "  Size: " << tmp::Size_v<MyList> << std::endl;
    std::cout << "  IsEmpty: " << tmp::IsEmpty_v<MyList> << std::endl;
    std::cout << "  IsEmpty (empty): " << tmp::IsEmpty_v<tmp::TypeList<>> << std::endl;
    std::cout << std::endl;

    // 2. 访问操作
    std::cout << "2. 访问操作:" << std::endl;
    std::cout << "  Front is int: "
              << std::is_same_v<tmp::Front_t<MyList>, int> << std::endl;
    std::cout << "  Get<0> is int: "
              << std::is_same_v<tmp::Get_t<0, MyList>, int> << std::endl;
    std::cout << "  Get<1> is double: "
              << std::is_same_v<tmp::Get_t<1, MyList>, double> << std::endl;
    std::cout << "  Get<2> is string: "
              << std::is_same_v<tmp::Get_t<2, MyList>, std::string> << std::endl;
    std::cout << std::endl;

    // 3. 查找操作
    std::cout << "3. 查找操作:" << std::endl;
    std::cout << "  IndexOf<int>: " << tmp::IndexOf_v<int, MyList> << std::endl;
    std::cout << "  IndexOf<double>: " << tmp::IndexOf_v<double, MyList> << std::endl;
    std::cout << "  IndexOf<string>: " << tmp::IndexOf_v<std::string, MyList> << std::endl;
    std::cout << "  Contains<int>: " << tmp::Contains_v<int, MyList> << std::endl;
    std::cout << "  Contains<float>: " << tmp::Contains_v<float, MyList> << std::endl;
    std::cout << std::endl;

    // 4. 修改操作
    std::cout << "4. 修改操作:" << std::endl;
    using PushedFront = tmp::PushFront_t<MyList, float>;
    std::cout << "  PushFront<float> size: " << tmp::Size_v<PushedFront> << std::endl;
    std::cout << "  PushFront<float> front is float: "
              << std::is_same_v<tmp::Front_t<PushedFront>, float> << std::endl;

    using PushedBack = tmp::PushBack_t<MyList, float>;
    std::cout << "  PushBack<float> size: " << tmp::Size_v<PushedBack> << std::endl;

    using PoppedFront = tmp::PopFront_t<MyList>;
    std::cout << "  PopFront size: " << tmp::Size_v<PoppedFront> << std::endl;
    std::cout << "  PopFront front is double: "
              << std::is_same_v<tmp::Front_t<PoppedFront>, double> << std::endl;
    std::cout << std::endl;

    // 5. 连接操作
    std::cout << "5. 连接操作:" << std::endl;
    using List1 = tmp::TypeList<int, double>;
    using List2 = tmp::TypeList<char, float>;
    using Concatenated = tmp::Concat_t<List1, List2>;
    std::cout << "  Concat size: " << tmp::Size_v<Concatenated> << std::endl;
    std::cout << "  Concat<0> is int: "
              << std::is_same_v<tmp::Get_t<0, Concatenated>, int> << std::endl;
    std::cout << std::endl;

    // 6. 反转操作
    std::cout << "6. 反转操作:" << std::endl;
    using Reversed = tmp::Reverse_t<MyList>;
    std::cout << "  Reversed<0> is char: "
              << std::is_same_v<tmp::Get_t<0, Reversed>, char> << std::endl;
    std::cout << "  Reversed<3> is int: "
              << std::is_same_v<tmp::Get_t<3, Reversed>, int> << std::endl;
    std::cout << std::endl;

    // 7. 过滤操作
    std::cout << "7. 过滤操作:" << std::endl;
    // 过滤出算术类型
    using ArithmeticOnly = tmp::Filter_t<std::is_arithmetic, MyList>;
    std::cout << "  Arithmetic types count: " << tmp::Size_v<ArithmeticOnly> << std::endl;
    std::cout << "  First is int: "
              << std::is_same_v<tmp::Front_t<ArithmeticOnly>, int> << std::endl;
    std::cout << std::endl;

    // 8. 去重操作
    std::cout << "8. 去重操作:" << std::endl;
    using DupList = tmp::TypeList<int, double, int, char, double, int>;
    using UniqueList = tmp::Unique_t<DupList>;
    std::cout << "  Original size: " << tmp::Size_v<DupList> << std::endl;
    std::cout << "  Unique size: " << tmp::Size_v<UniqueList> << std::endl;
    std::cout << std::endl;

    // 9. 变换操作
    std::cout << "9. 变换操作:" << std::endl;
    // 添加 const 到所有类型
    using ConstList = tmp::Transform_t<std::add_const, MyList>;
    std::cout << "  Transform<add_const><0> is const int: "
              << std::is_same_v<tmp::Get_t<0, ConstList>, const int> << std::endl;
    std::cout << "  Transform<add_const><1> is const double: "
              << std::is_same_v<tmp::Get_t<1, ConstList>, const double> << std::endl;
    std::cout << std::endl;

    // 10. 折叠操作
    std::cout << "10. 折叠操作:" << std::endl;
    // 计算所有类型的大小之和
    static constexpr std::size_t total_size =
        sizeof(int) + sizeof(double) + sizeof(std::string) + sizeof(char);
    std::cout << "  Total size of all types: " << total_size << " bytes" << std::endl;
    std::cout << std::endl;

    std::cout << "=== 编译期类型列表演示完成 ===" << std::endl;
    return 0;
}
