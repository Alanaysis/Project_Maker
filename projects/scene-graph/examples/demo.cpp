/**
 * 场景图系统演示程序
 *
 * 演示场景图的核心功能：
 * 1. 创建层级化的场景图
 * 2. 变换传播（父子节点）
 * 3. 视锥裁剪
 * 4. 包围盒计算
 */

#include "../include/scene_graph.h"
#include <iostream>
#include <iomanip>
#include <memory>

using namespace sg;

// 简单的可渲染对象（用于演示）
class Cube : public Renderable {
public:
    Cube(float size) : size_(size) {}

    AABB get_local_bounds() const override {
        float half = size_ / 2.0f;
        return AABB::from_center_size({0, 0, 0}, {half, half, half});
    }

    std::string get_type() const override { return "Cube"; }
    float get_size() const { return size_; }

private:
    float size_;
};

// 辅助函数：打印向量
void print_vec3(const std::string& label, const Vec3& v) {
    std::cout << label << ": ("
              << std::fixed << std::setprecision(2)
              << v.x << ", " << v.y << ", " << v.z << ")" << std::endl;
}

// 辅助函数：打印 AABB
void print_aabb(const std::string& label, const AABB& aabb) {
    std::cout << label << ":" << std::endl;
    print_vec3("  min", aabb.min);
    print_vec3("  max", aabb.max);
    print_vec3("  center", aabb.center());
}

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "  场景图系统演示" << std::endl;
    std::cout << "==========================================" << std::endl;
    std::cout << std::endl;

    // ========== 1. 创建场景图 ==========
    std::cout << "--- 1. 创建场景图 ---" << std::endl;
    SceneGraph scene;

    // 创建根节点（代表世界）
    auto root = scene.get_root();

    // 创建一个太阳系场景
    // 太阳 -> 地球 -> 月球
    auto sun = std::make_shared<SceneNode>("Sun");
    sun->set_renderable(std::make_shared<Cube>(2.0f));
    sun->get_transform().position = Vec3(0, 0, -10);
    root->add_child(sun);

    auto earth = std::make_shared<SceneNode>("Earth");
    earth->set_renderable(std::make_shared<Cube>(1.0f));
    earth->get_transform().position = Vec3(5, 0, 0);
    sun->add_child(earth);

    auto moon = std::make_shared<SceneNode>("Moon");
    moon->set_renderable(std::make_shared<Cube>(0.3f));
    moon->get_transform().position = Vec3(1.5f, 0, 0);
    earth->add_child(moon);

    // 添加一个遥远的星星（用于演示裁剪）
    auto star = std::make_shared<SceneNode>("Star");
    star->set_renderable(std::make_shared<Cube>(1.0f));
    star->get_transform().position = Vec3(500, 0, 0);
    root->add_child(star);

    std::cout << "场景节点数: " << scene.total_node_count() << std::endl;
    std::cout << std::endl;

    // ========== 2. 变换层级计算 ==========
    std::cout << "--- 2. 变换层级计算 ---" << std::endl;

    // 设置地球自转
    earth->get_transform().set_rotation_euler(0, 30, 0);

    // 更新所有变换
    scene.update();

    std::cout << "太阳世界位置: ";
    print_vec3("", sun->get_world_position());

    std::cout << "地球世界位置: ";
    print_vec3("", earth->get_world_position());

    std::cout << "月球世界位置: ";
    print_vec3("", moon->get_world_position());

    // 演示旋转后的变换
    std::cout << std::endl;
    std::cout << "旋转地球 90 度..." << std::endl;
    earth->get_transform().set_rotation_euler(0, 90, 0);
    scene.update();

    std::cout << "旋转后月球世界位置: ";
    print_vec3("", moon->get_world_position());
    std::cout << std::endl;

    // ========== 3. 包围盒计算 ==========
    std::cout << "--- 3. 包围盒计算 ---" << std::endl;

    print_aabb("太阳包围盒 (世界空间)", sun->get_world_bounds());
    print_aabb("地球包围盒 (世界空间)", earth->get_world_bounds());
    print_aabb("月球包围盒 (世界空间)", moon->get_world_bounds());
    std::cout << std::endl;

    // ========== 4. 视锥裁剪 ==========
    std::cout << "--- 4. 视锥裁剪 ---" << std::endl;

    // 设置摄像机
    Camera camera;
    camera.set_position({0, 5, 5});
    camera.set_target({0, 0, -10});
    camera.set_fov(60.0f);
    camera.set_aspect_ratio(16.0f / 9.0f);
    camera.set_near_far(0.1f, 100.0f);
    scene.set_camera(camera);

    // 执行裁剪
    auto result = scene.cull();

    std::cout << "裁剪结果:" << std::endl;
    std::cout << "  遍历节点数: " << result.total_nodes << std::endl;
    std::cout << "  可见节点数: " << result.visible_nodes << std::endl;
    std::cout << "  裁剪节点数: " << result.culled_nodes << std::endl;
    std::cout << "  提前退出数: " << result.early_exits << std::endl;

    std::cout << "可见物体:" << std::endl;
    for (const auto& node : scene.get_visible_nodes()) {
        std::cout << "  - " << node->get_name() << std::endl;
    }
    std::cout << std::endl;

    // ========== 5. 场景图遍历 ==========
    std::cout << "--- 5. 场景图遍历 (深度优先) ---" << std::endl;
    scene.traverse([](const SceneNodePtr& node) {
        int depth = node->get_depth();
        std::string indent(depth * 2, ' ');
        std::cout << indent << node->get_name()
                  << " [ID:" << node->get_id() << "]"
                  << (node->get_renderable() ? " [Renderable]" : "")
                  << std::endl;
    });
    std::cout << std::endl;

    // ========== 6. 动态修改场景 ==========
    std::cout << "--- 6. 动态修改场景 ---" << std::endl;

    // 隐藏太阳
    sun->set_visible(false);
    scene.update();
    result = scene.cull();

    std::cout << "隐藏太阳后:" << std::endl;
    std::cout << "  可见节点数: " << result.visible_nodes << std::endl;
    std::cout << "  裁剪节点数: " << result.culled_nodes << std::endl;

    // 重新显示
    sun->set_visible(true);
    scene.update();
    result = scene.cull();

    std::cout << "重新显示太阳后:" << std::endl;
    std::cout << "  可见节点数: " << result.visible_nodes << std::endl;

    std::cout << std::endl;
    std::cout << "==========================================" << std::endl;
    std::cout << "  演示完成！" << std::endl;
    std::cout << "==========================================" << std::endl;

    return 0;
}
