#include <iostream>
#include <cassert>
#include <string>
#include <vector>
#include <functional>
#include <cmath>

#include "scene_graph/scene_graph.h"

// Simple test framework
class TestRunner {
public:
    using TestFunc = std::function<void()>;

    struct TestCase {
        std::string name;
        TestFunc func;
    };

    void addTest(const std::string& name, TestFunc func) {
        tests_.push_back({name, func});
    }

    int runAll() {
        int passed = 0;
        int failed = 0;
        std::cout << "Running " << tests_.size() << " tests...\n\n";

        for (const auto& test : tests_) {
            try {
                std::cout << "[RUN    ] " << test.name << std::endl;
                test.func();
                std::cout << "[      OK] " << test.name << std::endl;
                passed++;
            } catch (const std::exception& e) {
                std::cout << "[FAILED ] " << test.name << " - " << e.what() << std::endl;
                failed++;
            } catch (...) {
                std::cout << "[FAILED ] " << test.name << " - unknown error" << std::endl;
                failed++;
            }
        }

        std::cout << "\n========================================\n";
        std::cout << "Results: " << passed << " passed, " << failed << " failed\n";
        std::cout << "========================================\n";
        return failed;
    }

private:
    std::vector<TestCase> tests_;
};

// Assertion macros
#define ASSERT_TRUE(expr) \
    do { if (!(expr)) throw std::runtime_error("ASSERT_TRUE failed: " #expr); } while(0)

#define ASSERT_FALSE(expr) \
    do { if (expr) throw std::runtime_error("ASSERT_FALSE failed: " #expr); } while(0)

#define ASSERT_EQ(a, b) \
    do { if ((a) != (b)) throw std::runtime_error("ASSERT_EQ failed: " #a " != " #b); } while(0)

#define ASSERT_FLOAT_EQ(a, b) \
    do { if (std::abs((a) - (b)) > 1e-5f) throw std::runtime_error("ASSERT_FLOAT_EQ failed: " + std::to_string(a) + " != " + std::to_string(b)); } while(0)

#define ASSERT_VEC3_EQ(a, b) \
    do { \
        if (std::abs((a).x - (b).x) > 1e-5f || \
            std::abs((a).y - (b).y) > 1e-5f || \
            std::abs((a).z - (b).z) > 1e-5f) \
            throw std::runtime_error("ASSERT_VEC3_EQ failed"); \
    } while(0)

// ============================================================================
// Test: Vec3 Operations
// ============================================================================
void test_vec3_operations() {
    sg::Vec3 a(1, 2, 3);
    sg::Vec3 b(4, 5, 6);

    // Addition
    sg::Vec3 c = a + b;
    ASSERT_FLOAT_EQ(c.x, 5.0f);
    ASSERT_FLOAT_EQ(c.y, 7.0f);
    ASSERT_FLOAT_EQ(c.z, 9.0f);

    // Subtraction
    sg::Vec3 d = b - a;
    ASSERT_FLOAT_EQ(d.x, 3.0f);
    ASSERT_FLOAT_EQ(d.y, 3.0f);
    ASSERT_FLOAT_EQ(d.z, 3.0f);

    // Scalar multiplication
    sg::Vec3 e = a * 2.0f;
    ASSERT_FLOAT_EQ(e.x, 2.0f);
    ASSERT_FLOAT_EQ(e.y, 4.0f);
    ASSERT_FLOAT_EQ(e.z, 6.0f);

    // Dot product
    float dot = a.dot(b);
    ASSERT_FLOAT_EQ(dot, 32.0f);

    // Cross product
    sg::Vec3 cross = sg::Vec3::right().cross(sg::Vec3::up());
    ASSERT_VEC3_EQ(cross, sg::Vec3::forward());

    // Length
    sg::Vec3 v(3, 4, 0);
    ASSERT_FLOAT_EQ(v.length(), 5.0f);

    // Normalization
    sg::Vec3 n = v.normalized();
    ASSERT_FLOAT_EQ(n.length(), 1.0f);
    ASSERT_FLOAT_EQ(n.x, 0.6f);
    ASSERT_FLOAT_EQ(n.y, 0.8f);
}

// ============================================================================
// Test: Mat4 Operations
// ============================================================================
void test_mat4_operations() {
    // Identity matrix
    sg::Mat4 I;
    ASSERT_FLOAT_EQ(I.at(0, 0), 1.0f);
    ASSERT_FLOAT_EQ(I.at(1, 1), 1.0f);
    ASSERT_FLOAT_EQ(I.at(2, 2), 1.0f);
    ASSERT_FLOAT_EQ(I.at(3, 3), 1.0f);
    ASSERT_FLOAT_EQ(I.at(0, 1), 0.0f);

    // Translation
    sg::Mat4 T = sg::Mat4::translation(sg::Vec3(10, 20, 30));
    sg::Vec3 p = T.transformPoint(sg::Vec3::zero());
    ASSERT_FLOAT_EQ(p.x, 10.0f);
    ASSERT_FLOAT_EQ(p.y, 20.0f);
    ASSERT_FLOAT_EQ(p.z, 30.0f);

    // Scale
    sg::Mat4 S = sg::Mat4::scale(sg::Vec3(2, 3, 4));
    sg::Vec3 s = S.transformPoint(sg::Vec3(1, 1, 1));
    ASSERT_FLOAT_EQ(s.x, 2.0f);
    ASSERT_FLOAT_EQ(s.y, 3.0f);
    ASSERT_FLOAT_EQ(s.z, 4.0f);

    // Matrix multiplication (TRS order)
    sg::Mat4 TRS = T * S;
    sg::Vec3 result = TRS.transformPoint(sg::Vec3(1, 1, 1));
    ASSERT_FLOAT_EQ(result.x, 12.0f);  // 1*2 + 10
    ASSERT_FLOAT_EQ(result.y, 23.0f);  // 1*3 + 20
    ASSERT_FLOAT_EQ(result.z, 34.0f);  // 1*4 + 30

    // Identity multiplication
    sg::Mat4 IM = I * T;
    sg::Vec3 im = IM.transformPoint(sg::Vec3(0, 0, 0));
    ASSERT_FLOAT_EQ(im.x, 10.0f);
    ASSERT_FLOAT_EQ(im.y, 20.0f);
    ASSERT_FLOAT_EQ(im.z, 30.0f);

    // Rotation
    sg::Mat4 Ry = sg::Mat4::rotationY(sg::degToRad(90));
    sg::Vec3 fwd = Ry.transformDirection(sg::Vec3::forward());
    // After 90 degree Y rotation, forward (-Z) should become -X direction? No...
    // Let's test with right vector: right (1,0,0) rotated 90 deg around Y = (0,0,-1)
    sg::Vec3 r = Ry.transformDirection(sg::Vec3::right());
    ASSERT_FLOAT_EQ(r.x, 0.0f);
    ASSERT_FLOAT_EQ(r.z, -1.0f);
}

// ============================================================================
// Test: Transform
// ============================================================================
void test_transform() {
    sg::Transform t;
    t.position = sg::Vec3(5, 0, 0);
    t.scale = sg::Vec3(2, 2, 2);

    sg::Mat4 localMatrix = t.getLocalMatrix();
    sg::Vec3 p = localMatrix.transformPoint(sg::Vec3(1, 0, 0));
    ASSERT_FLOAT_EQ(p.x, 7.0f);  // 1*2 + 5
    ASSERT_FLOAT_EQ(p.y, 0.0f);
    ASSERT_FLOAT_EQ(p.z, 0.0f);

    // Rotation
    sg::Transform t2;
    t2.rotation.y = sg::degToRad(90);
    sg::Vec3 fwd = t2.getForward();
    // Forward should be rotated
    ASSERT_TRUE(std::abs(fwd.x) > 0.9f);
}

// ============================================================================
// Test: Node Hierarchy
// ============================================================================
void test_node_hierarchy() {
    auto root = sg::Node::create("Root");
    auto child1 = sg::Node::create("Child1");
    auto child2 = sg::Node::create("Child2");
    auto grandchild = sg::Node::create("Grandchild");

    root->addChild(child1);
    root->addChild(child2);
    child1->addChild(grandchild);

    // Check hierarchy
    ASSERT_EQ(root->getChildCount(), 2u);
    ASSERT_EQ(child1->getChildCount(), 1u);
    ASSERT_EQ(grandchild->getDepth(), 2);

    // Find child by name
    auto found = root->getChild("Child1");
    ASSERT_TRUE(found != nullptr);
    ASSERT_EQ(found->getName(), "Child1");

    // Find child recursively
    auto foundDeep = root->findChild("Grandchild");
    ASSERT_TRUE(foundDeep != nullptr);
    ASSERT_EQ(foundDeep->getName(), "Grandchild");

    // Ancestor check
    ASSERT_TRUE(root->isAncestorOf(grandchild));
    ASSERT_FALSE(grandchild->isAncestorOf(root));

    // Remove child
    root->removeChild(child2);
    ASSERT_EQ(root->getChildCount(), 1u);

    // Parent check
    ASSERT_TRUE(grandchild->getParent() == child1);
}

// ============================================================================
// Test: Transform Hierarchy
// ============================================================================
void test_transform_hierarchy() {
    auto root = sg::Node::create("Root");
    root->getTransform().position = sg::Vec3(10, 0, 0);

    auto child = sg::Node::create("Child");
    child->getTransform().position = sg::Vec3(5, 0, 0);

    root->addChild(child);

    // Child world position should be parent + local
    sg::Vec3 childWorldPos = child->getWorldPosition();
    ASSERT_FLOAT_EQ(childWorldPos.x, 15.0f);
    ASSERT_FLOAT_EQ(childWorldPos.y, 0.0f);
    ASSERT_FLOAT_EQ(childWorldPos.z, 0.0f);

    // Deep hierarchy
    auto grandchild = sg::Node::create("Grandchild");
    grandchild->getTransform().position = sg::Vec3(0, 5, 0);
    child->addChild(grandchild);

    sg::Vec3 gcWorldPos = grandchild->getWorldPosition();
    ASSERT_FLOAT_EQ(gcWorldPos.x, 15.0f);
    ASSERT_FLOAT_EQ(gcWorldPos.y, 5.0f);
    ASSERT_FLOAT_EQ(gcWorldPos.z, 0.0f);

    // Scale propagation
    root->getTransform().scale = sg::Vec3(2, 2, 2);
    root->markDirty();

    sg::Vec3 scaledPos = grandchild->getWorldPosition();
    // Root scale 2x, child at 5, grandchild at 5
    // World pos = 10 + 2*(5 + 0) = 20
    ASSERT_FLOAT_EQ(scaledPos.x, 20.0f);
}

// ============================================================================
// Test: AABB
// ============================================================================
void test_aabb() {
    sg::AABB aabb(sg::Vec3(-1, -1, -1), sg::Vec3(1, 1, 1));

    // Center
    sg::Vec3 c = aabb.center();
    ASSERT_FLOAT_EQ(c.x, 0.0f);
    ASSERT_FLOAT_EQ(c.y, 0.0f);
    ASSERT_FLOAT_EQ(c.z, 0.0f);

    // Transform
    sg::Mat4 T = sg::Mat4::translation(sg::Vec3(10, 0, 0));
    sg::AABB moved = aabb.transformed(T);
    ASSERT_FLOAT_EQ(moved.min.x, 9.0f);
    ASSERT_FLOAT_EQ(moved.max.x, 11.0f);

    // Merge
    sg::AABB a(sg::Vec3(0, 0, 0), sg::Vec3(1, 1, 1));
    sg::AABB b(sg::Vec3(-1, -1, -1), sg::Vec3(0.5f, 0.5f, 0.5f));
    a.merge(b);
    ASSERT_FLOAT_EQ(a.min.x, -1.0f);
    ASSERT_FLOAT_EQ(a.max.x, 1.0f);
}

// ============================================================================
// Test: Frustum Culling
// ============================================================================
void test_frustum_culling() {
    // Create a camera
    sg::Camera camera;
    camera.setPosition(sg::Vec3(0, 0, 5));
    camera.setTarget(sg::Vec3(0, 0, 0));
    camera.setPerspective(sg::degToRad(60), 16.0f/9.0f, 0.1f, 100.0f);

    // Update frustum
    const sg::Frustum& frustum = camera.getFrustum();

    // Object at origin should be visible
    sg::AABB visibleBox(sg::Vec3(-0.5f, -0.5f, -0.5f), sg::Vec3(0.5f, 0.5f, 0.5f));
    ASSERT_TRUE(frustum.containsAABB(visibleBox));

    // Object behind camera should not be visible
    sg::AABB behindBox(sg::Vec3(-0.5f, -0.5f, 5.5f), sg::Vec3(0.5f, 0.5f, 6.5f));
    ASSERT_FALSE(frustum.containsAABB(behindBox));

    // Object far away but in front should be visible
    sg::AABB farBox(sg::Vec3(-1, -1, -80), sg::Vec3(1, 1, -78));
    ASSERT_TRUE(frustum.containsAABB(farBox));

    // Object very far away should be culled (beyond far plane)
    sg::AABB tooFarBox(sg::Vec3(-1, -1, -200), sg::Vec3(1, 1, -198));
    ASSERT_FALSE(frustum.containsAABB(tooFarBox));

    // Sphere test
    ASSERT_TRUE(frustum.containsSphere(sg::Vec3(0, 0, 0), 1.0f));
    ASSERT_FALSE(frustum.containsSphere(sg::Vec3(100, 100, 100), 1.0f));
}

// ============================================================================
// Test: Frustum Culling with Scene Graph
// ============================================================================
void test_frustum_culling_scene() {
    // Create camera
    sg::Camera camera;
    camera.setPosition(sg::Vec3(0, 0, 10));
    camera.setTarget(sg::Vec3(0, 0, 0));
    camera.setPerspective(sg::degToRad(60), 16.0f/9.0f, 0.1f, 100.0f);

    // Create scene
    auto root = sg::Node::create("Root");

    // Visible object at origin
    auto visibleObj = sg::Node::create("VisibleObj");
    visibleObj->setAABB(sg::AABB(sg::Vec3(-1, -1, -1), sg::Vec3(1, 1, 1)));
    root->addChild(visibleObj);

    // Hidden object behind camera
    auto hiddenObj = sg::Node::Create("HiddenObj");
    hiddenObj->getTransform().position = sg::Vec3(0, 0, 15);
    hiddenObj->setAABB(sg::AABB(sg::Vec3(-1, -1, -1), sg::Vec3(1, 1, 1)));
    root->addChild(hiddenObj);

    // Far object that should be visible
    auto farObj = sg::Node::create("FarObj");
    farObj->getTransform().position = sg::Vec3(0, 0, -50);
    farObj->setAABB(sg::AABB(sg::Vec3(-2, -2, -2), sg::Vec3(2, 2, 2)));
    root->addChild(farObj);

    // Create renderer
    sg::Renderer renderer;
    renderer.setCamera(&camera);
    renderer.processScene(root);

    // Check stats
    const auto& stats = renderer.getStats();
    ASSERT_TRUE(stats.visibleNodes >= 2);  // VisibleObj and FarObj should be visible
    ASSERT_TRUE(stats.culledNodes >= 1);   // HiddenObj should be culled

    std::cout << "\n" << renderer.getRenderListString() << std::endl;
}

// ============================================================================
// Test: Node traversal
// ============================================================================
void test_node_traversal() {
    auto root = sg::Node::create("Root");
    auto a = sg::Node::create("A");
    auto b = sg::Node::create("B");
    auto c = sg::Node::create("C");
    auto d = sg::Node::create("D");

    root->addChild(a);
    root->addChild(b);
    a->addChild(c);
    a->addChild(d);

    std::vector<std::string> visitOrder;
    root->traverse([&visitOrder](sg::NodePtr node) {
        visitOrder.push_back(node->getName());
    });

    // Should visit in pre-order: Root, A, C, D, B
    ASSERT_EQ(visitOrder.size(), 5u);
    ASSERT_EQ(visitOrder[0], "Root");
    ASSERT_EQ(visitOrder[1], "A");
    ASSERT_EQ(visitOrder[2], "C");
    ASSERT_EQ(visitOrder[3], "D");
    ASSERT_EQ(visitOrder[4], "B");

    // Post-order
    std::vector<std::string> postOrder;
    root->traversePostOrder([&postOrder](sg::NodePtr node) {
        postOrder.push_back(node->getName());
    });

    ASSERT_EQ(postOrder[0], "C");
    ASSERT_EQ(postOrder[1], "D");
    ASSERT_EQ(postOrder[2], "A");
    ASSERT_EQ(postOrder[3], "B");
    ASSERT_EQ(postOrder[4], "Root");
}

// ============================================================================
// Test: Node flags
// ============================================================================
void test_node_flags() {
    auto node = sg::Node::create("TestNode");

    // Default flags
    ASSERT_TRUE(node->isActive());
    ASSERT_TRUE(node->isVisible());

    // Set inactive
    node->setActive(false);
    ASSERT_FALSE(node->isActive());
    ASSERT_TRUE(node->isVisible());

    // Set invisible
    node->setVisible(false);
    ASSERT_FALSE(node->isActive());
    ASSERT_FALSE(node->isVisible());

    // Restore
    node->setActive(true);
    node->setVisible(true);
    ASSERT_TRUE(node->isActive());
    ASSERT_TRUE(node->isVisible());
}

// ============================================================================
// Test: Camera
// ============================================================================
void test_camera() {
    sg::Camera camera;
    camera.setPosition(sg::Vec3(0, 5, 10));
    camera.setTarget(sg::Vec3(0, 0, 0));
    camera.setPerspective(sg::degToRad(60), 16.0f/9.0f, 0.1f, 100.0f);

    // Forward direction
    sg::Vec3 forward = camera.getForward();
    ASSERT_TRUE(forward.z < 0);  // Should point towards -Z

    // Right direction
    sg::Vec3 right = camera.getRight();
    ASSERT_TRUE(right.x > 0);  // Should point towards +X

    // View matrix should be valid
    const sg::Mat4& view = camera.getViewMatrix();
    sg::Vec3 origin = view.transformPoint(sg::Vec3::zero());
    // Origin in view space should be at camera position offset
    ASSERT_TRUE(origin.z < 0);  // Should be in front of camera
}

// ============================================================================
// Test: Dirty flag propagation
// ============================================================================
void test_dirty_propagation() {
    auto root = sg::Node::create("Root");
    auto child = sg::Node::create("Child");
    auto grandchild = sg::Node::create("Grandchild");

    root->addChild(child);
    child->addChild(grandchild);

    // Initial update
    root->updateTransforms();
    ASSERT_FALSE(root->isDirty());
    ASSERT_FALSE(child->isDirty());
    ASSERT_FALSE(grandchild->isDirty());

    // Mark root dirty
    root->markDirty();
    ASSERT_TRUE(root->isDirty());
    ASSERT_TRUE(child->isDirty());
    ASSERT_TRUE(grandchild->isDirty());

    // Update again
    root->updateTransforms();
    ASSERT_FALSE(root->isDirty());
    ASSERT_FALSE(child->isDirty());
    ASSERT_FALSE(grandchild->isDirty());
}

// ============================================================================
// Test: Complex scene with transformations
// ============================================================================
void test_complex_scene() {
    // Create a solar system-like scene
    auto sun = sg::Node::create("Sun");
    sun->setAABB(sg::AABB(sg::Vec3(-2, -2, -2), sg::Vec3(2, 2, 2)));

    auto earth = sg::Node::create("Earth");
    earth->getTransform().position = sg::Vec3(10, 0, 0);
    earth->setAABB(sg::AABB(sg::Vec3(-1, -1, -1), sg::Vec3(1, 1, 1)));
    sun->addChild(earth);

    auto moon = sg::Node::create("Moon");
    moon->getTransform().position = sg::Vec3(2, 0, 0);
    moon->setAABB(sg::AABB(sg::Vec3(-0.3f, -0.3f, -0.3f), sg::Vec3(0.3f, 0.3f, 0.3f)));
    earth->addChild(moon);

    // Update transforms
    sun->updateTransforms();

    // Check world positions
    ASSERT_FLOAT_EQ(sun->getWorldPosition().x, 0.0f);
    ASSERT_FLOAT_EQ(earth->getWorldPosition().x, 10.0f);
    ASSERT_FLOAT_EQ(moon->getWorldPosition().x, 12.0f);

    // Create camera looking at the system
    sg::Camera camera;
    camera.setPosition(sg::Vec3(0, 10, 20));
    camera.setTarget(sg::Vec3(0, 0, 0));
    camera.setPerspective(sg::degToRad(60), 16.0f/9.0f, 0.1f, 100.0f);

    // Render
    sg::Renderer renderer;
    renderer.setCamera(&camera);
    renderer.processScene(sun);

    std::cout << "\nSolar System Scene:\n" << renderer.getRenderListString() << std::endl;

    // All objects should be visible
    const auto& stats = renderer.getStats();
    ASSERT_EQ(stats.visibleNodes, 3);
    ASSERT_EQ(stats.culledNodes, 0);
}

// ============================================================================
// Main
// ============================================================================
int main() {
    TestRunner runner;

    runner.addTest("Vec3 Operations", test_vec3_operations);
    runner.addTest("Mat4 Operations", test_mat4_operations);
    runner.addTest("Transform", test_transform);
    runner.addTest("Node Hierarchy", test_node_hierarchy);
    runner.addTest("Transform Hierarchy", test_transform_hierarchy);
    runner.addTest("AABB", test_aabb);
    runner.addTest("Frustum Culling", test_frustum_culling);
    runner.addTest("Frustum Culling Scene", test_frustum_culling_scene);
    runner.addTest("Node Traversal", test_node_traversal);
    runner.addTest("Node Flags", test_node_flags);
    runner.addTest("Camera", test_camera);
    runner.addTest("Dirty Propagation", test_dirty_propagation);
    runner.addTest("Complex Scene", test_complex_scene);

    return runner.runAll();
}
