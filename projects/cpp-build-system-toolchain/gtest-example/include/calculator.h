#ifndef CALCULATOR_H
#define CALCULATOR_H

#include <stdexcept>
#include <vector>

/**
 * @file calculator.h
 * @brief 计算器库头文件
 *
 * 用于演示 Google Test 的使用。
 */

class Calculator {
public:
    Calculator() : result_(0.0) {}

    // 基本运算
    double add(double a, double b);
    double subtract(double a, double b);
    double multiply(double a, double b);
    double divide(double a, double b);

    // 高级运算
    double power(double base, int exponent);
    double sqrt(double value);
    double factorial(int n);

    // 状态管理
    double get_result() const { return result_; }
    void clear() { result_ = 0.0; }
    void memory_store() { memory_ = result_; }
    double memory_recall() const { return memory_; }
    void memory_clear() { memory_ = 0.0; }

private:
    double result_;
    double memory_ = 0.0;
};

#endif  // CALCULATOR_H
