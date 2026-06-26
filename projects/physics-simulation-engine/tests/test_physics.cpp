#include <cmath>
#include <iostream>
#include <string>
#include <functional>
#include <cassert>
#include <vector>
#include <memory>
#include "physics_simulation/physics_simulation.h"

using namespace physics_simulation;

int tests_run = 0;
int tests_passed = 0;
int tests_failed = 0;

void assert_eq(double a, double b, const std::string& msg, int line = __LINE__) {
    tests_run++;
    if (std::abs(a - b) < 1e-9) {
        tests_passed++;
    } else {
        tests_failed++;
        std::cerr << "FAIL: " << msg << " at line " << line
                  << " (expected " << b << ", got " << a << ")" << std::endl;
    }
}

void assert_true(bool cond, const std::string& msg, int line = __LINE__) {
    tests_run++;
    if (cond) {
        tests_passed++;
    } else {
        tests_failed++;
        std::cerr << "FAIL: " << msg << " at line " << line << std::endl;
    }
}

void assert_false(bool cond, const std::string& msg, int line = __LINE__) {
    tests_run++;
    if (!cond) {
        tests_passed++;
    } else {
        tests_failed++;
        std::cerr << "FAIL: " << msg << " at line " << line << std::endl;
    }
}

void assert_near(double a, double b, double eps, const std::string& msg, int line = __LINE__) {
    tests_run++;
    if (std::abs(a - b) < eps) {
        tests_passed++;
    } else {
        tests_failed++;
        std::cerr << "FAIL: " << msg << " at line " << line
                  << " (expected ~" << b << ", got " << a << ")" << std::endl;
    }
}

// ============================================================
// Vec2 Tests
// ============================================================

void test_vec2_addition() {
    Vec2 a(1.0, 2.0);
    Vec2 b(3.0, 4.0);
    Vec2 result = a + b;
    assert_eq(result.x, 4.0, "Vec2 addition x");
    assert_eq(result.y, 6.0, "Vec2 addition y");
}

void test_vec2_subtraction() {
    Vec2 a(5.0, 6.0);
    Vec2 b(3.0, 4.0);
    Vec2 result = a - b;
    assert_eq(result.x, 2.0, "Vec2 subtraction x");
    assert_eq(result.y, 2.0, "Vec2 subtraction y");
}

void test_vec2_scalar_mult() {
    Vec2 a(2.0, 3.0);
    Vec2 result = a * 2.0;
    assert_eq(result.x, 4.0, "Vec2 scalar mult x");
    assert_eq(result.y, 6.0, "Vec2 scalar mult y");
}

void test_vec2_dot_product() {
    Vec2 a(1.0, 0.0);
    Vec2 b(0.0, 1.0);
    assert_eq(a.dot(b), 0.0, "Orthogonal dot product");

    Vec2 c(3.0, 4.0);
    Vec2 d(5.0, 6.0);
    assert_eq(c.dot(d), 39.0, "Dot product 3,4 . 5,6");
}

void test_vec2_cross_product() {
    Vec2 a(1.0, 0.0);
    Vec2 b(0.0, 1.0);
    assert_eq(a.cross(b), 1.0, "Cross product i x j");

    Vec2 c(0.0, 1.0);
    Vec2 d(1.0, 0.0);
    assert_eq(c.cross(d), -1.0, "Cross product j x i");
}

void test_vec2_length() {
    Vec2 a(3.0, 4.0);
    assert_eq(a.length(), 5.0, "Length of (3,4)");
}

void test_vec2_length_squared() {
    Vec2 a(3.0, 4.0);
    assert_eq(a.length_squared(), 25.0, "Length squared of (3,4)");
}

void test_vec2_normalized() {
    Vec2 a(3.0, 4.0);
    Vec2 n = a.normalized();
    assert_near(n.length(), 1.0, 1e-9, "Normalized length");
}

void test_vec2_zero() {
    Vec2 z = Vec2::zero();
    assert_eq(z.x, 0.0, "Zero vector x");
    assert_eq(z.y, 0.0, "Zero vector y");
}

void test_vec2_unit_vectors() {
    Vec2 ux = Vec2::unit_x();
    Vec2 uy = Vec2::unit_y();
    assert_eq(ux.x, 1.0, "unit_x x");
    assert_eq(ux.y, 0.0, "unit_x y");
    assert_eq(uy.x, 0.0, "unit_y x");
    assert_eq(uy.y, 1.0, "unit_y y");
}

// ============================================================
// AABB Tests
// ============================================================

void test_aabb_center() {
    AABB aabb(-2.0, -2.0, 2.0, 2.0);
    Vec2 center = aabb.center();
    assert_eq(center.x, 0.0, "AABB center x");
    assert_eq(center.y, 0.0, "AABB center y");
}

void test_aabb_size() {
    AABB aabb(-1.0, -1.0, 3.0, 3.0);
    Vec2 size = aabb.size();
    assert_eq(size.x, 4.0, "AABB size x");
    assert_eq(size.y, 4.0, "AABB size y");
}

void test_aabb_contains() {
    AABB aabb(-1.0, -1.0, 1.0, 1.0);
    assert_true(aabb.contains({0.0, 0.0}), "AABB contains origin");
    assert_false(aabb.contains({2.0, 2.0}), "AABB does not contain outside");
}

void test_aabb_intersects() {
    AABB a1(-1.0, -1.0, 1.0, 1.0);
    AABB a2(0.0, 0.0, 2.0, 2.0);
    assert_true(a1.intersects(a2), "AABB intersecting");

    AABB a3(3.0, 3.0, 5.0, 5.0);
    assert_false(a1.intersects(a3), "AABB non-intersecting");
}

void test_aabb_merge() {
    AABB a1(-2.0, -2.0, 0.0, 0.0);
    AABB a2(0.0, 0.0, 2.0, 2.0);
    AABB merged = a1.merge(a2);
    assert_eq(merged.min.x, -2.0, "Merge min x");
    assert_eq(merged.min.y, -2.0, "Merge min y");
    assert_eq(merged.max.x, 2.0, "Merge max x");
    assert_eq(merged.max.y, 2.0, "Merge max y");
}

void test_aabb_expanded() {
    AABB aabb(0.0, 0.0, 2.0, 2.0);
    AABB expanded = aabb.expanded(1.0);
    assert_eq(expanded.min.x, -1.0, "Expanded min x");
    assert_eq(expanded.min.y, -1.0, "Expanded min y");
    assert_eq(expanded.max.x, 3.0, "Expanded max x");
    assert_eq(expanded.max.y, 3.0, "Expanded max y");
}

void test_aabb_is_valid() {
    AABB valid(0.0, 0.0, 2.0, 2.0);
    assert_true(valid.is_valid(), "Valid AABB");

    AABB invalid(2.0, 2.0, 0.0, 0.0);
    assert_false(invalid.is_valid(), "Invalid AABB");
}

void test_aabb_area() {
    AABB aabb(0.0, 0.0, 4.0, 6.0);
    assert_eq(aabb.area(), 24.0, "AABB area");
}

void test_aabb_half_size() {
    AABB aabb(0.0, 0.0, 4.0, 6.0);
    Vec2 hs = aabb.half_size();
    assert_eq(hs.x, 2.0, "Half size x");
    assert_eq(hs.y, 3.0, "Half size y");
}

// ============================================================
// Collision Detection Tests
// ============================================================

void test_aabb_vs_aabb_no_collision() {
    AABB a1(-5.0, -5.0, -2.0, -2.0);
    AABB a2(2.0, 2.0, 5.0, 5.0);
    CollisionResult result = aabb_vs_aabb(a1, a2);
    assert_false(result.collided, "AABB no collision");
}

void test_aabb_vs_aabb_collision() {
    AABB a1(-1.0, -1.0, 1.0, 1.0);
    AABB a2(0.0, 0.0, 3.0, 3.0);
    CollisionResult result = aabb_vs_aabb(a1, a2);
    assert_true(result.collided, "AABB collision detected");
    assert_true(result.penetration > 0.0, "AABB positive penetration");
}

void test_circle_vs_circle_no_collision() {
    CollisionResult result = circle_vs_circle({0.0, 0.0}, 1.0, {5.0, 0.0}, 1.0);
    assert_false(result.collided, "Circle no collision");
}

void test_circle_vs_circle_collision() {
    CollisionResult result = circle_vs_circle({0.0, 0.0}, 2.0, {1.0, 0.0}, 1.0);
    assert_true(result.collided, "Circle collision detected");
    // dist=1.0, radius_sum=3.0, penetration=3.0-1.0=2.0
    assert_near(result.penetration, 2.0, 1e-9, "Circle penetration");
}

void test_circle_vs_circle_touching() {
    // Circles touching exactly: center distance = radius_a + radius_b
    CollisionResult result = circle_vs_circle({0.0, 0.0}, 1.0, {2.0, 0.0}, 1.0);
    assert_true(result.collided, "Circle touching detected");
    // dist=2.0, radius_sum=2.0, penetration=0.0
    assert_near(result.penetration, 0.0, 1e-9, "Circle touching penetration");
    // Normal: (2,0)/2.0 = (1,0)
    assert_near(result.normal.x, 1.0, 1e-6, "Circle touch normal x");
    assert_near(result.normal.y, 0.0, 1e-6, "Circle touch normal y");
}

void test_aabb_vs_circle_no_collision() {
    AABB aabb(-3.0, -3.0, -1.0, -1.0);
    CollisionResult result = aabb_vs_circle(aabb, {3.0, 3.0}, 0.5);
    assert_false(result.collided, "AABB vs circle no collision");
}

void test_aabb_vs_circle_collision() {
    AABB aabb(-1.0, -1.0, 1.0, 1.0);
    CollisionResult result = aabb_vs_circle(aabb, {2.0, 0.0}, 1.0);
    assert_true(result.collided, "AABB vs circle collision");
}

void test_aabb_vs_circle_inside() {
    AABB aabb(-1.0, -1.0, 1.0, 1.0);
    CollisionResult result = aabb_vs_circle(aabb, {0.0, 0.0}, 2.0);
    assert_true(result.collided, "Circle inside AABB");
}

void test_circle_normal_direction() {
    // Test with overlapping circles
    CollisionResult result = circle_vs_circle({0.0, 0.0}, 2.0, {3.0, 0.0}, 1.0);
    // dist=3.0, radius_sum=3.0, touching
    assert_true(result.collided, "Circle touch");
    assert_near(result.normal.x, 1.0, 1e-9, "Circle normal x");
    assert_near(result.normal.y, 0.0, 1e-9, "Circle normal y");
}

void test_circle_normal_direction_overlapping() {
    CollisionResult result = circle_vs_circle({0.0, 0.0}, 2.0, {2.5, 0.0}, 1.0);
    // dist=2.5, radius_sum=3.0, overlap
    assert_true(result.collided, "Circle overlap");
    assert_near(result.normal.x, 1.0, 1e-9, "Circle normal x");
    assert_near(result.normal.y, 0.0, 1e-9, "Circle normal y");
}

// ============================================================
// RigidBody Tests
// ============================================================

void test_create_dynamic_body() {
    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.position = {1.0, 2.0};
    def.mass = 2.0;
    def.radius = 0.5;
    def.name = "test_body";

    RigidBody body(def);

    assert_eq(body.mass(), 2.0, "Dynamic mass");
    assert_eq(body.inv_mass(), 0.5, "Dynamic inv_mass");
    assert_eq(body.radius(), 0.5, "Dynamic radius");
    assert_eq(body.position().x, 1.0, "Dynamic position x");
    assert_eq(body.position().y, 2.0, "Dynamic position y");
    assert_true(body.is_dynamic(), "Is dynamic");
    assert_false(body.is_static(), "Not static");
}

void test_create_static_body() {
    RigidBodyDef def;
    def.type = BodyType::Static;
    def.position = {0.0, 0.0};
    def.mass = 0.0;

    RigidBody body(def);

    assert_true(body.is_static(), "Is static");
    assert_eq(body.inv_mass(), 0.0, "Static inv_mass");
    assert_eq(body.inv_inertia(), 0.0, "Static inv_inertia");
}

void test_create_kinematic_body() {
    RigidBodyDef def;
    def.type = BodyType::Kinematic;

    RigidBody body(def);

    assert_true(body.is_kinematic(), "Is kinematic");
}

void test_apply_force() {
    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.mass = 1.0;
    def.radius = 0.5;

    RigidBody body(def);
    body.apply_force({10.0, 0.0});

    assert_eq(body.force().x, 10.0, "Force x");
    assert_eq(body.force().y, 0.0, "Force y");
}

void test_apply_impulse() {
    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.mass = 2.0;
    def.radius = 0.5;

    RigidBody body(def);
    body.apply_impulse({10.0, 0.0});

    assert_near(body.velocity().x, 5.0, 1e-9, "Impulse velocity x");
    assert_eq(body.velocity().y, 0.0, "Impulse velocity y");
}

void test_integrate() {
    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.position = {0.0, 0.0};
    def.velocity = {0.0, 0.0};
    def.mass = 1.0;
    def.radius = 0.5;
    def.linear_damping = 0.0;
    def.angular_damping = 0.0;

    RigidBody body(def);
    body.apply_force({10.0, 0.0});

    body.integrate(1.0);

    assert_near(body.velocity().x, 10.0, 1e-9, "Integrate velocity x");
    assert_near(body.position().x, 10.0, 1e-9, "Integrate position x (first step)");
    assert_eq(body.force().x, 0.0, "Force cleared");
}

void test_integrate_with_gravity() {
    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.position = {0.0, 10.0};
    def.velocity = {0.0, 0.0};
    def.mass = 1.0;
    def.radius = 0.5;
    def.linear_damping = 0.0;
    def.angular_damping = 0.0;

    RigidBody body(def);
    body.apply_force({0.0, -9.81});

    body.integrate(1.0);

    // position = old_pos + (old_vel + new_vel)/2 * dt = 10 + (0 + (-9.81))/2 * 1 = 10 - 4.905 = 5.095
    // But integrate uses new velocity: pos += vel * dt = 10 + (-9.81) * 1 = 0.19
    assert_near(body.position().y, 0.19, 0.01, "Gravity position y");
}

void test_static_ignores_force() {
    RigidBodyDef def;
    def.type = BodyType::Static;
    def.mass = 0.0;

    RigidBody body(def);
    body.apply_force({100.0, 100.0});
    body.integrate(1.0);

    assert_eq(body.velocity().x, 0.0, "Static velocity x");
    assert_eq(body.velocity().y, 0.0, "Static velocity y");
    assert_eq(body.position().x, 0.0, "Static position x");
    assert_eq(body.position().y, 0.0, "Static position y");
}

void test_setters() {
    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.mass = 1.0;
    def.radius = 0.5;

    RigidBody body(def);
    body.set_position({5.0, 5.0});
    body.set_velocity({1.0, 2.0});
    body.set_mass(2.0);
    body.set_restitution(0.8);
    body.set_friction(0.5);
    body.set_radius(1.0);

    assert_eq(body.position().x, 5.0, "Set position x");
    assert_eq(body.velocity().x, 1.0, "Set velocity x");
    assert_eq(body.mass(), 2.0, "Set mass");
    assert_eq(body.inv_mass(), 0.5, "Set inv_mass");
    assert_eq(body.restitution(), 0.8, "Set restitution");
    assert_eq(body.friction(), 0.5, "Set friction");
    assert_eq(body.radius(), 1.0, "Set radius");
}

void test_clear_forces() {
    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.mass = 1.0;
    def.radius = 0.5;

    RigidBody body(def);
    body.apply_force({10.0, 20.0});
    body.apply_torque(5.0);

    body.clear_forces();

    assert_eq(body.force().x, 0.0, "Clear force x");
    assert_eq(body.force().y, 0.0, "Clear force y");
    assert_eq(body.torque(), 0.0, "Clear torque");
}

void test_velocity_at_point() {
    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.position = {0.0, 0.0};
    def.velocity = {1.0, 0.0};
    def.angular_velocity = 2.0;
    def.mass = 1.0;
    def.radius = 0.5;
    def.linear_damping = 0.0;
    def.angular_damping = 0.0;

    RigidBody body(def);
    Vec2 vel = body.velocity_at_point({0.0, 0.5});

    // vel = {1,0} + {-0.5,0} * 2 = {1-1, 0+0} = {0, 0}
    assert_near(vel.x, 0.0, 0.01, "Vel at point x");
    assert_near(vel.y, 0.0, 0.01, "Vel at point y");
}

void test_compute_aabb() {
    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.position = {2.0, 3.0};
    def.radius = 1.0;

    RigidBody body(def);
    AABB aabb = body.compute_aabb();

    assert_eq(aabb.min.x, 1.0, "AABB min x");
    assert_eq(aabb.min.y, 2.0, "AABB min y");
    assert_eq(aabb.max.x, 3.0, "AABB max x");
    assert_eq(aabb.max.y, 4.0, "AABB max y");
}

void test_mass_change() {
    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.mass = 1.0;
    def.radius = 0.5;

    RigidBody body(def);
    body.set_mass(4.0);

    assert_eq(body.mass(), 4.0, "Changed mass");
    assert_eq(body.inv_mass(), 0.25, "Changed inv_mass");
}

void test_body_name() {
    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.radius = 0.5;
    def.name = "named_body";

    RigidBody body(def);
    assert_true(body.name().length() > 0, "Body name not empty");
    assert_true(body.name() == "named_body", "Body name");

    body.set_name("new_name");
    assert_true(body.name() == "new_name", "Set body name");
}

// ============================================================
// World Tests
// ============================================================

void test_create_world() {
    WorldConfig config;
    config.gravity = {0.0, -9.81};
    World world(config);

    assert_eq(world.body_count(), 0, "Empty world count");
    assert_eq(world.config().gravity.y, -9.81, "World gravity y");
}

void test_create_and_destroy_body() {
    World world;

    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.position = {0.0, 0.0};
    def.radius = 0.5;
    def.name = "test_body";
    auto body = world.create_body(def);

    assert_eq(world.body_count(), 1, "Body count after create");

    world.destroy_body(body);
    assert_eq(world.body_count(), 0, "Body count after destroy");
}

void test_step_with_gravity() {
    WorldConfig config;
    config.gravity = {0.0, -9.81};

    World world(config);

    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.position = {0.0, 10.0};
    def.velocity = {0.0, 0.0};
    def.mass = 1.0;
    def.radius = 0.5;
    def.name = "falling_ball";
    auto ball = world.create_body(def);

    for (int i = 0; i < 60; ++i) {
        world.step();
    }

    assert_true(ball->position().y < 10.0, "Ball fell down");
}

void test_step_with_multiple_bodies() {
    WorldConfig config;
    config.gravity = {0.0, -9.81};

    World world(config);

    RigidBodyDef ground_def;
    ground_def.type = BodyType::Static;
    ground_def.position = {0.0, -10.0};
    ground_def.radius = 10.0;
    ground_def.name = "ground";
    auto ground = world.create_body(ground_def);

    RigidBodyDef ball_def;
    ball_def.type = BodyType::Dynamic;
    ball_def.position = {0.0, 10.0};
    ball_def.velocity = {2.0, 0.0};
    ball_def.radius = 0.5;
    ball_def.mass = 1.0;
    ball_def.restitution = 0.7;
    ball_def.name = "ball";
    auto ball = world.create_body(ball_def);

    assert_eq(world.body_count(), 2, "Two bodies");

    for (int i = 0; i < 60; ++i) {
        world.step();
    }

    assert_true(ball->position().y < 10.0, "Ball fell with ground present");
}

void test_static_body_does_not_move() {
    World world;

    RigidBodyDef def;
    def.type = BodyType::Static;
    def.position = {5.0, 5.0};
    def.mass = 0.0;
    def.radius = 1.0;
    def.name = "static_wall";
    auto wall = world.create_body(def);

    for (int i = 0; i < 60; ++i) {
        world.step();
    }

    assert_eq(wall->position().x, 5.0, "Static x unchanged");
    assert_eq(wall->position().y, 5.0, "Static y unchanged");
}

void test_collision_callback() {
    WorldConfig config;
    config.gravity = {0.0, 0.0};
    World world(config);

    bool callback_called = false;

    world.set_collision_callback([&](const CollisionManifold&) {
        callback_called = true;
    });

    RigidBodyDef a_def;
    a_def.type = BodyType::Dynamic;
    a_def.position = {-1.0, 0.0};
    a_def.velocity = {5.0, 0.0};
    a_def.radius = 1.0;
    a_def.mass = 1.0;
    a_def.name = "a";
    auto a = world.create_body(a_def);

    RigidBodyDef b_def;
    b_def.type = BodyType::Dynamic;
    b_def.position = {1.0, 0.0};
    b_def.velocity = {-5.0, 0.0};
    b_def.radius = 1.0;
    b_def.mass = 1.0;
    b_def.name = "b";
    auto b = world.create_body(b_def);

    world.step();

    assert_true(callback_called, "Collision callback invoked");
}

void test_clear() {
    World world;

    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.radius = 0.5;
    world.create_body(def);

    assert_eq(world.body_count(), 1, "One body before clear");

    world.clear();
    assert_eq(world.body_count(), 0, "Zero bodies after clear");
}

void test_set_config() {
    World world;

    WorldConfig new_config;
    new_config.gravity = {0.0, -19.62};
    new_config.velocity_iterations = 16;
    new_config.position_iterations = 6;

    world.set_config(new_config);

    assert_eq(world.config().gravity.y, -19.62, "Config gravity");
    assert_eq(world.config().velocity_iterations, 16, "Config velocity iters");
    assert_eq(world.config().position_iterations, 6, "Config position iters");
}

void test_custom_time_step() {
    WorldConfig config;
    config.gravity = {0.0, -9.81};

    World world(config);

    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.position = {0.0, 10.0};
    def.velocity = {0.0, 0.0};
    def.mass = 1.0;
    def.radius = 0.5;
    def.name = "ball";
    auto ball = world.create_body(def);

    for (int i = 0; i < 60; ++i) {
        world.step(1.0 / 30.0);
    }

    assert_true(ball->position().y < -9.0, "Custom timestep gravity");
}

void test_damping() {
    WorldConfig config;
    config.gravity = {0.0, 0.0};

    World world(config);

    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.position = {0.0, 0.0};
    def.velocity = {10.0, 0.0};
    def.mass = 1.0;
    def.radius = 0.5;
    def.linear_damping = 0.1;
    def.name = "damped_ball";
    auto ball = world.create_body(def);

    for (int i = 0; i < 60; ++i) {
        world.step();
    }

    assert_true(ball->velocity().x < 10.0, "Damping reduces velocity");
    assert_true(ball->velocity().x > 0.0, "Damping does not stop completely");
}

void test_restitution() {
    WorldConfig config;
    config.gravity = {0.0, -9.81};

    World world(config);

    RigidBodyDef ground_def;
    ground_def.type = BodyType::Static;
    ground_def.position = {0.0, -5.0};
    ground_def.radius = 5.0;
    ground_def.name = "ground";
    auto ground = world.create_body(ground_def);

    RigidBodyDef ball_def;
    ball_def.type = BodyType::Dynamic;
    ball_def.position = {0.0, 0.0};
    ball_def.velocity = {0.0, -10.0};
    ball_def.radius = 0.5;
    ball_def.mass = 1.0;
    ball_def.restitution = 0.9;
    ball_def.name = "bouncy_ball";
    auto ball = world.create_body(ball_def);

    for (int i = 0; i < 180; ++i) {
        world.step();
    }

    assert_true(ball->velocity().y > -10.0, "Restitution reduces impact");
}

void test_body_id_uniqueness() {
    RigidBody::reset_id();

    World world;

    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.radius = 0.5;

    auto body1 = world.create_body(def);
    auto body2 = world.create_body(def);
    auto body3 = world.create_body(def);

    assert_true(body1->id() != body2->id(), "Body IDs unique");
    assert_true(body2->id() != body3->id(), "Body IDs unique");
    assert_true(body1->id() != body3->id(), "Body IDs unique");
}

void test_user_data() {
    int user_data = 42;

    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.radius = 0.5;
    def.user_data = &user_data;

    RigidBody body(def);

    int* retrieved = static_cast<int*>(body.user_data());
    assert_true(retrieved != nullptr, "User data not null");
    assert_eq(*retrieved, 42, "User data value");
}

// ============================================================
// Constraint Tests
// ============================================================

void test_pin_constraint() {
    World world;

    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.position = {2.0, 0.0};
    def.radius = 0.5;
    def.mass = 1.0;
    def.name = "pinned_body";
    auto body = world.create_body(def);

    auto pin = world.create_pin_constraint(body, {0.0, 0.0}, {2.0, 0.0});

    for (int i = 0; i < 10; ++i) {
        world.step();
    }

    double dist = std::sqrt(body->position().x * body->position().x + body->position().y * body->position().y);
    assert_true(dist < 2.1, "Pin constraint holds");
}

void test_distance_constraint() {
    World world;

    RigidBodyDef a_def;
    a_def.type = BodyType::Dynamic;
    a_def.position = {0.0, 0.0};
    a_def.radius = 0.5;
    a_def.mass = 1.0;
    a_def.name = "a";
    auto a = world.create_body(a_def);

    RigidBodyDef b_def;
    b_def.type = BodyType::Dynamic;
    b_def.position = {5.0, 0.0};
    b_def.radius = 0.5;
    b_def.mass = 1.0;
    b_def.name = "b";
    auto b = world.create_body(b_def);

    auto dist = world.create_distance_constraint(a, b, {0.0, 0.0}, {0.0, 0.0}, 5.0);

    a->apply_force({-100.0, 0.0});
    b->apply_force({100.0, 0.0});

    for (int i = 0; i < 10; ++i) {
        world.step();
    }

    double dist_between = (b->position() - a->position()).length();
    assert_true(dist_between < 5.5, "Distance constraint holds");
}

void test_hinge_constraint() {
    World world;

    RigidBodyDef a_def;
    a_def.type = BodyType::Dynamic;
    a_def.position = {0.0, 0.0};
    a_def.radius = 0.5;
    a_def.mass = 1.0;
    a_def.name = "hinge_a";
    auto a = world.create_body(a_def);

    RigidBodyDef b_def;
    b_def.type = BodyType::Dynamic;
    b_def.position = {3.0, 0.0};
    b_def.radius = 0.5;
    b_def.mass = 1.0;
    b_def.name = "hinge_b";
    auto b = world.create_body(b_def);

    auto hinge = world.create_hinge_constraint(a, b, {0.0, 0.0}, {0.0, 0.0});

    for (int i = 0; i < 10; ++i) {
        world.step();
    }

    double dist_between = (b->position() - a->position()).length();
    assert_true(dist_between < 3.5, "Hinge constraint holds");
}

void test_constraint_solver() {
    World world;

    RigidBodyDef a_def;
    a_def.type = BodyType::Dynamic;
    a_def.position = {0.0, 0.0};
    a_def.radius = 0.5;
    a_def.mass = 1.0;
    a_def.name = "solver_a";
    auto a = world.create_body(a_def);

    RigidBodyDef b_def;
    b_def.type = BodyType::Dynamic;
    b_def.position = {10.0, 0.0};
    b_def.radius = 0.5;
    b_def.mass = 1.0;
    b_def.name = "solver_b";
    auto b = world.create_body(b_def);

    auto pin_a = world.create_pin_constraint(a, {0.0, 0.0}, {0.0, 0.0});
    auto pin_b = world.create_pin_constraint(b, {10.0, 0.0}, {0.0, 0.0});

    b->apply_force({-1000.0, 0.0});

    world.step();

    assert_near(b->position().x, 10.0, 0.5, "Constraint solver holds pin");
}

void test_destroy_constraint() {
    World world;

    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.radius = 0.5;
    def.mass = 1.0;
    def.name = "body";
    auto body = world.create_body(def);

    auto pin = world.create_pin_constraint(body, {0.0, 0.0}, {0.0, 0.0});
    assert_eq(world.solver().constraints().size(), 1, "One constraint");

    world.destroy_constraint(pin);
    assert_eq(world.solver().constraints().size(), 0, "Zero constraints after destroy");
}

void test_kinematic_body() {
    RigidBodyDef def;
    def.type = BodyType::Kinematic;
    def.position = {0.0, 0.0};
    def.velocity = {1.0, 0.0};
    def.linear_damping = 0.0;
    def.angular_damping = 0.0;
    def.name = "kinematic";
    RigidBody body(def);

    body.apply_force({100.0, 100.0});
    body.integrate(1.0);

    // Kinematic bodies should not be affected by forces but still move with velocity
    assert_near(body.velocity().x, 1.0, 0.01, "Kinematic velocity unchanged");
    assert_near(body.position().x, 1.0, 0.01, "Kinematic position moves with velocity");
}

void test_sensor_body() {
    World world;

    RigidBodyDef sensor_def;
    sensor_def.type = BodyType::Dynamic;
    sensor_def.position = {0.0, 0.0};
    sensor_def.radius = 0.5;
    sensor_def.mass = 1.0;
    sensor_def.is_sensor = true;
    sensor_def.name = "sensor";
    auto sensor = world.create_body(sensor_def);

    RigidBodyDef ball_def;
    ball_def.type = BodyType::Dynamic;
    ball_def.position = {0.0, 10.0};
    ball_def.velocity = {0.0, -10.0};
    ball_def.radius = 0.5;
    ball_def.mass = 1.0;
    ball_def.restitution = 0.8;
    ball_def.name = "ball";
    auto ball = world.create_body(ball_def);

    for (int i = 0; i < 60; ++i) {
        world.step();
    }

    assert_true(ball->velocity().y < -5.0, "Sensor does not affect physics");
}

void test_multiple_time_steps() {
    WorldConfig config;
    config.gravity = {0.0, -9.81};

    World world(config);

    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.position = {0.0, 10.0};
    def.velocity = {0.0, 0.0};
    def.mass = 1.0;
    def.radius = 0.5;
    def.linear_damping = 0.0;
    def.angular_damping = 0.0;
    def.name = "ball";
    auto ball = world.create_body(def);

    for (int i = 0; i < 120; ++i) {
        world.step();
    }

    // After 2 seconds with no damping, ball should have fallen ~19.6m
    // With Euler integration and default damping, check it fell significantly
    assert_true(ball->position().y < 5.0, "Long simulation gravity");
}

void test_long_simulation_no_damping() {
    WorldConfig config;
    config.gravity = {0.0, -9.81};

    World world(config);

    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.position = {0.0, 10.0};
    def.velocity = {0.0, 0.0};
    def.mass = 1.0;
    def.radius = 0.5;
    def.linear_damping = 0.0;
    def.angular_damping = 0.0;
    def.name = "ball";
    auto ball = world.create_body(def);

    for (int i = 0; i < 120; ++i) {
        world.step();
    }

    // After 2 seconds with no damping, ball should have fallen ~19.6m
    assert_true(ball->position().y < 5.0, "Long simulation gravity");
}

void test_world_bodies_access() {
    World world;

    RigidBodyDef def;
    def.type = BodyType::Dynamic;
    def.radius = 0.5;
    auto b1 = world.create_body(def);
    auto b2 = world.create_body(def);

    const auto& bodies = world.bodies();
    assert_eq(bodies.size(), 2, "Bodies access count");
    assert_eq(bodies[0]->id(), b1->id(), "Bodies access first");
    assert_eq(bodies[1]->id(), b2->id(), "Bodies access second");
}

void test_weld_constraint() {
    World world;

    RigidBodyDef a_def;
    a_def.type = BodyType::Dynamic;
    a_def.position = {0.0, 0.0};
    a_def.radius = 0.5;
    a_def.mass = 1.0;
    a_def.name = "weld_a";
    auto a = world.create_body(a_def);

    RigidBodyDef b_def;
    b_def.type = BodyType::Dynamic;
    b_def.position = {3.0, 4.0};
    b_def.radius = 0.5;
    b_def.mass = 1.0;
    b_def.name = "weld_b";
    auto b = world.create_body(b_def);

    auto weld = world.create_weld_constraint(a, b, {0.0, 0.0}, {0.0, 0.0});

    a->apply_force({-100.0, -100.0});
    b->apply_force({100.0, 100.0});

    for (int i = 0; i < 10; ++i) {
        world.step();
    }

    double dist_between = (b->position() - a->position()).length();
    assert_true(dist_between < 6.0, "Weld constraint holds");
}

// ============================================================
// Main
// ============================================================

struct TestCase {
    const char* name;
    std::function<void()> func;
};

int main() {
    std::vector<TestCase> tests = {
        // Vec2
        {"Vec2::addition", test_vec2_addition},
        {"Vec2::subtraction", test_vec2_subtraction},
        {"Vec2::scalar_mult", test_vec2_scalar_mult},
        {"Vec2::dot_product", test_vec2_dot_product},
        {"Vec2::cross_product", test_vec2_cross_product},
        {"Vec2::length", test_vec2_length},
        {"Vec2::length_squared", test_vec2_length_squared},
        {"Vec2::normalized", test_vec2_normalized},
        {"Vec2::zero", test_vec2_zero},
        {"Vec2::unit_vectors", test_vec2_unit_vectors},
        // AABB
        {"AABB::center", test_aabb_center},
        {"AABB::size", test_aabb_size},
        {"AABB::contains", test_aabb_contains},
        {"AABB::intersects", test_aabb_intersects},
        {"AABB::merge", test_aabb_merge},
        {"AABB::expanded", test_aabb_expanded},
        {"AABB::is_valid", test_aabb_is_valid},
        {"AABB::area", test_aabb_area},
        {"AABB::half_size", test_aabb_half_size},
        // Collision
        {"Collision::aabb_vs_aabb no collision", test_aabb_vs_aabb_no_collision},
        {"Collision::aabb_vs_aabb collision", test_aabb_vs_aabb_collision},
        {"Collision::circle vs circle no collision", test_circle_vs_circle_no_collision},
        {"Collision::circle vs circle collision", test_circle_vs_circle_collision},
        {"Collision::circle vs circle touching", test_circle_vs_circle_touching},
        {"Collision::aabb vs circle no collision", test_aabb_vs_circle_no_collision},
        {"Collision::aabb vs circle collision", test_aabb_vs_circle_collision},
        {"Collision::aabb vs circle inside", test_aabb_vs_circle_inside},
        {"Collision::circle normal direction", test_circle_normal_direction},
        // RigidBody
        {"RigidBody::create dynamic", test_create_dynamic_body},
        {"RigidBody::create static", test_create_static_body},
        {"RigidBody::create kinematic", test_create_kinematic_body},
        {"RigidBody::apply_force", test_apply_force},
        {"RigidBody::apply_impulse", test_apply_impulse},
        {"RigidBody::integrate", test_integrate},
        {"RigidBody::integrate gravity", test_integrate_with_gravity},
        {"RigidBody::static ignores force", test_static_ignores_force},
        {"RigidBody::setters", test_setters},
        {"RigidBody::clear_forces", test_clear_forces},
        {"RigidBody::velocity_at_point", test_velocity_at_point},
        {"RigidBody::compute_aabb", test_compute_aabb},
        {"RigidBody::mass_change", test_mass_change},
        {"RigidBody::name", test_body_name},
        // World
        {"World::create", test_create_world},
        {"World::create/destroy body", test_create_and_destroy_body},
        {"World::step gravity", test_step_with_gravity},
        {"World::step multiple bodies", test_step_with_multiple_bodies},
        {"World::static stays put", test_static_body_does_not_move},
        {"World::collision callback", test_collision_callback},
        {"World::clear", test_clear},
        {"World::set_config", test_set_config},
        {"World::custom timestep", test_custom_time_step},
        {"World::damping", test_damping},
        {"World::restitution", test_restitution},
        {"World::body id uniqueness", test_body_id_uniqueness},
        {"World::user data", test_user_data},
        // Constraints
        {"Constraint::pin", test_pin_constraint},
        {"Constraint::distance", test_distance_constraint},
        {"Constraint::hinge", test_hinge_constraint},
        {"Constraint::solver", test_constraint_solver},
        {"Constraint::destroy", test_destroy_constraint},
        {"Constraint::kinematic", test_kinematic_body},
        {"Constraint::sensor", test_sensor_body},
        {"Constraint::multiple steps", test_multiple_time_steps},
        {"Constraint::long sim no damping", test_long_simulation_no_damping},
        {"Constraint::bodies access", test_world_bodies_access},
        {"Constraint::weld", test_weld_constraint},
    };

    std::cout << "Running " << tests.size() << " test cases..." << std::endl;
    std::cout << "========================================" << std::endl;

    for (const auto& test : tests) {
        std::cout << "  " << test.name << "... ";
        test.func();
    }

    std::cout << "========================================" << std::endl;
    std::cout << "Results: " << tests_run << " assertions" << std::endl;
    std::cout << "  Passed: " << tests_passed << std::endl;
    std::cout << "  Failed: " << tests_failed << std::endl;

    if (tests_failed > 0) {
        std::cerr << "FAILED: " << tests_failed << " assertion(s) failed!" << std::endl;
        return 1;
    }

    std::cout << "ALL TESTS PASSED!" << std::endl;
    return 0;
}
