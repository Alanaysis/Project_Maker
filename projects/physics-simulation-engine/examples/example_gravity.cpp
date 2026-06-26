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

    // Create a pendulum
    RigidBodyDef bob_def;
    bob_def.type = BodyType::Dynamic;
    bob_def.position = {2.0, 0.0};
    bob_def.radius = 0.3;
    bob_def.mass = 1.0;
    bob_def.restitution = 0.0;
    bob_def.friction = 0.1;
    bob_def.name = "pendulum_bob";
    auto bob = world.create_body(bob_def);

    // Pin the bob to the origin (pivot)
    auto pin = world.create_pin_constraint(bob, {0.0, 0.0}, {2.0, 0.0});

    // Simulate
    for (int i = 0; i < 360; ++i) {
        world.step();
    }

    std::cout << "Pendulum simulation:" << std::endl;
    std::cout << "Bob position: (" << bob->position().x << ", " << bob->position().y << ")" << std::endl;
    std::cout << "Bob velocity: (" << bob->velocity().x << ", " << bob->velocity().y << ")" << std::endl;

    // Verify pendulum is swinging
    assert(std::abs(bob->position().x) < 2.0);
    assert(bob->position().y < 0.0);

    std::cout << "Gravity example passed!" << std::endl;
    return 0;
}
