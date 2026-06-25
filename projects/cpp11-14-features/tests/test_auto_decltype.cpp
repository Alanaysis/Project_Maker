/**
 * auto 和 decltype 测试
 */

#include <gtest/gtest.h>
#include <vector>
#include <map>
#include <string>
#include <type_traits>

// 测试 auto 基本类型推导
TEST(AutoDecltype, BasicAuto) {
    auto i = 42;
    auto d = 3.14;
    auto c = 'A';
    auto b = true;
    auto s = std::string("Hello");

    EXPECT_EQ(i, 42);
    EXPECT_DOUBLE_EQ(d, 3.14);
    EXPECT_EQ(c, 'A');
    EXPECT_TRUE(b);
    EXPECT_EQ(s, "Hello");
}

// 测试 auto 与引用
TEST(AutoDecltype, AutoWithReferences) {
    int x = 42;
    int& ref = x;

    auto a = ref;      // int
    auto& b = ref;     // int&

    a = 100;
    EXPECT_EQ(x, 42);  // a 是副本

    b = 200;
    EXPECT_EQ(x, 200); // b 是引用
}

// 测试 auto 与 const
TEST(AutoDecltype, AutoWithConst) {
    const int x = 42;

    auto a = x;           // int (去除 const)
    const auto b = x;     // const int
    const auto& c = x;    // const int&

    EXPECT_EQ(a, 42);
    EXPECT_EQ(b, 42);
    EXPECT_EQ(c, 42);
}

// 测试 decltype 基本用法
TEST(AutoDecltype, BasicDecltype) {
    int x = 42;
    const int cx = 100;
    int& ref = x;

    decltype(x) a = x;      // int
    decltype(cx) b = cx;    // const int
    decltype(ref) c = ref;  // int&

    EXPECT_EQ(a, 42);
    EXPECT_EQ(b, 100);
    EXPECT_EQ(c, 42);
}

// 测试 decltype 与表达式
TEST(AutoDecltype, DecltypeWithExpressions) {
    int x = 42;
    int y = 10;

    decltype(x + y) a = x + y;  // int
    decltype(x * 2.0) b = 3.14; // double

    EXPECT_EQ(a, 52);
    EXPECT_DOUBLE_EQ(b, 3.14);
}

// 测试 auto 与容器
TEST(AutoDecltype, AutoWithContainers) {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    for (auto it = vec.begin(); it != vec.end(); ++it) {
        EXPECT_GT(*it, 0);
    }
}

// 测试 auto 与范围 for
TEST(AutoDecltype, AutoWithRangeFor) {
    std::vector<int> vec = {1, 2, 3, 4, 5};
    int sum = 0;

    for (auto val : vec) {
        sum += val;
    }

    EXPECT_EQ(sum, 15);
}

// 测试 auto 与 map
TEST(AutoDecltype, AutoWithMap) {
    std::map<std::string, int> map = {
        {"one", 1}, {"two", 2}, {"three", 3}
    };

    for (const auto& pair : map) {
        EXPECT_FALSE(pair.first.empty());
        EXPECT_GT(pair.second, 0);
    }
}

// 测试返回类型后置
template<typename T, typename U>
auto add(T t, U u) -> decltype(t + u) {
    return t + u;
}

TEST(AutoDecltype, TrailingReturnType) {
    EXPECT_EQ(add(3, 4), 7);
    EXPECT_DOUBLE_EQ(add(3.14, 2.86), 6.0);
}

// 测试 C++14 返回类型推导
template<typename T, typename U>
auto multiply(T t, U u) {
    return t * u;
}

TEST(AutoDecltype, AutoReturnType) {
    EXPECT_EQ(multiply(3, 4), 12);
    EXPECT_DOUBLE_EQ(multiply(3.14, 2.0), 6.28);
}

// 测试 decltype(auto)
TEST(AutoDecltype, DecltypeAuto) {
    int x = 42;
    const int& cref = x;

    decltype(auto) a = cref;  // const int&
    decltype(auto) b = (x);   // int&

    EXPECT_EQ(a, 42);
    EXPECT_EQ(b, 42);
}

// 测试 auto 与 Lambda
TEST(AutoDecltype, AutoWithLambda) {
    auto lambda = [](int x) { return x * 2; };
    EXPECT_EQ(lambda(21), 42);

    auto generic = [](auto a, auto b) { return a + b; };
    EXPECT_EQ(generic(3, 4), 7);
}

// 测试 auto 与初始化列表
TEST(AutoDecltype, AutoWithInitializerList) {
    auto vec = {1, 2, 3, 4, 5};
    EXPECT_EQ(vec.size(), 5);
}

// 测试类型特征
TEST(AutoDecltype, TypeTraits) {
    int x = 42;
    auto a = x;
    decltype(x) b = x;

    EXPECT_TRUE((std::is_same<decltype(a), int>::value));
    EXPECT_TRUE((std::is_same<decltype(b), int>::value));
}

// 测试 auto 与指针
TEST(AutoDecltype, AutoWithPointers) {
    int x = 42;
    int* ptr = &x;

    auto a = ptr;     // int*
    auto& b = ptr;    // int*&

    EXPECT_EQ(*a, 42);
    EXPECT_EQ(*b, 42);
}

// 测试 auto 与 const 指针
TEST(AutoDecltype, AutoWithConstPointers) {
    int x = 42;
    const int* ptr = &x;

    auto a = ptr;           // const int*
    const auto b = ptr;     // const int* const
    auto* c = ptr;          // const int*

    EXPECT_EQ(*a, 42);
    EXPECT_EQ(*b, 42);
    EXPECT_EQ(*c, 42);
}
