/**
 * 类型擦除 (Type Erasure) 技术演示
 *
 * 类型擦除是 C++ 中一种重要的设计模式，它允许我们在不使用继承的情况下，
 * 通过模板和多态的组合来实现"任何类型"的统一接口。
 *
 * 核心思想：
 *   - 外部接口使用非模板类（如 std::function）
 *   - 内部通过模板实现具体类型的存储和调用
 *   - 使用虚函数或函数指针实现运行时多态
 *
 * 典型应用：
 *   - std::function：存储任何可调用对象
 *   - std::any：存储任何类型的值
 *   - std::shared_ptr：自定义删除器
 *
 * 编译命令：g++ -std=c++17 -O2 -o type_erasure type_erasure.cpp
 */

#include <iostream>
#include <memory>
#include <string>
#include <vector>
#include <functional>
#include <typeinfo>
#include <cstring>

// ============================================================================
// 第一部分：简单的 Any 类型实现
// ============================================================================

/**
 * SimpleAny - 一个简单的类型擦除容器
 *
 * 实现原理：
 *   1. 定义一个基类 HolderBase，提供虚函数接口
 *   2. 定义模板类 Holder<T>，存储具体类型的数据
 *   3. SimpleAny 持有 HolderBase 的指针，通过虚函数实现多态
 *
 * 这种模式被称为 "外部多态" (External Polymorphism)
 */
class SimpleAny {
private:
    /**
     * HolderBase - 类型擦除的基类
     *
     * 所有被擦除的类型都会被包装成 HolderBase 的派生类
     * 通过虚函数实现运行时多态
     */
    struct HolderBase {
        virtual ~HolderBase() = default;

        // 获取类型信息
        virtual const std::type_info& type() const = 0;

        // 克隆自身（用于拷贝构造）
        virtual std::unique_ptr<HolderBase> clone() const = 0;

        // 打印值（用于演示）
        virtual void print() const = 0;
    };

    /**
     * Holder<T> - 具体类型的持有者
     *
     * 使用模板参数 T 存储实际的数据
     * 每个不同的 T 都会生成一个新的派生类
     */
    template<typename T>
    struct Holder : HolderBase {
        T value_;  // 存储实际的值

        // 构造函数：完美转发参数
        template<typename U>
        explicit Holder(U&& value) : value_(std::forward<U>(value)) {}

        // 返回类型信息
        const std::type_info& type() const override {
            return typeid(T);
        }

        // 克隆自身
        std::unique_ptr<HolderBase> clone() const override {
            return std::make_unique<Holder<T>>(value_);
        }

        // 打印值
        void print() const override {
            std::cout << value_;
        }
    };

    std::unique_ptr<HolderBase> holder_;  // 指向实际数据的指针

public:
    // 默认构造函数
    SimpleAny() = default;

    // 模板构造函数：接受任意类型的值
    // 使用 SFINAE 禁止 SimpleAny 自身的拷贝/移动
    template<typename T,
             typename = std::enable_if_t<!std::is_same_v<std::decay_t<T>, SimpleAny>>>
    SimpleAny(T&& value)
        : holder_(std::make_unique<Holder<std::decay_t<T>>>(std::forward<T>(value))) {}

    // 拷贝构造函数
    SimpleAny(const SimpleAny& other)
        : holder_(other.holder_ ? other.holder_->clone() : nullptr) {}

    // 移动构造函数
    SimpleAny(SimpleAny&&) noexcept = default;

    // 拷贝赋值运算符
    SimpleAny& operator=(const SimpleAny& other) {
        if (this != &other) {
            holder_ = other.holder_ ? other.holder_->clone() : nullptr;
        }
        return *this;
    }

    // 移动赋值运算符
    SimpleAny& operator=(SimpleAny&&) noexcept = default;

    // 获取存储值的类型信息
    const std::type_info& type() const {
        return holder_ ? holder_->type() : typeid(void);
    }

    // 检查是否持有值
    bool has_value() const {
        return holder_ != nullptr;
    }

    // 获取存储的值（类型安全的向下转型）
    template<typename T>
    T& get() {
        // 检查类型是否匹配
        if (!holder_ || holder_->type() != typeid(T)) {
            throw std::bad_cast();
        }
        // static_cast 是安全的，因为我们已经检查了类型
        return static_cast<Holder<T>*>(holder_.get())->value_;
    }

    // 打印存储的值
    void print() const {
        if (holder_) {
            holder_->print();
        } else {
            std::cout << "(empty)";
        }
    }
};

// ============================================================================
// 第二部分：类似 std::function 的可调用对象包装器
// ============================================================================

/**
 * SimpleFunction<R(Args...)> - 类型擦除的函数包装器
 *
 * 演示如何实现类似 std::function 的功能
 *
 * 实现要点：
 *   - 使用模板特化来匹配函数签名
 *   - 内部使用虚函数实现类型擦除
 *   - 支持任何可调用对象：函数指针、lambda、仿函数等
 */
template<typename Signature>
class SimpleFunction;  // 前向声明

// 针对 R(Args...) 的特化
template<typename R, typename... Args>
class SimpleFunction<R(Args...)> {
private:
    /**
     * CallableBase - 可调用对象的基类
     *
     * 定义统一的调用接口
     */
    struct CallableBase {
        virtual ~CallableBase() = default;
        virtual R invoke(Args... args) = 0;
        virtual std::unique_ptr<CallableBase> clone() const = 0;
    };

    /**
     * Callable<T> - 具体可调用对象的包装
     *
     * T 可以是函数指针、lambda、仿函数等任何可调用类型
     */
    template<typename T>
    struct Callable : CallableBase {
        T callable_;  // 存储实际的可调用对象

        template<typename U>
        explicit Callable(U&& callable) : callable_(std::forward<U>(callable)) {}

        R invoke(Args... args) override {
            // 使用完美转发调用实际的可调用对象
            return callable_(std::forward<Args>(args)...);
        }

        std::unique_ptr<CallableBase> clone() const override {
            return std::make_unique<Callable<T>>(callable_);
        }
    };

    std::unique_ptr<CallableBase> callable_;  // 指向实际可调用对象的指针

public:
    // 默认构造函数
    SimpleFunction() = default;

    // 从任意可调用对象构造
    template<typename T,
             typename = std::enable_if_t<!std::is_same_v<std::decay_t<T>, SimpleFunction>>>
    SimpleFunction(T&& callable)
        : callable_(std::make_unique<Callable<std::decay_t<T>>>(std::forward<T>(callable))) {}

    // 拷贝构造函数
    SimpleFunction(const SimpleFunction& other)
        : callable_(other.callable_ ? other.callable_->clone() : nullptr) {}

    // 移动构造函数
    SimpleFunction(SimpleFunction&&) noexcept = default;

    // 调用运算符
    R operator()(Args... args) {
        if (!callable_) {
            throw std::bad_function_call();
        }
        return callable_->invoke(std::forward<Args>(args)...);
    }

    // 检查是否持有可调用对象
    explicit operator bool() const {
        return callable_ != nullptr;
    }
};

// ============================================================================
// 第三部分：带小对象优化的类型擦除容器
// ============================================================================

/**
 * SmallAny - 带小对象优化的 Any 类型
 *
 * 小对象优化 (Small Object Optimization, SOO)：
 *   - 对于小对象，直接存储在栈上，避免堆分配
 *   - 对于大对象，才使用堆分配
 *   - 提高性能，减少内存碎片
 *
 * 这是 std::any 的常见实现策略
 */
template<size_t BufferSize = 32>
class SmallAny {
private:
    // 存储区：用于小对象的栈上存储
    alignas(std::max_align_t) char buffer_[BufferSize];

    /**
     * Operations - 操作函数表
     *
     * 使用函数指针表代替虚函数，避免额外的间接层
     * 这种技术称为 "手动虚函数表"
     */
    enum class Operation {
        Destroy,    // 销毁
        Clone,      // 克隆
        Type,       // 获取类型
        Print       // 打印
    };

    using OperationFn = void*(*)(Operation, const SmallAny*, SmallAny*);

    // 默认的空操作
    static void* empty_op(Operation, const SmallAny*, SmallAny*) {
        return nullptr;
    }

    OperationFn ops_ = &empty_op;  // 操作函数指针

    // 检查类型是否可以放在缓冲区中
    template<typename T>
    static constexpr bool is_small() {
        return sizeof(T) <= BufferSize
            && alignof(T) <= alignof(std::max_align_t)
            && std::is_nothrow_move_constructible_v<T>;
    }

    // 为小类型生成操作函数
    template<typename T>
    static void* small_op(Operation op, const SmallAny* src, SmallAny* dst) {
        switch (op) {
            case Operation::Destroy:
                // 显式调用析构函数
                reinterpret_cast<const T*>(src->buffer_)->~T();
                return nullptr;

            case Operation::Clone:
                // 在目标缓冲区中构造对象
                new (dst->buffer_) T(*reinterpret_cast<const T*>(src->buffer_));
                dst->ops_ = src->ops_;
                return nullptr;

            case Operation::Type:
                // 返回类型信息
                return const_cast<void*>(static_cast<const void*>(&typeid(T)));

            case Operation::Print:
                std::cout << *reinterpret_cast<const T*>(src->buffer_);
                return nullptr;
        }
        return nullptr;
    }

    // 为大类型生成操作函数（使用堆分配）
    template<typename T>
    static void* large_op(Operation op, const SmallAny* src, SmallAny* dst) {
        // 获取存储在 buffer 中的指针
        auto ptr = *reinterpret_cast<T* const*>(src->buffer_);

        switch (op) {
            case Operation::Destroy:
                delete ptr;
                return nullptr;

            case Operation::Clone:
                *reinterpret_cast<T**>(dst->buffer_) = new T(*ptr);
                dst->ops_ = src->ops_;
                return nullptr;

            case Operation::Type:
                return const_cast<void*>(static_cast<const void*>(&typeid(T)));

            case Operation::Print:
                std::cout << *ptr;
                return nullptr;
        }
        return nullptr;
    }

    // 销毁当前存储的对象
    void destroy() {
        ops_(Operation::Destroy, this, nullptr);
        ops_ = &empty_op;
    }

public:
    // 默认构造函数
    SmallAny() = default;

    // 模板构造函数
    template<typename T,
             typename = std::enable_if_t<!std::is_same_v<std::decay_t<T>, SmallAny>>>
    SmallAny(T&& value) {
        using Decayed = std::decay_t<T>;

        if constexpr (is_small<Decayed>()) {
            // 小对象：直接存储在缓冲区中
            new (buffer_) Decayed(std::forward<T>(value));
            ops_ = &small_op<Decayed>;
        } else {
            // 大对象：堆分配
            *reinterpret_cast<Decayed**>(buffer_) = new Decayed(std::forward<T>(value));
            ops_ = &large_op<Decayed>;
        }
    }

    // 析构函数
    ~SmallAny() {
        destroy();
    }

    // 拷贝构造函数
    SmallAny(const SmallAny& other) {
        if (other.ops_ != &empty_op) {
            other.ops_(Operation::Clone, &other, this);
        }
    }

    // 移动构造函数
    SmallAny(SmallAny&& other) noexcept {
        // 直接复制缓冲区和操作函数
        std::memcpy(buffer_, other.buffer_, BufferSize);
        ops_ = other.ops_;
        other.ops_ = &empty_op;
    }

    // 获取类型信息
    const std::type_info& type() const {
        if (ops_ == &empty_op) {
            return typeid(void);
        }
        auto* ti = static_cast<const std::type_info*>(
            ops_(Operation::Type, this, nullptr)
        );
        return *ti;
    }

    // 检查是否持有值
    bool has_value() const {
        return ops_ != &empty_op;
    }

    // 打印值
    void print() const {
        if (ops_ != &empty_op) {
            ops_(Operation::Print, this, nullptr);
        } else {
            std::cout << "(empty)";
        }
    }
};

// ============================================================================
// 第四部分：类型擦除的迭代器
// ============================================================================

/**
 * AnyIterator<T> - 类型擦除的迭代器
 *
 * 允许用统一的接口遍历不同类型的容器
 * 例如：可以用同一个函数遍历 vector、list、set 等
 */
template<typename T>
class AnyIterator {
private:
    /**
     * IteratorInterface - 迭代器接口
     *
     * 定义迭代器的基本操作
     */
    struct IteratorInterface {
        virtual ~IteratorInterface() = default;
        virtual T& dereference() = 0;
        virtual void increment() = 0;
        virtual bool equal(const IteratorInterface* other) const = 0;
        virtual std::unique_ptr<IteratorInterface> clone() const = 0;
    };

    /**
     * IteratorWrapper<Iter> - 具体迭代器的包装
     */
    template<typename Iter>
    struct IteratorWrapper : IteratorInterface {
        Iter iter_;

        explicit IteratorWrapper(Iter iter) : iter_(iter) {}

        T& dereference() override {
            // 使用 const_cast 处理 const 迭代器的情况
            return const_cast<T&>(*iter_);
        }

        void increment() override {
            ++iter_;
        }

        bool equal(const IteratorInterface* other) const override {
            // 使用 typeid 进行类型检查
            if (typeid(*this) != typeid(*other)) {
                return false;
            }
            return iter_ == static_cast<const IteratorWrapper*>(other)->iter_;
        }

        std::unique_ptr<IteratorInterface> clone() const override {
            return std::make_unique<IteratorWrapper>(iter_);
        }
    };

    std::unique_ptr<IteratorInterface> impl_;

public:
    // 从任意迭代器构造
    template<typename Iter>
    AnyIterator(Iter iter)
        : impl_(std::make_unique<IteratorWrapper<Iter>>(iter)) {}

    // 拷贝构造函数
    AnyIterator(const AnyIterator& other)
        : impl_(other.impl_->clone()) {}

    // 解引用
    T& operator*() {
        return impl_->dereference();
    }

    // 前置递增
    AnyIterator& operator++() {
        impl_->increment();
        return *this;
    }

    // 相等比较
    bool operator==(const AnyIterator& other) const {
        return impl_->equal(other.impl_.get());
    }

    // 不等比较
    bool operator!=(const AnyIterator& other) const {
        return !(*this == other);
    }
};

// ============================================================================
// 辅助函数：使用 AnyIterator 遍历任意容器
// ============================================================================

/**
 * print_container - 打印任意容器的内容
 *
 * 由于使用了类型擦除，这个函数可以接受任何容器
 */
template<typename Container>
void print_container(const Container& container) {
    AnyIterator<typename Container::value_type> begin(container.begin());
    AnyIterator<typename Container::value_type> end(container.end());

    std::cout << "[";
    bool first = true;
    for (auto it = begin; it != end; ++it) {
        if (!first) std::cout << ", ";
        std::cout << *it;
        first = false;
    }
    std::cout << "]" << std::endl;
}

// ============================================================================
// 主函数：演示各种类型擦除技术
// ============================================================================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "类型擦除 (Type Erasure) 技术演示" << std::endl;
    std::cout << "========================================" << std::endl;

    // ---- 第一部分：SimpleAny 演示 ----
    std::cout << "\n--- 1. SimpleAny 基本用法 ---" << std::endl;

    SimpleAny a1 = 42;           // 存储 int
    SimpleAny a2 = 3.14;         // 存储 double
    SimpleAny a3 = std::string("Hello");  // 存储 string

    std::cout << "a1 = "; a1.print();
    std::cout << " (type: " << a1.type().name() << ")" << std::endl;

    std::cout << "a2 = "; a2.print();
    std::cout << " (type: " << a2.type().name() << ")" << std::endl;

    std::cout << "a3 = "; a3.print();
    std::cout << " (type: " << a3.type().name() << ")" << std::endl;

    // 获取存储的值
    std::cout << "a1.get<int>() = " << a1.get<int>() << std::endl;
    std::cout << "a3.get<std::string>() = " << a3.get<std::string>() << std::endl;

    // 类型不匹配会抛出异常
    try {
        a1.get<double>();  // 错误：a1 存储的是 int
    } catch (const std::bad_cast& e) {
        std::cout << "捕获异常：" << e.what() << std::endl;
    }

    // ---- 第二部分：SimpleFunction 演示 ----
    std::cout << "\n--- 2. SimpleFunction 用法 ---" << std::endl;

    // 存储 lambda 表达式
    SimpleFunction<int(int, int)> add = [](int a, int b) {
        return a + b;
    };
    std::cout << "add(3, 4) = " << add(3, 4) << std::endl;

    // 存储函数对象
    struct Multiplier {
        int factor;
        int operator()(int x) const { return x * factor; }
    };

    SimpleFunction<int(int)> triple{Multiplier{3}};
    std::cout << "triple(5) = " << triple(5) << std::endl;

    // 存储普通函数
    auto square = [](double x) -> double { return x * x; };
    SimpleFunction<double(double)> sq = square;
    std::cout << "sq(4.0) = " << sq(4.0) << std::endl;

    // 存储带捕获的 lambda
    int offset = 100;
    SimpleFunction<int(int)> add_offset = [offset](int x) {
        return x + offset;
    };
    std::cout << "add_offset(5) = " << add_offset(5) << std::endl;

    // ---- 第三部分：SmallAny 演示 ----
    std::cout << "\n--- 3. SmallAny 小对象优化 ---" << std::endl;

    SmallAny<32> sa1 = 42;       // 小对象，存储在栈上
    SmallAny<32> sa2 = std::string("Stack allocated!");  // 可能需要堆分配

    std::cout << "sa1 = "; sa1.print();
    std::cout << " (type: " << sa1.type().name() << ")" << std::endl;

    std::cout << "sa2 = "; sa2.print();
    std::cout << " (type: " << sa2.type().name() << ")" << std::endl;

    // ---- 第四部分：AnyIterator 演示 ----
    std::cout << "\n--- 4. AnyIterator 类型擦除迭代器 ---" << std::endl;

    std::vector<int> vec = {1, 2, 3, 4, 5};
    std::vector<double> dbl_vec = {1.1, 2.2, 3.3};

    std::cout << "遍历 vector<int>: ";
    print_container(vec);

    std::cout << "遍历 vector<double>: ";
    print_container(dbl_vec);

    // ---- 性能对比说明 ----
    std::cout << "\n========================================" << std::endl;
    std::cout << "类型擦除的优缺点：" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "优点：" << std::endl;
    std::cout << "  1. 无需继承关系，解耦类型" << std::endl;
    std::cout << "  2. 值语义，易于使用" << std::endl;
    std::cout << "  3. 支持小对象优化" << std::endl;
    std::cout << "缺点：" << std::endl;
    std::cout << "  1. 有运行时开销（虚函数调用）" << std::endl;
    std::cout << "  2. 可能有堆分配" << std::endl;
    std::cout << "  3. 失去编译期类型信息" << std::endl;

    return 0;
}
