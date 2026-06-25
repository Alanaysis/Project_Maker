/**
 * 示例 6: 纹理渲染
 *
 * 本示例展示如何使用各种纹理：棋盘格、噪声、渐变等。
 */

#include "../include/vec3.h"
#include "../include/ray.h"
#include "../include/hitable.h"
#include "../include/sphere.h"
#include "../include/material.h"
#include "../include/camera.h"
#include "../include/renderer.h"
#include "../include/texture.h"
#include "../include/advanced_material.h"
#include <iostream>

int main() {
    std::cout << "=== 纹理渲染示例 ===" << std::endl;

    auto world = std::make_shared<rt::HitableList>();

    // 棋盘格纹理
    auto checker = std::make_shared<rt::CheckerTexture>(2.0,
        rt::Vec3(0.9, 0.9, 0.9), rt::Vec3(0.1, 0.1, 0.1));
    auto checker_mat = std::make_shared<rt::TexturedMaterial>(checker);
    world->add(std::make_shared<rt::Plane>(rt::Vec3(0, 0, 0), rt::Vec3(0, 1, 0), checker_mat));

    // 噪声纹理
    auto noise = std::make_shared<rt::NoiseTexture>(4.0, rt::Vec3(0.8, 0.4, 0.2));
    auto noise_mat = std::make_shared<rt::TexturedMaterial>(noise);
    world->add(std::make_shared<rt::Sphere>(rt::Vec3(-1.5, 0.5, 0), 0.5, noise_mat));

    // 纯色纹理
    auto solid = std::make_shared<rt::SolidColor>(rt::Vec3(0.2, 0.5, 0.8));
    auto solid_mat = std::make_shared<rt::TexturedMaterial>(solid);
    world->add(std::make_shared<rt::Sphere>(rt::Vec3(0, 0.5, 0), 0.5, solid_mat));

    // 渐变纹理
    auto gradient = std::make_shared<rt::GradientTexture>(
        rt::Vec3(1, 0, 0), rt::Vec3(0, 0, 1), true);
    auto gradient_mat = std::make_shared<rt::TexturedMaterial>(gradient);
    world->add(std::make_shared<rt::Sphere>(rt::Vec3(1.5, 0.5, 0), 0.5, gradient_mat));

    // 配置相机
    rt::CameraConfig cam_config;
    cam_config.lookfrom = rt::Vec3(0, 3, 6);
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
    renderer.render("textures.ppm");

    std::cout << "渲染完成！输出文件: textures.ppm" << std::endl;
    return 0;
}
