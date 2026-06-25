#ifndef MATH_UTILS_H
#define MATH_UTILS_H

/**
 * @file math_utils.h
 * @brief 数学工具库头文件
 *
 * 提供基础的数学运算函数，用于演示 CMake 静态库的创建和使用。
 */

namespace math {

/**
 * @brief 加法运算
 * @param a 第一个操作数
 * @param b 第二个操作数
 * @return 两数之和
 */
int add(int a, int b);

/**
 * @brief 减法运算
 * @param a 第一个操作数
 * @param b 第二个操作数
 * @return 两数之差
 */
int subtract(int a, int b);

/**
 * @brief 乘法运算
 * @param a 第一个操作数
 * @param b 第二个操作数
 * @return 两数之积
 */
int multiply(int a, int b);

/**
 * @brief 除法运算
 * @param a 被除数
 * @param b 除数
 * @return 商
 * @throws std::invalid_argument 当除数为零时抛出异常
 */
double divide(double a, double b);

/**
 * @brief 计算阶乘
 * @param n 非负整数
 * @return n 的阶乘
 */
unsigned long long factorial(int n);

/**
 * @brief 判断是否为素数
 * @param n 待判断的整数
 * @return 如果是素数返回 true，否则返回 false
 */
bool is_prime(int n);

}  // namespace math

#endif  // MATH_UTILS_H
