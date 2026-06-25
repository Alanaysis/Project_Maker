/**
 * 示例 10: 采样策略
 *
 * 本示例展示不同的采样策略对抗锯齿效果的影响。
 * 包含：随机采样、分层采样、Halton 序列采样。
 */

#include "../include/vec3.h"
#include "../include/ray.h"
#include "../include/hitable.h"
#include "../include/sphere.h"
#include "../include/material.h"
#include "../include/camera.h"
#include "../include/scene.h"
#include "../include/advanced_features.h"
#include <iostream>
#include <fstream>

int main() {
    std::cout << "=== 采样策略示例 ===" << std::endl;

    // 创建简单场景
    auto world = rt::SceneFactory::create_test_scene();

    // 配置相机
    rt::CameraConfig cam_config;
    cam_config.lookfrom = rt::Vec3(0, 0, 2);
    cam_config.lookat = rt::Vec3(0, 0, 0);
    cam_config.vfov = 90.0;
    cam_config.aspect_ratio = 1.0;  // 正方形

    rt::Camera camera(cam_config);

    int width = 200;
    int height = 200;
    int samples = 64;

    // 1. 随机采样
    {
        std::ofstream file("sampling_random.ppm");
        file << "P3\n" << width << " " << height << "\n255\n";

        std::mt19937 gen(42);
        std::uniform_real_distribution<double> dist(0.0, 1.0);

        for (int j = height - 1; j >= 0; --j) {
            for (int i = 0; i < width; ++i) {
                rt::Vec3 color(0, 0, 0);

                for (int s = 0; s < samples; s++) {
                    double u = (i + dist(gen)) / width;
                    double v = (j + dist(gen)) / height;
                    rt::Ray ray = camera.get_ray(u, v);

                    rt::HitRecord rec;
                    if (world->hit(ray, 0.001, 1000, rec)) {
                        color += rt::Vec3(0.5, 0.7, 1.0);
                    } else {
                        color += rt::Vec3(0.2, 0.2, 0.2);
                    }
                }

                color = color / samples;
                file << static_cast<int>(256 * color.x) << " "
                     << static_cast<int>(256 * color.y) << " "
                     << static_cast<int>(256 * color.z) << "\n";
            }
        }
        file.close();
        std::cout << "随机采样完成: sampling_random.ppm" << std::endl;
    }

    // 2. 分层采样
    {
        std::ofstream file("sampling_stratified.ppm");
        file << "P3\n" << width << " " << height << "\n255\n";

        auto samples_2d = rt::Sampler::stratified_samples(samples);

        for (int j = height - 1; j >= 0; --j) {
            for (int i = 0; i < width; ++i) {
                rt::Vec3 color(0, 0, 0);

                for (const auto& s : samples_2d) {
                    double u = (i + s.x) / width;
                    double v = (j + s.y) / height;
                    rt::Ray ray = camera.get_ray(u, v);

                    rt::HitRecord rec;
                    if (world->hit(ray, 0.001, 1000, rec)) {
                        color += rt::Vec3(0.5, 0.7, 1.0);
                    } else {
                        color += rt::Vec3(0.2, 0.2, 0.2);
                    }
                }

                color = color / samples;
                file << static_cast<int>(256 * color.x) << " "
                     << static_cast<int>(256 * color.y) << " "
                     << static_cast<int>(256 * color.z) << "\n";
            }
        }
        file.close();
        std::cout << "分层采样完成: sampling_stratified.ppm" << std::endl;
    }

    // 3. Halton 序列采样
    {
        std::ofstream file("sampling_halton.ppm");
        file << "P3\n" << width << " " << height << "\n255\n";

        auto samples_2d = rt::Sampler::halton_samples(samples);

        for (int j = height - 1; j >= 0; --j) {
            for (int i = 0; i < width; ++i) {
                rt::Vec3 color(0, 0, 0);

                for (const auto& s : samples_2d) {
                    double u = (i + s.x) / width;
                    double v = (j + s.y) / height;
                    rt::Ray ray = camera.get_ray(u, v);

                    rt::HitRecord rec;
                    if (world->hit(ray, 0.001, 1000, rec)) {
                        color += rt::Vec3(0.5, 0.7, 1.0);
                    } else {
                        color += rt::Vec3(0.2, 0.2, 0.2);
                    }
                }

                color = color / samples;
                file << static_cast<int>(256 * color.x) << " "
                     << static_cast<int>(256 * color.y) << " "
                     << static_cast<int>(256 * color.z) << "\n";
            }
        }
        file.close();
        std::cout << "Halton 序列采样完成: sampling_halton.ppm" << std::endl;
    }

    std::cout << "\n所有采样策略示例完成！" << std::endl;
    return 0;
}
