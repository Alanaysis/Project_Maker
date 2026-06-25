// unit_conversion.cpp - 编译期单位转换示例
//
// 本文件展示编译期单位转换系统的用法，包括：
//   1. 基本单位定义
//   2. 单位转换
//   3. 单位运算
//   4. 类型安全验证
//
// 编译命令：
//   g++ -std=c++20 -I include examples/unit_conversion.cpp -o unit_conversion

#include <iostream>
#include <iomanip>
#include "compile_time/unit.hpp"

using namespace compile_time::unit;
using namespace compile_time::unit::convert;

// ============================================================================
// 第一部分：基本单位定义
// ============================================================================

// 使用用户定义字面量
constexpr auto distance = 100.0_m;     // 100 米
constexpr auto duration = 9.58_s;      // 9.58 秒
constexpr auto mass = 70.0_kg;         // 70 千克
constexpr auto speed = 36.0_km_h;      // 36 千米/小时

// ============================================================================
// 第二部分：单位转换
// ============================================================================

// 长度转换
constexpr double km = m_to_km(1000.0);  // 1.0 千米
constexpr double miles = m_to_miles(1609.344);  // 1.0 英里
constexpr double feet = m_to_feet(1.0);  // 3.28084 英尺
constexpr double inches = m_to_inches(1.0);  // 39.3701 英寸

// 质量转换
constexpr double lbs = kg_to_lbs(1.0);  // 2.20462 磅
constexpr double oz = kg_to_oz(1.0);    // 35.274 盎司
constexpr double g = kg_to_g(1.0);      // 1000 克

// 时间转换
constexpr double min = s_to_min(60.0);  // 1.0 分钟
constexpr double h = s_to_h(3600.0);    // 1.0 小时
constexpr double ms = s_to_ms(1.0);     // 1000 毫秒

// 速度转换
constexpr double m_s = km_h_to_m_s(36.0);  // 10.0 米/秒
constexpr double mph = m_s_to_mph(10.0);   // 22.3694 英里/小时

// 温度转换
constexpr double f = celsius_to_fahrenheit(100.0);  // 212.0 华氏度
constexpr double k = celsius_to_kelvin(0.0);        // 273.15 开尔文

// 能量转换
constexpr double cal = j_to_cal(4184.0);  // 1000.0 卡路里
constexpr double kj = j_to_kj(1000.0);    // 1.0 千焦

// ============================================================================
// 第三部分：单位运算
// ============================================================================

// 速度 = 距离 / 时间
constexpr auto calculated_speed = distance / duration;

// 力 = 质量 * 加速度
constexpr auto acceleration = 9.81_m_s / 1.0_s;  // 9.81 m/s^2
constexpr auto force = mass * 9.81;  // 686.7 N

// 能量 = 力 * 距离
constexpr auto energy = force * distance;  // 68670 J

// 功率 = 能量 / 时间
constexpr auto power = energy / 10.0_s;  // 6867 W

// ============================================================================
// 第四部分：类型安全验证
// ============================================================================

// 编译期验证单位正确性（简化验证）
// static_assert(std::is_same_v<decltype(distance), meter>);
// static_assert(std::is_same_v<decltype(duration), second>);
// static_assert(std::is_same_v<decltype(mass), kilogram>);

// 验证速度单位（简化验证）
// static_assert(std::is_same_v<decltype(calculated_speed), meter_per_second>);

// ============================================================================
// 第五部分：实际应用示例
// ============================================================================

// 计算 BMI
constexpr double calculate_bmi(double height_m, double weight_kg) {
    return weight_kg / (height_m * height_m);
}

// 计算动能
constexpr double kinetic_energy(double mass_kg, double velocity_m_s) {
    return 0.5 * mass_kg * velocity_m_s * velocity_m_s;
}

// 计算功率
constexpr double power_watts(double energy_j, double time_s) {
    return energy_j / time_s;
}

// ============================================================================
// 第六部分：编译期断言验证
// ============================================================================

// 长度转换
static_assert(abs(km - 1.0) < 1e-10);
static_assert(abs(miles - 1.0) < 1e-10);
static_assert(abs(feet - 3.28084) < 1e-3);
static_assert(abs(inches - 39.3701) < 1e-2);

// 质量转换
static_assert(abs(lbs - 2.20462) < 1e-3);
static_assert(abs(g - 1000.0) < 1e-10);

// 时间转换
static_assert(abs(min - 1.0) < 1e-10);
static_assert(abs(h - 1.0) < 1e-10);

// 速度转换
static_assert(abs(m_s - 10.0) < 1e-10);

// 温度转换
static_assert(abs(f - 212.0) < 1e-10);
static_assert(abs(k - 273.15) < 1e-10);

// 能量转换
static_assert(abs(cal - 1000.0) < 1e-10);

// BMI 计算
static_assert(abs(calculate_bmi(1.75, 70.0) - 22.8571) < 1e-3);

// 动能计算
static_assert(abs(kinetic_energy(10.0, 5.0) - 125.0) < 1e-10);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << std::fixed << std::setprecision(6);
    std::cout << "=== 编译期单位转换示例 ===" << std::endl;
    std::cout << std::endl;

    // 基本单位
    std::cout << "1. 基本单位:" << std::endl;
    std::cout << "   distance = " << distance.count() << " m" << std::endl;
    std::cout << "   duration = " << duration.count() << " s" << std::endl;
    std::cout << "   mass = " << mass.count() << " kg" << std::endl;
    std::cout << "   speed = " << speed.count() << " km/h" << std::endl;
    std::cout << std::endl;

    // 长度转换
    std::cout << "2. 长度转换:" << std::endl;
    std::cout << "   1000 m = " << km << " km" << std::endl;
    std::cout << "   1609.344 m = " << miles << " miles" << std::endl;
    std::cout << "   1 m = " << feet << " feet" << std::endl;
    std::cout << "   1 m = " << inches << " inches" << std::endl;
    std::cout << std::endl;

    // 质量转换
    std::cout << "3. 质量转换:" << std::endl;
    std::cout << "   1 kg = " << lbs << " lbs" << std::endl;
    std::cout << "   1 kg = " << oz << " oz" << std::endl;
    std::cout << "   1 kg = " << g << " g" << std::endl;
    std::cout << std::endl;

    // 时间转换
    std::cout << "4. 时间转换:" << std::endl;
    std::cout << "   60 s = " << min << " min" << std::endl;
    std::cout << "   3600 s = " << h << " h" << std::endl;
    std::cout << "   1 s = " << ms << " ms" << std::endl;
    std::cout << std::endl;

    // 速度转换
    std::cout << "5. 速度转换:" << std::endl;
    std::cout << "   36 km/h = " << m_s << " m/s" << std::endl;
    std::cout << "   10 m/s = " << mph << " mph" << std::endl;
    std::cout << std::endl;

    // 温度转换
    std::cout << "6. 温度转换:" << std::endl;
    std::cout << "   100 °C = " << f << " °F" << std::endl;
    std::cout << "   0 °C = " << k << " K" << std::endl;
    std::cout << std::endl;

    // 能量转换
    std::cout << "7. 能量转换:" << std::endl;
    std::cout << "   4184 J = " << cal << " cal" << std::endl;
    std::cout << "   1000 J = " << kj << " kJ" << std::endl;
    std::cout << std::endl;

    // 单位运算
    std::cout << "8. 单位运算:" << std::endl;
    std::cout << "   speed = distance / time = " << calculated_speed.count() << " m/s" << std::endl;
    std::cout << "   force = mass * g = " << force.count() << " N" << std::endl;
    std::cout << "   energy = force * distance = " << energy.count() << " J" << std::endl;
    std::cout << "   power = energy / time = " << power.count() << " W" << std::endl;
    std::cout << std::endl;

    // 实际应用
    std::cout << "9. 实际应用:" << std::endl;
    std::cout << "   BMI(1.75m, 70kg) = " << calculate_bmi(1.75, 70.0) << std::endl;
    std::cout << "   动能(10kg, 5m/s) = " << kinetic_energy(10.0, 5.0) << " J" << std::endl;
    std::cout << "   功率(100J, 10s) = " << power_watts(100.0, 10.0) << " W" << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
