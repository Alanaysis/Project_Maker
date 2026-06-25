#pragma once
// unit.hpp - 编译期单位转换系统
//
// 实现类型安全的编译期单位转换系统。
// 使用模板参数表示单位的量纲（长度、质量、时间等），
// 在编译期验证单位运算的正确性。
//
// 核心思想：
//   使用模板参数编码单位的量纲，使得类型不匹配的运算在编译期报错。
//   所有转换因子都是 constexpr，在编译期计算。
//
// 使用示例：
//   constexpr auto distance = 100.0_m;  // 100 米
//   constexpr auto time = 9.58_s;       // 9.58 秒
//   auto speed = distance / time;       // 编译期验证单位正确性
//   constexpr auto km = distance.to_km(); // 单位转换

#include <cstddef>
#include <cmath>

namespace compile_time {
namespace unit {

// 量纲模板参数：length, mass, time, current, temperature, amount, luminosity
template<int L, int M, int T, int I = 0, int Th = 0, int N = 0, int J = 0>
struct dimension {
    static constexpr int length = L;
    static constexpr int mass = M;
    static constexpr int time = T;
    static constexpr int current = I;
    static constexpr int temperature = Th;
    static constexpr int amount = N;
    static constexpr int luminosity = J;
};

// 常用量纲别名
using dimensionless = dimension<0, 0, 0>;
using length_dim = dimension<1, 0, 0>;
using mass_dim = dimension<0, 1, 0>;
using time_dim = dimension<0, 0, 1>;
using velocity_dim = dimension<1, 0, -1>;
using acceleration_dim = dimension<1, 0, -2>;
using force_dim = dimension<1, 1, -2>;
using energy_dim = dimension<2, 1, -2>;
using power_dim = dimension<2, 1, -3>;
using frequency_dim = dimension<0, 0, -1>;

// quantity: 带单位的量
template<typename Dimension, typename Rep = double>
struct quantity {
    Rep value;

    constexpr quantity() : value(0) {}
    constexpr explicit quantity(Rep v) : value(v) {}

    // 访问值
    constexpr Rep count() const { return value; }
    constexpr explicit operator Rep() const { return value; }

    // 算术运算
    constexpr quantity operator+() const { return *this; }
    constexpr quantity operator-() const { return quantity(-value); }

    constexpr quantity& operator+=(const quantity& other) {
        value += other.value;
        return *this;
    }

    constexpr quantity& operator-=(const quantity& other) {
        value -= other.value;
        return *this;
    }

    constexpr quantity& operator*=(Rep factor) {
        value *= factor;
        return *this;
    }

    constexpr quantity& operator/=(Rep factor) {
        value /= factor;
        return *this;
    }

    // 比较运算
    constexpr bool operator==(const quantity& other) const { return value == other.value; }
    constexpr bool operator!=(const quantity& other) const { return value != other.value; }
    constexpr bool operator<(const quantity& other) const { return value < other.value; }
    constexpr bool operator<=(const quantity& other) const { return value <= other.value; }
    constexpr bool operator>(const quantity& other) const { return value > other.value; }
    constexpr bool operator>=(const quantity& other) const { return value >= other.value; }
};

// 同类型运算
template<typename D, typename Rep>
constexpr quantity<D, Rep> operator+(const quantity<D, Rep>& a, const quantity<D, Rep>& b) {
    return quantity<D, Rep>(a.count() + b.count());
}

template<typename D, typename Rep>
constexpr quantity<D, Rep> operator-(const quantity<D, Rep>& a, const quantity<D, Rep>& b) {
    return quantity<D, Rep>(a.count() - b.count());
}

// 标量乘除
template<typename D, typename Rep>
constexpr quantity<D, Rep> operator*(const quantity<D, Rep>& q, Rep factor) {
    return quantity<D, Rep>(q.count() * factor);
}

template<typename D, typename Rep>
constexpr quantity<D, Rep> operator*(Rep factor, const quantity<D, Rep>& q) {
    return quantity<D, Rep>(q.count() * factor);
}

template<typename D, typename Rep>
constexpr quantity<D, Rep> operator/(const quantity<D, Rep>& q, Rep factor) {
    return quantity<D, Rep>(q.count() / factor);
}

// 不同量纲的乘除（生成新量纲）
template<int L1, int M1, int T1, int L2, int M2, int T2, typename Rep>
constexpr quantity<dimension<L1+L2, M1+M2, T1+T2>, Rep>
operator*(const quantity<dimension<L1, M1, T1>, Rep>& a,
          const quantity<dimension<L2, M2, T2>, Rep>& b) {
    return quantity<dimension<L1+L2, M1+M2, T1+T2>, Rep>(a.count() * b.count());
}

template<int L1, int M1, int T1, int L2, int M2, int T2, typename Rep>
constexpr quantity<dimension<L1-L2, M1-M2, T1-T2>, Rep>
operator/(const quantity<dimension<L1, M1, T1>, Rep>& a,
          const quantity<dimension<L2, M2, T2>, Rep>& b) {
    return quantity<dimension<L1-L2, M1-M2, T1-T2>, Rep>(a.count() / b.count());
}

// 长度单位
using meter = quantity<length_dim>;
using kilometer = quantity<length_dim>;
using centimeter = quantity<length_dim>;
using millimeter = quantity<length_dim>;
using mile = quantity<length_dim>;
using yard = quantity<length_dim>;
using foot = quantity<length_dim>;
using inch = quantity<length_dim>;

// 质量单位
using kilogram = quantity<mass_dim>;
using gram = quantity<mass_dim>;
using milligram = quantity<mass_dim>;
using pound = quantity<mass_dim>;
using ounce = quantity<mass_dim>;

// 时间单位
using second = quantity<time_dim>;
using millisecond = quantity<time_dim>;
using minute = quantity<time_dim>;
using hour = quantity<time_dim>;

// 速度单位
using meter_per_second = quantity<velocity_dim>;
using kilometer_per_hour = quantity<velocity_dim>;
using mile_per_hour = quantity<velocity_dim>;

// 频率单位
using hertz = quantity<frequency_dim>;

// 力单位
using newton = quantity<force_dim>;

// 能量单位
using joule = quantity<energy_dim>;
using calorie = quantity<energy_dim>;

// 功率单位
using watt = quantity<power_dim>;

// 用户定义字面量
constexpr meter operator""_m(long double v) { return meter(static_cast<double>(v)); }
constexpr meter operator""_m(unsigned long long v) { return meter(static_cast<double>(v)); }
constexpr kilometer operator""_km(long double v) { return kilometer(static_cast<double>(v) * 1000.0); }
constexpr kilometer operator""_km(unsigned long long v) { return kilometer(static_cast<double>(v) * 1000.0); }
constexpr centimeter operator""_cm(long double v) { return centimeter(static_cast<double>(v) / 100.0); }
constexpr centimeter operator""_cm(unsigned long long v) { return centimeter(static_cast<double>(v) / 100.0); }
constexpr millimeter operator""_mm(long double v) { return millimeter(static_cast<double>(v) / 1000.0); }
constexpr millimeter operator""_mm(unsigned long long v) { return millimeter(static_cast<double>(v) / 1000.0); }

constexpr kilogram operator""_kg(long double v) { return kilogram(static_cast<double>(v)); }
constexpr kilogram operator""_kg(unsigned long long v) { return kilogram(static_cast<double>(v)); }
constexpr gram operator""_g(long double v) { return gram(static_cast<double>(v) / 1000.0); }
constexpr gram operator""_g(unsigned long long v) { return gram(static_cast<double>(v) / 1000.0); }

constexpr second operator""_s(long double v) { return second(static_cast<double>(v)); }
constexpr second operator""_s(unsigned long long v) { return second(static_cast<double>(v)); }
constexpr millisecond operator""_ms(long double v) { return millisecond(static_cast<double>(v) / 1000.0); }
constexpr millisecond operator""_ms(unsigned long long v) { return millisecond(static_cast<double>(v) / 1000.0); }
constexpr minute operator""_min(long double v) { return minute(static_cast<double>(v) * 60.0); }
constexpr minute operator""_min(unsigned long long v) { return minute(static_cast<double>(v) * 60.0); }
constexpr hour operator""_h(long double v) { return hour(static_cast<double>(v) * 3600.0); }
constexpr hour operator""_h(unsigned long long v) { return hour(static_cast<double>(v) * 3600.0); }

constexpr meter_per_second operator""_m_s(long double v) { return meter_per_second(static_cast<double>(v)); }
constexpr meter_per_second operator""_m_s(unsigned long long v) { return meter_per_second(static_cast<double>(v)); }
constexpr kilometer_per_hour operator""_km_h(long double v) { return kilometer_per_hour(static_cast<double>(v) / 3.6); }
constexpr kilometer_per_hour operator""_km_h(unsigned long long v) { return kilometer_per_hour(static_cast<double>(v) / 3.6); }

constexpr hertz operator""_Hz(long double v) { return hertz(static_cast<double>(v)); }
constexpr hertz operator""_Hz(unsigned long long v) { return hertz(static_cast<double>(v)); }

constexpr newton operator""_N(long double v) { return newton(static_cast<double>(v)); }
constexpr newton operator""_N(unsigned long long v) { return newton(static_cast<double>(v)); }

constexpr joule operator""_J(long double v) { return joule(static_cast<double>(v)); }
constexpr joule operator""_J(unsigned long long v) { return joule(static_cast<double>(v)); }

constexpr watt operator""_W(long double v) { return watt(static_cast<double>(v)); }
constexpr watt operator""_W(unsigned long long v) { return watt(static_cast<double>(v)); }

// 单位转换函数
namespace convert {
    // 长度转换
    constexpr double m_to_km(double m) { return m / 1000.0; }
    constexpr double km_to_m(double km) { return km * 1000.0; }
    constexpr double m_to_cm(double m) { return m * 100.0; }
    constexpr double cm_to_m(double cm) { return cm / 100.0; }
    constexpr double m_to_mm(double m) { return m * 1000.0; }
    constexpr double mm_to_m(double mm) { return mm / 1000.0; }
    constexpr double m_to_miles(double m) { return m / 1609.344; }
    constexpr double miles_to_m(double miles) { return miles * 1609.344; }
    constexpr double m_to_feet(double m) { return m / 0.3048; }
    constexpr double feet_to_m(double feet) { return feet * 0.3048; }
    constexpr double m_to_inches(double m) { return m / 0.0254; }
    constexpr double inches_to_m(double inches) { return inches * 0.0254; }

    // 质量转换
    constexpr double kg_to_g(double kg) { return kg * 1000.0; }
    constexpr double g_to_kg(double g) { return g / 1000.0; }
    constexpr double kg_to_mg(double kg) { return kg * 1000000.0; }
    constexpr double mg_to_kg(double mg) { return mg / 1000000.0; }
    constexpr double kg_to_lbs(double kg) { return kg * 2.20462; }
    constexpr double lbs_to_kg(double lbs) { return lbs / 2.20462; }
    constexpr double kg_to_oz(double kg) { return kg * 35.274; }
    constexpr double oz_to_kg(double oz) { return oz / 35.274; }

    // 时间转换
    constexpr double s_to_ms(double s) { return s * 1000.0; }
    constexpr double ms_to_s(double ms) { return ms / 1000.0; }
    constexpr double s_to_min(double s) { return s / 60.0; }
    constexpr double min_to_s(double min) { return min * 60.0; }
    constexpr double s_to_h(double s) { return s / 3600.0; }
    constexpr double h_to_s(double h) { return h * 3600.0; }

    // 速度转换
    constexpr double m_s_to_km_h(double m_s) { return m_s * 3.6; }
    constexpr double km_h_to_m_s(double km_h) { return km_h / 3.6; }
    constexpr double m_s_to_mph(double m_s) { return m_s * 2.23694; }
    constexpr double mph_to_m_s(double mph) { return mph / 2.23694; }

    // 温度转换
    constexpr double celsius_to_fahrenheit(double c) { return c * 9.0 / 5.0 + 32.0; }
    constexpr double fahrenheit_to_celsius(double f) { return (f - 32.0) * 5.0 / 9.0; }
    constexpr double celsius_to_kelvin(double c) { return c + 273.15; }
    constexpr double kelvin_to_celsius(double k) { return k - 273.15; }

    // 能量转换
    constexpr double j_to_cal(double j) { return j / 4.184; }
    constexpr double cal_to_j(double cal) { return cal * 4.184; }
    constexpr double j_to_kj(double j) { return j / 1000.0; }
    constexpr double kj_to_j(double kj) { return kj * 1000.0; }
    constexpr double j_to_kwh(double j) { return j / 3600000.0; }
    constexpr double kwh_to_j(double kwh) { return kwh * 3600000.0; }
} // namespace convert

} // namespace unit
} // namespace compile_time
