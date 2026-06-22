#include <gtest/gtest.h>
#include "../include/math_types.h"

using namespace sg;

// ========== Vec3 测试 ==========

TEST(Vec3Test, DefaultConstructor) {
    Vec3 v;
    EXPECT_FLOAT_EQ(v.x, 0.0f);
    EXPECT_FLOAT_EQ(v.y, 0.0f);
    EXPECT_FLOAT_EQ(v.z, 0.0f);
}

TEST(Vec3Test, ParameterizedConstructor) {
    Vec3 v(1.0f, 2.0f, 3.0f);
    EXPECT_FLOAT_EQ(v.x, 1.0f);
    EXPECT_FLOAT_EQ(v.y, 2.0f);
    EXPECT_FLOAT_EQ(v.z, 3.0f);
}

TEST(Vec3Test, Addition) {
    Vec3 a(1, 2, 3);
    Vec3 b(4, 5, 6);
    Vec3 c = a + b;
    EXPECT_FLOAT_EQ(c.x, 5.0f);
    EXPECT_FLOAT_EQ(c.y, 7.0f);
    EXPECT_FLOAT_EQ(c.z, 9.0f);
}

TEST(Vec3Test, Subtraction) {
    Vec3 a(5, 7, 9);
    Vec3 b(1, 2, 3);
    Vec3 c = a - b;
    EXPECT_FLOAT_EQ(c.x, 4.0f);
    EXPECT_FLOAT_EQ(c.y, 5.0f);
    EXPECT_FLOAT_EQ(c.z, 6.0f);
}

TEST(Vec3Test, ScalarMultiply) {
    Vec3 v(1, 2, 3);
    Vec3 result = v * 2.0f;
    EXPECT_FLOAT_EQ(result.x, 2.0f);
    EXPECT_FLOAT_EQ(result.y, 4.0f);
    EXPECT_FLOAT_EQ(result.z, 6.0f);
}

TEST(Vec3Test, DotProduct) {
    Vec3 a(1, 0, 0);
    Vec3 b(0, 1, 0);
    EXPECT_FLOAT_EQ(a.dot(b), 0.0f);

    Vec3 c(1, 2, 3);
    Vec3 d(4, 5, 6);
    EXPECT_FLOAT_EQ(c.dot(d), 32.0f);
}

TEST(Vec3Test, CrossProduct) {
    Vec3 a(1, 0, 0);
    Vec3 b(0, 1, 0);
    Vec3 c = a.cross(b);
    EXPECT_FLOAT_EQ(c.x, 0.0f);
    EXPECT_FLOAT_EQ(c.y, 0.0f);
    EXPECT_FLOAT_EQ(c.z, 1.0f);
}

TEST(Vec3Test, Length) {
    Vec3 v(3, 4, 0);
    EXPECT_FLOAT_EQ(v.length(), 5.0f);
}

TEST(Vec3Test, Normalized) {
    Vec3 v(3, 4, 0);
    Vec3 n = v.normalized();
    EXPECT_NEAR(n.length(), 1.0f, 1e-5f);
    EXPECT_NEAR(n.x, 0.6f, 1e-5f);
    EXPECT_NEAR(n.y, 0.8f, 1e-5f);
}

TEST(Vec3Test, ZeroVectorNormalized) {
    Vec3 v(0, 0, 0);
    Vec3 n = v.normalized();
    EXPECT_FLOAT_EQ(n.x, 0.0f);
    EXPECT_FLOAT_EQ(n.y, 0.0f);
    EXPECT_FLOAT_EQ(n.z, 0.0f);
}

// ========== Quaternion 测试 ==========

TEST(QuaternionTest, DefaultConstructor) {
    Quaternion q;
    EXPECT_FLOAT_EQ(q.x, 0.0f);
    EXPECT_FLOAT_EQ(q.y, 0.0f);
    EXPECT_FLOAT_EQ(q.z, 0.0f);
    EXPECT_FLOAT_EQ(q.w, 1.0f);
}

TEST(QuaternionTest, FromAxisAngleIdentity) {
    Quaternion q = Quaternion::from_axis_angle({0, 1, 0}, 0);
    EXPECT_NEAR(q.w, 1.0f, 1e-5f);
}

TEST(QuaternionTest, FromAxisAngle90) {
    Quaternion q = Quaternion::from_axis_angle({0, 1, 0}, 3.14159265f / 2.0f);
    Vec3 v = q.rotate({1, 0, 0});
    EXPECT_NEAR(v.x, 0.0f, 1e-5f);
    EXPECT_NEAR(v.y, 0.0f, 1e-5f);
    EXPECT_NEAR(v.z, -1.0f, 1e-5f);
}

TEST(QuaternionTest, Multiply) {
    Quaternion q1 = Quaternion::from_axis_angle({0, 1, 0}, 3.14159265f / 2.0f);
    Quaternion q2 = Quaternion::from_axis_angle({0, 1, 0}, 3.14159265f / 2.0f);
    Quaternion q3 = q1 * q2;
    Vec3 v = q3.rotate({1, 0, 0});
    EXPECT_NEAR(v.x, -1.0f, 1e-4f);
    EXPECT_NEAR(v.y, 0.0f, 1e-4f);
    EXPECT_NEAR(v.z, 0.0f, 1e-4f);
}

TEST(QuaternionTest, Conjugate) {
    Quaternion q(1, 2, 3, 4);
    Quaternion c = q.conjugate();
    EXPECT_FLOAT_EQ(c.x, -1.0f);
    EXPECT_FLOAT_EQ(c.y, -2.0f);
    EXPECT_FLOAT_EQ(c.z, -3.0f);
    EXPECT_FLOAT_EQ(c.w, 4.0f);
}

TEST(QuaternionTest, FromEuler) {
    Quaternion q = Quaternion::from_euler(0, 3.14159265f / 2.0f, 0);
    Vec3 v = q.rotate({1, 0, 0});
    EXPECT_NEAR(v.x, 0.0f, 1e-4f);
    EXPECT_NEAR(v.y, 0.0f, 1e-4f);
    EXPECT_NEAR(v.z, -1.0f, 1e-4f);
}

// ========== Mat4 测试 ==========

TEST(Mat4Test, IdentityConstructor) {
    Mat4 m;
    for (int r = 0; r < 4; ++r) {
        for (int c = 0; c < 4; ++c) {
            if (r == c)
                EXPECT_FLOAT_EQ(m.at(r, c), 1.0f);
            else
                EXPECT_FLOAT_EQ(m.at(r, c), 0.0f);
        }
    }
}

TEST(Mat4Test, Translation) {
    Mat4 m = Mat4::translation({1, 2, 3});
    Vec3 p = m.transform_point({0, 0, 0});
    EXPECT_FLOAT_EQ(p.x, 1.0f);
    EXPECT_FLOAT_EQ(p.y, 2.0f);
    EXPECT_FLOAT_EQ(p.z, 3.0f);
}

TEST(Mat4Test, TranslationDoesNotAffectDirection) {
    Mat4 m = Mat4::translation({1, 2, 3});
    Vec3 d = m.transform_direction({1, 0, 0});
    EXPECT_FLOAT_EQ(d.x, 1.0f);
    EXPECT_FLOAT_EQ(d.y, 0.0f);
    EXPECT_FLOAT_EQ(d.z, 0.0f);
}

TEST(Mat4Test, Scaling) {
    Mat4 m = Mat4::scaling({2, 3, 4});
    Vec3 p = m.transform_point({1, 1, 1});
    EXPECT_FLOAT_EQ(p.x, 2.0f);
    EXPECT_FLOAT_EQ(p.y, 3.0f);
    EXPECT_FLOAT_EQ(p.z, 4.0f);
}

TEST(Mat4Test, MatrixMultiply) {
    Mat4 t = Mat4::translation({1, 2, 3});
    Mat4 s = Mat4::scaling({2, 2, 2});
    Mat4 ts = t * s;
    Vec3 p = ts.transform_point({1, 1, 1});
    EXPECT_FLOAT_EQ(p.x, 3.0f);
    EXPECT_FLOAT_EQ(p.y, 4.0f);
    EXPECT_FLOAT_EQ(p.z, 5.0f);
}

TEST(Mat4Test, IdentityMultiply) {
    Mat4 identity;
    Mat4 t = Mat4::translation({1, 2, 3});
    Mat4 result = identity * t;
    Vec3 p = result.transform_point({0, 0, 0});
    EXPECT_FLOAT_EQ(p.x, 1.0f);
    EXPECT_FLOAT_EQ(p.y, 2.0f);
    EXPECT_FLOAT_EQ(p.z, 3.0f);
}

TEST(Mat4Test, Inverse) {
    Mat4 t = Mat4::translation({1, 2, 3});
    Mat4 t_inv = t.inverse();
    Mat4 result = t * t_inv;
    // 应该接近单位矩阵
    for (int r = 0; r < 4; ++r) {
        for (int c = 0; c < 4; ++c) {
            EXPECT_NEAR(result.at(r, c), (r == c) ? 1.0f : 0.0f, 1e-5f);
        }
    }
}

TEST(Mat4Test, InverseTransformPoint) {
    Mat4 t = Mat4::translation({1, 2, 3});
    Mat4 t_inv = t.inverse();
    Vec3 original(5, 6, 7);
    Vec3 transformed = t.transform_point(original);
    Vec3 restored = t_inv.transform_point(transformed);
    EXPECT_NEAR(restored.x, original.x, 1e-5f);
    EXPECT_NEAR(restored.y, original.y, 1e-5f);
    EXPECT_NEAR(restored.z, original.z, 1e-5f);
}

TEST(Mat4Test, Transpose) {
    Mat4 m;
    m.at(0, 1) = 5.0f;
    m.at(1, 0) = 3.0f;
    Mat4 mt = m.transposed();
    EXPECT_FLOAT_EQ(mt.at(0, 1), 3.0f);
    EXPECT_FLOAT_EQ(mt.at(1, 0), 5.0f);
}

TEST(Mat4Test, Rotation) {
    Quaternion q = Quaternion::from_axis_angle({0, 0, 1}, 3.14159265f / 2.0f);
    Mat4 r = Mat4::rotation(q);
    Vec3 p = r.transform_point({1, 0, 0});
    EXPECT_NEAR(p.x, 0.0f, 1e-5f);
    EXPECT_NEAR(p.y, 1.0f, 1e-5f);
    EXPECT_NEAR(p.z, 0.0f, 1e-5f);
}

TEST(Mat4Test, TRS) {
    Vec3 t(1, 2, 3);
    Quaternion r = Quaternion::from_axis_angle({0, 0, 1}, 3.14159265f / 2.0f);
    Vec3 s(2, 2, 2);
    Mat4 trs = Mat4::trs(t, r, s);
    Vec3 p = trs.transform_point({1, 0, 0});
    EXPECT_NEAR(p.x, 1.0f, 1e-4f);
    EXPECT_NEAR(p.y, 4.0f, 1e-4f);
    EXPECT_NEAR(p.z, 3.0f, 1e-4f);
}

// ========== Vec4 测试 ==========

TEST(Vec4Test, ToVec3) {
    Vec4 v(2, 4, 6, 2);
    Vec3 p = v.to_vec3();
    EXPECT_FLOAT_EQ(p.x, 1.0f);
    EXPECT_FLOAT_EQ(p.y, 2.0f);
    EXPECT_FLOAT_EQ(p.z, 3.0f);
}

TEST(Vec4Test, FromVec3) {
    Vec3 v(1, 2, 3);
    Vec4 v4(v, 1.0f);
    EXPECT_FLOAT_EQ(v4.x, 1.0f);
    EXPECT_FLOAT_EQ(v4.y, 2.0f);
    EXPECT_FLOAT_EQ(v4.z, 3.0f);
    EXPECT_FLOAT_EQ(v4.w, 1.0f);
}
