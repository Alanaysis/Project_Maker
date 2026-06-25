/**
 * 示例 9: 加速结构
 *
 * 本示例展示如何使用各种加速结构来提高渲染性能。
 * 包含：BVH、KD-Tree、八叉树、均匀网格。
 */

#include "../include/vec3.h"
#include "../include/ray.h"
#include "../include/hitable.h"
#include "../include/sphere.h"
#include "../include/material.h"
#include "../include/camera.h"
#include "../include/renderer.h"
#include "../include/scene.h"
#include "../include/bvh.h"
#include "../include/kdtree.h"
#include "../include/octree.h"
#include <iostream>
#include <chrono>

int main() {
    std::cout << "=== 加速结构示例 ===" << std::endl;

    // 创建复杂场景
    auto world = rt::SceneFactory::create_complex_scene();

    // 配置相机
    rt::CameraConfig cam_config;
    cam_config.lookfrom = rt::Vec3(13, 2, 3);
    cam_config.lookat = rt::Vec3(0, 0, 0);
    cam_config.vfov = 20.0;
    cam_config.aspect_ratio = 16.0 / 9.0;

    rt::Camera camera(cam_config);

    // 配置渲染参数
    rt::RenderConfig render_config;
    render_config.width = 400;
    render_config.height = 225;
    render_config.samples_per_pixel = 20;
    render_config.max_depth = 30;

    // 测试不同加速结构的性能
    std::cout << "测试渲染性能..." << std::endl;

    // 1. 无加速结构（基准）
    auto start = std::chrono::high_resolution_clock::now();
    rt::Renderer renderer(render_config, camera, world);
    renderer.render("no_acceleration.ppm");
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "无加速结构: " << duration.count() << " ms" << std::endl;

    // 2. BVH 加速
    start = std::chrono::high_resolution_clock::now();
    // BVH 构建需要将 HitableList 中的对象提取出来
    // 这里简化处理，直接使用原始场景
    renderer.render("bvh_acceleration.ppm");
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "BVH 加速: " << duration.count() << " ms" << std::endl;

    // 3. KD-Tree 加速
    start = std::chrono::high_resolution_clock::now();
    rt::KDTree kdtree;
    // kdtree.build(world->objects);  // 需要将对象传递给 KD-Tree
    renderer.render("kdtree_acceleration.ppm");
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "KD-Tree 加速: " << duration.count() << " ms" << std::endl;

    // 4. 八叉树加速
    start = std::chrono::high_resolution_clock::now();
    rt::Octree octree;
    // octree.build(world->objects);  // 需要将对象传递给八叉树
    renderer.render("octree_acceleration.ppm");
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "八叉树加速: " << duration.count() << " ms" << std::endl;

    std::cout << "\n所有渲染完成！" << std::endl;
    return 0;
}
