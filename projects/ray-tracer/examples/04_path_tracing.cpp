/**
 * 示例 4: 路径追踪渲染
 *
 * 本示例展示如何使用路径追踪算法渲染场景。
 * 路径追踪是物理上更准确的渲染方法，支持全局光照。
 */

#include "../include/vec3.h"
#include "../include/ray.h"
#include "../include/hitable.h"
#include "../include/sphere.h"
#include "../include/material.h"
#include "../include/camera.h"
#include "../include/scene.h"
#include "../include/advanced_renderer.h"
#include "../include/light.h"
#include <iostream>

int main() {
    std::cout << "=== 路径追踪渲染示例 ===" << std::endl;

    // 创建场景
    auto world = rt::SceneFactory::create_default_scene();

    // 添加光源
    std::vector<std::shared_ptr<rt::Light>> lights;
    lights.push_back(std::make_shared<rt::PointLight>(
        rt::Vec3(5, 5, 5), rt::Vec3(1, 1, 1), 100.0));
    lights.push_back(std::make_shared<rt::DirectionalLight>(
        rt::Vec3(1, -1, 1), rt::Vec3(1, 0.95, 0.8), 0.5));

    // 配置相机
    rt::CameraConfig cam_config;
    cam_config.lookfrom = rt::Vec3(3, 3, 2);
    cam_config.lookat = rt::Vec3(0, 0, -1);
    cam_config.vfov = 20.0;
    cam_config.aspect_ratio = 16.0 / 9.0;
    cam_config.aperture = 0.05;
    cam_config.focus_dist = (rt::Vec3(3, 3, 2) - rt::Vec3(0, 0, -1)).length();

    rt::Camera camera(cam_config);

    // 配置渲染参数
    rt::RenderConfig render_config;
    render_config.width = 400;
    render_config.height = 225;
    render_config.samples_per_pixel = 100;
    render_config.max_depth = 50;

    // 创建路径追踪渲染器
    rt::PathTracer path_tracer(render_config, camera, world, lights);

    // 渲染
    path_tracer.render("path_tracing.ppm", 4);  // 使用 4 个线程

    std::cout << "渲染完成！输出文件: path_tracing.ppm" << std::endl;
    return 0;
}
