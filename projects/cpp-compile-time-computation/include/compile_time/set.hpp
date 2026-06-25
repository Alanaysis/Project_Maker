#pragma once
// set.hpp - 编译期集合实现
//
// 编译期集合是一个在编译期构建的无序集合容器。
// 使用排序后的数组实现，支持高效的查找操作。
//
// 核心思想：
//   元素在构造时排序，查找时使用二分查找。
//   对于小规模集合，性能是可以接受的。
//
// 使用示例：
//   constexpr compile_time_set<int, 5> set = {1, 3, 5, 7, 9};
//   static_assert(set.contains(5));
//   static_assert(!set.contains(6));

#include <cstddef>
#include <algorithm>
#include "array.hpp"

namespace compile_time {

// compile_time_set: 编译期集合
template<typename T, std::size_t N>
struct compile_time_set {
    compile_time_array<T, N> data_;

    // 从初始化列表构造（自动排序）
    constexpr compile_time_set(const T (&arr)[N]) {
        for (std::size_t i = 0; i < N; ++i) {
            data_[i] = arr[i];
        }
        // 排序
        for (std::size_t i = 1; i < N; ++i) {
            T key = data_[i];
            std::size_t j = i;
            while (j > 0 && data_[j - 1] > key) {
                data_[j] = data_[j - 1];
                --j;
            }
            data_[j] = key;
        }
    }

    // 默认构造函数
    constexpr compile_time_set() = default;

    // 查找（二分查找）
    constexpr bool contains(const T& value) const {
        std::size_t left = 0, right = N;
        while (left < right) {
            std::size_t mid = left + (right - left) / 2;
            if (data_[mid] == value) return true;
            if (data_[mid] < value) left = mid + 1;
            else right = mid;
        }
        return false;
    }

    // 容量
    constexpr std::size_t size() const { return N; }
    constexpr bool empty() const { return N == 0; }

    // 迭代器
    constexpr auto begin() { return data_.begin(); }
    constexpr auto end() { return data_.end(); }
    constexpr auto begin() const { return data_.begin(); }
    constexpr auto end() const { return data_.end(); }

    // 元素访问
    constexpr const T& operator[](std::size_t i) const { return data_[i]; }
    constexpr const T& front() const { return data_.front(); }
    constexpr const T& back() const { return data_.back(); }

    // 集合操作：并集
    template<std::size_t M>
    constexpr auto union_with(const compile_time_set<T, M>& other) const {
        // 简化实现：合并两个数组并排序
        compile_time_array<T, N + M> merged;
        for (std::size_t i = 0; i < N; ++i) merged[i] = data_[i];
        for (std::size_t i = 0; i < M; ++i) merged[N + i] = other[i];
        auto sorted = merged.sorted();
        // 去重（简化实现，返回大小为 N+M 的数组）
        return sorted;
    }

    // 集合操作：交集
    template<std::size_t M>
    constexpr auto intersection_with(const compile_time_set<T, M>& other) const {
        // 简化实现：返回公共元素
        compile_time_array<T, (N < M ? N : M)> result;
        std::size_t count = 0;
        for (std::size_t i = 0; i < N; ++i) {
            if (other.contains(data_[i])) {
                result[count++] = data_[i];
            }
        }
        return result;
    }

    // 集合操作：差集
    template<std::size_t M>
    constexpr auto difference_with(const compile_time_set<T, M>& other) const {
        compile_time_array<T, N> result;
        std::size_t count = 0;
        for (std::size_t i = 0; i < N; ++i) {
            if (!other.contains(data_[i])) {
                result[count++] = data_[i];
            }
        }
        return result;
    }

    // 映射
    template<typename F>
    constexpr auto map(F func) const {
        using U = decltype(func(data_[0]));
        compile_time_set<U, N> result;
        for (std::size_t i = 0; i < N; ++i) {
            result.data_[i] = func(data_[i]);
        }
        // 重新排序
        for (std::size_t i = 1; i < N; ++i) {
            U key = result.data_[i];
            std::size_t j = i;
            while (j > 0 && result.data_[j - 1] > key) {
                result.data_[j] = result.data_[j - 1];
                --j;
            }
            result.data_[j] = key;
        }
        return result;
    }

    // 过滤（返回满足条件的元素数量）
    template<typename Pred>
    constexpr std::size_t count_if(Pred pred) const {
        std::size_t cnt = 0;
        for (std::size_t i = 0; i < N; ++i) {
            if (pred(data_[i])) ++cnt;
        }
        return cnt;
    }

    // 比较操作
    template<std::size_t M>
    constexpr bool operator==(const compile_time_set<T, M>& other) const {
        if constexpr (N != M) return false;
        for (std::size_t i = 0; i < N; ++i) {
            if (data_[i] != other.data_[i]) return false;
        }
        return true;
    }

    template<std::size_t M>
    constexpr bool operator!=(const compile_time_set<T, M>& other) const {
        return !(*this == other);
    }
};

// 辅助函数：从数组构造集合
template<typename T, std::size_t N>
constexpr auto make_set(const T (&arr)[N]) {
    return compile_time_set<T, N>(arr);
}

// 辅助函数：生成范围集合
template<std::size_t N>
constexpr auto make_range_set(int start = 0) {
    int arr[N];
    for (std::size_t i = 0; i < N; ++i) {
        arr[i] = start + static_cast<int>(i);
    }
    return compile_time_set<int, N>(arr);
}

} // namespace compile_time
