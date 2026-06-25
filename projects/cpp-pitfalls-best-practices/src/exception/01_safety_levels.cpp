/**
 * @file 01_safety_levels.cpp
 * @brief 异常安全级别示例
 *
 * 异常安全级别：
 * 1. 不抛出保证 (No-throw guarantee)
 * 2. 强异常安全保证 (Strong exception safety)
 * 3. 基本异常安全保证 (Basic exception safety)
 * 4. 无保证 (No guarantee)
 */

#include <iostream>
#include <vector>
#include <memory>
#include <string>
#include <stdexcept>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：无异常安全保证
 *
 * 问题：异常发生时资源泄漏
 */
class BadContainer {
public:
    void push_back(int value) {
        if (size_ == capacity_) {
            // 扩容
            int* new_data = new int[capacity_ * 2];
            for (size_t i = 0; i < size_; i++) {
                new_data[i] = data_[i];  // 如果这里抛出异常
            }
            delete[] data_;  // 不会执行
            data_ = new_data;
            capacity_ *= 2;
        }
        data_[size_++] = value;
    }

private:
    int* data_ = nullptr;
    size_t size_ = 0;
    size_t capacity_ = 0;
};

/**
 * 错误示例 2：基本保证失败
 *
 * 问题：异常发生时状态不一致
 */
class BadTransaction {
public:
    void transfer(int& from, int& to, int amount) {
        from -= amount;
        // 如果这里抛出异常，from 已修改但 to 未修改
        to += amount;
    }
};

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：不抛出保证
 *
 * 解决方案：使用 noexcept 标记不抛出异常的函数
 */
void good_no_throw() noexcept {
    // 这个函数保证不抛出异常
    int a = 1;
    int b = 2;
    int c = a + b;
    (void)c;
}

/**
 * 正确示例 2：强异常安全保证
 *
 * 解决方案：使用 copy-and-swap 惯用法
 */
class GoodContainer {
public:
    void push_back(int value) {
        if (size_ == capacity_) {
            // 创建新容器（可能抛出异常）
            auto new_data = std::make_unique<int[]>(capacity_ * 2);
            for (size_t i = 0; i < size_; i++) {
                new_data[i] = data_[i];
            }
            // 交换（不抛出异常）
            data_.swap(new_data);
            capacity_ *= 2;
        }
        data_[size_++] = value;
    }

private:
    std::unique_ptr<int[]> data_;
    size_t size_ = 0;
    size_t capacity_ = 0;
};

/**
 * 正确示例 3：使用 RAII 保证资源释放
 *
 * 解决方案：RAII 类在析构时释放资源
 */
class GoodResource {
public:
    GoodResource() : data_(new int(42)) {
        std::cout << "获取资源" << std::endl;
    }

    ~GoodResource() {
        delete data_;
        std::cout << "释放资源" << std::endl;
    }

    // 禁止拷贝
    GoodResource(const GoodResource&) = delete;
    GoodResource& operator=(const GoodResource&) = delete;

private:
    int* data_;
};

void good_raii() {
    GoodResource res;
    throw std::runtime_error("error");
    // res 自动释放
}

/**
 * 正确示例 4：强异常安全的事务
 *
 * 解决方案：先准备，再提交
 */
class GoodTransaction {
public:
    void transfer(int& from, int& to, int amount) {
        // 先准备（可能抛出异常）
        int new_from = from - amount;
        int new_to = to + amount;

        // 再提交（不抛出异常）
        from = new_from;
        to = new_to;
    }
};

/**
 * 正确示例 5：使用 std::unique_lock
 *
 * 解决方案：使用 RAII 管理锁
 */
#include <mutex>

std::mutex good_mutex;

void good_lock() {
    std::unique_lock<std::mutex> lock(good_mutex);
    // 可能抛出异常
    throw std::runtime_error("error");
    // 锁自动释放
}

/**
 * 正确示例 6：使用智能指针
 *
 * 解决方案：使用智能指针自动管理内存
 */
void good_smart_pointer() {
    auto ptr = std::make_unique<int>(42);
    // 可能抛出异常
    throw std::runtime_error("error");
    // ptr 自动释放
}

/**
 * 正确示例 7：基本异常安全保证
 *
 * 解决方案：保证资源不泄漏，但状态可能改变
 */
class GoodBasicSafe {
public:
    void add(int value) {
        auto temp = std::make_unique<int[]>(size_ + 1);
        for (size_t i = 0; i < size_; i++) {
            temp[i] = data_[i];
        }
        temp[size_] = value;
        data_.swap(temp);
        size_++;
    }

private:
    std::unique_ptr<int[]> data_;
    size_t size_ = 0;
};

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 异常安全级别示例 ===" << std::endl;
    std::cout << std::endl;

    // 不抛出保证
    std::cout << "[示例 1] 不抛出保证" << std::endl;
    good_no_throw();
    std::cout << "函数保证不抛出异常" << std::endl;
    std::cout << std::endl;

    // 强异常安全保证
    std::cout << "[示例 2] 强异常安全保证" << std::endl;
    try {
        good_raii();
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    // 事务示例
    std::cout << "[示例 3] 强异常安全的事务" << std::endl;
    int from = 100;
    int to = 50;
    GoodTransaction transaction;
    transaction.transfer(from, to, 30);
    std::cout << "from: " << from << ", to: " << to << std::endl;
    std::cout << std::endl;

    // 智能指针示例
    std::cout << "[示例 4] 使用智能指针" << std::endl;
    try {
        good_smart_pointer();
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    // 基本异常安全保证
    std::cout << "[示例 5] 基本异常安全保证" << std::endl;
    GoodBasicSafe safe;
    safe.add(1);
    safe.add(2);
    std::cout << "添加成功" << std::endl;
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
