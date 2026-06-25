/**
 * 初始化列表测试
 */

#include <gtest/gtest.h>
#include <vector>
#include <map>
#include <set>
#include <string>
#include <initializer_list>
#include <algorithm>

// 测试基本初始化列表
TEST(InitializerList, Basic) {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    EXPECT_EQ(vec.size(), 5);
    EXPECT_EQ(vec[0], 1);
    EXPECT_EQ(vec[4], 5);
}

// 测试空初始化列表
TEST(InitializerList, Empty) {
    std::vector<int> vec = {};

    EXPECT_EQ(vec.size(), 0);
}

// 测试 map 初始化列表
TEST(InitializerList, Map) {
    std::map<std::string, int> map = {
        {"one", 1},
        {"two", 2},
        {"three", 3}
    };

    EXPECT_EQ(map.size(), 3);
    EXPECT_EQ(map["one"], 1);
    EXPECT_EQ(map["two"], 2);
    EXPECT_EQ(map["three"], 3);
}

// 测试 set 初始化列表
TEST(InitializerList, Set) {
    std::set<int> set = {3, 1, 4, 1, 5, 9, 2, 6};

    EXPECT_EQ(set.size(), 7);  // 重复的 1 被去重
}

// 测试嵌套初始化列表
TEST(InitializerList, Nested) {
    std::vector<std::vector<int>> matrix = {
        {1, 2, 3},
        {4, 5, 6},
        {7, 8, 9}
    };

    EXPECT_EQ(matrix.size(), 3);
    EXPECT_EQ(matrix[0].size(), 3);
    EXPECT_EQ(matrix[0][0], 1);
    EXPECT_EQ(matrix[2][2], 9);
}

// 测试自定义类使用初始化列表
class MyVector {
    std::vector<int> data_;

public:
    MyVector(std::initializer_list<int> init) : data_(init) {}

    size_t size() const { return data_.size(); }
    int operator[](size_t i) const { return data_[i]; }
};

TEST(InitializerList, CustomClass) {
    MyVector vec = {1, 2, 3, 4, 5};

    EXPECT_EQ(vec.size(), 5);
    EXPECT_EQ(vec[0], 1);
    EXPECT_EQ(vec[4], 5);
}

// 测试初始化列表作为函数参数
void print_list(std::initializer_list<int> list) {
    // 只测试不崩溃
    (void)list;
}

TEST(InitializerList, FunctionParameter) {
    print_list({1, 2, 3, 4, 5});
    print_list({});
    print_list({42});
}

// 测试初始化列表与 auto
TEST(InitializerList, Auto) {
    auto vec = {1, 2, 3, 4, 5};

    EXPECT_EQ(vec.size(), 5);
}

// 测试初始化列表与赋值
TEST(InitializerList, Assignment) {
    std::vector<int> vec;
    vec = {1, 2, 3, 4, 5};

    EXPECT_EQ(vec.size(), 5);
    EXPECT_EQ(vec[0], 1);
}

// 测试初始化列表与 insert
TEST(InitializerList, Insert) {
    std::vector<int> vec = {1, 2, 5, 6};
    vec.insert(vec.begin() + 2, {3, 4});

    EXPECT_EQ(vec.size(), 6);
    EXPECT_EQ(vec[2], 3);
    EXPECT_EQ(vec[3], 4);
}

// 测试聚合初始化
struct Point {
    int x;
    int y;
    int z;
};

TEST(InitializerList, AggregateInitialization) {
    Point p = {1, 2, 3};

    EXPECT_EQ(p.x, 1);
    EXPECT_EQ(p.y, 2);
    EXPECT_EQ(p.z, 3);
}

// 测试嵌套聚合初始化
struct Line {
    Point start;
    Point end;
};

TEST(InitializerList, NestedAggregate) {
    Line line = {
        {0, 0, 0},
        {1, 1, 1}
    };

    EXPECT_EQ(line.start.x, 0);
    EXPECT_EQ(line.end.x, 1);
}

// 测试 initializer_list 特性
TEST(InitializerList, InitializerListProperties) {
    std::initializer_list<int> list = {1, 2, 3, 4, 5};

    EXPECT_EQ(list.size(), 5);
    EXPECT_EQ(*list.begin(), 1);
    EXPECT_EQ(*(list.end() - 1), 5);
}

// 测试初始化列表与算法
TEST(InitializerList, WithAlgorithms) {
    std::vector<int> vec = {3, 1, 4, 1, 5, 9, 2, 6};

    // 使用 minmax_element
    auto minmax = std::minmax_element(vec.begin(), vec.end());
    EXPECT_EQ(*minmax.first, 1);
    EXPECT_EQ(*minmax.second, 9);
}

// 测试初始化列表与字符串
TEST(InitializerList, Strings) {
    std::vector<std::string> vec = {"Hello", "World", "C++"};

    EXPECT_EQ(vec.size(), 3);
    EXPECT_EQ(vec[0], "Hello");
    EXPECT_EQ(vec[1], "World");
    EXPECT_EQ(vec[2], "C++");
}

// 测试初始化列表与混合类型
TEST(InitializerList, MixedTypes) {
    // 使用统一类型
    std::vector<double> vec = {1, 2.5, 3, 4.5, 5};

    EXPECT_EQ(vec.size(), 5);
    EXPECT_DOUBLE_EQ(vec[1], 2.5);
}
