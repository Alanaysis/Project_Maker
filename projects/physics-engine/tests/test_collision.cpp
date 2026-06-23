#include <gtest/gtest.h>
#include "physics_engine/collision.h"

using namespace physics_engine;

TEST(CollisionTest, AABBvsAABB_NoCollision) {
    AABB a(0.0, 0.0, 10.0, 10.0);
    AABB b(15.0, 15.0, 20.0, 20.0);

    CollisionResult result = aabb_vs_aabb(a, b);
    EXPECT_FALSE(result.collided);
}

TEST(CollisionTest, AABBvsAABB_OverlapX) {
    AABB a(0.0, 0.0, 10.0, 10.0);
    AABB b(5.0, 0.0, 15.0, 10.0);

    CollisionResult result = aabb_vs_aabb(a, b);
    EXPECT_TRUE(result.collided);
    EXPECT_DOUBLE_EQ(result.penetration, 5.0);
    EXPECT_DOUBLE_EQ(result.normal.x, 1.0);
    EXPECT_DOUBLE_EQ(result.normal.y, 0.0);
}

TEST(CollisionTest, AABBvsAABB_OverlapY) {
    AABB a(0.0, 0.0, 10.0, 10.0);
    AABB b(0.0, 5.0, 10.0, 15.0);

    CollisionResult result = aabb_vs_aabb(a, b);
    EXPECT_TRUE(result.collided);
    EXPECT_DOUBLE_EQ(result.penetration, 5.0);
    EXPECT_DOUBLE_EQ(result.normal.x, 0.0);
    EXPECT_DOUBLE_EQ(result.normal.y, 1.0);
}

TEST(CollisionTest, AABBvsAABB_OverlapXY_XSmaller) {
    AABB a(0.0, 0.0, 10.0, 10.0);
    AABB b(5.0, 2.0, 15.0, 12.0);

    CollisionResult result = aabb_vs_aabb(a, b);
    EXPECT_TRUE(result.collided);
    EXPECT_DOUBLE_EQ(result.penetration, 5.0);  // X 方向重叠较小
    EXPECT_DOUBLE_EQ(result.normal.x, 1.0);
    EXPECT_DOUBLE_EQ(result.normal.y, 0.0);
}

TEST(CollisionTest, AABBvsAABB_OverlapXY_YSmaller) {
    AABB a(0.0, 0.0, 10.0, 10.0);
    AABB b(2.0, 5.0, 12.0, 15.0);

    CollisionResult result = aabb_vs_aabb(a, b);
    EXPECT_TRUE(result.collided);
    EXPECT_DOUBLE_EQ(result.penetration, 5.0);  // Y 方向重叠较小
    EXPECT_DOUBLE_EQ(result.normal.x, 0.0);
    EXPECT_DOUBLE_EQ(result.normal.y, 1.0);
}

TEST(CollisionTest, AABBvsAABB_BA) {
    // 测试 B 在 A 左边的情况
    AABB a(5.0, 0.0, 15.0, 10.0);
    AABB b(0.0, 0.0, 10.0, 10.0);

    CollisionResult result = aabb_vs_aabb(a, b);
    EXPECT_TRUE(result.collided);
    EXPECT_DOUBLE_EQ(result.penetration, 5.0);
    EXPECT_DOUBLE_EQ(result.normal.x, -1.0);
    EXPECT_DOUBLE_EQ(result.normal.y, 0.0);
}

TEST(CollisionTest, CircleVsCircle_NoCollision) {
    Vector2D center_a(0.0, 0.0);
    Vector2D center_b(10.0, 0.0);
    double radius_a = 2.0;
    double radius_b = 2.0;

    CollisionResult result = circle_vs_circle(center_a, radius_a, center_b, radius_b);
    EXPECT_FALSE(result.collided);
}

TEST(CollisionTest, CircleVsCircle_Collision) {
    Vector2D center_a(0.0, 0.0);
    Vector2D center_b(3.0, 0.0);
    double radius_a = 2.0;
    double radius_b = 2.0;

    CollisionResult result = circle_vs_circle(center_a, radius_a, center_b, radius_b);
    EXPECT_TRUE(result.collided);
    EXPECT_NEAR(result.penetration, 1.0, 1e-10);
    EXPECT_NEAR(result.normal.x, 1.0, 1e-10);
    EXPECT_NEAR(result.normal.y, 0.0, 1e-10);
}

TEST(CollisionTest, CircleVsCircle_SameCenter) {
    Vector2D center(0.0, 0.0);
    double radius_a = 2.0;
    double radius_b = 3.0;

    CollisionResult result = circle_vs_circle(center, radius_a, center, radius_b);
    EXPECT_TRUE(result.collided);
    EXPECT_NEAR(result.penetration, 5.0, 1e-10);
    EXPECT_NEAR(result.normal.x, 1.0, 1e-10);
    EXPECT_NEAR(result.normal.y, 0.0, 1e-10);
}

TEST(CollisionTest, AABBvsCircle_NoCollision) {
    AABB aabb(0.0, 0.0, 10.0, 10.0);
    Vector2D circle_center(15.0, 5.0);
    double circle_radius = 2.0;

    CollisionResult result = aabb_vs_circle(aabb, circle_center, circle_radius);
    EXPECT_FALSE(result.collided);
}

TEST(CollisionTest, AABBvsCircle_CollisionRight) {
    AABB aabb(0.0, 0.0, 10.0, 10.0);
    Vector2D circle_center(11.0, 5.0);
    double circle_radius = 2.0;

    CollisionResult result = aabb_vs_circle(aabb, circle_center, circle_radius);
    EXPECT_TRUE(result.collided);
    EXPECT_NEAR(result.penetration, 1.0, 1e-10);
    EXPECT_NEAR(result.normal.x, 1.0, 1e-10);
    EXPECT_NEAR(result.normal.y, 0.0, 1e-10);
}

TEST(CollisionTest, AABBvsCircle_CollisionLeft) {
    AABB aabb(0.0, 0.0, 10.0, 10.0);
    Vector2D circle_center(-1.0, 5.0);
    double circle_radius = 2.0;

    CollisionResult result = aabb_vs_circle(aabb, circle_center, circle_radius);
    EXPECT_TRUE(result.collided);
    EXPECT_NEAR(result.penetration, 1.0, 1e-10);
    EXPECT_NEAR(result.normal.x, -1.0, 1e-10);
    EXPECT_NEAR(result.normal.y, 0.0, 1e-10);
}

TEST(CollisionTest, AABBvsCircle_CollisionTop) {
    AABB aabb(0.0, 0.0, 10.0, 10.0);
    Vector2D circle_center(5.0, 11.0);
    double circle_radius = 2.0;

    CollisionResult result = aabb_vs_circle(aabb, circle_center, circle_radius);
    EXPECT_TRUE(result.collided);
    EXPECT_NEAR(result.penetration, 1.0, 1e-10);
    EXPECT_NEAR(result.normal.x, 0.0, 1e-10);
    EXPECT_NEAR(result.normal.y, 1.0, 1e-10);
}

TEST(CollisionTest, AABBvsCircle_CollisionBottom) {
    AABB aabb(0.0, 0.0, 10.0, 10.0);
    Vector2D circle_center(5.0, -1.0);
    double circle_radius = 2.0;

    CollisionResult result = aabb_vs_circle(aabb, circle_center, circle_radius);
    EXPECT_TRUE(result.collided);
    EXPECT_NEAR(result.penetration, 1.0, 1e-10);
    EXPECT_NEAR(result.normal.x, 0.0, 1e-10);
    EXPECT_NEAR(result.normal.y, -1.0, 1e-10);
}

TEST(CollisionTest, AABBvsCircle_CircleInside) {
    AABB aabb(0.0, 0.0, 10.0, 10.0);
    Vector2D circle_center(5.0, 5.0);
    double circle_radius = 2.0;

    CollisionResult result = aabb_vs_circle(aabb, circle_center, circle_radius);
    EXPECT_TRUE(result.collided);
    EXPECT_NEAR(result.penetration, 2.0, 1e-10);
}

TEST(CollisionTest, AABBvsCircle_CircleCoversAABB) {
    AABB aabb(0.0, 0.0, 10.0, 10.0);
    Vector2D circle_center(5.0, 5.0);
    double circle_radius = 20.0;

    CollisionResult result = aabb_vs_circle(aabb, circle_center, circle_radius);
    EXPECT_TRUE(result.collided);
    EXPECT_NEAR(result.penetration, 20.0, 1e-10);
}
