#pragma once

#include "hitable.h"
#include "sphere.h"
#include "material.h"
#include <memory>
#include <random>

namespace rt {

// 场景工厂
class SceneFactory {
public:
    // 默认场景：三个球体 + 地面
    static std::shared_ptr<HitableList> create_default_scene() {
        auto world = std::make_shared<HitableList>();

        // 地面材质
        auto ground_material = std::make_shared<Lambertian>(Vec3(0.5, 0.5, 0.5));
        world->add(std::make_shared<Plane>(Vec3(0, -0.5, 0), Vec3(0, 1, 0), ground_material));

        // 中心球体（漫反射）
        auto material1 = std::make_shared<Lambertian>(Vec3(0.1, 0.2, 0.5));
        world->add(std::make_shared<Sphere>(Vec3(0, 0, -1), 0.5, material1));

        // 左球体（金属）
        auto material2 = std::make_shared<Metal>(Vec3(0.8, 0.8, 0.8), 0.1);
        world->add(std::make_shared<Sphere>(Vec3(-1.0, 0, -1), 0.5, material2));

        // 右球体（玻璃）
        auto material3 = std::make_shared<Dielectric>(1.5);
        world->add(std::make_shared<Sphere>(Vec3(1.0, 0, -1), 0.5, material3));

        return world;
    }

    // 复杂场景：多个随机球体
    static std::shared_ptr<HitableList> create_complex_scene() {
        auto world = std::make_shared<HitableList>();

        // 地面
        auto ground_material = std::make_shared<Lambertian>(Vec3(0.5, 0.5, 0.5));
        world->add(std::make_shared<Plane>(Vec3(0, -0.5, 0), Vec3(0, 1, 0), ground_material));

        // 中心球体
        auto material1 = std::make_shared<Dielectric>(1.5);
        world->add(std::make_shared<Sphere>(Vec3(0, 1, 0), 1.0, material1));

        auto material2 = std::make_shared<Lambertian>(Vec3(0.4, 0.2, 0.1));
        world->add(std::make_shared<Sphere>(Vec3(-4, 1, 0), 1.0, material2));

        auto material3 = std::make_shared<Metal>(Vec3(0.7, 0.6, 0.5), 0.0);
        world->add(std::make_shared<Sphere>(Vec3(4, 1, 0), 1.0, material3));

        // 随机小球
        std::mt19937 gen(42);
        std::uniform_real_distribution<double> dist(0, 1);

        for (int a = -11; a < 11; a++) {
            for (int b = -11; b < 11; b++) {
                double choose_mat = dist(gen);
                Vec3 center(a + 0.9 * dist(gen), 0.2, b + 0.9 * dist(gen));

                if ((center - Vec3(4, 0.2, 0)).length() > 0.9) {
                    std::shared_ptr<Material> sphere_material;

                    if (choose_mat < 0.8) {
                        // 漫反射
                        Vec3 albedo;
                        albedo.x = dist(gen) * dist(gen);
                        albedo.y = dist(gen) * dist(gen);
                        albedo.z = dist(gen) * dist(gen);
                        sphere_material = std::make_shared<Lambertian>(albedo);
                    } else if (choose_mat < 0.95) {
                        // 金属
                        Vec3 albedo;
                        albedo.x = 0.5 + dist(gen) / 2;
                        albedo.y = 0.5 + dist(gen) / 2;
                        albedo.z = 0.5 + dist(gen) / 2;
                        double fuzz = dist(gen) / 2;
                        sphere_material = std::make_shared<Metal>(albedo, fuzz);
                    } else {
                        // 玻璃
                        sphere_material = std::make_shared<Dielectric>(1.5);
                    }

                    world->add(std::make_shared<Sphere>(center, 0.2, sphere_material));
                }
            }
        }

        return world;
    }

    // 简单测试场景
    static std::shared_ptr<HitableList> create_test_scene() {
        auto world = std::make_shared<HitableList>();

        // 红色球体
        auto red = std::make_shared<Lambertian>(Vec3(0.9, 0.1, 0.1));
        world->add(std::make_shared<Sphere>(Vec3(0, 0, -2), 0.5, red));

        // 蓝色球体
        auto blue = std::make_shared<Lambertian>(Vec3(0.1, 0.1, 0.9));
        world->add(std::make_shared<Sphere>(Vec3(0, 0, -4), 0.5, blue));

        return world;
    }
};

} // namespace rt
