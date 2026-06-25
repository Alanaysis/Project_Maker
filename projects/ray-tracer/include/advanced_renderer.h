#pragma once

#include "camera.h"
#include "hitable.h"
#include "material.h"
#include "light.h"
#include "renderer.h"
#include "advanced_material.h"
#include <vector>
#include <memory>
#include <random>
#include <thread>
#include <mutex>
#include <atomic>
#include <fstream>
#include <algorithm>

namespace rt {

// 路径追踪渲染器
class PathTracer {
public:
    RenderConfig config;
    Camera camera;
    std::shared_ptr<Hitable> world;
    std::vector<std::shared_ptr<Light>> lights;

    PathTracer(const RenderConfig& config, const Camera& camera,
               std::shared_ptr<Hitable> world,
               const std::vector<std::shared_ptr<Light>>& lights = {})
        : config(config), camera(camera), world(world), lights(lights) {}

    // 路径追踪核心算法
    Color path_trace(const Ray& ray, int depth) const {
        if (depth <= 0) return Color(0, 0, 0);

        HitRecord rec;
        if (world->hit(ray, 0.001, std::numeric_limits<double>::infinity(), rec)) {
            Ray scattered;
            Vec3 attenuation;

            // 检查是否是自发光材质
            auto emissive = std::dynamic_pointer_cast<Emissive>(rec.material);
            if (emissive) {
                return emissive->emit_color * emissive->intensity;
            }

            if (rec.material->scatter(ray, rec, attenuation, scattered)) {
                // 直接光照
                Color direct_light = compute_direct_light(rec);

                // 间接光照（递归）
                Color indirect_light = attenuation * path_trace(scattered, depth - 1);

                return direct_light + indirect_light;
            }

            return Color(0, 0, 0);
        }

        // 天空背景
        Vec3 unit_direction = ray.direction.normalize();
        double t = 0.5 * (unit_direction.y + 1.0);
        return Color(1.0, 1.0, 1.0) * (1.0 - t) + Color(0.5, 0.7, 1.0) * t;
    }

    // 渲染到 PPM 文件
    void render(const std::string& filename, int num_threads = 4) const {
        std::vector<std::vector<Color>> buffer(config.height,
            std::vector<Color>(config.width));

        std::atomic<int> rows_done(0);
        std::mutex mutex;

        // 多线程渲染
        auto render_rows = [&](int start_row, int end_row) {
            for (int j = start_row; j < end_row; j++) {
                for (int i = 0; i < config.width; i++) {
                    Color pixel_color(0, 0, 0);

                    for (int s = 0; s < config.samples_per_pixel; s++) {
                        double u = (i + random_double()) / config.width;
                        double v = (j + random_double()) / config.height;
                        Ray ray = camera.get_ray(u, v);
                        pixel_color += path_trace(ray, config.max_depth);
                    }

                    buffer[j][i] = pixel_color / config.samples_per_pixel;
                }

                rows_done++;
                if (rows_done % 10 == 0) {
                    std::cerr << "\rRendering: " << (100 * rows_done / config.height) << "%" << std::flush;
                }
            }
        };

        // 启动线程
        std::vector<std::thread> threads;
        int rows_per_thread = config.height / num_threads;

        for (int t = 0; t < num_threads; t++) {
            int start_row = t * rows_per_thread;
            int end_row = (t == num_threads - 1) ? config.height : start_row + rows_per_thread;
            threads.emplace_back(render_rows, start_row, end_row);
        }

        for (auto& thread : threads) {
            thread.join();
        }

        // 写入 PPM 文件
        std::ofstream file(filename);
        file << "P3\n" << config.width << " " << config.height << "\n255\n";

        for (int j = 0; j < config.height; j++) {
            for (int i = 0; i < config.width; i++) {
                Color c = buffer[j][i];
                // 伽马校正
                c = Color(std::sqrt(c.x), std::sqrt(c.y), std::sqrt(c.z));
                c = Color(std::min(std::max(c.x, 0.0), 0.999),
                         std::min(std::max(c.y, 0.0), 0.999),
                         std::min(std::max(c.z, 0.0), 0.999));
                file << static_cast<int>(256 * c.x) << " "
                     << static_cast<int>(256 * c.y) << " "
                     << static_cast<int>(256 * c.z) << "\n";
            }
        }

        file.close();
        std::cerr << "\nDone. Image saved to " << filename << std::endl;
    }

private:
    // 计算直接光照
    Color compute_direct_light(const HitRecord& rec) const {
        Color total_light(0, 0, 0);

        for (const auto& light : lights) {
            Vec3 light_dir = light->direction_to(rec.point);
            double light_distance = light->distance_to(rec.point);

            // 阴影测试
            Ray shadow_ray(rec.point, light_dir);
            HitRecord shadow_rec;
            if (world->hit(shadow_ray, 0.001, light_distance, shadow_rec)) {
                continue;  // 在阴影中
            }

            // 计算光照
            double cos_theta = std::fmax(rec.normal.dot(light_dir), 0.0);
            double attenuation = light->intensity_at(rec.point);
            total_light += light->color * attenuation * cos_theta;
        }

        return total_light;
    }
};

// 双向路径追踪
class BidirectionalPathTracer {
public:
    RenderConfig config;
    Camera camera;
    std::shared_ptr<Hitable> world;

    BidirectionalPathTracer(const RenderConfig& config, const Camera& camera,
                            std::shared_ptr<Hitable> world)
        : config(config), camera(camera), world(world) {}

    Color bidirectional_trace(const Ray& ray, int depth) const {
        // 简化实现：使用单向路径追踪
        if (depth <= 0) return Color(0, 0, 0);

        HitRecord rec;
        if (world->hit(ray, 0.001, std::numeric_limits<double>::infinity(), rec)) {
            Ray scattered;
            Vec3 attenuation;

            if (rec.material->scatter(ray, rec, attenuation, scattered)) {
                return attenuation * bidirectional_trace(scattered, depth - 1);
            }

            return Color(0, 0, 0);
        }

        Vec3 unit_direction = ray.direction.normalize();
        double t = 0.5 * (unit_direction.y + 1.0);
        return Color(1.0, 1.0, 1.0) * (1.0 - t) + Color(0.5, 0.7, 1.0) * t;
    }
};

// 光子映射
class PhotonMapper {
public:
    struct Photon {
        Vec3 position;
        Vec3 power;                     // 光子能量
        Vec3 direction;
    };

    std::vector<Photon> photons;
    int num_photons;

    PhotonMapper(int num_photons = 10000) : num_photons(num_photons) {}

    // 从光源发射光子
    void emit_photons(const std::shared_ptr<Hitable>& world,
                      const std::vector<std::shared_ptr<Light>>& lights) {
        for (const auto& light : lights) {
            for (int i = 0; i < num_photons / lights.size(); i++) {
                // 从光源发射光子
                Vec3 origin = Vec3(0, 10, 0);  // 简化：固定光源位置
                Vec3 direction = random_unit_vector();

                Ray photon_ray(origin, direction);
                trace_photon(photon_ray, world, Vec3(1, 1, 1), 5);
            }
        }
    }

    // 查询光子
    Vec3 query_photons(const Vec3& point, double radius) const {
        Vec3 total_power(0, 0, 0);
        int count = 0;

        for (const auto& photon : photons) {
            if ((photon.position - point).length_squared() < radius * radius) {
                total_power += photon.power;
                count++;
            }
        }

        if (count > 0) {
            return total_power / (M_PI * radius * radius * num_photons);
        }
        return Vec3(0, 0, 0);
    }

private:
    void trace_photon(const Ray& ray, const std::shared_ptr<Hitable>& world,
                      const Vec3& power, int depth) {
        if (depth <= 0) return;

        HitRecord rec;
        if (world->hit(ray, 0.001, std::numeric_limits<double>::infinity(), rec)) {
            // 存储光子
            Photon photon;
            photon.position = rec.point;
            photon.power = power;
            photon.direction = ray.direction;
            photons.push_back(photon);

            // 漫反射散射
            Ray scattered;
            Vec3 attenuation;
            if (rec.material->scatter(ray, rec, attenuation, scattered)) {
                trace_photon(scattered, world, power * attenuation, depth - 1);
            }
        }
    }
};

} // namespace rt
