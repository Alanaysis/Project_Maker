/**
 * 示例 7: 高级材质渲染
 *
 * 本示例展示如何使用各种高级材质：自发光、各向异性、清漆、混合材质等。
 */

#include "../include/vec3.h"
#include "../include/ray.h"
#include "../include/hitable.h"
#include "../include/sphere.h"
#include "../include/material.h"
#include "../include/camera.h"
#include "../include/renderer.h"
#include "../include/advanced_material.h"
#include <iostream>

int main() {
    std::cout << "=== 高级材质渲染示例 ===" << std::endl;

    auto world = std::make_shared<rt::HitableList>();

    // 地面
    auto ground = std::make_shared<rt::Lambertian>(rt::Vec3(0.5, 0.5, 0.5));
    world->add(std::make_shared<rt::Plane>(rt::Vec3(0, 0, 0), rt::Vec3(0, 1, 0), ground));

    // 自发光材质
    auto emissive = std::make_shared<rt::Emissive>(rt::Vec3(1, 0.8, 0.2), 5.0);
    world->add(std::make_shared<rt::Sphere>(rt::Vec3(-2, 1, 0), 0.5, emissive));

    // 各向异性材质（拉丝金属效果）
    auto anisotropic = std::make_shared<rt::Anisotropic>(rt::Vec3(0.8, 0.6, 0.2), 0.3, 0.05);
    world->add(std::make_shared<rt::Sphere>(rt::Vec3(0, 1, 0), 0.5, anisotropic));

    // 清漆材质
    auto base = std::make_shared<rt::Lambertian>(rt::Vec3(0.8, 0.2, 0.2));
    auto clearcoat = std::make_shared<rt::Clearcoat>(base, 0.7, 0.05);
    world->add(std::make_shared<rt::Sphere>(rt::Vec3(2, 1, 0), 0.5, clearcoat));

    // 混合材质
    auto metal = std::make_shared<rt::Metal>(rt::Vec3(0.9, 0.9, 0.9), 0.1);
    auto diffuse = std::make_shared<rt::Lambertian>(rt::Vec3(0.2, 0.5, 0.8));
    auto blend = std::make_shared<rt::BlendMaterial>(metal, diffuse, 0.5);
    world->add(std::make_shared<rt::Sphere>(rt::Vec3(-1, 0.5, -2), 0.5, blend));

    // 菲涅尔材质
    auto glass = std::make_shared<rt::Dielectric>(1.5);
    auto gold = std::make_shared<rt::Metal>(rt::Vec3(0.8, 0.6, 0.2), 0.0);
    auto fresnel = std::make_shared<rt::FresnelBlend>(gold, glass);
    world->add(std::make_shared<rt::Sphere>(rt::Vec3(1, 0.5, -2), 0.5, fresnel));

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
    renderer.render("advanced_materials.ppm");

    std::cout << "渲染完成！输出文件: advanced_materials.ppm" << std::endl;
    return 0;
}
