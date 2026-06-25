/**
 * 05_spaceship_operator.cpp - C++20 三向比较运算符 <=>
 *
 * 三向比较运算符（太空船运算符）简化了比较操作的实现。
 *
 * 核心要点：
 * 1. operator<=> 自动生成所有比较运算符
 * 2. 三种比较类别：strong_ordering, weak_ordering, partial_ordering
 * 3. std::compare_three_way 默认比较器
 * 4. 与自定义类型的结合
 */

#include <iostream>
#include <string>
#include <vector>
#include <compare>
#include <algorithm>
#include <set>

// ============================================================
// 1. 基本三向比较
// ============================================================

struct Point {
    int x, y;

    // 使用 defaulted 自动生成所有比较运算符
    auto operator<=>(const Point&) const = default;

    // 注意：defaulted 的 <=> 会逐成员比较
    // 同时自动生成 == 和 != 运算符（C++20）
};

// ============================================================
// 2. 自定义比较逻辑
// ============================================================

struct Student {
    std::string name;
    int score;
    int age;

    // 按分数降序，分数相同按年龄升序
    std::strong_ordering operator<=>(const Student& other) const {
        if (auto cmp = other.score <=> score; cmp != 0) return cmp;
        return age <=> other.age;
    }

    // == 需要单独定义（除非使用 defaulted）
    bool operator==(const Student& other) const {
        return score == other.score && age == other.age;
    }
};

// ============================================================
// 3. weak_ordering 示例
// ============================================================

struct CaseInsensitiveString {
    std::string value;

    // 不区分大小写的比较 - weak_ordering
    // 因为不同字符串可能"等价"（如 "Hello" 和 "hello"）
    std::weak_ordering operator<=>(const CaseInsensitiveString& other) const {
        auto it1 = value.begin(), it2 = other.value.begin();
        while (it1 != value.end() && it2 != other.value.end()) {
            auto c1 = std::tolower(*it1);
            auto c2 = std::tolower(*it2);
            if (c1 < c2) return std::weak_ordering::less;
            if (c1 > c2) return std::weak_ordering::greater;
            ++it1; ++it2;
        }
        if (value.size() < other.value.size()) return std::weak_ordering::less;
        if (value.size() > other.value.size()) return std::weak_ordering::greater;
        return std::weak_ordering::equivalent;
    }

    bool operator==(const CaseInsensitiveString& other) const {
        return (*this <=> other) == 0;
    }
};

// ============================================================
// 4. partial_ordering 示例
// ============================================================

struct Measurement {
    double value;
    bool valid;

    // 部分排序 - 测量值可能无效
    std::partial_ordering operator<=>(const Measurement& other) const {
        if (!valid || !other.valid) return std::partial_ordering::unordered;
        return value <=> other.value;
    }

    bool operator==(const Measurement& other) const {
        if (!valid || !other.valid) return false;
        return value == other.value;
    }
};

// ============================================================
// 5. 继承中的三向比较
// ============================================================

struct Base {
    int id;
    auto operator<=>(const Base&) const = default;
};

struct Derived : Base {
    std::string name;
    // 不使用 defaulted <=> 因为 string 不支持 defaulted <=> 与 Base 组合
    std::strong_ordering operator<=>(const Derived& other) const {
        if (auto cmp = Base::operator<=>(other); cmp != 0) return cmp;
        return name <=> other.name;
    }
    bool operator==(const Derived& other) const {
        return id == other.id && name == other.name;
    }
};

// ============================================================
// 6. 嵌套类型比较
// ============================================================

struct Rectangle {
    Point top_left;
    Point bottom_right;

    auto operator<=>(const Rectangle&) const = default;
};

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 三向比较运算符 <=> 示例 ===\n\n";

    // 1. 基本比较
    std::cout << "【1. Point 基本比较】\n";
    Point p1{1, 2}, p2{3, 4}, p3{1, 2};
    std::cout << "(1,2) <=> (3,4): "
              << (p1 < p2 ? "less" : p1 > p2 ? "greater" : "equal") << "\n";
    std::cout << "(1,2) == (1,2): " << std::boolalpha << (p1 == p3) << "\n";
    std::cout << "(1,2) != (3,4): " << (p1 != p2) << "\n\n";

    // 2. Student 排序
    std::cout << "【2. Student 自定义排序】\n";
    std::vector<Student> students = {
        {"Alice", 85, 20}, {"Bob", 92, 19},
        {"Charlie", 85, 21}, {"Diana", 95, 20}
    };
    std::sort(students.begin(), students.end());
    for (const auto& s : students) {
        std::cout << "  " << s.name << " score=" << s.score << " age=" << s.age << "\n";
    }

    // 3. 不区分大小写比较
    std::cout << "\n【3. 不区分大小写字符串】\n";
    CaseInsensitiveString s1{"Hello"}, s2{"hello"}, s3{"World"};
    std::cout << "\"Hello\" == \"hello\": " << (s1 == s2) << "\n";
    std::cout << "\"Hello\" < \"World\": " << (s1 < s3) << "\n";

    // 使用 set 排序
    std::set<CaseInsensitiveString> word_set;
    word_set.insert({"apple"});
    word_set.insert({"APPLE"});  // 不会重复插入
    word_set.insert({"Banana"});
    std::cout << "set 大小（应为2）: " << word_set.size() << "\n";

    // 4. partial_ordering
    std::cout << "\n【4. Measurement 部分排序】\n";
    Measurement m1{3.14, true}, m2{2.71, true}, m3{0.0, false};
    std::cout << "3.14 > 2.71: " << (m1 > m2) << "\n";
    std::cout << "有效比较无效: " << ((m1 <=> m3) == std::partial_ordering::unordered ? "unordered" : "ordered") << "\n";

    // 5. 继承比较
    std::cout << "\n【5. 继承层次比较】\n";
    Derived d1{1, "Alice"}, d2{2, "Bob"};
    std::cout << "比较 Derived: " << (d1 < d2 ? "d1 < d2" : "d1 >= d2") << "\n";

    // 6. 嵌套类型
    std::cout << "\n【6. Rectangle 嵌套比较】\n";
    Rectangle r1{{0, 10}, {10, 0}}, r2{{0, 20}, {20, 0}};
    std::cout << "r1 < r2: " << (r1 < r2) << "\n";

    // 7. 三种排序类别总结
    std::cout << "\n【7. 三种比较类别】\n";
    std::cout << "strong_ordering - 严格全序（int, string）\n";
    std::cout << "  - less, equal, greater, equivalent\n";
    std::cout << "weak_ordering - 弱序（不区分大小写）\n";
    std::cout << "  - less, equivalent, greater\n";
    std::cout << "partial_ordering - 部分序（浮点NaN）\n";
    std::cout << "  - less, equivalent, greater, unordered\n";

    std::cout << "\n=== 三向比较示例完成 ===\n";
    return 0;
}
