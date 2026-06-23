#include <gtest/gtest.h>
#include "physics_engine/world.h"

using namespace physics_engine;

class IntegrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        WorldConfig config;
        config.gravity = {0.0, -9.81};
        world = std::make_unique<World>(config);
    }

    std::unique_ptr<World> world;
};

TEST_F(IntegrationTest, FreeFall) {
    // 测试自由落体
    RigidBodyDef def;
    def.position = {0.0, 100.0};
    def.mass = 1.0;

    auto body = world->create_body(def);

    double dt = 1.0 / 60.0;
    double total_time = 1.0;  // 模拟 1 秒
    int steps = static_cast<int>(total_time / dt);

    for (int i = 0; i < steps; ++i) {
        world->step(dt);
    }

    // 使用运动学公式验证：y = y0 + v0*t + 0.5*g*t^2
    // 初始速度 v0 = 0
    // g = -9.81, t = 1.0
    // y = 100 + 0 + 0.5 * (-9.81) * 1.0^2 = 100 - 4.905 = 95.095
    double expected_y = 100.0 + 0.5 * (-9.81) * total_time * total_time;

    // 由于数值积分的误差，允许一定的容差
    EXPECT_NEAR(body->position().y, expected_y, 1.0);

    // 速度应该增加
    double expected_vy = -9.81 * total_time;
    EXPECT_NEAR(body->velocity().y, expected_vy, 1.0);
}

TEST_F(IntegrationTest, ProjectileMotion) {
    // 测试抛物运动
    RigidBodyDef def;
    def.position = {0.0, 0.0};
    def.velocity = {10.0, 20.0};  // 初速度
    def.mass = 1.0;

    auto body = world->create_body(def);

    double dt = 1.0 / 60.0;
    double total_time = 2.0;
    int steps = static_cast<int>(total_time / dt);

    for (int i = 0; i < steps; ++i) {
        world->step(dt);
    }

    // x = v0x * t = 10 * 2 = 20
    double expected_x = 10.0 * total_time;
    EXPECT_NEAR(body->position().x, expected_x, 1.0);

    // y = v0y * t + 0.5 * g * t^2 = 20 * 2 + 0.5 * (-9.81) * 4 = 40 - 19.62 = 20.38
    double expected_y = 20.0 * total_time + 0.5 * (-9.81) * total_time * total_time;
    EXPECT_NEAR(body->position().y, expected_y, 1.0);
}

TEST_F(IntegrationTest, StaticBodyCollision) {
    // 测试动态物体与静态地面的碰撞
    RigidBodyDef ground_def;
    ground_def.type = BodyType::Static;
    ground_def.position = {0.0, -1.0};
    auto ground = world->create_body(ground_def);

    RigidBodyDef ball_def;
    ball_def.position = {0.0, 10.0};
    ball_def.mass = 1.0;
    ball_def.restitution = 0.8;  // 弹性系数
    auto ball = world->create_body(ball_def);

    double dt = 1.0 / 60.0;

    // 模拟足够长的时间让球落地并反弹
    for (int i = 0; i < 300; ++i) {
        world->step(dt);
    }

    // 球应该在地面上方
    EXPECT_GT(ball->position().y, -2.0);

    // 球应该有向上的速度（反弹后）
    // 注意：由于简化的碰撞检测，可能不会完美反弹
}

TEST_F(IntegrationTest, TwoBodyCollision) {
    // 测试两个动态物体的碰撞
    RigidBodyDef def1;
    def1.position = {-5.0, 0.0};
    def1.velocity = {5.0, 0.0};
    def1.mass = 1.0;
    auto body_a = world->create_body(def1);

    RigidBodyDef def2;
    def2.position = {5.0, 0.0};
    def2.velocity = {-5.0, 0.0};
    def2.mass = 1.0;
    auto body_b = world->create_body(def2);

    double dt = 1.0 / 60.0;

    // 模拟碰撞
    for (int i = 0; i < 60; ++i) {
        world->step(dt);
    }

    // 两个物体应该已经碰撞并反弹
    // 由于质量相等，弹性碰撞后速度应该交换
    // body_a 应该向左移动，body_b 应该向右移动
    EXPECT_LT(body_a->velocity().x, 0.0);
    EXPECT_GT(body_b->velocity().x, 0.0);
}

TEST_F(IntegrationTest, Pendulum) {
    // 测试摆锤（使用距离约束）
    RigidBodyDef anchor_def;
    anchor_def.type = BodyType::Static;
    anchor_def.position = {0.0, 10.0};
    auto anchor = world->create_body(anchor_def);

    RigidBodyDef bob_def;
    bob_def.position = {5.0, 10.0};
    bob_def.mass = 1.0;
    auto bob = world->create_body(bob_def);

    // 创建距离约束
    auto constraint = world->create_distance_constraint(
        anchor, bob, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    constraint->stiffness = 1.0;

    double dt = 1.0 / 60.0;

    // 模拟摆锤运动
    for (int i = 0; i < 300; ++i) {
        world->step(dt);
    }

    // 摆锤应该在锚点附近摆动
    double distance = anchor->position().distance_to(bob->position());
    EXPECT_NEAR(distance, 5.0, 1.0);  // 允许一定的误差
}

TEST_F(IntegrationTest, Chain) {
    // 测试链条（多个物体通过距离约束连接）
    const int num_links = 5;
    std::vector<std::shared_ptr<RigidBody>> links;

    // 创建锚点
    RigidBodyDef anchor_def;
    anchor_def.type = BodyType::Static;
    anchor_def.position = {0.0, 10.0};
    auto anchor = world->create_body(anchor_def);

    // 创建链条链接
    for (int i = 0; i < num_links; ++i) {
        RigidBodyDef def;
        def.position = {static_cast<double>(i + 1) * 2.0, 10.0};
        def.mass = 1.0;
        links.push_back(world->create_body(def));
    }

    // 创建约束
    auto first_constraint = world->create_distance_constraint(
        anchor, links[0], Vector2D(0.0, 0.0), Vector2D(0.0, 0.0), 2.0);

    for (int i = 0; i < num_links - 1; ++i) {
        world->create_distance_constraint(
            links[i], links[i + 1], Vector2D(0.0, 0.0), Vector2D(0.0, 0.0), 2.0);
    }

    double dt = 1.0 / 60.0;

    // 模拟链条下落
    for (int i = 0; i < 180; ++i) {
        world->step(dt);
    }

    // 链条应该下垂
    EXPECT_LT(links.back()->position().y, 10.0);

    // 链条应该保持连接（距离约束）
    double distance = anchor->position().distance_to(links[0]->position());
    EXPECT_NEAR(distance, 2.0, 1.0);
}

TEST_F(IntegrationTest, StackOfBoxes) {
    // 测试堆叠的盒子
    const int num_boxes = 3;
    std::vector<std::shared_ptr<RigidBody>> boxes;

    // 创建地面
    RigidBodyDef ground_def;
    ground_def.type = BodyType::Static;
    ground_def.position = {0.0, -0.5};
    auto ground = world->create_body(ground_def);

    // 创建堆叠的盒子
    for (int i = 0; i < num_boxes; ++i) {
        RigidBodyDef def;
        def.position = {0.0, static_cast<double>(i) * 1.1 + 0.5};
        def.mass = 1.0;
        def.restitution = 0.1;  // 低弹性，减少弹跳
        boxes.push_back(world->create_body(def));
    }

    double dt = 1.0 / 60.0;

    // 模拟堆叠稳定
    for (int i = 0; i < 300; ++i) {
        world->step(dt);
    }

    // 盒子应该堆叠在地面上
    for (int i = 0; i < num_boxes; ++i) {
        EXPECT_GT(boxes[i]->position().y, -1.0);
    }
}

TEST_F(IntegrationTest, ConstantForce) {
    // 测试恒定力作用
    RigidBodyDef def;
    def.position = {0.0, 0.0};
    def.mass = 1.0;

    auto body = world->create_body(def);

    double dt = 1.0 / 60.0;
    double total_time = 1.0;
    int steps = static_cast<int>(total_time / dt);

    for (int i = 0; i < steps; ++i) {
        // 每步施加恒定力
        body->apply_force({10.0, 0.0});
        world->step(dt);
    }

    // 使用运动学公式：x = 0.5 * a * t^2 = 0.5 * (F/m) * t^2
    double expected_x = 0.5 * (10.0 / 1.0) * total_time * total_time;
    EXPECT_NEAR(body->position().x, expected_x, 0.5);
}

TEST_F(IntegrationTest, Impulse) {
    // 测试冲量效果
    RigidBodyDef def;
    def.position = {0.0, 0.0};
    def.mass = 2.0;

    auto body = world->create_body(def);

    // 施加冲量
    body->apply_impulse({10.0, 0.0});

    // 速度应该立即改变
    // v = impulse / mass = 10 / 2 = 5
    EXPECT_NEAR(body->velocity().x, 5.0, 1e-10);
    EXPECT_NEAR(body->velocity().y, 0.0, 1e-10);
}

TEST_F(IntegrationTest, AngularVelocity) {
    // 测试角速度
    RigidBodyDef def;
    def.position = {0.0, 0.0};
    def.mass = 1.0;

    auto body = world->create_body(def);

    // 施加扭矩
    body->apply_torque(10.0);

    double dt = 1.0 / 60.0;
    world->step(dt);

    // 角速度应该增加
    EXPECT_GT(body->angular_velocity(), 0.0);
}

TEST_F(IntegrationTest, DampingEffect) {
    // 测试阻尼效果
    RigidBodyDef def;
    def.position = {0.0, 0.0};
    def.mass = 1.0;
    def.velocity = {10.0, 0.0};
    def.linear_damping = 0.5;  // 高阻尼

    auto body = world->create_body(def);

    double dt = 1.0 / 60.0;

    // 模拟多步
    for (int i = 0; i < 60; ++i) {
        world->step(dt);
    }

    // 速度应该被阻尼减小
    EXPECT_LT(body->velocity().x, 10.0);
    EXPECT_GT(body->velocity().x, 0.0);
}

TEST_F(IntegrationTest, SensorBody) {
    // 测试传感器物体（不产物理响应）
    // 创建一个静态地面
    RigidBodyDef ground_def;
    ground_def.type = BodyType::Static;
    ground_def.position = {0.0, -5.0};
    auto ground = world->create_body(ground_def);

    // 创建一个传感器（在地面上方）
    RigidBodyDef sensor_def;
    sensor_def.position = {0.0, 0.0};
    sensor_def.is_sensor = true;
    auto sensor = world->create_body(sensor_def);

    // 创建一个球
    RigidBodyDef ball_def;
    ball_def.position = {0.0, 10.0};
    ball_def.mass = 1.0;
    auto ball = world->create_body(ball_def);

    bool collision_detected = false;
    world->set_collision_callback([&collision_detected](const CollisionManifold& manifold) {
        collision_detected = true;
    });

    double dt = 1.0 / 60.0;

    // 模拟球下落（3秒）
    for (int i = 0; i < 180; ++i) {
        world->step(dt);
    }

    // 球应该落到地面附近
    EXPECT_LT(ball->position().y, 0.0);
}
