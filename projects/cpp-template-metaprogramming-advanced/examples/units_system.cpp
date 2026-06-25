/**
 * @file units_system.cpp
 * @brief 单位系统示例
 *
 * 类型安全的物理单位系统，在编译期检查单位一致性。
 */

#include <iostream>
#include "../include/applications/units_system.hpp"

int main() {
    using namespace tmp::units;

    std::cout << "=== Units System ===" << std::endl;
    std::cout << std::endl;

    // 1. 基本量
    std::cout << "--- 1. Basic Quantities ---" << std::endl;

    Quantity<Meter> distance(100.0);
    Quantity<Second> time(9.58);
    Quantity<Kilogram> mass(80.0);

    std::cout << "Distance: " << distance << std::endl;
    std::cout << "Time: " << time << std::endl;
    std::cout << "Mass: " << mass << std::endl;
    std::cout << std::endl;

    // 2. 导出量（自动计算单位）
    std::cout << "--- 2. Derived Quantities ---" << std::endl;

    auto velocity = distance / time;
    std::cout << "Velocity = distance / time = " << velocity << std::endl;

    auto acceleration = velocity / time;
    std::cout << "Acceleration = velocity / time = " << acceleration << std::endl;

    auto force = mass * acceleration;
    std::cout << "Force = mass * acceleration = " << force << std::endl;
    std::cout << std::endl;

    // 3. 单位转换
    std::cout << "--- 3. Unit Conversion ---" << std::endl;

    Quantity<Kilometer> km(1.0);
    Quantity<Meter> m(km);  // 自动转换
    std::cout << "1 km = " << m << std::endl;

    Quantity<Hour> hour(1.0);
    Quantity<Second> sec(hour);  // 自动转换
    std::cout << "1 hour = " << sec << std::endl;
    std::cout << std::endl;

    // 4. 数学运算
    std::cout << "--- 4. Math Operations ---" << std::endl;

    Quantity<Meter> a(3.0);
    Quantity<Meter> b(4.0);

    auto sum = a + b;
    std::cout << "3m + 4m = " << sum << std::endl;

    auto scaled = a + a;  // 3m + 3m = 6m
    std::cout << "3m + 3m = " << scaled << std::endl;

    auto area = a * b;
    std::cout << "3m * 4m = " << area << " (area)" << std::endl;
    std::cout << std::endl;

    // 5. 能量计算
    std::cout << "--- 5. Energy Calculation ---" << std::endl;

    Quantity<Kilogram> m1(2.0);
    Quantity<VelocityUnit> v(10.0);  // 10 m/s

    // 力 = m * a
    Quantity<AccelerationUnit> acc(9.81);
    auto weight = m1 * acc;
    std::cout << "Weight = " << weight << std::endl;
    std::cout << std::endl;

    // 6. 编译期检查
    std::cout << "--- 6. Compile-time Checks ---" << std::endl;
    std::cout << "Units system prevents errors like:" << std::endl;
    std::cout << "  distance + time  // ERROR: different dimensions" << std::endl;
    std::cout << "  mass + force     // ERROR: different dimensions" << std::endl;
    std::cout << "These errors are caught at compile time!" << std::endl;

    return 0;
}
