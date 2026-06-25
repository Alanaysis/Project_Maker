/**
 * @file matrix_operations.cpp
 * @brief 矩阵运算优化示例
 */

#include <iostream>
#include "../include/applications/matrix_operations.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== Matrix Operations ===" << std::endl;
    std::cout << std::endl;

    // 1. 基本矩阵
    std::cout << "--- 1. Basic Matrix ---" << std::endl;

    Matrix<double, 3, 3> m1 = {1, 2, 3, 4, 5, 6, 7, 8, 9};
    Matrix<double, 3, 3> m2 = {9, 8, 7, 6, 5, 4, 3, 2, 1};

    std::cout << "Matrix m1:" << std::endl << m1;
    std::cout << "Matrix m2:" << std::endl << m2;
    std::cout << std::endl;

    // 2. 加法（表达式模板，无临时对象）
    std::cout << "--- 2. Addition (Expression Templates) ---" << std::endl;
    auto sum = (m1 + m2).eval();
    std::cout << "m1 + m2:" << std::endl << sum;
    std::cout << std::endl;

    // 3. 减法
    std::cout << "--- 3. Subtraction ---" << std::endl;
    auto diff = (m1 - m2).eval();
    std::cout << "m1 - m2:" << std::endl << diff;
    std::cout << std::endl;

    // 4. 乘法
    std::cout << "--- 4. Multiplication ---" << std::endl;
    auto prod = (m1 * m2).eval();
    std::cout << "m1 * m2:" << std::endl << prod;
    std::cout << std::endl;

    // 5. 标量乘法
    std::cout << "--- 5. Scalar Multiplication ---" << std::endl;
    auto scaled = (2.0 * m1).eval();
    std::cout << "2 * m1:" << std::endl << scaled;
    std::cout << std::endl;

    // 6. 转置
    std::cout << "--- 6. Transpose ---" << std::endl;
    auto transposed = m1.transpose();
    std::cout << "m1^T:" << std::endl << transposed;
    std::cout << std::endl;

    // 7. 行列式
    std::cout << "--- 7. Determinant ---" << std::endl;
    Matrix<double, 2, 2> m2x2 = {1, 2, 3, 4};
    std::cout << "det([1,2;3,4]) = " << determinant(m2x2) << std::endl;

    Matrix<double, 3, 3> m3x3 = {1, 2, 3, 0, 1, 4, 5, 6, 0};
    std::cout << "det(m3x3) = " << determinant(m3x3) << std::endl;
    std::cout << std::endl;

    // 8. 迹
    std::cout << "--- 8. Trace ---" << std::endl;
    std::cout << "trace(m1) = " << trace(m1) << std::endl;
    std::cout << std::endl;

    // 9. 单位矩阵
    std::cout << "--- 9. Identity Matrix ---" << std::endl;
    auto I = Matrix<double, 3, 3>::identity();
    std::cout << "I:" << std::endl << I;
    std::cout << std::endl;

    // 10. 向量运算
    std::cout << "--- 10. Vector Operations ---" << std::endl;
    Vector<double, 3> v1 = {1, 0, 0};
    Vector<double, 3> v2 = {0, 1, 0};

    auto v3 = cross(v1, v2);
    std::cout << "cross([1,0,0], [0,1,0]) = ";
    std::cout << "[" << v3(0,0) << ", " << v3(1,0) << ", " << v3(2,0) << "]" << std::endl;

    std::cout << "dot(v1, v2) = " << dot(v1, v2) << std::endl;
    std::cout << std::endl;

    // 11. 复合表达式
    std::cout << "--- 11. Compound Expression ---" << std::endl;
    // 先计算 2*m2，再与 m1 相加
    auto scaled_m2 = (2.0 * m2).eval();
    auto result = (m1 + scaled_m2).eval();
    std::cout << "m1 + 2*m2:" << std::endl << result;

    return 0;
}
