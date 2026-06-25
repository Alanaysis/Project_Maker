/**
 * C++11 移动语义和右值引用示例
 *
 * 学习目标：
 * 1. 理解右值引用（T&&）
 * 2. 掌握移动构造函数和移动赋值运算符
 * 3. 学会使用 std::move
 * 4. 理解移动语义带来的性能提升
 */

#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include <algorithm>
#include <memory>

// ==========================================
// 1. 基础示例：具有资源所有权的 Buffer 类
// ==========================================

class Buffer {
    int* data_;
    size_t size_;

public:
    // 默认构造
    Buffer() : data_(nullptr), size_(0) {
        std::cout << "  [Buffer] 默认构造" << std::endl;
    }

    // 带大小构造
    explicit Buffer(size_t size) : data_(new int[size]()), size_(size) {
        std::cout << "  [Buffer] 带大小构造: size=" << size << std::endl;
    }

    // 拷贝构造函数
    Buffer(const Buffer& other) : data_(new int[other.size_]), size_(other.size_) {
        std::cout << "  [Buffer] 拷贝构造: size=" << size_ << std::endl;
        std::copy(other.data_, other.data_ + size_, data_);
    }

    // 移动构造函数（C++11 新增）
    // noexcept 很重要，它告诉编译器这个函数不会抛出异常
    // 这样 STL 容器在移动元素时会选择移动而不是拷贝
    Buffer(Buffer&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        std::cout << "  [Buffer] 移动构造: size=" << size_ << std::endl;
        // 将源对象置为空状态
        other.data_ = nullptr;
        other.size_ = 0;
    }

    // 拷贝赋值运算符
    Buffer& operator=(const Buffer& other) {
        std::cout << "  [Buffer] 拷贝赋值" << std::endl;
        if (this != &other) {
            delete[] data_;
            size_ = other.size_;
            data_ = new int[size_];
            std::copy(other.data_, other.data_ + size_, data_);
        }
        return *this;
    }

    // 移动赋值运算符（C++11 新增）
    Buffer& operator=(Buffer&& other) noexcept {
        std::cout << "  [Buffer] 移动赋值" << std::endl;
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }

    // 析构函数
    ~Buffer() {
        std::cout << "  [Buffer] 析构: size=" << size_ << std::endl;
        delete[] data_;
    }

    // 访问器
    size_t size() const { return size_; }
    int* data() const { return data_; }

    // 填充数据
    void fill(int value) {
        std::fill(data_, data_ + size_, value);
    }
};

// ==========================================
// 2. 右值引用基础
// ==========================================

void demonstrate_rvalue_references() {
    std::cout << "\n=== 1. 右值引用基础 ===" << std::endl;

    // 左值：有名字、可取地址的表达式
    int x = 42;          // x 是左值
    int& lref = x;       // 左值引用绑定到左值

    // 右值：临时的、即将销毁的表达式
    int&& rref = 42;     // 右值引用绑定到右值（字面量）
    int&& rref2 = x + 1; // 右值引用绑定到临时对象

    std::cout << "x = " << x << std::endl;
    std::cout << "lref = " << lref << std::endl;
    std::cout << "rref = " << rref << std::endl;
    std::cout << "rref2 = " << rref2 << std::endl;

    // std::move 将左值转换为右值引用
    int&& rref3 = std::move(x);  // x 被转换为右值引用
    std::cout << "rref3 (after std::move) = " << rref3 << std::endl;
    // 注意：std::move 后，x 的值仍然存在，但不应该再使用它
}

// ==========================================
// 3. 移动语义的实际应用
// ==========================================

void demonstrate_move_semantics() {
    std::cout << "\n=== 2. 移动语义实际应用 ===" << std::endl;

    // 创建 Buffer 对象
    Buffer buf1(100);
    buf1.fill(42);

    std::cout << "\n--- 拷贝构造 ---" << std::endl;
    Buffer buf2 = buf1;  // 调用拷贝构造函数
    std::cout << "buf1.size() = " << buf1.size() << std::endl;
    std::cout << "buf2.size() = " << buf2.size() << std::endl;

    std::cout << "\n--- 移动构造 ---" << std::endl;
    Buffer buf3 = std::move(buf1);  // 调用移动构造函数
    std::cout << "buf1.size() = " << buf1.size() << " (移动后为空)" << std::endl;
    std::cout << "buf3.size() = " << buf3.size() << std::endl;
}

// ==========================================
// 4. 函数返回值优化
// ==========================================

// 返回大对象时，移动语义可以避免不必要的拷贝
Buffer create_large_buffer(size_t size) {
    Buffer buf(size);
    buf.fill(100);
    return buf;  // 编译器会使用移动构造函数（或 RVO）
}

void demonstrate_return_value() {
    std::cout << "\n=== 3. 函数返回值优化 ===" << std::endl;

    Buffer buf = create_large_buffer(1000);
    std::cout << "创建的 Buffer 大小: " << buf.size() << std::endl;
}

// ==========================================
// 5. 移动语义与 STL 容器
// ==========================================

void demonstrate_move_with_containers() {
    std::cout << "\n=== 4. 移动语义与 STL 容器 ===" << std::endl;

    std::vector<Buffer> buffers;

    std::cout << "\n--- 使用 emplace_back 直接构造 ---" << std::endl;
    // emplace_back 可以在容器内部直接构造对象，避免临时对象
    buffers.emplace_back(50);
    buffers.emplace_back(100);

    std::cout << "\n--- 使用 push_back 和 std::move ---" << std::endl;
    Buffer temp(200);
    buffers.push_back(std::move(temp));  // 移动而非拷贝
    std::cout << "temp.size() after move: " << temp.size() << std::endl;

    std::cout << "\n--- 容器元素数量: " << buffers.size() << " ---" << std::endl;
}

// ==========================================
// 6. 移动语义性能对比
// ==========================================

void benchmark_move_vs_copy() {
    std::cout << "\n=== 5. 性能对比：移动 vs 拷贝 ===" << std::endl;

    const size_t SIZE = 1000000;
    const int ITERATIONS = 100;

    // 拷贝性能测试
    auto start_copy = std::chrono::high_resolution_clock::now();
    {
        std::vector<std::vector<int>> vec;
        vec.reserve(ITERATIONS);
        std::vector<int> source(SIZE, 42);
        for (int i = 0; i < ITERATIONS; ++i) {
            vec.push_back(source);  // 拷贝
        }
    }
    auto end_copy = std::chrono::high_resolution_clock::now();
    auto duration_copy = std::chrono::duration_cast<std::chrono::milliseconds>(
        end_copy - start_copy).count();

    // 移动性能测试
    auto start_move = std::chrono::high_resolution_clock::now();
    {
        std::vector<std::vector<int>> vec;
        vec.reserve(ITERATIONS);
        for (int i = 0; i < ITERATIONS; ++i) {
            std::vector<int> source(SIZE, 42);
            vec.push_back(std::move(source));  // 移动
        }
    }
    auto end_move = std::chrono::high_resolution_clock::now();
    auto duration_move = std::chrono::duration_cast<std::chrono::milliseconds>(
        end_move - start_move).count();

    std::cout << "拷贝耗时: " << duration_copy << " ms" << std::endl;
    std::cout << "移动耗时: " << duration_move << " ms" << std::endl;
    if (duration_move > 0) {
        std::cout << "性能提升: " << (double)duration_copy / duration_move << "x" << std::endl;
    }
}

// ==========================================
// 7. 完美转发简介
// ==========================================

// 完美转发可以将参数的值类别（左值/右值）原封不动地传递给另一个函数
template<typename T>
void wrapper(T&& arg) {
    // std::forward 保持参数的值类别
    // 如果传入的是左值，forward 后仍是左值
    // 如果传入的是右值，forward 后仍是右值
    std::cout << "  wrapper received: " << arg << std::endl;
}

template<typename T, typename... Args>
std::unique_ptr<T> make_unique_custom(Args&&... args) {
    // 完美转发参数给 T 的构造函数
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

void demonstrate_perfect_forwarding() {
    std::cout << "\n=== 6. 完美转发 ===" << std::endl;

    int x = 42;
    std::cout << "--- 传递左值 ---" << std::endl;
    wrapper(x);           // T 被推导为 int&

    std::cout << "--- 传递右值 ---" << std::endl;
    wrapper(42);          // T 被推导为 int
    wrapper(std::move(x)); // T 被推导为 int
}

// ==========================================
// 主函数
// ==========================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "C++11 移动语义和右值引用示例" << std::endl;
    std::cout << "========================================" << std::endl;

    // 1. 右值引用基础
    demonstrate_rvalue_references();

    // 2. 移动语义实际应用
    demonstrate_move_semantics();

    // 3. 函数返回值优化
    demonstrate_return_value();

    // 4. 移动语义与 STL 容器
    demonstrate_move_with_containers();

    // 5. 性能对比
    benchmark_move_vs_copy();

    // 6. 完美转发
    demonstrate_perfect_forwarding();

    std::cout << "\n========================================" << std::endl;
    std::cout << "所有示例执行完毕！" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
