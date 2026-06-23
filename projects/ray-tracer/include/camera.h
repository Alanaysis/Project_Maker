#pragma once

#include "ray.h"
#include "material.h"

namespace rt {

// 相机参数
struct CameraConfig {
    Vec3 lookfrom = Vec3(0, 0, 0);      // 相机位置
    Vec3 lookat = Vec3(0, 0, -1);       // 看向的点
    Vec3 vup = Vec3(0, 1, 0);           // 上方向
    double vfov = 90.0;                 // 垂直视野角度
    double aspect_ratio = 16.0 / 9.0;   // 宽高比
    double aperture = 0.0;              // 光圈大小（景深）
    double focus_dist = 1.0;            // 焦距
};

// 相机
class Camera {
public:
    Vec3 origin;           // 相机位置
    Vec3 lower_left_corner; // 图像左下角
    Vec3 horizontal;        // 水平方向
    Vec3 vertical;          // 垂直方向
    Vec3 u, v, w;           // 相机坐标系
    double lens_radius;     // 镜头半径

    Camera() {}

    Camera(const CameraConfig& config) {
        double theta = config.vfov * M_PI / 180.0;
        double h = std::tan(theta / 2.0);
        double viewport_height = 2.0 * h;
        double viewport_width = config.aspect_ratio * viewport_height;

        w = (config.lookfrom - config.lookat).normalize();
        u = config.vup.cross(w).normalize();
        v = w.cross(u);

        origin = config.lookfrom;
        horizontal = u * viewport_width * config.focus_dist;
        vertical = v * viewport_height * config.focus_dist;
        lower_left_corner = origin - horizontal / 2.0 - vertical / 2.0 - w * config.focus_dist;

        lens_radius = config.aperture / 2.0;
    }

    // 生成光线 (u, v 为屏幕坐标 [0, 1])
    Ray get_ray(double s, double t) const {
        Vec3 rd = random_in_unit_disk() * lens_radius;
        Vec3 offset = u * rd.x + v * rd.y;

        return Ray(
            origin + offset,
            lower_left_corner + horizontal * s + vertical * t - origin - offset
        );
    }

private:
    static Vec3 random_in_unit_disk() {
        while (true) {
            Vec3 p(random_double(-1, 1), random_double(-1, 1), 0);
            if (p.length_squared() < 1) return p;
        }
    }
};

} // namespace rt
