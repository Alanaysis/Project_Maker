/**
 * @file type_list.cpp
 * @brief 类型列表单元测试
 */

#include <iostream>
#include <string>
#include <type_traits>
#include "../include/type_computation/type_list.hpp"
#include "../include/type_computation/type_counting.hpp"
#include "../include/type_computation/type_conversion.hpp"

int tests_passed = 0;
int tests_failed = 0;

template <typename T, typename U>
constexpr bool same_v = std::is_same_v<T, U>;

int main() {
    using namespace tmp;

    std::cout << "=== Type List Tests ===" << std::endl;
    std::cout << std::endl;

    // Test front/back
    std::cout << "Testing front/back... ";
    {
        using L = type_list<int, double, char>;
        static_assert(same_v<front<L>, int>, "front should be int");
        static_assert(same_v<back<L>, char>, "back should be char");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test push_front/push_back
    std::cout << "Testing push_front/push_back... ";
    {
        using L = type_list<int, double>;
        using PF = push_front<L, char>;
        using PB = push_back<L, char>;
        static_assert(same_v<front<PF>, char>, "push_front front should be char");
        static_assert(PF::size == 3, "push_front size should be 3");
        static_assert(same_v<back<PB>, char>, "push_back back should be char");
        static_assert(PB::size == 3, "push_back size should be 3");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test pop_front/pop_back
    std::cout << "Testing pop_front/pop_back... ";
    {
        using L = type_list<int, double, char>;
        using PF = pop_front<L>;
        using PB = pop_back<L>;
        static_assert(same_v<front<PF>, double>, "pop_front front should be double");
        static_assert(PF::size == 2, "pop_front size should be 2");
        static_assert(same_v<back<PB>, double>, "pop_back back should be double");
        static_assert(PB::size == 2, "pop_back size should be 2");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test at
    std::cout << "Testing at... ";
    {
        using L = type_list<int, double, char, float>;
        static_assert(same_v<at<L, 0>, int>, "at<0> should be int");
        static_assert(same_v<at<L, 1>, double>, "at<1> should be double");
        static_assert(same_v<at<L, 2>, char>, "at<2> should be char");
        static_assert(same_v<at<L, 3>, float>, "at<3> should be float");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test contains
    std::cout << "Testing contains... ";
    {
        using L = type_list<int, double, char>;
        static_assert(contains<L, int>, "should contain int");
        static_assert(contains<L, double>, "should contain double");
        static_assert(!contains<L, float>, "should not contain float");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test index_of
    std::cout << "Testing index_of... ";
    {
        using L = type_list<int, double, char>;
        static_assert(index_of<L, int> == 0, "int at index 0");
        static_assert(index_of<L, double> == 1, "double at index 1");
        static_assert(index_of<L, char> == 2, "char at index 2");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test reverse
    std::cout << "Testing reverse... ";
    {
        using L = type_list<int, double, char>;
        using R = reverse<L>;
        static_assert(same_v<front<R>, char>, "reverse front should be char");
        static_assert(same_v<at<R, 1>, double>, "reverse at<1> should be double");
        static_assert(same_v<back<R>, int>, "reverse back should be int");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test concat
    std::cout << "Testing concat... ";
    {
        using L1 = type_list<int, double>;
        using L2 = type_list<char, float>;
        using C = concat<L1, L2>;
        static_assert(C::size == 4, "concat size should be 4");
        static_assert(same_v<at<C, 2>, char>, "concat at<2> should be char");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test transform
    std::cout << "Testing transform... ";
    {
        using L = type_list<int, double, char>;
        using T = transform<L, std::add_pointer>;
        static_assert(same_v<front<T>, int*>, "transform front should be int*");
        static_assert(same_v<at<T, 1>, double*>, "transform at<1> should be double*");
        static_assert(same_v<at<T, 2>, char*>, "transform at<2> should be char*");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test filter
    std::cout << "Testing filter... ";
    {
        using L = type_list<int, double, char, float, bool>;
        using F = filter<L, std::is_floating_point>;
        static_assert(F::size == 2, "filter size should be 2");
        static_assert(same_v<front<F>, double>, "filter front should be double");
        static_assert(same_v<at<F, 1>, float>, "filter at<1> should be float");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test count
    std::cout << "Testing count... ";
    {
        using L = type_list<int, double, int, char, int>;
        static_assert(count<L, int> == 3, "count<int> should be 3");
        static_assert(count<L, double> == 1, "count<double> should be 1");
        static_assert(count<L, float> == 0, "count<float> should be 0");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test unique
    std::cout << "Testing unique... ";
    {
        using L = type_list<int, double, int, char, double>;
        using U = unique<L>;
        static_assert(U::size == 3, "unique size should be 3");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test has_duplicates
    std::cout << "Testing has_duplicates... ";
    {
        using D = type_list<int, double, int>;
        using N = type_list<int, double, char>;
        static_assert(has_duplicates<D>, "should have duplicates");
        static_assert(!has_duplicates<N>, "should not have duplicates");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test type_union
    std::cout << "Testing type_union... ";
    {
        using A = type_list<int, double, char>;
        using B = type_list<double, char, float>;
        using U = type_union<A, B>;
        static_assert(contains<U, int>, "union should contain int");
        static_assert(contains<U, double>, "union should contain double");
        static_assert(contains<U, char>, "union should contain char");
        static_assert(contains<U, float>, "union should contain float");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test type_intersection
    std::cout << "Testing type_intersection... ";
    {
        using A = type_list<int, double, char>;
        using B = type_list<double, char, float>;
        using I = type_intersection<A, B>;
        static_assert(I::size == 2, "intersection size should be 2");
        static_assert(contains<I, double>, "intersection should contain double");
        static_assert(contains<I, char>, "intersection should contain char");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test type_difference
    std::cout << "Testing type_difference... ";
    {
        using A = type_list<int, double, char>;
        using B = type_list<double, char, float>;
        using D = type_difference<A, B>;
        static_assert(D::size == 1, "difference size should be 1");
        static_assert(contains<D, int>, "difference should contain int");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    std::cout << std::endl;
    std::cout << "Results: " << tests_passed << " passed, "
              << tests_failed << " failed" << std::endl;

    return tests_failed > 0 ? 1 : 0;
}
