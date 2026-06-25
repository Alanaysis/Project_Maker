/**
 * @file basic_test.cpp
 * @brief doctest 测试框架基础示例
 * @details 展示 doctest 的基本用法
 *          doctest 是一个轻量级的 C++ 测试框架
 *          编译速度快，宏使用少
 */

#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include <doctest/doctest.h>
#include <string>
#include <vector>
#include <algorithm>

/**
 * @brief 基础测试示例
 * @details 展示 doctest 的基本断言
 */
TEST_CASE("Basic assertions") {
    // 基础断言
    CHECK(1 + 1 == 2);
    CHECK_FALSE(1 + 1 == 3);

    // 比较断言
    CHECK(5 > 3);
    CHECK(3 < 5);
    CHECK(5 >= 5);
    CHECK(3 <= 5);
}

/**
 * @brief 字符串测试示例
 * @details 展示字符串相关的测试
 */
TEST_CASE("String operations") {
    std::string str = "Hello, World!";

    SUBCASE("Length") {
        CHECK(str.length() == 13);
    }

    SUBCASE("Substring") {
        CHECK(str.substr(0, 5) == "Hello");
    }

    SUBCASE("Find") {
        CHECK(str.find("World") != std::string::npos);
        CHECK(str.find("Foo") == std::string::npos);
    }
}

/**
 * @brief 容器测试示例
 * @details 展示容器相关的测试
 */
TEST_CASE("Vector operations") {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    SUBCASE("Size") {
        CHECK(vec.size() == 5);
        CHECK_FALSE(vec.empty());
    }

    SUBCASE("Element access") {
        CHECK(vec.front() == 1);
        CHECK(vec.back() == 5);
        CHECK(vec[2] == 3);
    }

    SUBCASE("Modification") {
        vec.push_back(6);
        CHECK(vec.size() == 6);
        CHECK(vec.back() == 6);
    }
}

/**
 * @brief 测试套件示例
 * @details 展示如何使用测试套件
 */
TEST_SUITE("Math operations") {
    TEST_CASE("Addition") {
        CHECK(1 + 1 == 2);
        CHECK(2 + 3 == 5);
    }

    TEST_CASE("Subtraction") {
        CHECK(5 - 3 == 2);
        CHECK(10 - 4 == 6);
    }
}

/**
 * @brief 参数化测试示例
 * @details 展示如何进行参数化测试
 */
TEST_CASE("Parameterized test") {
    int value = 42;

    CHECK(value > 0);
    CHECK(value < 100);
}

/**
 * @brief 异常测试示例
 * @details 展示异常相关的测试
 */
TEST_CASE("Exception handling") {
    // 测试是否抛出异常
    CHECK_THROWS_AS(throw std::runtime_error("error"), std::runtime_error);

    // 测试是否不抛出异常
    CHECK_NOTHROW(int x = 1 + 1; (void)x);
}

/**
 * @brief doctest 概念说明
 * @details 介绍 doctest 的核心概念
 */
TEST_CASE("doctest concepts") {
    SUBCASE("Main features") {
        // 轻量级
        CHECK(true);

        // 快速编译
        CHECK(true);

        // 宏使用少
        CHECK(true);
    }

    SUBCASE("Comparison with other frameworks") {
        // 比 GTest 更快编译
        CHECK(true);

        // 比 Catch2 更轻量
        CHECK(true);
    }
}