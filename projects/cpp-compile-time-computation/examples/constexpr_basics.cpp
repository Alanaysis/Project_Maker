// constexpr_basics.cpp - constexpr 基础示例
//
// 本文件展示 C++ constexpr 的基本用法，包括：
//   1. constexpr 函数
//   2. constexpr 变量
//   3. constexpr 类
//   4. C++11/14/17/20 的演进
//
// 编译命令：
//   g++ -std=c++20 examples/constexpr_basics.cpp -o constexpr_basics

#include <iostream>
#include <array>
#include <type_traits>

// ============================================================================
// 第一部分：constexpr 函数
// ============================================================================

// C++11: constexpr 函数只能有一条 return 语句
constexpr int factorial_cpp11(int n) {
    return (n <= 1) ? 1 : n * factorial_cpp11(n - 1);
}

// C++14: 允许局部变量、循环和条件分支
constexpr long long factorial_cpp14(int n) {
    long long result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

// C++17: constexpr if
template<typename T>
constexpr auto absolute(T value) {
    if constexpr (std::is_unsigned_v<T>) {
        return value;  // 无符号数不需要取绝对值
    } else {
        return value < 0 ? -value : value;
    }
}

// C++20: constexpr lambda
constexpr auto square = [](int x) { return x * x; };
constexpr auto cube = [](int x) { return x * x * x; };

// ============================================================================
// 第二部分：constexpr 变量
// ============================================================================

// 编译期常量
constexpr int MAX_SIZE = 100;
constexpr double PI = 3.14159265358979323846;
constexpr const char* GREETING = "Hello, Compile-Time!";

// 编译期数组
constexpr int FIBONACCI[] = {0, 1, 1, 2, 3, 5, 8, 13, 21, 34};

// ============================================================================
// 第三部分：constexpr 类
// ============================================================================

// 二维点
struct Point {
    double x, y;

    constexpr Point() : x(0), y(0) {}
    constexpr Point(double x, double y) : x(x), y(y) {}

    constexpr double distance_to(const Point& other) const {
        double dx = x - other.x;
        double dy = y - other.y;
        // 简单的平方根近似（编译期不能调用 std::sqrt）
        double sum = dx * dx + dy * dy;
        double guess = sum / 2.0;
        for (int i = 0; i < 20; ++i) {
            guess = (guess + sum / guess) / 2.0;
        }
        return guess;
    }

    constexpr double distance_squared() const {
        return x * x + y * y;
    }

    constexpr Point operator+(const Point& other) const {
        return {x + other.x, y + other.y};
    }

    constexpr Point operator-(const Point& other) const {
        return {x - other.x, y - other.y};
    }

    constexpr bool operator==(const Point& other) const {
        return x == other.x && y == other.y;
    }
};

// 编译期向量
template<typename T, std::size_t N>
struct ConstExprVector {
    T data[N]{};
    std::size_t size_ = 0;

    constexpr void push_back(const T& value) {
        if (size_ < N) {
            data[size_++] = value;
        }
    }

    constexpr T& operator[](std::size_t i) { return data[i]; }
    constexpr const T& operator[](std::size_t i) const { return data[i]; }
    constexpr std::size_t size() const { return size_; }
    constexpr bool empty() const { return size_ == 0; }

    constexpr T& front() { return data[0]; }
    constexpr T& back() { return data[size_ - 1]; }

    constexpr void clear() { size_ = 0; }

    constexpr void insert(std::size_t pos, const T& value) {
        if (size_ < N) {
            for (std::size_t i = size_; i > pos; --i) {
                data[i] = data[i - 1];
            }
            data[pos] = value;
            ++size_;
        }
    }

    constexpr void erase(std::size_t pos) {
        if (pos < size_) {
            for (std::size_t i = pos; i < size_ - 1; ++i) {
                data[i] = data[i + 1];
            }
            --size_;
        }
    }
};

// ============================================================================
// 第四部分：编译期算法
// ============================================================================

// 编译期二分查找
constexpr int binary_search(const int* arr, int size, int target) {
    int left = 0, right = size - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}

// 编译期快速排序（简化版）
constexpr void quick_sort(int* arr, int left, int right) {
    if (left >= right) return;

    int pivot = arr[right];
    int i = left - 1;

    for (int j = left; j < right; ++j) {
        if (arr[j] <= pivot) {
            ++i;
            int temp = arr[i];
            arr[i] = arr[j];
            arr[j] = temp;
        }
    }

    int temp = arr[i + 1];
    arr[i + 1] = arr[right];
    arr[right] = temp;

    int pivot_pos = i + 1;
    quick_sort(arr, left, pivot_pos - 1);
    quick_sort(arr, pivot_pos + 1, right);
}

// ============================================================================
// 第五部分：编译期断言验证
// ============================================================================

// 验证 constexpr 函数
static_assert(factorial_cpp11(5) == 120);
static_assert(factorial_cpp14(5) == 120);
static_assert(factorial_cpp11(10) == 3628800LL);
static_assert(factorial_cpp14(10) == 3628800LL);

// 验证 constexpr if
static_assert(absolute(-5) == 5);
static_assert(absolute(5u) == 5u);

// 验证 constexpr lambda
static_assert(square(5) == 25);
static_assert(cube(3) == 27);

// 验证 constexpr 变量
static_assert(MAX_SIZE == 100);
static_assert(PI > 3.14 && PI < 3.15);
static_assert(FIBONACCI[7] == 13);

// 验证 constexpr 类
constexpr Point p1(0, 0);
constexpr Point p2(3, 4);
constexpr double dist_sq = p2.distance_squared();
static_assert(dist_sq == 25.0);

constexpr Point p3 = p1 + p2;
static_assert(p3 == Point(3, 4));

// 验证编译期向量
constexpr auto test_vector() {
    ConstExprVector<int, 10> vec;
    vec.push_back(1);
    vec.push_back(2);
    vec.push_back(3);
    return vec.size();
}
static_assert(test_vector() == 3);

// 验证编译期算法
constexpr int sorted_arr[] = {1, 3, 5, 7, 9, 11, 13, 15};
static_assert(binary_search(sorted_arr, 8, 7) == 3);
static_assert(binary_search(sorted_arr, 8, 10) == -1);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== C++ constexpr 基础示例 ===" << std::endl;
    std::cout << std::endl;

    // constexpr 函数
    std::cout << "1. constexpr 函数:" << std::endl;
    std::cout << "   factorial(5) = " << factorial_cpp14(5) << std::endl;
    std::cout << "   factorial(10) = " << factorial_cpp14(10) << std::endl;
    std::cout << "   absolute(-42) = " << absolute(-42) << std::endl;
    std::cout << "   square(7) = " << square(7) << std::endl;
    std::cout << "   cube(4) = " << cube(4) << std::endl;
    std::cout << std::endl;

    // constexpr 变量
    std::cout << "2. constexpr 变量:" << std::endl;
    std::cout << "   MAX_SIZE = " << MAX_SIZE << std::endl;
    std::cout << "   PI = " << PI << std::endl;
    std::cout << "   FIBONACCI[7] = " << FIBONACCI[7] << std::endl;
    std::cout << std::endl;

    // constexpr 类
    std::cout << "3. constexpr 类:" << std::endl;
    std::cout << "   Point(3,4).distance_squared() = " << p2.distance_squared() << std::endl;
    std::cout << "   p1 + p2 = (" << p3.x << ", " << p3.y << ")" << std::endl;
    std::cout << std::endl;

    // 编译期算法
    std::cout << "4. 编译期算法:" << std::endl;
    std::cout << "   binary_search({1,3,5,7,9,11,13,15}, 7) = "
              << binary_search(sorted_arr, 8, 7) << std::endl;
    std::cout << std::endl;

    // 运行时使用 constexpr 函数
    std::cout << "5. 运行时使用 constexpr 函数:" << std::endl;
    int n = 15;
    std::cout << "   factorial(" << n << ") = " << factorial_cpp14(n) << std::endl;
    std::cout << std::endl;

    // 编译期 vs 运行时
    std::cout << "6. 编译期 vs 运行时:" << std::endl;
    constexpr long long compile_time_result = factorial_cpp14(20);
    long long runtime_result = factorial_cpp14(20);
    std::cout << "   编译期: factorial(20) = " << compile_time_result << std::endl;
    std::cout << "   运行时: factorial(20) = " << runtime_result << std::endl;
    std::cout << "   结果相同: " << (compile_time_result == runtime_result ? "是" : "否") << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
