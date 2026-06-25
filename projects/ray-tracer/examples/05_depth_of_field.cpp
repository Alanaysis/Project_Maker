/**
 * 示例 5: 景深效果
 *
 * 本示例展示如何使用景深相机创建景深效果。
 * 景深可以让焦点处的物体清晰，而前景和背景模糊。
 */

#include "../include/vec3.h"
#include "../include/ray.h"
#include "../include/hitable.h"
#include "../include/sphere.h"
#include "../include/material.h"
#include "../include/scene.h"
#include "../include/advanced_features.h"
#include "../include/renderer.h"
#include <iostream>

int main() {
    std::cout << "=== 景深效果示例 ===" << std::endl;

    // 创建场景
    auto world = rt::SceneFactory::create_default_scene();

    // 使用景深相机
    rt::DepthOfFieldCamera camera(
        rt::Vec3(3, 3, 2),        // 相机位置
        rt::Vec3(0, 0, -1),       // 看向的点
        rt::Vec3(0, 1, 0),        // 上方向
        20.0,                     // 垂直视野角度
        16.0 / 9.0,              // 宽高比
        0.2,                      // 光圈大小（控制景深强度）
        (rt::Vec3(3, 3, 2) - rt::Vec3(0, 0, -1)).length()  // 焦距
    );

    // 配置渲染参数
    rt::RenderConfig render_config;
    render_config.width = 400;
    render_config.height = 225;
    render_config.samples_per_pixel = 100;
    render_config.max_depth = 30;

    // 手动渲染循环（使用景深相机）
    std::ofstream file("depth_of_field.ppm");
    file << "P3\n" << render_config.width << " " << render_config.height << "\n255\n";

    for (int j = render_config.height - 1; j >= 0; --j) {
        std::cerr << "\rScanlines remaining: " << j << " " << std::flush;
        for (int i = 0; i < render_config.width; ++i) {
            rt::Vec3 pixel_color(0, 0, 0);

            for (int s = 0; s < render_config.samples_per_pixel; ++s) {
                double u = (i + rt::random_double()) / render_config.width;
                double v = (j + rt::random_double()) / render_config.height;
                rt::Ray ray = camera.get_ray(u, v);

                // 简单的光线追踪
                rt::HitRecord rec;
                if (world->hit(ray, 0.001, 1000, rec)) {
                    rt::Ray scattered;
                    rt::Vec3 attenuation;
                    if (rec.material->scatter(ray, rec, attenuation, scattered)) {
                        pixel_color += attenuation;
                    }
                } else {
                    // 背景
                    rt::Vec3 unit = ray.direction.normalize();
                    double t = 0.5 * (unit.y + 1.0);
                    pixel_color += rt::Vec3(1.0, 1.0, 1.0) * (1.0 - t) +
                                   rt::Vec3(0.5, 0.7, 1.0) * t;
                }
            }

            pixel_color = pixel_color / render_config.samples_per_pixel;
            pixel_color = rt::Vec3(std::sqrt(pixel_color.x),
                                   std::sqrt(pixel_color.y),
                                   std::sqrt(pixel_color.z));
            pixel_color = rt::Vec3(std::clamp(pixel_color.x, 0.0, 0.999),
                                   std::clamp(pixel_color.y, 0.0, 0.999),
                                   std::clamp(pixel_color.z, 0.0, 0.999));

            file << static_cast<int>(256 * pixel_color.x) << " "
                 << static_cast<int>(256 * pixel_color.y) << " "
                 << static_cast<int>(256 * pixel_color.z) << "\n";
        }
    }

    file.close();
    std::cout << "\n渲染完成！输出文件: depth_of_field.ppm" << std::endl;
    return 0;
}
