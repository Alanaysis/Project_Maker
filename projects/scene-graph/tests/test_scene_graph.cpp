#include <gtest/gtest.h>
#include "../include/scene_graph.h"

using namespace sg;

// 简单的可渲染对象实现
class TestRenderable : public Renderable {
public:
    TestRenderable(const AABB& bounds) : bounds_(bounds) {}
    AABB get_local_bounds() const override { return bounds_; }
    std::string get_type() const override { return "Test"; }
private:
    AABB bounds_;
};

class SceneGraphTest : public ::testing::Test {
protected:
    void SetUp() override {
        graph = std::make_unique<SceneGraph>();
        camera.set_position({0, 0, 10});
        camera.set_target({0, 0, 0});
        camera.set_fov(60.0f);
        camera.set_aspect_ratio(16.0f / 9.0f);
        camera.set_near_far(0.1f, 1000.0f);
        graph->set_camera(camera);
    }

    std::unique_ptr<SceneGraph> graph;
    Camera camera;
};

TEST_F(SceneGraphTest, CreateSceneGraph) {
    EXPECT_NE(graph->get_root(), nullptr);
    EXPECT_EQ(graph->get_root()->get_name(), "Root");
}

TEST_F(SceneGraphTest, FindNode) {
    auto child = std::make_shared<SceneNode>("TestNode");
    graph->get_root()->add_child(child);
    EXPECT_EQ(graph->find("TestNode"), child);
}

TEST_F(SceneGraphTest, TotalNodeCount) {
    auto child1 = std::make_shared<SceneNode>("Child1");
    auto child2 = std::make_shared<SceneNode>("Child2");
    graph->get_root()->add_child(child1);
    graph->get_root()->add_child(child2);
    EXPECT_EQ(graph->total_node_count(), 3); // Root + Child1 + Child2
}

TEST_F(SceneGraphTest, UpdateTransforms) {
    auto child = std::make_shared<SceneNode>("Child");
    child->get_transform().position = Vec3(5, 0, 0);
    graph->get_root()->add_child(child);

    graph->update();

    Vec3 wp = child->get_world_position();
    EXPECT_FLOAT_EQ(wp.x, 5.0f);
    EXPECT_FLOAT_EQ(wp.y, 0.0f);
    EXPECT_FLOAT_EQ(wp.z, 0.0f);
}

TEST_F(SceneGraphTest, CullAllVisible) {
    // 在摄像机前方的物体应该可见
    auto node = std::make_shared<SceneNode>("Visible");
    node->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({0, 0, 0}, {1, 1, 1})
    ));
    graph->get_root()->add_child(node);

    graph->update();
    auto result = graph->cull();

    EXPECT_EQ(result.visible_nodes, 1);
    EXPECT_EQ(result.culled_nodes, 0);
    EXPECT_EQ(graph->get_visible_nodes().size(), 1);
}

TEST_F(SceneGraphTest, CullBehindCamera) {
    // 在摄像机后面的物体应该被裁剪
    auto node = std::make_shared<SceneNode>("Behind");
    node->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({0, 0, 20}, {1, 1, 1})
    ));
    graph->get_root()->add_child(node);

    graph->update();
    auto result = graph->cull();

    EXPECT_EQ(result.visible_nodes, 0);
    EXPECT_EQ(result.culled_nodes, 1);
    EXPECT_EQ(graph->get_visible_nodes().size(), 0);
}

TEST_F(SceneGraphTest, CullOutsideFrustum) {
    // 在视锥体外的物体应该被裁剪
    auto node = std::make_shared<SceneNode>("Outside");
    node->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({500, 500, 0}, {1, 1, 1})
    ));
    graph->get_root()->add_child(node);

    graph->update();
    auto result = graph->cull();

    EXPECT_EQ(result.visible_nodes, 0);
    EXPECT_EQ(result.culled_nodes, 1);
}

TEST_F(SceneGraphTest, CullHierarchy) {
    // 测试层级裁剪：如果父节点被裁剪，子节点也被裁剪
    // 使用不可见的父节点来测试层级裁剪
    auto parent = std::make_shared<SceneNode>("Parent");
    parent->set_visible(false);  // 设置为不可见
    parent->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({0, 0, 0}, {1, 1, 1})
    ));
    auto child = std::make_shared<SceneNode>("Child");
    child->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({0, 0, 0}, {1, 1, 1})
    ));
    parent->add_child(child);
    graph->get_root()->add_child(parent);

    graph->update();
    auto result = graph->cull();

    // 父节点不可见，子节点也应该被跳过
    EXPECT_EQ(result.culled_nodes, 2);  // 父节点和子节点都被裁剪
    EXPECT_EQ(graph->get_visible_nodes().size(), 0);
}

TEST_F(SceneGraphTest, CullMixedVisibility) {
    // 一个可见，一个不可见
    auto visible = std::make_shared<SceneNode>("Visible");
    visible->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({0, 0, 0}, {1, 1, 1})
    ));

    auto hidden = std::make_shared<SceneNode>("Hidden");
    hidden->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({500, 500, 0}, {1, 1, 1})
    ));

    graph->get_root()->add_child(visible);
    graph->get_root()->add_child(hidden);

    graph->update();
    auto result = graph->cull();

    EXPECT_EQ(result.visible_nodes, 1);
    EXPECT_EQ(result.culled_nodes, 1);
    EXPECT_EQ(graph->get_visible_nodes().size(), 1);
}

TEST_F(SceneGraphTest, CullInvisibleNode) {
    // 设置节点为不可见
    auto node = std::make_shared<SceneNode>("Invisible");
    node->set_visible(false);
    node->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({0, 0, 0}, {1, 1, 1})
    ));
    graph->get_root()->add_child(node);

    graph->update();
    auto result = graph->cull();

    EXPECT_EQ(result.visible_nodes, 0);
    EXPECT_EQ(result.culled_nodes, 1);
}

TEST_F(SceneGraphTest, CullOnlyRenderableNodes) {
    // 没有可渲染对象的节点不会参与裁剪
    auto node = std::make_shared<SceneNode>("Empty");
    // 不设置 renderable
    graph->get_root()->add_child(node);

    graph->update();
    auto result = graph->cull();

    // 节点没有 renderable，跳过裁剪测试，不计入 visible 或 culled
    EXPECT_EQ(result.visible_nodes, 0);
    EXPECT_EQ(result.culled_nodes, 0);
    EXPECT_EQ(graph->get_visible_nodes().size(), 0);
}

TEST_F(SceneGraphTest, CameraGetters) {
    EXPECT_FLOAT_EQ(camera.get_fov(), 60.0f);
    EXPECT_FLOAT_EQ(camera.get_near(), 0.1f);
    EXPECT_FLOAT_EQ(camera.get_far(), 1000.0f);
}

TEST_F(SceneGraphTest, FrustumFromCamera) {
    Frustum frustum = camera.get_frustum();
    EXPECT_TRUE(frustum.test_point({0, 0, 0}));
    EXPECT_FALSE(frustum.test_point({100, 100, 0}));
}

TEST_F(SceneGraphTest, Traverse) {
    auto child1 = std::make_shared<SceneNode>("Child1");
    auto child2 = std::make_shared<SceneNode>("Child2");
    graph->get_root()->add_child(child1);
    graph->get_root()->add_child(child2);

    std::vector<std::string> names;
    graph->traverse([&names](const SceneNodePtr& node) {
        names.push_back(node->get_name());
    });

    ASSERT_EQ(names.size(), 3);
    EXPECT_EQ(names[0], "Root");
    EXPECT_EQ(names[1], "Child1");
    EXPECT_EQ(names[2], "Child2");
}

TEST_F(SceneGraphTest, CullDeepHierarchy) {
    // 测试多层级的裁剪
    auto level1 = std::make_shared<SceneNode>("L1");
    level1->get_transform().position = Vec3(0, 0, 0);

    auto level2 = std::make_shared<SceneNode>("L2");
    level2->get_transform().position = Vec3(1, 0, 0);
    level2->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({0, 0, 0}, {0.5f, 0.5f, 0.5f})
    ));

    auto level3 = std::make_shared<SceneNode>("L3");
    level3->get_transform().position = Vec3(1, 0, 0);
    level3->set_renderable(std::make_shared<TestRenderable>(
        AABB::from_center_size({0, 0, 0}, {0.5f, 0.5f, 0.5f})
    ));

    level2->add_child(level3);
    level1->add_child(level2);
    graph->get_root()->add_child(level1);

    graph->update();
    auto result = graph->cull();

    EXPECT_EQ(result.visible_nodes, 2); // L2 和 L3 的 renderable
    EXPECT_EQ(graph->get_visible_nodes().size(), 2);
}
