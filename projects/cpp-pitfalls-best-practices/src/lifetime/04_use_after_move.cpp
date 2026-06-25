/**
 * @file 04_use_after_move.cpp
 * @brief 移动后使用陷阱示例
 *
 * 移动后使用：对象被移动后继续使用
 * 危害：未定义行为、数据损坏、程序崩溃
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <utility>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：使用已移动的字符串
 *
 * 问题：字符串被移动后处于有效但未指定状态
 */
void bad_string_after_move() {
    std::string str = "hello";
    std::string other = std::move(str);
    // str 处于有效但未指定状态
    std::cout << str << std::endl;  // 可能输出空字符串
}

/**
 * 错误示例 2：使用已移动的容器
 *
 * 问题：容器被移动后为空
 */
void bad_vector_after_move() {
    std::vector<int> vec = {1, 2, 3};
    std::vector<int> other = std::move(vec);
    // vec 为空
    std::cout << "vec 大小: " << vec.size() << std::endl;  // 0
    // std::cout << vec[0] << std::endl;  // 未定义行为
}

/**
 * 错误示例 3：使用已移动的智能指针
 *
 * 问题：unique_ptr 被移动后为空
 */
void bad_unique_ptr_after_move() {
    auto ptr = std::make_unique<int>(42);
    auto other = std::move(ptr);
    // ptr 为空
    // std::cout << *ptr << std::endl;  // 未定义行为
}

/**
 * 错误示例 4：移动后继续使用
 *
 * 问题：移动后对象状态不确定
 */
void bad_use_after_move() {
    std::vector<int> vec = {1, 2, 3};
    auto it = vec.begin();

    std::vector<int> other = std::move(vec);
    // it 可能失效
    // std::cout << *it << std::endl;  // 未定义行为
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：移动后重置
 *
 * 解决方案：移动后将对象重置为有效状态
 */
void good_reset_after_move() {
    std::string str = "hello";
    std::string other = std::move(str);
    str.clear();  // 明确重置
    str = "new value";  // 重新赋值
    std::cout << str << std::endl;
}

/**
 * 正确示例 2：检查移动后状态
 *
 * 解决方案：移动后检查对象状态
 */
void good_check_after_move() {
    std::vector<int> vec = {1, 2, 3};
    std::vector<int> other = std::move(vec);

    if (vec.empty()) {
        std::cout << "vec 已移动" << std::endl;
    }

    // 重新使用
    vec = {4, 5, 6};
    std::cout << "vec 大小: " << vec.size() << std::endl;
}

/**
 * 正确示例 3：使用移动后重新初始化
 *
 * 解决方案：移动后重新初始化对象
 */
void good_reinit_after_move() {
    std::unique_ptr<int> ptr = std::make_unique<int>(42);
    std::unique_ptr<int> other = std::move(ptr);

    // 重新初始化
    ptr = std::make_unique<int>(100);
    std::cout << *ptr << std::endl;
}

/**
 * 正确示例 4：使用 std::exchange
 *
 * 解决方案：使用 exchange 同时移动和赋值
 */
void good_exchange() {
    std::string str = "hello";
    std::string other = std::exchange(str, "world");
    std::cout << "other: " << other << std::endl;
    std::cout << "str: " << str << std::endl;
}

/**
 * 正确示例 5：使用移动语义的函数
 *
 * 解决方案：函数参数使用移动语义
 */
class GoodContainer {
public:
    void set_data(std::vector<int> data) {
        data_ = std::move(data);  // 移动赋值
    }

    const std::vector<int>& get_data() const { return data_; }

private:
    std::vector<int> data_;
};

void good_move_function() {
    std::vector<int> vec = {1, 2, 3};
    GoodContainer container;
    container.set_data(std::move(vec));
    // vec 已移动，但 container 拥有数据
    std::cout << "容器大小: " << container.get_data().size() << std::endl;
}

/**
 * 正确示例 6：使用移动迭代器
 *
 * 解决方案：使用移动迭代器批量移动
 */
void good_move_iterator() {
    std::vector<std::string> src = {"hello", "world", "foo"};
    std::vector<std::string> dst;

    // 使用移动迭代器
    dst.insert(dst.end(),
               std::make_move_iterator(src.begin()),
               std::make_move_iterator(src.end()));

    // src 中的字符串已被移动
    for (auto& s : src) {
        std::cout << "'" << s << "' ";
    }
    std::cout << std::endl;

    for (auto& s : dst) {
        std::cout << "'" << s << "' ";
    }
    std::cout << std::endl;
}

/**
 * 正确示例 7：使用 RAII 和移动语义
 *
 * 解决方案：RAII 类正确实现移动语义
 */
class GoodResource {
public:
    GoodResource() : data_(new int(42)) {
        std::cout << "构造" << std::endl;
    }

    ~GoodResource() {
        delete data_;
        std::cout << "析构" << std::endl;
    }

    // 移动构造函数
    GoodResource(GoodResource&& other) noexcept : data_(other.data_) {
        other.data_ = nullptr;
        std::cout << "移动构造" << std::endl;
    }

    // 移动赋值运算符
    GoodResource& operator=(GoodResource&& other) noexcept {
        if (this != &other) {
            delete data_;
            data_ = other.data_;
            other.data_ = nullptr;
            std::cout << "移动赋值" << std::endl;
        }
        return *this;
    }

    int get() const { return data_ ? *data_ : 0; }

private:
    int* data_;
};

void good_raii_move() {
    GoodResource r1;
    GoodResource r2 = std::move(r1);
    std::cout << "r1: " << r1.get() << std::endl;
    std::cout << "r2: " << r2.get() << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 移动后使用陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 使用已移动的字符串" << std::endl;
    std::cout << "问题：字符串被移动后处于有效但未指定状态" << std::endl;
    bad_string_after_move();
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 移动后重置" << std::endl;
    good_reset_after_move();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 检查移动后状态" << std::endl;
    good_check_after_move();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 移动后重新初始化" << std::endl;
    good_reinit_after_move();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 exchange" << std::endl;
    good_exchange();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用移动语义的函数" << std::endl;
    good_move_function();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用移动迭代器" << std::endl;
    good_move_iterator();
    std::cout << std::endl;

    std::cout << "[正确示例 7] 使用 RAII 和移动语义" << std::endl;
    good_raii_move();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
