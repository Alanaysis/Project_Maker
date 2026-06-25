/**
 * 智能指针测试
 */

#include <gtest/gtest.h>
#include <memory>
#include <vector>
#include <string>

// 测试 unique_ptr 基本操作
TEST(SmartPointers, UniquePtrBasic) {
    auto ptr = std::make_unique<int>(42);
    EXPECT_EQ(*ptr, 42);
    EXPECT_NE(ptr, nullptr);
}

// 测试 unique_ptr 移动
TEST(SmartPointers, UniquePtrMove) {
    auto ptr1 = std::make_unique<int>(42);
    auto ptr2 = std::move(ptr1);

    EXPECT_EQ(*ptr2, 42);
    EXPECT_EQ(ptr1, nullptr);
}

// 测试 unique_ptr 重置
TEST(SmartPointers, UniquePtrReset) {
    auto ptr = std::make_unique<int>(42);
    ptr.reset();

    EXPECT_EQ(ptr, nullptr);
}

// 测试 unique_ptr 释放所有权
TEST(SmartPointers, UniquePtrRelease) {
    auto ptr = std::make_unique<int>(42);
    int* raw = ptr.release();

    EXPECT_EQ(ptr, nullptr);
    EXPECT_EQ(*raw, 42);
    delete raw;
}

// 测试 unique_ptr 与容器
TEST(SmartPointers, UniquePtrContainer) {
    std::vector<std::unique_ptr<int>> vec;
    vec.push_back(std::make_unique<int>(1));
    vec.push_back(std::make_unique<int>(2));
    vec.push_back(std::make_unique<int>(3));

    EXPECT_EQ(*vec[0], 1);
    EXPECT_EQ(*vec[1], 2);
    EXPECT_EQ(*vec[2], 3);
}

// 测试 shared_ptr 基本操作
TEST(SmartPointers, SharedPtrBasic) {
    auto ptr = std::make_shared<int>(42);
    EXPECT_EQ(*ptr, 42);
    EXPECT_EQ(ptr.use_count(), 1);
}

// 测试 shared_ptr 共享
TEST(SmartPointers, SharedPtrSharing) {
    auto ptr1 = std::make_shared<int>(42);
    auto ptr2 = ptr1;

    EXPECT_EQ(*ptr1, 42);
    EXPECT_EQ(*ptr2, 42);
    EXPECT_EQ(ptr1.use_count(), 2);
    EXPECT_EQ(ptr2.use_count(), 2);
}

// 测试 shared_ptr 移动
TEST(SmartPointers, SharedPtrMove) {
    auto ptr1 = std::make_shared<int>(42);
    auto ptr2 = std::move(ptr1);

    EXPECT_EQ(*ptr2, 42);
    EXPECT_EQ(ptr1, nullptr);
    EXPECT_EQ(ptr2.use_count(), 1);
}

// 测试 shared_ptr 重置
TEST(SmartPointers, SharedPtrReset) {
    auto ptr = std::make_shared<int>(42);
    ptr.reset();

    EXPECT_EQ(ptr, nullptr);
}

// 测试 weak_ptr 基本操作
TEST(SmartPointers, WeakPtrBasic) {
    auto shared = std::make_shared<int>(42);
    std::weak_ptr<int> weak = shared;

    EXPECT_EQ(weak.use_count(), 1);
    EXPECT_FALSE(weak.expired());
}

// 测试 weak_ptr 锁定
TEST(SmartPointers, WeakPtrLock) {
    auto shared = std::make_shared<int>(42);
    std::weak_ptr<int> weak = shared;

    auto locked = weak.lock();
    EXPECT_NE(locked, nullptr);
    EXPECT_EQ(*locked, 42);
    EXPECT_EQ(locked.use_count(), 2);
}

// 测试 weak_ptr 过期
TEST(SmartPointers, WeakPtrExpired) {
    std::weak_ptr<int> weak;
    {
        auto shared = std::make_shared<int>(42);
        weak = shared;
        EXPECT_FALSE(weak.expired());
    }
    // shared 已销毁
    EXPECT_TRUE(weak.expired());
    EXPECT_EQ(weak.lock(), nullptr);
}

// 测试 shared_ptr 引用计数
TEST(SmartPointers, SharedPtrRefCount) {
    auto ptr1 = std::make_shared<int>(42);
    EXPECT_EQ(ptr1.use_count(), 1);

    {
        auto ptr2 = ptr1;
        EXPECT_EQ(ptr1.use_count(), 2);
        EXPECT_EQ(ptr2.use_count(), 2);
    }
    // ptr2 已销毁
    EXPECT_EQ(ptr1.use_count(), 1);
}

// 测试自定义删除器
TEST(SmartPointers, CustomDeleter) {
    bool deleted = false;
    auto deleter = [&deleted](int* ptr) {
        deleted = true;
        delete ptr;
    };

    {
        std::unique_ptr<int, decltype(deleter)> ptr(new int(42), deleter);
        EXPECT_EQ(*ptr, 42);
        EXPECT_FALSE(deleted);
    }
    EXPECT_TRUE(deleted);
}

// 测试 shared_ptr 自定义删除器
TEST(SmartPointers, SharedPtrCustomDeleter) {
    bool deleted = false;
    auto deleter = [&deleted](int* ptr) {
        deleted = true;
        delete ptr;
    };

    {
        std::shared_ptr<int> ptr(new int(42), deleter);
        EXPECT_EQ(*ptr, 42);
        EXPECT_FALSE(deleted);
    }
    EXPECT_TRUE(deleted);
}

// 测试 weak_ptr 打破循环引用
TEST(SmartPointers, WeakPtrBreakCycle) {
    struct Node {
        std::shared_ptr<Node> next;
        std::weak_ptr<Node> prev;
        int value;

        Node(int v) : value(v) {}
    };

    auto node1 = std::make_shared<Node>(1);
    auto node2 = std::make_shared<Node>(2);

    node1->next = node2;
    node2->prev = node1;

    EXPECT_EQ(node1.use_count(), 1);
    EXPECT_EQ(node2.use_count(), 2);  // node1->next 引用 node2

    auto locked = node2->prev.lock();
    EXPECT_NE(locked, nullptr);
    EXPECT_EQ(locked->value, 1);
}

// 测试智能指针与多态
TEST(SmartPointers, Polymorphism) {
    struct Base {
        virtual ~Base() = default;
        virtual int value() const = 0;
    };

    struct Derived : Base {
        int value() const override { return 42; }
    };

    std::unique_ptr<Base> ptr = std::make_unique<Derived>();
    EXPECT_EQ(ptr->value(), 42);
}

// 测试 make_unique 和 make_shared
TEST(SmartPointers, MakeFunctions) {
    auto unique = std::make_unique<int>(42);
    auto shared = std::make_shared<int>(42);

    EXPECT_EQ(*unique, 42);
    EXPECT_EQ(*shared, 42);
}

// 测试智能指针数组
TEST(SmartPointers, UniquePtrArray) {
    auto arr = std::make_unique<int[]>(5);
    for (int i = 0; i < 5; ++i) {
        arr[i] = i * 10;
    }

    EXPECT_EQ(arr[0], 0);
    EXPECT_EQ(arr[4], 40);
}
