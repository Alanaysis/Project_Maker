#include <gtest/gtest.h>
#include "physics_engine/rigid_body.h"

using namespace physics_engine;

class RigidBodyTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 每个测试前重置 ID
    }

    void TearDown() override {
        // 每个测试后清理
    }
};

TEST_F(RigidBodyTest, DefaultConstruction) {
    RigidBodyDef def;
    def.position = {5.0, 10.0};
    def.mass = 2.0;

    RigidBody body(def);

    EXPECT_DOUBLE_EQ(body.position().x, 5.0);
    EXPECT_DOUBLE_EQ(body.position().y, 10.0);
    EXPECT_DOUBLE_EQ(body.mass(), 2.0);
    EXPECT_DOUBLE_EQ(body.inv_mass(), 0.5);
    EXPECT_EQ(body.type(), BodyType::Dynamic);
    EXPECT_DOUBLE_EQ(body.rotation(), 0.0);
    EXPECT_DOUBLE_EQ(body.velocity().x, 0.0);
    EXPECT_DOUBLE_EQ(body.velocity().y, 0.0);
    EXPECT_DOUBLE_EQ(body.angular_velocity(), 0.0);
    EXPECT_DOUBLE_EQ(body.restitution(), 0.5);
    EXPECT_DOUBLE_EQ(body.friction(), 0.3);
    EXPECT_FALSE(body.is_sensor());
    EXPECT_TRUE(body.is_dynamic());
    EXPECT_FALSE(body.is_static());
    EXPECT_FALSE(body.is_kinematic());
}

TEST_F(RigidBodyTest, StaticBody) {
    RigidBodyDef def;
    def.type = BodyType::Static;
    def.position = {0.0, 0.0};
    def.mass = 100.0;  // 静态物体的质量应该被忽略

    RigidBody body(def);

    EXPECT_TRUE(body.is_static());
    EXPECT_FALSE(body.is_dynamic());
    EXPECT_DOUBLE_EQ(body.inv_mass(), 0.0);
}

TEST_F(RigidBodyTest, KinematicBody) {
    RigidBodyDef def;
    def.type = BodyType::Kinematic;
    def.position = {0.0, 0.0};
    def.velocity = {1.0, 2.0};

    RigidBody body(def);

    EXPECT_TRUE(body.is_kinematic());
    EXPECT_FALSE(body.is_static());
    EXPECT_FALSE(body.is_dynamic());
}

TEST_F(RigidBodyTest, ApplyForce) {
    RigidBodyDef def;
    def.mass = 2.0;

    RigidBody body(def);

    body.apply_force({10.0, 20.0});
    EXPECT_DOUBLE_EQ(body.force().x, 10.0);
    EXPECT_DOUBLE_EQ(body.force().y, 20.0);

    body.apply_force({5.0, 5.0});
    EXPECT_DOUBLE_EQ(body.force().x, 15.0);
    EXPECT_DOUBLE_EQ(body.force().y, 25.0);
}

TEST_F(RigidBodyTest, ApplyForceAtPoint) {
    RigidBodyDef def;
    def.mass = 1.0;
    def.position = {0.0, 0.0};

    RigidBody body(def);

    // 在 (1, 0) 施加向上的力，应该产生正扭矩
    body.apply_force_at_point({0.0, 10.0}, {1.0, 0.0});

    EXPECT_DOUBLE_EQ(body.force().x, 0.0);
    EXPECT_DOUBLE_EQ(body.force().y, 10.0);
    EXPECT_GT(body.torque(), 0.0);
}

TEST_F(RigidBodyTest, ApplyImpulse) {
    RigidBodyDef def;
    def.mass = 2.0;

    RigidBody body(def);

    body.apply_impulse({10.0, 20.0});
    EXPECT_DOUBLE_EQ(body.velocity().x, 5.0);   // 10 / 2
    EXPECT_DOUBLE_EQ(body.velocity().y, 10.0);  // 20 / 2
}

TEST_F(RigidBodyTest, ApplyImpulseAtPoint) {
    RigidBodyDef def;
    def.mass = 1.0;
    def.position = {0.0, 0.0};

    RigidBody body(def);

    // 在 (1, 0) 施加向上的冲量，应该产生正角速度
    body.apply_impulse_at_point({0.0, 10.0}, {1.0, 0.0});

    EXPECT_DOUBLE_EQ(body.velocity().x, 0.0);
    EXPECT_DOUBLE_EQ(body.velocity().y, 10.0);
    EXPECT_GT(body.angular_velocity(), 0.0);
}

TEST_F(RigidBodyTest, ApplyTorque) {
    RigidBodyDef def;
    def.mass = 1.0;

    RigidBody body(def);

    body.apply_torque(5.0);
    EXPECT_DOUBLE_EQ(body.torque(), 5.0);

    body.apply_torque(3.0);
    EXPECT_DOUBLE_EQ(body.torque(), 8.0);
}

TEST_F(RigidBodyTest, ClearForces) {
    RigidBodyDef def;
    def.mass = 1.0;

    RigidBody body(def);

    body.apply_force({10.0, 20.0});
    body.apply_torque(5.0);

    EXPECT_GT(body.force().x, 0.0);
    EXPECT_GT(body.torque(), 0.0);

    body.clear_forces();

    EXPECT_DOUBLE_EQ(body.force().x, 0.0);
    EXPECT_DOUBLE_EQ(body.force().y, 0.0);
    EXPECT_DOUBLE_EQ(body.torque(), 0.0);
}

TEST_F(RigidBodyTest, Integration) {
    RigidBodyDef def;
    def.mass = 1.0;
    def.position = {0.0, 0.0};
    def.velocity = {1.0, 0.0};

    RigidBody body(def);

    double dt = 0.1;
    body.integrate(dt);

    // 位置应该更新（考虑阻尼）
    EXPECT_NEAR(body.position().x, 0.1, 1e-3);
    EXPECT_NEAR(body.position().y, 0.0, 1e-10);

    // 速度应该保持（考虑阻尼）
    EXPECT_NEAR(body.velocity().x, 1.0, 1e-2);
    EXPECT_NEAR(body.velocity().y, 0.0, 1e-10);
}

TEST_F(RigidBodyTest, IntegrationWithForce) {
    RigidBodyDef def;
    def.mass = 1.0;
    def.position = {0.0, 0.0};
    def.velocity = {0.0, 0.0};

    RigidBody body(def);

    // 施加力
    body.apply_force({10.0, 0.0});

    double dt = 0.1;
    body.integrate(dt);

    // 速度应该增加（F * dt / m = 10 * 0.1 / 1 = 1.0，考虑阻尼）
    EXPECT_NEAR(body.velocity().x, 1.0, 1e-2);

    // 位置应该更新
    EXPECT_NEAR(body.position().x, 0.1, 1e-2);
}

TEST_F(RigidBodyTest, IntegrationStaticBody) {
    RigidBodyDef def;
    def.type = BodyType::Static;
    def.position = {5.0, 5.0};

    RigidBody body(def);

    body.apply_force({100.0, 100.0});
    body.integrate(0.1);

    // 静态物体不应该移动
    EXPECT_DOUBLE_EQ(body.position().x, 5.0);
    EXPECT_DOUBLE_EQ(body.position().y, 5.0);
}

TEST_F(RigidBodyTest, Damping) {
    RigidBodyDef def;
    def.mass = 1.0;
    def.velocity = {10.0, 10.0};
    def.linear_damping = 0.5;

    RigidBody body(def);

    body.integrate(1.0);

    // 速度应该被阻尼减小
    EXPECT_LT(body.velocity().x, 10.0);
    EXPECT_LT(body.velocity().y, 10.0);
}

TEST_F(RigidBodyTest, SetMass) {
    RigidBodyDef def;
    def.mass = 2.0;

    RigidBody body(def);

    EXPECT_DOUBLE_EQ(body.mass(), 2.0);
    EXPECT_DOUBLE_EQ(body.inv_mass(), 0.5);

    body.set_mass(4.0);
    EXPECT_DOUBLE_EQ(body.mass(), 4.0);
    EXPECT_DOUBLE_EQ(body.inv_mass(), 0.25);
}

TEST_F(RigidBodyTest, VelocityAtPoint) {
    RigidBodyDef def;
    def.mass = 1.0;
    def.position = {0.0, 0.0};
    def.velocity = {1.0, 0.0};
    def.angular_velocity = 1.0;

    RigidBody body(def);

    // 在 (0, 1) 的速度应该是 (1, 0) + (-1, 0) * 1 = (0, 0)
    Vector2D vel = body.velocity_at_point({0.0, 1.0});
    EXPECT_NEAR(vel.x, 0.0, 1e-10);
    EXPECT_NEAR(vel.y, 0.0, 1e-10);

    // 在 (1, 0) 的速度应该是 (1, 0) + (0, 1) * 1 = (1, 1)
    Vector2D vel2 = body.velocity_at_point({1.0, 0.0});
    EXPECT_NEAR(vel2.x, 1.0, 1e-10);
    EXPECT_NEAR(vel2.y, 1.0, 1e-10);
}

TEST_F(RigidBodyTest, ComputeAABB) {
    RigidBodyDef def;
    def.position = {5.0, 5.0};

    RigidBody body(def);

    AABB aabb = body.compute_aabb();
    EXPECT_DOUBLE_EQ(aabb.min.x, 4.5);
    EXPECT_DOUBLE_EQ(aabb.min.y, 4.5);
    EXPECT_DOUBLE_EQ(aabb.max.x, 5.5);
    EXPECT_DOUBLE_EQ(aabb.max.y, 5.5);
}

TEST_F(RigidBodyTest, UniqueId) {
    RigidBodyDef def1;
    RigidBodyDef def2;

    RigidBody body1(def1);
    RigidBody body2(def2);

    EXPECT_NE(body1.id(), body2.id());
}

TEST_F(RigidBodyTest, UserData) {
    RigidBodyDef def;
    int data = 42;
    def.user_data = &data;

    RigidBody body(def);

    EXPECT_EQ(body.user_data(), &data);
    EXPECT_EQ(*static_cast<int*>(body.user_data()), 42);
}
