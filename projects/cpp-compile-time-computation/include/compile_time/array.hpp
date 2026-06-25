#pragma once
// array.hpp - 编译期数组实现
//
// 编译期数组是编译期计算的基础数据结构。它支持编译期的元素访问、
// 修改、排序、查找等操作。
//
// 核心思想：
//   使用 constexpr 函数和方法，使得所有操作都可以在编译期执行。
//   与 std::array 不同，compile_time_array 的所有方法都是 constexpr。
//
// 使用示例：
//   constexpr compile_time_array<int, 5> arr = {5, 3, 1, 4, 2};
//   constexpr auto sorted = arr.sorted();
//   static_assert(sorted[0] == 1);

#include <cstddef>
#include <algorithm>
#include <initializer_list>

namespace compile_time {

// compile_time_array: 编译期数组
template<typename T, std::size_t N>
struct compile_time_array {
    T data_[N]{};

    // 元素访问
    constexpr T& operator[](std::size_t i) { return data_[i]; }
    constexpr const T& operator[](std::size_t i) const { return data_[i]; }
    constexpr T& front() { return data_[0]; }
    constexpr const T& front() const { return data_[0]; }
    constexpr T& back() { return data_[N - 1]; }
    constexpr const T& back() const { return data_[N - 1]; }
    constexpr T* data() { return data_; }
    constexpr const T* data() const { return data_; }

    // 容量
    constexpr std::size_t size() const { return N; }
    constexpr bool empty() const { return N == 0; }

    // 迭代器
    constexpr T* begin() { return data_; }
    constexpr T* end() { return data_ + N; }
    constexpr const T* begin() const { return data_; }
    constexpr const T* end() const { return data_ + N; }

    // 填充
    constexpr void fill(const T& value) {
        for (std::size_t i = 0; i < N; ++i) {
            data_[i] = value;
        }
    }

    // 编译期排序（插入排序，对小数组高效）
    constexpr compile_time_array sorted() const {
        compile_time_array result = *this;
        for (std::size_t i = 1; i < N; ++i) {
            T key = result.data_[i];
            std::size_t j = i;
            while (j > 0 && result.data_[j - 1] > key) {
                result.data_[j] = result.data_[j - 1];
                --j;
            }
            result.data_[j] = key;
        }
        return result;
    }

    // 编译期排序（自定义比较函数）
    template<typename Compare>
    constexpr compile_time_array sorted(Compare comp) const {
        compile_time_array result = *this;
        for (std::size_t i = 1; i < N; ++i) {
            T key = result.data_[i];
            std::size_t j = i;
            while (j > 0 && comp(key, result.data_[j - 1])) {
                result.data_[j] = result.data_[j - 1];
                --j;
            }
            result.data_[j] = key;
        }
        return result;
    }

    // 编译期查找
    constexpr std::size_t find(const T& value) const {
        for (std::size_t i = 0; i < N; ++i) {
            if (data_[i] == value) return i;
        }
        return N;  // 未找到
    }

    // 编译期查找（自定义谓词）
    template<typename Pred>
    constexpr std::size_t find_if(Pred pred) const {
        for (std::size_t i = 0; i < N; ++i) {
            if (pred(data_[i])) return i;
        }
        return N;
    }

    // 编译期计数
    constexpr std::size_t count(const T& value) const {
        std::size_t cnt = 0;
        for (std::size_t i = 0; i < N; ++i) {
            if (data_[i] == value) ++cnt;
        }
        return cnt;
    }

    // 编译期累加
    constexpr T sum() const {
        T result = T{};
        for (std::size_t i = 0; i < N; ++i) {
            result += data_[i];
        }
        return result;
    }

    // 编译期最小值
    constexpr T min() const {
        T result = data_[0];
        for (std::size_t i = 1; i < N; ++i) {
            if (data_[i] < result) result = data_[i];
        }
        return result;
    }

    // 编译期最大值
    constexpr T max() const {
        T result = data_[0];
        for (std::size_t i = 1; i < N; ++i) {
            if (data_[i] > result) result = data_[i];
        }
        return result;
    }

    // 编译期反转
    constexpr compile_time_array reversed() const {
        compile_time_array result = *this;
        for (std::size_t i = 0; i < N / 2; ++i) {
            T tmp = result.data_[i];
            result.data_[i] = result.data_[N - 1 - i];
            result.data_[N - 1 - i] = tmp;
        }
        return result;
    }

    // 编译期映射（转换元素）
    template<typename F>
    constexpr auto map(F func) const {
        using U = decltype(func(data_[0]));
        compile_time_array<U, N> result;
        for (std::size_t i = 0; i < N; ++i) {
            result.data_[i] = func(data_[i]);
        }
        return result;
    }

    // 编译期过滤（返回满足条件的元素数量）
    template<typename Pred>
    constexpr std::size_t count_if(Pred pred) const {
        std::size_t cnt = 0;
        for (std::size_t i = 0; i < N; ++i) {
            if (pred(data_[i])) ++cnt;
        }
        return cnt;
    }

    // 编译期折叠（左折叠）
    template<typename F>
    constexpr T fold_left(F func, T init) const {
        for (std::size_t i = 0; i < N; ++i) {
            init = func(init, data_[i]);
        }
        return init;
    }

    // 编译期折叠（右折叠）
    template<typename F>
    constexpr T fold_right(F func, T init) const {
        for (std::size_t i = N; i > 0; --i) {
            init = func(data_[i - 1], init);
        }
        return init;
    }

    // 比较操作
    template<std::size_t M>
    constexpr bool operator==(const compile_time_array<T, M>& other) const {
        if constexpr (N != M) return false;
        for (std::size_t i = 0; i < N; ++i) {
            if (data_[i] != other.data_[i]) return false;
        }
        return true;
    }

    template<std::size_t M>
    constexpr bool operator!=(const compile_time_array<T, M>& other) const {
        return !(*this == other);
    }

    template<std::size_t M>
    constexpr bool operator<(const compile_time_array<T, M>& other) const {
        for (std::size_t i = 0; i < N && i < M; ++i) {
            if (data_[i] < other.data_[i]) return true;
            if (data_[i] > other.data_[i]) return false;
        }
        return N < M;
    }
};

// 辅助函数：从初始化列表构造
template<typename T, std::size_t N>
constexpr compile_time_array<T, N> make_array(const T (&arr)[N]) {
    compile_time_array<T, N> result;
    for (std::size_t i = 0; i < N; ++i) {
        result[i] = arr[i];
    }
    return result;
}

// 辅助函数：生成等差数列
template<typename T, std::size_t N>
constexpr auto iota(T start = T{}, T step = T{1}) {
    compile_time_array<T, N> result;
    T value = start;
    for (std::size_t i = 0; i < N; ++i) {
        result[i] = value;
        value += step;
    }
    return result;
}

// 编译期数组拼接
template<typename T, std::size_t N, std::size_t M>
constexpr auto concat(const compile_time_array<T, N>& a,
                      const compile_time_array<T, M>& b) {
    compile_time_array<T, N + M> result;
    for (std::size_t i = 0; i < N; ++i) {
        result[i] = a[i];
    }
    for (std::size_t i = 0; i < M; ++i) {
        result[N + i] = b[i];
    }
    return result;
}

} // namespace compile_time
