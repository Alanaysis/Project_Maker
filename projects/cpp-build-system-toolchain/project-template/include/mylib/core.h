#ifndef MYLIB_CORE_H
#define MYLIB_CORE_H

#include <string>
#include <memory>
#include <vector>

/**
 * @file core.h
 * @brief MyLib 核心模块
 *
 * 项目模板的核心库，展示现代 CMake 的库组织方式。
 */

namespace mylib {

/**
 * @brief 版本信息
 */
struct Version {
    static constexpr int major = 1;
    static constexpr int minor = 0;
    static constexpr int patch = 0;
    static std::string string() {
        return std::to_string(major) + "." + std::to_string(minor) + "." + std::to_string(patch);
    }
};

/**
 * @brief 字符串工具类
 */
class StringUtils {
public:
    static std::string to_upper(const std::string& input);
    static std::string to_lower(const std::string& input);
    static std::string trim(const std::string& input);
    static std::vector<std::string> split(const std::string& input, char delimiter);
    static std::string join(const std::vector<std::string>& parts, const std::string& separator);
};

/**
 * @brief 数学工具类
 */
class MathUtils {
public:
    static int add(int a, int b);
    static int subtract(int a, int b);
    static int multiply(int a, int b);
    static double divide(double a, double b);
    static double power(double base, int exponent);
    static bool is_prime(int n);
};

}  // namespace mylib

#endif  // MYLIB_CORE_H
