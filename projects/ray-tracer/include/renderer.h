#pragma once

#include "camera.h"
#include "hitable.h"
#include "material.h"
#include <vector>
#include <fstream>
#include <iostream>
#include <algorithm>

namespace rt {

// 渲染配置
struct RenderConfig {
    int width = 800;           // 图像宽度
    int height = 450;          // 图像高度
    int samples_per_pixel = 100; // 每像素采样数
    int max_depth = 50;        // 最大递归深度
};

// 颜色类型（使用 Vec3）
using Color = Vec3;

// 线性转伽马校正
inline double linear_to_gamma(double linear) {
    if (linear > 0) return std::sqrt(linear);
    return 0;
}

// 颜色值转整数
inline int color_to_int(double color, int samples_per_pixel) {
    // 采样平均 + 伽马校正
    double c = color / samples_per_pixel;
    c = linear_to_gamma(c);

    // 限制到 [0, 1] 范围
    c = std::clamp(c, 0.0, 0.999);

    return static_cast<int>(256 * c);
}

// 渲染器
class Renderer {
public:
    RenderConfig config;
    Camera camera;
    std::shared_ptr<Hitable> world;

    Renderer(const RenderConfig& config, const Camera& camera, std::shared_ptr<Hitable> world)
        : config(config), camera(camera), world(world) {}

    // 计算光线颜色
    Color ray_color(const Ray& ray, int depth) const {
        HitRecord rec;

        // 递归深度限制
        if (depth <= 0) return Color(0, 0, 0);

        // 检测命中（t_min 设为 0.001 避免自相交）
        if (world->hit(ray, 0.001, std::numeric_limits<double>::infinity(), rec)) {
            Ray scattered;
            Vec3 attenuation;

            if (rec.material->scatter(ray, rec, attenuation, scattered)) {
                return attenuation * ray_color(scattered, depth - 1);
            }
            return Color(0, 0, 0); // 光线被吸收
        }

        // 背景渐变（天空颜色）
        Vec3 unit_direction = ray.direction.normalize();
        double t = 0.5 * (unit_direction.y + 1.0);
        return Color(1.0, 1.0, 1.0) * (1.0 - t) + Color(0.5, 0.7, 1.0) * t;
    }

    // 渲染到 PPM 文件
    void render(const std::string& filename) const {
        std::ofstream file(filename);
        if (!file.is_open()) {
            std::cerr << "Error: Could not open file " << filename << std::endl;
            return;
        }

        file << "P3\n" << config.width << " " << config.height << "\n255\n";

        for (int j = config.height - 1; j >= 0; --j) {
            std::cerr << "\rScanlines remaining: " << j << " " << std::flush;
            for (int i = 0; i < config.width; ++i) {
                Color pixel_color(0, 0, 0);

                // 多重采样抗锯齿
                for (int s = 0; s < config.samples_per_pixel; ++s) {
                    double u = (i + random_double()) / config.width;
                    double v = (j + random_double()) / config.height;
                    Ray ray = camera.get_ray(u, v);
                    pixel_color += ray_color(ray, config.max_depth);
                }

                // 写入像素
                int r = color_to_int(pixel_color.x, config.samples_per_pixel);
                int g = color_to_int(pixel_color.y, config.samples_per_pixel);
                int b = color_to_int(pixel_color.z, config.samples_per_pixel);
                file << r << " " << g << " " << b << "\n";
            }
        }

        file.close();
        std::cerr << "\nDone. Image saved to " << filename << std::endl;
    }

    // 渲染到内存中的像素缓冲区
    std::vector<std::vector<Color>> render_to_buffer() const {
        std::vector<std::vector<Color>> buffer(config.height,
            std::vector<Color>(config.width));

        int total_rows = config.height;
        int rows_done = 0;

        for (int j = config.height - 1; j >= 0; --j) {
            for (int i = 0; i < config.width; ++i) {
                Color pixel_color(0, 0, 0);

                for (int s = 0; s < config.samples_per_pixel; ++s) {
                    double u = (i + random_double()) / config.width;
                    double v = (j + random_double()) / config.height;
                    Ray ray = camera.get_ray(u, v);
                    pixel_color += ray_color(ray, config.max_depth);
                }

                buffer[config.height - 1 - j][i] = pixel_color / config.samples_per_pixel;
            }

            rows_done++;
            if (rows_done % 10 == 0) {
                std::cerr << "\rRendering: " << (100 * rows_done / total_rows) << "%" << std::flush;
            }
        }
        std::cerr << "\rRendering: 100%" << std::endl;

        return buffer;
    }
};

} // namespace rt
