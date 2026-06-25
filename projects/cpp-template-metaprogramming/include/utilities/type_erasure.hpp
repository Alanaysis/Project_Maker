#pragma once
// =============================================================================
// type_erasure.hpp - 类型擦除 (Type Erasure)
// =============================================================================
// 类型擦除是一种将具体类型信息隐藏在统一接口背后的技术
// 它结合了模板的灵活性和多态的统一性
// 典型案例：std::function, std::any, std::shared_ptr 的删除器
// =============================================================================

#include <memory>
#include <utility>
#include <typeinfo>
#include <functional>
#include <iostream>
#include <string>
#include <vector>

namespace tmp {

// ---------------------------------------------------------------------------
// 示例1：简单的类型擦除 - Drawable
// ---------------------------------------------------------------------------

// 使用虚函数实现类型擦除
class Drawable {
public:
    template <typename T>
    Drawable(T obj)
        : pimpl_(std::make_unique<Model<T>>(std::move(obj))) {}

    // 拷贝构造
    Drawable(const Drawable& other)
        : pimpl_(other.pimpl_->clone()) {}

    Drawable& operator=(const Drawable& other) {
        pimpl_ = other.pimpl_->clone();
        return *this;
    }

    Drawable(Drawable&&) = default;
    Drawable& operator=(Drawable&&) = default;

    void draw() const {
        pimpl_->draw();
    }

private:
    // 概念接口（抽象基类）
    struct Concept {
        virtual ~Concept() = default;
        virtual void draw() const = 0;
        virtual std::unique_ptr<Concept> clone() const = 0;
    };

    // 模型（具体实现）
    template <typename T>
    struct Model : Concept {
        T object_;

        explicit Model(T obj) : object_(std::move(obj)) {}

        void draw() const override {
            object_.draw();
        }

        std::unique_ptr<Concept> clone() const override {
            return std::make_unique<Model<T>>(object_);
        }
    };

    std::unique_ptr<Concept> pimpl_;
};

// ---------------------------------------------------------------------------
// 示例2：通用的类型擦除容器 - Any
// ---------------------------------------------------------------------------

class Any {
public:
    Any() = default;

    template <typename T>
    Any(T value)
        : storage_(std::make_unique<StorageImpl<T>>(std::move(value))) {}

    Any(const Any& other)
        : storage_(other.storage_ ? other.storage_->clone() : nullptr) {}

    Any(Any&&) = default;

    Any& operator=(const Any& other) {
        storage_ = other.storage_ ? other.storage_->clone() : nullptr;
        return *this;
    }

    Any& operator=(Any&&) = default;

    // 获取存储的值
    template <typename T>
    T& get() {
        auto* ptr = dynamic_cast<StorageImpl<T>*>(storage_.get());
        if (!ptr) {
            throw std::bad_cast();
        }
        return ptr->value_;
    }

    template <typename T>
    const T& get() const {
        const auto* ptr = dynamic_cast<const StorageImpl<T>*>(storage_.get());
        if (!ptr) {
            throw std::bad_cast();
        }
        return ptr->value_;
    }

    // 检查是否有值
    explicit operator bool() const { return storage_ != nullptr; }

    // 获取类型信息
    const std::type_info& type() const {
        return storage_ ? storage_->type() : typeid(void);
    }

private:
    struct Storage {
        virtual ~Storage() = default;
        virtual std::unique_ptr<Storage> clone() const = 0;
        virtual const std::type_info& type() const = 0;
    };

    template <typename T>
    struct StorageImpl : Storage {
        T value_;

        explicit StorageImpl(T val) : value_(std::move(val)) {}

        std::unique_ptr<Storage> clone() const override {
            return std::make_unique<StorageImpl<T>>(value_);
        }

        const std::type_info& type() const override {
            return typeid(T);
        }
    };

    std::unique_ptr<Storage> storage_;
};

// ---------------------------------------------------------------------------
// 示例3：使用类型擦除的函数包装器
// ---------------------------------------------------------------------------

// 简化版的 std::function
template <typename Signature>
class Function;

template <typename Ret, typename... Args>
class Function<Ret(Args...)> {
public:
    Function() = default;

    // 接受任何可调用对象
    template <typename F>
    Function(F func)
        : invoker_(std::make_unique<InvokerImpl<F>>(std::move(func))) {}

    // 调用
    Ret operator()(Args... args) const {
        if (!invoker_) throw std::bad_function_call();
        return invoker_->invoke(std::forward<Args>(args)...);
    }

    explicit operator bool() const { return invoker_ != nullptr; }

private:
    struct Invoker {
        virtual ~Invoker() = default;
        virtual Ret invoke(Args... args) = 0;
        virtual std::unique_ptr<Invoker> clone() const = 0;
    };

    template <typename F>
    struct InvokerImpl : Invoker {
        F func_;

        explicit InvokerImpl(F func) : func_(std::move(func)) {}

        Ret invoke(Args... args) override {
            return func_(std::forward<Args>(args)...);
        }

        std::unique_ptr<Invoker> clone() const override {
            return std::make_unique<InvokerImpl<F>>(func_);
        }
    };

    std::unique_ptr<Invoker> invoker_;
};

// ---------------------------------------------------------------------------
// 示例4：带小对象优化的类型擦除
// ---------------------------------------------------------------------------

// 带 SBO (Small Buffer Optimization) 的类型擦除
template <typename Interface, std::size_t BufferSize = 64>
class SmallObject {
public:
    SmallObject() = default;

    template <typename T>
    SmallObject(T obj) {
        if constexpr (sizeof(T) <= BufferSize && alignof(T) <= alignof(std::max_align_t)) {
            // 放入栈缓冲区
            new (&buffer_) StorageImpl<T>(std::move(obj));
            storage_ = reinterpret_cast<Interface*>(&buffer_);
        } else {
            // 使用堆分配
            heap_storage_ = std::make_unique<HeapStorageImpl<T>>(std::move(obj));
            storage_ = heap_storage_.get();
        }
    }

    Interface* operator->() { return storage_; }
    const Interface* operator->() const { return storage_; }

private:
    // 堆存储
    struct HeapStorage : Interface {
        virtual ~HeapStorage() = default;
    };

    template <typename T>
    struct HeapStorageImpl : HeapStorage {
        T object_;
        explicit HeapStorageImpl(T obj) : object_(std::move(obj)) {}
    };

    // 栈存储
    template <typename T>
    struct StorageImpl : Interface {
        T object_;
        explicit StorageImpl(T obj) : object_(std::move(obj)) {}
    };

    alignas(std::max_align_t) char buffer_[BufferSize];
    Interface* storage_ = nullptr;
    std::unique_ptr<HeapStorage> heap_storage_;
};

// ---------------------------------------------------------------------------
// 示例5：类型擦除的迭代器
// ---------------------------------------------------------------------------

// 类型擦除的迭代器接口
template <typename ValueType>
class AnyIterator {
public:
    using value_type = ValueType;
    using reference = ValueType&;
    using pointer = ValueType*;
    using difference_type = std::ptrdiff_t;
    using iterator_category = std::forward_iterator_tag;

    template <typename Iter>
    AnyIterator(Iter it)
        : pimpl_(std::make_unique<Impl<Iter>>(std::move(it))) {}

    AnyIterator(const AnyIterator& other)
        : pimpl_(other.pimpl_->clone()) {}

    AnyIterator& operator++() {
        pimpl_->increment();
        return *this;
    }

    ValueType& operator*() const {
        return pimpl_->dereference();
    }

    bool operator==(const AnyIterator& other) const {
        return pimpl_->equal(*other.pimpl_);
    }

    bool operator!=(const AnyIterator& other) const {
        return !(*this == other);
    }

private:
    struct Concept {
        virtual ~Concept() = default;
        virtual void increment() = 0;
        virtual ValueType& dereference() const = 0;
        virtual bool equal(const Concept& other) const = 0;
        virtual std::unique_ptr<Concept> clone() const = 0;
    };

    template <typename Iter>
    struct Impl : Concept {
        Iter iter_;

        explicit Impl(Iter it) : iter_(std::move(it)) {}

        void increment() override { ++iter_; }
        ValueType& dereference() const override { return *iter_; }

        bool equal(const Concept& other) const override {
            const auto& other_impl = dynamic_cast<const Impl&>(other);
            return iter_ == other_impl.iter_;
        }

        std::unique_ptr<Concept> clone() const override {
            return std::make_unique<Impl>(iter_);
        }
    };

    std::unique_ptr<Concept> pimpl_;
};

} // namespace tmp
