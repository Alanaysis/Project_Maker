/**
 * 范围 for 循环测试
 */

#include <gtest/gtest.h>
#include <vector>
#include <list>
#include <map>
#include <set>
#include <string>

// 测试基本范围 for
TEST(RangeFor, Basic) {
    std::vector<int> vec = {1, 2, 3, 4, 5};
    int sum = 0;

    for (int val : vec) {
        sum += val;
    }

    EXPECT_EQ(sum, 15);
}

// 测试 auto 范围 for
TEST(RangeFor, Auto) {
    std::vector<int> vec = {1, 2, 3, 4, 5};
    int sum = 0;

    for (auto val : vec) {
        sum += val;
    }

    EXPECT_EQ(sum, 15);
}

// 测试引用范围 for
TEST(RangeFor, Reference) {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    for (auto& val : vec) {
        val *= 2;
    }

    EXPECT_EQ(vec[0], 2);
    EXPECT_EQ(vec[4], 10);
}

// 测试 const 引用范围 for
TEST(RangeFor, ConstReference) {
    std::vector<int> vec = {1, 2, 3, 4, 5};
    int sum = 0;

    for (const auto& val : vec) {
        sum += val;
    }

    EXPECT_EQ(sum, 15);
}

// 测试 list 范围 for
TEST(RangeFor, List) {
    std::list<int> list = {1, 2, 3, 4, 5};
    int sum = 0;

    for (int val : list) {
        sum += val;
    }

    EXPECT_EQ(sum, 15);
}

// 测试 map 范围 for
TEST(RangeFor, Map) {
    std::map<std::string, int> map = {
        {"one", 1}, {"two", 2}, {"three", 3}
    };

    int sum = 0;
    for (const auto& pair : map) {
        sum += pair.second;
    }

    EXPECT_EQ(sum, 6);
}

// 测试 set 范围 for
TEST(RangeFor, Set) {
    std::set<int> set = {1, 2, 3, 4, 5};
    int sum = 0;

    for (int val : set) {
        sum += val;
    }

    EXPECT_EQ(sum, 15);
}

// 测试数组范围 for
TEST(RangeFor, Array) {
    int arr[] = {1, 2, 3, 4, 5};
    int sum = 0;

    for (int val : arr) {
        sum += val;
    }

    EXPECT_EQ(sum, 15);
}

// 测试初始化列表范围 for
TEST(RangeFor, InitializerList) {
    int sum = 0;

    for (int val : {1, 2, 3, 4, 5}) {
        sum += val;
    }

    EXPECT_EQ(sum, 15);
}

// 测试字符串范围 for
TEST(RangeFor, String) {
    std::string str = "Hello";
    int count = 0;

    for (char c : str) {
        if (c != '\0') ++count;
    }

    EXPECT_EQ(count, 5);
}

// 测试嵌套范围 for
TEST(RangeFor, Nested) {
    std::vector<std::vector<int>> matrix = {
        {1, 2, 3},
        {4, 5, 6},
        {7, 8, 9}
    };

    int sum = 0;
    for (const auto& row : matrix) {
        for (int val : row) {
            sum += val;
        }
    }

    EXPECT_EQ(sum, 45);
}

// 测试自定义容器
class MyContainer {
    std::vector<int> data_;

public:
    MyContainer(std::initializer_list<int> init) : data_(init) {}
    auto begin() { return data_.begin(); }
    auto end() { return data_.end(); }
    auto begin() const { return data_.begin(); }
    auto end() const { return data_.end(); }
};

TEST(RangeFor, CustomContainer) {
    MyContainer container = {1, 2, 3, 4, 5};
    int sum = 0;

    for (int val : container) {
        sum += val;
    }

    EXPECT_EQ(sum, 15);
}

// 测试修改容器元素
TEST(RangeFor, ModifyElements) {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    for (auto& val : vec) {
        val = val * val;
    }

    EXPECT_EQ(vec[0], 1);
    EXPECT_EQ(vec[1], 4);
    EXPECT_EQ(vec[2], 9);
    EXPECT_EQ(vec[3], 16);
    EXPECT_EQ(vec[4], 25);
}

// 测试范围 for 与算法
TEST(RangeFor, WithAlgorithms) {
    std::vector<int> vec = {5, 2, 8, 1, 9, 3};
    std::vector<int> filtered;

    for (int val : vec) {
        if (val > 3) {
            filtered.push_back(val);
        }
    }

    EXPECT_EQ(filtered.size(), 3);
    EXPECT_EQ(filtered[0], 5);
    EXPECT_EQ(filtered[1], 8);
    EXPECT_EQ(filtered[2], 9);
}

// 测试范围 for 性能
TEST(RangeFor, Performance) {
    std::vector<std::string> strings = {"Hello", "World", "C++", "Modern"};

    // 使用 const 引用避免拷贝
    size_t total_length = 0;
    for (const auto& s : strings) {
        total_length += s.length();
    }

    EXPECT_EQ(total_length, 19);
}
