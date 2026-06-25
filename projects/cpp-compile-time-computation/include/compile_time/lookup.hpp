#pragma once
// lookup.hpp - 编译期查找表生成
//
// 在编译期生成数学函数的查找表，运行时直接查表，避免重复计算。
//
// 核心思想：
//   使用 constexpr 函数在编译期计算查找表的每个元素。
//   运行时通过数组索引直接获取结果，时间复杂度 O(1)。
//
// 使用示例：
//   constexpr auto sin_table = ct_lookup::make_table<360>([](int i) {
//       return ct_math::sin(i * pi / 180.0);
//   });
//   double sin_30 = sin_table[30];  // 运行时直接查表

#include <cstddef>
#include <cmath>
#include "array.hpp"
#include "math.hpp"

namespace compile_time {
namespace lookup {

// lookup_table: 编译期查找表
template<typename T, std::size_t N>
struct lookup_table {
    compile_time_array<T, N> data_;

    constexpr T operator[](std::size_t i) const {
        return data_[i];
    }

    constexpr T at(std::size_t i) const {
        if (i >= N) throw "Index out of range";
        return data_[i];
    }

    constexpr std::size_t size() const { return N; }

    // 线性插值
    constexpr T interpolate(double index) const {
        if (index < 0) return data_[0];
        if (index >= N - 1) return data_[N - 1];

        std::size_t i = static_cast<std::size_t>(index);
        double frac = index - i;
        return static_cast<T>(data_[i] * (1 - frac) + data_[i + 1] * frac);
    }

    // 查找最接近的值
    constexpr std::size_t find_nearest(T value) const {
        std::size_t best = 0;
        T best_diff = abs(data_[0] - value);
        for (std::size_t i = 1; i < N; ++i) {
            T diff = abs(data_[i] - value);
            if (diff < best_diff) {
                best_diff = diff;
                best = i;
            }
        }
        return best;
    }

    // 映射
    template<typename F>
    constexpr auto map(F func) const {
        return data_.map(func);
    }
};

// 辅助函数：查找表的绝对值
template<typename T>
constexpr T abs(T x) {
    return x < 0 ? -x : x;
}

// make_table: 使用函数对象生成查找表
template<std::size_t N, typename F>
constexpr auto make_table(F func) {
    lookup_table<decltype(func(0)), N> table;
    for (std::size_t i = 0; i < N; ++i) {
        table.data_[i] = func(i);
    }
    return table;
}

// make_table_with_range: 带范围的查找表
template<std::size_t N, typename F>
constexpr auto make_table_with_range(F func, double start, double end) {
    lookup_table<decltype(func(0.0)), N> table;
    double step = (end - start) / (N - 1);
    for (std::size_t i = 0; i < N; ++i) {
        table.data_[i] = func(start + i * step);
    }
    return table;
}

// 预定义的数学查找表

// 正弦表（0-359度）
constexpr auto make_sine_table() {
    return make_table<360>([](int i) {
        return math::sin(i * math::pi / 180.0);
    });
}

// 余弦表（0-359度）
constexpr auto make_cosine_table() {
    return make_table<360>([](int i) {
        return math::cos(i * math::pi / 180.0);
    });
}

// 正切表（0-89度，避免 90 度附近的无穷大）
constexpr auto make_tangent_table() {
    return make_table<90>([](int i) {
        return math::tan(i * math::pi / 180.0);
    });
}

// 平方表
template<std::size_t N>
constexpr auto make_square_table() {
    return make_table<N>([](int i) { return i * i; });
}

// 立方表
template<std::size_t N>
constexpr auto make_cube_table() {
    return make_table<N>([](int i) { return i * i * i; });
}

// 阶乘表
template<std::size_t N>
constexpr auto make_factorial_table() {
    compile_time_array<unsigned long long, N> table{};
    table[0] = 1;
    for (std::size_t i = 1; i < N; ++i) {
        table[i] = table[i - 1] * i;
    }
    return table;
}

// 斐波那契数列表
template<std::size_t N>
constexpr auto make_fibonacci_table() {
    compile_time_array<unsigned long long, N> table{};
    if (N > 0) table[0] = 0;
    if (N > 1) table[1] = 1;
    for (std::size_t i = 2; i < N; ++i) {
        table[i] = table[i - 1] + table[i - 2];
    }
    return table;
}

// 对数表（以 10 为底）
constexpr auto make_log10_table() {
    return make_table_with_range<100>([](double x) {
        return math::log10(x);
    }, 1.0, 10.0);
}

// 指数表
constexpr auto make_exp_table() {
    return make_table_with_range<100>([](double x) {
        return math::exp(x);
    }, 0.0, 5.0);
}

// 平方根表
constexpr auto make_sqrt_table() {
    return make_table_with_range<100>([](double x) {
        return math::sqrt(x);
    }, 0.0, 100.0);
}

// 二进制权重表（用于快速计算）
template<std::size_t N>
constexpr auto make_binary_weight_table() {
    compile_time_array<int, N> table{};
    for (std::size_t i = 0; i < N; ++i) {
        table[i] = 1 << i;
    }
    return table;
}

// ASCII 字符分类表
constexpr auto make_ascii_class_table() {
    // 0: 控制字符, 1: 数字, 2: 大写字母, 3: 小写字母, 4: 其他
    compile_time_array<int, 128> table{};
    for (int i = 0; i < 128; ++i) {
        if (i < 32 || i == 127) table[i] = 0;
        else if (i >= '0' && i <= '9') table[i] = 1;
        else if (i >= 'A' && i <= 'Z') table[i] = 2;
        else if (i >= 'a' && i <= 'z') table[i] = 3;
        else table[i] = 4;
    }
    return table;
}

} // namespace lookup
} // namespace compile_time
