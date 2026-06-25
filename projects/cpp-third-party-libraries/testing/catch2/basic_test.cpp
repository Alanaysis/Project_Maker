/**
 * @file basic_test.cpp
 * @brief Catch2 测试框架基础示例
 * @details 展示 Catch2 的基本用法
 *          Catch2 是一个现代 C++ 测试框架
 *          宏使用少，代码风格自然
 */

#include <catch2/catch_test_macros.hpp>
#include <string>
#include <vector>
#include <algorithm>

/**
 * @brief 基础测试示例
 * @details 展示 Catch2 的基本断言
 */
TEST_CASE("Basic assertions", "[basic]") {
    // 基础断言
    REQUIRE(1 + 1 == 2);
    REQUIRE_FALSE(1 + 1 == 3);

    // 比较断言
    REQUIRE(5 > 3);
    REQUIRE(3 < 5);
    REQUIRE(5 >= 5);
    REQUIRE(3 <= 5);
}

/**
 * @brief 字符串测试示例
 * @details 展示字符串相关的测试
 */
TEST_CASE("String operations", "[string]") {
    std::string str = "Hello, World!";

    SECTION("Length") {
        REQUIRE(str.length() == 13);
    }

    SECTION("Substring") {
        REQUIRE(str.substr(0, 5) == "Hello");
    }

    SECTION("Find") {
        REQUIRE(str.find("World") != std::string::npos);
        REQUIRE(str.find("Foo") == std::string::npos);
    }
}

/**
 * @brief 容器测试示例
 * @details 展示容器相关的测试
 */
TEST_CASE("Vector operations", "[container]") {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    SECTION("Size") {
        REQUIRE(vec.size() == 5);
        REQUIRE_FALSE(vec.empty());
    }

    SECTION("Element access") {
        REQUIRE(vec.front() == 1);
        REQUIRE(vec.back() == 5);
        REQUIRE(vec[2] == 3);
    }

    SECTION("Modification") {
        vec.push_back(6);
        REQUIRE(vec.size() == 6);
        REQUIRE(vec.back() == 6);
    }
}

/**
 * @brief 测试夹具示例
 * @details 展示如何使用测试夹具
 */
TEST_CASE("Test fixture example", "[fixture]") {
    // 设置
    std::vector<int> data = {5, 3, 1, 4, 2};

    SECTION("Sort") {
        std::sort(data.begin(), data.end());
        REQUIRE(data == std::vector<int>{1, 2, 3, 4, 5});
    }

    SECTION("Find") {
        auto it = std::find(data.begin(), data.end(), 4);
        REQUIRE(it != data.end());
        REQUIRE(*it == 4);
    }

    SECTION("Count") {
        REQUIRE(std::count(data.begin(), data.end(), 3) == 1);
        REQUIRE(std::count(data.begin(), data.end(), 6) == 0);
    }
}

/**
 * @brief BDD 风格测试示例
 * @details 展示 Catch2 的 BDD 风格测试
 */
SCENARIO("Vector operations BDD style", "[bdd]") {
    GIVEN("A vector with some elements") {
        std::vector<int> vec = {1, 2, 3, 4, 5};

        WHEN("We add an element") {
            vec.push_back(6);

            THEN("Size increases") {
                REQUIRE(vec.size() == 6);
            }

            THEN("New element is at the back") {
                REQUIRE(vec.back() == 6);
            }
        }

        WHEN("We remove the last element") {
            vec.pop_back();

            THEN("Size decreases") {
                REQUIRE(vec.size() == 4);
            }

            THEN("Last element changes") {
                REQUIRE(vec.back() == 4);
            }
        }
    }
}

/**
 * @brief 参数化测试示例
 * @details 展示如何进行参数化测试
 */
TEST_CASE("Parameterized test", "[parameterized]") {
    auto value = GENERATE(1, 2, 3, 4, 5);

    REQUIRE(value > 0);
    REQUIRE(value < 10);
}