/**
 * 10_no_unique_address.cpp - C++20 [[no_unique_address]] 属性
 *
 * 允许空成员不占用存储空间，实现 EBO (Empty Base Optimization) 的成员版本。
 *
 * 核心要点：
 * 1. 空类型的大小至少为 1（保证唯一地址）
 * 2. [[no_unique_address]] 允许与其他成员共享地址
 * 3. 适用于分配器、比较器等策略类
 * 4. 压缩存储，减少内存占用
 */

#include <iostream>
#include <string>
#include <memory>
#include <cstring>
#include <vector>
#include <algorithm>

// ============================================================
// 1. 空类型大小问题
// ============================================================

struct Empty {};

struct WithoutAttr {
    int value;
    Empty e;  // 空成员仍占 1 字节
};

struct WithAttr {
    int value;
    [[no_unique_address]] Empty e;  // 空成员不占额外空间
};

// ============================================================
// 2. 策略模式优化
// ============================================================

// 排序策略
struct Ascending {
    template <typename T>
    bool compare(const T& a, const T& b) const { return a < b; }
};

struct Descending {
    template <typename T>
    bool compare(const T& a, const T& b) const { return a > b; }
};

// 有状态的策略
struct Threshold {
    int limit;
    bool check(int val) const { return val > limit; }
};

template <typename Compare = Ascending>
class Sorter {
    [[no_unique_address]] Compare comp_;
public:
    template <typename Container>
    void sort(Container& c) const {
        // 使用策略进行排序
        for (size_t i = 0; i < c.size(); ++i) {
            for (size_t j = i + 1; j < c.size(); ++j) {
                if (!comp_.compare(c[i], c[j])) {
                    std::swap(c[i], c[j]);
                }
            }
        }
    }
};

// ============================================================
// 3. 分配器优化
// ============================================================

struct NullAllocator {
    void* allocate(size_t) { return nullptr; }
    void deallocate(void*, size_t) {}
};

template <typename T, typename Allocator = NullAllocator>
class SimpleVector {
    T* data_ = nullptr;
    size_t size_ = 0;
    size_t capacity_ = 0;
    [[no_unique_address]] Allocator alloc_;
public:
    size_t size() const { return size_; }
    size_t capacity() const { return capacity_; }
    Allocator& allocator() { return alloc_; }
};

// ============================================================
// 4. 压缩存储示例
// ============================================================

// 空标签类
struct TagA {};
struct TagB {};
struct TagC {};

struct Packed {
    [[no_unique_address]] TagA a;
    [[no_unique_address]] TagB b;
    [[no_unique_address]] TagC c;
    int value;
};

// ============================================================
// 5. 有状态和无状态混合
// ============================================================

template <typename Validator = void*>
struct Config {
    int max_retries;
    int timeout_ms;
    [[no_unique_address]] Validator validator;
};

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 [[no_unique_address]] 示例 ===\n\n";

    // 1. 大小对比
    std::cout << "【1. 大小对比】\n";
    std::cout << "sizeof(Empty) = " << sizeof(Empty) << "\n";
    std::cout << "sizeof(WithoutAttr) = " << sizeof(WithoutAttr)
              << " (Empty 成员占 1 字节, 需要 padding)\n";
    std::cout << "sizeof(WithAttr) = " << sizeof(WithAttr)
              << " (Empty 成员不占空间)\n";
    std::cout << "节省: " << sizeof(WithoutAttr) - sizeof(WithAttr) << " 字节\n\n";

    // 验证地址共享
    WithAttr wa{42, {}};
    std::cout << "&wa.value = " << (void*)&wa.value << "\n";
    std::cout << "&wa.e     = " << (void*)&wa.e << "\n";
    std::cout << "地址相同: " << std::boolalpha
              << ((void*)&wa.value == (void*)&wa.e) << "\n\n";

    // 2. 策略模式
    std::cout << "【2. 策略模式优化】\n";
    std::cout << "sizeof(Sorter<Ascending>) = " << sizeof(Sorter<Ascending>) << "\n";

    std::vector<int> nums2 = {5, 3, 1, 4, 2};
    Sorter<Ascending> sorter;
    sorter.sort(nums2);
    std::cout << "升序排序: ";
    for (auto n : nums2) std::cout << n << " ";
    std::cout << "\n\n";

    // 3. 分配器
    std::cout << "【3. 分配器优化】\n";
    std::cout << "sizeof(SimpleVector<int>) = " << sizeof(SimpleVector<int>) << "\n";
    std::cout << "sizeof(SimpleVector<int, NullAllocator>) = " << sizeof(SimpleVector<int, NullAllocator>) << "\n\n";

    // 4. 压缩存储
    std::cout << "【4. 多个空标签压缩】\n";
    std::cout << "sizeof(Packed) = " << sizeof(Packed) << " (只有 int 占空间)\n\n";

    // 5. 总结
    std::cout << "【5. 使用场景】\n";
    std::cout << "  - 空分配器 (std::allocator)\n";
    std::cout << "  - 空比较器 (std::less)\n";
    std::cout << "  - 策略模式中的无状态策略\n";
    std::cout << "  - 类型标签 (Tag Dispatch)\n";
    std::cout << "  - CRTP 中的空基类\n";

    std::cout << "\n=== [[no_unique_address]] 示例完成 ===\n";
    return 0;
}
