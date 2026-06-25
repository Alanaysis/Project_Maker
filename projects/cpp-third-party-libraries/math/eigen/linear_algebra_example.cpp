/**
 * @file linear_algebra_example.cpp
 * @brief Eigen 线性代数示例
 * @details 展示 Eigen 的线性代数功能
 */

#include <iostream>
#include <Eigen/Dense>

/**
 * @brief 特征值分解示例
 * @details 展示矩阵的特征值分解
 */
void eigenvalue_decomposition() {
    std::cout << "=== 特征值分解 ===" << std::endl;

    Eigen::Matrix3d A;
    A << 2, 1, 1,
         1, 3, 2,
         1, 0, 0;

    std::cout << "Matrix A:" << std::endl;
    std::cout << A << std::endl;

    // 计算特征值和特征向量
    Eigen::EigenSolver<Eigen::Matrix3d> solver(A);
    Eigen::Vector3d eigenvalues = solver.eigenvalues().real();
    Eigen::Matrix3d eigenvectors = solver.eigenvectors().real();

    std::cout << "Eigenvalues: " << eigenvalues.transpose() << std::endl;
    std::cout << "Eigenvectors:" << std::endl;
    std::cout << eigenvectors << std::endl;

    // 验证：A * v = lambda * v
    Eigen::Vector3d v = eigenvectors.col(0);
    double lambda = eigenvalues(0);
    Eigen::Vector3d Av = A * v;
    Eigen::Vector3d lambda_v = lambda * v;

    std::cout << "Verification (A*v): " << Av.transpose() << std::endl;
    std::cout << "Verification (lambda*v): " << lambda_v.transpose() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 奇异值分解示例
 * @details 展示矩阵的奇异值分解（SVD）
 */
void svd_decomposition() {
    std::cout << "=== 奇异值分解 ===" << std::endl;

    Eigen::MatrixXd A(3, 2);
    A << 1, 2,
         3, 4,
         5, 6;

    std::cout << "Matrix A:" << std::endl;
    std::cout << A << std::endl;

    // 计算 SVD
    Eigen::JacobiSVD<Eigen::MatrixXd> svd(A, Eigen::ComputeThinU | Eigen::ComputeThinV);

    Eigen::MatrixXd U = svd.matrixU();
    Eigen::VectorXd S = svd.singularValues();
    Eigen::MatrixXd V = svd.matrixV();

    std::cout << "U:" << std::endl;
    std::cout << U << std::endl;

    std::cout << "Singular values: " << S.transpose() << std::endl;

    std::cout << "V:" << std::endl;
    std::cout << V << std::endl;

    // 验证：A = U * S * V^T
    Eigen::MatrixXd A_reconstructed = U * S.asDiagonal() * V.transpose();
    std::cout << "Reconstructed A:" << std::endl;
    std::cout << A_reconstructed << std::endl;

    std::cout << std::endl;
}

/**
 * @brief LU 分解示例
 * @details 展示矩阵的 LU 分解
 */
void lu_decomposition() {
    std::cout << "=== LU 分解 ===" << std::endl;

    Eigen::Matrix3d A;
    A << 2, 1, 1,
         1, 3, 2,
         1, 0, 0;

    std::cout << "Matrix A:" << std::endl;
    std::cout << A << std::endl;

    // LU 分解
    Eigen::PartialPivLU<Eigen::Matrix3d> lu(A);

    Eigen::Matrix3d L = lu.matrixLU().triangularView<Eigen::UnitLower>();
    Eigen::Matrix3d U = lu.matrixLU().triangularView<Eigen::Upper>();

    std::cout << "L:" << std::endl;
    std::cout << L << std::endl;

    std::cout << "U:" << std::endl;
    std::cout << U << std::endl;

    // 验证：A = L * U
    Eigen::Matrix3d A_reconstructed = L * U;
    std::cout << "Reconstructed A:" << std::endl;
    std::cout << A_reconstructed << std::endl;

    std::cout << std::endl;
}

/**
 * @brief QR 分解示例
 * @details 展示矩阵的 QR 分解
 */
void qr_decomposition() {
    std::cout << "=== QR 分解 ===" << std::endl;

    Eigen::MatrixXd A(3, 2);
    A << 1, 2,
         3, 4,
         5, 6;

    std::cout << "Matrix A:" << std::endl;
    std::cout << A << std::endl;

    // QR 分解
    Eigen::HouseholderQR<Eigen::MatrixXd> qr(A);

    Eigen::MatrixXd Q = qr.householderQ();
    Eigen::MatrixXd R = qr.matrixQR().triangularView<Eigen::Upper>();

    std::cout << "Q:" << std::endl;
    std::cout << Q << std::endl;

    std::cout << "R:" << std::endl;
    std::cout << R << std::endl;

    // 验证：A = Q * R
    Eigen::MatrixXd A_reconstructed = Q * R;
    std::cout << "Reconstructed A:" << std::endl;
    std::cout << A_reconstructed << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 最小二乘法示例
 * @details 展示如何使用 Eigen 求解最小二乘问题
 */
void least_squares() {
    std::cout << "=== 最小二乘法 ===" << std::endl;

    // 超定方程组 Ax = b
    Eigen::MatrixXd A(4, 2);
    A << 1, 1,
         2, 1,
         3, 1,
         4, 1;

    Eigen::VectorXd b(4);
    b << 2, 3, 5, 6;

    std::cout << "A:" << std::endl;
    std::cout << A << std::endl;

    std::cout << "b: " << b.transpose() << std::endl;

    // 使用 QR 分解求解最小二乘
    Eigen::VectorXd x = A.colPivHouseholderQr().solve(b);

    std::cout << "Solution x: " << x.transpose() << std::endl;

    // 计算残差
    Eigen::VectorXd residual = A * x - b;
    std::cout << "Residual: " << residual.transpose() << std::endl;
    std::cout << "Residual norm: " << residual.norm() << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Eigen 线性代数示例 ===" << std::endl;
    std::cout << std::endl;

    eigenvalue_decomposition();
    svd_decomposition();
    lu_decomposition();
    qr_decomposition();
    least_squares();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}