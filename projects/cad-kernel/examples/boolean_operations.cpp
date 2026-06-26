// ============================================================
// Example 2: Boolean Operations Demo
//
// Demonstrates the three fundamental boolean operations:
// - Union (合并): A | B
// - Intersection (交集): A & B
// - Difference (差集): A - B
//
// Boolean operations are the core of CAD modeling, enabling
// complex shapes to be built from simple primitives.
// ============================================================

#include <iostream>
#include <memory>
#include <cmath>
#include "../src/brep.h"
#include "../src/geometry.h"
#include "../src/topology.h"
#include "../src/boolean.h"
#include "../src/mesh.h"

void printSeparator() {
    std::cout << "\n====================================================\n\n";
}

void printSolidInfo(Solid* solid) {
    std::cout << "  " << solid->name << ":\n";
    std::cout << "    V=" << solid->vertexCount() << " E=" << solid->edgeCount()
              << " F=" << solid->faceCount() << "\n";
    std::cout << "    Volume=" << solid->computeVolume() << "\n";
}

int main() {
    std::cout << "=== CAD Kernel: Boolean Operations Demo ===\n\n";

    // --------------------------------------------------------
    // Create two overlapping spheres
    // --------------------------------------------------------
    printSeparator();
    std::cout << "Test Case 1: Two Overlapping Spheres (两个相交球体)\n";

    auto sphereA = SolidBuilder::createSphere({-0.5, 0, 0}, 1.0, 24, 24);
    sphereA->name = "SphereA";

    auto sphereB = SolidBuilder::createSphere({0.5, 0, 0}, 1.0, 24, 24);
    sphereB->name = "SphereB";

    std::cout << "  Sphere A:\n";
    printSolidInfo(sphereA.get());
    std::cout << "  Sphere B:\n";
    printSolidInfo(sphereB.get());

    // --------------------------------------------------------
    // Union
    // --------------------------------------------------------
    printSeparator();
    std::cout << "  UNION (A | B):\n";
    auto unionResult = BooleanOps::unionSolids(sphereA.get(), sphereB.get());
    printSolidInfo(unionResult.get());

    // --------------------------------------------------------
    // Intersection
    // --------------------------------------------------------
    printSeparator();
    std::cout << "  INTERSECTION (A & B):\n";
    auto intersectResult = BooleanOps::intersectSolids(sphereA.get(), sphereB.get());
    printSolidInfo(intersectResult.get());

    // --------------------------------------------------------
    // Difference
    // --------------------------------------------------------
    printSeparator();
    std::cout << "  DIFFERENCE (A - B):\n";
    auto diffResult = BooleanOps::differenceSolids(sphereA.get(), sphereB.get());
    printSolidInfo(diffResult.get());

    // --------------------------------------------------------
    // Symmetric Difference
    // --------------------------------------------------------
    printSeparator();
    std::cout << "  SYMMETRIC DIFFERENCE:\n";
    auto symDiffResult = BooleanOps::symmetricDifference(sphereA.get(), sphereB.get());
    printSolidInfo(symDiffResult.get());

    // --------------------------------------------------------
    // Box-Box operations
    // --------------------------------------------------------
    printSeparator();
    std::cout << "Test Case 2: Two Overlapping Boxes (两个相交长方体)\n";

    auto boxA = SolidBuilder::createBox({-0.5, -0.5, -0.5}, 2.0, 2.0, 2.0);
    boxA->name = "BoxA";

    auto boxB = SolidBuilder::createBox({0.5, 0.5, 0.5}, 2.0, 2.0, 2.0);
    boxB->name = "BoxB";

    std::cout << "  Box A volume: " << boxA->computeVolume() << " (expected: 8.0)\n";
    std::cout << "  Box B volume: " << boxB->computeVolume() << " (expected: 8.0)\n";

    printSeparator();
    std::cout << "  UNION (BoxA | BoxB):\n";
    auto boxUnion = BooleanOps::unionSolids(boxA.get(), boxB.get());
    printSolidInfo(boxUnion.get());

    printSeparator();
    std::cout << "  DIFFERENCE (BoxA - BoxB):\n";
    auto boxDiff = BooleanOps::differenceSolids(boxA.get(), boxB.get());
    printSolidInfo(boxDiff.get());

    // --------------------------------------------------------
    // Sphere-Box operations
    // --------------------------------------------------------
    printSeparator();
    std::cout << "Test Case 3: Sphere-Box Intersection (球体-长方体相交)\n";

    auto sphere = SolidBuilder::createSphere({0, 0, 0}, 1.5, 24, 24);
    sphere->name = "Sphere(r=1.5)";
    sphere->computeVolume(); // Compute for reference

    auto box = SolidBuilder::createBox({-1.0, -1.0, -1.0}, 3.0, 3.0, 3.0);
    box->name = "Box(3x3x3)";
    box->computeVolume(); // Should be 27

    std::cout << "  Sphere volume: " << sphere->computeVolume()
              << " (expected: " << ((4.0/3.0) * M_PI * 3.375) << ")\n";
    std::cout << "  Box volume: " << box->computeVolume() << " (expected: 27.0)\n";

    printSeparator();
    std::cout << "  INTERSECTION (Sphere & Box):\n";
    auto sphereBoxIntersect = BooleanOps::intersectSolids(sphere.get(), box.get());
    printSolidInfo(sphereBoxIntersect.get());

    printSeparator();
    std::cout << "  DIFFERENCE (Box - Sphere):\n";
    auto sphereBoxDiff = BooleanOps::differenceSolids(box.get(), sphere.get());
    printSolidInfo(sphereBoxDiff.get());

    // --------------------------------------------------------
    // Cylinder-Box operations
    // --------------------------------------------------------
    printSeparator();
    std::cout << "Test Case 4: Cylinder-Box Intersection (圆柱体-长方体相交)\n";

    auto cyl = SolidBuilder::createCylinder({0, 0, 0}, {0, 0, 1}, 0.8, 3.0, 32);
    cyl->name = "Cylinder(r=0.8,h=3)";

    auto bigBox = SolidBuilder::createBox({-1.5, -1.5, -1.5}, 3.0, 3.0, 3.0);
    bigBox->name = "Box(3x3x3)";

    printSeparator();
    std::cout << "  DIFFERENCE (Box - Cylinder):\n";
    auto cylBoxDiff = BooleanOps::differenceSolids(bigBox.get(), cyl.get());
    printSolidInfo(cylBoxDiff.get());

    // --------------------------------------------------------
    // Summary
    // --------------------------------------------------------
    printSeparator();
    std::cout << "Summary (总结):\n";
    std::cout << "  - Demonstrated union, intersection, and difference operations\n";
    std::cout << "  - Tested on sphere-sphere, box-box, sphere-box, and cylinder-box pairs\n";
    std::cout << "  - Boolean operations are fundamental to CAD modeling\n";
    std::cout << "  - Production kernels use more sophisticated algorithms (CSG, plane clipping)\n";
    std::cout << "\n=== Done ===\n";

    return 0;
}
