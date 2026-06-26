// ============================================================
// Example 1: Basic Solid Modeling
//
// Demonstrates creating basic CAD primitives (box, cylinder,
// sphere, torus) and computing their properties (volume,
// surface area, Euler characteristic).
// ============================================================

#include <iostream>
#include <memory>
#include <cmath>
#include "../src/brep.h"
#include "../src/geometry.h"
#include "../src/topology.h"
#include "../src/mesh.h"

void printSeparator() {
    std::cout << "\n====================================================\n\n";
}

void printSolidInfo(Solid* solid) {
    std::cout << "  Solid: " << solid->name << "\n";
    std::cout << "    Vertices: " << solid->vertexCount() << "\n";
    std::cout << "    Edges:    " << solid->edgeCount() << "\n";
    std::cout << "    Faces:    " << solid->faceCount() << "\n";
    std::cout << "    Shells:   " << solid->shellCount() << "\n";
    std::cout << "    Volume:   " << solid->computeVolume() << "\n";
    std::cout << "    Surface Area: " << solid->computeSurfaceArea() << "\n";
    std::cout << "    Euler (V-E+F): " << solid->vertexCount() << " - "
              << solid->edgeCount() << " + " << solid->faceCount()
              << " = " << (solid->vertexCount() - solid->edgeCount() + solid->faceCount())
              << " (expected: 2 for convex solid)\n";
    std::cout << "    Validity: " << (solid->validate() == TopoStatus::VALID ? "VALID" : "INVALID") << "\n";
}

int main() {
    std::cout << "=== CAD Kernel: Basic Solid Modeling ===\n\n";

    // --------------------------------------------------------
    // 1. Create a box (rectangular prism)
    // --------------------------------------------------------
    printSeparator();
    std::cout << "1. Box (长方体)\n";

    auto box = SolidBuilder::createBox({0, 0, 0}, 2.0, 3.0, 4.0);
    box->name = "Box(2x3x4)";
    printSolidInfo(box.get());
    // Box: V=8, E=12, F=6, V-E+F = 2 (correct for convex solid)

    // --------------------------------------------------------
    // 2. Create a cylinder
    // --------------------------------------------------------
    printSeparator();
    std::cout << "2. Cylinder (圆柱体)\n";

    auto cylinder = SolidBuilder::createCylinder(
        {0, 0, 0}, {0, 0, 1}, 1.0, 3.0, 32);
    cylinder->name = "Cylinder(r=1,h=3)";
    printSolidInfo(cylinder.get());
    // Expected volume: pi * r^2 * h = pi * 1 * 3 ≈ 9.425
    std::cout << "  Expected volume: " << (M_PI * 1.0 * 1.0 * 3.0) << "\n";

    // --------------------------------------------------------
    // 3. Create a sphere
    // --------------------------------------------------------
    printSeparator();
    std::cout << "3. Sphere (球体)\n";

    auto sphere = SolidBuilder::createSphere({0, 0, 0}, 2.0, 24, 24);
    sphere->name = "Sphere(r=2)";
    printSolidInfo(sphere.get());
    // Expected volume: (4/3) * pi * r^3 = (4/3) * pi * 8 ≈ 33.51
    std::cout << "  Expected volume: " << ((4.0/3.0) * M_PI * 8.0) << "\n";
    // Expected surface area: 4 * pi * r^2 = 4 * pi * 4 ≈ 50.27
    std::cout << "  Expected surface area: " << (4.0 * M_PI * 4.0) << "\n";

    // --------------------------------------------------------
    // 4. Create a torus
    // --------------------------------------------------------
    printSeparator();
    std::cout << "4. Torus (环面)\n";

    auto torus = SolidBuilder::createTorus({0, 0, 0}, {0, 0, 1}, 2.0, 0.5, 32, 16);
    torus->name = "Torus(R=2,r=0.5)";
    printSolidInfo(torus.get());
    // Expected volume: 2 * pi^2 * R * r^2 = 2 * pi^2 * 2 * 0.25 ≈ 9.87
    std::cout << "  Expected volume: " << (2.0 * M_PI * M_PI * 2.0 * 0.25) << "\n";

    // --------------------------------------------------------
    // 5. Create a prism (extruded polygon)
    // --------------------------------------------------------
    printSeparator();
    std::cout << "5. Hexagonal Prism (六角柱)\n";

    std::vector<Point3D> hexBase;
    for (int i = 0; i < 6; ++i) {
        double angle = 2.0 * M_PI * i / 6;
        hexBase.push_back({std::cos(angle), std::sin(angle), 0});
    }

    auto prism = SolidBuilder::createPrism(hexBase, 3.0, {0, 0, 1});
    prism->name = "HexPrism(h=3)";
    printSolidInfo(prism.get());

    // --------------------------------------------------------
    // 6. B-rep container
    // --------------------------------------------------------
    printSeparator();
    std::cout << "6. B-rep Container (B-rep 容器)\n";

    BRep brep("Learning Project");
    brep.addSolid(std::move(box));
    brep.addSolid(std::move(cylinder));
    brep.addSolid(std::move(sphere));
    brep.addSolid(std::move(torus));
    brep.addSolid(std::move(prism));

    std::cout << brep.toString() << "\n";
    std::cout << "  Total solids: " << brep.solids.size() << "\n";

    auto allVerts = brep.allVertices();
    auto allEdges = brep.allEdges();
    auto allFaces = brep.allFaces();

    std::cout << "  Total vertices: " << allVerts.size() << "\n";
    std::cout << "  Total edges: " << allEdges.size() << "\n";
    std::cout << "  Total faces: " << allFaces.size() << "\n";

    // --------------------------------------------------------
    // 7. Mesh generation
    // --------------------------------------------------------
    printSeparator();
    std::cout << "7. Mesh Generation (网格生成)\n";

    auto sphereMesh = MeshGenerator::generateSphereMesh({0, 0, 0}, 1.0, 24, 24);
    std::cout << "  Sphere mesh (r=1, 24x24 segments):\n";
    sphereMesh.printStats();
    std::cout << "  Expected surface area: " << (4.0 * M_PI) << "\n";

    auto torusMesh = MeshGenerator::generateTorusMesh(
        {0, 0, 0}, {0, 0, 1}, 2.0, 0.5, 32, 16);
    std::cout << "  Torus mesh (R=2, r=0.5, 32x16 segments):\n";
    torusMesh.printStats();

    // Export meshes
    sphereMesh.exportSTL("sphere.stl");
    std::cout << "  Exported sphere.stl\n";

    torusMesh.exportSTL("torus.stl");
    std::cout << "  Exported torus.stl\n";

    sphereMesh.exportSTLAscii("sphere_ascii.stl");
    std::cout << "  Exported sphere_ascii.stl\n";

    // --------------------------------------------------------
    // Summary
    // --------------------------------------------------------
    printSeparator();
    std::cout << "Summary (总结):\n";
    std::cout << "  - Created 5 basic solid types\n";
    std::cout << "  - Verified Euler characteristic for convex solids\n";
    std::cout << "  - Generated triangular meshes from B-rep geometry\n";
    std::cout << "  - Exported meshes in STL format\n";
    std::cout << "\n=== Done ===\n";

    return 0;
}
