#include "../include/solver.h"
#include <iostream>
#include <cassert>
#include <cmath>

using namespace cadsolver;

// Simple test framework
int tests_run = 0;
int tests_passed = 0;

#define TEST(name) \
    void test_##name(); \
    struct TestRunner_##name { \
        TestRunner_##name() { \
            std::cout << "Running " #name "... "; \
            tests_run++; \
            try { \
                test_##name(); \
                tests_passed++; \
                std::cout << "PASSED" << std::endl; \
            } catch (const std::exception& e) { \
                std::cout << "FAILED: " << e.what() << std::endl; \
            } \
        } \
    } runner_##name; \
    void test_##name()

#define ASSERT_NEAR(a, b, eps) \
    if (std::abs((a) - (b)) > (eps)) { \
        throw std::runtime_error("Assertion failed: " + std::to_string(a) + \
                                " != " + std::to_string(b) + \
                                " (diff=" + std::to_string(std::abs((a)-(b))) + ")"); \
    }

#define ASSERT_TRUE(expr) \
    if (!(expr)) { \
        throw std::runtime_error("Assertion failed: " #expr); \
    }

// ============================================================================
// Geometry Tests
// ============================================================================

TEST(point_distance) {
    Point2D p1(0, 0), p2(3, 4);
    ASSERT_NEAR(p1.distanceTo(p2), 5.0, 1e-10);
    ASSERT_NEAR(p1.distanceSquaredTo(p2), 25.0, 1e-10);
}

TEST(point_operations) {
    Point2D p1(1, 2), p2(3, 4);
    auto sum = p1 + p2;
    ASSERT_NEAR(sum.x, 4.0, 1e-10);
    ASSERT_NEAR(sum.y, 6.0, 1e-10);

    auto diff = p2 - p1;
    ASSERT_NEAR(diff.x, 2.0, 1e-10);
    ASSERT_NEAR(diff.y, 2.0, 1e-10);

    auto scaled = p1 * 3.0;
    ASSERT_NEAR(scaled.x, 3.0, 1e-10);
    ASSERT_NEAR(scaled.y, 6.0, 1e-10);
}

TEST(point_dot_cross) {
    Point2D p1(1, 0), p2(0, 1);
    ASSERT_NEAR(p1.dot(p2), 0.0, 1e-10);
    ASSERT_NEAR(p1.cross(p2), 1.0, 1e-10);
}

TEST(line_angle) {
    Line2D l1(Point2D(0, 0), Point2D(1, 0));
    Line2D l2(Point2D(0, 0), Point2D(0, 1));
    ASSERT_NEAR(l1.angleWith(l2), M_PI / 2.0, 1e-10);

    Line2D l3(Point2D(0, 0), Point2D(1, 1));
    ASSERT_NEAR(l1.angleWith(l3), M_PI / 4.0, 1e-10);
}

TEST(line_closest_point) {
    Line2D line(Point2D(0, 0), Point2D(10, 0));
    Point2D p(5, 5);
    auto closest = line.closestPointTo(p);
    ASSERT_NEAR(closest.x, 5.0, 1e-10);
    ASSERT_NEAR(closest.y, 0.0, 1e-10);
    ASSERT_NEAR(line.distanceToPoint(p), 5.0, 1e-10);
}

TEST(circle_contains) {
    Circle2D circle(Point2D(0, 0), 5.0);
    ASSERT_TRUE(circle.containsPoint(Point2D(0, 0)));
    ASSERT_TRUE(circle.containsPoint(Point2D(3, 4)));
    ASSERT_TRUE(!circle.containsPoint(Point2D(10, 10)));
}

// ============================================================================
// Constraint Residual Tests
// ============================================================================

TEST(coincident_constraint) {
    // Two points at same location - should have zero residual
    std::vector<double> params = {1.0, 2.0, 1.0, 2.0};
    CoincidentConstraint c(0, 2);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // Points apart - should have non-zero residual
    params = {0.0, 0.0, 3.0, 4.0};
    ASSERT_NEAR(c.residual(params), 25.0, 1e-10);
}

TEST(distance_constraint) {
    // Distance of 5 between (0,0) and (3,4)
    std::vector<double> params = {0.0, 0.0, 3.0, 4.0};
    DistanceConstraint c(0, 2, 5.0);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // Wrong distance
    params = {0.0, 0.0, 1.0, 0.0};
    ASSERT_NEAR(c.residual(params), 1.0 - 25.0, 1e-10);
}

TEST(horizontal_constraint) {
    // Horizontal line
    std::vector<double> params = {0.0, 5.0, 10.0, 5.0};
    HorizontalConstraint c(0);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // Non-horizontal line
    params = {0.0, 0.0, 10.0, 5.0};
    ASSERT_NEAR(c.residual(params), -5.0, 1e-10);
}

TEST(vertical_constraint) {
    // Vertical line
    std::vector<double> params = {5.0, 0.0, 5.0, 10.0};
    VerticalConstraint c(0);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // Non-vertical line
    params = {0.0, 0.0, 5.0, 10.0};
    ASSERT_NEAR(c.residual(params), -5.0, 1e-10);
}

TEST(parallel_constraint) {
    // Two horizontal lines (parallel)
    std::vector<double> params = {0.0, 0.0, 10.0, 0.0,
                                  0.0, 5.0, 10.0, 5.0};
    ParallelConstraint c(0, 4);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // Two vertical lines (parallel)
    params = {0.0, 0.0, 0.0, 10.0,
              5.0, 0.0, 5.0, 10.0};
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // Non-parallel lines
    params = {0.0, 0.0, 10.0, 0.0,
              0.0, 0.0, 0.0, 10.0};
    ASSERT_NEAR(c.residual(params), 100.0, 1e-10);
}

TEST(perpendicular_constraint) {
    // Horizontal and vertical lines (perpendicular)
    std::vector<double> params = {0.0, 0.0, 10.0, 0.0,
                                  0.0, 0.0, 0.0, 10.0};
    PerpendicularConstraint c(0, 4);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // Two horizontal lines (not perpendicular)
    params = {0.0, 0.0, 10.0, 0.0,
              0.0, 5.0, 10.0, 5.0};
    ASSERT_NEAR(c.residual(params), 100.0, 1e-10);
}

TEST(radius_constraint) {
    // Circle with radius 5
    std::vector<double> params = {0.0, 0.0, 5.0};
    RadiusConstraint c(0, 5.0);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // Wrong radius
    params = {0.0, 0.0, 3.0};
    ASSERT_NEAR(c.residual(params), -2.0, 1e-10);
}

TEST(point_on_line_constraint) {
    // Point (5, 0) on line from (0,0) to (10,0)
    std::vector<double> params = {5.0, 0.0, 0.0, 0.0, 10.0, 0.0};
    PointOnLineConstraint c(0, 2);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // Point not on line - residual should be non-zero
    params = {5.0, 5.0, 0.0, 0.0, 10.0, 0.0};
    ASSERT_TRUE(std::abs(c.residual(params)) > 1e-6);
}

TEST(point_on_circle_constraint) {
    // Point (3, 4) on circle at origin with radius 5
    std::vector<double> params = {3.0, 4.0, 0.0, 0.0, 5.0};
    PointOnCircleConstraint c(0, 2);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // Point not on circle
    params = {1.0, 0.0, 0.0, 0.0, 5.0};
    ASSERT_NEAR(c.residual(params), 1.0 - 25.0, 1e-10);
}

TEST(length_constraint) {
    // Line of length 5
    std::vector<double> params = {0.0, 0.0, 3.0, 4.0};
    LengthConstraint c(0, 5.0);
    ASSERT_NEAR(c.residual(params), 0.0, 1e-10);

    // Wrong length
    params = {0.0, 0.0, 1.0, 0.0};
    ASSERT_NEAR(c.residual(params), 1.0 - 25.0, 1e-10);
}

// ============================================================================
// Gradient Tests
// ============================================================================

TEST(distance_gradient) {
    std::vector<double> params = {0.0, 0.0, 3.0, 4.0};
    DistanceConstraint c(0, 2, 5.0);

    auto grad = c.gradient(params);
    double eps = 1e-8;
    double f0 = c.residual(params);

    // Numerical gradient check
    for (size_t i = 0; i < params.size(); ++i) {
        std::vector<double> p_plus = params;
        p_plus[i] += eps;
        double numerical = (c.residual(p_plus) - f0) / eps;
        ASSERT_NEAR(grad[i], numerical, 1e-5);
    }
}

TEST(horizontal_gradient) {
    std::vector<double> params = {0.0, 3.0, 10.0, 7.0};
    HorizontalConstraint c(0);

    auto grad = c.gradient(params);
    double eps = 1e-8;
    double f0 = c.residual(params);

    for (size_t i = 0; i < params.size(); ++i) {
        std::vector<double> p_plus = params;
        p_plus[i] += eps;
        double numerical = (c.residual(p_plus) - f0) / eps;
        ASSERT_NEAR(grad[i], numerical, 1e-5);
    }
}

TEST(perpendicular_gradient) {
    std::vector<double> params = {0.0, 0.0, 10.0, 0.0,
                                  0.0, 0.0, 0.0, 10.0};
    PerpendicularConstraint c(0, 4);

    auto grad = c.gradient(params);
    double eps = 1e-8;
    double f0 = c.residual(params);

    for (size_t i = 0; i < params.size(); ++i) {
        std::vector<double> p_plus = params;
        p_plus[i] += eps;
        double numerical = (c.residual(p_plus) - f0) / eps;
        ASSERT_NEAR(grad[i], numerical, 1e-4);
    }
}

// Main
int main() {
    std::cout << "=== Constraint Tests ===" << std::endl;
    std::cout << tests_passed << "/" << tests_run << " tests passed" << std::endl;
    return (tests_passed == tests_run) ? 0 : 1;
}
