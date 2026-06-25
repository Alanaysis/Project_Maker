/**
 * Lambda 表达式测试
 */

#include <gtest/gtest.h>
#include <vector>
#include <algorithm>
#include <functional>
#include <string>
#include <numeric>

// 测试基本 Lambda
TEST(Lambda, BasicLambda) {
    auto add = [](int a, int b) { return a + b; };
    EXPECT_EQ(add(3, 4), 7);
}

// 测试 Lambda 调用
TEST(Lambda, LambdaCall) {
    int result = [](int x) { return x * x; }(5);
    EXPECT_EQ(result, 25);
}

// 测试值捕获
TEST(Lambda, CaptureByValue) {
    int x = 10;
    auto capture = [x]() { return x; };
    EXPECT_EQ(capture(), 10);

    // 修改原变量不影响捕获的值
    x = 20;
    EXPECT_EQ(capture(), 10);
}

// 测试引用捕获
TEST(Lambda, CaptureByReference) {
    int x = 10;
    auto capture = [&x]() { x += 5; return x; };
    EXPECT_EQ(capture(), 15);
    EXPECT_EQ(x, 15);
}

// 测试隐式值捕获
TEST(Lambda, ImplicitCaptureByValue) {
    int x = 10;
    int y = 20;
    auto capture = [=]() { return x + y; };
    EXPECT_EQ(capture(), 30);
}

// 测试隐式引用捕获
TEST(Lambda, ImplicitCaptureByReference) {
    int x = 10;
    int y = 20;
    auto capture = [&]() { x += 5; y += 10; return x + y; };
    EXPECT_EQ(capture(), 45);
    EXPECT_EQ(x, 15);
    EXPECT_EQ(y, 30);
}

// 测试 Lambda 与算法
TEST(Lambda, LambdaWithAlgorithms) {
    std::vector<int> vec = {5, 2, 8, 1, 9, 3};

    // 排序
    std::sort(vec.begin(), vec.end(), [](int a, int b) { return a < b; });
    EXPECT_EQ(vec[0], 1);
    EXPECT_EQ(vec[5], 9);

    // 查找
    auto it = std::find_if(vec.begin(), vec.end(), [](int n) { return n > 5; });
    EXPECT_NE(it, vec.end());
    EXPECT_EQ(*it, 8);

    // 计数
    auto count = std::count_if(vec.begin(), vec.end(), [](int n) { return n % 2 == 0; });
    EXPECT_EQ(count, 2);
}

// 测试 Lambda 作为函数参数
TEST(Lambda, LambdaAsParameter) {
    std::function<int(int, int)> func = [](int a, int b) { return a + b; };
    EXPECT_EQ(func(3, 4), 7);
}

// 测试 Lambda 闭包
TEST(Lambda, Closure) {
    auto create_adder = [](int base) {
        return [base](int x) { return base + x; };
    };

    auto add5 = create_adder(5);
    auto add10 = create_adder(10);

    EXPECT_EQ(add5(3), 8);
    EXPECT_EQ(add10(3), 13);
}

// 测试泛型 Lambda (C++14)
TEST(Lambda, GenericLambda) {
    auto generic_add = [](auto a, auto b) { return a + b; };

    EXPECT_EQ(generic_add(3, 4), 7);
    EXPECT_DOUBLE_EQ(generic_add(3.14, 2.86), 6.0);
}

// 测试 Lambda 与 STL 容器
TEST(Lambda, LambdaWithContainers) {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    // 转换
    std::vector<int> squared;
    std::transform(vec.begin(), vec.end(), std::back_inserter(squared),
        [](int n) { return n * n; });

    EXPECT_EQ(squared[0], 1);
    EXPECT_EQ(squared[4], 25);

    // 过滤
    std::vector<int> evens;
    std::copy_if(vec.begin(), vec.end(), std::back_inserter(evens),
        [](int n) { return n % 2 == 0; });

    EXPECT_EQ(evens.size(), 2);
    EXPECT_EQ(evens[0], 2);
    EXPECT_EQ(evens[1], 4);
}

// 测试 Lambda 与累积
TEST(Lambda, LambdaWithAccumulate) {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    int sum = std::accumulate(vec.begin(), vec.end(), 0,
        [](int acc, int n) { return acc + n; });

    EXPECT_EQ(sum, 15);
}

// 测试 mutable Lambda
TEST(Lambda, MutableLambda) {
    int count = 0;
    auto counter = [count]() mutable -> int {
        return ++count;
    };

    EXPECT_EQ(counter(), 1);
    EXPECT_EQ(counter(), 2);
    EXPECT_EQ(counter(), 3);
}

// 测试 Lambda 与字符串
TEST(Lambda, LambdaWithStrings) {
    std::vector<std::string> strings = {"Hello", "World", "C++"};

    std::sort(strings.begin(), strings.end(),
        [](const std::string& a, const std::string& b) {
            return a < b;
        });

    EXPECT_EQ(strings[0], "C++");
    EXPECT_EQ(strings[1], "Hello");
    EXPECT_EQ(strings[2], "World");
}
