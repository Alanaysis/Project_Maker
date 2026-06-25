#pragma once
/**
 * @file matrix_operations.hpp
 * @brief 矩阵运算优化
 *
 * 使用模板元编程优化矩阵运算：
 *   - 表达式模板避免临时对象
 *   - 编译期循环展开
 *   - 类型安全的维度检查
 *   - 延迟求值
 */

#include <cstddef>
#include <array>
#include <iostream>
#include <cmath>
#include <initializer_list>
#include <type_traits>

namespace tmp {

// ============================================================================
// 1. 矩阵类型定义
// ============================================================================

/**
 * @brief 静态矩阵
 * @tparam T 元素类型
 * @tparam Rows 行数
 * @tparam Cols 列数
 */
template <typename T, std::size_t Rows, std::size_t Cols>
class Matrix {
    std::array<T, Rows * Cols> data_;

public:
    using value_type = T;
    static constexpr std::size_t rows = Rows;
    static constexpr std::size_t cols = Cols;
    static constexpr std::size_t size = Rows * Cols;

    /// @brief 默认构造（零初始化）
    constexpr Matrix() : data_{} {}

    /// @brief 从初始化列表构造
    constexpr Matrix(std::initializer_list<T> init) : data_{} {
        std::size_t i = 0;
        for (auto it = init.begin(); it != init.end() && i < size; ++it, ++i) {
            data_[i] = *it;
        }
    }

    /// @brief 从表达式构造
    template <typename Expr>
    constexpr Matrix(const Expr& expr) : data_{} {
        for (std::size_t i = 0; i < Rows; ++i) {
            for (std::size_t j = 0; j < Cols; ++j) {
                data_[i * Cols + j] = expr(i, j);
            }
        }
    }

    /// @brief 访问元素
    constexpr T& operator()(std::size_t i, std::size_t j) {
        return data_[i * Cols + j];
    }

    constexpr const T& operator()(std::size_t i, std::size_t j) const {
        return data_[i * Cols + j];
    }

    /// @brief 获取内部数据
    constexpr const T* data() const { return data_.data(); }
    constexpr T* data() { return data_.data(); }

    /// @brief 创建单位矩阵
    static constexpr Matrix identity() {
        Matrix m;
        for (std::size_t i = 0; i < std::min(Rows, Cols); ++i) {
            m(i, i) = T{1};
        }
        return m;
    }

    /// @brief 创建全值矩阵
    static constexpr Matrix fill(T value) {
        Matrix m;
        for (auto& elem : m.data_) {
            elem = value;
        }
        return m;
    }

    /// @brief 转置
    constexpr Matrix<T, Cols, Rows> transpose() const {
        Matrix<T, Cols, Rows> result;
        for (std::size_t i = 0; i < Rows; ++i) {
            for (std::size_t j = 0; j < Cols; ++j) {
                result(j, i) = (*this)(i, j);
            }
        }
        return result;
    }

    /// @brief 获取行
    constexpr std::array<T, Cols> row(std::size_t i) const {
        std::array<T, Cols> result;
        for (std::size_t j = 0; j < Cols; ++j) {
            result[j] = (*this)(i, j);
        }
        return result;
    }

    /// @brief 获取列
    constexpr std::array<T, Rows> col(std::size_t j) const {
        std::array<T, Rows> result;
        for (std::size_t i = 0; i < Rows; ++i) {
            result[i] = (*this)(i, j);
        }
        return result;
    }
};

// ============================================================================
// 2. 表达式模板 - 矩阵运算优化
// ============================================================================

/**
 * @brief 矩阵表达式基类
 */
template <typename Derived, typename T, std::size_t Rows, std::size_t Cols>
class MatrixExpr {
public:
    constexpr T operator()(std::size_t i, std::size_t j) const {
        return static_cast<const Derived&>(*this)(i, j);
    }

    /// @brief 求值到矩阵
    constexpr Matrix<T, Rows, Cols> eval() const {
        return Matrix<T, Rows, Cols>(*this);
    }
};

/**
 * @brief 矩阵加法表达式
 */
template <typename LHS, typename RHS, typename T,
          std::size_t Rows, std::size_t Cols>
class MatrixAdd : public MatrixExpr<MatrixAdd<LHS, RHS, T, Rows, Cols>,
                                     T, Rows, Cols> {
    const LHS& lhs_;
    const RHS& rhs_;

public:
    constexpr MatrixAdd(const LHS& lhs, const RHS& rhs)
        : lhs_(lhs), rhs_(rhs) {}

    constexpr T operator()(std::size_t i, std::size_t j) const {
        return lhs_(i, j) + rhs_(i, j);
    }
};

/**
 * @brief 矩阵减法表达式
 */
template <typename LHS, typename RHS, typename T,
          std::size_t Rows, std::size_t Cols>
class MatrixSub : public MatrixExpr<MatrixSub<LHS, RHS, T, Rows, Cols>,
                                     T, Rows, Cols> {
    const LHS& lhs_;
    const RHS& rhs_;

public:
    constexpr MatrixSub(const LHS& lhs, const RHS& rhs)
        : lhs_(lhs), rhs_(rhs) {}

    constexpr T operator()(std::size_t i, std::size_t j) const {
        return lhs_(i, j) - rhs_(i, j);
    }
};

/**
 * @brief 矩阵乘法表达式
 */
template <typename LHS, typename RHS, typename T,
          std::size_t Rows, std::size_t Cols, std::size_t Inner>
class MatrixMul : public MatrixExpr<MatrixMul<LHS, RHS, T, Rows, Cols, Inner>,
                                     T, Rows, Cols> {
    const LHS& lhs_;
    const RHS& rhs_;

public:
    constexpr MatrixMul(const LHS& lhs, const RHS& rhs)
        : lhs_(lhs), rhs_(rhs) {}

    constexpr T operator()(std::size_t i, std::size_t j) const {
        T sum = T{0};
        for (std::size_t k = 0; k < Inner; ++k) {
            sum += lhs_(i, k) * rhs_(k, j);
        }
        return sum;
    }
};

/**
 * @brief 标量乘法表达式
 */
template <typename MatrixType, typename T,
          std::size_t Rows, std::size_t Cols>
class ScalarMul : public MatrixExpr<ScalarMul<MatrixType, T, Rows, Cols>,
                                     T, Rows, Cols> {
    T scalar_;
    const MatrixType& matrix_;

public:
    constexpr ScalarMul(T scalar, const MatrixType& matrix)
        : scalar_(scalar), matrix_(matrix) {}

    constexpr T operator()(std::size_t i, std::size_t j) const {
        return scalar_ * matrix_(i, j);
    }
};

// ============================================================================
// 3. 矩阵运算符重载
// ============================================================================

/// @brief 矩阵 + 矩阵
template <typename T, std::size_t R, std::size_t C>
constexpr auto operator+(const Matrix<T, R, C>& lhs,
                          const Matrix<T, R, C>& rhs) {
    return MatrixAdd<Matrix<T, R, C>, Matrix<T, R, C>, T, R, C>(lhs, rhs);
}

/// @brief 矩阵 - 矩阵
template <typename T, std::size_t R, std::size_t C>
constexpr auto operator-(const Matrix<T, R, C>& lhs,
                          const Matrix<T, R, C>& rhs) {
    return MatrixSub<Matrix<T, R, C>, Matrix<T, R, C>, T, R, C>(lhs, rhs);
}

/// @brief 矩阵 * 矩阵
template <typename T, std::size_t R1, std::size_t C1, std::size_t C2>
constexpr auto operator*(const Matrix<T, R1, C1>& lhs,
                          const Matrix<T, C1, C2>& rhs) {
    return MatrixMul<Matrix<T, R1, C1>, Matrix<T, C1, C2>,
                     T, R1, C2, C1>(lhs, rhs);
}

/// @brief 标量 * 矩阵
template <typename T, std::size_t R, std::size_t C>
constexpr auto operator*(T scalar, const Matrix<T, R, C>& m) {
    return ScalarMul<Matrix<T, R, C>, T, R, C>(scalar, m);
}

/// @brief 矩阵 * 标量
template <typename T, std::size_t R, std::size_t C>
constexpr auto operator*(const Matrix<T, R, C>& m, T scalar) {
    return ScalarMul<Matrix<T, R, C>, T, R, C>(scalar, m);
}

// ============================================================================
// 4. 矩阵函数
// ============================================================================

/// @brief 行列式（2x2）
template <typename T>
constexpr T determinant(const Matrix<T, 2, 2>& m) {
    return m(0, 0) * m(1, 1) - m(0, 1) * m(1, 0);
}

/// @brief 行列式（3x3）
template <typename T>
constexpr T determinant(const Matrix<T, 3, 3>& m) {
    return m(0, 0) * (m(1, 1) * m(2, 2) - m(1, 2) * m(2, 1)) -
           m(0, 1) * (m(1, 0) * m(2, 2) - m(1, 2) * m(2, 0)) +
           m(0, 2) * (m(1, 0) * m(2, 1) - m(1, 1) * m(2, 0));
}

/// @brief 迹（对角线之和）
template <typename T, std::size_t N>
constexpr T trace(const Matrix<T, N, N>& m) {
    T sum = T{0};
    for (std::size_t i = 0; i < N; ++i) {
        sum += m(i, i);
    }
    return sum;
}

/// @brief Frobenius 范数
template <typename T, std::size_t R, std::size_t C>
constexpr T frobenius_norm(const Matrix<T, R, C>& m) {
    T sum = T{0};
    for (std::size_t i = 0; i < R; ++i) {
        for (std::size_t j = 0; j < C; ++j) {
            sum += m(i, j) * m(i, j);
        }
    }
    return std::sqrt(sum);
}

// ============================================================================
// 5. 向量特化
// ============================================================================

/**
 * @brief 列向量
 */
template <typename T, std::size_t N>
using Vector = Matrix<T, N, 1>;

/**
 * @brief 行向量
 */
template <typename T, std::size_t N>
using RowVector = Matrix<T, 1, N>;

/// @brief 点积
template <typename T, std::size_t N>
constexpr T dot(const Vector<T, N>& a, const Vector<T, N>& b) {
    T sum = T{0};
    for (std::size_t i = 0; i < N; ++i) {
        sum += a(i, 0) * b(i, 0);
    }
    return sum;
}

/// @brief 3D 叉积
template <typename T>
constexpr Vector<T, 3> cross(const Vector<T, 3>& a, const Vector<T, 3>& b) {
    return Vector<T, 3>{
        a(1, 0) * b(2, 0) - a(2, 0) * b(1, 0),
        a(2, 0) * b(0, 0) - a(0, 0) * b(2, 0),
        a(0, 0) * b(1, 0) - a(1, 0) * b(0, 0)
    };
}

// ============================================================================
// 6. 输出
// ============================================================================

template <typename T, std::size_t R, std::size_t C>
std::ostream& operator<<(std::ostream& os, const Matrix<T, R, C>& m) {
    for (std::size_t i = 0; i < R; ++i) {
        os << "[";
        for (std::size_t j = 0; j < C; ++j) {
            if (j > 0) os << ", ";
            os << m(i, j);
        }
        os << "]" << std::endl;
    }
    return os;
}

// ============================================================================
// 7. 编译期断言
// ============================================================================

/// @brief 检查矩阵是否为方阵
template <typename T, std::size_t R, std::size_t C>
inline constexpr bool is_square_matrix = (R == C);

/// @brief 检查是否可以相乘
template <std::size_t C1, std::size_t R2>
inline constexpr bool can_multiply = (C1 == R2);

/// @brief 检查是否可以相加
template <std::size_t R1, std::size_t C1, std::size_t R2, std::size_t C2>
inline constexpr bool can_add = (R1 == R2 && C1 == C2);

}  // namespace tmp
