#include "../include/solver.h"
#include <iostream>
#include <iomanip>

using namespace cadsolver;

void printSeparator(const std::string& title) {
    std::cout << "\n========================================" << std::endl;
    std::cout << "  " << title << std::endl;
    std::cout << "========================================\n" << std::endl;
}

void example_distance() {
    printSeparator("Example 1: Distance Constraint");

    ConstraintSolver solver;
    solver.setConfig({1e-10, 100, 1.0, true});

    // Create two points
    int p1 = solver.addPoint(0.0, 0.0);
    int p2 = solver.addPoint(1.0, 0.0);

    // Constrain distance to 5 units
    solver.addDistance(p1, p2, 5.0);

    std::cout << "Initial state:" << std::endl;
    std::cout << "  P1: " << solver.getPoint(p1).toString() << std::endl;
    std::cout << "  P2: " << solver.getPoint(p2).toString() << std::endl;

    auto result = solver.solve();

    std::cout << "\nResult: " << result.message << std::endl;
    std::cout << "Final state:" << std::endl;
    std::cout << "  P1: " << solver.getPoint(p1).toString() << std::endl;
    std::cout << "  P2: " << solver.getPoint(p2).toString() << std::endl;
    std::cout << "  Distance: " << solver.getPoint(p1).distanceTo(solver.getPoint(p2)) << std::endl;
}

void example_coincident() {
    printSeparator("Example 2: Coincident Points");

    ConstraintSolver solver;

    int p1 = solver.addPoint(0.0, 0.0);
    int p2 = solver.addPoint(10.0, 10.0);

    solver.addCoincident(p1, p2);

    std::cout << "Initial state:" << std::endl;
    std::cout << "  P1: " << solver.getPoint(p1).toString() << std::endl;
    std::cout << "  P2: " << solver.getPoint(p2).toString() << std::endl;

    auto result = solver.solve();

    std::cout << "\nResult: " << result.message << std::endl;
    std::cout << "Final state:" << std::endl;
    std::cout << "  P1: " << solver.getPoint(p1).toString() << std::endl;
    std::cout << "  P2: " << solver.getPoint(p2).toString() << std::endl;
}

void example_parallel_lines() {
    printSeparator("Example 3: Parallel Lines");

    ConstraintSolver solver;

    // Two lines that are not parallel
    int line1 = solver.addLine(0.0, 0.0, 10.0, 0.0);
    int line2 = solver.addLine(0.0, 5.0, 10.0, 8.0);

    solver.addParallel(line1, line2);

    std::cout << "Initial state:" << std::endl;
    std::cout << "  Line1: " << solver.getLine(line1).toString() << std::endl;
    std::cout << "  Line2: " << solver.getLine(line2).toString() << std::endl;

    auto result = solver.solve();

    std::cout << "\nResult: " << result.message << std::endl;
    std::cout << "Final state:" << std::endl;
    std::cout << "  Line1: " << solver.getLine(line1).toString() << std::endl;
    std::cout << "  Line2: " << solver.getLine(line2).toString() << std::endl;
}

void example_perpendicular_lines() {
    printSeparator("Example 4: Perpendicular Lines");

    ConstraintSolver solver;

    // Two lines that are not perpendicular
    int line1 = solver.addLine(0.0, 0.0, 10.0, 0.0);
    int line2 = solver.addLine(0.0, 0.0, 5.0, 5.0);  // 45 degrees

    solver.addPerpendicular(line1, line2);

    std::cout << "Initial state:" << std::endl;
    std::cout << "  Line1: " << solver.getLine(line1).toString() << std::endl;
    std::cout << "  Line2: " << solver.getLine(line2).toString() << std::endl;
    std::cout << "  Angle: " << (solver.getLine(line1).angleWith(solver.getLine(line2)) * 180.0 / M_PI) << " degrees" << std::endl;

    auto result = solver.solve();

    std::cout << "\nResult: " << result.message << std::endl;
    std::cout << "Final state:" << std::endl;
    std::cout << "  Line1: " << solver.getLine(line1).toString() << std::endl;
    std::cout << "  Line2: " << solver.getLine(line2).toString() << std::endl;
    std::cout << "  Angle: " << (solver.getLine(line1).angleWith(solver.getLine(line2)) * 180.0 / M_PI) << " degrees" << std::endl;
}

void example_fixed_radius() {
    printSeparator("Example 5: Fixed Circle Radius");

    ConstraintSolver solver;

    int circle = solver.addCircle(5.0, 5.0, 1.0);

    solver.addRadius(circle, 10.0);

    std::cout << "Initial state:" << std::endl;
    std::cout << "  Circle: " << solver.getCircle(circle).toString() << std::endl;

    auto result = solver.solve();

    std::cout << "\nResult: " << result.message << std::endl;
    std::cout << "Final state:" << std::endl;
    std::cout << "  Circle: " << solver.getCircle(circle).toString() << std::endl;
}

void example_point_on_line() {
    printSeparator("Example 6: Point on Line");

    ConstraintSolver solver;

    int point = solver.addPoint(5.0, 10.0);
    int line = solver.addLine(0.0, 0.0, 10.0, 0.0);

    solver.addPointOnLine(point, line);

    std::cout << "Initial state:" << std::endl;
    std::cout << "  Point: " << solver.getPoint(point).toString() << std::endl;
    std::cout << "  Line: " << solver.getLine(line).toString() << std::endl;

    auto result = solver.solve();

    std::cout << "\nResult: " << result.message << std::endl;
    std::cout << "Final state:" << std::endl;
    std::cout << "  Point: " << solver.getPoint(point).toString() << std::endl;
    std::cout << "  Line: " << solver.getLine(line).toString() << std::endl;
}

int main() {
    std::cout << "=== CAD Constraint Solver Examples ===" << std::endl;

    example_distance();
    example_coincident();
    example_parallel_lines();
    example_perpendicular_lines();
    example_fixed_radius();
    example_point_on_line();

    std::cout << "\n=== All examples completed ===" << std::endl;

    return 0;
}
