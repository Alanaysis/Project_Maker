/**
 * 示例 8: 运动模糊
 *
 * 本示例展示如何使用运动模糊效果。
 * 运动模糊可以让移动的物体看起来更自然。
 */

#include "../include/vec3.h"
#include "../include/ray.h"
#include "../include/hitable.h"
#include "../include/sphere.h"
#include "../include/material.h"
#include "../include/camera.h"
#include "../include/renderer.h"
#include "../include/advanced_features.h"
#include <iostream>

int main() {
    std::cout << "=== 运动模糊示例 ===" << std::endl;

    auto world = std::make_shared<rt::HitableList>();

    // 地面
    auto ground = std::make_shared<rt::Lambertian>(rt::Vec3(0.5, 0.5, 0.5));
    world->add(std::make_shared<rt::Plane>(rt::Vec3(0, 0, 0), rt::Vec3(0, 1, 0), ground));

    // 运动模糊的球体
    auto red = std::make_shared<rt::Lambertian>(rt::Vec3(0.9, 0.1, 0.1));
    world->add(std::make_shared<rt::MovingSphere>(
        rt::Vec3(-1, 0.5, 0),   // 起始位置
        rt::Vec3(1, 0.5, 0),    // 结束位置
        0.0, 1.0,               // 时间范围
        0.5,                    // 半径
        red));

    // 静止的金属球体
    auto metal = std::make_shared<rt::Metal>(rt::Vec3(0.8, 0.8, 0.8), 0.1);
    world->add(std::make_shared<rt::Sphere>(rt::Vec3(0, 0.5, -2), 0.5, metal));

    // 配置相机
    rt::CameraConfig cam_config;
    cam_config.lookfrom = rt::Vec3(0, 3, 6);
    cam_config.lookat = rt::Vec3(0, 0.5, 0);
    cam_config.vfov = 45.0;
    cam_config.aspect_ratio = 16.0 / 9.0;

    rt::Camera camera(cam_config);

    // 配置渲染参数
    rt::RenderConfig render_config;
    render_config.width = 400;
    render_config.height = 225;
    render_config.samples_per_pixel = 50;
    render_config.max_depth = 30;

    // 创建渲染器并渲染
    rt::Renderer renderer(render_config, camera, world);
    renderer.render("motion_blur.ppm");

    std::cout << "渲染完成！输出文件: motion_blur.ppm" << std::endl;
    return 0;
}
