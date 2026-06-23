#include <gtest/gtest.h>
#include "physics_engine/aabb.h"

using namespace physics_engine;

TEST(AABBTest, DefaultConstructor) {
    AABB aabb;
    EXPECT_DOUBLE_EQ(aabb.min.x, 0.0);
    EXPECT_DOUBLE_EQ(aabb.min.y, 0.0);
    EXPECT_DOUBLE_EQ(aabb.max.x, 0.0);
    EXPECT_DOUBLE_EQ(aabb.max.y, 0.0);
}

TEST(AABBTest, ParameterizedConstructor) {
    AABB aabb(Vector2D(1.0, 2.0), Vector2D(3.0, 4.0));
    EXPECT_DOUBLE_EQ(aabb.min.x, 1.0);
    EXPECT_DOUBLE_EQ(aabb.min.y, 2.0);
    EXPECT_DOUBLE_EQ(aabb.max.x, 3.0);
    EXPECT_DOUBLE_EQ(aabb.max.y, 4.0);
}

TEST(AABBTest, ScalarConstructor) {
    AABB aabb(1.0, 2.0, 3.0, 4.0);
    EXPECT_DOUBLE_EQ(aabb.min.x, 1.0);
    EXPECT_DOUBLE_EQ(aabb.min.y, 2.0);
    EXPECT_DOUBLE_EQ(aabb.max.x, 3.0);
    EXPECT_DOUBLE_EQ(aabb.max.y, 4.0);
}

TEST(AABBTest, Center) {
    AABB aabb(0.0, 0.0, 4.0, 6.0);
    Vector2D center = aabb.center();
    EXPECT_DOUBLE_EQ(center.x, 2.0);
    EXPECT_DOUBLE_EQ(center.y, 3.0);
}

TEST(AABBTest, Size) {
    AABB aabb(1.0, 2.0, 5.0, 8.0);
    Vector2D size = aabb.size();
    EXPECT_DOUBLE_EQ(size.x, 4.0);
    EXPECT_DOUBLE_EQ(size.y, 6.0);
}

TEST(AABBTest, HalfSize) {
    AABB aabb(0.0, 0.0, 4.0, 6.0);
    Vector2D half_size = aabb.half_size();
    EXPECT_DOUBLE_EQ(half_size.x, 2.0);
    EXPECT_DOUBLE_EQ(half_size.y, 3.0);
}

TEST(AABBTest, Area) {
    AABB aabb(0.0, 0.0, 3.0, 4.0);
    EXPECT_DOUBLE_EQ(aabb.area(), 12.0);
}

TEST(AABBTest, Perimeter) {
    AABB aabb(0.0, 0.0, 3.0, 4.0);
    EXPECT_DOUBLE_EQ(aabb.perimeter(), 14.0);
}

TEST(AABBTest, ContainsPoint) {
    AABB aabb(0.0, 0.0, 10.0, 10.0);

    // 内部点
    EXPECT_TRUE(aabb.contains(Vector2D(5.0, 5.0)));

    // 边界点
    EXPECT_TRUE(aabb.contains(Vector2D(0.0, 0.0)));
    EXPECT_TRUE(aabb.contains(Vector2D(10.0, 10.0)));

    // 外部点
    EXPECT_FALSE(aabb.contains(Vector2D(-1.0, 5.0)));
    EXPECT_FALSE(aabb.contains(Vector2D(11.0, 5.0)));
    EXPECT_FALSE(aabb.contains(Vector2D(5.0, -1.0)));
    EXPECT_FALSE(aabb.contains(Vector2D(5.0, 11.0)));
}

TEST(AABBTest, ContainsAABB) {
    AABB outer(0.0, 0.0, 10.0, 10.0);
    AABB inner(2.0, 2.0, 8.0, 8.0);
    AABB overlapping(5.0, 5.0, 15.0, 15.0);

    EXPECT_TRUE(outer.contains(inner));
    EXPECT_FALSE(inner.contains(outer));
    EXPECT_FALSE(outer.contains(overlapping));
}

TEST(AABBTest, Intersects) {
    AABB aabb1(0.0, 0.0, 10.0, 10.0);
    AABB aabb2(5.0, 5.0, 15.0, 15.0);  // 重叠
    AABB aabb3(10.0, 10.0, 20.0, 20.0); // 边界接触
    AABB aabb4(11.0, 11.0, 20.0, 20.0); // 分离

    EXPECT_TRUE(aabb1.intersects(aabb2));
    EXPECT_TRUE(aabb2.intersects(aabb1));
    EXPECT_TRUE(aabb1.intersects(aabb3));
    EXPECT_FALSE(aabb1.intersects(aabb4));
    EXPECT_FALSE(aabb4.intersects(aabb1));
}

TEST(AABBTest, Intersection) {
    AABB aabb1(0.0, 0.0, 10.0, 10.0);
    AABB aabb2(5.0, 5.0, 15.0, 15.0);

    AABB intersection = aabb1.intersection(aabb2);
    EXPECT_DOUBLE_EQ(intersection.min.x, 5.0);
    EXPECT_DOUBLE_EQ(intersection.min.y, 5.0);
    EXPECT_DOUBLE_EQ(intersection.max.x, 10.0);
    EXPECT_DOUBLE_EQ(intersection.max.y, 10.0);
}

TEST(AABBTest, Merge) {
    AABB aabb1(0.0, 0.0, 10.0, 10.0);
    AABB aabb2(5.0, 5.0, 15.0, 15.0);

    AABB merged = aabb1.merge(aabb2);
    EXPECT_DOUBLE_EQ(merged.min.x, 0.0);
    EXPECT_DOUBLE_EQ(merged.min.y, 0.0);
    EXPECT_DOUBLE_EQ(merged.max.x, 15.0);
    EXPECT_DOUBLE_EQ(merged.max.y, 15.0);
}

TEST(AABBTest, MergeInPlace) {
    AABB aabb1(0.0, 0.0, 10.0, 10.0);
    AABB aabb2(5.0, 5.0, 15.0, 15.0);

    aabb1.merge_inplace(aabb2);
    EXPECT_DOUBLE_EQ(aabb1.min.x, 0.0);
    EXPECT_DOUBLE_EQ(aabb1.min.y, 0.0);
    EXPECT_DOUBLE_EQ(aabb1.max.x, 15.0);
    EXPECT_DOUBLE_EQ(aabb1.max.y, 15.0);
}

TEST(AABBTest, Expanded) {
    AABB aabb(0.0, 0.0, 10.0, 10.0);
    AABB expanded = aabb.expanded(2.0);

    EXPECT_DOUBLE_EQ(expanded.min.x, -2.0);
    EXPECT_DOUBLE_EQ(expanded.min.y, -2.0);
    EXPECT_DOUBLE_EQ(expanded.max.x, 12.0);
    EXPECT_DOUBLE_EQ(expanded.max.y, 12.0);
}

TEST(AABBTest, DistanceTo) {
    AABB aabb1(0.0, 0.0, 10.0, 10.0);
    AABB aabb2(15.0, 0.0, 20.0, 10.0);  // 右侧，距离 5
    AABB aabb3(0.0, 15.0, 10.0, 20.0);  // 上方，距离 5

    EXPECT_DOUBLE_EQ(aabb1.distance_to(aabb2), 5.0);
    EXPECT_DOUBLE_EQ(aabb1.distance_to(aabb3), 5.0);

    // 重叠的 AABB 距离为 0
    AABB aabb4(5.0, 5.0, 15.0, 15.0);
    EXPECT_DOUBLE_EQ(aabb1.distance_to(aabb4), 0.0);
}

TEST(AABBTest, Corner) {
    AABB aabb(0.0, 0.0, 10.0, 10.0);

    Vector2D corner0 = aabb.corner(0);  // 左下
    EXPECT_DOUBLE_EQ(corner0.x, 0.0);
    EXPECT_DOUBLE_EQ(corner0.y, 0.0);

    Vector2D corner1 = aabb.corner(1);  // 右下
    EXPECT_DOUBLE_EQ(corner1.x, 10.0);
    EXPECT_DOUBLE_EQ(corner1.y, 0.0);

    Vector2D corner2 = aabb.corner(2);  // 右上
    EXPECT_DOUBLE_EQ(corner2.x, 10.0);
    EXPECT_DOUBLE_EQ(corner2.y, 10.0);

    Vector2D corner3 = aabb.corner(3);  // 左上
    EXPECT_DOUBLE_EQ(corner3.x, 0.0);
    EXPECT_DOUBLE_EQ(corner3.y, 10.0);
}

TEST(AABBTest, IsValid) {
    AABB valid(0.0, 0.0, 10.0, 10.0);
    EXPECT_TRUE(valid.is_valid());

    AABB invalid(10.0, 10.0, 0.0, 0.0);
    EXPECT_FALSE(invalid.is_valid());
}
