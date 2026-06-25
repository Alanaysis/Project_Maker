/**
 * @file matrix_example.cpp
 * @brief Eigen 矩阵运算示例
 * @details 展示 Eigen 库的矩阵操作
 *          Eigen 是一个高性能的 C++ 线性代数库
 *          广泛用于科学计算、机器学习、图形学等领域
 */

#include <iostream>
#include <Eigen/Dense>

/**
 * @brief 基础矩阵操作
 * @details 展示矩阵的创建和基本操作
 */
void basic_matrix() {
    std::cout << "=== 基础矩阵操作 ===" << std::endl;

    // 创建矩阵
    Eigen::Matrix3d m1;  // 3x3 双精度矩阵
    m1 << 1, 2, 3,
          4, 5, 6,
          7, 8, 9;

    std::cout << "Matrix m1:" << std::endl;
    std::cout << m1 << std::endl;

    // 创建动态大小矩阵
    Eigen::MatrixXd m2(2, 3);
    m2 << 1, 2, 3,
          4, 5, 6;

    std::cout << "\nMatrix m2 (2x3):" << std::endl;
    std::cout << m2 << std::endl;

    // 矩阵运算
    Eigen::Matrix3d m3 = m1 * 2;
    std::cout << "\nm1 * 2:" << std::endl;
    std::cout << m3 << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 向量操作示例
 * @details 展示向量的创建和操作
 */
void vector_operations() {
    std::cout << "=== 向量操作 ===" << std::endl;

    // 创建向量
    Eigen::Vector3d v1(1, 2, 3);
    Eigen::Vector3d v2(4, 5, 6);

    std::cout << "v1: " << v1.transpose() << std::endl;
    std::cout << "v2: " << v2.transpose() << std::endl;

    // 向量运算
    std::cout << "v1 + v2: " << (v1 + v2).transpose() << std::endl;
    std::cout << "v1 - v2: " << (v1 - v2).transpose() << std::endl;
    std::cout << "v1 * 2: " << (v1 * 2).transpose() << std::endl;

    // 点积和叉积
    double dot = v1.dot(v2);
    Eigen::Vector3d cross = v1.cross(v2);

    std::cout << "Dot product: " << dot << std::endl;
    std::cout << "Cross product: " << cross.transpose() << std::endl;

    // 向量长度
    std::cout << "v1 norm: " << v1.norm() << std::endl;
    std::cout << "v1 normalized: " << v1.normalized().transpose() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 矩阵运算示例
 * @details 展示矩阵的高级运算
 */
void matrix_operations() {
    std::cout << "=== 矩阵运算 ===" << std::endl;

    Eigen::Matrix3d A;
    A << 1, 2, 3,
         4, 5, 6,
         7, 8, 10;

    std::cout << "Matrix A:" << std::endl;
    std::cout << A << std::endl;

    // 转置
    std::cout << "Transpose:" << std::endl;
    std::cout << A.transpose() << std::endl;

    // 逆矩阵
    std::cout << "Inverse:" << std::endl;
    std::cout << A.inverse() << std::endl;

    // 行列式
    std::cout << "Determinant: " << A.determinant() << std::endl;

    // 特征值和特征向量
    Eigen::EigenSolver<Eigen::Matrix3d> solver(A);
    std::cout << "Eigenvalues: " << solver.eigenvalues().transpose() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 解线性方程组示例
 * @details 展示如何求解线性方程组
 */
void solve_linear_system() {
    std::cout << "=== 解线性方程组 ===" << std::endl;

    // 求解 Ax = b
    Eigen::Matrix3d A;
    A << 2, 1, 1,
         1, 3, 2,
         1, 0, 0;

    Eigen::Vector3d b(4, 5, 6);

    std::cout << "A:" << std::endl;
    std::cout << A << std::endl;

    std::cout << "b: " << b.transpose() << std::endl;

    // 求解
    Eigen::Vector3d x = A.colPivHouseholderQr().solve(b);

    std::cout << "Solution x: " << x.transpose() << std::endl;

    // 验证
    std::cout << "Verification Ax: " << (A * x).transpose() << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 Eigen 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：3D 变换
    // 旋转矩阵（绕 Z 轴旋转 45 度）
    double angle = M_PI / 4;  // 45 度
    Eigen::Matrix3d rotation;
    rotation << cos(angle), -sin(angle), 0,
                sin(angle),  cos(angle), 0,
                0,           0,          1;

    std::cout << "Rotation matrix (45 degrees):" << std::endl;
    std::cout << rotation << std::endl;

    // 变换一个点
    Eigen::Vector3d point(1, 0, 0);
    Eigen::Vector3d rotated = rotation * point;

    std::cout << "Original point: " << point.transpose() << std::endl;
    std::cout << "Rotated point: " << rotated.transpose() << std::endl;

    // 验证长度不变
    std::cout << "Original norm: " << point.norm() << std::endl;
    std::cout << "Rotated norm: " << rotated.norm() << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Eigen 矩阵运算示例 ===" << std::endl;
    std::cout << std::endl;

    basic_matrix();
    vector_operations();
    matrix_operations();
    solve_linear_system();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}