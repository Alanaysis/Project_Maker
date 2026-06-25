#pragma once
/**
 * @file units_system.hpp
 * @brief 单位系统 (Units Library)
 *
 * 使用模板元编程实现类型安全的物理单位系统。
 * 在编译期检查单位一致性，避免单位错误。
 *
 * 核心特性：
 *   - 编译期单位检查
 *   - 自动单位转换
 *   - 类型安全的算术运算
 *   - 零运行时开销
 */

#include <ratio>
#include <iostream>
#include <string>
#include <cmath>
#include <type_traits>

namespace tmp {
namespace units {

// ============================================================================
// 1. 基本维度定义
// ============================================================================

/**
 * @brief 维度标签
 * 使用整数指数表示物理量的维度
 */
template <int M, int L, int T, int I, int Theta, int N, int J>
struct Dimension {
    static constexpr int mass = M;           // 质量 (kg)
    static constexpr int length = L;         // 长度 (m)
    static constexpr int time = T;           // 时间 (s)
    static constexpr int current = I;        // 电流 (A)
    static constexpr int temperature = Theta; // 温度 (K)
    static constexpr int amount = N;         // 物质的量 (mol)
    static constexpr int luminous = J;       // 发光强度 (cd)
};

// 预定义维度
using Dimensionless = Dimension<0, 0, 0, 0, 0, 0, 0>;
using Mass = Dimension<1, 0, 0, 0, 0, 0, 0>;
using Length = Dimension<0, 1, 0, 0, 0, 0, 0>;
using Time = Dimension<0, 0, 1, 0, 0, 0, 0>;
using Current = Dimension<0, 0, 0, 1, 0, 0, 0>;
using Temperature = Dimension<0, 0, 0, 0, 1, 0, 0>;

// 导出维度
using Velocity = Dimension<0, 1, -1, 0, 0, 0, 0>;        // m/s
using Acceleration = Dimension<0, 1, -2, 0, 0, 0, 0>;    // m/s^2
using Force = Dimension<1, 1, -2, 0, 0, 0, 0>;           // N (kg*m/s^2)
using Energy = Dimension<1, 2, -2, 0, 0, 0, 0>;          // J (kg*m^2/s^2)
using Power = Dimension<1, 2, -3, 0, 0, 0, 0>;           // W (kg*m^2/s^3)
using Pressure = Dimension<1, -1, -2, 0, 0, 0, 0>;       // Pa (kg/(m*s^2))
using Frequency = Dimension<0, 0, -1, 0, 0, 0, 0>;       // Hz (1/s)
using Area = Dimension<0, 2, 0, 0, 0, 0, 0>;             // m^2
using Volume = Dimension<0, 3, 0, 0, 0, 0, 0>;           // m^3

// ============================================================================
// 2. 维度运算
// ============================================================================

/// @brief 维度乘法
template <typename D1, typename D2>
struct dimension_multiply {
    using type = Dimension<
        D1::mass + D2::mass,
        D1::length + D2::length,
        D1::time + D2::time,
        D1::current + D2::current,
        D1::temperature + D2::temperature,
        D1::amount + D2::amount,
        D1::luminous + D2::luminous>;
};

template <typename D1, typename D2>
using dimension_multiply_t = typename dimension_multiply<D1, D2>::type;

/// @brief 维度除法
template <typename D1, typename D2>
struct dimension_divide {
    using type = Dimension<
        D1::mass - D2::mass,
        D1::length - D2::length,
        D1::time - D2::time,
        D1::current - D2::current,
        D1::temperature - D2::temperature,
        D1::amount - D2::amount,
        D1::luminous - D2::luminous>;
};

template <typename D1, typename D2>
using dimension_divide_t = typename dimension_divide<D1, D2>::type;

/// @brief 维度幂
template <typename D, int N>
struct dimension_power {
    using type = Dimension<
        D::mass * N,
        D::length * N,
        D::time * N,
        D::current * N,
        D::temperature * N,
        D::amount * N,
        D::luminous * N>;
};

template <typename D, int N>
using dimension_power_t = typename dimension_power<D, N>::type;

// ============================================================================
// 3. 单位系统
// ============================================================================

/**
 * @brief 单位定义
 * @tparam Dim 维度
 * @tparam Scale 比例因子 (std::ratio)
 */
template <typename Dim, typename Scale = std::ratio<1>>
struct Unit {
    using dimension = Dim;
    using scale = Scale;
};

// 预定义单位 (SI)
using Meter = Unit<Length>;
using Second = Unit<Time>;
using Kilogram = Unit<Mass>;
using Ampere = Unit<Current>;
using Kelvin = Unit<Temperature>;
using Newton = Unit<Force>;
using Joule = Unit<Energy>;
using Watt = Unit<Power>;
using Pascal = Unit<Pressure>;
using Hertz = Unit<Frequency>;
using VelocityUnit = Unit<Velocity>;
using AccelerationUnit = Unit<Acceleration>;

// 非 SI 单位
using Kilometer = Unit<Length, std::ratio<1000>>;
using Centimeter = Unit<Length, std::ratio<1, 100>>;
using Millimeter = Unit<Length, std::ratio<1, 1000>>;
using Gram = Unit<Mass, std::ratio<1, 1000>>;
using Hour = Unit<Time, std::ratio<3600>>;
using Minute = Unit<Time, std::ratio<60>>;
using Degree = Unit<Dimensionless, std::ratio<17453292519943, 100000000000000>>; // pi/180

// ============================================================================
// 4. 量 (Quantity) - 带单位的数值
// ============================================================================

/**
 * @brief 量 - 带单位的数值
 * @tparam Unit 单位类型
 * @tparam T 数值类型
 */
template <typename UnitType, typename T = double>
class Quantity {
    T value_;

public:
    using unit_type = UnitType;
    using value_type = T;
    using dimension = typename UnitType::dimension;

    /// @brief 构造函数
    explicit constexpr Quantity(T value = T{0}) : value_(value) {}

    /// @brief 获取数值
    constexpr T value() const { return value_; }

    /// @brief 同维度单位转换
    template <typename OtherUnit>
    constexpr Quantity(const Quantity<OtherUnit, T>& other)
        : value_(other.value() *
                 static_cast<double>(OtherUnit::scale::num) /
                 static_cast<double>(OtherUnit::scale::den) *
                 static_cast<double>(UnitType::scale::den) /
                 static_cast<double>(UnitType::scale::num)) {
        static_assert(
            std::is_same_v<typename OtherUnit::dimension, dimension>,
            "Cannot convert between different dimensions");
    }

    /// @brief 加法（相同单位）
    constexpr Quantity operator+(const Quantity& other) const {
        return Quantity(value_ + other.value_);
    }

    /// @brief 减法（相同单位）
    constexpr Quantity operator-(const Quantity& other) const {
        return Quantity(value_ - other.value_);
    }

    /// @brief 乘以标量
    constexpr Quantity operator*(T scalar) const {
        return Quantity(value_ * scalar);
    }

    /// @brief 除以标量
    constexpr Quantity operator/(T scalar) const {
        return Quantity(value_ / scalar);
    }

    /// @brief 乘以另一个量（维度相加）
    template <typename U2>
    constexpr auto operator*(const Quantity<U2, T>& other) const {
        using result_unit = Unit<dimension_multiply_t<dimension, typename U2::dimension>,
                                  std::ratio_multiply<typename UnitType::scale,
                                                       typename U2::scale>>;
        return Quantity<result_unit, T>(value_ * other.value());
    }

    /// @brief 除以另一个量（维度相减）
    template <typename U2>
    constexpr auto operator/(const Quantity<U2, T>& other) const {
        using result_unit = Unit<dimension_divide_t<dimension, typename U2::dimension>,
                                  std::ratio_divide<typename UnitType::scale,
                                                     typename U2::scale>>;
        return Quantity<result_unit, T>(value_ / other.value());
    }

    /// @brief 比较运算符
    constexpr bool operator==(const Quantity& other) const {
        return value_ == other.value_;
    }

    constexpr bool operator!=(const Quantity& other) const {
        return value_ != other.value_;
    }

    constexpr bool operator<(const Quantity& other) const {
        return value_ < other.value_;
    }

    constexpr bool operator>(const Quantity& other) const {
        return value_ > other.value_;
    }

    /// @brief 输出
    friend std::ostream& operator<<(std::ostream& os, const Quantity& q) {
        os << q.value_;
        // 输出单位符号（简化版本）
        if constexpr (dimension::length == 1 && dimension::mass == 0) {
            os << " m";
        } else if constexpr (dimension::time == 1 && dimension::length == 0) {
            os << " s";
        } else if constexpr (dimension::mass == 1 && dimension::length == 0) {
            os << " kg";
        } else if constexpr (dimension::length == 1 && dimension::time == -1) {
            os << " m/s";
        } else if constexpr (dimension::mass == 1 && dimension::length == 1 &&
                             dimension::time == -2) {
            os << " N";
        }
        return os;
    }
};

// ============================================================================
// 5. 用户定义字面量
// ============================================================================

constexpr Quantity<Meter, double> operator"" _m(long double v) {
    return Quantity<Meter, double>(static_cast<double>(v));
}

constexpr Quantity<Kilometer, double> operator"" _km(long double v) {
    return Quantity<Kilometer, double>(static_cast<double>(v));
}

constexpr Quantity<Second, double> operator"" _s(long double v) {
    return Quantity<Second, double>(static_cast<double>(v));
}

constexpr Quantity<Kilogram, double> operator"" _kg(long double v) {
    return Quantity<Kilogram, double>(static_cast<double>(v));
}

constexpr Quantity<Newton, double> operator"" _N(long double v) {
    return Quantity<Newton, double>(static_cast<double>(v));
}

constexpr Quantity<Joule, double> operator"" _J(long double v) {
    return Quantity<Joule, double>(static_cast<double>(v));
}

// ============================================================================
// 6. 数学函数
// ============================================================================

/// @brief 绝对值
template <typename U, typename T>
constexpr Quantity<U, T> abs(const Quantity<U, T>& q) {
    return Quantity<U, T>(std::abs(q.value()));
}

/// @brief 平方
template <typename U, typename T>
constexpr auto square(const Quantity<U, T>& q) {
    return q * q;
}

/// @brief 立方
template <typename U, typename T>
constexpr auto cube(const Quantity<U, T>& q) {
    return q * q * q;
}

/// @brief 平方根（需要维度可被2整除）
template <typename U, typename T>
constexpr auto sqrt(const Quantity<U, T>& q) {
    using result_dim = Dimension<
        U::dimension::mass / 2,
        U::dimension::length / 2,
        U::dimension::time / 2,
        U::dimension::current / 2,
        U::dimension::temperature / 2,
        U::dimension::amount / 2,
        U::dimension::luminous / 2>;
    using result_unit = Unit<result_dim>;
    return Quantity<result_unit, T>(std::sqrt(q.value()));
}

}  // namespace units
}  // namespace tmp
