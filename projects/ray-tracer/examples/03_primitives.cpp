/**
 * 示例 3: 几何图元渲染
 *
 * 本示例展示如何渲染各种几何图元：球体、平面、三角形、盒子、圆柱体。
 */

#include "../include/vec3.h"
#include "../include/ray.h"
#include "../include/hitable.h"
#include "../include/sphere.h"
#include "../include/triangle.h"
#include "../include/box.h"
#include "../include/cylinder.h"
#include "../include/material.h"
#include "../include/camera.h"
#include "../include/renderer.h"
#include <iostream>

int main() {
    std::cout << "=== 几何图元渲染示例 ===" << std::endl;

    auto world = std::make_shared<rt::HitableList>();

    // 地面
    auto ground = std::make_shared<rt::Lambertian>(rt::Vec3(0.5, 0.5, 0.5));
    world->add(std::make_shared<rt::Plane>(rt::Vec3(0, 0, 0), rt::Vec3(0, 1, 0), ground));

    // 球体
    auto red = std::make_shared<rt::Lambertian>(rt::Vec3(0.9, 0.1, 0.1));
    world->add(std::make_shared<rt::Sphere>(rt::Vec3(-3, 0.5, 0), 0.5, red));

    // 金属球体
    auto metal = std::make_shared<rt::Metal>(rt::Vec3(0.8, 0.8, 0.8), 0.1);
    world->add(std::make_shared<rt::Sphere>(rt::Vec3(-1, 0.5, 0), 0.5, metal));

    // 玻璃球体
    auto glass = std::make_shared<rt::Dielectric>(1.5);
    world->add(std::make_shared<rt::Sphere>(rt::Vec3(1, 0.5, 0), 0.5, glass));

    // 三角形
    auto blue = std::make_shared<rt::Lambertian>(rt::Vec3(0.1, 0.1, 0.9));
    world->add(std::make_shared<rt::Triangle>(
        rt::Vec3(3, 0, 0), rt::Vec3(4, 1, 0), rt::Vec3(3.5, 0, 1), blue));

    // 盒子
    auto green = std::make_shared<rt::Lambertian>(rt::Vec3(0.1, 0.9, 0.1));
    world->add(std::make_shared<rt::AABB>(
        rt::Vec3(-3, 0, 2), rt::Vec3(-2, 1, 3), green));

    // 圆柱体
    auto yellow = std::make_shared<rt::Lambertian>(rt::Vec3(0.9, 0.9, 0.1));
    world->add(std::make_shared<rt::Cylinder>(rt::Vec3(1, 0, 2), 0.3, 1.0, yellow));

    // 配置相机
    rt::CameraConfig cam_config;
    cam_config.lookfrom = rt::Vec3(0, 3, 8);
    cam_config.lookat = rt::Vec3(0, 0.5, 0);
    cam_config.vfov = 45.0;
    cam_config.aspect_ratio = 16.0 / 9.0;

    rt::Camera camera(cam_config);

    // 配置渲染参数
    rt::RenderConfig render_config;
    render_config.width = 800;
    render_config.height = 450;
    render_config.samples_per_pixel = 50;
    render_config.max_depth = 30;

    // 创建渲染器并渲染
    rt::Renderer renderer(render_config, camera, world);
    renderer.render("primitives.ppm");

    std::cout << "渲染完成！输出文件: primitives.ppm" << std::endl;
    return 0;
}
