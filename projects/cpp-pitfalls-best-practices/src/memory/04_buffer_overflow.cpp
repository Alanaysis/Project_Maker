/**
 * @file 04_buffer_overflow.cpp
 * @brief 缓冲区溢出陷阱示例
 *
 * 缓冲区溢出 (Buffer Overflow)：访问超出数组边界的内存
 * 危害：程序崩溃、数据损坏、安全漏洞
 */

#include <iostream>
#include <vector>
#include <array>
#include <string>
#include <cstring>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：数组越界
 *
 * 问题：访问超出数组边界的元素
 */
void bad_array_out_of_bounds() {
    int arr[5] = {1, 2, 3, 4, 5};
    // arr[5] 越界，下标 0-4 有效
    // std::cout << arr[5] << std::endl;  // 未定义行为
}

/**
 * 错误示例 2：字符串溢出
 *
 * 问题：strcpy 不检查边界
 */
void bad_string_overflow() {
    char dest[5];
    strcpy(dest, "Hello World");  // 溢出！
    // "Hello World" 需要 12 字节
}

/**
 * 错误示例 3：循环越界
 *
 * 问题：循环条件错误导致越界
 */
void bad_loop_overflow() {
    int arr[5] = {1, 2, 3, 4, 5};
    for (int i = 0; i <= 5; i++) {  // 错误：应该是 i < 5
        std::cout << arr[i] << " ";
    }
    std::cout << std::endl;
}

/**
 * 错误示例 4：指针运算越界
 *
 * 问题：指针运算超出有效范围
 */
void bad_pointer_overflow() {
    int arr[5] = {1, 2, 3, 4, 5};
    int* ptr = arr;
    ptr += 10;  // 超出范围
    // *ptr = 100;  // 未定义行为
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用 std::array
 *
 * 解决方案：std::array 有边界检查（at() 方法）
 */
void good_std_array() {
    std::array<int, 5> arr = {1, 2, 3, 4, 5};

    // 使用 at() 进行边界检查
    try {
        std::cout << "arr.at(2): " << arr.at(2) << std::endl;
        std::cout << "arr.at(10): ";  // 越界，抛出异常
        std::cout << arr.at(10) << std::endl;
    } catch (const std::out_of_range& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
}

/**
 * 正确示例 2：使用 std::vector
 *
 * 解决方案：vector 的 at() 方法进行边界检查
 */
void good_std_vector() {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    try {
        std::cout << "vec.at(2): " << vec.at(2) << std::endl;
        std::cout << "vec.at(10): ";  // 越界，抛出异常
        std::cout << vec.at(10) << std::endl;
    } catch (const std::out_of_range& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
}

/**
 * 正确示例 3：使用 std::string
 *
 * 解决方案：string 的 at() 方法进行边界检查
 */
void good_std_string() {
    std::string str = "Hello";

    try {
        std::cout << "str.at(0): " << str.at(0) << std::endl;
        std::cout << "str.at(10): ";  // 越界，抛出异常
        std::cout << str.at(10) << std::endl;
    } catch (const std::out_of_range& e) {
        std::cout << "捕获异常: " << e.what() << std::endl;
    }
}

/**
 * 正确示例 4：使用 strncpy 代替 strcpy
 *
 * 解决方案：strncpy 限制复制长度
 */
void good_strncpy() {
    char dest[5];
    strncpy(dest, "Hello World", sizeof(dest) - 1);
    dest[sizeof(dest) - 1] = '\0';  // 确保 null 结尾
    std::cout << "dest: " << dest << std::endl;
}

/**
 * 正确示例 5：使用 std::span (C++20)
 *
 * 解决方案：span 提供安全的数组视图
 */
#include <span>

void good_std_span() {
    int arr[5] = {1, 2, 3, 4, 5};
    std::span<int> sp(arr);

    // span 提供 size() 方法
    for (size_t i = 0; i < sp.size(); i++) {
        std::cout << sp[i] << " ";
    }
    std::cout << std::endl;
}

/**
 * 正确示例 6：使用范围 for 循环
 *
 * 解决方案：范围 for 自动处理边界
 */
void good_range_for() {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    // 自动遍历，不会越界
    for (const auto& val : vec) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 缓冲区溢出陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 数组越界" << std::endl;
    std::cout << "问题：访问超出数组边界的元素" << std::endl;
    std::cout << "结果：未定义行为" << std::endl;
    // bad_array_out_of_bounds();  // 注释掉
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用 std::array" << std::endl;
    good_std_array();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 std::vector" << std::endl;
    good_std_vector();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 std::string" << std::endl;
    good_std_string();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 strncpy" << std::endl;
    good_strncpy();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用 std::span" << std::endl;
    good_std_span();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用范围 for 循环" << std::endl;
    good_range_for();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
