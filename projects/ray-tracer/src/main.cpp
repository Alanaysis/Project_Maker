/**
 * 光线追踪渲染器 - 主程序
 *
 * 本程序展示光线追踪渲染器的各种功能：
 * - 基础光线追踪
 * - 多种材质
 * - 多种光源
 * - 纹理系统
 * - 加速结构
 * - 高级特性
 *
 * 用法：
 *   ./ray-tracer [options]
 *
 * 选项：
 *   --scene <name>   场景名称 (default, complex, test, primitives, textures, advanced)
 *   --output <file>  输出文件 (默认: output.ppm)
 *   --width <int>    图像宽度 (默认: 400)
 *   --height <int>   图像高度 (默认: 225)
 *   --samples <int>  每像素采样数 (默认: 50)
 *   --depth <int>    最大递归深度 (默认: 20)
 *   --threads <int>  线程数 (默认: 4)
 *   --help           显示帮助信息
 */

#include "../include/vec3.h"
#include "../include/ray.h"
#include "../include/hitable.h"
#include "../include/sphere.h"
#include "../include/triangle.h"
#include "../include/box.h"
#include "../include/cylinder.h"
#include "../include/material.h"
#include "../include/advanced_material.h"
#include "../include/texture.h"
#include "../include/light.h"
#include "../include/camera.h"
#include "../include/renderer.h"
#include "../include/advanced_renderer.h"
#include "../include/advanced_features.h"
#include "../include/scene.h"
#include "../include/bvh.h"
#include "../include/kdtree.h"
#include "../include/octree.h"
#include <iostream>
#include <string>
#include <memory>
#include <chrono>

// 显示帮助信息
void show_help() {
    std::cout << "=== 光线追踪渲染器 ===\n"
              << "\n用法: ray-tracer [options]\n"
              << "\n选项:\n"
              << "  --scene <name>   场景名称\n"
              << "    default        默认场景（三个球体）\n"
              << "    complex        复杂场景（随机球体）\n"
              << "    test           测试场景\n"
              << "    primitives     几何图元场景\n"
              << "    textures       纹理场景\n"
              << "    advanced       高级材质场景\n"
              << "  --output <file>  输出文件 (默认: output.ppm)\n"
              << "  --width <int>    图像宽度 (默认: 400)\n"
              << "  --height <int>   图像高度 (默认: 225)\n"
              << "  --samples <int>  每像素采样数 (默认: 50)\n"
              << "  --depth <int>    最大递归深度 (默认: 20)\n"
              << "  --threads <int>  线程数 (默认: 4)\n"
              << "  --help           显示帮助信息\n"
              << "\n示例:\n"
              << "  ./ray-tracer --scene default --output default.ppm\n"
              << "  ./ray-tracer --scene complex --width 800 --height 450 --samples 100\n"
              << "  ./ray-tracer --scene primitives --output primitives.ppm\n";
}

// 创建几何图元场景
std::shared_ptr<rt::HitableList> create_primitives_scene() {
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

    return world;
}

// 创建纹理场景
std::shared_ptr<rt::HitableList> create_textures_scene() {
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

    return world;
}

// 创建高级材质场景
std::shared_ptr<rt::HitableList> create_advanced_scene() {
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

    return world;
}

int main(int argc, char* argv[]) {
    std::string scene_name = "default";
    std::string output_file = "output.ppm";
    int width = 400;
    int height = 225;
    int samples = 50;
    int max_depth = 20;
    int num_threads = 4;

    // 解析命令行参数
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--scene" && i + 1 < argc) {
            scene_name = argv[++i];
        } else if (arg == "--output" && i + 1 < argc) {
            output_file = argv[++i];
        } else if (arg == "--width" && i + 1 < argc) {
            width = std::stoi(argv[++i]);
        } else if (arg == "--height" && i + 1 < argc) {
            height = std::stoi(argv[++i]);
        } else if (arg == "--samples" && i + 1 < argc) {
            samples = std::stoi(argv[++i]);
        } else if (arg == "--depth" && i + 1 < argc) {
            max_depth = std::stoi(argv[++i]);
        } else if (arg == "--threads" && i + 1 < argc) {
            num_threads = std::stoi(argv[++i]);
        } else if (arg == "--help") {
            show_help();
            return 0;
        }
    }

    // 创建场景
    std::shared_ptr<rt::HitableList> world;
    if (scene_name == "complex") {
        world = rt::SceneFactory::create_complex_scene();
    } else if (scene_name == "test") {
        world = rt::SceneFactory::create_test_scene();
    } else if (scene_name == "primitives") {
        world = create_primitives_scene();
    } else if (scene_name == "textures") {
        world = create_textures_scene();
    } else if (scene_name == "advanced") {
        world = create_advanced_scene();
    } else {
        world = rt::SceneFactory::create_default_scene();
    }

    // 配置相机
    rt::CameraConfig cam_config;
    if (scene_name == "complex") {
        cam_config.lookfrom = rt::Vec3(13, 2, 3);
        cam_config.lookat = rt::Vec3(0, 0, 0);
        cam_config.vfov = 20.0;
    } else if (scene_name == "primitives") {
        cam_config.lookfrom = rt::Vec3(0, 3, 8);
        cam_config.lookat = rt::Vec3(0, 0.5, 0);
        cam_config.vfov = 45.0;
    } else if (scene_name == "textures") {
        cam_config.lookfrom = rt::Vec3(0, 3, 6);
        cam_config.lookat = rt::Vec3(0, 0.5, 0);
        cam_config.vfov = 45.0;
    } else if (scene_name == "advanced") {
        cam_config.lookfrom = rt::Vec3(0, 3, 8);
        cam_config.lookat = rt::Vec3(0, 0.5, 0);
        cam_config.vfov = 45.0;
    } else {
        cam_config.lookfrom = rt::Vec3(3, 3, 2);
        cam_config.lookat = rt::Vec3(0, 0, -1);
        cam_config.vfov = 20.0;
    }

    cam_config.aspect_ratio = static_cast<double>(width) / height;
    cam_config.aperture = 0.1;
    cam_config.focus_dist = (cam_config.lookfrom - cam_config.lookat).length();

    rt::Camera camera(cam_config);

    // 配置渲染参数
    rt::RenderConfig render_config;
    render_config.width = width;
    render_config.height = height;
    render_config.samples_per_pixel = samples;
    render_config.max_depth = max_depth;

    // 显示渲染信息
    std::cout << "=== 光线追踪渲染器 ===" << std::endl;
    std::cout << "场景: " << scene_name << std::endl;
    std::cout << "分辨率: " << width << "x" << height << std::endl;
    std::cout << "采样数: " << samples << std::endl;
    std::cout << "递归深度: " << max_depth << std::endl;
    std::cout << "线程数: " << num_threads << std::endl;
    std::cout << "输出文件: " << output_file << std::endl;
    std::cout << std::endl;

    // 开始渲染
    auto start = std::chrono::high_resolution_clock::now();

    // 创建渲染器并渲染
    rt::Renderer renderer(render_config, camera, world);
    renderer.render(output_file);

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << std::endl;
    std::cout << "渲染完成！" << std::endl;
    std::cout << "渲染时间: " << duration.count() << " ms" << std::endl;
    std::cout << "输出文件: " << output_file << std::endl;

    return 0;
}
