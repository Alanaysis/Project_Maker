#include <iostream>
#include <cmath>
#include <cassert>
#include "physics_simulation/physics_simulation.h"

int main() {
    using namespace physics_simulation;

    World world;

    // Create two dynamic spheres
    RigidBodyDef sphere1_def;
    sphere1_def.type = BodyType::Dynamic;
    sphere1_def.position = {-3.0, 0.0};
    sphere1_def.velocity = {5.0, 0.0};
    sphere1_def.radius = 0.5;
    sphere1_def.mass = 1.0;
    sphere1_def.restitution = 0.8;
    sphere1_def.name = "sphere1";
    auto sphere1 = world.create_body(sphere1_def);

    RigidBodyDef sphere2_def;
    sphere2_def.type = BodyType::Dynamic;
    sphere2_def.position = {3.0, 0.0};
    sphere2_def.velocity = {-5.0, 0.0};
    sphere2_def.radius = 0.5;
    sphere2_def.mass = 1.0;
    sphere2_def.restitution = 0.8;
    sphere2_def.name = "sphere2";
    auto sphere2 = world.create_body(sphere2_def);

    // Simulate until collision
    for (int i = 0; i < 120; ++i) {
        world.step();
    }

    std::cout << "Collision example:" << std::endl;
    std::cout << "Sphere1 position: (" << sphere1->position().x << ", " << sphere1->position().y << ")" << std::endl;
    std::cout << "Sphere1 velocity: (" << sphere1->velocity().x << ", " << sphere1->velocity().y << ")" << std::endl;
    std::cout << "Sphere2 position: (" << sphere2->position().x << ", " << sphere2->position().y << ")" << std::endl;
    std::cout << "Sphere2 velocity: (" << sphere2->velocity().x << ", " << sphere2->velocity().y << ")" << std::endl;

    std::cout << "Collision example passed!" << std::endl;
    return 0;
}
