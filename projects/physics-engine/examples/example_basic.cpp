#include "physics_engine/physics_engine.h"
#include <iostream>
#include <iomanip>

int main() {
    std::cout << "=== 物理引擎基础示例 ===" << std::endl;
    std::cout << "版本: " << physics_engine::get_version() << std::endl;
    std::cout << std::endl;

    // 创建物理世界
    physics_engine::WorldConfig config;
    config.gravity = {0.0, -9.81};  // 重力加速度
    config.time_step = 1.0 / 60.0;  // 60 FPS

    physics_engine::World world(config);

    // 创建一个动态物体
    physics_engine::RigidBodyDef ball_def;
    ball_def.position = {0.0, 50.0};  // 初始位置
    ball_def.mass = 1.0;              // 质量
    ball_def.restitution = 0.7;       // 弹性系数

    auto ball = world.create_body(ball_def);

    // 创建一个静态地面
    physics_engine::RigidBodyDef ground_def;
    ground_def.type = physics_engine::BodyType::Static;
    ground_def.position = {0.0, -1.0};

    auto ground = world.create_body(ground_def);

    // 模拟循环
    double total_time = 3.0;  // 模拟 3 秒
    double dt = config.time_step;
    int steps = static_cast<int>(total_time / dt);

    std::cout << "开始模拟..." << std::endl;
    std::cout << std::fixed << std::setprecision(3);
    std::cout << std::setw(10) << "时间(s)"
              << std::setw(15) << "位置Y(m)"
              << std::setw(15) << "速度Y(m/s)" << std::endl;
    std::cout << std::string(40, '-') << std::endl;

    for (int i = 0; i < steps; ++i) {
        double time = i * dt;

        // 每 0.5 秒输出一次状态
        if (i % static_cast<int>(0.5 / dt) == 0) {
            std::cout << std::setw(10) << time
                      << std::setw(15) << ball->position().y
                      << std::setw(15) << ball->velocity().y << std::endl;
        }

        world.step(dt);
    }

    std::cout << std::endl;
    std::cout << "模拟结束" << std::endl;
    std::cout << "最终位置: " << ball->position() << std::endl;
    std::cout << "最终速度: " << ball->velocity() << std::endl;

    return 0;
}
