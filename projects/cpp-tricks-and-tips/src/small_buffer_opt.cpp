/**
 * small_buffer_opt.cpp - 小缓冲区优化 (Small Buffer Optimization, SBO)
 *
 * 本文件演示了小缓冲区优化的原理和实现，包括：
 *   1. SBO 的基本原理：在对象内部嵌入小缓冲区，避免堆分配
 *   2. 一个简单的 SBO 容器实现
 *   3. 何时触发堆分配
 *   4. 性能对比
 *
 * 编译: g++ -std=c++17 -O2 -o small_buffer_opt small_buffer_opt.cpp
 *
 * SBO 的核心思想：
 *   对于小对象，栈上分配比堆上分配快得多（无需系统调用，缓存友好）。
 *   SBO 在容器内部预留一块固定大小的缓冲区，
 *   当数据量小于等于缓冲区大小时，直接使用内部缓冲区；
 *   当数据量超过缓冲区大小时，才切换到堆分配。
 *
 * 典型应用：
 *   - std::string 的短字符串优化 (SSO)
 *   - folly::small_vector
 *   - LLVM 的 SmallVector
 *   - 各种嵌入式系统中的容器
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <cstring>
#include <algorithm>
#include <type_traits>
#include <cassert>
#include <iomanip>
#include <new>      // std::bad_alloc
#include <memory>   // std::destroy_at

// ============================================================================
// 第一部分：SmallBuffer - 小缓冲区优化容器
// ============================================================================

/**
 * SmallBuffer - 小缓冲区优化的动态数组
 *
 * 模板参数:
 *   T           - 元素类型
 *   N           - 内部缓冲区能容纳的元素个数（默认 16）
 *   Allocator   - 堆分配时使用的分配器类型
 *
 * 设计要点:
 *   1. 使用 union 存储内部缓冲区和堆指针，节省空间
 *   2. 使用对齐存储确保类型安全
 *   3. 提供与 std::vector 兼容的接口
 */
template <typename T, std::size_t N = 16, typename Allocator = std::allocator<T>>
class SmallBuffer {
public:
    using value_type = T;
    using size_type = std::size_t;
    using reference = T&;
    using const_reference = const T&;
    using pointer = T*;
    using const_pointer = const T*;
    using iterator = T*;
    using const_iterator = const T*;

    // 默认构造：使用内部缓冲区
    SmallBuffer() : size_(0), capacity_(N), use_heap_(false) {
        // 使用 aligned storage 作为内部缓冲区
        // 确保满足类型 T 的对齐要求
    }

    // 析构函数
    ~SmallBuffer() {
        destroy_all();
        if (use_heap_) {
            Allocator alloc;
            alloc.deallocate(heap_data_, capacity_);
        }
    }

    // 拷贝构造
    SmallBuffer(const SmallBuffer& other) : size_(0), capacity_(N), use_heap_(false) {
        if (other.use_heap_) {
            // 源使用堆，我们也需要堆
            ensure_capacity(other.size_);
        }
        // 拷贝所有元素
        for (size_type i = 0; i < other.size_; ++i) {
            new (data() + i) T(other[i]);
            size_++;
        }
    }

    // 拷贝赋值
    SmallBuffer& operator=(const SmallBuffer& other) {
        if (this == &other) return *this;

        // 先销毁现有内容
        destroy_all();

        if (other.size_ > capacity_) {
            // 需要更大的空间
            if (use_heap_) {
                Allocator alloc;
                alloc.deallocate(heap_data_, capacity_);
            }
            capacity_ = other.size_;
            Allocator alloc;
            heap_data_ = alloc.allocate(capacity_);
            use_heap_ = true;
        }

        size_ = 0;
        for (size_type i = 0; i < other.size_; ++i) {
            new (data() + i) T(other[i]);
            size_++;
        }
        return *this;
    }

    // 移动构造
    SmallBuffer(SmallBuffer&& other) noexcept
        : size_(other.size_), capacity_(other.capacity_), use_heap_(other.use_heap_) {
        if (use_heap_) {
            // 堆模式：直接接管指针
            heap_data_ = other.heap_data_;
            other.heap_data_ = nullptr;
        } else {
            // 内部缓冲区模式：逐个移动元素
            for (size_type i = 0; i < size_; ++i) {
                new (local_buffer() + i) T(std::move(other[i]));
            }
        }
        other.size_ = 0;
    }

    // 移动赋值
    SmallBuffer& operator=(SmallBuffer&& other) noexcept {
        if (this == &other) return *this;

        destroy_all();
        if (use_heap_) {
            Allocator alloc;
            alloc.deallocate(heap_data_, capacity_);
        }

        size_ = other.size_;
        capacity_ = other.capacity_;
        use_heap_ = other.use_heap_;

        if (use_heap_) {
            heap_data_ = other.heap_data_;
            other.heap_data_ = nullptr;
        } else {
            for (size_type i = 0; i < size_; ++i) {
                new (local_buffer() + i) T(std::move(other[i]));
            }
        }
        other.size_ = 0;
        return *this;
    }

    /**
     * push_back - 在末尾添加元素
     *
     * 如果当前 size < N，使用内部缓冲区（O(1)，无堆分配）
     * 如果当前 size >= N，切换到堆分配（如果还没切换的话）
     */
    void push_back(const T& value) {
        ensure_capacity(size_ + 1);
        new (data() + size_) T(value);
        size_++;
    }

    void push_back(T&& value) {
        ensure_capacity(size_ + 1);
        new (data() + size_) T(std::move(value));
        size_++;
    }

    // 原地构造
    template <typename... Args>
    reference emplace_back(Args&&... args) {
        ensure_capacity(size_ + 1);
        new (data() + size_) T(std::forward<Args>(args)...);
        return data()[size_++];
    }

    // 弹出最后一个元素
    void pop_back() {
        assert(size_ > 0);
        size_--;
        std::destroy_at(data() + size_);
    }

    // 访问元素
    reference operator[](size_type i) { return data()[i]; }
    const_reference operator[](size_type i) const { return data()[i]; }

    reference front() { return data()[0]; }
    const_reference front() const { return data()[0]; }
    reference back() { return data()[size_ - 1]; }
    const_reference back() const { return data()[size_ - 1]; }

    // 容量信息
    size_type size() const { return size_; }
    size_type capacity() const { return capacity_; }
    bool empty() const { return size_ == 0; }
    bool is_using_heap() const { return use_heap_; }

    /**
     * small_capacity - 返回内部缓冲区的容量
     * 这是 SBO 的核心参数
     */
    static constexpr size_type small_capacity() { return N; }

    // 迭代器
    iterator begin() { return data(); }
    iterator end() { return data() + size_; }
    const_iterator begin() const { return data(); }
    const_iterator end() const { return data() + size_; }

    // 预留空间
    void reserve(size_type new_cap) {
        if (new_cap > capacity_) {
            ensure_capacity(new_cap);
        }
    }

    // 清空
    void clear() {
        destroy_all();
        size_ = 0;
    }

    // 获取当前存储状态的描述
    const char* storage_mode() const {
        return use_heap_ ? "堆存储 (Heap)" : "本地缓冲区 (Local Buffer)";
    }

private:
    /**
     * data() - 获取数据指针
     *
     * 根据当前模式返回内部缓冲区或堆内存的指针
     */
    T* data() {
        return use_heap_ ? heap_data_ : local_buffer();
    }

    const T* data() const {
        return use_heap_ ? heap_data_ : local_buffer();
    }

    /**
     * local_buffer() - 获取内部缓冲区的指针
     *
     * 使用 std::aligned_storage 确保对齐正确
     * alignof(T) 保证满足 T 的对齐要求
     */
    T* local_buffer() {
        return reinterpret_cast<T*>(&buffer_);
    }

    const T* local_buffer() const {
        return reinterpret_cast<const T*>(&buffer_);
    }

    /**
     * ensure_capacity - 确保有足够的容量
     *
     * 这是 SBO 的核心逻辑：
     *   - 如果 new_size <= 当前容量，什么都不做
     *   - 如果 new_size > N 且当前使用内部缓冲区，切换到堆
     *   - 如果 new_size > 当前堆容量，重新分配更大的堆
     */
    void ensure_capacity(size_type new_size) {
        if (new_size <= capacity_) {
            return;  // 容量足够
        }

        // 需要更多空间
        size_type new_cap = std::max(new_size, capacity_ * 2);

        if (!use_heap_) {
            // 从内部缓冲区切换到堆
            Allocator alloc;
            T* new_data = alloc.allocate(new_cap);

            // 将现有元素移动到新内存
            for (size_type i = 0; i < size_; ++i) {
                new (new_data + i) T(std::move(local_buffer()[i]));
                std::destroy_at(local_buffer() + i);
            }

            heap_data_ = new_data;
            use_heap_ = true;
            capacity_ = new_cap;
        } else {
            // 已经在堆上，重新分配更大的空间
            Allocator alloc;
            T* new_data = alloc.allocate(new_cap);

            // 移动现有元素
            for (size_type i = 0; i < size_; ++i) {
                new (new_data + i) T(std::move(heap_data_[i]));
                std::destroy_at(&heap_data_[i]);
            }

            alloc.deallocate(heap_data_, capacity_);
            heap_data_ = new_data;
            capacity_ = new_cap;
        }
    }

    // 销毁所有元素
    void destroy_all() {
        T* p = data();
        for (size_type i = 0; i < size_; ++i) {
            std::destroy_at(p + i);
        }
    }

    size_type size_;       // 当前元素个数
    size_type capacity_;   // 当前容量
    bool use_heap_;        // 是否使用堆内存

    // 使用 union 实现双模式存储
    // aligned_storage 确保内部缓冲区满足 T 的对齐要求
    union {
        std::aligned_storage_t<sizeof(T) * N, alignof(T)> buffer_;  // 内部缓冲区
        T* heap_data_;   // 堆内存指针（与 buffer_ 共用空间）
    };
};

// ============================================================================
// 第二部分：性能对比测试
// ============================================================================

class Timer {
public:
    using Clock = std::chrono::high_resolution_clock;
    void start() { start_ = Clock::now(); }
    double elapsed_ms() const {
        return std::chrono::duration<double, std::milli>(Clock::now() - start_).count();
    }
private:
    Clock::time_point start_;
};

void print_section(const char* title) {
    std::cout << "\n========================================\n"
              << title << "\n"
              << "========================================\n";
}

int main() {
    std::cout << "===== 小缓冲区优化 (SBO) 演示 =====\n";

    // ---- 演示 1: 基本使用和存储模式切换 ----
    print_section("1. 基本使用和存储模式切换");

    {
        // SmallBuffer<int, 8> 内部缓冲区可以容纳 8 个 int
        SmallBuffer<int, 8> buf;

        std::cout << "内部缓冲区容量: " << SmallBuffer<int, 8>::small_capacity() << "\n\n";

        // 添加元素，观察存储模式
        for (int i = 0; i < 12; ++i) {
            buf.push_back(i);
            std::cout << "size=" << buf.size()
                      << " capacity=" << buf.capacity()
                      << " mode=" << buf.storage_mode() << "\n";
        }

        std::cout << "\n最终内容: ";
        for (const auto& v : buf) {
            std::cout << v << " ";
        }
        std::cout << "\n";

        std::cout << "\n关键观察:\n"
                  << "  - 前 8 个元素使用内部缓冲区（无堆分配）\n"
                  << "  - 第 9 个元素触发切换到堆分配\n"
                  << "  - 切换时原元素被移动到堆上\n";
    }

    // ---- 演示 2: 移动语义与 SBO ----
    print_section("2. 移动语义与 SBO");

    {
        SmallBuffer<std::string, 4> buf;

        // 使用 emplace_back 原地构造
        buf.emplace_back("Hello");
        buf.emplace_back("World");
        buf.emplace_back("SBO");
        buf.emplace_back("优化");

        std::cout << "内部缓冲区模式 (4 个字符串):\n";
        std::cout << "  mode=" << buf.storage_mode() << "\n";
        for (const auto& s : buf) {
            std::cout << "  \"" << s << "\"\n";
        }

        // 添加第 5 个，触发堆分配
        buf.emplace_back("触发堆分配");

        std::cout << "\n添加第 5 个后:\n";
        std::cout << "  mode=" << buf.storage_mode() << "\n";
        for (const auto& s : buf) {
            std::cout << "  \"" << s << "\"\n";
        }

        // 移动构造：内部缓冲区内容逐个移动
        SmallBuffer<std::string, 4> buf2 = std::move(buf);
        std::cout << "\n移动后:\n";
        std::cout << "  原对象 size=" << buf.size() << "\n";
        std::cout << "  新对象 size=" << buf2.size() << "\n";
    }

    // ---- 演示 3: 性能对比 ----
    print_section("3. 性能对比: SBO vs std::vector");

    Timer timer;
    const int ITERATIONS = 1000000;

    // 测试 1: 小规模（在 SBO 缓冲区内）
    {
        double sbo_time, vec_time;

        // SBO 版本 - 元素数量在内部缓冲区范围内
        {
            timer.start();
            for (int i = 0; i < ITERATIONS; ++i) {
                SmallBuffer<int, 16> buf;
                for (int j = 0; j < 10; ++j) {
                    buf.push_back(j);
                }
                // buf 在此析构
            }
            sbo_time = timer.elapsed_ms();
        }

        // std::vector 版本
        {
            timer.start();
            for (int i = 0; i < ITERATIONS; ++i) {
                std::vector<int> vec;
                for (int j = 0; j < 10; ++j) {
                    vec.push_back(j);
                }
            }
            vec_time = timer.elapsed_ms();
        }

        std::cout << "小规模测试 (" << ITERATIONS << " 次，每次 10 个元素):\n";
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "  SBO:         " << sbo_time << " ms\n";
        std::cout << "  std::vector: " << vec_time << " ms\n";
        std::cout << "  性能提升:    " << (vec_time / sbo_time) << "x\n\n";
    }

    // 测试 2: 中等规模（刚好超出 SBO 缓冲区）
    {
        double sbo_time, vec_time;

        {
            timer.start();
            for (int i = 0; i < ITERATIONS / 10; ++i) {
                SmallBuffer<int, 8> buf;
                for (int j = 0; j < 20; ++j) {
                    buf.push_back(j);
                }
            }
            sbo_time = timer.elapsed_ms();
        }

        {
            timer.start();
            for (int i = 0; i < ITERATIONS / 10; ++i) {
                std::vector<int> vec;
                for (int j = 0; j < 20; ++j) {
                    vec.push_back(j);
                }
            }
            vec_time = timer.elapsed_ms();
        }

        std::cout << "中等规模测试 (" << ITERATIONS / 10 << " 次，每次 20 个元素，SBO 容量 8):\n";
        std::cout << "  SBO:         " << sbo_time << " ms\n";
        std::cout << "  std::vector: " << vec_time << " ms\n";
        std::cout << "  性能提升:    " << (vec_time / sbo_time) << "x\n\n";
    }

    // 测试 3: 纯内部缓冲区场景（不触发堆分配）
    {
        double sbo_time, vec_time;

        {
            timer.start();
            for (int i = 0; i < ITERATIONS; ++i) {
                SmallBuffer<int, 16> buf;
                for (int j = 0; j < 16; ++j) {
                    buf.push_back(j);
                }
            }
            sbo_time = timer.elapsed_ms();
        }

        {
            timer.start();
            for (int i = 0; i < ITERATIONS; ++i) {
                std::vector<int> vec;
                vec.reserve(16);
                for (int j = 0; j < 16; ++j) {
                    vec.push_back(j);
                }
            }
            vec_time = timer.elapsed_ms();
        }

        std::cout << "纯缓冲区测试 (" << ITERATIONS << " 次，每次 16 个元素，刚好填满):\n";
        std::cout << "  SBO:         " << sbo_time << " ms\n";
        std::cout << "  std::vector: " << vec_time << " ms\n";
        std::cout << "  性能提升:    " << (vec_time / sbo_time) << "x\n";
    }

    // ---- 演示 4: 不同类型的 SBO 效果 ----
    print_section("4. 不同类型的 SBO 效果");

    {
        std::cout << "sizeof 和 SBO 容量的关系:\n\n";

        // 小类型：可以放更多在内部缓冲区
        std::cout << "int:\n"
                  << "  sizeof = " << sizeof(int) << " 字节\n"
                  << "  SmallBuffer<int, 32> 内部缓冲区 = "
                  << sizeof(SmallBuffer<int, 32>) << " 字节\n"
                  << "  实际可容纳 = " << SmallBuffer<int, 32>::small_capacity() << " 个\n\n";

        // 中等类型
        std::cout << "std::string:\n"
                  << "  sizeof = " << sizeof(std::string) << " 字节\n"
                  << "  SmallBuffer<std::string, 8> 内部缓冲区 = "
                  << sizeof(SmallBuffer<std::string, 8>) << " 字节\n"
                  << "  实际可容纳 = " << SmallBuffer<std::string, 8>::small_capacity() << " 个\n\n";

        // 大类型：SBO 可能不划算
        struct LargeType { char data[256]; };
        std::cout << "LargeType (256 bytes):\n"
                  << "  sizeof = " << sizeof(LargeType) << " 字节\n"
                  << "  SmallBuffer<LargeType, 4> 总大小 = "
                  << sizeof(SmallBuffer<LargeType, 4>) << " 字节\n"
                  << "  实际可容纳 = " << SmallBuffer<LargeType, 4>::small_capacity() << " 个\n"
                  << "  注意: 大类型使用 SBO 可能浪费栈空间\n";
    }

    // ---- 演示 5: emplace_back 和完美转发 ----
    print_section("5. emplace_back 和完美转发");

    {
        struct Widget {
            int id;
            std::string name;
            std::vector<double> data;

            Widget(int i, std::string n, std::vector<double> d)
                : id(i), name(std::move(n)), data(std::move(d)) {
                std::cout << "  Widget 构造: id=" << id << " name=" << name << "\n";
            }

            ~Widget() {
                std::cout << "  Widget 析构: id=" << id << "\n";
            }
        };

        SmallBuffer<Widget, 4> widgets;

        std::cout << "emplace_back 直接在容器内存中构造对象:\n";
        widgets.emplace_back(1, "小部件A", std::vector<double>{1.0, 2.0});
        widgets.emplace_back(2, "小部件B", std::vector<double>{3.0, 4.0});

        std::cout << "\n当前 " << widgets.size() << " 个 widget，"
                  << "存储模式: " << widgets.storage_mode() << "\n";
    }

    // ---- 演示 6: SBO 的最佳实践 ----
    print_section("6. SBO 最佳实践");

    std::cout <<
        "SBO 使用建议:\n\n"
        "1. 选择合适的 N 值:\n"
        "   - N 太小: 频繁触发堆分配，失去优化意义\n"
        "   - N 太大: 浪费栈空间，对象拷贝/移动开销增大\n"
        "   - 经验法则: N = 典型使用场景的 80th 百分位数\n\n"
        "2. 适用场景:\n"
        "   - 元素数量通常较少（如路径、配置项、标签）\n"
        "   - 频繁创建和销毁的临时容器\n"
        "   - 对延迟敏感的代码路径\n\n"
        "3. 不适用场景:\n"
        "   - 元素数量通常很大\n"
        "   - 元素类型很大（浪费栈空间）\n"
        "   - 需要频繁移动/拷贝的容器\n\n"
        "4. 真实世界案例:\n"
        "   - std::string 的 SSO（短字符串优化）\n"
        "   - folly::small_vector（Facebook）\n"
        "   - LLVM::SmallVector（编译器基础设施）\n"
        "   - absl::InlinedVector（Google）\n";

    std::cout << "\n===== 演示结束 =====\n";
    return 0;
}
