/**
 * @file basic_example.cpp
 * @brief Armadillo 线性代数库基础示例
 * @details 展示 Armadillo 的基本用法
 *          Armadillo 是一个高级 C++ 线性代数库
 *          类似 MATLAB 的语法
 */

#include <iostream>
#include <armadillo>

/**
 * @brief 基础矩阵操作
 * @details 展示矩阵的创建和基本操作
 */
void basic_matrix() {
    std::cout << "=== 基础矩阵操作 ===" << std::endl;

    // 创建矩阵
    arma::mat A = {{1, 2, 3},
                   {4, 5, 6},
                   {7, 8, 9}};

    std::cout << "Matrix A:" << std::endl;
    std::cout << A << std::endl;

    // 创建向量
    arma::vec v = {1, 2, 3};
    std::cout << "Vector v:" << std::endl;
    std::cout << v << std::endl;

    // 矩阵运算
    arma::mat B = A * 2;
    std::cout << "A * 2:" << std::endl;
    std::cout << B << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 线性代数运算
 * @details 展示线性代数相关的运算
 */
void linear_algebra() {
    std::cout << "=== 线性代数运算 ===" << std::endl;

    arma::mat A = {{2, 1, 1},
                   {1, 3, 2},
                   {1, 0, 0}};

    std::cout << "Matrix A:" << std::endl;
    std::cout << A << std::endl;

    // 转置
    std::cout << "Transpose:" << std::endl;
    std::cout << A.t() << std::endl;

    // 逆矩阵
    std::cout << "Inverse:" << std::endl;
    std::cout << arma::inv(A) << std::endl;

    // 行列式
    std::cout << "Determinant: " << arma::det(A) << std::endl;

    // 特征值和特征向量
    arma::cx_vec eigval;
    arma::cx_mat eigvec;
    arma::eig_gen(eigval, eigvec, A);

    std::cout << "Eigenvalues: " << std::endl;
    std::cout << eigval << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 解线性方程组
 * @details 展示如何求解线性方程组
 */
void solve_linear_system() {
    std::cout << "=== 解线性方程组 ===" << std::endl;

    // 求解 Ax = b
    arma::mat A = {{2, 1, 1},
                   {1, 3, 2},
                   {1, 0, 0}};

    arma::vec b = {4, 5, 6};

    std::cout << "A:" << std::endl;
    std::cout << A << std::endl;

    std::cout << "b:" << std::endl;
    std::cout << b << std::endl;

    // 求解
    arma::vec x = arma::solve(A, b);

    std::cout << "Solution x:" << std::endl;
    std::cout << x << std::endl;

    // 验证
    std::cout << "Verification Ax:" << std::endl;
    std::cout << A * x << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 统计函数
 * @details 展示统计相关的函数
 */
void statistics() {
    std::cout << "=== 统计函数 ===" << std::endl;

    arma::vec data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    std::cout << "Data: " << data.t() << std::endl;

    std::cout << "Mean: " << arma::mean(data) << std::endl;
    std::cout << "Std Dev: " << arma::stddev(data) << std::endl;
    std::cout << "Variance: " << arma::var(data) << std::endl;
    std::cout << "Min: " << arma::min(data) << std::endl;
    std::cout << "Max: " << arma::max(data) << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Armadillo 线性代数库示例 ===" << std::endl;
    std::cout << std::endl;

    basic_matrix();
    linear_algebra();
    solve_linear_system();
    statistics();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}