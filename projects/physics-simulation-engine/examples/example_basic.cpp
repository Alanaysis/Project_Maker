#include <iostream>
#include <cmath>
#include <cassert>
#include "physics_simulation/physics_simulation.h"

int main() {
    using namespace physics_simulation;

    WorldConfig config;
    config.gravity = {0.0, -9.81};
    config.velocity_iterations = 8;
    config.position_iterations = 3;

    World world(config);

    // Create a static ground
    RigidBodyDef ground_def;
    ground_def.type = BodyType::Static;
    ground_def.position = {0.0, -10.0};
    ground_def.radius = 10.0;
    ground_def.name = "ground";
    auto ground = world.create_body(ground_def);

    // Create a dynamic ball
    RigidBodyDef ball_def;
    ball_def.type = BodyType::Dynamic;
    ball_def.position = {0.0, 10.0};
    ball_def.velocity = {2.0, 0.0};
    ball_def.radius = 0.5;
    ball_def.mass = 1.0;
    ball_def.restitution = 0.7;
    ball_def.friction = 0.3;
    ball_def.name = "ball";
    auto ball = world.create_body(ball_def);

    // Simulate a few steps
    for (int i = 0; i < 60; ++i) {
        world.step();
    }

    std::cout << "After 60 steps (1 second):" << std::endl;
    std::cout << "Ball position: (" << ball->position().x << ", " << ball->position().y << ")" << std::endl;
    std::cout << "Ball velocity: (" << ball->velocity().x << ", " << ball->velocity().y << ")" << std::endl;

    // Verify ball has fallen
    assert(ball->position().y < 10.0);
    assert(ball->position().y > -10.0);

    std::cout << "Basic example passed!" << std::endl;
    return 0;
}
