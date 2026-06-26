// ============================================================
// Example 4: Mesh Generation Demo
//
// Demonstrates mesh generation from various sources:
// - B-rep solids (triangulation of faces)
// - Parametric surfaces (sampling)
// - Marching Cubes (implicit surfaces)
// - Mesh subdivision (refinement)
// - STL export/import
// ============================================================

#include <iostream>
#include <cmath>
#include <functional>
#include "../src/brep.h"
#include "../src/geometry.h"
#include "../src/topology.h"
#include "../src/boolean.h"
#include "../src/intersection.h"
#include "../src/mesh.h"

void printSeparator() {
    std::cout << "\n====================================================\n\n";
}

int main() {
    std::cout << "=== CAD Kernel: Mesh Generation Demo ===\n\n";

    // --------------------------------------------------------
    // 1. Mesh from Box Solid
    // --------------------------------------------------------
    printSeparator();
    std::cout << "1. Mesh from Box Solid (长方体网格)\n";

    auto box = SolidBuilder::createBox({0, 0, 0}, 2.0, 3.0, 4.0);
    box->name = "Box";

    auto boxMesh = MeshGenerator::generateFromSolid(box.get(), 16);
    std::cout << "  Box mesh:\n";
    boxMesh.printStats();
    boxMesh.exportSTL("box_mesh.stl");
    std::cout << "  Exported box_mesh.stl\n";

    // --------------------------------------------------------
    // 2. Mesh from Cylinder Solid
    // --------------------------------------------------------
    printSeparator();
    std::cout << "2. Mesh from Cylinder Solid (圆柱体网格)\n";

    auto cyl = SolidBuilder::createCylinder({0, 0, 0}, {0, 0, 1}, 1.0, 3.0, 32);
    cyl->name = "Cylinder";

    auto cylMesh = MeshGenerator::generateFromSolid(cyl.get(), 16);
    std::cout << "  Cylinder mesh:\n";
    cylMesh.printStats();
    cylMesh.exportSTL("cylinder_mesh.stl");
    std::cout << "  Exported cylinder_mesh.stl\n";

    // --------------------------------------------------------
    // 3. Mesh from Sphere Solid
    // --------------------------------------------------------
    printSeparator();
    std::cout << "3. Mesh from Sphere Solid (球体网格)\n";

    auto sphere = SolidBuilder::createSphere({0, 0, 0}, 1.5, 24, 24);
    sphere->name = "Sphere";

    auto sphereMesh = MeshGenerator::generateFromSolid(sphere.get(), 16);
    std::cout << "  Sphere mesh from solid:\n";
    sphereMesh.printStats();

    // Compare with parametric sphere mesh
    auto paramSphere = MeshGenerator::generateSphereMesh({0, 0, 0}, 1.5, 24, 24);
    std::cout << "  Parametric sphere mesh:\n";
    paramSphere.printStats();
    std::cout << "  Area difference: " << std::fabs(sphereMesh.surfaceArea() - paramSphere.surfaceArea()) << "\n";

    // --------------------------------------------------------
    // 4. Mesh from Torus Solid
    // --------------------------------------------------------
    printSeparator();
    std::cout << "4. Mesh from Torus Solid (环面网格)\n";

    auto torus = SolidBuilder::createTorus({0, 0, 0}, {0, 0, 1}, 2.0, 0.5, 32, 16);
    torus->name = "Torus";

    auto torusMesh = MeshGenerator::generateFromSolid(torus.get(), 16);
    std::cout << "  Torus mesh:\n";
    torusMesh.printStats();

    auto paramTorus = MeshGenerator::generateTorusMesh({0, 0, 0}, {0, 0, 1}, 2.0, 0.5, 32, 16);
    std::cout << "  Parametric torus mesh:\n";
    paramTorus.printStats();

    // --------------------------------------------------------
    // 5. Mesh from Prism (extruded polygon)
    // --------------------------------------------------------
    printSeparator();
    std::cout << "5. Mesh from Prism (棱柱网格)\n";

    std::vector<Point3D> pentBase;
    for (int i = 0; i < 5; ++i) {
        double angle = 2.0 * M_PI * i / 5;
        pentBase.push_back({std::cos(angle), std::sin(angle), 0});
    }
    auto prism = SolidBuilder::createPrism(pentBase, 2.0);
    prism->name = "PentagonalPrism";

    auto prismMesh = MeshGenerator::generateFromSolid(prism.get(), 16);
    std::cout << "  Prism mesh:\n";
    prismMesh.printStats();

    // --------------------------------------------------------
    // 6. Mesh Subdivision (网格细分)
    // --------------------------------------------------------
    printSeparator();
    std::cout << "6. Mesh Subdivision (网格细分)\n";

    auto lowPoly = MeshGenerator::generateSphereMesh({0, 0, 0}, 1.0, 8, 8);
    std::cout << "  Low-poly sphere (8x8 segments):\n";
    lowPoly.printStats();

    auto subdivided = MeshGenerator::subdivide(lowPoly, 2);
    std::cout << "  After 2 subdivision iterations:\n";
    subdivided.printStats();

    // --------------------------------------------------------
    // 7. Marching Cubes (Marching Cubes 算法)
    // --------------------------------------------------------
    printSeparator();
    std::cout << "7. Marching Cubes (移动立方体算法)\n";

    // Create implicit sphere: f(x,y,z) = (x^2+y^2+z^2) - r^2
    auto implicitSphere = [](Point3D p) {
        return p.x*p.x + p.y*p.y + p.z*p.z - 1.0;
    };

    auto mcMesh = MeshGenerator::marchingCubes(
        implicitSphere,
        {-1.5, -1.5, -1.5},
        {1.5, 1.5, 1.5},
        40
    );
    std::cout << "  Marching Cubes sphere (r=1, 40x40x40 grid):\n";
    mcMesh.printStats();
    mcMesh.exportSTL("mc_sphere.stl");
    std::cout << "  Exported mc_sphere.stl\n";

    // Create implicit torus: f(x,y,z) = (sqrt(x^2+y^2) - R)^2 + z^2 - r^2
    auto implicitTorus = [](Point3D p) {
        double R = 2.0, r = 0.5;
        double dx = std::sqrt(p.x*p.x + p.y*p.y) - R;
        return dx*dx + p.z*p.z - r*r;
    };

    auto mcTorus = MeshGenerator::marchingCubes(
        implicitTorus,
        {-3.0, -3.0, -1.0},
        {3.0, 3.0, 1.0},
        50
    );
    std::cout << "\n  Marching Cubes torus (R=2, r=0.5, 50x50x50 grid):\n";
    mcTorus.printStats();
    mcTorus.exportSTL("mc_torus.stl");
    std::cout << "  Exported mc_torus.stl\n";

    // Create implicit intersection (two overlapping spheres)
    auto implicitUnion = [](Point3D p) {
        double d1 = std::sqrt((p.x+0.5)*(p.x+0.5) + p.y*p.y + p.z*p.z) - 1.0;
        double d2 = std::sqrt((p.x-0.5)*(p.x-0.5) + p.y*p.y + p.z*p.z) - 1.0;
        return std::min(d1, d2); // Union: min of signed distances
    };

    auto mcUnion = MeshGenerator::marchingCubes(
        implicitUnion,
        {-2.0, -2.0, -2.0},
        {2.0, 2.0, 2.0},
        40
    );
    std::cout << "\n  Marching Cubes union of two spheres:\n";
    mcUnion.printStats();
    mcUnion.exportSTL("mc_union.stl");
    std::cout << "  Exported mc_union.stl\n";

    // --------------------------------------------------------
    // 8. Mesh Statistics Comparison
    // --------------------------------------------------------
    printSeparator();
    std::cout << "8. Mesh Statistics Comparison (网格统计对比)\n";

    struct MeshInfo {
        std::string name;
        int triangles;
        int vertices;
        double area;
    };

    std::vector<MeshInfo> meshes = {
        {"Box", static_cast<int>(boxMesh.triangles.size()), 0, boxMesh.surfaceArea()},
        {"Cylinder", static_cast<int>(cylMesh.triangles.size()), 0, cylMesh.surfaceArea()},
        {"Sphere (B-rep)", static_cast<int>(sphereMesh.triangles.size()), 0, sphereMesh.surfaceArea()},
        {"Sphere (parametric)", static_cast<int>(paramSphere.triangles.size()), 0, paramSphere.surfaceArea()},
        {"Torus", static_cast<int>(torusMesh.triangles.size()), 0, torusMesh.surfaceArea()},
        {"Prism", static_cast<int>(prismMesh.triangles.size()), 0, prismMesh.surfaceArea()},
    };

    std::cout << "  Name              | Tris    | Area\n";
    std::cout << "  ------------------|---------|--------\n";
    for (const auto& m : meshes) {
        printf("  %-18s| %7d | %.4f\n", m.name.c_str(), m.triangles, m.area);
    }

    // --------------------------------------------------------
    // 9. ASCII STL Example
    // --------------------------------------------------------
    printSeparator();
    std::cout << "9. ASCII STL Example (ASCII STL 示例)\n";

    auto smallMesh = MeshGenerator::generateSphereMesh({0, 0, 0}, 0.5, 8, 8);
    smallMesh.name = "SmallSphere";
    smallMesh.exportSTLAscii("small_sphere_ascii.stl");
    std::cout << "  Exported small_sphere_ascii.stl\n";
    std::cout << "  (ASCII STL is human-readable but larger than binary)\n";

    // --------------------------------------------------------
    // Summary
    // --------------------------------------------------------
    printSeparator();
    std::cout << "Summary (总结):\n";
    std::cout << "  - Generated meshes from B-rep solids (box, cylinder, sphere, torus, prism)\n";
    std::cout << "  - Compared B-rep triangulation vs parametric surface sampling\n";
    std::cout << "  - Demonstrated mesh subdivision for refinement\n";
    std::cout << "  - Generated implicit surface meshes with Marching Cubes\n";
    std::cout << "  - Exported meshes in binary and ASCII STL formats\n";
    std::cout << "  - Compared mesh statistics (triangles, area)\n";
    std::cout << "\n=== Done ===\n";

    return 0;
}
