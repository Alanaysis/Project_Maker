/**
 * @file 01_code_review.cpp
 * @brief 代码审查清单示例
 *
 * 代码审查：检查代码质量、安全性和可维护性
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <stdexcept>

// ============================================================================
// 代码审查清单
// ============================================================================

/**
 * 审查点 1：内存管理
 *
 * 检查：
 * - 是否有内存泄漏
 * - 是否有悬空指针
 * - 是否正确使用智能指针
 */
class MemoryCheck {
public:
    // 不好的做法
    void bad_memory() {
        int* ptr = new int(42);
        // 忘记 delete
    }

    // 好的做法
    void good_memory() {
        auto ptr = std::make_unique<int>(42);
        // 自动释放
    }
};

/**
 * 审查点 2：异常安全
 *
 * 检查：
 * - 是否有资源泄漏
 * - 异常安全级别
 * - 是否正确使用 RAII
 */
class ExceptionCheck {
public:
    // 不好的做法
    void bad_exception() {
        int* ptr = new int(42);
        throw std::runtime_error("error");
        delete ptr;  // 不会执行
    }

    // 好的做法
    void good_exception() {
        auto ptr = std::make_unique<int>(42);
        throw std::runtime_error("error");
        // ptr 自动释放
    }
};

/**
 * 审查点 3：线程安全
 *
 * 检查：
 * - 是否有数据竞争
 * - 是否正确使用同步原语
 * - 是否有死锁风险
 */
#include <mutex>

class ThreadCheck {
public:
    // 不好的做法
    int bad_counter = 0;
    void bad_increment() {
        bad_counter++;  // 数据竞争
    }

    // 好的做法
    std::mutex mutex_;
    int good_counter = 0;
    void good_increment() {
        std::lock_guard<std::mutex> lock(mutex_);
        good_counter++;
    }
};

/**
 * 审查点 4：输入验证
 *
 * 检查：
 * - 是否验证输入参数
 * - 是否处理边界情况
 * - 是否防止缓冲区溢出
 */
class InputCheck {
public:
    // 不好的做法
    void bad_input(const char* str) {
        // 未检查空指针
        std::cout << str << std::endl;
    }

    // 好的做法
    void good_input(const char* str) {
        if (str == nullptr) {
            throw std::invalid_argument("str is null");
        }
        std::cout << str << std::endl;
    }
};

/**
 * 审查点 5：类型安全
 *
 * 检查：
 * - 是否有隐式转换
 * - 是否有类型截断
 * - 是否正确使用类型系统
 */
class TypeCheck {
public:
    // 不好的做法
    void bad_type() {
        double d = 3.14;
        int i = d;  // 隐式转换，精度丢失
        std::cout << i << std::endl;
    }

    // 好的做法
    void good_type() {
        double d = 3.14;
        int i = static_cast<int>(d);  // 显式转换
        std::cout << i << std::endl;
    }
};

/**
 * 审查点 6：资源管理
 *
 * 检查：
 * - 是否正确释放资源
 * - 是否使用 RAII
 * - 是否有资源泄漏
 */
class ResourceCheck {
public:
    // 不好的做法
    void bad_resource() {
        FILE* file = fopen("test.txt", "w");
        if (!file) return;
        // 使用文件
        // 忘记 fclose
    }

    // 好的做法
    void good_resource() {
        std::ofstream file("test.txt");
        if (!file.is_open()) return;
        // 使用文件
        // 自动关闭
    }
};

/**
 * 审查点 7：错误处理
 *
 * 检查：
 * - 是否处理所有错误情况
 * - 是否有明确的错误处理策略
 * - 是否记录错误信息
 */
class ErrorCheck {
public:
    // 不好的做法
    void bad_error() {
        try {
            // 可能抛出异常的操作
        } catch (...) {
            // 忽略错误
        }
    }

    // 好的做法
    void good_error() {
        try {
            // 可能抛出异常的操作
        } catch (const std::exception& e) {
            std::cerr << "错误: " << e.what() << std::endl;
            throw;  // 重新抛出或处理
        }
    }
};

/**
 * 审查点 8：代码风格
 *
 * 检查：
 * - 是否遵循命名规范
 * - 是否有适当的注释
 * - 是否有清晰的代码结构
 */
class StyleCheck {
public:
    // 不好的做法
    void bad_style() {
        int x = 42;
        int y = x * 2;
        int z = y + 1;
        std::cout << z << std::endl;
    }

    // 好的做法
    void good_style() {
        const int base_value = 42;
        const int doubled_value = base_value * 2;
        const int result = doubled_value + 1;
        std::cout << result << std::endl;
    }
};

/**
 * 审查点 9：性能
 *
 * 检查：
 * - 是否有不必要的拷贝
 * - 是否有性能瓶颈
 * - 是否正确使用移动语义
 */
class PerformanceCheck {
public:
    // 不好的做法
    void bad_performance() {
        std::vector<int> vec = {1, 2, 3};
        std::vector<int> copy = vec;  // 不必要的拷贝
        std::cout << copy.size() << std::endl;
    }

    // 好的做法
    void good_performance() {
        std::vector<int> vec = {1, 2, 3};
        std::vector<int> moved = std::move(vec);  // 移动语义
        std::cout << moved.size() << std::endl;
    }
};

/**
 * 审查点 10：可维护性
 *
 * 检查：
 * - 代码是否易于理解
 * - 是否有适当的抽象
 * - 是否易于修改和扩展
 */
class MaintainabilityCheck {
public:
    // 不好的做法
    void bad_maintainability() {
        // 复杂的嵌套逻辑
        for (int i = 0; i < 10; i++) {
            if (i % 2 == 0) {
                if (i % 3 == 0) {
                    if (i % 5 == 0) {
                        std::cout << i << std::endl;
                    }
                }
            }
        }
    }

    // 好的做法
    void good_maintainability() {
        for (int i = 0; i < 10; i++) {
            if (is_special_number(i)) {
                std::cout << i << std::endl;
            }
        }
    }

private:
    bool is_special_number(int n) const {
        return n % 2 == 0 && n % 3 == 0 && n % 5 == 0;
    }
};

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 代码审查清单示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "[1] 内存管理" << std::endl;
    MemoryCheck mem;
    mem.good_memory();
    std::cout << std::endl;

    std::cout << "[2] 异常安全" << std::endl;
    ExceptionCheck exc;
    try {
        exc.good_exception();
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
    std::cout << std::endl;

    std::cout << "[3] 线程安全" << std::endl;
    ThreadCheck thread;
    thread.good_increment();
    std::cout << "计数器: " << thread.good_counter << std::endl;
    std::cout << std::endl;

    std::cout << "[4] 输入验证" << std::endl;
    InputCheck input;
    input.good_input("hello");
    std::cout << std::endl;

    std::cout << "[5] 类型安全" << std::endl;
    TypeCheck type;
    type.good_type();
    std::cout << std::endl;

    std::cout << "[6] 资源管理" << std::endl;
    ResourceCheck res;
    res.good_resource();
    std::cout << std::endl;

    std::cout << "[7] 错误处理" << std::endl;
    ErrorCheck error;
    error.good_error();
    std::cout << std::endl;

    std::cout << "[8] 代码风格" << std::endl;
    StyleCheck style;
    style.good_style();
    std::cout << std::endl;

    std::cout << "[9] 性能" << std::endl;
    PerformanceCheck perf;
    perf.good_performance();
    std::cout << std::endl;

    std::cout << "[10] 可维护性" << std::endl;
    MaintainabilityCheck maint;
    maint.good_maintainability();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
