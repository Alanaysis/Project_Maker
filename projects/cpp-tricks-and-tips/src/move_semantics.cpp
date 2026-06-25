/**
 * move_semantics.cpp - 移动语义 (Move Semantics)
 *
 * 本文件全面演示 C++ 移动语义的各个方面：
 *   1. 移动构造函数和移动赋值运算符
 *   2. std::move 的使用
 *   3. 移动专用类型 (Move-only types)
 *   4. 返回值优化 (RVO/NRVO)
 *   5. 性能收益对比
 *
 * 编译: g++ -std=c++17 -O2 -o move_semantics move_semantics.cpp
 *
 * 移动语义的核心思想：
 *   当一个对象即将被销毁（临时对象）或不再需要时，
 *   我们可以"偷取"它的资源（如堆内存、文件句柄），
 *   而不是深拷贝。这大大减少了不必要的内存分配和数据复制。
 *
 * C++11 引入了右值引用 (&&) 来实现移动语义。
 * std::move 本身不做任何移动，它只是将左值转换为右值引用，
 * 使得移动构造/赋值函数可以被调用。
 */

#include <iostream>
#include <vector>
#include <string>
#include <memory>
#include <chrono>
#include <cstring>
#include <algorithm>
#include <cassert>
#include <iomanip>
#include <utility>  // std::move, std::exchange

// ============================================================================
// 第一部分：演示用的 Buffer 类
// ============================================================================
// 这个类管理一块动态分配的内存，用于清晰地展示移动 vs 拷贝的区别。

class Buffer {
public:
    // 默认构造
    Buffer() : data_(nullptr), size_(0) {
        std::cout << "  [默认构造] 空缓冲区\n";
    }

    // 带大小的构造
    explicit Buffer(size_t size) : data_(new char[size]), size_(size) {
        std::memset(data_, 0, size_);
        std::cout << "  [构造] 分配 " << size_ << " 字节 @ "
                  << static_cast<void*>(data_) << "\n";
    }

    // 带数据的构造
    Buffer(const char* str) : size_(std::strlen(str) + 1) {
        data_ = new char[size_];
        std::memcpy(data_, str, size_);
        std::cout << "  [构造] \"" << str << "\" @ "
                  << static_cast<void*>(data_) << "\n";
    }

    // ================================================================
    // 拷贝构造函数 - 深拷贝
    // ================================================================
    // 执行深拷贝：分配新内存，复制所有数据
    // 时间复杂度: O(n)，其中 n 是数据大小
    Buffer(const Buffer& other) : size_(other.size_) {
        if (size_ > 0) {
            data_ = new char[size_];
            std::memcpy(data_, other.data_, size_);
        } else {
            data_ = nullptr;
        }
        std::cout << "  [拷贝构造] 深拷贝 " << size_ << " 字节 @ "
                  << static_cast<void*>(data_) << "\n";
    }

    // ================================================================
    // 拷贝赋值运算符 - 深拷贝
    // ================================================================
    Buffer& operator=(const Buffer& other) {
        std::cout << "  [拷贝赋值]\n";
        if (this == &other) return *this;

        // 释放旧资源
        delete[] data_;

        // 深拷贝新资源
        size_ = other.size_;
        if (size_ > 0) {
            data_ = new char[size_];
            std::memcpy(data_, other.data_, size_);
        } else {
            data_ = nullptr;
        }
        return *this;
    }

    // ================================================================
    // 移动构造函数 - 资源转移
    // ================================================================
    // 不分配内存，只是"偷取"源对象的资源
    // 时间复杂度: O(1)，只是几个指针的赋值
    //
    // noexcept 非常重要！标准库容器（如 std::vector）在需要移动时
    // 会检查移动操作是否是 noexcept 的，如果不是，会回退到拷贝。
    Buffer(Buffer&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        // 将源对象置于"有效但未指定"的状态
        // 这里我们将其置为空状态
        other.data_ = nullptr;
        other.size_ = 0;
        std::cout << "  [移动构造] 转移资源 @ " << static_cast<void*>(data_)
                  << " (" << size_ << " 字节)\n";
    }

    // ================================================================
    // 移动赋值运算符 - 资源转移
    // ================================================================
    Buffer& operator=(Buffer&& other) noexcept {
        std::cout << "  [移动赋值]\n";
        if (this == &other) return *this;

        // 释放当前资源
        delete[] data_;

        // 偷取源对象的资源
        data_ = other.data_;
        size_ = other.size_;

        // 源对象置空
        other.data_ = nullptr;
        other.size_ = 0;

        return *this;
    }

    // 析构函数
    ~Buffer() {
        if (data_) {
            std::cout << "  [析构] 释放 " << size_ << " 字节 @ "
                      << static_cast<void*>(data_) << "\n";
            delete[] data_;
        } else {
            std::cout << "  [析构] 空缓冲区\n";
        }
    }

    // 辅助函数
    size_t size() const { return size_; }
    bool empty() const { return size_ == 0; }
    const char* data() const { return data_; }
    const char* c_str() const { return data_ ? data_ : ""; }

    // 打印状态
    void print(const char* name = "") const {
        std::cout << "  " << name
                  << " [size=" << size_
                  << " addr=" << static_cast<const void*>(data_)
                  << " data=\"" << c_str() << "\"]\n";
    }

private:
    char* data_;
    size_t size_;
};

// ============================================================================
// 第二部分：移动专用类型 (Move-only Type)
// ============================================================================
// 某些资源不能被拷贝，只能被移动，例如：
//   - std::unique_ptr
//   - std::thread
//   - std::fstream
//   - 文件描述符
//   - 互斥锁

/**
 * UniqueResource - 一个移动专用的资源管理类
 *
 * 类似于 std::unique_ptr，但管理的是一个模拟的"系统资源"
 */
class UniqueResource {
public:
    // 构造：获取资源
    explicit UniqueResource(int id) : id_(new int(id)) {
        std::cout << "  获取资源 #" << *id_ << "\n";
    }

    // 析构：释放资源
    ~UniqueResource() {
        if (id_) {
            std::cout << "  释放资源 #" << *id_ << "\n";
            delete id_;
        }
    }

    // 禁止拷贝！这是移动专用类型的核心特征
    UniqueResource(const UniqueResource&) = delete;
    UniqueResource& operator=(const UniqueResource&) = delete;

    // 移动构造：转移所有权
    UniqueResource(UniqueResource&& other) noexcept : id_(other.id_) {
        other.id_ = nullptr;  // 源不再拥有资源
        std::cout << "  移动资源 #" << *id_ << "\n";
    }

    // 移动赋值：释放旧资源，获取新资源
    UniqueResource& operator=(UniqueResource&& other) noexcept {
        if (this == &other) return *this;

        // 释放旧资源
        if (id_) {
            std::cout << "  释放旧资源 #" << *id_ << "\n";
            delete id_;
        }

        // 获取新资源
        id_ = other.id_;
        other.id_ = nullptr;
        std::cout << "  接管资源 #" << *id_ << "\n";
        return *this;
    }

    int id() const { return id_ ? *id_ : -1; }
    bool valid() const { return id_ != nullptr; }

private:
    int* id_;  // 模拟的资源句柄
};

// ============================================================================
// 第三部分：返回值优化 (RVO/NRVO) 演示
// ============================================================================

// 返回大对象时，编译器可以优化掉拷贝/移动操作

/**
 * create_buffer_with_rvo - 命名返回值优化 (NRVO)
 *
 * 编译器可以直接在调用者的栈帧上构造返回值，
 * 完全省略拷贝或移动操作。
 *
 * 注意：NRVO 不是语言标准强制要求的，但所有主流编译器都会执行。
 */
Buffer create_buffer_with_rvo(const char* str) {
    Buffer buf(str);  // 在返回时，编译器可能直接在调用者空间构造
    return buf;       // NRVO: 不调用移动构造
}

/**
 * create_buffer_prvalue - 纯右值返回
 *
 * 返回临时对象时，几乎肯定会被 RVO 优化。
 * 这是最可靠的优化场景。
 */
Buffer create_buffer_prvalue() {
    return Buffer("直接构造");  // RVO: 编译器直接在调用者空间构造
}

/**
 * create_buffer_conditionally - 条件返回（可能无法 NRVO）
 *
 * 当函数有多个返回路径且返回不同变量时，
 * 编译器可能无法执行 NRVO。
 */
Buffer create_buffer_conditionally(bool flag) {
    if (flag) {
        Buffer a("从分支A返回");
        return a;  // 可能 NRVO
    } else {
        Buffer b("从分支B返回");
        return b;  // 可能 NRVO
    }
    // 注意：现代编译器通常仍能优化这种情况
}

// ============================================================================
// 第四部分：辅助函数和测试
// ============================================================================

void print_section(const char* title) {
    std::cout << "\n========================================\n"
              << title << "\n"
              << "========================================\n";
}

// 工厂函数示例：返回移动专用类型
UniqueResource create_resource(int id) {
    UniqueResource res(id);
    return res;  // 移动（或 NRVO）
}

int main() {
    std::cout << "===== C++ 移动语义演示 =====\n";

    // ---- 演示 1: 拷贝 vs 移动 基本对比 ----
    print_section("1. 拷贝 vs 移动 基本对比");

    {
        std::cout << "--- 拷贝构造 ---\n";
        Buffer original("Hello, World!");
        Buffer copy = original;  // 调用拷贝构造
        original.print("original");
        copy.print("copy");
        std::cout << "注意: 两个对象各自拥有独立的内存\n";

        std::cout << "\n--- 移动构造 ---\n";
        Buffer moved = std::move(original);  // 调用移动构造
        original.print("original (已移动)");
        moved.print("moved");
        std::cout << "注意: original 的资源被转移给了 moved\n";
    }

    // ---- 演示 2: std::move 的本质 ----
    print_section("2. std::move 的本质");

    {
        std::cout << "std::move 本身不做任何移动！\n"
                  << "它只是将左值转换为右值引用，\n"
                  << "使得移动构造/赋值函数可以被调用。\n\n";

        Buffer buf("测试数据");

        // std::move(buf) 返回一个 Buffer&&（右值引用）
        // 这使得编译器选择移动构造函数而不是拷贝构造函数
        Buffer moved = std::move(buf);

        std::cout << "\n重要: std::move 后，原对象处于 [有效但未指定] 状态\n"
                  << "不应该再使用被移动的对象（除非先赋新值）\n";

        buf.print("buf (已被移动)");
        moved.print("moved");
    }

    // ---- 演示 3: 移动赋值 ----
    print_section("3. 移动赋值运算符");

    {
        Buffer a("缓冲区A");
        Buffer b("缓冲区B");

        std::cout << "\n--- 移动赋值前 ---\n";
        a.print("a");
        b.print("b");

        std::cout << "\n--- 执行 a = std::move(b) ---\n";
        a = std::move(b);  // 移动赋值

        std::cout << "\n--- 移动赋值后 ---\n";
        a.print("a");
        b.print("b (已被移动)");
    }

    // ---- 演示 4: 移动专用类型 ----
    print_section("4. 移动专用类型 (Move-only Type)");

    {
        std::cout << "--- 创建资源 ---\n";
        UniqueResource res1(42);

        std::cout << "\n--- 移动构造 ---\n";
        UniqueResource res2 = std::move(res1);

        std::cout << "\nres1 有效: " << (res1.valid() ? "是" : "否") << "\n";
        std::cout << "res2 有效: " << (res2.valid() ? "是" : "否")
                  << " id=" << res2.id() << "\n";

        std::cout << "\n--- 移动赋值 ---\n";
        UniqueResource res3(99);
        res3 = std::move(res2);

        std::cout << "\nres2 有效: " << (res2.valid() ? "是" : "否") << "\n";
        std::cout << "res3 有效: " << (res3.valid() ? "是" : "否")
                  << " id=" << res3.id() << "\n";

        // 以下代码无法编译，因为拷贝被禁止：
        // UniqueResource res4 = res3;  // 错误！
    }

    // ---- 演示 5: 工厂函数和移动 ----
    print_section("5. 工厂函数和移动专用类型");

    {
        std::cout << "工厂函数返回移动专用类型:\n\n";
        UniqueResource res = create_resource(7);
        std::cout << "\n资源 id: " << res.id() << "\n";

        std::cout << "\n将资源放入容器:\n";
        std::vector<UniqueResource> resources;
        resources.push_back(std::move(res));

        std::cout << "\nres 有效: " << (res.valid() ? "是" : "否") << "\n";
        std::cout << "容器中的资源: " << resources[0].id() << "\n";
    }

    // ---- 演示 6: 返回值优化 (RVO/NRVO) ----
    print_section("6. 返回值优化 (RVO/NRVO)");

    {
        std::cout << "编译器优化可以省略移动/拷贝操作:\n\n";

        std::cout << "--- NRVO (命名返回值优化) ---\n";
        {
            Buffer buf = create_buffer_with_rvo("NRVO测试");
            buf.print("结果");
        }

        std::cout << "\n--- RVO (返回临时对象) ---\n";
        {
            Buffer buf = create_buffer_prvalue();
            buf.print("结果");
        }

        std::cout << "\n--- 条件返回 ---\n";
        {
            Buffer buf = create_buffer_conditionally(true);
            buf.print("结果");
        }

        std::cout << "\n注意: 使用 -fno-elide-constructors 编译选项可以禁用 RVO，\n"
                  << "观察实际的移动操作:\n"
                  << "  g++ -std=c++17 -fno-elide-constructors move_semantics.cpp\n";
    }

    // ---- 演示 7: 性能对比 ----
    print_section("7. 性能对比: 拷贝 vs 移动");

    {
        using Clock = std::chrono::high_resolution_clock;
        const int N = 100000;
        const size_t BUF_SIZE = 4096;

        // 测试拷贝
        double copy_time;
        {
            std::vector<Buffer> vec;
            vec.reserve(N);

            auto start = Clock::now();
            for (int i = 0; i < N; ++i) {
                Buffer buf(BUF_SIZE);
                vec.push_back(buf);  // 拷贝！
            }
            copy_time = std::chrono::duration<double, std::milli>(
                Clock::now() - start).count();
        }

        // 测试移动
        double move_time;
        {
            std::vector<Buffer> vec;
            vec.reserve(N);

            auto start = Clock::now();
            for (int i = 0; i < N; ++i) {
                Buffer buf(BUF_SIZE);
                vec.push_back(std::move(buf));  // 移动！
            }
            move_time = std::chrono::duration<double, std::milli>(
                Clock::now() - start).count();
        }

        std::cout << std::fixed << std::setprecision(2);
        std::cout << N << " 次 push_back (" << BUF_SIZE << " 字节缓冲区):\n";
        std::cout << "  拷贝: " << copy_time << " ms\n";
        std::cout << "  移动: " << move_time << " ms\n";
        std::cout << "  性能提升: " << (copy_time / move_time) << "x\n";
    }

    // ---- 演示 8: 移动和容器 ----
    print_section("8. 移动语义与容器操作");

    {
        std::vector<Buffer> vec;
        vec.push_back(Buffer("第一个"));
        vec.push_back(Buffer("第二个"));
        vec.push_back(Buffer("第三个"));

        std::cout << "\nvector 中的元素（push_back 临时对象会自动移动）:\n";
        for (const auto& buf : vec) {
            std::cout << "  " << buf.c_str() << "\n";
        }

        // emplace_back 直接在容器内存中构造，避免任何拷贝或移动
        std::cout << "\nemplace_back 直接原地构造:\n";
        vec.emplace_back("原地构造");

        // 从 vector 中"取走"元素
        std::cout << "\n从 vector 中移动出元素:\n";
        Buffer taken = std::move(vec[0]);
        taken.print("取出的元素");
        vec[0].print("原位置 (已被移动)");
    }

    // ---- 总结 ----
    print_section("总结: 移动语义要点");

    std::cout <<
        "关键要点:\n"
        "  1. 移动构造/赋值应该标记 noexcept\n"
        "     - 标准容器依赖此保证来选择移动而非拷贝\n\n"
        "  2. 移动后对象处于 [有效但未指定] 状态\n"
        "     - 可以安全地调用不依赖值的函数（如 size(), empty()）\n"
        "     - 可以安全地赋新值或析构\n\n"
        "  3. std::move 本身不做任何移动\n"
        "     - 只是类型转换（左值 -> 右值引用）\n"
        "     - 移动是否真的发生取决于类型的移动构造函数\n\n"
        "  4. RVO/NRVO 可以完全省略移动\n"
        "     - 编译器可以直接在目标位置构造对象\n"
        "     - 返回局部对象时，优先使用返回值而不是 std::move\n\n"
        "  5. 移动专用类型（如 unique_ptr）只能移动，不能拷贝\n"
        "     - 表达了资源的独占所有权语义\n";

    std::cout << "\n===== 演示结束 =====\n";
    return 0;
}
