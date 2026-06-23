#include <gtest/gtest.h>
#include "physics_engine/world.h"

using namespace physics_engine;

class WorldTest : public ::testing::Test {
protected:
    void SetUp() override {
        WorldConfig config;
        config.gravity = {0.0, -10.0};
        world = std::make_unique<World>(config);
    }

    std::unique_ptr<World> world;
};

TEST_F(WorldTest, CreateBody) {
    RigidBodyDef def;
    def.position = {5.0, 10.0};
    def.mass = 2.0;

    auto body = world->create_body(def);

    EXPECT_EQ(world->body_count(), 1);
    EXPECT_DOUBLE_EQ(body->position().x, 5.0);
    EXPECT_DOUBLE_EQ(body->position().y, 10.0);
    EXPECT_DOUBLE_EQ(body->mass(), 2.0);
}

TEST_F(WorldTest, DestroyBody) {
    RigidBodyDef def;
    auto body = world->create_body(def);

    EXPECT_EQ(world->body_count(), 1);

    world->destroy_body(body);

    EXPECT_EQ(world->body_count(), 0);
}

TEST_F(WorldTest, CreateMultipleBodies) {
    RigidBodyDef def1;
    def1.position = {0.0, 0.0};

    RigidBodyDef def2;
    def2.position = {10.0, 0.0};

    RigidBodyDef def3;
    def3.position = {20.0, 0.0};

    world->create_body(def1);
    world->create_body(def2);
    world->create_body(def3);

    EXPECT_EQ(world->body_count(), 3);
}

TEST_F(WorldTest, StepSimulation) {
    RigidBodyDef def;
    def.position = {0.0, 10.0};
    def.mass = 1.0;

    auto body = world->create_body(def);

    // 模拟一步
    world->step(1.0 / 60.0);

    // 物体应该下落（重力）
    EXPECT_LT(body->position().y, 10.0);
    EXPECT_LT(body->velocity().y, 0.0);
}

TEST_F(WorldTest, GravityEffect) {
    RigidBodyDef def;
    def.position = {0.0, 100.0};
    def.mass = 1.0;
    def.linear_damping = 0.0;  // 禁用阻尼

    auto body = world->create_body(def);

    // 模拟多步（3秒）
    for (int i = 0; i < 180; ++i) {
        world->step(1.0 / 60.0);
    }

    // 物体应该明显下落
    // y = 100 + 0.5 * (-10) * 3^2 = 100 - 45 = 55
    EXPECT_LT(body->position().y, 60.0);
}

TEST_F(WorldTest, StaticBodyNotAffectedByGravity) {
    RigidBodyDef def;
    def.type = BodyType::Static;
    def.position = {0.0, 50.0};

    auto body = world->create_body(def);

    world->step(1.0 / 60.0);

    // 静态物体不应该移动
    EXPECT_NEAR(body->position().x, 0.0, 1e-10);
    EXPECT_NEAR(body->position().y, 50.0, 1e-10);
}

TEST_F(WorldTest, KinematicBodyNotAffectedByGravity) {
    RigidBodyDef def;
    def.type = BodyType::Kinematic;
    def.position = {0.0, 50.0};

    auto body = world->create_body(def);

    world->step(1.0 / 60.0);

    // 运动学物体不应该受重力影响
    EXPECT_NEAR(body->position().y, 50.0, 1e-10);
}

TEST_F(WorldTest, CreateDistanceConstraint) {
    RigidBodyDef def1;
    def1.position = {0.0, 0.0};
    auto body_a = world->create_body(def1);

    RigidBodyDef def2;
    def2.position = {5.0, 0.0};
    auto body_b = world->create_body(def2);

    auto constraint = world->create_distance_constraint(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    EXPECT_NE(constraint, nullptr);
    EXPECT_EQ(constraint->type(), ConstraintType::Distance);
}

TEST_F(WorldTest, CreatePinConstraint) {
    RigidBodyDef def;
    def.position = {0.0, 0.0};
    auto body = world->create_body(def);

    auto constraint = world->create_pin_constraint(
        body, Vector2D(5.0, 5.0), Vector2D(0.0, 0.0));

    EXPECT_NE(constraint, nullptr);
    EXPECT_EQ(constraint->type(), ConstraintType::Pin);
}

TEST_F(WorldTest, CreateHingeConstraint) {
    RigidBodyDef def1;
    def1.position = {0.0, 0.0};
    auto body_a = world->create_body(def1);

    RigidBodyDef def2;
    def2.position = {5.0, 0.0};
    auto body_b = world->create_body(def2);

    auto constraint = world->create_hinge_constraint(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    EXPECT_NE(constraint, nullptr);
    EXPECT_EQ(constraint->type(), ConstraintType::Hinge);
}

TEST_F(WorldTest, CreateWeldConstraint) {
    RigidBodyDef def1;
    def1.position = {0.0, 0.0};
    auto body_a = world->create_body(def1);

    RigidBodyDef def2;
    def2.position = {5.0, 0.0};
    auto body_b = world->create_body(def2);

    auto constraint = world->create_weld_constraint(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    EXPECT_NE(constraint, nullptr);
    EXPECT_EQ(constraint->type(), ConstraintType::Weld);
}

TEST_F(WorldTest, CollisionDetection) {
    RigidBodyDef def1;
    def1.position = {0.0, 0.0};
    auto body_a = world->create_body(def1);

    RigidBodyDef def2;
    def2.position = {0.5, 0.0};  // 重叠
    auto body_b = world->create_body(def2);

    bool collision_detected = false;
    world->set_collision_callback([&collision_detected](const CollisionManifold& manifold) {
        collision_detected = true;
    });

    world->step(1.0 / 60.0);

    EXPECT_TRUE(collision_detected);
}

TEST_F(WorldTest, NoCollisionWhenSeparated) {
    RigidBodyDef def1;
    def1.position = {0.0, 0.0};
    auto body_a = world->create_body(def1);

    RigidBodyDef def2;
    def2.position = {10.0, 0.0};  // 远离
    auto body_b = world->create_body(def2);

    bool collision_detected = false;
    world->set_collision_callback([&collision_detected](const CollisionManifold& manifold) {
        collision_detected = true;
    });

    world->step(1.0 / 60.0);

    EXPECT_FALSE(collision_detected);
}

TEST_F(WorldTest, Clear) {
    RigidBodyDef def;
    world->create_body(def);
    world->create_body(def);

    EXPECT_EQ(world->body_count(), 2);

    world->clear();

    EXPECT_EQ(world->body_count(), 0);
}

TEST_F(WorldTest, GetConfig) {
    WorldConfig config = world->config();

    EXPECT_DOUBLE_EQ(config.gravity.x, 0.0);
    EXPECT_DOUBLE_EQ(config.gravity.y, -10.0);
    EXPECT_EQ(config.velocity_iterations, 8);
    EXPECT_EQ(config.position_iterations, 3);
}

TEST_F(WorldTest, SetConfig) {
    WorldConfig new_config;
    new_config.gravity = {0.0, -20.0};
    new_config.velocity_iterations = 16;

    world->set_config(new_config);

    WorldConfig config = world->config();
    EXPECT_DOUBLE_EQ(config.gravity.y, -20.0);
    EXPECT_EQ(config.velocity_iterations, 16);
}
