#include "../include/sphere.h"
#include "../include/material.h"
#include <iostream>
#include <cassert>
#include <cmath>

using namespace rt;

void test_sphere_hit() {
    auto material = std::make_shared<Lambertian>(Vec3(0.5, 0.5, 0.5));
    Sphere sphere(Vec3(0, 0, -5), 1.0, material);

    // 光线指向球体
    Ray ray(Vec3(0, 0, 0), Vec3(0, 0, -1));
    HitRecord rec;

    bool hit = sphere.hit(ray, 0, std::numeric_limits<double>::infinity(), rec);
    assert(hit == true);
    assert(std::abs(rec.t - 4.0) < 1e-10);
    assert(std::abs(rec.point.z - (-4.0)) < 1e-10);

    std::cout << "  [PASS] Sphere Hit" << std::endl;
}

void test_sphere_miss() {
    auto material = std::make_shared<Lambertian>(Vec3(0.5, 0.5, 0.5));
    Sphere sphere(Vec3(0, 0, -5), 1.0, material);

    // 光线偏离球体
    Ray ray(Vec3(0, 2, 0), Vec3(0, 0, -1));
    HitRecord rec;

    bool hit = sphere.hit(ray, 0, std::numeric_limits<double>::infinity(), rec);
    assert(hit == false);

    std::cout << "  [PASS] Sphere Miss" << std::endl;
}

void test_sphere_normal() {
    auto material = std::make_shared<Lambertian>(Vec3(0.5, 0.5, 0.5));
    Sphere sphere(Vec3(0, 0, -5), 1.0, material);

    // 光线从正面打到球体
    Ray ray(Vec3(0, 0, 0), Vec3(0, 0, -1));
    HitRecord rec;

    sphere.hit(ray, 0, std::numeric_limits<double>::infinity(), rec);

    // 法线应该指向观察者
    assert(rec.front_face == true);
    assert(rec.normal.z > 0); // 法线应该有正的 z 分量

    std::cout << "  [PASS] Sphere Normal" << std::endl;
}

void test_sphere_inside() {
    auto material = std::make_shared<Lambertian>(Vec3(0.5, 0.5, 0.5));
    Sphere sphere(Vec3(0, 0, -5), 1.0, material);

    // 光线从球体内部发射
    Ray ray(Vec3(0, 0, -5), Vec3(0, 0, -1));
    HitRecord rec;

    bool hit = sphere.hit(ray, 0, std::numeric_limits<double>::infinity(), rec);
    assert(hit == true);
    assert(rec.front_face == false); // 从内部命中

    std::cout << "  [PASS] Sphere Inside" << std::endl;
}

void test_sphere_tangent() {
    auto material = std::make_shared<Lambertian>(Vec3(0.5, 0.5, 0.5));
    Sphere sphere(Vec3(0, 0, -5), 1.0, material);

    // 光线刚好切过球体
    Ray ray(Vec3(0, 1, 0), Vec3(0, 0, -1));
    HitRecord rec;

    bool hit = sphere.hit(ray, 0, std::numeric_limits<double>::infinity(), rec);
    assert(hit == true); // 切线也是命中

    std::cout << "  [PASS] Sphere Tangent" << std::endl;
}

void test_plane_hit() {
    auto material = std::make_shared<Lambertian>(Vec3(0.5, 0.5, 0.5));
    Plane plane(Vec3(0, 0, 0), Vec3(0, 1, 0), material);

    // 光线从上往下打到平面
    Ray ray(Vec3(0, 5, 0), Vec3(0, -1, 0));
    HitRecord rec;

    bool hit = plane.hit(ray, 0, std::numeric_limits<double>::infinity(), rec);
    assert(hit == true);
    assert(std::abs(rec.t - 5.0) < 1e-10);

    std::cout << "  [PASS] Plane Hit" << std::endl;
}

void test_plane_miss_parallel() {
    auto material = std::make_shared<Lambertian>(Vec3(0.5, 0.5, 0.5));
    Plane plane(Vec3(0, 0, 0), Vec3(0, 1, 0), material);

    // 光线平行于平面
    Ray ray(Vec3(0, 5, 0), Vec3(1, 0, 0));
    HitRecord rec;

    bool hit = plane.hit(ray, 0, std::numeric_limits<double>::infinity(), rec);
    assert(hit == false);

    std::cout << "  [PASS] Plane Miss Parallel" << std::endl;
}

int main() {
    std::cout << "Running Sphere tests..." << std::endl;

    test_sphere_hit();
    test_sphere_miss();
    test_sphere_normal();
    test_sphere_inside();
    test_sphere_tangent();
    test_plane_hit();
    test_plane_miss_parallel();

    std::cout << "All Sphere tests passed!" << std::endl;
    return 0;
}
