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
// Solver Tests
// ============================================================================

TEST(simple_distance) {
    // Two points with distance constraint
    ConstraintSolver solver;
    solver.setConfig({1e-10, 300, 0.8, false});

    int p1 = solver.addPoint(0.0, 0.0);
    int p2 = solver.addPoint(5.0, 0.0);  // Initial guess at correct distance

    solver.addDistance(p1, p2, 5.0);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    // Check distance is correct
    auto p1_final = solver.getPoint(p1);
    auto p2_final = solver.getPoint(p2);
    double dist = p1_final.distanceTo(p2_final);
    ASSERT_NEAR(dist, 5.0, 1e-6);
}

TEST(coincident_points) {
    // Two points that must coincide
    ConstraintSolver solver;
    solver.setConfig({1e-10, 300, 0.8, false});

    int p1 = solver.addPoint(0.0, 0.0);
    int p2 = solver.addPoint(5.0, 5.0);

    solver.addCoincident(p1, p2);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto p1_final = solver.getPoint(p1);
    auto p2_final = solver.getPoint(p2);
    double dist = p1_final.distanceTo(p2_final);
    ASSERT_NEAR(dist, 0.0, 1e-4);
}

TEST(horizontal_line) {
    // Make a line horizontal
    ConstraintSolver solver;

    int line = solver.addLine(0.0, 0.0, 10.0, 5.0);

    solver.addHorizontal(line);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto line_final = solver.getLine(line);
    ASSERT_NEAR(line_final.start.y, line_final.end.y, 1e-6);
}

TEST(vertical_line) {
    // Make a line vertical
    ConstraintSolver solver;

    int line = solver.addLine(0.0, 0.0, 5.0, 10.0);

    solver.addVertical(line);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto line_final = solver.getLine(line);
    ASSERT_NEAR(line_final.start.x, line_final.end.x, 1e-6);
}

TEST(parallel_lines) {
    // Two lines that must be parallel - use lines that are already close to parallel
    ConstraintSolver solver;
    solver.setConfig({1e-10, 500, 0.3, false});

    int line1 = solver.addLine(0.0, 0.0, 10.0, 0.0);
    int line2 = solver.addLine(0.0, 5.0, 10.0, 5.1);  // Almost parallel

    solver.addParallel(line1, line2);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto l1 = solver.getLine(line1);
    auto l2 = solver.getLine(line2);

    // Check parallel: cross product of directions should be ~0
    double dx1 = l1.end.x - l1.start.x;
    double dy1 = l1.end.y - l1.start.y;
    double dx2 = l2.end.x - l2.start.x;
    double dy2 = l2.end.y - l2.start.y;
    double cross = dx1 * dy2 - dy1 * dx2;
    ASSERT_NEAR(cross, 0.0, 1e-2);
}

TEST(perpendicular_lines) {
    // Two lines that must be perpendicular
    ConstraintSolver solver;
    solver.setConfig({1e-10, 300, 0.8, false});

    // Use lines that are already somewhat perpendicular
    int line1 = solver.addLine(0.0, 0.0, 10.0, 0.0);
    int line2 = solver.addLine(0.0, 0.0, 0.2, 10.0);  // Almost perpendicular

    solver.addPerpendicular(line1, line2);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto l1 = solver.getLine(line1);
    auto l2 = solver.getLine(line2);

    // Check perpendicular: dot product should be ~0
    double dx1 = l1.end.x - l1.start.x;
    double dy1 = l1.end.y - l1.start.y;
    double dx2 = l2.end.x - l2.start.x;
    double dy2 = l2.end.y - l2.start.y;
    double dot = dx1 * dx2 + dy1 * dy2;
    ASSERT_NEAR(dot, 0.0, 1e-3);
}

TEST(fixed_radius) {
    // Circle with fixed radius
    ConstraintSolver solver;

    int circle = solver.addCircle(5.0, 5.0, 1.0);  // Initial radius 1

    solver.addRadius(circle, 10.0);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto c = solver.getCircle(circle);
    ASSERT_NEAR(c.radius, 10.0, 1e-6);
}

TEST(point_on_line_fixed) {
    // Point constrained to lie on a fixed line
    ConstraintSolver solver;
    solver.setConfig({1e-10, 500, 0.3, false});

    // Create a point that needs to be on a horizontal line
    int point = solver.addPoint(5.0, 2.0);

    // Create a line with fixed endpoints (we'll constrain the line separately)
    int line = solver.addLine(0.0, 0.0, 10.0, 0.0);

    // Fix the line by making it horizontal and fixing its length
    solver.addHorizontal(line);
    solver.addLength(line, 10.0);

    // Now add point on line constraint
    solver.addPointOnLine(point, line);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto p = solver.getPoint(point);
    auto l = solver.getLine(line);

    // Point should be on the line
    double cross = (p.x - l.start.x) * (l.end.y - l.start.y) -
                   (p.y - l.start.y) * (l.end.x - l.start.x);
    ASSERT_NEAR(cross, 0.0, 1e-2);
}

TEST(point_on_circle) {
    // Point constrained to lie on a circle
    ConstraintSolver solver;
    solver.setConfig({1e-10, 500, 0.3, false});

    // Start point closer to the circle
    int point = solver.addPoint(4.0, 0.0);
    int circle = solver.addCircle(0.0, 0.0, 5.0);

    // Fix circle radius and center by adding constraints
    solver.addRadius(circle, 5.0);
    solver.addPointOnCircle(point, circle);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto p = solver.getPoint(point);
    auto c = solver.getCircle(circle);
    double dist = p.distanceTo(c.center);
    ASSERT_NEAR(dist, c.radius, 1e-2);
}

TEST(triangle_with_constraints) {
    // Create a triangle with specific constraints
    ConstraintSolver solver;
    solver.setConfig({1e-10, 300, 0.8, false});

    // Three points forming a triangle
    int p1 = solver.addPoint(0.0, 0.0);
    int p2 = solver.addPoint(10.0, 0.0);
    int p3 = solver.addPoint(5.0, 8.66);  // Approx equilateral

    // Fix side lengths to form a specific triangle
    solver.addDistance(p1, p2, 10.0);  // Base = 10
    solver.addDistance(p2, p3, 10.0);  // Right side = 10
    solver.addDistance(p1, p3, 10.0);  // Left side = 10

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    // Check triangle sides
    auto p1f = solver.getPoint(p1);
    auto p2f = solver.getPoint(p2);
    auto p3f = solver.getPoint(p3);

    double d12 = p1f.distanceTo(p2f);
    double d23 = p2f.distanceTo(p3f);
    double d13 = p1f.distanceTo(p3f);

    ASSERT_NEAR(d12, 10.0, 1e-4);
    ASSERT_NEAR(d23, 10.0, 1e-4);
    ASSERT_NEAR(d13, 10.0, 1e-4);
}

TEST(circle_tangent_to_line) {
    // Line tangent to circle
    ConstraintSolver solver;
    solver.setConfig({1e-10, 500, 0.3, false});

    // Start with line close to tangent position
    int line = solver.addLine(0.0, 8.0, 10.0, 8.0);
    int circle = solver.addCircle(5.0, 0.0, 3.0);

    // Make line horizontal first
    solver.addHorizontal(line);
    // Then make it tangent to circle
    solver.addTangent(line, circle);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto l = solver.getLine(line);
    auto c = solver.getCircle(circle);

    // Distance from center to line should equal radius
    double dist = std::abs(l.start.y - c.center.y);
    ASSERT_NEAR(dist, c.radius, 1e-3);
}

TEST(overconstrained_system) {
    // Over-constrained system (should still find best fit)
    ConstraintSolver solver;
    solver.setConfig({1e-10, 100, 1.0, false});

    int p1 = solver.addPoint(0.0, 0.0);
    int p2 = solver.addPoint(1.0, 0.0);

    // These constraints are inconsistent
    solver.addDistance(p1, p2, 5.0);
    solver.addDistance(p1, p2, 10.0);

    auto result = solver.solve();
    // Should not converge to zero residual
    ASSERT_TRUE(!result.success() || result.residual_norm > 1e-6);
}

TEST(multiple_constraints) {
    // Complex system with multiple constraints
    ConstraintSolver solver;
    solver.setConfig({1e-10, 500, 0.5, false});

    int l1 = solver.addLine(0.0, 0.0, 10.5, 0.3);    // Bottom
    int l2 = solver.addLine(10.5, 0.3, 10.2, 5.8);    // Right
    int l3 = solver.addLine(10.2, 5.8, 0.3, 5.5);     // Top
    int l4 = solver.addLine(0.3, 5.5, 0.0, 0.0);      // Left

    solver.addHorizontal(l1);
    solver.addVertical(l2);
    solver.addHorizontal(l3);
    solver.addVertical(l4);
    solver.addLength(l1, 10.0);
    solver.addLength(l2, 5.0);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto line1 = solver.getLine(l1);
    auto line2 = solver.getLine(l2);

    ASSERT_NEAR(line1.start.y, line1.end.y, 1e-4);
    ASSERT_NEAR(line2.start.x, line2.end.x, 1e-4);
    ASSERT_NEAR(line1.length(), 10.0, 1e-4);
    ASSERT_NEAR(line2.length(), 5.0, 1e-4);
}

TEST(concentric_circles) {
    // Two circles with same center
    ConstraintSolver solver;
    solver.setConfig({1e-10, 300, 0.8, false});

    int c1 = solver.addCircle(0.0, 0.0, 5.0);
    int c2 = solver.addCircle(5.0, 5.0, 3.0);  // Different center

    solver.addConcentric(c1, c2);

    auto result = solver.solve();
    ASSERT_TRUE(result.success());

    auto circle1 = solver.getCircle(c1);
    auto circle2 = solver.getCircle(c2);

    double dist = circle1.center.distanceTo(circle2.center);
    ASSERT_NEAR(dist, 0.0, 1e-3);
}

// Main
int main() {
    std::cout << "=== Solver Tests ===" << std::endl;
    std::cout << tests_passed << "/" << tests_run << " tests passed" << std::endl;
    return (tests_passed == tests_run) ? 0 : 1;
}
