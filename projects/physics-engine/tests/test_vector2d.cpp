#include <gtest/gtest.h>
#include "physics_engine/vector2d.h"

using namespace physics_engine;

TEST(Vector2DTest, DefaultConstructor) {
    Vector2D v;
    EXPECT_DOUBLE_EQ(v.x, 0.0);
    EXPECT_DOUBLE_EQ(v.y, 0.0);
}

TEST(Vector2DTest, ParameterizedConstructor) {
    Vector2D v(3.0, 4.0);
    EXPECT_DOUBLE_EQ(v.x, 3.0);
    EXPECT_DOUBLE_EQ(v.y, 4.0);
}

TEST(Vector2DTest, Addition) {
    Vector2D a(1.0, 2.0);
    Vector2D b(3.0, 4.0);
    Vector2D c = a + b;
    EXPECT_DOUBLE_EQ(c.x, 4.0);
    EXPECT_DOUBLE_EQ(c.y, 6.0);
}

TEST(Vector2DTest, Subtraction) {
    Vector2D a(5.0, 7.0);
    Vector2D b(2.0, 3.0);
    Vector2D c = a - b;
    EXPECT_DOUBLE_EQ(c.x, 3.0);
    EXPECT_DOUBLE_EQ(c.y, 4.0);
}

TEST(Vector2DTest, ScalarMultiplication) {
    Vector2D v(2.0, 3.0);
    Vector2D result = v * 2.0;
    EXPECT_DOUBLE_EQ(result.x, 4.0);
    EXPECT_DOUBLE_EQ(result.y, 6.0);

    // 测试标量在左边
    Vector2D result2 = 3.0 * v;
    EXPECT_DOUBLE_EQ(result2.x, 6.0);
    EXPECT_DOUBLE_EQ(result2.y, 9.0);
}

TEST(Vector2DTest, ScalarDivision) {
    Vector2D v(6.0, 8.0);
    Vector2D result = v / 2.0;
    EXPECT_DOUBLE_EQ(result.x, 3.0);
    EXPECT_DOUBLE_EQ(result.y, 4.0);
}

TEST(Vector2DTest, CompoundAssignment) {
    Vector2D v(1.0, 2.0);
    v += Vector2D(3.0, 4.0);
    EXPECT_DOUBLE_EQ(v.x, 4.0);
    EXPECT_DOUBLE_EQ(v.y, 6.0);

    v -= Vector2D(1.0, 2.0);
    EXPECT_DOUBLE_EQ(v.x, 3.0);
    EXPECT_DOUBLE_EQ(v.y, 4.0);

    v *= 2.0;
    EXPECT_DOUBLE_EQ(v.x, 6.0);
    EXPECT_DOUBLE_EQ(v.y, 8.0);

    v /= 2.0;
    EXPECT_DOUBLE_EQ(v.x, 3.0);
    EXPECT_DOUBLE_EQ(v.y, 4.0);
}

TEST(Vector2DTest, Negation) {
    Vector2D v(3.0, -4.0);
    Vector2D neg = -v;
    EXPECT_DOUBLE_EQ(neg.x, -3.0);
    EXPECT_DOUBLE_EQ(neg.y, 4.0);
}

TEST(Vector2DTest, Equality) {
    Vector2D a(1.0, 2.0);
    Vector2D b(1.0, 2.0);
    Vector2D c(1.0, 3.0);

    EXPECT_TRUE(a == b);
    EXPECT_FALSE(a == c);
    EXPECT_TRUE(a != c);
    EXPECT_FALSE(a != b);
}

TEST(Vector2DTest, DotProduct) {
    Vector2D a(1.0, 2.0);
    Vector2D b(3.0, 4.0);
    double dot = a.dot(b);
    EXPECT_DOUBLE_EQ(dot, 11.0);  // 1*3 + 2*4
}

TEST(Vector2DTest, CrossProduct) {
    Vector2D a(1.0, 0.0);
    Vector2D b(0.0, 1.0);
    double cross = a.cross(b);
    EXPECT_DOUBLE_EQ(cross, 1.0);  // 1*1 - 0*0
}

TEST(Vector2DTest, Length) {
    Vector2D v(3.0, 4.0);
    EXPECT_DOUBLE_EQ(v.length_squared(), 25.0);
    EXPECT_DOUBLE_EQ(v.length(), 5.0);
}

TEST(Vector2DTest, Normalization) {
    Vector2D v(3.0, 4.0);
    Vector2D n = v.normalized();
    EXPECT_NEAR(n.x, 0.6, 1e-10);
    EXPECT_NEAR(n.y, 0.8, 1e-10);
    EXPECT_NEAR(n.length(), 1.0, 1e-10);
}

TEST(Vector2DTest, NormalizeInPlace) {
    Vector2D v(3.0, 4.0);
    v.normalize();
    EXPECT_NEAR(v.x, 0.6, 1e-10);
    EXPECT_NEAR(v.y, 0.8, 1e-10);
    EXPECT_NEAR(v.length(), 1.0, 1e-10);
}

TEST(Vector2DTest, ZeroVectorNormalization) {
    Vector2D v(0.0, 0.0);
    Vector2D n = v.normalized();
    EXPECT_DOUBLE_EQ(n.x, 0.0);
    EXPECT_DOUBLE_EQ(n.y, 0.0);
}

TEST(Vector2DTest, Distance) {
    Vector2D a(0.0, 0.0);
    Vector2D b(3.0, 4.0);
    EXPECT_DOUBLE_EQ(a.distance_to(b), 5.0);
    EXPECT_DOUBLE_EQ(a.distance_squared_to(b), 25.0);
}

TEST(Vector2DTest, Rotation) {
    Vector2D v(1.0, 0.0);
    Vector2D rotated = v.rotated(M_PI / 2);  // 90度
    EXPECT_NEAR(rotated.x, 0.0, 1e-10);
    EXPECT_NEAR(rotated.y, 1.0, 1e-10);
}

TEST(Vector2DTest, Angle) {
    Vector2D v(1.0, 0.0);
    EXPECT_DOUBLE_EQ(v.angle(), 0.0);

    Vector2D v2(0.0, 1.0);
    EXPECT_NEAR(v2.angle(), M_PI / 2, 1e-10);
}

TEST(Vector2DTest, AngleBetweenVectors) {
    Vector2D a(1.0, 0.0);
    Vector2D b(0.0, 1.0);
    EXPECT_NEAR(a.angle_to(b), M_PI / 2, 1e-10);
}

TEST(Vector2DTest, Projection) {
    Vector2D a(2.0, 3.0);
    Vector2D b(1.0, 0.0);
    Vector2D proj = a.project_onto(b);
    EXPECT_DOUBLE_EQ(proj.x, 2.0);
    EXPECT_DOUBLE_EQ(proj.y, 0.0);
}

TEST(Vector2DTest, Reflection) {
    Vector2D v(1.0, -1.0);
    Vector2D normal(0.0, 1.0);
    Vector2D reflected = v.reflect(normal);
    EXPECT_DOUBLE_EQ(reflected.x, 1.0);
    EXPECT_DOUBLE_EQ(reflected.y, 1.0);
}

TEST(Vector2DTest, Lerp) {
    Vector2D a(0.0, 0.0);
    Vector2D b(10.0, 10.0);

    Vector2D mid = Vector2D::lerp(a, b, 0.5);
    EXPECT_DOUBLE_EQ(mid.x, 5.0);
    EXPECT_DOUBLE_EQ(mid.y, 5.0);

    Vector2D start = Vector2D::lerp(a, b, 0.0);
    EXPECT_DOUBLE_EQ(start.x, 0.0);
    EXPECT_DOUBLE_EQ(start.y, 0.0);

    Vector2D end = Vector2D::lerp(a, b, 1.0);
    EXPECT_DOUBLE_EQ(end.x, 10.0);
    EXPECT_DOUBLE_EQ(end.y, 10.0);
}
