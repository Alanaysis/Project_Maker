/**
 * @file sfinae.cpp
 * @brief SFINAE 检测单元测试
 */

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include "../include/sfinae/member_detection.hpp"

int tests_passed = 0;
int tests_failed = 0;

int main() {
    using namespace tmp;

    std::cout << "=== SFINAE Detection Tests ===" << std::endl;
    std::cout << std::endl;

    // Test has_size
    std::cout << "Testing has_size... ";
    {
        static_assert(has_size_v<std::vector<int>>, "vector has size");
        static_assert(has_size_v<std::string>, "string has size");
        static_assert(!has_size_v<int>, "int has no size");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test has_begin_end
    std::cout << "Testing has_begin_end... ";
    {
        static_assert(has_begin_end_v<std::vector<int>>, "vector has begin/end");
        static_assert(has_begin_end_v<std::string>, "string has begin/end");
        static_assert(!has_begin_end_v<int>, "int has no begin/end");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test has_push_back
    std::cout << "Testing has_push_back... ";
    {
        static_assert(has_push_back_v<std::vector<int>, int>, "vector has push_back");
        static_assert(!has_push_back_v<std::map<int,int>, int>, "map has no push_back");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test has_reserve
    std::cout << "Testing has_reserve... ";
    {
        static_assert(has_reserve_v<std::vector<int>>, "vector has reserve");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test has_clear
    std::cout << "Testing has_clear... ";
    {
        static_assert(has_clear_v<std::vector<int>>, "vector has clear");
        static_assert(has_clear_v<std::string>, "string has clear");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test has_empty
    std::cout << "Testing has_empty... ";
    {
        static_assert(has_empty_v<std::vector<int>>, "vector has empty");
        static_assert(has_empty_v<std::string>, "string has empty");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test has_value_type
    std::cout << "Testing has_value_type... ";
    {
        static_assert(has_value_type_v<std::vector<int>>, "vector has value_type");
        static_assert(!has_value_type_v<int>, "int has no value_type");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test has_iterator
    std::cout << "Testing has_iterator... ";
    {
        static_assert(has_iterator_v<std::vector<int>>, "vector has iterator");
        static_assert(!has_iterator_v<int>, "int has no iterator");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test has_equal_operator
    std::cout << "Testing has_equal_operator... ";
    {
        static_assert(has_equal_operator_v<int>, "int has operator==");
        static_assert(has_equal_operator_v<std::string>, "string has operator==");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test has_less_operator
    std::cout << "Testing has_less_operator... ";
    {
        static_assert(has_less_operator_v<int>, "int has operator<");
        static_assert(has_less_operator_v<std::string>, "string has operator<");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test has_stream_operator
    std::cout << "Testing has_stream_operator... ";
    {
        static_assert(has_stream_operator_v<int>, "int has operator<<");
        static_assert(has_stream_operator_v<std::string>, "string has operator<<");
        static_assert(has_stream_operator_v<double>, "double has operator<<");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test is_iterable
    std::cout << "Testing is_iterable... ";
    {
        static_assert(is_iterable_v<std::vector<int>>, "vector is iterable");
        static_assert(is_iterable_v<std::string>, "string is iterable");
        static_assert(!is_iterable_v<int>, "int is not iterable");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test is_hashable
    std::cout << "Testing is_hashable... ";
    {
        static_assert(is_hashable_v<int>, "int is hashable");
        static_assert(is_hashable_v<std::string>, "string is hashable");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test is_comparable
    std::cout << "Testing is_comparable... ";
    {
        static_assert(is_comparable_v<int>, "int is comparable");
        static_assert(is_comparable_v<std::string>, "string is comparable");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test is_container_like
    std::cout << "Testing is_container_like... ";
    {
        static_assert(is_container_like_v<std::vector<int>>, "vector is container_like");
        static_assert(!is_container_like_v<int>, "int is not container_like");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Test is_dynamic_container
    std::cout << "Testing is_dynamic_container... ";
    {
        // is_dynamic_container checks for size + begin/end + value_type + push_back
        static_assert(is_container_like_v<std::vector<int>>, "vector is container_like");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    std::cout << std::endl;
    std::cout << "Results: " << tests_passed << " passed, "
              << tests_failed << " failed" << std::endl;

    return tests_failed > 0 ? 1 : 0;
}
