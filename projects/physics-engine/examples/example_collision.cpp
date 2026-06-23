#include "physics_engine/physics_engine.h"
#include <iostream>
#include <iomanip>

int main() {
    std::cout << "=== 碰撞检测示例 ===" << std::endl;
    std::cout << std::endl;

    // 创建物理世界
    physics_engine::WorldConfig config;
    config.gravity = {0.0, -9.81};

    physics_engine::World world(config);

    // 设置碰撞回调
    int collision_count = 0;
    world.set_collision_callback([&collision_count](const physics_engine::CollisionManifold& manifold) {
        collision_count++;
        std::cout << "碰撞 #" << collision_count << " 检测到!" << std::endl;
        std::cout << "  法线: " << manifold.normal << std::endl;
        if (!manifold.contacts.empty()) {
            std::cout << "  接触点: " << manifold.contacts[0].position << std::endl;
            std::cout << "  穿透深度: " << manifold.contacts[0].penetration << std::endl;
        }
        std::cout << std::endl;
    });

    // 创建多个下落的球
    const int num_balls = 5;
    std::vector<std::shared_ptr<physics_engine::RigidBody>> balls;

    for (int i = 0; i < num_balls; ++i) {
        physics_engine::RigidBodyDef def;
        def.position = {static_cast<double>(i) * 2.0 - 4.0, 20.0 + static_cast<double>(i) * 5.0};
        def.mass = 1.0;
        def.restitution = 0.6;

        balls.push_back(world.create_body(def));
    }

    // 创建地面
    physics_engine::RigidBodyDef ground_def;
    ground_def.type = physics_engine::BodyType::Static;
    ground_def.position = {0.0, -1.0};
    auto ground = world.create_body(ground_def);

    // 创建墙壁
    physics_engine::RigidBodyDef left_wall_def;
    left_wall_def.type = physics_engine::BodyType::Static;
    left_wall_def.position = {-10.0, 5.0};
    auto left_wall = world.create_body(left_wall_def);

    physics_engine::RigidBodyDef right_wall_def;
    right_wall_def.type = physics_engine::BodyType::Static;
    right_wall_def.position = {10.0, 5.0};
    auto right_wall = world.create_body(right_wall_def);

    // 模拟
    double dt = 1.0 / 60.0;
    double total_time = 5.0;
    int steps = static_cast<int>(total_time / dt);

    std::cout << "开始模拟 " << num_balls << " 个球的碰撞..." << std::endl;
    std::cout << std::endl;

    for (int i = 0; i < steps; ++i) {
        world.step(dt);
    }

    std::cout << "模拟结束" << std::endl;
    std::cout << "总碰撞次数: " << collision_count << std::endl;
    std::cout << std::endl;

    // 输出最终状态
    std::cout << "球的最终状态:" << std::endl;
    std::cout << std::fixed << std::setprecision(2);
    for (int i = 0; i < num_balls; ++i) {
        std::cout << "  球 " << i << ": 位置=" << balls[i]->position()
                  << ", 速度=" << balls[i]->velocity() << std::endl;
    }

    return 0;
}
