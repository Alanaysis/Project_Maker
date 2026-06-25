// =============================================================================
// fold_expressions_demo.cpp - 折叠表达式演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o fold_expressions_demo fold_expressions_demo.cpp
// 运行: ./fold_expressions_demo
// =============================================================================

#include <iostream>
#include <string>
#include <vector>
#include "variadic/fold_expressions.hpp"

int main() {
    using namespace tmp::fold;

    std::cout << "=== 折叠表达式演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. 四种折叠形式
    std::cout << "1. 四种折叠形式:" << std::endl;
    std::cout << "  左折叠 sum_left(1,2,3,4,5) = " << sum_left(1, 2, 3, 4, 5) << std::endl;
    std::cout << "  右折叠 sum_right(1,2,3,4,5) = " << sum_right(1, 2, 3, 4, 5) << std::endl;
    std::cout << std::endl;

    // 2. 二元折叠
    std::cout << "2. 二元折叠:" << std::endl;
    std::cout << "  sum_with_init(100, 1,2,3) = " << sum_with_init(100, 1, 2, 3) << std::endl;
    std::cout << std::endl;

    // 3. 逻辑折叠
    std::cout << "3. 逻辑折叠:" << std::endl;
    std::cout << "  all_true(true, true, true) = " << all_true(true, true, true) << std::endl;
    std::cout << "  all_true(true, false, true) = " << all_true(true, false, true) << std::endl;
    std::cout << "  any_true(false, false, true) = " << any_true(false, false, true) << std::endl;
    std::cout << "  any_true(false, false, false) = " << any_true(false, false, false) << std::endl;
    std::cout << std::endl;

    // 4. 类型检查折叠
    std::cout << "4. 类型检查折叠:" << std::endl;
    std::cout << "  are_all_same<int, int, int>() = "
              << are_all_same<int, int, int>() << std::endl;
    std::cout << "  are_all_same<int, double, int>() = "
              << are_all_same<int, double, int>() << std::endl;
    std::cout << "  all_satisfy<std::is_integral, int, long, short>() = "
              << all_satisfy<std::is_integral, int, long, short>() << std::endl;
    std::cout << std::endl;

    // 5. 统计折叠
    std::cout << "5. 统计折叠:" << std::endl;
    std::cout << "  count_if(even, 1,2,3,4,5,6) = "
              << count_if([](int x) { return x % 2 == 0; }, 1, 2, 3, 4, 5, 6) << std::endl;
    std::cout << std::endl;

    // 6. 收集到数组
    std::cout << "6. 收集到数组:" << std::endl;
    auto arr = to_array<double>(1, 2, 3, 4, 5);
    std::cout << "  array: ";
    for (auto v : arr) std::cout << v << " ";
    std::cout << std::endl;
    std::cout << std::endl;

    // 7. 范围检查
    std::cout << "7. 范围检查:" << std::endl;
    std::cout << "  all_in_range(0, 10, 1,5,8) = "
              << all_in_range(0, 10, 1, 5, 8) << std::endl;
    std::cout << "  all_in_range(0, 10, 1,15,8) = "
              << all_in_range(0, 10, 1, 15, 8) << std::endl;
    std::cout << std::endl;

    // 8. 字符串拼接
    std::cout << "8. 字符串拼接:" << std::endl;
    std::cout << "  concat(1,2,3) = " << concat(1, 2, 3) << std::endl;
    std::cout << "  concat_strings(\"Hello\", \" \", \"World\") = "
              << concat_strings(std::string("Hello"), std::string(" "), std::string("World")) << std::endl;
    std::cout << std::endl;

    // 9. 编译期折叠
    std::cout << "9. 编译期折叠:" << std::endl;
    std::cout << "  constexpr_sum<1,2,3,4,5>() = " << constexpr_sum<1, 2, 3, 4, 5>() << std::endl;
    std::cout << "  constexpr_product<2,3,4>() = " << constexpr_product<2, 3, 4>() << std::endl;
    std::cout << "  constexpr_max<3,7,2,9,1>() = " << constexpr_max<3, 7, 2, 9, 1>() << std::endl;
    std::cout << "  constexpr_min<3,7,2,9,1>() = " << constexpr_min<3, 7, 2, 9, 1>() << std::endl;
    std::cout << std::endl;

    // 10. TypeList 连接
    std::cout << "10. TypeList 连接:" << std::endl;
    using L1 = TypeList<int, double>;
    using L2 = TypeList<char, float>;
    using L3 = TypeList<std::string>;
    using Combined = Concat_t<L1, L2, L3>;
    std::cout << "  Concat size = " << Combined::size << std::endl;
    std::cout << std::endl;

    // 11. 安全释放
    std::cout << "11. 批量操作:" << std::endl;
    int* p1 = new int(1);
    int* p2 = new int(2);
    int* p3 = new int(3);
    std::cout << "  Before: p1=" << *p1 << " p2=" << *p2 << " p3=" << *p3 << std::endl;
    safe_delete_all(p1, p2, p3);
    std::cout << "  After delete: p1=" << (p1 ? "valid" : "null")
              << " p2=" << (p2 ? "valid" : "null")
              << " p3=" << (p3 ? "valid" : "null") << std::endl;
    std::cout << std::endl;

    std::cout << "=== 折叠表达式演示完成 ===" << std::endl;
    return 0;
}
