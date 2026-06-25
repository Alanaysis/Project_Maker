#include "../include/solver.h"
#include <iostream>
#include <iomanip>
#include <cmath>

using namespace cadsolver;

/**
 * @brief Tangent constraint demonstrations
 *
 * Shows various tangent constraint scenarios:
 * 1. Line tangent to circle
 * 2. Two circles externally tangent
 * 3. Two circles internally tangent
 */
void demoLineTangentToCircle() {
    std::cout << "=== Demo 1: Line Tangent to Circle ===\n" << std::endl;

    ConstraintSolver solver;
    solver.setConfig({1e-10, 200, 0.5, false});

    // Circle at (0, 0) with radius 5
    int circle = solver.addCircle(0.0, 0.0, 5.0);
    solver.addRadius(circle, 5.0);

    // Horizontal line that should be tangent
    int line1 = solver.addLine(0.0, 8.0, 10.0, 8.0);  // Above circle
    solver.addHorizontal(line1);
    solver.addTangent(line1, circle);

    std::cout << "Line 1 (above circle):" << std::endl;
    auto result1 = solver.solve();
    if (result1.success()) {
        auto l = solver.getLine(line1);
        std::cout << "  Final position: " << l.toString() << std::endl;
        std::cout << "  Distance from center: " << std::abs(l.start.y) << std::endl;
    }

    // Another line tangent from below
    ConstraintSolver solver2;
    solver2.setConfig({1e-10, 200, 0.5, false});

    int circle2 = solver2.addCircle(0.0, 0.0, 5.0);
    solver2.addRadius(circle2, 5.0);

    int line2 = solver2.addLine(0.0, -8.0, 10.0, -8.0);  // Below circle
    solver2.addHorizontal(line2);
    solver2.addTangent(line2, circle2);

    std::cout << "\nLine 2 (below circle):" << std::endl;
    auto result2 = solver2.solve();
    if (result2.success()) {
        auto l = solver2.getLine(line2);
        std::cout << "  Final position: " << l.toString() << std::endl;
        std::cout << "  Distance from center: " << std::abs(l.start.y) << std::endl;
    }
}

void demoExternalTangent() {
    std::cout << "\n=== Demo 2: Two Circles Externally Tangent ===\n" << std::endl;

    ConstraintSolver solver;
    solver.setConfig({1e-10, 200, 0.5, false});

    // Two circles at different positions
    int c1 = solver.addCircle(0.0, 0.0, 3.0);
    int c2 = solver.addCircle(10.0, 0.0, 5.0);

    solver.addRadius(c1, 3.0);
    solver.addRadius(c2, 5.0);
    solver.addTangent(c1, c2, true);  // External tangent

    std::cout << "Initial circles:" << std::endl;
    std::cout << "  C1: " << solver.getCircle(c1).toString() << std::endl;
    std::cout << "  C2: " << solver.getCircle(c2).toString() << std::endl;

    auto result = solver.solve();

    std::cout << "\nResult: " << result.message << std::endl;
    if (result.success()) {
        auto circle1 = solver.getCircle(c1);
        auto circle2 = solver.getCircle(c2);

        std::cout << "Final circles:" << std::endl;
        std::cout << "  C1: " << circle1.toString() << std::endl;
        std::cout << "  C2: " << circle2.toString() << std::endl;

        double dist = circle1.center.distanceTo(circle2.center);
        double expected = circle1.radius + circle2.radius;
        std::cout << "\nDistance between centers: " << dist << std::endl;
        std::cout << "Expected (r1 + r2):      " << expected << std::endl;
        std::cout << "Difference:              " << std::abs(dist - expected) << std::endl;
    }
}

void demoInternalTangent() {
    std::cout << "\n=== Demo 3: Two Circles Internally Tangent ===\n" << std::endl;

    ConstraintSolver solver;
    solver.setConfig({1e-10, 200, 0.5, false});

    // Large circle at origin
    int c1 = solver.addCircle(0.0, 0.0, 10.0);
    // Small circle inside, not at center
    int c2 = solver.addCircle(5.0, 0.0, 3.0);

    solver.addRadius(c1, 10.0);
    solver.addRadius(c2, 3.0);
    solver.addTangent(c1, c2, false);  // Internal tangent

    std::cout << "Initial circles:" << std::endl;
    std::cout << "  C1 (outer): " << solver.getCircle(c1).toString() << std::endl;
    std::cout << "  C2 (inner): " << solver.getCircle(c2).toString() << std::endl;

    auto result = solver.solve();

    std::cout << "\nResult: " << result.message << std::endl;
    if (result.success()) {
        auto circle1 = solver.getCircle(c1);
        auto circle2 = solver.getCircle(c2);

        std::cout << "Final circles:" << std::endl;
        std::cout << "  C1 (outer): " << circle1.toString() << std::endl;
        std::cout << "  C2 (inner): " << circle2.toString() << std::endl;

        double dist = circle1.center.distanceTo(circle2.center);
        double expected = circle1.radius - circle2.radius;
        std::cout << "\nDistance between centers: " << dist << std::endl;
        std::cout << "Expected (r1 - r2):      " << expected << std::endl;
        std::cout << "Difference:              " << std::abs(dist - expected) << std::endl;
    }
}

void demoPointOnCircle() {
    std::cout << "\n=== Demo 4: Point on Circle ===\n" << std::endl;

    ConstraintSolver solver;
    solver.setConfig({1e-10, 200, 0.8, false});

    // Circle at origin with radius 5
    int circle = solver.addCircle(0.0, 0.0, 5.0);
    solver.addRadius(circle, 5.0);

    // Point that should lie on circle (start closer to the circle)
    int point = solver.addPoint(3.0, 0.0);
    solver.addPointOnCircle(point, circle);

    std::cout << "Initial point: " << solver.getPoint(point).toString() << std::endl;

    auto result = solver.solve();

    std::cout << "Result: " << result.message << std::endl;
    if (result.success()) {
        auto p = solver.getPoint(point);
        auto c = solver.getCircle(circle);

        std::cout << "Final point: " << p.toString() << std::endl;
        std::cout << "Circle: " << c.toString() << std::endl;

        double dist = p.distanceTo(c.center);
        std::cout << "Distance from center: " << dist << std::endl;
        std::cout << "Circle radius: " << c.radius << std::endl;
    }
}

void demoMultipleTangents() {
    std::cout << "\n=== Demo 5: Chain of Tangent Circles ===\n" << std::endl;

    ConstraintSolver solver;
    solver.setConfig({1e-10, 300, 0.5, false});

    // Three circles in a chain
    int c1 = solver.addCircle(0.0, 0.0, 3.0);
    int c2 = solver.addCircle(10.0, 0.0, 4.0);
    int c3 = solver.addCircle(20.0, 0.0, 5.0);

    solver.addRadius(c1, 3.0);
    solver.addRadius(c2, 4.0);
    solver.addRadius(c3, 5.0);

    // c1 tangent to c2, c2 tangent to c3
    solver.addTangent(c1, c2, true);
    solver.addTangent(c2, c3, true);

    std::cout << "Initial circles:" << std::endl;
    std::cout << "  C1: " << solver.getCircle(c1).toString() << std::endl;
    std::cout << "  C2: " << solver.getCircle(c2).toString() << std::endl;
    std::cout << "  C3: " << solver.getCircle(c3).toString() << std::endl;

    auto result = solver.solve();

    std::cout << "\nResult: " << result.message << std::endl;
    if (result.success()) {
        auto circle1 = solver.getCircle(c1);
        auto circle2 = solver.getCircle(c2);
        auto circle3 = solver.getCircle(c3);

        std::cout << "Final circles:" << std::endl;
        std::cout << "  C1: " << circle1.toString() << std::endl;
        std::cout << "  C2: " << circle2.toString() << std::endl;
        std::cout << "  C3: " << circle3.toString() << std::endl;

        double dist12 = circle1.center.distanceTo(circle2.center);
        double dist23 = circle2.center.distanceTo(circle3.center);

        std::cout << "\nDistances:" << std::endl;
        std::cout << "  C1-C2: " << dist12 << " (expected: "
                  << (circle1.radius + circle2.radius) << ")" << std::endl;
        std::cout << "  C2-C3: " << dist23 << " (expected: "
                  << (circle2.radius + circle3.radius) << ")" << std::endl;
    }
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  Tangent Constraint Demonstrations" << std::endl;
    std::cout << "========================================\n" << std::endl;

    demoLineTangentToCircle();
    demoExternalTangent();
    demoInternalTangent();
    demoPointOnCircle();
    demoMultipleTangents();

    std::cout << "\n========================================" << std::endl;
    std::cout << "  All tangent demos completed!" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
