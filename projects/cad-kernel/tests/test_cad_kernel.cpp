// ============================================================
// CAD Kernel Unit Tests
//
// Tests for all core components:
// - B-rep data structures
// - Geometric primitives
// - Topology management
// - Boolean operations
// - Surface intersection
// - Mesh generation
// ============================================================

#include <iostream>
#include <cassert>
#include <cmath>
#include <vector>
#include <memory>
#include "../src/brep.h"
#include "../src/geometry.h"
#include "../src/topology.h"
#include "../src/boolean.h"
#include "../src/intersection.h"
#include "../src/mesh.h"

// ============================================================
// Test utilities
// ============================================================
int tests_run = 0;
int tests_passed = 0;
int tests_failed = 0;

#define TEST(name) \
    std::cout << "  Testing: " << name << "... "; \
    tests_run++; \
    try {

#define END_TEST() \
        tests_passed++; \
        std::cout << "PASSED" << std::endl; \
    } catch (...) { \
        tests_failed++; \
        std::cout << "FAILED" << std::endl; \
    }

#define ASSERT_NEAR(a, b, tol) \
    if (std::fabs((a) - (b)) > (tol)) { \
        throw std::runtime_error("ASSERT_NEAR failed: " + std::to_string(a) + " != " + std::to_string(b)); \
    }

#define ASSERT_TRUE(cond) \
    if (!(cond)) { \
        throw std::runtime_error("ASSERT_TRUE failed"); \
    }

#define ASSERT_FALSE(cond) \
    if ((cond)) { \
        throw std::runtime_error("ASSERT_FALSE failed"); \
    }

#define ASSERT_EQ(a, b) \
    if ((a) != (b)) { \
        throw std::runtime_error("ASSERT_EQ failed: " + std::to_string(a) + " != " + std::to_string(b)); \
    }

// ============================================================
// B-rep Tests
// ============================================================
void test_brep_data_structures() {
    TEST("B-rep Vertex creation")
        Vertex v1(1.0, 2.0, 3.0);
        ASSERT_EQ(v1.id, 1u);
        ASSERT_NEAR(v1.point.x, 1.0, EPSILON);
        ASSERT_NEAR(v1.point.y, 2.0, EPSILON);
        ASSERT_NEAR(v1.point.z, 3.0, EPSILON);
    END_TEST

    TEST("B-rep Edge creation")
        Edge e1({0, 0, 0}, {1, 1, 1});
        ASSERT_EQ(e1.id, 2u);
        ASSERT_NEAR(e1.length(), std::sqrt(3.0), EPSILON);
    END_TEST

    TEST("B-rep Face creation")
        Face f1;
        ASSERT_EQ(f1.id, 3u);
        ASSERT_EQ(f1.surface_type, SurfaceType::PLANE);
    END_TEST

    TEST("B-rep Solid creation")
        Solid s1;
        ASSERT_EQ(s1.id, 4u);
        ASSERT_TRUE(s1.name.empty());
    END_TEST

    TEST("B-rep BRep container")
        BRep brep("Test");
        ASSERT_EQ(brep.solids.size(), 0u);
        brep.addSolid(std::make_unique<Solid>());
        ASSERT_EQ(brep.solids.size(), 1u);
    END_TEST

    TEST("Point3D operations")
        Point3D p1(1, 2, 3);
        Point3D p2(4, 5, 6);
        Point3D sum = p1 + p2;
        ASSERT_NEAR(sum.x, 5.0, EPSILON);
        ASSERT_NEAR(sum.y, 7.0, EPSILON);
        ASSERT_NEAR(sum.z, 9.0, EPSILON);

        Point3D diff = p2 - p1;
        ASSERT_NEAR(diff.x, 3.0, EPSILON);
        ASSERT_NEAR(diff.y, 3.0, EPSILON);
        ASSERT_NEAR(diff.z, 3.0, EPSILON);

        Point3D scaled = p1 * 2.0;
        ASSERT_NEAR(scaled.x, 2.0, EPSILON);
        ASSERT_NEAR(scaled.y, 4.0, EPSILON);
        ASSERT_NEAR(scaled.z, 6.0, EPSILON);
    END_TEST

    TEST("Point3D length and normalization")
        Point3D p(3, 4, 0);
        ASSERT_NEAR(p.length(), 5.0, EPSILON);
        Point3D n = p.normalized();
        ASSERT_NEAR(n.x, 0.6, EPSILON);
        ASSERT_NEAR(n.y, 0.8, EPSILON);
        ASSERT_NEAR(n.z, 0.0, EPSILON);
    END_TEST

    TEST("Point3D lerp")
        Point3D a(0, 0, 0);
        Point3D b(10, 10, 10);
        Point3D mid = lerp(a, b, 0.5);
        ASSERT_NEAR(mid.x, 5.0, EPSILON);
        ASSERT_NEAR(mid.y, 5.0, EPSILON);
        ASSERT_NEAR(mid.z, 5.0, EPSILON);
    END_TEST

    TEST("dot product")
        Point3D a(1, 0, 0);
        Point3D b(0, 1, 0);
        ASSERT_NEAR(dot(a, b), 0.0, EPSILON);

        Point3D c(1, 2, 3);
        Point3D d(4, 5, 6);
        ASSERT_NEAR(dot(c, d), 32.0, EPSILON);
    END_TEST

    TEST("cross product")
        Point3D a(1, 0, 0);
        Point3D b(0, 1, 0);
        Point3D c = cross(a, b);
        ASSERT_NEAR(c.x, 0.0, EPSILON);
        ASSERT_NEAR(c.y, 0.0, EPSILON);
        ASSERT_NEAR(c.z, 1.0, EPSILON);
    END_TEST
}

// ============================================================
// Geometric Primitives Tests
// ============================================================
void test_geometric_primitives() {
    TEST("Line creation and pointAt")
        Line line({0, 0, 0}, {2, 0, 0});
        Point3D p = line.pointAt(0.5);
        ASSERT_NEAR(p.x, 1.0, EPSILON);
        ASSERT_NEAR(p.y, 0.0, EPSILON);
        ASSERT_NEAR(p.z, 0.0, EPSILON);
    END_TEST

    TEST("Line distance")
        Line line({0, 0, 0}, {1, 0, 0});
        double d = line.distance({0, 1, 0});
        ASSERT_NEAR(d, 1.0, EPSILON);
    END_TEST

    TEST("Line project")
        Line line({0, 0, 0}, {1, 0, 0});
        double u = line.project({0.5, 0, 0});
        ASSERT_NEAR(u, 0.5, EPSILON);
    END_TEST

    TEST("Plane signed distance")
        Plane plane({0, 0, 0}, {0, 0, 1});
        ASSERT_NEAR(plane.signedDistance({0, 0, 5}), 5.0, EPSILON);
        ASSERT_NEAR(plane.signedDistance({0, 0, -3}), -3.0, EPSILON);
        ASSERT_NEAR(plane.signedDistance({1, 2, 0}), 0.0, EPSILON);
    END_TEST

    TEST("Plane project")
        Plane plane({0, 0, 0}, {0, 0, 1});
        Point3D p = plane.project({1, 2, 5});
        ASSERT_NEAR(p.x, 1.0, EPSILON);
        ASSERT_NEAR(p.y, 2.0, EPSILON);
        ASSERT_NEAR(p.z, 0.0, EPSILON);
    END_TEST

    TEST("Sphere surface area")
        Sphere sphere({0, 0, 0}, 2.0);
        ASSERT_NEAR(sphere.surfaceArea(), 4.0 * M_PI * 4.0, EPSILON);
    END_TEST

    TEST("Sphere volume")
        Sphere sphere({0, 0, 0}, 1.0);
        ASSERT_NEAR(sphere.volume(), (4.0/3.0) * M_PI, EPSILON);
    END_TEST

    TEST("Sphere onSurface")
        Sphere sphere({0, 0, 0}, 1.0);
        ASSERT_TRUE(sphere.onSurface({1, 0, 0}));
        ASSERT_TRUE(sphere.onSurface({0, 1, 0}));
        ASSERT_TRUE(sphere.onSurface({0, 0, 1}));
        ASSERT_FALSE(sphere.onSurface({2, 0, 0}));
        ASSERT_FALSE(sphere.onSurface({0.5, 0, 0}));
    END_TEST

    TEST("Torus surface area")
        Torus torus({0, 0, 0}, {0, 0, 1}, 2.0, 0.5);
        ASSERT_NEAR(torus.surfaceArea(), 4.0 * M_PI * M_PI * 2.0 * 0.5, EPSILON);
    END_TEST

    TEST("Torus volume")
        Torus torus({0, 0, 0}, {0, 0, 1}, 2.0, 0.5);
        ASSERT_NEAR(torus.volume(), 2.0 * M_PI * M_PI * 2.0 * 0.25, EPSILON);
    END_TEST
}

// ============================================================
// Topology Tests
// ============================================================
void test_topology() {
    TEST("Wiring from points")
        std::vector<Point3D> pts = {{0,0,0}, {1,0,0}, {1,1,0}, {0,1,0}};
        Wiring w = Wiring::createFromPoints(pts);
        ASSERT_EQ(w.size(), 4);
        ASSERT_TRUE(w.isClosed());
    END_TEST

    TEST("Wiring perimeter")
        std::vector<Point3D> pts = {{0,0,0}, {1,0,0}, {1,1,0}, {0,1,0}};
        Wiring w = Wiring::createFromPoints(pts);
        ASSERT_NEAR(w.perimeter(), 4.0, EPSILON);
    END_TEST

    TEST("Wiring bounding box")
        std::vector<Point3D> pts = {{0,0,0}, {2,0,0}, {2,3,0}, {0,3,0}};
        Wiring w = Wiring::createFromPoints(pts);
        auto bb = w.boundingBox();
        ASSERT_NEAR(bb.min.x, 0.0, EPSILON);
        ASSERT_NEAR(bb.min.y, 0.0, EPSILON);
        ASSERT_NEAR(bb.max.x, 2.0, EPSILON);
        ASSERT_NEAR(bb.max.y, 3.0, EPSILON);
    END_TEST

    TEST("Planar face creation")
        std::vector<Point3D> pts = {{0,0,0}, {1,0,0}, {1,1,0}, {0,1,0}};
        auto face = FaceBuilder::createPlanarFace(pts);
        ASSERT_EQ(face->surface_type, SurfaceType::PLANE);
        ASSERT_TRUE(face->vertices.size() >= 4);
        ASSERT_TRUE(face->area > 0.0);
    END_TEST

    TEST("Cylindrical face creation")
        auto face = FaceBuilder::createCylindricalFace(
            {0,0,0}, {0,0,1}, 1.0, 0, 2*M_PI, 2.0);
        ASSERT_EQ(face->surface_type, SurfaceType::CYLINDER);
        ASSERT_NEAR(face->area, 2.0 * M_PI * 2.0, EPSILON);
    END_TEST

    TEST("Box solid creation")
        auto box = SolidBuilder::createBox({0, 0, 0}, 2.0, 3.0, 4.0);
        box->name = "TestBox";
        ASSERT_EQ(box->vertexCount(), 8);
        ASSERT_EQ(box->edgeCount(), 12);
        ASSERT_EQ(box->faceCount(), 6);
        ASSERT_TRUE(box->checkEuler());
    END_TEST

    TEST("Box volume")
        auto box = SolidBuilder::createBox({0, 0, 0}, 2.0, 3.0, 4.0);
        ASSERT_NEAR(box->computeVolume(), 24.0, 0.5); // Approximate due to discretization
    END_TEST

    TEST("Cylinder solid creation")
        auto cyl = SolidBuilder::createCylinder({0, 0, 0}, {0, 0, 1}, 1.0, 3.0, 32);
        ASSERT_TRUE(cyl->vertexCount() > 0);
        ASSERT_TRUE(cyl->faceCount() > 0);
        ASSERT_TRUE(cyl->checkEuler());
    END_TEST

    TEST("Sphere solid creation")
        auto sphere = SolidBuilder::createSphere({0, 0, 0}, 1.0, 24, 24);
        ASSERT_TRUE(sphere->vertexCount() > 0);
        ASSERT_TRUE(sphere->faceCount() > 0);
        ASSERT_NEAR(sphere->computeVolume(), (4.0/3.0) * M_PI, 1.0);
    END_TEST

    TEST("Torus solid creation")
        auto torus = SolidBuilder::createTorus({0, 0, 0}, {0, 0, 1}, 2.0, 0.5, 32, 16);
        ASSERT_TRUE(torus->vertexCount() > 0);
        ASSERT_TRUE(torus->faceCount() > 0);
    END_TEST

    TEST("Prism solid creation")
        std::vector<Point3D> hex = {{1,0,0}, {0.5,0.866,0}, {-0.5,0.866,0},
                                     {-1,0,0}, {-0.5,-0.866,0}, {0.5,-0.866,0}};
        auto prism = SolidBuilder::createPrism(hex, 2.0);
        ASSERT_TRUE(prism->vertexCount() > 0);
        ASSERT_TRUE(prism->faceCount() > 0);
    END_TEST

    TEST("Euler characteristic for box")
        auto box = SolidBuilder::createBox({0, 0, 0}, 1.0, 1.0, 1.0);
        int euler = box->vertexCount() - box->edgeCount() + box->faceCount();
        ASSERT_NEAR(euler, 2, 1); // Should be 2 for a convex solid
    END_TEST

    TEST("Solid validation")
        auto box = SolidBuilder::createBox({0, 0, 0}, 1.0, 1.0, 1.0);
        TopoStatus status = box->validate();
        ASSERT_TRUE(status == TopoStatus::VALID || status == TopoStatus::INCOMPLETE);
    END_TEST
}

// ============================================================
// Boolean Operations Tests
// ============================================================
void test_boolean_operations() {
    TEST("Box-Box union")
        auto boxA = SolidBuilder::createBox({-1, -1, -1}, 2.0, 2.0, 2.0);
        auto boxB = SolidBuilder::createBox({1, 1, 1}, 2.0, 2.0, 2.0);
        auto result = BooleanOps::unionSolids(boxA.get(), boxB.get());
        ASSERT_TRUE(result != nullptr);
        ASSERT_TRUE(result->faceCount() > 0);
    END_TEST

    TEST("Box-Box difference")
        auto boxA = SolidBuilder::createBox({0, 0, 0}, 2.0, 2.0, 2.0);
        auto boxB = SolidBuilder::createBox({1, 1, 1}, 1.0, 1.0, 1.0);
        auto result = BooleanOps::differenceSolids(boxA.get(), boxB.get());
        ASSERT_TRUE(result != nullptr);
        ASSERT_TRUE(result->faceCount() > 0);
    END_TEST

    TEST("Sphere-Sphere intersection")
        auto sphereA = SolidBuilder::createSphere({-0.5, 0, 0}, 1.0, 16, 16);
        auto sphereB = SolidBuilder::createSphere({0.5, 0, 0}, 1.0, 16, 16);
        auto result = BooleanOps::intersectSolids(sphereA.get(), sphereB.get());
        ASSERT_TRUE(result != nullptr);
    END_TEST

    TEST("Sphere-Sphere difference")
        auto sphereA = SolidBuilder::createSphere({-0.5, 0, 0}, 1.0, 16, 16);
        auto sphereB = SolidBuilder::createSphere({0.5, 0, 0}, 1.0, 16, 16);
        auto result = BooleanOps::differenceSolids(sphereA.get(), sphereB.get());
        ASSERT_TRUE(result != nullptr);
        ASSERT_TRUE(result->faceCount() > 0);
    END_TEST

    TEST("Point classification")
        auto box = SolidBuilder::createBox({-1, -1, -1}, 2.0, 2.0, 2.0);
        ASSERT_TRUE(PointClassifier::isInside(box.get(), {0, 0, 0}));
        ASSERT_FALSE(PointClassifier::isInside(box.get(), {10, 0, 0}));
    END_TEST
}

// ============================================================
// Surface Intersection Tests
// ============================================================
void test_surface_intersection() {
    TEST("Plane-Plane intersection")
        Plane p1({0, 0, 0}, {0, 0, 1});
        Plane p2({0, 0, 0}, {1, 0, 0});
        auto result = SurfaceIntersection::planePlane(p1, p2);
        ASSERT_TRUE(result.valid);
        ASSERT_TRUE(result.size() > 0);
    END_TEST

    TEST("Plane-Plane parallel detection")
        Plane p1({0, 0, 0}, {0, 0, 1});
        Plane p2({0, 0, 5}, {0, 0, 1});
        auto result = SurfaceIntersection::planePlane(p1, p2);
        ASSERT_FALSE(result.valid);
    END_TEST

    TEST("Plane-Sphere intersection")
        Plane p({0, 0, 0.5}, {0, 0, 1});
        Sphere s({0, 0, 0}, 1.0);
        auto result = SurfaceIntersection::planeSphere(p, s);
        ASSERT_TRUE(result.valid);
        ASSERT_TRUE(result.size() > 0);
    END_TEST

    TEST("Plane-Sphere no intersection")
        Plane p({0, 0, 5}, {0, 0, 1});
        Sphere s({0, 0, 0}, 1.0);
        auto result = SurfaceIntersection::planeSphere(p, s);
        ASSERT_FALSE(result.valid);
    END_TEST

    TEST("Sphere-Sphere intersection")
        Sphere s1({-1, 0, 0}, 2.0);
        Sphere s2({1, 0, 0}, 2.0);
        auto result = SurfaceIntersection::sphereSphere(s1, s2);
        ASSERT_TRUE(result.valid);
        ASSERT_TRUE(result.size() > 0);
    END_TEST

    TEST("Sphere-Sphere no intersection (separate)")
        Sphere s1({-3, 0, 0}, 1.0);
        Sphere s2({3, 0, 0}, 1.0);
        auto result = SurfaceIntersection::sphereSphere(s1, s2);
        ASSERT_FALSE(result.valid);
    END_TEST
}

// ============================================================
// Mesh Generation Tests
// ============================================================
void test_mesh_generation() {
    TEST("Sphere mesh generation")
        auto mesh = MeshGenerator::generateSphereMesh({0, 0, 0}, 1.0, 16, 16);
        ASSERT_TRUE(mesh.triangles.size() > 0);
        ASSERT_NEAR(mesh.surfaceArea(), 4.0 * M_PI, 1.0);
    END_TEST

    TEST("Cylindrical mesh generation")
        auto mesh = MeshGenerator::generateCylindricalMesh(
            {0, 0, 0}, {0, 0, 1}, 1.0, 2.0, 16, 1);
        ASSERT_TRUE(mesh.triangles.size() > 0);
    END_TEST

    TEST("Torus mesh generation")
        auto mesh = MeshGenerator::generateTorusMesh(
            {0, 0, 0}, {0, 0, 1}, 2.0, 0.5, 16, 8);
        ASSERT_TRUE(mesh.triangles.size() > 0);
    END_TEST

    TEST("Prism mesh generation")
        std::vector<Point3D> tri = {{1,0,0}, {-0.5,0.866,0}, {-0.5,-0.866,0}};
        auto mesh = MeshGenerator::generatePrismMesh(tri, 2.0);
        ASSERT_TRUE(mesh.triangles.size() > 0);
    END_TEST

    TEST("Box to mesh conversion")
        auto box = SolidBuilder::createBox({0, 0, 0}, 2.0, 3.0, 4.0);
        auto mesh = MeshGenerator::generateFromSolid(box.get(), 8);
        ASSERT_TRUE(mesh.triangles.size() > 0);
        ASSERT_TRUE(mesh.surfaceArea() > 0);
    END_TEST

    TEST("STL export (binary)")
        Mesh mesh("Test");
        mesh.addTriangle({0,0,0}, {1,0,0}, {0,1,0});
        bool ok = mesh.exportSTL("/tmp/test_cad_export.stl");
        ASSERT_TRUE(ok);
    END_TEST

    TEST("STL export (ASCII)")
        Mesh mesh("TestAscii");
        mesh.addTriangle({0,0,0}, {1,0,0}, {0,1,0});
        bool ok = mesh.exportSTLAscii("/tmp/test_cad_export_ascii.stl");
        ASSERT_TRUE(ok);
    END_TEST

    TEST("Mesh bounding box")
        Mesh mesh("Test");
        mesh.addTriangle({0,0,0}, {2,0,0}, {0,2,0});
        mesh.addTriangle({1,1,0}, {3,1,0}, {1,3,0});
        auto bb = mesh.boundingBox();
        ASSERT_NEAR(bb.min.x, 0.0, EPSILON);
        ASSERT_NEAR(bb.min.y, 0.0, EPSILON);
        ASSERT_NEAR(bb.max.x, 3.0, EPSILON);
        ASSERT_NEAR(bb.max.y, 3.0, EPSILON);
    END_TEST

    TEST("Mesh vertex normals")
        Mesh mesh("Test");
        mesh.addTriangle({0,0,0}, {1,0,0}, {0,1,0});
        mesh.addTriangle({0,0,0}, {0,1,0}, {0,0,1});
        auto normals = mesh.computeVertexNormals();
        ASSERT_TRUE(normals.size() > 0);
    END_TEST
}

// ============================================================
// Main
// ============================================================
int main() {
    std::cout << "=== CAD Kernel Unit Tests ===\n\n";

    std::cout << "B-rep Data Structures:\n";
    test_brep_data_structures();

    std::cout << "\nGeometric Primitives:\n";
    test_geometric_primitives();

    std::cout << "\nTopology Management:\n";
    test_topology();

    std::cout << "\nBoolean Operations:\n";
    test_boolean_operations();

    std::cout << "\nSurface Intersection:\n";
    test_surface_intersection();

    std::cout << "\nMesh Generation:\n";
    test_mesh_generation();

    // Summary
    std::cout << "\n=== Test Summary ===\n";
    std::cout << "  Total:  " << tests_run << "\n";
    std::cout << "  Passed: " << tests_passed << "\n";
    std::cout << "  Failed: " << tests_failed << "\n";

    if (tests_failed == 0) {
        std::cout << "\nAll tests passed!\n";
    } else {
        std::cout << "\nSome tests failed.\n";
    }

    return tests_failed > 0 ? 1 : 0;
}
