#include "../include/solver.h"
#include <iostream>
#include <iomanip>
#include <cmath>

using namespace cadsolver;

/**
 * @brief CAD Sketch Example - Creating a parametric rectangle
 *
 * This example demonstrates how to create a parametric rectangle
 * with constraints that maintain its geometric properties:
 * - Horizontal top and bottom edges
 * - Vertical left and right edges
 * - Fixed width and height
 */
void createRectangle() {
    std::cout << "=== Creating a Parametric Rectangle ===\n" << std::endl;

    ConstraintSolver solver;
    solver.setConfig({1e-10, 200, 0.8, false});

    // Define rectangle corners (slightly off to show constraint solving)
    int p1 = solver.addPoint(0.0, 0.0);    // Bottom-left
    int p2 = solver.addPoint(10.5, 0.3);   // Bottom-right (slightly off)
    int p3 = solver.addPoint(10.2, 5.8);   // Top-right (slightly off)
    int p4 = solver.addPoint(0.3, 5.5);    // Top-left (slightly off)

    // Create edges
    int bottom = solver.addLine(0.0, 0.0, 10.5, 0.3);
    int right  = solver.addLine(10.5, 0.3, 10.2, 5.8);
    int top    = solver.addLine(10.2, 5.8, 0.3, 5.5);
    int left   = solver.addLine(0.3, 5.5, 0.0, 0.0);

    // Apply geometric constraints
    solver.addHorizontal(bottom);  // Bottom edge horizontal
    solver.addHorizontal(top);     // Top edge horizontal
    solver.addVertical(right);     // Right edge vertical
    solver.addVertical(left);      // Left edge vertical

    // Apply dimensional constraints
    solver.addLength(bottom, 10.0);  // Width = 10
    solver.addLength(right, 5.0);    // Height = 5

    std::cout << "Constraints applied:" << std::endl;
    auto descriptions = solver.getConstraintDescriptions();
    for (const auto& desc : descriptions) {
        std::cout << "  - " << desc << std::endl;
    }

    std::cout << "\nSolving..." << std::endl;
    auto result = solver.solve();

    std::cout << "Result: " << result.message << std::endl;
    std::cout << "Residual norm: " << result.residual_norm << std::endl;

    if (result.success()) {
        std::cout << "\nRectangle vertices:" << std::endl;
        std::cout << "  P1 (bottom-left):  " << solver.getPoint(p1).toString() << std::endl;
        std::cout << "  P2 (bottom-right): " << solver.getPoint(p2).toString() << std::endl;
        std::cout << "  P3 (top-right):    " << solver.getPoint(p3).toString() << std::endl;
        std::cout << "  P4 (top-left):     " << solver.getPoint(p4).toString() << std::endl;

        std::cout << "\nEdge lengths:" << std::endl;
        std::cout << "  Bottom: " << solver.getLine(bottom).length() << std::endl;
        std::cout << "  Right:  " << solver.getLine(right).length() << std::endl;
        std::cout << "  Top:    " << solver.getLine(top).length() << std::endl;
        std::cout << "  Left:   " << solver.getLine(left).length() << std::endl;
    }
}

/**
 * @brief Creating a right triangle
 */
void createRightTriangle() {
    std::cout << "\n=== Creating a Right Triangle ===\n" << std::endl;

    ConstraintSolver solver;
    solver.setConfig({1e-10, 200, 0.8, false});

    // Triangle vertices
    int p1 = solver.addPoint(0.0, 0.0);    // Origin
    int p2 = solver.addPoint(8.0, 0.5);    // Base point (slightly off)
    int p3 = solver.addPoint(0.5, 6.0);    // Apex (slightly off)

    // Edges
    int base = solver.addLine(0.0, 0.0, 8.0, 0.5);
    int height = solver.addLine(0.0, 0.0, 0.5, 6.0);
    int hypotenuse = solver.addLine(0.5, 6.0, 8.0, 0.5);

    // Constraints
    solver.addHorizontal(base);           // Base is horizontal
    solver.addVertical(height);           // Height is vertical
    solver.addPerpendicular(base, height); // Right angle at origin
    solver.addLength(base, 8.0);          // Base = 8
    solver.addLength(height, 6.0);        // Height = 6

    std::cout << "Solving right triangle constraints..." << std::endl;
    auto result = solver.solve();

    if (result.success()) {
        std::cout << "Triangle vertices:" << std::endl;
        std::cout << "  P1 (right angle): " << solver.getPoint(p1).toString() << std::endl;
        std::cout << "  P2 (base end):    " << solver.getPoint(p2).toString() << std::endl;
        std::cout << "  P3 (apex):        " << solver.getPoint(p3).toString() << std::endl;

        std::cout << "\nSide lengths:" << std::endl;
        std::cout << "  Base:       " << solver.getLine(base).length() << std::endl;
        std::cout << "  Height:     " << solver.getLine(height).length() << std::endl;
        std::cout << "  Hypotenuse: " << solver.getLine(hypotenuse).length() << std::endl;

        // Verify right angle
        double angle = solver.getLine(base).angleWith(solver.getLine(height));
        std::cout << "\nAngle at origin: " << (angle * 180.0 / M_PI) << " degrees" << std::endl;
    }
}

/**
 * @brief Creating a circle with tangent line
 */
void createTangentExample() {
    std::cout << "\n=== Circle with Tangent Line ===\n" << std::endl;

    ConstraintSolver solver;
    solver.setConfig({1e-10, 200, 0.5, false});

    // Circle at origin with radius 5
    int circle = solver.addCircle(0.0, 0.0, 5.0);

    // Line that should be tangent to circle
    // Start with line at y=8 (not tangent)
    int line = solver.addLine(0.0, 8.0, 10.0, 8.0);

    // Constraints
    solver.addRadius(circle, 5.0);
    solver.addHorizontal(line);
    solver.addTangent(line, circle);

    std::cout << "Solving tangent constraint..." << std::endl;
    auto result = solver.solve();

    if (result.success()) {
        auto c = solver.getCircle(circle);
        auto l = solver.getLine(line);

        std::cout << "Circle: " << c.toString() << std::endl;
        std::cout << "Line: " << l.toString() << std::endl;
        std::cout << "Distance from center to line: "
                  << std::abs(l.start.y - c.center.y) << std::endl;
        std::cout << "Circle radius: " << c.radius << std::endl;
    }
}

/**
 * @brief Creating concentric circles
 */
void createConcentricCircles() {
    std::cout << "\n=== Concentric Circles ===\n" << std::endl;

    ConstraintSolver solver;
    solver.setConfig({1e-10, 200, 0.8, false});

    // Two circles at different positions
    int c1 = solver.addCircle(0.0, 0.0, 3.0);
    int c2 = solver.addCircle(10.0, 10.0, 5.0);

    // Make them concentric
    solver.addConcentric(c1, c2);
    solver.addRadius(c1, 3.0);
    solver.addRadius(c2, 5.0);

    std::cout << "Solving concentric constraint..." << std::endl;
    auto result = solver.solve();

    if (result.success()) {
        auto circle1 = solver.getCircle(c1);
        auto circle2 = solver.getCircle(c2);

        std::cout << "Circle 1: " << circle1.toString() << std::endl;
        std::cout << "Circle 2: " << circle2.toString() << std::endl;
        std::cout << "Distance between centers: "
                  << circle1.center.distanceTo(circle2.center) << std::endl;
    }
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  CAD Constraint Solver - Sketch Demo" << std::endl;
    std::cout << "========================================\n" << std::endl;

    createRectangle();
    createRightTriangle();
    createTangentExample();
    createConcentricCircles();

    std::cout << "\n========================================" << std::endl;
    std::cout << "  All CAD sketch examples completed!" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
