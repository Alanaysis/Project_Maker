#include <gtest/gtest.h>
#include "../include/transform.h"

using namespace sg;

TEST(TransformTest, DefaultConstructor) {
    Transform t;
    EXPECT_FLOAT_EQ(t.position.x, 0.0f);
    EXPECT_FLOAT_EQ(t.position.y, 0.0f);
    EXPECT_FLOAT_EQ(t.position.z, 0.0f);
    EXPECT_FLOAT_EQ(t.scale.x, 1.0f);
    EXPECT_FLOAT_EQ(t.scale.y, 1.0f);
    EXPECT_FLOAT_EQ(t.scale.z, 1.0f);
    EXPECT_FLOAT_EQ(t.rotation.w, 1.0f);
}

TEST(TransformTest, LocalMatrixIdentity) {
    Transform t;
    Mat4 m = t.get_local_matrix();
    for (int r = 0; r < 4; ++r) {
        for (int c = 0; c < 4; ++c) {
            EXPECT_NEAR(m.at(r, c), (r == c) ? 1.0f : 0.0f, 1e-5f);
        }
    }
}

TEST(TransformTest, PositionOnly) {
    Transform t;
    t.position = Vec3(1, 2, 3);
    Mat4 m = t.get_local_matrix();
    Vec3 p = m.transform_point({0, 0, 0});
    EXPECT_FLOAT_EQ(p.x, 1.0f);
    EXPECT_FLOAT_EQ(p.y, 2.0f);
    EXPECT_FLOAT_EQ(p.z, 3.0f);
}

TEST(TransformTest, ScaleOnly) {
    Transform t;
    t.scale = Vec3(2, 3, 4);
    Mat4 m = t.get_local_matrix();
    Vec3 p = m.transform_point({1, 1, 1});
    EXPECT_FLOAT_EQ(p.x, 2.0f);
    EXPECT_FLOAT_EQ(p.y, 3.0f);
    EXPECT_FLOAT_EQ(p.z, 4.0f);
}

TEST(TransformTest, Translate) {
    Transform t;
    t.translate(Vec3(1, 2, 3));
    EXPECT_FLOAT_EQ(t.position.x, 1.0f);
    EXPECT_FLOAT_EQ(t.position.y, 2.0f);
    EXPECT_FLOAT_EQ(t.position.z, 3.0f);
}

TEST(TransformTest, ScaleBy) {
    Transform t;
    t.scale_by(Vec3(2, 3, 4));
    EXPECT_FLOAT_EQ(t.scale.x, 2.0f);
    EXPECT_FLOAT_EQ(t.scale.y, 3.0f);
    EXPECT_FLOAT_EQ(t.scale.z, 4.0f);
}

TEST(TransformTest, Forward) {
    Transform t;
    Vec3 fwd = t.forward();
    EXPECT_NEAR(fwd.x, 0.0f, 1e-5f);
    EXPECT_NEAR(fwd.y, 0.0f, 1e-5f);
    EXPECT_NEAR(fwd.z, -1.0f, 1e-5f);
}

TEST(TransformTest, Right) {
    Transform t;
    Vec3 r = t.right();
    EXPECT_NEAR(r.x, 1.0f, 1e-5f);
    EXPECT_NEAR(r.y, 0.0f, 1e-5f);
    EXPECT_NEAR(r.z, 0.0f, 1e-5f);
}

TEST(TransformTest, Up) {
    Transform t;
    Vec3 u = t.up();
    EXPECT_NEAR(u.x, 0.0f, 1e-5f);
    EXPECT_NEAR(u.y, 1.0f, 1e-5f);
    EXPECT_NEAR(u.z, 0.0f, 1e-5f);
}

TEST(TransformTest, RotateAxis) {
    Transform t;
    t.rotate_axis({0, 1, 0}, 90.0f);
    Vec3 fwd = t.forward();
    EXPECT_NEAR(fwd.x, -1.0f, 1e-4f);
    EXPECT_NEAR(fwd.y, 0.0f, 1e-4f);
    EXPECT_NEAR(fwd.z, 0.0f, 1e-4f);
}

TEST(TransformTest, SetRotationEuler) {
    Transform t;
    t.set_rotation_euler(0, 90, 0);
    Vec3 fwd = t.forward();
    EXPECT_NEAR(fwd.x, -1.0f, 1e-4f);
    EXPECT_NEAR(fwd.y, 0.0f, 1e-4f);
    EXPECT_NEAR(fwd.z, 0.0f, 1e-4f);
}

TEST(TransformTest, CombinedTransform) {
    Transform t;
    t.position = Vec3(10, 0, 0);
    t.scale = Vec3(2, 2, 2);
    Mat4 m = t.get_local_matrix();
    Vec3 p = m.transform_point({1, 0, 0});
    EXPECT_FLOAT_EQ(p.x, 12.0f);
    EXPECT_FLOAT_EQ(p.y, 0.0f);
    EXPECT_FLOAT_EQ(p.z, 0.0f);
}
