// ============================================================
// Example 3: Surface Modeling Demo
//
// Demonstrates parametric surface creation and manipulation:
// - Plane, Cylinder, Sphere, Torus, Cone
// - Surface-surface intersections
// - Surface sampling and visualization
// ============================================================

#include <iostream>
#include <cmath>
#include "../src/brep.h"
#include "../src/geometry.h"
#include "../src/intersection.h"
#include "../src/mesh.h"

void printSeparator() {
    std::cout << "\n====================================================\n\n";
}

void printPoint(Point3D p, const char* label) {
    std::cout << "  " << label << " = (" << p.x << ", " << p.y << ", " << p.z << ")\n";
}

int main() {
    std::cout << "=== CAD Kernel: Surface Modeling Demo ===\n\n";

    // --------------------------------------------------------
    // 1. Geometric Primitives
    // --------------------------------------------------------
    printSeparator();
    std::cout << "1. Geometric Primitives (几何基本体)\n";

    // Line
    Line line({0, 0, 0}, {1, 1, 1});
    std::cout << "  Line:\n";
    line.print();
    std::cout << "  Point at u=0.5: (" << line.pointAt(0.5).x << ", "
              << line.pointAt(0.5).y << ", " << line.pointAt(0.5).z << ")\n";
    std::cout << "  Distance from (1,0,0): " << line.distance({1,0,0}) << "\n";

    // Plane
    Plane plane({0, 0, 0}, {0, 0, 1});
    std::cout << "\n  Plane:\n";
    plane.print();
    std::cout << "  Signed distance from (0,0,5): " << plane.signedDistance({0,0,5}) << "\n";
    std::cout << "  Projected point: (" << plane.project({0,0,5}).x << ", "
              << plane.project({0,0,5}).y << ", " << plane.project({0,0,5}).z << ")\n";

    // Cylinder
    Cylinder cyl({0, 0, 0}, {0, 0, 1}, 2.0);
    std::cout << "\n  Cylinder:\n";
    cyl.print();
    Point3D onSurface = cyl.sample(M_PI/4, 1.0);
    printPoint(onSurface, "Point on surface at (theta=pi/4, z=1)");
    std::cout << "  Distance from (3,0,0): " << cyl.distance({3,0,0}) << "\n";

    // Sphere
    Sphere sphere({0, 0, 0}, 3.0);
    std::cout << "\n  Sphere:\n";
    sphere.print();
    Point3D spherePt = sphere.sample(M_PI/3, M_PI/4);
    printPoint(spherePt, "Point on surface at (phi=pi/3, theta=pi/4)");
    std::cout << "  Surface area: " << sphere.surfaceArea() << " (expected: " << (4*M_PI*9) << ")\n";
    std::cout << "  Volume: " << sphere.volume() << " (expected: " << ((4.0/3.0)*M_PI*27) << ")\n";

    // Torus
    Torus torus({0, 0, 0}, {0, 0, 1}, 3.0, 0.8);
    std::cout << "\n  Torus:\n";
    torus.print();
    Point3D torusPt = torus.sample(M_PI/2, M_PI/3);
    printPoint(torusPt, "Point on surface at (theta=pi/2, phi=pi/3)");
    std::cout << "  Surface area: " << torus.surfaceArea() << "\n";
    std::cout << "  Volume: " << torus.volume() << "\n";

    // Cone
    Cone cone({0, 0, 0}, {0, 0, 1}, M_PI/6);
    std::cout << "\n  Cone:\n";
    cone.print();

    // --------------------------------------------------------
    // 2. Surface-Surface Intersections
    // --------------------------------------------------------
    printSeparator();
    std::cout << "2. Surface-Surface Intersections (曲面相交)\n";

    // Plane-Plane intersection
    std::cout << "  (a) Plane-Plane Intersection:\n";
    Plane p1({0, 0, 0}, {0, 0, 1});  // XY plane
    Plane p2({0, 0, 0}, {1, 0, 0});  // YZ plane
    auto pp_result = SurfaceIntersection::planePlane(p1, p2);
    pp_result.print();

    // Plane-Sphere intersection
    std::cout << "\n  (b) Plane-Sphere Intersection:\n";
    Plane p3({0, 0, 1}, {0, 0, 1});  // Plane at z=1
    auto ps_result = SurfaceIntersection::planeSphere(p3, sphere);
    ps_result.print();
    // The intersection should be a circle of radius sqrt(9-1) = sqrt(8) ≈ 2.83

    // Plane-Cylinder intersection
    std::cout << "\n  (c) Plane-Cylinder Intersection:\n";
    Plane p4({0, 0, 0}, {1, 0, 0});  // YZ plane
    Cylinder cyl2({0, 0, 0}, {0, 0, 1}, 2.0);
    auto pc_result = SurfaceIntersection::planeCylinder(p4, cyl2);
    pc_result.print();

    // Sphere-Sphere intersection
    std::cout << "\n  (d) Sphere-Sphere Intersection:\n";
    Sphere s1({-1, 0, 0}, 2.0);
    Sphere s2({1, 0, 0}, 2.0);
    auto ss_result = SurfaceIntersection::sphereSphere(s1, s2);
    ss_result.print();
    // The intersection should be a circle at x=0 with radius sqrt(4-1) = sqrt(3)

    // Cylinder-Cylinder intersection
    std::cout << "\n  (e) Cylinder-Cylinder Intersection:\n";
    Cylinder c1({0, 0, 0}, {0, 0, 1}, 1.5);
    Cylinder c2({0, 0, 0}, {1, 0, 0}, 1.5);
    auto cc_result = SurfaceIntersection::cylinderCylinder(c1, c2);
    std::cout << "  Cylinder-Cylinder intersection: " << cc_result.size() << " sample points\n";
    // This creates a Steinmetz curve (figure-8 in 3D)

    // --------------------------------------------------------
    // 3. Surface Mesh Generation
    // --------------------------------------------------------
    printSeparator();
    std::cout << "3. Surface Mesh Generation (曲面网格生成)\n";

    // Cylindrical surface mesh
    auto cylMesh = MeshGenerator::generateCylindricalMesh(
        {0, 0, 0}, {0, 0, 1}, 1.0, 2.0, 32, 1);
    std::cout << "  Cylindrical surface mesh (r=1, h=2, 32 segments):\n";
    cylMesh.printStats();

    // Sphere mesh
    auto sphereMesh = MeshGenerator::generateSphereMesh({0, 0, 0}, 1.0, 32, 32);
    std::cout << "\n  Sphere mesh (r=1, 32x32 segments):\n";
    sphereMesh.printStats();
    std::cout << "  Expected area: " << (4.0 * M_PI) << "\n";
    std::cout << "  Area error: " << std::fabs(sphereMesh.surfaceArea() - 4.0*M_PI) << "\n";

    // Torus mesh
    auto torusMesh = MeshGenerator::generateTorusMesh(
        {0, 0, 0}, {0, 0, 1}, 2.0, 0.5, 32, 16);
    std::cout << "\n  Torus mesh (R=2, r=0.5, 32x16 segments):\n";
    torusMesh.printStats();
    std::cout << "  Expected area: " << (4.0 * M_PI * M_PI * 2.0 * 0.5) << "\n";

    // --------------------------------------------------------
    // 4. Surface Properties
    // --------------------------------------------------------
    printSeparator();
    std::cout << "4. Surface Properties (曲面属性)\n";

    // Normal vectors at various points on sphere
    std::cout << "  Sphere normals:\n";
    for (int i = 0; i < 5; ++i) {
        double phi = M_PI * (i+1) / 6;
        double theta = 2.0 * M_PI * i / 5;
        Point3D p = sphere.sample(phi, theta);
        Vector3D n = sphere.normalAt(phi, theta);
        std::cout << "    At (" << p.x << ", " << p.y << ", " << p.z << "): "
                  << "normal=(" << n.x << ", " << n.y << ", " << n.z << ")\n";
    }

    // Distance field visualization
    std::cout << "\n  Sphere distance field (sampled on grid):\n";
    for (int i = -3; i <= 3; ++i) {
        std::cout << "  ";
        for (int j = -3; j <= 3; ++j) {
            double dist = sphere.distance({i, j, 0});
            if (dist < 0.1) std::cout << "* ";
            else if (dist < 0.5) std::cout << ". ";
            else std::cout << "  ";
        }
        std::cout << "\n";
    }

    // --------------------------------------------------------
    // 5. Export surfaces as meshes
    // --------------------------------------------------------
    printSeparator();
    std::cout << "5. Export Meshes (导出网格)\n";

    cylMesh.exportSTL("cylinder_mesh.stl");
    std::cout << "  Exported cylinder_mesh.stl\n";

    sphereMesh.exportSTL("sphere_surface.stl");
    std::cout << "  Exported sphere_surface.stl\n";

    torusMesh.exportSTL("torus_surface.stl");
    std::cout << "  Exported torus_surface.stl\n";

    // --------------------------------------------------------
    // Summary
    // --------------------------------------------------------
    printSeparator();
    std::cout << "Summary (总结):\n";
    std::cout << "  - Created and queried 5 geometric primitive types\n";
    std::cout << "  - Computed 5 types of surface-surface intersections\n";
    std::cout << "  - Generated triangular meshes from parametric surfaces\n";
    std::cout << "  - Computed surface normals and distance fields\n";
    std::cout << "  - Exported meshes in STL format\n";
    std::cout << "\n=== Done ===\n";

    return 0;
}
