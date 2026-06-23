#include "physics_engine/physics_engine.h"
#include <iostream>
#include <iomanip>
#include <vector>

int main() {
    std::cout << "=== 约束求解示例 ===" << std::endl;
    std::cout << std::endl;

    // 创建物理世界
    physics_engine::WorldConfig config;
    config.gravity = {0.0, -9.81};

    physics_engine::World world(config);

    // 创建锚点（固定在空中）
    physics_engine::RigidBodyDef anchor_def;
    anchor_def.type = physics_engine::BodyType::Static;
    anchor_def.position = {0.0, 15.0};
    auto anchor = world.create_body(anchor_def);

    // 创建链条
    const int num_links = 6;
    std::vector<std::shared_ptr<physics_engine::RigidBody>> links;

    for (int i = 0; i < num_links; ++i) {
        physics_engine::RigidBodyDef def;
        def.position = {static_cast<double>(i + 1) * 3.0, 15.0};
        def.mass = 1.0;

        links.push_back(world.create_body(def));
    }

    // 创建距离约束（链条）
    auto first_constraint = world.create_distance_constraint(
        anchor, links[0],
        physics_engine::Vector2D(0.0, 0.0),
        physics_engine::Vector2D(0.0, 0.0),
        3.0);
    first_constraint->stiffness = 1.0;

    for (int i = 0; i < num_links - 1; ++i) {
        auto constraint = world.create_distance_constraint(
            links[i], links[i + 1],
            physics_engine::Vector2D(0.0, 0.0),
            physics_engine::Vector2D(0.0, 0.0),
            3.0);
        constraint->stiffness = 1.0;
    }

    // 模拟
    double dt = 1.0 / 60.0;
    double total_time = 5.0;
    int steps = static_cast<int>(total_time / dt);

    std::cout << "开始模拟链条下落..." << std::endl;
    std::cout << std::fixed << std::setprecision(2);
    std::cout << std::setw(10) << "时间(s)"
              << std::setw(20) << "最后一个链接位置" << std::endl;
    std::cout << std::string(30, '-') << std::endl;

    for (int i = 0; i < steps; ++i) {
        double time = i * dt;

        // 每 0.5 秒输出一次状态
        if (i % static_cast<int>(0.5 / dt) == 0) {
            std::cout << std::setw(10) << time
                      << std::setw(20) << links.back()->position() << std::endl;
        }

        world.step(dt);
    }

    std::cout << std::endl;
    std::cout << "模拟结束" << std::endl;
    std::cout << std::endl;

    // 输出链条状态
    std::cout << "链条最终状态:" << std::endl;
    std::cout << "  锚点: " << anchor->position() << std::endl;
    for (int i = 0; i < num_links; ++i) {
        std::cout << "  链接 " << i << ": " << links[i]->position() << std::endl;
    }

    // 验证约束是否保持
    std::cout << std::endl;
    std::cout << "约束验证:" << std::endl;
    double dist = anchor->position().distance_to(links[0]->position());
    std::cout << "  锚点到第一个链接的距离: " << dist
              << " (目标: 3.0)" << std::endl;

    for (int i = 0; i < num_links - 1; ++i) {
        dist = links[i]->position().distance_to(links[i + 1]->position());
        std::cout << "  链接 " << i << " 到链接 " << i + 1
                  << " 的距离: " << dist << " (目标: 3.0)" << std::endl;
    }

    return 0;
}
