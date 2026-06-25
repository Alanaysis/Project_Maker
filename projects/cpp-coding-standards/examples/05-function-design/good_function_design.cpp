/**
 * @file good_function_design.cpp
 * @brief 良好函数设计规范示例
 *
 * 本文件展示 C++ 函数设计规范的最佳实践，包括：
 * - 函数长度
 * - 参数设计
 * - 返回值设计
 * - 异常规范
 * - 内联函数
 */

#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include <stdexcept>
#include <algorithm>

// ============================================================================
// 函数长度示例 - 保持函数简短
// ============================================================================

/**
 * @brief 计算平均值
 *
 * 良好：函数简短，职责单一
 *
 * @param numbers 数字列表
 * @return 平均值
 */
double calculateAverage(const std::vector<double>& numbers) {
    if (numbers.empty()) {
        return 0.0;
    }

    double sum = 0.0;
    for (double num : numbers) {
        sum += num;
    }

    return sum / static_cast<double>(numbers.size());
}

/**
 * @brief 查找最大值
 *
 * 良好：函数简短，职责单一
 *
 * @param numbers 数字列表
 * @return 最大值
 */
double findMax(const std::vector<double>& numbers) {
    if (numbers.empty()) {
        throw std::invalid_argument("Cannot find max of empty list");
    }

    return *std::max_element(numbers.begin(), numbers.end());
}

/**
 * @brief 查找最小值
 *
 * 良好：函数简短，职责单一
 *
 * @param numbers 数字列表
 * @return 最小值
 */
double findMin(const std::vector<double>& numbers) {
    if (numbers.empty()) {
        throw std::invalid_argument("Cannot find min of empty list");
    }

    return *std::min_element(numbers.begin(), numbers.end());
}

// ============================================================================
// 参数设计示例 - 使用 const 引用和值传递
// ============================================================================

/**
 * @brief 连接字符串
 *
 * 良好：使用 const 引用传递大型对象
 *
 * @param first 第一个字符串
 * @param second 第二个字符串
 * @param separator 分隔符
 * @return 连接后的字符串
 */
std::string concatenate(
    const std::string& first,
    const std::string& second,
    const std::string& separator = ""
) {
    if (separator.empty()) {
        return first + second;
    }
    return first + separator + second;
}

/**
 * @brief 查找字符串
 *
 * 良好：使用 const 引用，返回 optional
 *
 * @param text 文本
 * @param pattern 模式
 * @return 位置（如果找到）
 */
std::optional<size_t> findPattern(
    const std::string& text,
    const std::string& pattern
) {
    size_t pos = text.find(pattern);
    if (pos == std::string::npos) {
        return std::nullopt;
    }
    return pos;
}

/**
 * @brief 过滤数字
 *
 * 良好：使用 const 引用，使用谓词
 *
 * @param numbers 数字列表
 * @param predicate 谓词函数
 * @return 过滤后的列表
 */
std::vector<double> filterNumbers(
    const std::vector<double>& numbers,
    std::function<bool(double)> predicate
) {
    std::vector<double> result;
    std::copy_if(numbers.begin(), numbers.end(),
                 std::back_inserter(result), predicate);
    return result;
}

// ============================================================================
// 返回值设计示例 - 使用 optional 和 expected
// ============================================================================

/**
 * @brief 解析整数
 *
 * 良好：使用 optional 表示可能失败
 *
 * @param str 字符串
 * @return 整数（如果解析成功）
 */
std::optional<int> parseInt(const std::string& str) {
    try {
        return std::stoi(str);
    } catch (const std::exception&) {
        return std::nullopt;
    }
}

/**
 * @brief 除法运算
 *
 * 良好：使用 optional 处理除零错误
 *
 * @param a 被除数
 * @param b 除数
 * @return 结果（如果除数不为零）
 */
std::optional<double> divide(double a, double b) {
    if (b == 0.0) {
        return std::nullopt;
    }
    return a / b;
}

/**
 * @brief 查找用户
 *
 * 良好：使用 optional 表示可能不存在
 *
 * @param users 用户列表
 * @param name 用户名
 * @return 用户索引（如果找到）
 */
std::optional<size_t> findUser(
    const std::vector<std::string>& users,
    const std::string& name
) {
    for (size_t i = 0; i < users.size(); ++i) {
        if (users[i] == name) {
            return i;
        }
    }
    return std::nullopt;
}

// ============================================================================
// 异常规范示例 - 使用 noexcept 和异常
// ============================================================================

/**
 * @brief 交换两个值
 *
 * 良好：使用 noexcept 标记不会抛出异常的函数
 *
 * @param a 第一个值
 * @param b 第二个值
 */
void swapValues(int& a, int& b) noexcept {
    int temp = a;
    a = b;
    b = temp;
}

/**
 * @brief 计算阶乘
 *
 * 良好：使用异常处理无效输入
 *
 * @param n 输入数
 * @return 阶乘
 * @throw std::invalid_argument 如果输入为负数
 */
int factorial(int n) {
    if (n < 0) {
        throw std::invalid_argument("Factorial of negative number");
    }

    if (n <= 1) {
        return 1;
    }

    return n * factorial(n - 1);
}

/**
 * @brief 读取文件
 *
 * 良好：使用异常处理文件错误
 *
 * @param filename 文件名
 * @return 文件内容
 * @throw std::runtime_error 如果文件无法打开
 */
std::string readFile(const std::string& filename) {
    // 模拟文件读取
    if (filename.empty()) {
        throw std::runtime_error("Filename cannot be empty");
    }

    return "File content of " + filename;
}

// ============================================================================
// 内联函数示例 - 简单函数内联
// ============================================================================

/**
 * @brief 获取绝对值
 *
 * 良好：简单函数内联
 *
 * @param x 输入值
 * @return 绝对值
 */
inline int absValue(int x) {
    return x < 0 ? -x : x;
}

/**
 * @brief 检查是否为偶数
 *
 * 良好：简单函数内联
 *
 * @param x 输入值
 * @return 是否为偶数
 */
inline bool isEven(int x) {
    return x % 2 == 0;
}

/**
 * @brief 限制值在范围内
 *
 * 良好：简单函数内联
 *
 * @param value 值
 * @param min 最小值
 * @param max 最大值
 * @return 限制后的值
 */
inline int clamp(int value, int min, int max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
}

// ============================================================================
// 演示函数
// ============================================================================

/**
 * @brief 演示良好函数设计
 */
void demonstrateGoodFunctionDesign() {
    std::cout << "=== 良好函数设计规范示例 ===" << std::endl;

    // 函数长度示例
    std::cout << "\n1. 函数长度示例 (保持简短):" << std::endl;
    std::vector<double> numbers = {1.0, 2.0, 3.0, 4.0, 5.0};
    std::cout << "   平均值: " << calculateAverage(numbers) << std::endl;
    std::cout << "   最大值: " << findMax(numbers) << std::endl;
    std::cout << "   最小值: " << findMin(numbers) << std::endl;

    // 参数设计示例
    std::cout << "\n2. 参数设计示例:" << std::endl;
    std::string result = concatenate("Hello", "World", ", ");
    std::cout << "   连接: " << result << std::endl;

    auto pos = findPattern("Hello World", "World");
    if (pos) {
        std::cout << "   位置: " << *pos << std::endl;
    }

    // 返回值设计示例
    std::cout << "\n3. 返回值设计示例:" << std::endl;
    auto num = parseInt("123");
    if (num) {
        std::cout << "   解析: " << *num << std::endl;
    }

    auto div = divide(10.0, 3.0);
    if (div) {
        std::cout << "   除法: " << *div << std::endl;
    }

    auto divZero = divide(10.0, 0.0);
    if (!divZero) {
        std::cout << "   除零: 失败" << std::endl;
    }

    // 异常规范示例
    std::cout << "\n4. 异常规范示例:" << std::endl;
    try {
        std::cout << "   阶乘(5): " << factorial(5) << std::endl;
        std::cout << "   阶乘(-1): ";
        factorial(-1);
    } catch (const std::invalid_argument& e) {
        std::cout << "异常: " << e.what() << std::endl;
    }

    // 内联函数示例
    std::cout << "\n5. 内联函数示例:" << std::endl;
    std::cout << "   |−5| = " << absValue(-5) << std::endl;
    std::cout << "   4 是偶数: " << (isEven(4) ? "是" : "否") << std::endl;
    std::cout << "   clamp(15, 0, 10) = " << clamp(15, 0, 10) << std::endl;
}
