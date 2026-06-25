/**
 * 移动语义测试
 */

#include <gtest/gtest.h>
#include <vector>
#include <string>
#include <memory>

// 测试 Buffer 类的移动语义
class Buffer {
    int* data_;
    size_t size_;

public:
    Buffer() : data_(nullptr), size_(0) {}

    explicit Buffer(size_t size) : data_(new int[size]()), size_(size) {}

    Buffer(const Buffer& other) : data_(new int[other.size_]), size_(other.size_) {
        std::copy(other.data_, other.data_ + size_, data_);
    }

    Buffer(Buffer&& other) noexcept : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }

    Buffer& operator=(const Buffer& other) {
        if (this != &other) {
            delete[] data_;
            size_ = other.size_;
            data_ = new int[size_];
            std::copy(other.data_, other.data_ + size_, data_);
        }
        return *this;
    }

    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }

    ~Buffer() {
        delete[] data_;
    }

    size_t size() const { return size_; }
    int* data() const { return data_; }
};

// 测试移动构造函数
TEST(MoveSemantics, MoveConstructor) {
    Buffer buf1(100);
    Buffer buf2 = std::move(buf1);

    EXPECT_EQ(buf2.size(), 100);
    EXPECT_EQ(buf1.size(), 0);
    EXPECT_EQ(buf1.data(), nullptr);
}

// 测试移动赋值运算符
TEST(MoveSemantics, MoveAssignment) {
    Buffer buf1(100);
    Buffer buf2;
    buf2 = std::move(buf1);

    EXPECT_EQ(buf2.size(), 100);
    EXPECT_EQ(buf1.size(), 0);
    EXPECT_EQ(buf1.data(), nullptr);
}

// 测试拷贝构造函数
TEST(MoveSemantics, CopyConstructor) {
    Buffer buf1(100);
    Buffer buf2 = buf1;

    EXPECT_EQ(buf2.size(), 100);
    EXPECT_EQ(buf1.size(), 100);
    EXPECT_NE(buf1.data(), buf2.data());
}

// 测试拷贝赋值运算符
TEST(MoveSemantics, CopyAssignment) {
    Buffer buf1(100);
    Buffer buf2;
    buf2 = buf1;

    EXPECT_EQ(buf2.size(), 100);
    EXPECT_EQ(buf1.size(), 100);
    EXPECT_NE(buf1.data(), buf2.data());
}

// 测试 std::move
TEST(MoveSemantics, StdMove) {
    std::string s1 = "Hello";
    std::string s2 = std::move(s1);

    EXPECT_EQ(s2, "Hello");
    EXPECT_TRUE(s1.empty());
}

// 测试容器移动
TEST(MoveSemantics, ContainerMove) {
    std::vector<int> v1 = {1, 2, 3, 4, 5};
    std::vector<int> v2 = std::move(v1);

    EXPECT_EQ(v2.size(), 5);
    EXPECT_TRUE(v1.empty());
}

// 测试 unique_ptr 移动
TEST(MoveSemantics, UniquePtrMove) {
    auto ptr1 = std::make_unique<int>(42);
    auto ptr2 = std::move(ptr1);

    EXPECT_EQ(*ptr2, 42);
    EXPECT_EQ(ptr1, nullptr);
}

// 测试 noexcept 标记
TEST(MoveSemantics, NoexceptMove) {
    EXPECT_TRUE(std::is_nothrow_move_constructible<Buffer>::value);
    EXPECT_TRUE(std::is_nothrow_move_assignable<Buffer>::value);
}

// 测试移动后状态
TEST(MoveSemantics, MovedFromState) {
    Buffer buf(100);
    Buffer moved = std::move(buf);

    // 移动后的对象应该处于有效但未指定的状态
    EXPECT_EQ(buf.size(), 0);
    EXPECT_EQ(buf.data(), nullptr);
}

// 测试自移动赋值
TEST(MoveSemantics, SelfMoveAssignment) {
    Buffer buf(100);
    buf = std::move(buf);

    // 自移动赋值应该安全
    EXPECT_EQ(buf.size(), 100);
}
