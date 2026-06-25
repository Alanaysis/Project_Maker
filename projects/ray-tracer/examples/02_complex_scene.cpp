/**
 * 示例 2: 复杂场景渲染
 *
 * 本示例展示如何渲染包含多个物体和材质的复杂场景。
 * 包含：随机球体、金属材质、玻璃材质。
 */

#include "../include/vec3.h"
#include "../include/ray.h"
#include "../include/hitable.h"
#include "../include/sphere.h"
#include "../include/material.h"
#include "../include/camera.h"
#include "../include/renderer.h"
#include "../include/scene.h"
#include <iostream>

int main() {
    std::cout << "=== 复杂场景渲染示例 ===" << std::endl;

    // 创建复杂场景
    auto world = rt::SceneFactory::create_complex_scene();

    // 配置相机
    rt::CameraConfig cam_config;
    cam_config.lookfrom = rt::Vec3(13, 2, 3);
    cam_config.lookat = rt::Vec3(0, 0, 0);
    cam_config.vup = rt::Vec3(0, 1, 0);
    cam_config.vfov = 20.0;
    cam_config.aspect_ratio = 16.0 / 9.0;
    cam_config.aperture = 0.1;
    cam_config.focus_dist = 10.0;

    rt::Camera camera(cam_config);

    // 配置渲染参数
    rt::RenderConfig render_config;
    render_config.width = 800;
    render_config.height = 450;
    render_config.samples_per_pixel = 100;
    render_config.max_depth = 50;

    // 创建渲染器并渲染
    rt::Renderer renderer(render_config, camera, world);
    renderer.render("complex_scene.ppm");

    std::cout << "渲染完成！输出文件: complex_scene.ppm" << std::endl;
    return 0;
}
