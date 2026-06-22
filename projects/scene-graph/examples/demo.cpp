#include "scene_graph/scene_graph.h"
#include <iostream>
#include <string>

using namespace sg;

// Helper to print indented tree
void printTree(NodePtr node, const std::string& prefix = "", bool isLast = true) {
    std::cout << prefix;
    std::cout << (isLast ? "└── " : "├── ");
    std::cout << node->getName();

    // Show position
    Vec3 pos = node->getTransform().position;
    std::cout << " [" << pos.x << ", " << pos.y << ", " << pos.z << "]";

    // Show visibility
    std::cout << " " << (node->isVisible() ? "[V]" : "[H]");

    std::cout << std::endl;

    const auto& children = node->getChildren();
    for (size_t i = 0; i < children.size(); ++i) {
        printTree(children[i], prefix + (isLast ? "    " : "│   "), i == children.size() - 1);
    }
}

// Create a game scene
NodePtr createGameScene() {
    auto root = Node::create("GameWorld");

    // Terrain
    auto terrain = Node::create("Terrain");
    terrain->setAABB(AABB(Vec3(-50, -1, -50), Vec3(50, 0, 50)));
    root->addChild(terrain);

    // Buildings
    auto buildings = Node::create("Buildings");
    buildings->getTransform().position = Vec3(0, 0, 0);
    root->addChild(buildings);

    auto house1 = Node::create("House1");
    house1->getTransform().position = Vec3(-10, 0, -5);
    house1->setAABB(AABB(Vec3(-2, 0, -2), Vec3(2, 4, 2)));
    buildings->addChild(house1);

    auto house2 = Node::create("House2");
    house2->getTransform().position = Vec3(10, 0, -5);
    house2->setAABB(AABB(Vec3(-3, 0, -2), Vec3(3, 5, 2)));
    buildings->addChild(house2);

    // Trees
    auto trees = Node::create("Trees");
    root->addChild(trees);

    for (int i = 0; i < 5; ++i) {
        auto tree = Node::create("Tree_" + std::to_string(i));
        tree->getTransform().position = Vec3(-20 + i * 10, 0, -15);
        tree->setAABB(AABB(Vec3(-0.5f, 0, -0.5f), Vec3(0.5f, 3, 0.5f)));
        trees->addChild(tree);
    }

    // Player
    auto player = Node::create("Player");
    player->getTransform().position = Vec3(0, 0, 5);
    player->setAABB(AABB(Vec3(-0.5f, 0, -0.5f), Vec3(0.5f, 1.8f, 0.5f)));
    player->addFlag(NodeFlag_CastShadow);
    root->addChild(player);

    // Enemies (far away)
    auto enemies = Node::create("Enemies");
    root->addChild(enemies);

    auto enemy1 = Node::create("Enemy1");
    enemy1->getTransform().position = Vec3(-30, 0, -40);
    enemy1->setAABB(AABB(Vec3(-0.5f, 0, -0.5f), Vec3(0.5f, 1.8f, 0.5f)));
    enemies->addChild(enemy1);

    auto enemy2 = Node::create("Enemy2");
    enemy2->getTransform().position = Vec3(40, 0, -60);
    enemy2->setAABB(AABB(Vec3(-0.5f, 0, -0.5f), Vec3(0.5f, 1.8f, 0.5f)));
    enemies->addChild(enemy2);

    // Skybox (very far, should be culled)
    auto skybox = Node::create("Skybox");
    skybox->setAABB(AABB(Vec3(-1000, -1000, -1000), Vec3(1000, 1000, 1000)));
    root->addChild(skybox);

    return root;
}

// Create a scene with deep hierarchy
NodePtr createDeepHierarchy() {
    auto root = Node::create("Root");

    // Robot arm with multiple joints
    auto shoulder = Node::create("Shoulder");
    shoulder->getTransform().position = Vec3(0, 2, 0);
    shoulder->setAABB(AABB(Vec3(-0.5f, -0.5f, -0.5f), Vec3(0.5f, 0.5f, 0.5f)));
    root->addChild(shoulder);

    auto upperArm = Node::create("UpperArm");
    upperArm->getTransform().position = Vec3(0, 1.5f, 0);
    upperArm->setAABB(AABB(Vec3(-0.2f, 0, -0.2f), Vec3(0.2f, 2, 0.2f)));
    shoulder->addChild(upperArm);

    auto elbow = Node::create("Elbow");
    elbow->getTransform().position = Vec3(0, 1.5f, 0);
    elbow->setAABB(AABB(Vec3(-0.3f, -0.3f, -0.3f), Vec3(0.3f, 0.3f, 0.3f)));
    upperArm->addChild(elbow);

    auto forearm = Node::create("Forearm");
    forearm->getTransform().position = Vec3(0, 1, 0);
    forearm->setAABB(AABB(Vec3(-0.15f, 0, -0.15f), Vec3(0.15f, 1.5f, 0.15f)));
    elbow->addChild(forearm);

    auto hand = Node::create("Hand");
    hand->getTransform().position = Vec3(0, 1.5f, 0);
    hand->setAABB(AABB(Vec3(-0.3f, -0.1f, -0.2f), Vec3(0.3f, 0.1f, 0.2f)));
    forearm->addChild(hand);

    return root;
}

void demoFrustumCulling() {
    std::cout << "========================================\n";
    std::cout << "  FRUSTUM CULLING DEMO\n";
    std::cout << "========================================\n\n";

    // Create scene
    NodePtr scene = createGameScene();

    // Print scene tree
    std::cout << "Scene Graph:\n";
    printTree(scene);
    std::cout << std::endl;

    // Setup camera
    Camera camera;
    camera.setPosition(Vec3(0, 15, 25));
    camera.setTarget(Vec3(0, 0, -10));
    camera.setPerspective(degToRad(60), 16.0f/9.0f, 0.1f, 100.0f);

    // Test with frustum culling
    std::cout << "--- With Frustum Culling ---\n";
    Renderer renderer;
    renderer.setCamera(&camera);
    renderer.setFrustumCullingEnabled(true);
    renderer.processScene(scene);
    std::cout << renderer.getRenderListString() << std::endl;

    // Test without frustum culling
    std::cout << "--- Without Frustum Culling ---\n";
    renderer.setFrustumCullingEnabled(false);
    renderer.processScene(scene);
    std::cout << renderer.getRenderListString() << std::endl;
}

void demoTransformHierarchy() {
    std::cout << "========================================\n";
    std::cout << "  TRANSFORM HIERARCHY DEMO\n";
    std::cout << "========================================\n\n";

    NodePtr robot = createDeepHierarchy();

    std::cout << "Robot Arm Hierarchy:\n";
    printTree(robot);
    std::cout << std::endl;

    // Update transforms
    robot->updateTransforms();

    // Print world positions
    std::cout << "World Positions:\n";
    robot->traverse([](NodePtr node) {
        Vec3 pos = node->getWorldPosition();
        std::string indent(node->getDepth() * 2, ' ');
        std::cout << indent << node->getName() << ": ("
                  << pos.x << ", " << pos.y << ", " << pos.z << ")\n";
    });
    std::cout << std::endl;

    // Simulate rotation at shoulder
    std::cout << "--- Rotating shoulder 30 degrees ---\n";
    robot->findChild("Shoulder")->getTransform().rotation.z = degToRad(30);
    robot->markDirty();
    robot->updateTransforms();

    std::cout << "Updated World Positions:\n";
    robot->traverse([](NodePtr node) {
        Vec3 pos = node->getWorldPosition();
        std::string indent(node->getDepth() * 2, ' ');
        std::cout << indent << node->getName() << ": ("
                  << pos.x << ", " << pos.y << ", " << pos.z << ")\n";
    });
    std::cout << std::endl;
}

void demoCullingComparison() {
    std::cout << "========================================\n";
    std::cout << "  CULLING EFFICIENCY COMPARISON\n";
    std::cout << "========================================\n\n";

    // Create a scene with many objects
    auto scene = Node::create("World");

    // Objects at various distances
    struct ObjectInfo {
        std::string name;
        Vec3 position;
    };

    std::vector<ObjectInfo> objects = {
        {"NearCube", {0, 0, -5}},
        {"MediumCube", {10, 0, -20}},
        {"FarCube", {-20, 0, -50}},
        {"VeryFarCube", {0, 0, -80}},
        {"BehindCamera", {0, 0, 20}},
        {"WayLeft", {-50, 0, -10}},
        {"WayRight", {50, 0, -10}},
        {"Above", {0, 50, -10}},
        {"Below", {0, -50, -10}},
    };

    for (const auto& obj : objects) {
        auto node = Node::create(obj.name);
        node->getTransform().position = obj.position;
        node->setAABB(AABB(Vec3(-1, -1, -1), Vec3(1, 1, 1)));
        scene->addChild(node);
    }

    // Camera setup
    Camera camera;
    camera.setPosition(Vec3(0, 5, 10));
    camera.setTarget(Vec3(0, 0, -10));
    camera.setPerspective(degToRad(45), 16.0f/9.0f, 0.1f, 100.0f);

    // Test different sort modes
    Renderer renderer;
    renderer.setCamera(&camera);

    // Unsorted
    renderer.setSortMode(Renderer::SortMode::None);
    renderer.processScene(scene);
    std::cout << "--- No Sorting ---\n" << renderer.getRenderListString() << std::endl;

    // Front to back
    renderer.setSortMode(Renderer::SortMode::FrontToBack);
    renderer.processScene(scene);
    renderer.sortCommands();
    std::cout << "--- Front to Back ---\n" << renderer.getRenderListString() << std::endl;

    // Back to front
    renderer.setSortMode(Renderer::SortMode::BackToFront);
    renderer.processScene(scene);
    renderer.sortCommands();
    std::cout << "--- Back to Front ---\n" << renderer.getRenderListString() << std::endl;
}

int main() {
    std::cout << "Scene Graph System - Demo\n";
    std::cout << "========================\n\n";

    demoFrustumCulling();
    std::cout << "\n\n";

    demoTransformHierarchy();
    std::cout << "\n\n";

    demoCullingComparison();

    return 0;
}
