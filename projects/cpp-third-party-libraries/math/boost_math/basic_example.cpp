/**
 * @file basic_example.cpp
 * @brief Boost.Math 数学库基础示例
 * @details 展示 Boost.Math 的基本用法
 *          提供特殊函数、统计分布、数值积分等
 */

#include <iostream>
#include <cmath>
#include <boost/math/constants/constants.hpp>
#include <boost/math/special_functions.hpp>
#include <boost/math/distributions/normal.hpp>

/**
 * @brief 数学常量示例
 * @details 展示 Boost.Math 的数学常量
 */
void math_constants() {
    std::cout << "=== 数学常量 ===" << std::endl;

    // 使用 Boost.Math 常量
    std::cout << "Pi: " << boost::math::constants::pi<double>() << std::endl;
    std::cout << "E: " << boost::math::constants::e<double>() << std::endl;
    std::cout << "Sqrt(2): " << boost::math::constants::root_two<double>() << std::endl;
    std::cout << "Ln(2): " << boost::math::constants::ln_two<double>() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 特殊函数示例
 * @details 展示 Boost.Math 的特殊函数
 */
void special_functions() {
    std::cout << "=== 特殊函数 ===" << std::endl;

    // Gamma 函数
    std::cout << "Gamma(5) = " << boost::math::tgamma(5.0) << std::endl;
    std::cout << "Gamma(0.5) = " << boost::math::tgamma(0.5) << std::endl;

    // Beta 函数
    std::cout << "Beta(2, 3) = " << boost::math::beta(2.0, 3.0) << std::endl;

    // 误差函数
    std::cout << "Erf(1) = " << boost::math::erf(1.0) << std::endl;

    // Bessel 函数
    std::cout << "Bessel J0(1) = " << boost::math::cyl_bessel_j(0, 1.0) << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 统计分布示例
 * @details 展示 Boost.Math 的统计分布
 */
void statistical_distributions() {
    std::cout << "=== 统计分布 ===" << std::endl;

    // 正态分布
    boost::math::normal_distribution<> norm(0.0, 1.0);  // 均值=0，标准差=1

    std::cout << "Normal Distribution (mean=0, std=1):" << std::endl;
    std::cout << "  PDF at 0: " << boost::math::pdf(norm, 0.0) << std::endl;
    std::cout << "  CDF at 0: " << boost::math::cdf(norm, 0.0) << std::endl;
    std::cout << "  Quantile at 0.5: " << boost::math::quantile(norm, 0.5) << std::endl;

    // 计算置信区间
    double alpha = 0.05;
    double lower = boost::math::quantile(norm, alpha / 2);
    double upper = boost::math::quantile(norm, 1 - alpha / 2);
    std::cout << "  95% Confidence Interval: [" << lower << ", " << upper << "]" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 数值计算示例
 * @details 展示数值计算功能
 */
void numerical_computation() {
    std::cout << "=== 数值计算 ===" << std::endl;

    // 阶乘
    std::cout << "5! = " << boost::math::factorial<double>(5) << std::endl;

    // 二项式系数
    std::cout << "C(5,2) = " << boost::math::binomial_coefficient<double>(5, 2) << std::endl;

    // 幂运算
    std::cout << "2^10 = " << boost::math::pow<10>(2.0) << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 Boost.Math 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：计算正态分布的概率
    boost::math::normal_distribution<> exam_scores(75.0, 10.0);  // 均值=75，标准差=10

    double score = 85.0;
    double probability = 1 - boost::math::cdf(exam_scores, score);
    std::cout << "Probability of scoring above " << score << ": "
              << probability * 100 << "%" << std::endl;

    // 场景：计算置信区间
    double mean = 100.0;
    double std_dev = 15.0;
    double n = 100.0;  // 样本量
    double se = std_dev / std::sqrt(n);  // 标准误差

    boost::math::normal_distribution<> sampling_dist(mean, se);
    double ci_lower = boost::math::quantile(sampling_dist, 0.025);
    double ci_upper = boost::math::quantile(sampling_dist, 0.975);

    std::cout << "95% Confidence Interval for mean: ["
              << ci_lower << ", " << ci_upper << "]" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Boost.Math 数学库示例 ===" << std::endl;
    std::cout << std::endl;

    math_constants();
    special_functions();
    statistical_distributions();
    numerical_computation();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}