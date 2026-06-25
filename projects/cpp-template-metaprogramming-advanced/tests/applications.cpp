/**
 * @file applications.cpp
 * @brief 应用层单元测试
 */

#include <iostream>
#include <string>
#include "../include/applications/matrix_operations.hpp"
#include "../include/applications/compile_time_regex.hpp"
#include "../include/applications/serialization.hpp"

int tests_passed = 0;
int tests_failed = 0;

int main() {
    using namespace tmp;

    std::cout << "=== Application Tests ===" << std::endl;
    std::cout << std::endl;

    // Matrix tests
    std::cout << "Testing matrix_identity... ";
    {
        constexpr auto I = Matrix<double, 3, 3>::identity();
        static_assert(I(0,0) == 1.0, "I(0,0) should be 1");
        static_assert(I(1,1) == 1.0, "I(1,1) should be 1");
        static_assert(I(2,2) == 1.0, "I(2,2) should be 1");
        static_assert(I(0,1) == 0.0, "I(0,1) should be 0");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    std::cout << "Testing matrix_transpose... ";
    {
        constexpr Matrix<int, 2, 3> m = {1, 2, 3, 4, 5, 6};
        constexpr auto t = m.transpose();
        static_assert(t(0,0) == 1, "t(0,0) should be 1");
        static_assert(t(0,1) == 4, "t(0,1) should be 4");
        static_assert(t(1,0) == 2, "t(1,0) should be 2");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    std::cout << "Testing matrix_determinant_2x2... ";
    {
        constexpr Matrix<double, 2, 2> m = {1, 2, 3, 4};
        constexpr auto det = determinant(m);
        static_assert(det == -2.0, "det should be -2");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    std::cout << "Testing matrix_trace... ";
    {
        constexpr Matrix<int, 3, 3> m = {1, 2, 3, 4, 5, 6, 7, 8, 9};
        constexpr auto t = trace(m);
        static_assert(t == 15, "trace should be 15");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Regex tests
    std::cout << "Testing regex_digits... ";
    {
        static_assert(regex::Digits::match("12345", 5), "12345 is digits");
        static_assert(!regex::Digits::match("123a5", 5), "123a5 is not digits");
        static_assert(!regex::Digits::match("", 0), "empty is not digits");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    std::cout << "Testing regex_alpha... ";
    {
        static_assert(regex::Alpha::match("hello", 5), "hello is alpha");
        static_assert(!regex::Alpha::match("hel1o", 5), "hel1o is not alpha");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    std::cout << "Testing regex_alnum... ";
    {
        static_assert(regex::Alnum::match("hello123", 8), "hello123 is alnum");
        static_assert(!regex::Alnum::match("hello!", 6), "hello! is not alnum");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    std::cout << "Testing regex_hex... ";
    {
        static_assert(regex::HexDigits::match("1a2B3c", 6), "1a2B3c is hex");
        static_assert(!regex::HexDigits::match("1g2B3c", 6), "1g2B3c is not hex");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    std::cout << "Testing regex_wildcard... ";
    {
        static_assert(regex::wildcard_match("hello", 5, "hello", 5), "hello matches hello");
        static_assert(regex::wildcard_match("hello", 5, "h*o", 3), "hello matches h*o");
        static_assert(regex::wildcard_match("hello", 5, "h?llo", 5), "hello matches h?llo");
        static_assert(!regex::wildcard_match("hello", 5, "h?l", 3), "hello doesn't match h?l");
        static_assert(regex::wildcard_match("hello", 5, "*", 1), "hello matches *");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    std::cout << "Testing regex_ipv4... ";
    {
        static_assert(regex::is_valid_ipv4("192.168.1.1", 11), "192.168.1.1 is valid IPv4");
        static_assert(regex::is_valid_ipv4("0.0.0.0", 7), "0.0.0.0 is valid IPv4");
        static_assert(!regex::is_valid_ipv4("256.1.1.1", 9), "256.1.1.1 is not valid IPv4");
        static_assert(!regex::is_valid_ipv4("1.2.3", 5), "1.2.3 is not valid IPv4");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    std::cout << "Testing regex_email... ";
    {
        static_assert(regex::is_valid_email("test@example.com", 16), "test@example.com is valid email");
        static_assert(!regex::is_valid_email("invalid", 7), "invalid is not valid email");
        static_assert(!regex::is_valid_email("@example.com", 12), "@example.com is not valid email");
        std::cout << "PASSED" << std::endl;
        tests_passed++;
    }

    // Serialization tests
    std::cout << "Testing serialize_value... ";
    {
        // serialize_value is not constexpr, so use runtime checks
        auto s1 = serialize_value(42);
        auto s2 = serialize_value(true);
        auto s3 = serialize_value(false);
        if (s1 == "42" && s2 == "true" && s3 == "false") {
            std::cout << "PASSED" << std::endl;
            tests_passed++;
        } else {
            std::cout << "FAILED" << std::endl;
            tests_failed++;
        }
    }

    std::cout << std::endl;
    std::cout << "Results: " << tests_passed << " passed, "
              << tests_failed << " failed" << std::endl;

    return tests_failed > 0 ? 1 : 0;
}
