#include <iostream>
#include <vector>
#include <cstring>

/**
 * @file cppcheck_demo.cpp
 * @brief Cppcheck 静态分析示例
 *
 * 演示 Cppcheck 能够检测的各种代码问题。
 * Cppcheck 是一个开源的 C/C++ 静态分析工具。
 *
 * 主要检查:
 * - 内存泄漏
 * - 空指针解引用
 * - 数组越界
 * - 未初始化变量
 * - 未使用变量
 * - 缓冲区溢出
 */

// ============================================================================
// 1. 内存泄漏示例
// ============================================================================
void memory_leak_example() {
    // Cppcheck 会检测到内存泄漏
    int* ptr = new int[10];
    // 忘记 delete[] ptr;

    // 正确做法:
    delete[] ptr;
}

// ============================================================================
// 2. 空指针解引用示例
// ============================================================================
void null_pointer_example() {
    int* ptr = nullptr;

    // Cppcheck 会检测到潜在的空指针解引用
    // if (ptr != nullptr) {
    //     *ptr = 42;  // 正确
    // }

    // 正确做法: 检查后再使用
    if (ptr != nullptr) {
        *ptr = 42;
    }
}

// ============================================================================
// 3. 未初始化变量示例
// ============================================================================
void uninitialized_variable_example() {
    int x;
    // Cppcheck 会检测到未初始化变量
    // std::cout << x << std::endl;

    // 正确做法: 初始化变量
    x = 0;
    std::cout << x << std::endl;
}

// ============================================================================
// 4. 数组越界示例
// ============================================================================
void array_bounds_example() {
    int arr[5] = {1, 2, 3, 4, 5};

    // Cppcheck 会检测到数组越界
    // arr[10] = 42;

    // 正确做法: 使用正确的索引
    for (int i = 0; i < 5; ++i) {
        arr[i] = i * 2;
    }
}

// ============================================================================
// 5. 资源泄漏示例
// ============================================================================
void resource_leak_example() {
    FILE* file = fopen("test.txt", "r");
    if (file == nullptr) {
        return;
    }

    // Cppcheck 会检测到资源泄漏
    // 如果忘记 fclose(file);

    // 正确做法: 确保关闭文件
    fclose(file);
}

// ============================================================================
// 6. 使用 RAII 避免泄漏
// ============================================================================
class Resource {
public:
    Resource() : data_(new int[100]) {
        std::cout << "Resource 创建" << std::endl;
    }
    ~Resource() {
        delete[] data_;
        std::cout << "Resource 销毁" << std::endl;
    }

    // 禁用拷贝
    Resource(const Resource&) = delete;
    Resource& operator=(const Resource&) = delete;

    // 启用移动
    Resource(Resource&&) noexcept = default;
    Resource& operator=(Resource&&) noexcept = default;

private:
    int* data_;
};

void raii_example() {
    // 使用 RAII 自动管理资源
    Resource res;
    // 离开作用域时自动释放
}

int main() {
    std::cout << "=== Cppcheck 静态分析示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "Cppcheck 检查类别:" << std::endl;
    std::cout << "  --enable=all      : 启用所有检查" << std::endl;
    std::cout << "  --enable=warning  : 警告" << std::endl;
    std::cout << "  --enable=style    : 代码风格" << std::endl;
    std::cout << "  --enable=performance : 性能" << std::endl;
    std::cout << "  --enable=portability : 可移植性" << std::endl;
    std::cout << "  --enable=information : 信息" << std::endl;
    std::cout << std::endl;

    // 运行示例
    memory_leak_example();
    null_pointer_example();
    uninitialized_variable_example();
    array_bounds_example();
    resource_leak_example();
    raii_example();

    std::cout << std::endl;
    std::cout << "Cppcheck 使用方法:" << std::endl;
    std::cout << "  1. 在 CMakeLists.txt 中设置 CMAKE_CXX_CPPCHECK" << std::endl;
    std::cout << "  2. 运行 cmake --build . 时自动检查" << std::endl;
    std::cout << "  3. 或手动运行: cppcheck --enable=all src/" << std::endl;

    return 0;
}
