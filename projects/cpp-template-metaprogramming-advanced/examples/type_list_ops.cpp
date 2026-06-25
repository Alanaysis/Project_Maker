/**
 * @file type_list_ops.cpp
 * @brief 类型列表操作示例
 */

#include <iostream>
#include <string>
#include <type_traits>
#include "../include/type_computation/type_list.hpp"
#include "../include/type_computation/type_counting.hpp"
#include "../include/type_computation/type_conversion.hpp"

// 辅助函数：打印类型名
template <typename T>
const char* type_name() { return "unknown"; }

template <> const char* type_name<int>() { return "int"; }
template <> const char* type_name<double>() { return "double"; }
template <> const char* type_name<char>() { return "char"; }
template <> const char* type_name<float>() { return "float"; }
template <> const char* type_name<std::string>() { return "string"; }
template <> const char* type_name<bool>() { return "bool"; }

int main() {
    using namespace tmp;

    std::cout << "=== Type List Operations ===" << std::endl;
    std::cout << std::endl;

    using my_list = type_list<int, double, char, float>;

    // 1. 基本操作
    std::cout << "--- 1. Basic Operations ---" << std::endl;
    std::cout << "List size: " << my_list::size << std::endl;
    std::cout << "Is empty: " << my_list::empty << std::endl;
    std::cout << "Front: " << type_name<front<my_list>>() << std::endl;
    std::cout << "Back: " << type_name<back<my_list>>() << std::endl;
    std::cout << "At<1>: " << type_name<at<my_list, 1>>() << std::endl;
    std::cout << "At<2>: " << type_name<at<my_list, 2>>() << std::endl;
    std::cout << std::endl;

    // 2. push_front / push_back
    std::cout << "--- 2. Push Front/Back ---" << std::endl;
    using pushed_front = push_front<my_list, bool>;
    using pushed_back = push_back<my_list, std::string>;
    std::cout << "Push front bool: size = " << pushed_front::size
              << ", front = " << type_name<front<pushed_front>>() << std::endl;
    std::cout << "Push back string: size = " << pushed_back::size
              << ", back = " << type_name<back<pushed_back>>() << std::endl;
    std::cout << std::endl;

    // 3. pop_front / pop_back
    std::cout << "--- 3. Pop Front/Back ---" << std::endl;
    using popped_front = pop_front<my_list>;
    using popped_back = pop_back<my_list>;
    std::cout << "Pop front: size = " << popped_front::size
              << ", front = " << type_name<front<popped_front>>() << std::endl;
    std::cout << "Pop back: size = " << popped_back::size
              << ", back = " << type_name<back<popped_back>>() << std::endl;
    std::cout << std::endl;

    // 4. contains / index_of
    std::cout << "--- 4. Contains / Index Of ---" << std::endl;
    std::cout << "Contains int: " << contains<my_list, int> << std::endl;
    std::cout << "Contains bool: " << contains<my_list, bool> << std::endl;
    std::cout << "Index of double: " << index_of<my_list, double> << std::endl;
    std::cout << "Index of char: " << index_of<my_list, char> << std::endl;
    std::cout << std::endl;

    // 5. reverse
    std::cout << "--- 5. Reverse ---" << std::endl;
    using reversed = reverse<my_list>;
    std::cout << "Original: int, double, char, float" << std::endl;
    std::cout << "Reversed: " << type_name<front<reversed>>() << ", "
              << type_name<at<reversed, 1>>() << ", "
              << type_name<at<reversed, 2>>() << ", "
              << type_name<at<reversed, 3>>() << std::endl;
    std::cout << std::endl;

    // 6. concat
    std::cout << "--- 6. Concat ---" << std::endl;
    using list1 = type_list<int, double>;
    using list2 = type_list<char, float>;
    using combined = concat<list1, list2>;
    std::cout << "List1 + List2: size = " << combined::size << std::endl;
    std::cout << "Elements: " << type_name<at<combined, 0>>() << ", "
              << type_name<at<combined, 1>>() << ", "
              << type_name<at<combined, 2>>() << ", "
              << type_name<at<combined, 3>>() << std::endl;
    std::cout << std::endl;

    // 7. transform
    std::cout << "--- 7. Transform ---" << std::endl;
    // 使用 std::add_pointer 给每个类型添加指针
    using pointers = transform<my_list, std::add_pointer>;
    std::cout << "Transformed (add pointer): size = " << pointers::size << std::endl;
    std::cout << "First is pointer: "
              << std::is_pointer_v<front<pointers>> << std::endl;
    std::cout << std::endl;

    // 8. filter
    std::cout << "--- 8. Filter ---" << std::endl;
    // 过滤出算术类型
    using arithmetic_only = filter<my_list, std::is_arithmetic>;
    std::cout << "Arithmetic types only: size = " << arithmetic_only::size << std::endl;
    std::cout << std::endl;

    // 9. fold
    std::cout << "--- 9. Fold ---" << std::endl;
    // 使用 plus_sizeof 计算总大小
    using mixed_list = type_list<int, double, char>;
    std::cout << "Total sizeof(int, double, char) = " << total_sizeof<mixed_list> << std::endl;
    std::cout << std::endl;

    // 10. 类型计数
    std::cout << "--- 10. Type Counting ---" << std::endl;
    using dup_list = type_list<int, double, int, char, int>;
    std::cout << "Count<int> in [int,double,int,char,int]: " << count<dup_list, int> << std::endl;
    std::cout << "Count<double>: " << count<dup_list, double> << std::endl;
    std::cout << "Unique: " << unique<dup_list>::size << " types" << std::endl;
    std::cout << "Has duplicates: " << has_duplicates<dup_list> << std::endl;
    std::cout << std::endl;

    // 11. 类型集合操作
    std::cout << "--- 11. Type Set Operations ---" << std::endl;
    using set_a = type_list<int, double, char>;
    using set_b = type_list<double, char, float>;

    using union_set = type_union<set_a, set_b>;
    using inter_set = type_intersection<set_a, set_b>;
    using diff_set = type_difference<set_a, set_b>;

    std::cout << "Union size: " << union_set::size << std::endl;
    std::cout << "Intersection size: " << inter_set::size << std::endl;
    std::cout << "Difference size: " << diff_set::size << std::endl;

    return 0;
}
