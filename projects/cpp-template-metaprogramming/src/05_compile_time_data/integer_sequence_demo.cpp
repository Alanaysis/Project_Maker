// =============================================================================
// integer_sequence_demo.cpp - 编译期整数序列演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o integer_sequence_demo integer_sequence_demo.cpp
// 运行: ./integer_sequence_demo
// =============================================================================

#include <iostream>
#include <array>
#include <tuple>
#include <string>
#include "compile_time/integer_sequence.hpp"

// 使用整数序列遍历 tuple 的辅助函数
template <typename Tuple, typename F, std::size_t... Is>
void print_tuple_impl(const Tuple& t, F f, tmp::index_sequence<Is...>) {
    (f(std::get<Is>(t)), ...);
}

template <typename Tuple, typename F>
void print_tuple(const Tuple& t, F f) {
    constexpr auto size = std::tuple_size_v<Tuple>;
    print_tuple_impl(t, f, tmp::make_index_sequence<size>{});
}

int main() {
    std::cout << "=== 编译期整数序列演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. 基本定义
    std::cout << "1. 基本定义:" << std::endl;
    using Seq = tmp::integer_sequence<int, 0, 1, 2, 3, 4>;
    std::cout << "  Sequence size: " << Seq::size() << std::endl;

    using IdxSeq = tmp::index_sequence<10, 20, 30>;
    std::cout << "  Index sequence size: " << IdxSeq::size() << std::endl;
    std::cout << std::endl;

    // 2. 生成序列
    std::cout << "2. 生成序列:" << std::endl;
    using Seq0_5 = tmp::make_index_sequence<5>;
    std::cout << "  make_index_sequence<5> size: " << Seq0_5::size() << std::endl;

    using Seq0_10 = tmp::make_integer_sequence<int, 10>;
    std::cout << "  make_integer_sequence<int, 10> size: " << Seq0_10::size() << std::endl;

    using IdxFor = tmp::index_sequence_for<int, double, char, float>;
    std::cout << "  index_sequence_for<int,double,char,float> size: " << IdxFor::size() << std::endl;
    std::cout << std::endl;

    // 3. 访问操作
    std::cout << "3. 访问操作:" << std::endl;
    using MySeq = tmp::integer_sequence<int, 10, 20, 30, 40, 50>;
    std::cout << "  element<0>: " << tmp::sequence_element_v<0, MySeq> << std::endl;
    std::cout << "  element<2>: " << tmp::sequence_element_v<2, MySeq> << std::endl;
    std::cout << "  element<4>: " << tmp::sequence_element_v<4, MySeq> << std::endl;
    std::cout << "  front: " << tmp::sequence_front_v<MySeq> << std::endl;
    std::cout << "  back: " << tmp::sequence_back_v<MySeq> << std::endl;
    std::cout << std::endl;

    // 4. 变换操作
    std::cout << "4. 变换操作:" << std::endl;
    using Reversed = tmp::reverse_sequence_t<MySeq>;
    std::cout << "  reversed<0>: " << tmp::sequence_element_v<0, Reversed> << std::endl;
    std::cout << "  reversed<4>: " << tmp::sequence_element_v<4, Reversed> << std::endl;

    using Seq1 = tmp::index_sequence<1, 2, 3>;
    using Seq2 = tmp::index_sequence<4, 5, 6>;
    using Concat = tmp::concat_sequence_t<Seq1, Seq2>;
    std::cout << "  concat<3>: " << tmp::sequence_element_v<3, Concat> << std::endl;
    std::cout << "  concat size: " << Concat::size() << std::endl;
    std::cout << std::endl;

    // 5. 归约操作
    std::cout << "5. 归约操作:" << std::endl;
    using NumSeq = tmp::integer_sequence<int, 1, 2, 3, 4, 5>;
    std::cout << "  sum(1,2,3,4,5): " << tmp::sequence_sum_v<NumSeq> << std::endl;
    std::cout << "  product(1,2,3,4,5): " << tmp::sequence_product_v<NumSeq> << std::endl;
    std::cout << std::endl;

    // 6. 斐波那契序列
    std::cout << "6. 斐波那契序列:" << std::endl;
    using Fib10 = tmp::fib_sequence_t<10>;
    std::cout << "  First 10 Fibonacci numbers: ";
    for (std::size_t i = 0; i < Fib10::size(); ++i) {
        // 运行时打印（编译期值）
    }
    // 使用编译期访问
    std::cout << tmp::sequence_element_v<0, Fib10> << " "
              << tmp::sequence_element_v<1, Fib10> << " "
              << tmp::sequence_element_v<2, Fib10> << " "
              << tmp::sequence_element_v<3, Fib10> << " "
              << tmp::sequence_element_v<4, Fib10> << " "
              << tmp::sequence_element_v<5, Fib10> << " "
              << tmp::sequence_element_v<6, Fib10> << " "
              << tmp::sequence_element_v<7, Fib10> << " "
              << tmp::sequence_element_v<8, Fib10> << " "
              << tmp::sequence_element_v<9, Fib10> << std::endl;
    std::cout << std::endl;

    // 7. 遍历 tuple
    std::cout << "7. 遍历 tuple:" << std::endl;
    auto my_tuple = std::make_tuple(1, 3.14, std::string("hello"), 'A');
    std::cout << "  Tuple elements: ";
    print_tuple(my_tuple, [](const auto& elem) {
        std::cout << elem << " ";
    });
    std::cout << std::endl;
    std::cout << std::endl;

    // 8. tuple 转数组
    std::cout << "8. tuple 转数组:" << std::endl;
    auto num_tuple = std::make_tuple(10, 20, 30, 40, 50);
    auto arr = tmp::tuple_to_array(num_tuple);
    std::cout << "  Array: ";
    for (auto v : arr) std::cout << v << " ";
    std::cout << std::endl;
    std::cout << std::endl;

    // 9. 编译期数组初始化
    std::cout << "9. 编译期数组初始化:" << std::endl;
    auto squares = tmp::make_array<int, 8>([](std::size_t i) {
        return static_cast<int>(i * i);
    });
    std::cout << "  Squares: ";
    for (auto v : squares) std::cout << v << " ";
    std::cout << std::endl;

    auto cubes = tmp::make_array<int, 6>([](std::size_t i) {
        return static_cast<int>(i * i * i);
    });
    std::cout << "  Cubes: ";
    for (auto v : cubes) std::cout << v << " ";
    std::cout << std::endl;
    std::cout << std::endl;

    // 10. for_each with tuple
    std::cout << "10. for_each with tuple:" << std::endl;
    auto mixed = std::make_tuple(42, 3.14, std::string("world"));
    tmp::for_each(mixed, [](const auto& elem) {
        std::cout << "  Element: " << elem << std::endl;
    });
    std::cout << std::endl;

    std::cout << "=== 编译期整数序列演示完成 ===" << std::endl;
    return 0;
}
