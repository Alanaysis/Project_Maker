#include <gtest/gtest.h>
#include "physics_engine/constraint.h"

using namespace physics_engine;

class ConstraintTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 创建测试用的刚体
        RigidBodyDef def1;
        def1.mass = 1.0;
        def1.position = {0.0, 0.0};
        body_a = std::make_shared<RigidBody>(def1);

        RigidBodyDef def2;
        def2.mass = 1.0;
        def2.position = {5.0, 0.0};
        body_b = std::make_shared<RigidBody>(def2);

        RigidBodyDef static_def;
        static_def.type = BodyType::Static;
        static_def.position = {0.0, 0.0};
        static_body = std::make_shared<RigidBody>(static_def);
    }

    std::shared_ptr<RigidBody> body_a;
    std::shared_ptr<RigidBody> body_b;
    std::shared_ptr<RigidBody> static_body;
};

TEST_F(ConstraintTest, DistanceConstraintInitialize) {
    auto constraint = std::make_shared<DistanceConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    constraint->initialize();

    // 初始距离应该是 5.0
    EXPECT_NEAR(constraint->target_distance(), 5.0, 1e-10);
}

TEST_F(ConstraintTest, DistanceConstraintCustomDistance) {
    auto constraint = std::make_shared<DistanceConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0), 10.0);

    constraint->initialize();

    // 应该使用自定义距离
    EXPECT_NEAR(constraint->target_distance(), 10.0, 1e-10);
}

TEST_F(ConstraintTest, DistanceConstraintSolve) {
    auto constraint = std::make_shared<DistanceConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    constraint->initialize();
    constraint->stiffness = 1.0;

    // 移动 body_b 使距离变为 10.0
    body_b->set_position({10.0, 0.0});

    // 多次求解约束
    for (int i = 0; i < 10; ++i) {
        constraint->solve(1.0 / 60.0);
    }

    // 物体应该被拉近
    EXPECT_LT(body_b->position().x, 10.0);
    EXPECT_GT(body_a->position().x, 0.0);
}

TEST_F(ConstraintTest, DistanceConstraintStaticBody) {
    auto constraint = std::make_shared<DistanceConstraint>(
        static_body, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    constraint->initialize();

    body_b->set_position({10.0, 0.0});

    // 多次求解约束
    for (int i = 0; i < 10; ++i) {
        constraint->solve(1.0 / 60.0);
    }

    // 静态物体不应该移动
    EXPECT_NEAR(static_body->position().x, 0.0, 1e-10);
    // 动态物体应该被拉近
    EXPECT_LT(body_b->position().x, 10.0);
}

TEST_F(ConstraintTest, DistanceConstraintType) {
    auto constraint = std::make_shared<DistanceConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    EXPECT_EQ(constraint->type(), ConstraintType::Distance);
}

TEST_F(ConstraintTest, DistanceConstraintDisabled) {
    auto constraint = std::make_shared<DistanceConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    constraint->initialize();
    constraint->enabled = false;

    body_b->set_position({10.0, 0.0});
    Vector2D pos_before = body_b->position();

    constraint->solve(1.0 / 60.0);

    // 禁用的约束不应该改变位置
    EXPECT_NEAR(body_b->position().x, pos_before.x, 1e-10);
}

TEST_F(ConstraintTest, PinConstraintInitialize) {
    auto constraint = std::make_shared<PinConstraint>(
        body_a, Vector2D(5.0, 5.0), Vector2D(0.0, 0.0));

    constraint->initialize();

    // 检查初始偏移
    EXPECT_NEAR(constraint->world_point().x, 5.0, 1e-10);
    EXPECT_NEAR(constraint->world_point().y, 5.0, 1e-10);
}

TEST_F(ConstraintTest, PinConstraintSolve) {
    body_a->set_position({0.0, 0.0});
    auto constraint = std::make_shared<PinConstraint>(
        body_a, Vector2D(5.0, 5.0), Vector2D(0.0, 0.0));

    constraint->initialize();

    // 移动物体
    body_a->set_position({2.0, 2.0});

    // 多次求解约束
    for (int i = 0; i < 10; ++i) {
        constraint->solve(1.0 / 60.0);
    }

    // 物体应该被拉向固定点
    EXPECT_GT(body_a->position().x, 2.0);
    EXPECT_GT(body_a->position().y, 2.0);
}

TEST_F(ConstraintTest, PinConstraintType) {
    auto constraint = std::make_shared<PinConstraint>(
        body_a, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    EXPECT_EQ(constraint->type(), ConstraintType::Pin);
}

TEST_F(ConstraintTest, HingeConstraintInitialize) {
    body_a->set_position({0.0, 0.0});
    body_b->set_position({5.0, 0.0});

    auto constraint = std::make_shared<HingeConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    constraint->initialize();

    // 不应该抛出异常
    EXPECT_EQ(constraint->type(), ConstraintType::Hinge);
}

TEST_F(ConstraintTest, HingeConstraintSolve) {
    body_a->set_position({0.0, 0.0});
    body_b->set_position({10.0, 0.0});

    auto constraint = std::make_shared<HingeConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    constraint->initialize();
    constraint->stiffness = 1.0;

    // 多次求解约束
    for (int i = 0; i < 10; ++i) {
        constraint->solve(1.0 / 60.0);
    }

    // 物体应该被拉近
    EXPECT_LT(body_b->position().x, 10.0);
    EXPECT_GT(body_a->position().x, 0.0);
}

TEST_F(ConstraintTest, WeldConstraintInitialize) {
    body_a->set_position({0.0, 0.0});
    body_b->set_position({5.0, 0.0});

    auto constraint = std::make_shared<WeldConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    constraint->initialize();

    EXPECT_EQ(constraint->type(), ConstraintType::Weld);
}

TEST_F(ConstraintTest, WeldConstraintSolve) {
    body_a->set_position({0.0, 0.0});
    body_b->set_position({10.0, 0.0});

    auto constraint = std::make_shared<WeldConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    constraint->initialize();
    constraint->stiffness = 1.0;

    // 多次求解约束
    for (int i = 0; i < 10; ++i) {
        constraint->solve(1.0 / 60.0);
    }

    // 物体应该被拉近
    EXPECT_LT(body_b->position().x, 10.0);
    EXPECT_GT(body_a->position().x, 0.0);
}

TEST_F(ConstraintTest, ConstraintSolverAddAndRemove) {
    ConstraintSolver solver;

    auto constraint = std::make_shared<DistanceConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    EXPECT_EQ(solver.constraint_count(), 0);

    solver.add_constraint(constraint);
    EXPECT_EQ(solver.constraint_count(), 1);

    solver.remove_constraint(constraint);
    EXPECT_EQ(solver.constraint_count(), 0);
}

TEST_F(ConstraintTest, ConstraintSolverClear) {
    ConstraintSolver solver;

    auto constraint1 = std::make_shared<DistanceConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    auto constraint2 = std::make_shared<PinConstraint>(
        body_a, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0));

    solver.add_constraint(constraint1);
    solver.add_constraint(constraint2);
    EXPECT_EQ(solver.constraint_count(), 2);

    solver.clear();
    EXPECT_EQ(solver.constraint_count(), 0);
}

TEST_F(ConstraintTest, ConstraintSolverSolve) {
    ConstraintSolver solver;

    body_a->set_position({0.0, 0.0});
    body_b->set_position({10.0, 0.0});

    // 创建约束，指定目标距离为 5.0
    auto constraint = std::make_shared<DistanceConstraint>(
        body_a, body_b, Vector2D(0.0, 0.0), Vector2D(0.0, 0.0), 5.0);

    constraint->stiffness = 1.0;

    solver.add_constraint(constraint);
    solver.initialize();

    // 直接求解约束
    solver.solve(1.0 / 60.0, 10);

    // 物体应该被拉近（目标距离是 5.0，当前是 10.0）
    double distance = body_a->position().distance_to(body_b->position());
    EXPECT_LT(distance, 10.0);
}
