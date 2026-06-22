#include <gtest/gtest.h>
#include "../include/scene_node.h"

using namespace sg;

// 简单的可渲染对象实现，用于测试
class SimpleRenderable : public Renderable {
public:
    SimpleRenderable(const AABB& bounds) : bounds_(bounds) {}

    AABB get_local_bounds() const override { return bounds_; }
    std::string get_type() const override { return "Simple"; }

private:
    AABB bounds_;
};

class SceneNodeTest : public ::testing::Test {
protected:
    void SetUp() override {
        root = std::make_shared<SceneNode>("Root");
    }

    SceneNodePtr root;
};

TEST_F(SceneNodeTest, CreateNode) {
    EXPECT_EQ(root->get_name(), "Root");
    EXPECT_TRUE(root->is_visible());
    EXPECT_EQ(root->child_count(), 0);
    EXPECT_EQ(root->get_depth(), 0);
}

TEST_F(SceneNodeTest, AddChild) {
    auto child = std::make_shared<SceneNode>("Child");
    root->add_child(child);
    EXPECT_EQ(root->child_count(), 1);
    EXPECT_EQ(child->get_parent(), root);
    EXPECT_EQ(child->get_depth(), 1);
}

TEST_F(SceneNodeTest, RemoveChild) {
    auto child = std::make_shared<SceneNode>("Child");
    root->add_child(child);
    EXPECT_EQ(root->child_count(), 1);
    root->remove_child(child);
    EXPECT_EQ(root->child_count(), 0);
    EXPECT_EQ(child->get_parent(), nullptr);
}

TEST_F(SceneNodeTest, FindByName) {
    auto child1 = std::make_shared<SceneNode>("Child1");
    auto child2 = std::make_shared<SceneNode>("Child2");
    auto grandchild = std::make_shared<SceneNode>("GrandChild");

    root->add_child(child1);
    root->add_child(child2);
    child1->add_child(grandchild);

    EXPECT_EQ(root->find("Child1"), child1);
    EXPECT_EQ(root->find("GrandChild"), grandchild);
    EXPECT_EQ(root->find("NonExistent"), nullptr);
}

TEST_F(SceneNodeTest, FindById) {
    auto child = std::make_shared<SceneNode>("Child");
    root->add_child(child);
    uint64_t id = child->get_id();
    EXPECT_EQ(root->find_by_id(id), child);
}

TEST_F(SceneNodeTest, WorldTransformRoot) {
    root->get_transform().position = Vec3(1, 2, 3);
    root->update_transforms();
    Vec3 wp = root->get_world_position();
    EXPECT_FLOAT_EQ(wp.x, 1.0f);
    EXPECT_FLOAT_EQ(wp.y, 2.0f);
    EXPECT_FLOAT_EQ(wp.z, 3.0f);
}

TEST_F(SceneNodeTest, WorldTransformHierarchy) {
    root->get_transform().position = Vec3(1, 0, 0);
    auto child = std::make_shared<SceneNode>("Child");
    child->get_transform().position = Vec3(0, 2, 0);
    root->add_child(child);

    root->update_transforms();

    Vec3 wp = child->get_world_position();
    EXPECT_FLOAT_EQ(wp.x, 1.0f);
    EXPECT_FLOAT_EQ(wp.y, 2.0f);
    EXPECT_FLOAT_EQ(wp.z, 0.0f);
}

TEST_F(SceneNodeTest, WorldTransformWithScale) {
    root->get_transform().scale = Vec3(2, 2, 2);
    auto child = std::make_shared<SceneNode>("Child");
    child->get_transform().position = Vec3(1, 0, 0);
    root->add_child(child);

    root->update_transforms();

    Vec3 wp = child->get_world_position();
    EXPECT_FLOAT_EQ(wp.x, 2.0f);
    EXPECT_FLOAT_EQ(wp.y, 0.0f);
    EXPECT_FLOAT_EQ(wp.z, 0.0f);
}

TEST_F(SceneNodeTest, WorldTransformDeepHierarchy) {
    root->get_transform().position = Vec3(1, 0, 0);
    auto child1 = std::make_shared<SceneNode>("Child1");
    child1->get_transform().position = Vec3(0, 1, 0);
    auto child2 = std::make_shared<SceneNode>("Child2");
    child2->get_transform().position = Vec3(0, 0, 1);

    root->add_child(child1);
    child1->add_child(child2);

    root->update_transforms();

    Vec3 wp = child2->get_world_position();
    EXPECT_FLOAT_EQ(wp.x, 1.0f);
    EXPECT_FLOAT_EQ(wp.y, 1.0f);
    EXPECT_FLOAT_EQ(wp.z, 1.0f);
}

TEST_F(SceneNodeTest, WorldBoundsWithRenderable) {
    auto renderable = std::make_shared<SimpleRenderable>(
        AABB::from_center_size({0, 0, 0}, {1, 1, 1})
    );
    root->set_renderable(renderable);
    root->update_transforms();

    const AABB& bounds = root->get_world_bounds();
    EXPECT_NEAR(bounds.min.x, -1.0f, 1e-5f);
    EXPECT_NEAR(bounds.max.x, 1.0f, 1e-5f);
}

TEST_F(SceneNodeTest, WorldBoundsWithTransform) {
    auto renderable = std::make_shared<SimpleRenderable>(
        AABB::from_center_size({0, 0, 0}, {1, 1, 1})
    );
    root->set_renderable(renderable);
    root->get_transform().position = Vec3(10, 0, 0);
    root->update_transforms();

    const AABB& bounds = root->get_world_bounds();
    EXPECT_NEAR(bounds.min.x, 9.0f, 1e-5f);
    EXPECT_NEAR(bounds.max.x, 11.0f, 1e-5f);
}

TEST_F(SceneNodeTest, WorldBoundsIncludesChildren) {
    root->get_transform().position = Vec3(0, 0, 0);

    auto child1 = std::make_shared<SceneNode>("Child1");
    child1->set_renderable(std::make_shared<SimpleRenderable>(
        AABB::from_center_size({0, 0, 0}, {1, 1, 1})
    ));
    child1->get_transform().position = Vec3(10, 0, 0);

    auto child2 = std::make_shared<SceneNode>("Child2");
    child2->set_renderable(std::make_shared<SimpleRenderable>(
        AABB::from_center_size({0, 0, 0}, {1, 1, 1})
    ));
    child2->get_transform().position = Vec3(-10, 0, 0);

    root->add_child(child1);
    root->add_child(child2);
    root->update_transforms();

    const AABB& bounds = root->get_world_bounds();
    EXPECT_NEAR(bounds.min.x, -11.0f, 1e-5f);
    EXPECT_NEAR(bounds.max.x, 11.0f, 1e-5f);
}

TEST_F(SceneNodeTest, Visibility) {
    EXPECT_TRUE(root->is_visible());
    root->set_visible(false);
    EXPECT_FALSE(root->is_visible());
}

TEST_F(SceneNodeTest, TraverseDfs) {
    auto child1 = std::make_shared<SceneNode>("Child1");
    auto child2 = std::make_shared<SceneNode>("Child2");
    auto grandchild = std::make_shared<SceneNode>("GrandChild");

    root->add_child(child1);
    root->add_child(child2);
    child1->add_child(grandchild);

    std::vector<std::string> names;
    root->traverse_dfs([&names](const SceneNodePtr& node) {
        names.push_back(node->get_name());
    });

    ASSERT_EQ(names.size(), 4);
    EXPECT_EQ(names[0], "Root");
    EXPECT_EQ(names[1], "Child1");
    EXPECT_EQ(names[2], "GrandChild");
    EXPECT_EQ(names[3], "Child2");
}

TEST_F(SceneNodeTest, TotalNodeCount) {
    auto child1 = std::make_shared<SceneNode>("Child1");
    auto child2 = std::make_shared<SceneNode>("Child2");
    auto grandchild = std::make_shared<SceneNode>("GrandChild");

    root->add_child(child1);
    root->add_child(child2);
    child1->add_child(grandchild);

    EXPECT_EQ(root->total_node_count(), 4);
}

TEST_F(SceneNodeTest, CustomBounds) {
    root->set_local_bounds(AABB::from_center_size({0, 0, 0}, {5, 5, 5}));
    root->update_transforms();

    const AABB& bounds = root->get_world_bounds();
    EXPECT_NEAR(bounds.min.x, -5.0f, 1e-5f);
    EXPECT_NEAR(bounds.max.x, 5.0f, 1e-5f);
}

TEST_F(SceneNodeTest, ReparentChild) {
    auto parent1 = std::make_shared<SceneNode>("Parent1");
    auto parent2 = std::make_shared<SceneNode>("Parent2");
    auto child = std::make_shared<SceneNode>("Child");

    parent1->add_child(child);
    EXPECT_EQ(child->get_parent(), parent1);

    parent2->add_child(child);
    EXPECT_EQ(child->get_parent(), parent2);
    EXPECT_EQ(parent1->child_count(), 0);
}
