#include <gtest/gtest.h>
#include "../include/bounds.h"

using namespace sg;

// ========== AABB 测试 ==========

TEST(AABBTest, DefaultConstructor) {
    AABB aabb;
    EXPECT_GT(aabb.min.x, aabb.max.x); // 应该是无效的 AABB
}

TEST(AABBTest, FromCenterSize) {
    AABB aabb = AABB::from_center_size({0, 0, 0}, {1, 1, 1});
    EXPECT_FLOAT_EQ(aabb.min.x, -1.0f);
    EXPECT_FLOAT_EQ(aabb.max.x, 1.0f);
    EXPECT_FLOAT_EQ(aabb.min.y, -1.0f);
    EXPECT_FLOAT_EQ(aabb.max.y, 1.0f);
}

TEST(AABBTest, Expand) {
    AABB aabb;
    aabb.expand({1, 2, 3});
    aabb.expand({-1, -2, -3});
    EXPECT_FLOAT_EQ(aabb.min.x, -1.0f);
    EXPECT_FLOAT_EQ(aabb.max.x, 1.0f);
    EXPECT_FLOAT_EQ(aabb.min.y, -2.0f);
    EXPECT_FLOAT_EQ(aabb.max.y, 2.0f);
}

TEST(AABBTest, Center) {
    AABB aabb = AABB::from_center_size({5, 5, 5}, {1, 1, 1});
    Vec3 c = aabb.center();
    EXPECT_FLOAT_EQ(c.x, 5.0f);
    EXPECT_FLOAT_EQ(c.y, 5.0f);
    EXPECT_FLOAT_EQ(c.z, 5.0f);
}

TEST(AABBTest, Contains) {
    AABB aabb = AABB::from_center_size({0, 0, 0}, {1, 1, 1});
    EXPECT_TRUE(aabb.contains({0, 0, 0}));
    EXPECT_TRUE(aabb.contains({0.5f, 0.5f, 0.5f}));
    EXPECT_FALSE(aabb.contains({2, 0, 0}));
}

TEST(AABBTest, IntersectsTrue) {
    AABB a = AABB::from_center_size({0, 0, 0}, {1, 1, 1});
    AABB b = AABB::from_center_size({0.5f, 0, 0}, {1, 1, 1});
    EXPECT_TRUE(a.intersects(b));
}

TEST(AABBTest, IntersectsFalse) {
    AABB a = AABB::from_center_size({0, 0, 0}, {1, 1, 1});
    AABB b = AABB::from_center_size({5, 5, 5}, {1, 1, 1});
    EXPECT_FALSE(a.intersects(b));
}

TEST(AABBTest, Merge) {
    AABB a = AABB::from_center_size({0, 0, 0}, {1, 1, 1});
    AABB b = AABB::from_center_size({5, 5, 5}, {1, 1, 1});
    AABB merged = AABB::merge(a, b);
    EXPECT_FLOAT_EQ(merged.min.x, -1.0f);
    EXPECT_FLOAT_EQ(merged.max.x, 6.0f);
}

TEST(AABBTest, Transform) {
    AABB aabb = AABB::from_center_size({0, 0, 0}, {1, 1, 1});
    Mat4 translation = Mat4::translation({10, 0, 0});
    AABB transformed = aabb.transform(translation);
    EXPECT_NEAR(transformed.min.x, 9.0f, 1e-5f);
    EXPECT_NEAR(transformed.max.x, 11.0f, 1e-5f);
}

TEST(AABBTest, TransformWithScale) {
    AABB aabb = AABB::from_center_size({0, 0, 0}, {1, 1, 1});
    Mat4 scale = Mat4::scaling({2, 2, 2});
    AABB transformed = aabb.transform(scale);
    EXPECT_NEAR(transformed.min.x, -2.0f, 1e-5f);
    EXPECT_NEAR(transformed.max.x, 2.0f, 1e-5f);
}

TEST(AABBTest, Volume) {
    AABB aabb({0, 0, 0}, {2, 3, 4});
    EXPECT_FLOAT_EQ(aabb.volume(), 24.0f);
}

TEST(AABBTest, SurfaceArea) {
    AABB aabb({0, 0, 0}, {2, 3, 4});
    EXPECT_FLOAT_EQ(aabb.surface_area(), 52.0f); // 2*(2*3 + 3*4 + 4*2) = 52
}

// ========== Plane 测试 ==========

TEST(PlaneTest, DistanceTo) {
    Plane p(Vec3(0, 1, 0), -5.0f); // y = 5 平面
    EXPECT_FLOAT_EQ(p.distance_to({0, 5, 0}), 0.0f);
    EXPECT_GT(p.distance_to({0, 6, 0}), 0.0f); // 上方为正
    EXPECT_LT(p.distance_to({0, 4, 0}), 0.0f); // 下方为负
}

TEST(PlaneTest, FromPoints) {
    Vec3 a(0, 0, 0), b(1, 0, 0), c(0, 0, 1);
    Plane p = Plane::from_points(a, b, c);
    EXPECT_NEAR(p.normal.y, 1.0f, 1e-5f); // 法向量应该朝上
}

// ========== Frustum 测试 ==========

TEST(FrustumTest, PointInside) {
    // 创建一个简单的视锥体
    Mat4 vp = Mat4::perspective(1.047f, 16.0f/9.0f, 0.1f, 100.0f) *
              Mat4::look_at({0,0,5}, {0,0,0}, {0,1,0});
    Frustum frustum = Frustum::from_view_projection(vp);
    EXPECT_TRUE(frustum.test_point({0, 0, 0}));
}

TEST(FrustumTest, PointOutside) {
    Mat4 vp = Mat4::perspective(1.047f, 16.0f/9.0f, 0.1f, 100.0f) *
              Mat4::look_at({0,0,5}, {0,0,0}, {0,1,0});
    Frustum frustum = Frustum::from_view_projection(vp);
    EXPECT_FALSE(frustum.test_point({100, 0, 0}));
}

TEST(FrustumTest, AABBInside) {
    Mat4 vp = Mat4::perspective(1.047f, 16.0f/9.0f, 0.1f, 100.0f) *
              Mat4::look_at({0,0,5}, {0,0,0}, {0,1,0});
    Frustum frustum = Frustum::from_view_projection(vp);
    AABB aabb = AABB::from_center_size({0, 0, 0}, {0.5f, 0.5f, 0.5f});
    EXPECT_TRUE(frustum.test_aabb(aabb));
}

TEST(FrustumTest, AABBOutside) {
    Mat4 vp = Mat4::perspective(1.047f, 16.0f/9.0f, 0.1f, 100.0f) *
              Mat4::look_at({0,0,5}, {0,0,0}, {0,1,0});
    Frustum frustum = Frustum::from_view_projection(vp);
    AABB aabb = AABB::from_center_size({100, 0, 0}, {1, 1, 1});
    EXPECT_FALSE(frustum.test_aabb(aabb));
}

TEST(FrustumTest, SphereInside) {
    Mat4 vp = Mat4::perspective(1.047f, 16.0f/9.0f, 0.1f, 100.0f) *
              Mat4::look_at({0,0,5}, {0,0,0}, {0,1,0});
    Frustum frustum = Frustum::from_view_projection(vp);
    EXPECT_TRUE(frustum.test_sphere({0, 0, 0}, 0.5f));
}

TEST(FrustumTest, SphereOutside) {
    Mat4 vp = Mat4::perspective(1.047f, 16.0f/9.0f, 0.1f, 100.0f) *
              Mat4::look_at({0,0,5}, {0,0,0}, {0,1,0});
    Frustum frustum = Frustum::from_view_projection(vp);
    EXPECT_FALSE(frustum.test_sphere({100, 0, 0}, 1.0f));
}
