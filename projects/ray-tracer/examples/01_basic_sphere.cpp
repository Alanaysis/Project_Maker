/**
 * 示例 1: 基础球体渲染
 *
 * 本示例展示如何使用光线追踪渲染一个简单的球体场景。
 * 包含：漫反射、金属、玻璃材质的球体。
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
    std::cout << "=== 基础球体渲染示例 ===" << std::endl;

    // 创建场景
    auto world = rt::SceneFactory::create_default_scene();

    // 配置相机
    rt::CameraConfig cam_config;
    cam_config.lookfrom = rt::Vec3(3, 3, 2);
    cam_config.lookat = rt::Vec3(0, 0, -1);
    cam_config.vup = rt::Vec3(0, 1, 0);
    cam_config.vfov = 20.0;
    cam_config.aspect_ratio = 16.0 / 9.0;
    cam_config.aperture = 0.1;
    cam_config.focus_dist = (rt::Vec3(3, 3, 2) - rt::Vec3(0, 0, -1)).length();

    rt::Camera camera(cam_config);

    // 配置渲染参数
    rt::RenderConfig render_config;
    render_config.width = 400;
    render_config.height = 225;
    render_config.samples_per_pixel = 50;
    render_config.max_depth = 30;

    // 创建渲染器并渲染
    rt::Renderer renderer(render_config, camera, world);
    renderer.render("basic_spheres.ppm");

    std::cout << "渲染完成！输出文件: basic_spheres.ppm" << std::endl;
    return 0;
}
