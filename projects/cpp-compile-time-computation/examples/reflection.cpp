// reflection.cpp - 编译期反射示例
//
// 本文件展示编译期反射的用法，包括：
//   1. 类型信息查询
//   2. 类型特征检查
//   3. 类型列表操作
//   4. 类型名称获取
//
// 编译命令：
//   g++ -std=c++20 -I include examples/reflection.cpp -o reflection

#include <iostream>
#include <type_traits>
#include "compile_time/reflection.hpp"

using namespace compile_time::reflection;

// ============================================================================
// 第一部分：类型信息查询
// ============================================================================

// 查询基本类型信息
constexpr auto int_info = get_type_info<int>();
constexpr auto double_info = get_type_info<double>();
constexpr auto bool_info = get_type_info<bool>();

// ============================================================================
// 第二部分：类型特征检查
// ============================================================================

// 检查类型特征
constexpr bool is_int_integral = int_info.is_integral;
constexpr bool is_double_floating = double_info.is_floating_point;
constexpr bool is_bool_arithmetic = bool_info.is_arithmetic;

// 检查大小和对齐
constexpr std::size_t int_size = int_info.size;
constexpr std::size_t double_size = double_info.size;
constexpr std::size_t int_alignment = int_info.alignment;

// ============================================================================
// 第三部分：类型名称获取
// ============================================================================

// 获取类型名称
constexpr const char* int_name = simple_type_name<int>();
constexpr const char* double_name = simple_type_name<double>();
constexpr const char* bool_name = simple_type_name<bool>();
constexpr const char* float_name = simple_type_name<float>();
constexpr const char* char_name = simple_type_name<char>();

// ============================================================================
// 第四部分：类型列表操作
// ============================================================================

// 创建类型列表
using MyTypes = type_list<int, double, bool, char>;

// 查询类型列表大小
constexpr std::size_t type_list_size = MyTypes::size;

// 检查类型是否在列表中
constexpr bool has_int = contains<MyTypes, int>::value;
constexpr bool has_float = contains<MyTypes, float>::value;

// 获取类型在列表中的索引
constexpr std::size_t int_index = index_of<MyTypes, int>::value;
constexpr std::size_t double_index = index_of<MyTypes, double>::value;

// ============================================================================
// 第五部分：类型比较和哈希
// ============================================================================

// 类型哈希
constexpr std::size_t int_type_hash = type_hash<int>();
constexpr std::size_t double_type_hash = type_hash<double>();

// ============================================================================
// 第六部分：自定义类型示例
// ============================================================================

// 自定义结构体
struct Point {
    int x;
    int y;
};

// 查询自定义类型信息
constexpr auto point_info = get_type_info<Point>();
constexpr bool is_point_class = point_info.is_class;
constexpr std::size_t point_size = point_info.size;

// 获取自定义类型名称
constexpr const char* point_name = simple_type_name<Point>();

// ============================================================================
// 第七部分：编译期断言验证
// ============================================================================

// 类型信息
static_assert(is_int_integral == true);
static_assert(is_double_floating == true);
static_assert(is_bool_arithmetic == true);

// 大小和对齐
static_assert(int_size == sizeof(int));
static_assert(double_size == sizeof(double));
static_assert(int_alignment == alignof(int));

// 类型名称
static_assert(int_name[0] == 'i');
static_assert(double_name[0] == 'd');
static_assert(bool_name[0] == 'b');

// 类型列表
static_assert(type_list_size == 4);
static_assert(has_int == true);
static_assert(has_float == false);
static_assert(int_index == 0);
static_assert(double_index == 1);

// 自定义类型
static_assert(is_point_class == true);
static_assert(point_size == sizeof(Point));
static_assert(point_name[0] == 'u');  // "user_type"

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期反射示例 ===" << std::endl;
    std::cout << std::endl;

    // 类型信息查询
    std::cout << "1. 类型信息查询:" << std::endl;
    std::cout << "   int.is_integral = " << (int_info.is_integral ? "true" : "false") << std::endl;
    std::cout << "   double.is_floating_point = " << (double_info.is_floating_point ? "true" : "false") << std::endl;
    std::cout << "   bool.is_arithmetic = " << (bool_info.is_arithmetic ? "true" : "false") << std::endl;
    std::cout << std::endl;

    // 大小和对齐
    std::cout << "2. 大小和对齐:" << std::endl;
    std::cout << "   sizeof(int) = " << int_size << std::endl;
    std::cout << "   sizeof(double) = " << double_size << std::endl;
    std::cout << "   alignof(int) = " << int_alignment << std::endl;
    std::cout << std::endl;

    // 类型名称
    std::cout << "3. 类型名称:" << std::endl;
    std::cout << "   int -> " << int_name << std::endl;
    std::cout << "   double -> " << double_name << std::endl;
    std::cout << "   bool -> " << bool_name << std::endl;
    std::cout << "   float -> " << float_name << std::endl;
    std::cout << "   char -> " << char_name << std::endl;
    std::cout << "   Point -> " << point_name << std::endl;
    std::cout << std::endl;

    // 类型列表
    std::cout << "4. 类型列表:" << std::endl;
    std::cout << "   type_list<int, double, bool, char>::size = " << type_list_size << std::endl;
    std::cout << "   contains<int> = " << (has_int ? "true" : "false") << std::endl;
    std::cout << "   contains<float> = " << (has_float ? "true" : "false") << std::endl;
    std::cout << "   index_of<int> = " << int_index << std::endl;
    std::cout << "   index_of<double> = " << double_index << std::endl;
    std::cout << std::endl;

    // 类型哈希
    std::cout << "5. 类型哈希:" << std::endl;
    std::cout << "   type_hash<int>() = " << int_type_hash << std::endl;
    std::cout << "   type_hash<double>() = " << double_type_hash << std::endl;
    std::cout << std::endl;

    // 自定义类型
    std::cout << "6. 自定义类型:" << std::endl;
    std::cout << "   Point.is_class = " << (is_point_class ? "true" : "false") << std::endl;
    std::cout << "   sizeof(Point) = " << point_size << std::endl;
    std::cout << "   Point.name = " << point_name << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
