#pragma once
// map.hpp - 编译期映射实现
//
// 编译期映射是一个在编译期构建的键值对容器。
// 由于编译期不能使用堆内存，所有数据都存储在固定大小的数组中。
//
// 核心思想：
//   使用编译期数组存储键值对，通过线性查找实现映射。
//   对于小规模映射，线性查找的性能是可以接受的。
//
// 使用示例：
//   constexpr compile_time_map<int, const char*, 3> map = {
//       {{1, "one"}, {2, "two"}, {3, "three"}}
//   };
//   static_assert(map.at(1) == "one");

#include <cstddef>
#include <utility>
#include <optional>
#include "array.hpp"

namespace compile_time {

// pair: 编译期键值对
template<typename Key, typename Value>
struct pair {
    Key first;
    Value second;

    constexpr bool operator==(const pair& other) const {
        return first == other.first && second == other.second;
    }
};

// compile_time_map: 编译期映射
template<typename Key, typename Value, std::size_t N>
struct compile_time_map {
    compile_time_array<pair<Key, Value>, N> data_;

    // 访问元素（如果不存在则抛出编译期错误）
    constexpr Value& operator[](const Key& key) {
        for (auto& entry : data_) {
            if (entry.first == key) return entry.second;
        }
        throw "Key not found in compile_time_map";
    }

    constexpr const Value& at(const Key& key) const {
        for (const auto& entry : data_) {
            if (entry.first == key) return entry.second;
        }
        throw "Key not found in compile_time_map";
    }

    // 安全访问（返回 optional）
    constexpr std::optional<Value> try_at(const Key& key) const {
        for (const auto& entry : data_) {
            if (entry.first == key) return entry.second;
        }
        return std::nullopt;
    }

    // 查找
    constexpr bool contains(const Key& key) const {
        for (const auto& entry : data_) {
            if (entry.first == key) return true;
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

    // 键列表
    constexpr auto keys() const {
        compile_time_array<Key, N> result;
        for (std::size_t i = 0; i < N; ++i) {
            result[i] = data_[i].first;
        }
        return result;
    }

    // 值列表
    constexpr auto values() const {
        compile_time_array<Value, N> result;
        for (std::size_t i = 0; i < N; ++i) {
            result[i] = data_[i].second;
        }
        return result;
    }

    // 映射（转换值）
    template<typename F>
    constexpr auto map_values(F func) const {
        using NewValue = decltype(func(data_[0].second));
        compile_time_array<pair<Key, NewValue>, N> result;
        for (std::size_t i = 0; i < N; ++i) {
            result[i] = {data_[i].first, func(data_[i].second)};
        }
        return result;
    }

    // 比较操作
    template<std::size_t M>
    constexpr bool operator==(const compile_time_map<Key, Value, M>& other) const {
        if constexpr (N != M) return false;
        for (std::size_t i = 0; i < N; ++i) {
            if (data_[i] != other.data_[i]) return false;
        }
        return true;
    }

    template<std::size_t M>
    constexpr bool operator!=(const compile_time_map<Key, Value, M>& other) const {
        return !(*this == other);
    }
};

// 辅助函数：从数组构造 map
template<typename Key, typename Value, std::size_t N>
constexpr auto make_map(const pair<Key, Value>(&entries)[N]) {
    compile_time_map<Key, Value, N> result;
    for (std::size_t i = 0; i < N; ++i) {
        result.data_[i] = entries[i];
    }
    return result;
}

} // namespace compile_time
