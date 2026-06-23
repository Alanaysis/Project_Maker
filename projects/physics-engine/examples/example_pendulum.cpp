#include "physics_engine/physics_engine.h"
#include <iostream>
#include <iomanip>
#include <cmath>

int main() {
    std::cout << "=== 摆锤示例 ===" << std::endl;
    std::cout << std::endl;

    // 创建物理世界
    physics_engine::WorldConfig config;
    config.gravity = {0.0, -9.81};

    physics_engine::World world(config);

    // 创建固定点
    physics_engine::RigidBodyDef pivot_def;
    pivot_def.type = physics_engine::BodyType::Static;
    pivot_def.position = {0.0, 10.0};
    auto pivot = world.create_body(pivot_def);

    // 创建摆锤
    double pendulum_length = 8.0;
    double initial_angle = M_PI / 4;  // 45 度

    physics_engine::RigidBodyDef bob_def;
    bob_def.position = {
        pendulum_length * std::sin(initial_angle),
        10.0 - pendulum_length * std::cos(initial_angle)
    };
    bob_def.mass = 1.0;

    auto bob = world.create_body(bob_def);

    // 创建距离约束
    auto constraint = world.create_distance_constraint(
        pivot, bob,
        physics_engine::Vector2D(0.0, 0.0),
        physics_engine::Vector2D(0.0, 0.0),
        pendulum_length);

    constraint->stiffness = 1.0;

    // 模拟
    double dt = 1.0 / 60.0;
    double total_time = 10.0;
    int steps = static_cast<int>(total_time / dt);

    std::cout << "摆锤参数:" << std::endl;
    std::cout << "  长度: " << pendulum_length << " m" << std::endl;
    std::cout << "  初始角度: " << (initial_angle * 180.0 / M_PI) << " 度" << std::endl;
    std::cout << "  质量: " << bob->mass() << " kg" << std::endl;
    std::cout << std::endl;

    std::cout << "开始模拟..." << std::endl;
    std::cout << std::fixed << std::setprecision(3);
    std::cout << std::setw(10) << "时间(s)"
              << std::setw(15) << "角度(度)"
              << std::setw(15) << "角速度"
              << std::setw(20) << "位置" << std::endl;
    std::cout << std::string(60, '-') << std::endl;

    // 理论周期：T = 2π√(L/g)
    double theoretical_period = 2.0 * M_PI * std::sqrt(pendulum_length / 9.81);
    std::cout << "理论周期: " << theoretical_period << " s" << std::endl;
    std::cout << std::endl;

    // 记录几个周期
    double max_angle = 0.0;
    double prev_angle = 0.0;
    int period_count = 0;

    for (int i = 0; i < steps; ++i) {
        double time = i * dt;

        // 计算当前角度
        physics_engine::Vector2D diff = bob->position() - pivot->position();
        double current_angle = std::atan2(diff.x, -diff.y);

        // 检测最大角度（用于验证能量守恒）
        if (std::abs(current_angle) > std::abs(max_angle)) {
            max_angle = current_angle;
        }

        // 检测周期（角度过零点）
        if (prev_angle < 0 && current_angle >= 0) {
            period_count++;
            if (period_count <= 3) {
                std::cout << "第 " << period_count << " 个周期完成于 t = " << time << " s" << std::endl;
            }
        }
        prev_angle = current_angle;

        // 每 0.5 秒输出一次状态
        if (i % static_cast<int>(0.5 / dt) == 0) {
            double angle_degrees = current_angle * 180.0 / M_PI;
            double angular_velocity = bob->angular_velocity();

            std::cout << std::setw(10) << time
                      << std::setw(15) << angle_degrees
                      << std::setw(15) << angular_velocity
                      << std::setw(20) << bob->position() << std::endl;
        }

        world.step(dt);
    }

    std::cout << std::endl;
    std::cout << "模拟结束" << std::endl;
    std::cout << std::endl;

    // 验证能量守恒
    std::cout << "能量分析:" << std::endl;

    // 初始能量
    double initial_height = bob_def.position.y;
    double initial_energy = bob->mass() * 9.81 * initial_height;

    // 最终能量
    double final_height = bob->position().y;
    double final_kinetic = 0.5 * bob->mass() * bob->velocity().length_squared();
    double final_potential = bob->mass() * 9.81 * final_height;
    double final_energy = final_kinetic + final_potential;

    std::cout << "  初始势能: " << initial_energy << " J" << std::endl;
    std::cout << "  最终动能: " << final_kinetic << " J" << std::endl;
    std::cout << "  最终势能: " << final_potential << " J" << std::endl;
    std::cout << "  最终总能量: " << final_energy << " J" << std::endl;
    std::cout << "  能量损失: " << (initial_energy - final_energy) << " J"
              << " (" << ((initial_energy - final_energy) / initial_energy * 100.0) << "%)" << std::endl;

    // 验证约束
    std::cout << std::endl;
    std::cout << "约束验证:" << std::endl;
    double distance = pivot->position().distance_to(bob->position());
    std::cout << "  摆长: " << distance << " m (目标: " << pendulum_length << " m)" << std::endl;
    std::cout << "  误差: " << std::abs(distance - pendulum_length) << " m" << std::endl;

    return 0;
}
