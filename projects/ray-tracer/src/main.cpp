#include "../include/renderer.h"
#include "../include/scene.h"
#include <iostream>
#include <string>

int main(int argc, char* argv[]) {
    std::string scene_name = "default";
    std::string output_file = "output.ppm";

    // 解析命令行参数
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--scene" && i + 1 < argc) {
            scene_name = argv[++i];
        } else if (arg == "--output" && i + 1 < argc) {
            output_file = argv[++i];
        } else if (arg == "--help") {
            std::cout << "Usage: ray-tracer [options]\n"
                      << "Options:\n"
                      << "  --scene <name>   Scene to render (default, complex, test)\n"
                      << "  --output <file>  Output file (default: output.ppm)\n"
                      << "  --help           Show this help\n";
            return 0;
        }
    }

    // 创建场景
    std::shared_ptr<rt::HitableList> world;
    if (scene_name == "complex") {
        world = rt::SceneFactory::create_complex_scene();
    } else if (scene_name == "test") {
        world = rt::SceneFactory::create_test_scene();
    } else {
        world = rt::SceneFactory::create_default_scene();
    }

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
    render_config.width = 400;
    render_config.height = 225;
    render_config.samples_per_pixel = 50;
    render_config.max_depth = 20;

    // 渲染
    std::cout << "Rendering scene: " << scene_name << std::endl;
    std::cout << "Resolution: " << render_config.width << "x" << render_config.height << std::endl;
    std::cout << "Samples per pixel: " << render_config.samples_per_pixel << std::endl;

    rt::Renderer renderer(render_config, camera, world);
    renderer.render(output_file);

    std::cout << "Done!" << std::endl;

    return 0;
}
