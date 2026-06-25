#include "calculator.h"
#include <cmath>
#include <stdexcept>

/**
 * @file calculator.cpp
 * @brief 计算器库实现
 */

double Calculator::add(double a, double b) {
    result_ = a + b;
    return result_;
}

double Calculator::subtract(double a, double b) {
    result_ = a - b;
    return result_;
}

double Calculator::multiply(double a, double b) {
    result_ = a * b;
    return result_;
}

double Calculator::divide(double a, double b) {
    if (b == 0.0) {
        throw std::invalid_argument("Division by zero");
    }
    result_ = a / b;
    return result_;
}

double Calculator::power(double base, int exponent) {
    result_ = std::pow(base, exponent);
    return result_;
}

double Calculator::sqrt(double value) {
    if (value < 0) {
        throw std::invalid_argument("Square root of negative number");
    }
    result_ = std::sqrt(value);
    return result_;
}

double Calculator::factorial(int n) {
    if (n < 0) {
        throw std::invalid_argument("Factorial of negative number");
    }
    if (n <= 1) {
        result_ = 1.0;
        return result_;
    }
    result_ = 1.0;
    for (int i = 2; i <= n; ++i) {
        result_ *= i;
    }
    return result_;
}
