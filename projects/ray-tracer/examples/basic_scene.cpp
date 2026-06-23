#include "../include/renderer.h"
#include "../include/scene.h"
#include <iostream>

int main() {
    std::cout << "=== Basic Scene Example ===" << std::endl;
    std::cout << "This example demonstrates a simple ray-traced scene." << std::endl;
    std::cout << std::endl;

    // 创建场景
    auto world = rt::SceneFactory::create_default_scene();

    // 配置相机
    rt::CameraConfig cam_config;
    cam_config.lookfrom = rt::Vec3(3, 2, 2);
    cam_config.lookat = rt::Vec3(0, 0, -1);
    cam_config.vup = rt::Vec3(0, 1, 0);
    cam_config.vfov = 20.0;
    cam_config.aspect_ratio = 16.0 / 9.0;
    cam_config.aperture = 0.1;
    cam_config.focus_dist = (cam_config.lookfrom - cam_config.lookat).length();
    rt::Camera camera(cam_config);

    // 配置渲染参数
    rt::RenderConfig render_config;
    render_config.width = 200;
    render_config.height = 112;
    render_config.samples_per_pixel = 25;
    render_config.max_depth = 10;

    std::cout << "Scene: Default (3 spheres + ground plane)" << std::endl;
    std::cout << "Resolution: " << render_config.width << "x" << render_config.height << std::endl;
    std::cout << "Samples per pixel: " << render_config.samples_per_pixel << std::endl;
    std::cout << std::endl;

    // 渲染
    rt::Renderer renderer(render_config, camera, world);
    renderer.render("basic_scene.ppm");

    std::cout << std::endl;
    std::cout << "Scene description:" << std::endl;
    std::cout << "  - Ground plane (gray Lambertian)" << std::endl;
    std::cout << "  - Center sphere (blue Lambertian)" << std::endl;
    std::cout << "  - Left sphere (metallic)" << std::endl;
    std::cout << "  - Right sphere (glass/dielectric)" << std::endl;
    std::cout << std::endl;
    std::cout << "Output saved to basic_scene.ppm" << std::endl;

    return 0;
}
