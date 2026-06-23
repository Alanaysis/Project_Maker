#include "../include/renderer.h"
#include "../include/scene.h"
#include <iostream>
#include <cassert>
#include <cmath>

using namespace std;

void test_ray_color_background() {
    rt::RenderConfig config;
    config.width = 10;
    config.height = 10;
    config.samples_per_pixel = 1;
    config.max_depth = 5;

    rt::CameraConfig cam_config;
    rt::Camera camera(cam_config);

    auto world = std::make_shared<rt::HitableList>();
    rt::Renderer renderer(config, camera, world);

    // 向上发射光线应该得到天空颜色
    rt::Ray ray(rt::Vec3(0, 0, 0), rt::Vec3(0, 1, 0));
    rt::Color color = renderer.ray_color(ray, 5);

    // 天空颜色应该是渐变的
    assert(color.y > 0.5); // 应该有蓝色分量

    std::cout << "  [PASS] Ray Color Background" << std::endl;
}

void test_ray_color_object() {
    rt::RenderConfig config;
    config.width = 10;
    config.height = 10;
    config.samples_per_pixel = 1;
    config.max_depth = 5;

    rt::CameraConfig cam_config;
    rt::Camera camera(cam_config);

    // 创建简单场景
    auto world = rt::SceneFactory::create_test_scene();
    rt::Renderer renderer(config, camera, world);

    // 向红色球体发射光线
    rt::Ray ray(rt::Vec3(0, 0, 0), rt::Vec3(0, 0, -1));
    rt::Color color = renderer.ray_color(ray, 5);

    // 应该有红色分量
    assert(color.x > 0);

    std::cout << "  [PASS] Ray Color Object" << std::endl;
}

void test_ray_color_max_depth() {
    rt::RenderConfig config;
    config.width = 10;
    config.height = 10;
    config.samples_per_pixel = 1;
    config.max_depth = 0; // 零深度

    rt::CameraConfig cam_config;
    rt::Camera camera(cam_config);

    auto world = rt::SceneFactory::create_test_scene();
    rt::Renderer renderer(config, camera, world);

    // 即使有物体，深度为 0 应该返回黑色
    rt::Ray ray(rt::Vec3(0, 0, 0), rt::Vec3(0, 0, -1));
    rt::Color color = renderer.ray_color(ray, 0);

    assert(color.x == 0);
    assert(color.y == 0);
    assert(color.z == 0);

    std::cout << "  [PASS] Ray Color Max Depth" << std::endl;
}

void test_render_to_buffer() {
    rt::RenderConfig config;
    config.width = 4;
    config.height = 3;
    config.samples_per_pixel = 1;
    config.max_depth = 5;

    rt::CameraConfig cam_config;
    rt::Camera camera(cam_config);

    auto world = rt::SceneFactory::create_test_scene();
    rt::Renderer renderer(config, camera, world);

    auto buffer = renderer.render_to_buffer();

    // 检查缓冲区大小
    assert(buffer.size() == 3);  // height
    assert(buffer[0].size() == 4);  // width

    // 检查颜色值在合理范围内
    for (int y = 0; y < 3; y++) {
        for (int x = 0; x < 4; x++) {
            assert(buffer[y][x].x >= 0 && buffer[y][x].x <= 1);
            assert(buffer[y][x].y >= 0 && buffer[y][x].y <= 1);
            assert(buffer[y][x].z >= 0 && buffer[y][x].z <= 1);
        }
    }

    std::cout << "  [PASS] Render To Buffer" << std::endl;
}

int main() {
    std::cout << "Running Renderer tests..." << std::endl;

    test_ray_color_background();
    test_ray_color_object();
    test_ray_color_max_depth();
    test_render_to_buffer();

    std::cout << "All Renderer tests passed!" << std::endl;
    return 0;
}
